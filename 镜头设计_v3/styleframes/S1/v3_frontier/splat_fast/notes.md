# SPLAT 快速渲染版（S1 前沿测试）

同样的 297,380 个光斑、同样的动画，不用 Cycles 光追，改成显卡直接画：每帧按深度排序，从后往前叠。在 WebGL2 里跑（Remotion + ANGLE，走 RTX 5080），内部 4K 超采样再缩到 1080p，线性光的浮点缓冲里混合。

## 实测（Cycles 和 PULSE 的渲染同时占着显卡和 CPU）

| 步骤 | 时间 | 每帧 |
|---|---|---|
| 渲染 300 帧（含 numpy 算动画、截图存 PNG） | 90 秒 | 约 0.3 秒 |
| 后期 `splat/code/post.py`（numpy，CPU） | 512 秒 | 约 1.7 秒 |

单帧的光斑绘制 46 毫秒。Cycles 版约 21 秒一帧。

## 和 Cycles 对比

- 第 150 帧：平均每像素差 1.33 / 255。
- 闪烁（连续帧差的高频部分）：第 120、150 帧 Cycles 0.33 / 这版 0.34、0.36；第 30 帧 2.33 / 2.26；第 60 帧 4.18 / 4.12。第 30、60 帧的高值是光斑汇聚的真实运动，两版一样。
- 差别：排序是按整个光斑，不是按像素，所以血管略亮，黑色空洞略浅。

## 能用在哪

只适用于光斑这种半透明的点。PULSE 的真实虚焦、玻璃器官的折射仍然要光线追踪。4K 输出还没测。

## 跑法

1. `python code/state_server.py`（localhost:8765，每帧现算，不占硬盘）
2. Remotion：`src/v3/s1v3/frontier/splat_fast/entry.jsx`，渲染加 `--gl=angle --concurrency=1`；注意确认日志里的 GL renderer 是 RTX，不是 SwiftShader。
3. 输出重命名成 `f_%04d.png`，再跑 `splat/code/post.py`。

后续：bloom 搬进着色器，后期这 1.7 秒也可以省掉。
