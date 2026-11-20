# 交接：Gemini 娘立绘和 14 个表情（给 Codex，gpt-6.2-sol 高思考）

HKBU SCIE1007 课程作业的科普视频。片尾彩蛋新加第四个角色 Gemini，你来画她的立绘和表情图。另外三个角色（Claude、ChatGPT、DeepSeek）由另一个 Codex 在做 v4，你不要动它们的文件。

## 定死的设计决定（不许改）

1. **画风对齐**：参考图是 `G:/cdk20/work/mascots/refs/claude.png`、`gpt.png`、`deepseek.png` 和 `refs/director_1120/*_card.jpg`。Gemini 必须像同一个画师画的第四个角色：线条粗细、上色方式、头身比、眼睛画法、明度和饱和度都对齐。先把四人并排的对照图做出来，自己看一眼不像一家人就重画。
2. **外形**：照 `镜头设计_v3/深化/12_Gemini角色设定.md` 第 2 节和第 6 节英文提示词。改动一处：**去掉腿环和过膝丝袜**，换成白色及膝袜加深蓝短靴（课程作业，服装要端庄）。其余照写：蓝→紫渐变双马尾、瞳孔四角星高光、珍珠白立领上衣、蓝紫缎带、午夜蓝星纱半裙、两侧水晶四角星发饰、右手上方悬浮发光四角星棱晶。不出现谷歌 logo 和红黄绿蓝四色。
3. **母图流程**：先出一张全身正面母图（透明背景）。母图定了以后，所有表情都在母图上只改脸（和挥手的手臂、道具姿势的手臂），身体、服装、发型像素级不动。不许每个表情重新生成整个人。
4. **14 个表情**（每个出 full_ 全身和 bust_ 胸像两张，胸像从全身母图裁，但要在超分后的大图上裁）：neutral, blink, talk_a, talk_o, wink, laugh, smug, pout, surprised, shy, sigh, think, wave, prop（prop = 右手托起发光棱晶摆 pose）。另出 wink.gif、laugh.gif（12 帧循环）。
5. **影分身**：再出一张 `clone.png`：母图做成半透明全息版（55–65% 不透明，青蓝→淡紫色偏，柔光描边，脚下向上飘的光点和扫描线）。以及 6 个版本小牌 PNG：`tag_Pro.png`、`tag_Flash.png`、`tag_Flash-Lite.png`、`tag_Nano.png`、`tag_Deep-Think.png`、`tag_Exp-1120.png`：圆角胶囊，深夜蓝半透明底 `#12162E`，1.5 px 冰蓝→紫渐变描边 `#4DA6FF→#9B6BFF`，白字，左侧小四角星 ✦，底部小三角，几何无衬线字体，高 120 px。
6. **分辨率**：realesrgan-ncnn-vulkan anime 2× 放大，全身长边 ≥3000 px，胸像 ≥2400 px，透明背景保留。
7. **磁盘**：生图工具先写 C 盘可以，每出一张立刻搬到 `G:/cdk20/work/mascots/codex/v4/gemini/`，删掉 C 盘那份（只删你自己刚生成的）。后处理全在 G 盘做。
8. **质量档**：能设就设最高档；设不了用默认档，在 README 写一句，不要停工。

## 交付

`G:/cdk20/work/mascots/codex/v4/gemini/` 里：full_*.png ×14、bust_*.png ×14、clone.png、tag_*.png ×6、wink.gif、laugh.gif、`lineup.png`（四人并排对照）、`compare_expressions.png`（14 表情联系表）、README.md（每张尺寸、用的工具和质量档）。

自检：14 张表情叠在一起身体不动；lineup 里四人画风一致；透明背景边缘没有白边；没有 logo。卡住时自己选一个合理、可改回的方案写进 README，接着做。
