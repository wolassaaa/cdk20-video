# HKBU SCIE1007 片尾彩蛋制作方案（剧本 · 名牌字卡 · 分镜 · 配音）

> **定位**：全片正片（Ren et al. 2023，AI 辅助发现肝癌 CDK20 抑制剂）片尾 W5 结束、画面黑屏后的 **55–58 秒片尾彩蛋**。  
> **规则**：片中所有字幕、名牌、小卡、数据卡与出处一律使用**英文**；全部科学案例与数字严格限定在《09_AI角色插段》已核实范围内，不新增事实、不夸大结论，最终收束于 **"AI narrows the search. Experiments still decide."**。  
> **素材规范**：角色图使用 Codex v4 放大至长边约 `3000 px`；近景（胸像）**必须直接调用 v4 胸像图**，禁止从全身图硬裁；说话时口型按音量在 `talk_a` / `talk_o` 间自动切换（滞后 3 帧防抖），表中所列为该句的**主表情**。

---

## 一、剧本（共 19 句，160 英文词，目标时长约 56.5 秒）

**站位基准**（用于甩镜方向与全景站位）：左 `Claude` ｜ 中 `ChatGPT` ｜ 右 `DeepSeek`。

| 序号 | 谁说 | 英文台词 | 情绪 / 语气提示（英文，供 Chatterbox 用） | 表情图文件名（主表情） | 听的人的反应表情 |
|---|---|---|---|---|---|
| L01 | DeepSeek | It's not over yet! | bright, mischievous, energetic shout in the dark | `neutral`（黑屏仅出声） | —（均未出场） |
| L02 | DeepSeek | Behind the scenes, we AIs pushed real new results—and my big sisters are already arguing. | bubbly, excited, gossipy, cheerful | `wave` | —（二人尚未入画） |
| L03 | Claude | I'll start. Scorpion venom. A research version of me designed proteins that grab its toxins. | warm, composed, unhurried, lightly proud | `prop` | DeepSeek: `think` |
| L04 | ChatGPT | Wait—YOU designed proteins? | cool tease, mock surprise, languid eyebrow raise | `surprised` | Claude: `blink`；DeepSeek: `surprised` |
| L05 | Claude | Sixty-four hours. Over three hundred thousand designs. Seventeen stuck in lab tests. | poised, crisp, building smoothly to proud climax | `smug` | ChatGPT: `sigh`；DeepSeek: `think` |
| L06 | DeepSeek | Seventeen binders! Not an antivenom—not yet. | bright, fast, cheeky fact-check | `wink` | Claude: `surprised`；ChatGPT: `laugh` |
| L07 | Claude | Fair enough. Binding only. | soft shy chuckle, gentle, gracefully conceding | `shy` | ChatGPT: `smug`；DeepSeek: `wink` |
| L08 | ChatGPT | Cute. A mini me redesigned stem-cell proteins. Fifty times the reprogramming markers. | husky, languid, effortlessly smug brag | `smug` | Claude: `think`；DeepSeek: `blink` |
| L09 | DeepSeek | That's OpenAI's own report! Not peer-reviewed yet. | bubbly, sing-song, playful call-out | `laugh` | ChatGPT: `surprised`；Claude: `wink` |
| L10 | ChatGPT | Ugh, details. Quiet, big fat fish. | lazy sigh, amused, teasing big-sister poke | `sigh` | DeepSeek: `surprised`；Claude: `blink` |
| L11 | DeepSeek | I'm NOT a big fat fish! | puffed-up, cute indignant pout, high energy | `pout` | ChatGPT: `laugh`；Claude: `shy` |
| L12 | DeepSeek | Plot twist! AI-designed proteins blocked deadly snake toxins, and the mice survived! | huge burst of excitement, dramatic reveal, triumphant | `laugh` | Claude: `surprised`；ChatGPT: `surprised` |
| L13 | Claude | And AI found halicin and abaucin—two new antibiotic leads that fought superbugs in mice. | warm wonder, articulate, steady and clear | `prop` | ChatGPT: `think`；DeepSeek: `blink` |
| L14 | ChatGPT | So we're curing everything now? | husky, playful tease, dry amusement | `smug` | Claude: `sigh`；DeepSeek: `blink` |
| L15 | DeepSeek | Nope! Early leads, not approved medicines. | instant snappy cut-in, cheerful and firm | `wink` | ChatGPT: `pout`；Claude: `laugh` |
| L16 | Claude | Every one still had to pass a real lab. AI narrows the search. | calm, sincere, grounded, reassuring | `neutral` | ChatGPT: `think`；DeepSeek: `neutral` |
| L17 | ChatGPT | Fine. Experiments still decide. | brief amused sigh, then warm, confident certainty | `sigh`（句尾切 `wink`） | Claude: `wink`；DeepSeek: `laugh` |
| L18 | Claude | Now come on—dinner's ready. | warm, gentle smile, playful big-sister call | `laugh` | DeepSeek: `surprised`；ChatGPT: `wink` |
| L19 | DeepSeek | Dinner?! Wait for me! Bye, everyone! | instant starry-eyed joy, rushing off, bright farewell | `prop`（句尾切 `wave`） | Claude: `wave`；ChatGPT: `wave` |

> **事实核查确认**：L03/05/06/07（蝎毒结合蛋白 64h / 30 万+设计 / 17 个结合，非解毒剂）、L08/09（GPT-4b micro 干细胞蛋白 50× 重编程标志物，公司报告未同行评审）、L12（抗蛇毒蛋白阻断致命蛇毒小鼠存活）、L13/15（halicin 与 abaucin 两个新抗生素线索，小鼠抗超级细菌，非获批药物）、L16/17（过真实实验室、AI 缩小范围、实验说了算）全部 100% 对齐《09_AI角色插段》出处表，零新增科学事实。

---

## 二、名牌、Voice Prompt 小卡与数据字卡文字（全英文）

### 2.1 角色登场名牌 & Voice Prompt 小卡

样式参考 B 站角色卡：顶部小编号 `No.0X` + 大字角色名 + 一行英文副标题；下方深色半透明磨砂小卡，左上带小星标 `✦ VOICE PROMPT` + 底部动态声波条。主题色：`DeepSeek` 海洋蓝 `#4DA6FF`、`Claude` 暖橙金 `#F08C3E`、`ChatGPT` 冰白紫 `#C9B8FF`。

| 角色 | 登场编号 | 大字名字 | 英文小标题 | VOICE PROMPT 小卡文字（照原设定忠实英译） |
|---|---|---|---|---|
| **DeepSeek** | `No.01` | `DeepSeek` | `the Whale Maid` | `Sweet, soft, and a little bubbly. Pouts instantly if called "big fat fish"—but perks right up the second dinner's ready.` |
| **Claude** | `No.02` | `Claude` | `the Orange-haired Lady` | `A warm, mid-low voice in her twenties—unhurried and crisp. Gentle beneath her poise, with the occasional shy chuckle.` |
| **ChatGPT** | `No.03` | `ChatGPT` | `the White Dragon` | `A mature, husky big-sister voice with steady breath. Confident, lazily amused—like someone who's seen it all.` |

### 2.2 配套数据牌与收束横幅（沿用已核实出处）

字卡宽 `780 px` 竖牌，放置在人物相对的三分侧，不挡脸。数字区在 `hit` 词前 `0.45 s` 展开（之前不显示 `0`），提醒行在打假词上展开并微亮。

| 牌号 | 标题 / 小标题 | 大数字（及落点词） | 简短说明 | 提醒行（打假展开） | 出处行（底部小字） |
|---|---|---|---|---|---|
| **Card 0** | `SCORPION VENOM` / `AI Protein Binders` | `17 / 211`（0.4s 计数停在 L05 `Seventeen`） | `Bound neurotoxins in lab tests (64 h, 300k+ designs)` | `Binding only — not yet proven as an antivenom`（L06 `antivenom` 展开） | `Anthropic (20 Oct 2026); lab tests by Adaptyv Bio & Twist Bioscience` |
| **Card 1** | `STEM-CELL PROTEINS` / `GPT-4b micro` | `50×`（0.4s 计数停在 L08 `Fifty`） | `Higher reprogramming markers reported` | `Company report — not yet peer-reviewed`（L09 `report` 展开） | `OpenAI, "Accelerating life sciences research" (22 Aug 2025)` |
| **Card 2** | `SNAKE TOXINS` / `De Novo Binders` | `80–100%`（定值弹出在 L12 `survived`） | `Mouse survival against lethal snake toxin` | `Single cobra-like toxin — not whole snake venom`（L12 `survived` 后展开） | `Vázquez Torres et al., Nature 2025 (Baker lab, Univ. of Washington)` |
| **Card 3** | `NEW ANTIBIOTICS` / `Halicin & Abaucin` | `2`（定值弹出在 L13 `superbugs`） | `AI-identified leads active against superbugs in mice` | `Early leads — not approved medicines`（L15 `Early leads` 展开） | `Stokes et al., Cell 2020; Liu et al., Nature Chemical Biology 2023` |
| **Banner 4** | `THE TAKEAWAY`（顶部横幅） | `AI narrows the search. Experiments still decide.` | — | — | `Summary of verified cases above` |

**画面右下角固定鸣谢小字**（仅在全景及结尾显示，20 px 半透明白字）：  
`Illustration. Characters adapted from fan designs by ZipZipPipe (Bilibili) and Shangshan Wuxing (CC BY-NC-SA 4.0).`

---

## 三、分镜表（共 32 镜，单镜 1.0–2.8 秒，总时长约 56.5 秒）

**通用视觉规范**：
- **舞台**：沿用柔光棚（深蓝到靛紫弧形底 + 远处分子六边形网格 + 竖直柔光箱 + 缓动光柱 + 角色主题色背光与轮廓光）。
- **景别与图源**：`全景`（三人七分身，下沿裁在大腿中段裙摆，不裁膝盖，用全身图）；`半身`（放大 `1.24–1.30×`，用全身图）；`胸像`（直接调用 v4 胸像图，头顶留白 `40–50 px`）。
- **字幕**：底部居中单行分句，54 px Instrument Serif，压在腰/裙摆区域，不压脸与胸口；换人镜头开始前必须先收掉上一位字幕。所有字卡、闪白、速度线图层常驻并用透明度控制，避免卸载残留帧。

| 镜号 | 起止句号 | 预估时长 | 景别与构图 | 镜头运动 | 转场方式 | 名牌 / 字卡出现时机 | 特效（闪白 / 速度线 / 震一下等） |
|---|---|---|---|---|---|---|---|
| **S01** | L01 | 1.5 s | 纯黑屏（接正片 W5 黑场） | 静止 | 直接接黑场 | 仅出居底英文字幕 `"It's not over yet!"` + 中央一道海洋蓝声波脉冲 | 声波随人声跳动，无人物 |
| **S02** | L02（前半） | 2.6 s | **半身**（DeepSeek 居右三分，`wave`） | 人物自下轻弹入画，镜头缓推 `1.24→1.29×` | **开场亮起**：`T6` 奶白光扫横贯黑屏 + 柔光棚灯箱由中心向外点亮 | 左侧翻入 `No.01 DeepSeek` 名牌 + `VOICE PROMPT` 小卡（声波微动） | 柔光棚开机光晕扩散 |
| **S03** | L02（后半） | 2.0 s | **胸像**（DeepSeek 居中，`wave→laugh`） | 沿轴切近并微推 `1.00→1.05×` | 硬切（`and my big sisters` 词首） | `No.01` 名牌与小卡平滑淡出 | 无 |
| **S04** | L03（前半） | 2.4 s | **半身**（Claude 居左三分，`prop` 持书） | 人物轻滑入画，缓推 `1.24→1.29×` | 硬切 | 右侧翻入 `No.02 Claude` 名牌 + `VOICE PROMPT` 小卡 | 背景背光切换为暖橙金 |
| **S05** | L03（后半） | 2.7 s | **胸像**（Claude 居左三分，`prop`） | 沿轴切近微推；末 5 帧向右甩出 | 硬切（`A research version` 词首） | 右侧 `No.02` 名牌翻转替换为 `Card 0`（蝎毒牌） | 末 5 帧横向运动模糊预备抢话 |
| **S06** | L04 | 1.7 s | **胸像**（ChatGPT 居中偏右，`surprised`） | `YOU` 词上 0.16 s 急推 `1.00→1.14×` | **甩镜**（左→右，带横向运动模糊） | 左侧滑入 `No.03 ChatGPT` 名牌 + `VOICE PROMPT` 小卡 | **`YOU` 上画面震一下** + 冰白紫背光闪亮 |
| **S07** | L05（前半） | 2.1 s | **半身**（Claude 居左三分，`smug`） | 缓推 `1.24→1.28×` | 硬切 | 右侧保持 `Card 0`（数字区暂隐藏） | 无 |
| **S08** | L05（中段反应） | 1.0 s | **胸像**（ChatGPT 居中，`sigh`） | 身体微沉，轻微下摇 | 硬切（`thousand designs` 处插听众反应） | 无牌 | 无 |
| **S09** | L05（后半） | 1.7 s | **胸像**（Claude 居左三分，`smug`） | 切近定格微推 | 硬切（`Seventeen` 前半拍） | 右侧 `Card 0` 数字区展开，`17 / 211` 计数停在 `Seventeen` | 数字落定瞬间轻闪高光 |
| **S10** | L06（前半） | 1.2 s | **半身**（DeepSeek 居右三分，`wink`） | 轻弹入画 | 硬切 | `Card 0` 换至左侧 | 无 |
| **S11** | L06（后半） | 1.5 s | **胸像斜线分屏**（左 DeepSeek `wink` ｜ 右 Claude `surprised`） | 两人分别从两侧滑入，Claude 微下沉 | 斜线分屏切入（第一帧画面即在，仅人物滑入） | 顶部/角标亮出 `Card 0` 提醒行 `Binding only...`（`antivenom` 上展开） | 提醒行边缘高亮扫光 |
| **S12** | L07 | 1.5 s | **胸像**（Claude 居中，`shy`） | 柔和微拉 `1.06→1.00×` | 硬切 | 无牌 | 人物脸颊侧淡粉微光粒子 |
| **S13** | L08（前半） | 2.3 s | **半身**（ChatGPT 居右三分，`smug`） | 缓推 `1.24→1.30×` | 硬切 | `mini me` 上左侧翻入 `Card 1`（GPT-4b micro） | 背景背光切为冰白紫 |
| **S14** | L08（后半） | 1.9 s | **胸像**（ChatGPT 居右三分，`smug`） | 沿轴切近；末 5 帧向左甩出 | 硬切（`Fifty` 前 0.45 s） | 左侧 `Card 1` 的 `50×` 计数停在 `Fifty` | 数字落定闪光 + 末 5 帧横向模糊 |
| **S15** | L09（前半） | 1.5 s | **半身**（DeepSeek 居左三分，`laugh`） | 弹跳落位 | **甩镜**（右→左，横向运动模糊） | `

---

> 注（Claude 11-20 复核）：Gemini 输出在分镜 S15 处被截断，第四节配音设定缺失。剧本 19 句和四张牌的数字、出处已逐条对过 09 出处表，一致，可直接用；分镜和配音由施工方（Fable）照剧本、09 第七节和 12_导演意见 补全。
