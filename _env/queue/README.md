# 渲染任务队列与排期面板

HKBU SCIE1007 课程作业的科普视频：这套东西只负责让渲染任务 7×24 小时按顺序自动跑，并给导演一个本机网页控制排期。不涉及任何画面设计。

## 文件
- `queue.json`：任务列表，列表顺序就是优先级。读写都带锁，写入先写临时文件再原子替换。
- `runner.py`：后台守护进程，每 10 秒看一次队列，按槽位规则启动任务，写心跳 `heartbeat.txt` 和状态变化日志 `events.log`。单实例（`runner.pid`）。
- `panel.py`：导演用的网页面板，只监听 `127.0.0.1:8770`。每 5 秒自动刷新，点任务看日志最后 40 行。
- `qctl.py`：给代理用的命令行。
- `ensure.py`：发现 runner 或面板挂了就拉起。已登记到 Windows 任务计划（任务名 `CDK20_Queue_Ensure`，每 5 分钟一次 + 登录时）。
- `start_queue.bat`：双击启动并打开面板（桌面有 `渲染排期.lnk` 指向它）。
- `settings.json`：显卡静音时段（`gpu_quiet`，如 `23:00-08:00`）。
- `logs/<id>.log`：每个任务的输出（只追加）；`logs/runner.log`、`logs/panel.log` 是两个服务的输出。

## 加任务
```
py -3.11 -X utf8 "D:/。hkbu/molecular science/_env/queue/qctl.py" add '{"id":"p1","title":"第二章页面渲染","kind":"remotion","res":"cpu","cmd":"bash 镜头设计_v3/映射/_cache/render_ch2pages.sh","est_min":40}'
py -3.11 -X utf8 ".../qctl.py" add '{"id":"b1","title":"样片 2-03 渲染","kind":"blender","cmd":"bash 镜头设计_v3/inserts/render_s203_v2.sh","after":["p1"],"est_min":90}'
```
`cmd` 在项目根目录下用 Git Bash 运行，必须可重跑（已完成的帧跳过）。`kind=blender` 默认 `res=gpu`，其余默认 `cpu`。也可以传 json 文件路径，里面放一个对象或一个数组。
其他命令：`list`、`hold/release/retry/top/cancel <id>`、`pause`/`resume`（全部）、`gpu pause`/`gpu resume`、`quiet 23:00-08:00`（`quiet off` 取消）。

## 槽位规则
- 只有 `after` 里的任务都 `done`，任务才会启动；按列表顺序挑第一个能启动的。
- 显卡任务：`GPU_PAUSED`（导演总开关）、`GPU_HOLD`（排期里的显卡暂停）、静音时段内都不启动；同时在跑的 blender.exe 进程数和显卡任务数取较大者，必须小于 2。
- 非显卡任务（11-24 起，按内存/显存/NVENC 决定并发，CPU 重活不再一刀切一次一个）：逐个放行，要同时满足
  - 同类上限：`remotion` 2、`ffmpeg` 4、`comp` 4、`cut` 1、`whisper` 1（没列的种类不限个数）；
  - 空闲内存：放行后系统还剩 ≥ 1 GB。预扣：remotion 3 GB（`--concurrency=6` 实测）、ffmpeg/comp 0.9 GB、cut 2 GB、whisper 3 GB、其他 0.5 GB；起来不到 2 分钟的任务按满额预扣；
  - 显存：nvidia-smi 已用 + 本任务（显卡合成类约 0.4 GB）≤ 12 GB（16 GB 里留 4 GB 给导演）；
  - NVENC：同时编码会话 ≤ 8（11-23 一次开 18 路报错过）。
  - 数字在 `qlib.py` 顶部（`KIND_MAX`、`MEM_NEED_GB`、`VRAM_BUDGET_MB`、`NVENC_MAX`）；`QUEUE_OLD_SLOTS=1` 启动 runner 回到旧规矩（remotion/ffmpeg 一次一个）。
- 存在 `PAUSED_ALL` 时什么都不启动。
- 退出码 0 为完成；否则重试，共 2 次都失败为 `failed`。runner 重启时发现运行中的任务进程已不在，按“退出码未知”处理（回到等待，次数加 1）。

## 绝不删除
所有代码都不删文件、不删目录。开关一律“新建 / 改名为 `.off`”：`PAUSED_ALL`、`GPU_HOLD` 关闭时改名为 `PAUSED_ALL.off`、`GPU_HOLD.off`，再开时改名回来。面板没有删除接口，“取消”只是暂停并停止进程。日志只追加。
