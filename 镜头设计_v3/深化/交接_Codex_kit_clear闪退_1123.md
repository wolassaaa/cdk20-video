# 交接：Codex 修 kit_clear 材质导致 Blender 闪退（急）

HKBU SCIE1007 课程作业的科普视频。这一步：修一个 Blender 闪退的问题。

## 问题

你在 11-23 04:49 改了 `镜头设计_v3/inserts/kit_deep_r5.py`，给 kit_clear 材质的 Volume 接了一个 Mix Shader，按物体属性混合。

Blender 5.3 用 Cycles 渲到用这个材质的零件就会闪退，CPU 和 GPU 都一样。位2 用二分法定位到的就是这一处，它在 `drill_302.py` 里把 Volume 临时直连回原来的吸收节点，才绕了过去。

## 要做

1. 改 kit_deep_r5.py：Volume 不再用按物体属性混合的 Mix Shader。
   - 要做出不同的透明度或颜色，就每种做一个材质副本，比如 `K.clear0` 和 `K.clear0_tint`，分别赋给零件。
   - 或者用别的、在 5.3 Cycles 下不会闪退的办法。
2. 用 Blender 5.3（看 memory 或 `_env` 里的路径），Cycles 加 OPTIX，各渲一帧验证，不许闪退：
   - u05_cell_shell 的开盖和合盖两格；
   - 用到 kit_clear 的别的件。
   
   验证走队列（`_env/queue/qctl.py`）。
3. u05 的检查图和合盖专项再跑一次，结果仍要 0 对网格交叉。旧图改名加 `_r3` 保留。
4. 不要改 `drill_302.py`。告诉我改好之后，`drill_302.py` 里那段绕路代码能不能去掉，我转给施工方。

## 规矩

- 不 git 提交，不派子代理。
- 不打开 `_env` 下的密钥文件和名字文件。
- 做完在 `镜头设计_v3/工作记录.md` 末尾追加一行。
- 回一段话：怎么改的、验证结果。
