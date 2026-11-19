# 交给 Codex：三位 AI 娘的 wink 动图帧（只出图，不做别的）

HKBU SCIE1007 课程作业的科普视频。片中有一段 30–50 秒的小插段，三位二次元可爱画风的 AI 角色 **Claude**、**GPT**、**DeepSeek** 出场介绍 AI 在药物发现上的最新公开进展。这一步只请你**生成角色图像帧**，台词、配音、动画合成由别人做。导演说明：Codex 额度这次只用于这个出图任务，不做其他工作。

## 角色依据
- Claude 娘：参考 https://genderswapai.com/zh-CN/ai-gijinka/claude （长橙发、花朵发饰、白黑层叠裙装；三视图 PNG 链接在该页）。
- GPT 娘、DeepSeek 娘：在同站角色索引 https://genderswapai.com/zh-CN/ai-gijinka#characters 找对应页面；没有就按网上流传最广的 ChatGPT 娘 / DeepSeek 娘设定（DeepSeek 常见深蓝配色、鲸鱼元素；GPT 常见黑白加青绿）。
- 三人画风统一：二次元 Q 版可爱、干净线条、明亮配色。不画任何公司官方 logo。

## 要的图（每个角色一组，三人同样规格）
用你的图像生成能力出图，每组**同一姿势、同一构图、同一尺寸**，只变表情，方便逐帧切换做动画：
1. `open`：正面半身，双眼睁开，嘴闭，微笑。
2. `blink`：双眼闭。
3. `wink`：一只眼闭、另一只睁，俏皮。
4. `talk_a`：嘴张开（说话口型）。
5. `talk_o`：嘴圆（说话口型）。
6. `wave`：挥手打招呼（可换手臂姿势，其余一致）。
- 尺寸 1536×1536，**透明背景 PNG**（做不到透明就纯色 #00FF00 绿底，便于抠）。角色占画面高度 85%，居中，脚下不留地面。
- 三人身高比例一致，可以并排站。
- 再各出一个 12 帧的 wink 小循环 GIF（open→wink→open），`<name>_wink.gif`。

## 交付
- 放 `G:/cdk20/work/mascots/codex/<claude|gpt|deepseek>/`，文件名如上。
- 一份 `G:/cdk20/work/mascots/codex/README.md`：每个角色依据的参考来源链接、原作者、许可说明（照参考页写的抄过来），以及你生成时用的提示词。
- 不改项目代码，不 git 提交，不删任何文件。
