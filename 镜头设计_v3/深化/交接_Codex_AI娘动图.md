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

## 11-21 更新：照下面的完整提示词直接出图，不要自己再构思

推理强度用中档即可，按提示词逐张生成，不要反复推敲。每张都是同一角色、同一姿势，只换"表情行"。

### 共用部分（每张提示词都以这段开头）
> Cute anime chibi-proportion girl (head-to-body 1:3.5), half-body portrait from the waist up, facing the viewer straight on, centered, character fills 85% of the image height, both shoulders level, arms relaxed at the sides unless stated. Clean crisp lineart (dark brown lines, uniform 3px weight), flat cel shading with one soft shadow tone and one small highlight, bright saturated but soft pastel-leaning palette, large glossy anime eyes with two white catchlights, small blush marks on the cheeks. Plain transparent background (if transparency is impossible use flat pure #00FF00 green, no gradient, no shadow on the ground). No text, no logos, no watermark, no frame. 1536×1536.

### Claude（依据 genderswapai Claude 娘：长橙发、花朵发饰、白黑层叠裙装）
> Character: "Claude". Long straight warm orange hair (#E8834A base, #F2A673 highlight) reaching the waist, soft side-swept bangs, two thin strands framing the face. A small cream-white five-petal flower hair ornament with an orange center clipped above her left ear. Warm amber eyes (#C46A2B). Outfit: layered dress — white high-collar blouse with a small black ribbon tie, black sleeveless overdress with a white frilled hem layer peeking out, black-and-white layered skirt. Gentle, calm, thoughtful smile. Personality: kind and careful.

### GPT
> Character: "GPT". Shoulder-length sleek black bob hair (#1E1E1E) with a soft teal (#10A37F) gradient at the tips, straight blunt bangs. Teal-green eyes (#10A37F). A small white hexagon-shaped hair clip on the right side (simple geometric shape, NOT any logo). Outfit: crisp white hoodie-jacket with black inner shirt, thin teal piping along the zipper and hood edge, black pleated skirt. Confident, cheerful grin. Personality: energetic and talkative.

### DeepSeek
> Character: "DeepSeek". Long wavy deep-blue hair (#2B4DB8 base, #6C8CF0 highlight) in a high side ponytail tied with a light-blue ribbon, a small cute cartoon whale hair accessory (round, light blue #8FB4FF, tiny water spout) on the ribbon. Deep-blue eyes (#2B4DB8). Outfit: navy sailor-style top with a light-blue collar and white stripe, small whale-tail charm on the bow, navy skirt. Curious, bright smile. Personality: curious and studious.

### 表情行（每个角色各 6 张，替换到提示词末尾）
1. open — "Expression: both eyes open, mouth closed in a soft smile."
2. blink — "Expression: both eyes gently closed (curved lines), soft smile, everything else identical."
3. wink — "Expression: left eye closed in a playful wink (curved line), right eye open with sparkle, small open-mouth smile, everything else identical."
4. talk_a — "Expression: eyes open, mouth open wide in an 'ah' shape, everything else identical."
5. talk_o — "Expression: eyes open, mouth small and round in an 'oh' shape, everything else identical."
6. wave — "Pose change: right hand raised beside the face waving, palm open; expression: eyes open, cheerful open smile. Everything else identical."

为了一致：先出 open，再以 open 为参考图做其余五张（若工具支持图生图/编辑，就用编辑只改脸和手）。GIF 用 open→wink→open 三帧做 12 帧循环（open 5 帧、wink 4 帧、open 3 帧）。
