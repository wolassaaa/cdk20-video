# WORTH TESTING? — Narration script v3

SCIE1007 Molecular Science in Daily Life · Group Project Topic 10: *Computer-aided drug discovery and its benefits* · 15–20 min English video · due Fri 27 Nov 2026, 11:59 pm (Moodle, one file per group, named like `S#-Gp#-T10.mp4`).

Draft v3, 2026-10-26, for team review. Written only from the local course files and the fact-checked CDK20 materials. Nothing here has been checked by the instructor.

**Research question.** How can computer-aided methods help scientists find and assess potential cancer drug candidates? A case study of CDK20 in liver cancer.

**Objectives (as submitted in Tutorial 1).** (1) Identify major computer-aided methods used in cancer drug discovery. (2) Evaluate how these methods help assess potential cancer drug candidates.

**Team assumption.** Four speakers, A–D, with C as the female voice. Real names go in later. A five-member re-split is in Part 6.

## Runtime at a glance

| Measure | Value |
|---|---|
| Narration words | 2,120 |
| Speech time at 130 wpm (word count) | 16:18 |
| Speech time, conservative (numbers and acronyms spelled out, 195 syllables/min) | 17:02 |
| Non-speech: title card 4 s, six 2-s music breaths, end card 15 s | 31 s |
| **Total runtime** | **16:49 (word count) to 17:33 (conservative)** |

All time codes below use the conservative estimate, so the real cut is more likely to come in a little shorter than longer. Both ends sit inside the 15–20 minute window. Re-time everything from the recorded voice before editing.

## How to read this script

- **ON-CAM** = talking head. The member films it against a plain wall on a tripod, eye level, medium close-up. Every ON-CAM line is 19 words or fewer so it can be lip-synced if the voice is re-recorded later.
- **VO** = voice-over under visuals, spoken by the same member.
- Visual codes: **[CAM]** talking head · **[INK]** hand-drawn ink (bone-white `#EDEBE4` on ink-black `#070707`) · **[TD]** TouchDesigner vessel / flow visuals · **[3D]** real molecular structure (AlphaFold model or molecules redrawn from the paper) · **[2D]** clean data type for numbers. Accent colours follow the v3 plan: vermilion `#FF3B1F` for body and biology, cyan `#29F0FF` for AI and computation, at most two accents per shot.
- Numbers: speech rounds a few long numbers ("about 570 nanomolar"); the screen always shows the exact value with its ± spread and a short citation footnote (Tutorial 2 asks for citations on the relevant slide and a full list at the end).
- Labels must stay honest: "predicted model", "predicted pose", "schematic" wherever that is what the viewer is seeing.

## Part 0 · Source codes used in the Source lines

| Code | Source | Evidence-list ID |
|---|---|---|
| R23 | Ren, F. et al. Chem. Sci. 2023, 14 (6), 1443-1452 (main case study; full text). Section names / figure numbers given after the code. | S02 |
| R23-SI | Electronic supplementary information of R23 (synthesis and characterisation of the compounds). | S02-SI |
| F11 | Feng, H. et al. J. Clin. Invest. 2011, 121 (8), 3159-3175 (CUHK study of CCRK/CDK20 in HCC; full text). | S08 |
| W23 | Wang, L. et al. Pharmaceuticals 2023, 16 (2), 253 (narrative review; full text; searches to Dec 2022). | S03 |
| J21 | Jumper, J. et al. Nature 2021, 596, 583-589 (AlphaFold method; full text). | S04 |
| I23 | Ivanenkov, Y. A. et al. J. Chem. Inf. Model. 2023, 63 (3), 695-701 (Chemistry42 platform; full text; same company as R23). | S05 |
| B26 | Bender, A. et al. Nat. Rev. Drug Discov. 2026 (Perspective; public abstract only). | S07 |
| L07 | Lengauer, T. Bioinformatics - From Genomes to Therapies, Vol. 1, Ch. 1, Wiley-VCH 2007, pp 1-24 (public chapter; printed page given). | S10 |
| NCI | National Cancer Institute, Liver and Bile Duct Cancer web page. | S01 |
| GPI | SCIE1007 Group Project Introduction slides (Topic 10 = slides 45-49). Course material, not a scientific source. | T01 |
| T1 / T2 | SCIE1007 Tutorial 1 / Tutorial 2 notes and worksheets. | T01 |
| E## | Row number in 资料准备_CDK20/证据清单.csv (the fact-checked evidence list). | - |

## Part 1 · Beat sheet

| # | Section | Time | Speakers (words) | What it does | Key facts | Serves | ON-CAM beats |
|---|---|---|---|---|---|---|---|
| S1 | Hook: Worth testing? | 00:00–01:20 | A 35, B 47, C 44, D 34 | Grab attention with the cost/time/failure problem, the 2024 Nobel link, and the Hong Kong angle; all four members on camera in the first minute. | 10-17 yrs, ~US$2.8 B, ~1 in 10 reach market (Wang 2023); Nobel 2024 / AlphaFold | Audience (why it matters); Teamwork (all 4 on camera in first 80 s) | 1-01 A, 1-03 D, 1-04 B, 1-05 C |
| S2 | Introduction: why it matters, question, objectives, method | 01:20–04:27 | A 195, C 61, D 107 | Daily-life and local relevance; state the research question, the two Tutorial 1 objectives, the literature-review method and how sources were judged; give the overview. | Primary liver cancer 6th most common, 3rd in cancer deaths; HCC ~75% (GLOBOCAN 2020 via Ren 2023); CUHK / Prince of Wales Hospital (Feng 2011); Insilico HK, Science Park (Ren 2023) | Structure (intro + overview); Literature (source types + evaluation); Audience (daily life, Hong Kong) | 2-05 A, 2-07 C |
| S3 | Background: the lock, the key, and why CDK20 | 04:27–06:40 | B 93, D 189 | Explain protein / target / candidate / selectivity with the lock-and-key analogy first, then the evidence for CDK20 (Hong Kong 2011 study + AI target ranking), and the 'no picture of the lock' problem. | Lock-and-key, selectivity (Lengauer 2007); CDK20 higher in 36/52 HCC, later stage, shorter survival, knock-down slows growth (Feng 2011); 10 data sets, 1,133 + 674 samples, top 20, no structure, no approved drugs (Ren 2023) | Audience (analogy then term); Content (target evidence); Critical thinking (link is not proof) | 3-01 D, 3-06 D, 3-09 B |
| S4 | Methods: four computer tools (Objective 1) | 06:40–09:42 | A 138, B 255 | Objective 1. Walk through structure prediction (with the low-confidence tail fix), generative design (with platform filters), docking/virtual screening and clustering, then summarise the four tools. | Few proteins measured; AlphaFold confidence; tail 303-346 with Arg305 in ATP pocket removed, 1-302 kept; Chemistry42, hinge Met84, filters; 8,918 → docking + clustering → 54 → 7 | Objective 1; Content (methods); Visual aids (real AlphaFold model) | 4-04 B, 4-10 A |
| S5 | Results: from 8,918 designs to one candidate (Objective 2 evidence) | 09:42–12:25 | C 291, D 27 | The case story with numbers: first hit 001 in 30 days (binding but weak blocking), second round to 048 (binding, enzyme and cell results), with each number's meaning and boundary. | 001 Kd 9.2 µM, 30 days, enzyme IC50 > 6 µM; round 2: 16 → 6 within 30 days; 048 Kd 566.7 nM (~15x), IC50 33.4 nM; Huh7 208.7 vs HEK293 1,706.7 nM | Objective 2 evidence; Content (numbers with meaning and limits) | 5-02 C, 5-06 C, 5-10 C |
| S6 | Evaluation: benefits and limits (Objective 2 judgement) | 12:25–14:59 | B 135, D 189 | Place the results on an evidence ladder; separate shown benefits from possible ones across health/economic/ethical/environmental angles; give four concrete limits (prediction error, no fair comparison, cells vs people, independence). | Ladder stops at cells; no animal / human data; novel core (Fig. 2); benefits possible but unmeasured; limits: prediction error, no fair comparison, cells vs people (ADME, selectivity), independence (COI; Bender 2026) | Objective 2 judgement; Critical thinking (four limits); Topic 10 'benefits' (4 angles) | 6-02 D, 6-05 D, 6-09 B |
| S7 | Future directions | 14:59–16:02 | A 124 | Three concrete, testable suggestions that answer the limits: a fair benchmark, stronger biology for 048, and checking the model against experiment with feedback of failures. | Fair benchmark; stronger biology for 048; compare with measured structure and feed back failures | Critical thinking (multiple future directions) | 7-01 A |
| S8 | Conclusion: answering the question | 16:02–17:33 | A 15, B 13, C 116, D 12 | Answer the research question, judge how well each objective was met, give two take-home messages (what computers do / how to read 'AI drug' headlines) and close with all four members on camera. | Four tools; objective 1 met for this case; objective 2 partly met; two take-home messages | Structure (conclusion back to objectives); Audience (take-home, daily life); Teamwork | 8-01 C, 8-04 C, 8-05 B, 8-06 D, 8-07 A |

Proportions (Tutorial 2 gives about 30 / 50 / 20 as a rough guide): introduction S1–S2 is 25% of the runtime, body S3–S5 45%, evaluation and conclusion S6–S8 with the end card 29%. Tutorial 2 (p.13) puts definitions, background and analogies in the introduction; counted that way (S1–S3) the introduction is 38% and the body S4–S5 33%. The tilt toward evaluation is deliberate: Content and Critical Thinking reward it.

## Part 2 · Speaker balance

| Member | Role | Words | Time at 130 wpm | Time, conservative | Share | ON-CAM moments | Sections with ON-CAM |
|---|---|---|---|---|---|---|---|
| A | Opener and guide: hook question, research question, plan, docking and the tool summary, future directions, final line. | 507 | 03:54 | 04:09 | 24% | 5: 1-01, 2-05, 4-10, 7-01, 8-07 | S1, S2, S4, S7, S8 |
| B | Methods lead: target ranking by AI, structure prediction and the tail fix, generative design and filters, the four limits. | 543 | 04:11 | 04:10 | 26% | 5: 1-04, 3-09, 4-04, 6-09, 8-05 | S1, S3, S4, S6, S8 |
| C (female voice) | Results lead: objectives, the 001 and 048 story with all key numbers, the answer to the research question. | 512 | 03:56 | 04:19 | 24% | 7: 1-05, 2-07, 5-02, 5-06, 5-10, 8-01, 8-04 | S1, S2, S5, S8 |
| D | Concepts and judgement: sources and how we judged them, lock-and-key, why CDK20, the evidence ladder, benefits. | 558 | 04:18 | 04:23 | 26% | 6: 1-03, 3-01, 3-06, 6-02, 6-05, 8-06 | S1, S3, S6, S8 |

Every member is on camera in the first 80 seconds and again in the closing relay, plus at least two more times in between. C carries the results section, which is the centre of the film, and the answer to the research question.

## Part 3 · Full script

### S1 · Hook: Worth testing? · 00:00–01:20 · lead A

*Grab attention with the cost/time/failure problem, the 2024 Nobel link, and the Hong Kong angle; all four members on camera in the first minute.*

**1-01 · 00:00–00:08 · A · ON-CAM** (16 words)

> Before anyone makes a new medicine, could a computer tell us which molecule is worth making?

- Visual: [CAM] A at the plain wall, tripod, eye-level medium close-up, graded to high-contrast mono so the wall sinks toward black; one bone-white ink stroke underlines "worth making?".
- Source: Our framing question (no fact)

**1-02 · 00:08–00:18 · A · VO** (19 words)

> It matters, because making a new drug is slow, expensive and risky. A 2023 review puts it in numbers.

- Visual: [INK] one long horizontal pen stroke draws a drug's timeline across black; [TD] a thin vessel flow trickles along it and keeps stalling.
- Source: W23 p.1

**1-03 · 00:18–00:21 · D · ON-CAM** (9 words)

> It can take more than ten to seventeen years...

- Visual: [CAM] D; ink numerals "10-17 yrs" scrawl beside him; footnote "Wang et al., 2023".
- Source: W23 p.1

**1-04 · 00:21–00:28 · B · ON-CAM** (14 words)

> ...and almost 2.8 billion US dollars to bring one new drug into clinical use.

- Visual: [CAM] B; ink "~US$2.8 billion" scrawled beside him.
- Source: W23 p.1 (paper writes "dollars"; "US" is our reading, see flag F1)

**1-05 · 00:28–00:35 · C · ON-CAM** (14 words)

> And only about one in ten compounds tested in clinical trials reaches the market.

- Visual: [CAM] C; ten ink dots drawn beside her, nine fade out.
- Source: W23 p.1

**1-06 · 00:35–00:46 · D · VO** (25 words)

> Every drug behind those numbers started with an early choice: which molecule to make and test first? That's where computers are now trying to help.

- Visual: [TD] one vessel branches into thousands of capillaries (possible molecules); a single branch is picked out in cyan ink.
- Source: L07 p.13 (computers asked to suggest a small set of promising candidates)

**1-07 · 00:46–01:02 · B · VO** (33 words)

> In 2024, part of the Nobel Prize in Chemistry went to Demis Hassabis and John Jumper, who led the team behind AlphaFold: a program that predicts a protein's 3D shape from its sequence.

- Visual: [3D] the real AlphaFold CDK20 ribbon assembles out of [TD] flow lines; hand-drawn ink medal outline (no photo); caption "Nobel Prize in Chemistry 2024".
- Source: GPI slide 48 (citing nobelprize.org press release); J21 author list

**1-08 · 01:02–01:16 · C · VO** (30 words)

> In this video, we follow one real case: AI tools, including AlphaFold, hunting for a liver cancer drug candidate. And part of this story begins right here in Hong Kong.

- Visual: [INK] Hong Kong coastline in a few strokes; [TD] a vessel line runs from Sha Tin to Pak Shek Kok → TITLE CARD (4 s): "WORTH TESTING? How computers help find cancer drug candidates: the CDK20 story" + section / group / member names.
- Source: R23 Abstract; F11 affiliations; R23 affiliation b

`[01:16–01:20] Title card 4 s (no speech)`

### S2 · Introduction: why it matters, question, objectives, method · 01:20–04:27 · lead A

*Daily-life and local relevance; state the research question, the two Tutorial 1 objectives, the literature-review method and how sources were judged; give the overview.*

**2-01 · 01:20–01:39 · A · VO** (40 words)

> First, why liver cancer? Cancer that starts in the liver itself is called primary liver cancer. Worldwide, it's the sixth most common cancer and the third biggest cause of cancer deaths, according to 2020 figures quoted in our main paper.

- Visual: [INK] an anatomical liver in bone-white line on black, its vessels then filled by vermilion [TD] flow; [2D] "6th most common / 3rd in cancer deaths (GLOBOCAN 2020, cited in Ren et al. 2023)".
- Source: R23 'Target selection and identification' (citing GLOBOCAN 2020 / IARC); flag F2

**2-02 · 01:39–01:53 · A · VO** (27 words)

> The most common type is hepatocellular carcinoma, or HCC: about three quarters of cases. And the paper says there's still a huge unmet need for better treatment.

- Visual: [INK] liver cells sketched as a honeycomb; three quarters of an ink ring fills; label "HCC ~75%".
- Source: R23 'Target selection and identification'; NCI (E01)

**2-03 · 01:53–02:16 · A · VO** (45 words)

> Now, the Hong Kong link. In 2011, a team at the Chinese University of Hong Kong studied liver tumours from patients operated on at the Prince of Wales Hospital. They found a protein called CCRK, also known as CDK20, raised in many of these tumours.

- Visual: [INK] a generic hospital outline (no logo) and sample tubes; [2D] "CCRK = CDK20"; footnote Feng et al., 2011.
- Source: F11 affiliations; Methods 'Patients and clinical specimens'; Results/Fig. 10; R23 ('also known as CCRK')

**2-04 · 02:16–02:26 · A · VO** (17 words)

> And the 2023 AI study lists co-authors at Insilico Medicine's Hong Kong office, in the Science Park.

- Visual: [INK] Science Park skyline in a few strokes; [2D] the affiliation line typed exactly as printed in the paper.
- Source: R23 author affiliation b

**2-05 · 02:26–02:36 · A · ON-CAM** (18 words)

> So our research question is: how can computer-aided methods help scientists find and assess potential cancer drug candidates?

- Visual: [CAM] A; the question types itself in bone-white beneath the frame.
- Source: Our research question (Tutorial 1)

**2-06 · 02:36–02:42 · A · VO** (11 words)

> We answer it with one case study: CDK20 in liver cancer.

- Visual: [2D] strip "A case study of CDK20 in liver cancer".
- Source: -

**2-07 · 02:42–02:45 · C · ON-CAM** (5 words)

> We set ourselves two objectives.

- Visual: [CAM] C; ink numerals "1" and "2" appear beside her.
- Source: Tutorial 1 worksheet

**2-08 · 02:45–02:59 · C · VO** (24 words)

> One: to identify the major computer-aided methods used in cancer drug discovery. Two: to evaluate how these methods help scientists assess potential drug candidates.

- Visual: [2D] both objectives in clean type with an ink underline; they shrink into corner tags that return in Sections 4, 5 and 8.
- Source: Tutorial 1 objectives as submitted

**2-09 · 02:59–03:18 · C · VO** (32 words)

> Our method was a literature review. We didn't run any software or experiments ourselves. Our main source is one original research paper: Ren and colleagues, Chemical Science, 2023, with its supplementary data.

- Visual: [INK] outline of the paper's first page with a legible title; ink stamp "original research"; full citation as footnote.
- Source: R23; R23-SI

**2-10 · 03:18–03:35 · D · VO** (33 words)

> Around it, we used the earlier Hong Kong study, the papers behind two AI tools, a 2023 review, a textbook chapter, and a 2026 expert Perspective, of which we read only the abstract.

- Visual: [INK] six cards fan out from the main paper, each tagged by type: original study / method paper x2 / review / book chapter / Perspective (abstract only).
- Source: F11; J21; I23; W23; L07; B26 (abstract only)

**2-11 · 03:35–03:50 · D · VO** (37 words)

> We judged every source in two ways. First: what kind of source is it, and how much did we actually read? Second: how strong is the evidence? Were there controls and repeat tests? Who did the work?

- Visual: [INK] two hand-drawn magnifying glasses pass over the cards; ticks appear.
- Source: Tutorial 1 worksheet Q9; T2 notes p.5

**2-12 · 03:50–04:07 · D · VO** (37 words)

> For example, most authors of our main paper work for Insilico Medicine, the company behind the AI platforms they used. The paper says so openly. That doesn't make the results wrong, but it isn't an independent check.

- Visual: [2D] the paper's "Conflicts of interest" heading typed, with a neutral ink bracket.
- Source: R23 affiliations and 'Conflicts of interest' (E28, E29)

**2-13 · 04:07–04:25 · A · VO** (37 words)

> Here's the plan. First, what a drug target is, and why CDK20. Then the computer methods, step by step, and the lab results. Finally, we weigh up benefits and limits, suggest future research, and answer our question.

- Visual: [TD] one main vessel splits into five labelled branches: Target / Methods / Results / Benefits & limits / Answer; this map returns as a corner icon at each section start.
- Source: T2 notes p.14 (overview of the body)

`[04:25–04:27] 2 s music breath`

### S3 · Background: the lock, the key, and why CDK20 · 04:27–06:40 · lead D

*Explain protein / target / candidate / selectivity with the lock-and-key analogy first, then the evidence for CDK20 (Hong Kong 2011 study + AI target ranking), and the 'no picture of the lock' problem.*

**3-01 · 04:27–04:31 · D · ON-CAM** (10 words)

> To follow this story, picture a lock and a key.

- Visual: [CAM] D; an ink keyhole sketches itself on the wall beside him.
- Source: L07 p.12

**3-02 · 04:31–04:45 · D · VO** (38 words)

> Inside our cells, proteins do much of the work. Most drugs act by sticking tightly to one protein and changing what it does. The drug fits into a pocket on the protein, like a key in a lock.

- Visual: [INK] a cell outline zooms to a protein drawn as an ink blob with a pocket; a small key-shaped molecule slides in (labelled "schematic").
- Source: L07 p.7, p.12

**3-03 · 04:45–05:08 · D · VO** (47 words)

> This lock-and-key idea is over a century old. In drug discovery, the lock is the target: the protein we want to affect. The key is a candidate molecule. A good key fits its own lock tightly and doesn't open other locks. That second part is called selectivity.

- Visual: [INK] LOCK → "target (a protein)", KEY → "candidate (a small molecule)"; a second, different lock rejects the key → "selectivity".
- Source: L07 p.7, p.12 (Emil Fischer's lock-and-key principle) (E34, E35)

**3-04 · 05:08–05:23 · D · VO** (31 words)

> Our lock is CDK20. It's an enzyme, a protein that does a chemical job in the cell. Its keyhole is a pocket where it normally grabs a small molecule called ATP.

- Visual: [3D] the real AlphaFold CDK20 model (AF-Q8IZL9-F1) as a grey ribbon, slowly rotating; ATP pocket ringed in ink; tag "predicted model".
- Source: R23 ('CDK20 as a promising target'; ATP pocket; kinase activity assay)

**3-05 · 05:23–05:47 · D · VO** (45 words)

> Why this lock? Remember the Hong Kong team. In 52 liver tumours compared with matching non-tumour tissue, CDK20 was higher in 36. Patients with high levels tended to have later-stage tumours and shorter survival. And lowering CDK20 in liver cancer cells made them grow less.

- Visual: [2D] 52 ink tally marks, 36 filled in ("69%"); arrows to "later stage" and "shorter survival"; [INK] cells dividing less once CDK20 is dimmed (schematic). No invented curves.
- Source: F11 Results, Fig. 10, Table 1; knock-down results (E31, E32)

**3-06 · 05:47–05:55 · D · ON-CAM** (18 words)

> But a link is not proof. CDK20 is one possible lock, not the single cause of liver cancer.

- Visual: [CAM] D.
- Source: T2 notes p.8 (correlation is not causation); E02

**3-07 · 05:55–06:16 · B · VO** (41 words)

> In the 2023 study, an AI platform called PandaOmics helped pick the lock. It pooled ten liver cancer data sets, with more than a thousand tumour samples and hundreds of healthy controls, added evidence from research papers, and ranked possible targets.

- Visual: [TD] ten thin data streams flow like vessels into one channel (cyan = computation); [2D] "10 data sets / 1,133 tumour / 674 healthy".
- Source: R23 'Target selection and identification'; Methods 'Target ID' (E08)

**3-08 · 06:16–06:31 · B · VO** (34 words)

> People then filtered that ranking and reviewed the top 20 by hand. CDK20 came out on top: a strong link to liver cancer, no approved drugs aimed at it, and no lab-measured 3D structure.

- Visual: [INK] a hand-written list of 20 rows; a pen circles CDK20; three ticks appear beside it.
- Source: R23 Introduction; 'Target selection and identification'; Methods (first-in-class criteria)

**3-09 · 06:31–06:38 · B · ON-CAM** (18 words)

> That last point was the problem. How do you design a key without a picture of the lock?

- Visual: [CAM] B.
- Source: R23 Abstract ('novel target without an experimental structure')

`[06:38–06:40] 2 s music breath`

### S4 · Methods: four computer tools (Objective 1) · 06:40–09:42 · lead B

*Objective 1. Walk through structure prediction (with the low-confidence tail fix), generative design (with platform filters), docking/virtual screening and clustering, then summarise the four tools.*

**4-01 · 06:40–06:54 · B · VO** (28 words)

> Usually, a protein's shape is measured in difficult lab experiments, and only a small fraction of known proteins have been measured. So the first tool is structure prediction.

- Visual: Corner tag "Objective 1 / Tool 1"; [INK] a grid of protein outlines, most left blank; a crystal sketch with a question mark.
- Source: R23 Introduction; T2 notes p.6

**4-02 · 06:54–07:12 · B · VO** (45 words)

> Think of a protein as a long chain of beads that folds into a 3D shape. The order of the beads is its sequence. AlphaFold learned from known structures how sequences fold, so it can predict a shape and give each part a confidence score.

- Visual: [INK] a bead chain (one dot per residue) folds into the real CDK20 ribbon [3D]; the ribbon recolours by AlphaFold confidence (pLDDT).
- Source: J21 (E06); R23 Introduction (pLDDT confidence metric)

**4-03 · 07:12–07:33 · B · VO** (45 words)

> The team downloaded CDK20's predicted structure from the public AlphaFold database. Most of it had high confidence. But a tail at one end had very low confidence, and in the model, it blocked the keyhole: one of its building blocks sat inside the ATP pocket.

- Visual: [3D] real model AF-Q8IZL9-F1; the C-terminal tail (Pro303-Gly346) in low-confidence orange ink; Arg305 highlighted inside the pocket; camera pushes in.
- Source: R23 'Generation of novel hits...', Fig. 4A (E09)

**4-04 · 07:33–07:38 · B · ON-CAM** (14 words)

> So the scientists cut the tail off. The computer's guess needed a human check.

- Visual: [CAM] B; an ink scissors doodle snips across the frame edge.
- Source: R23 Fig. 4A text

**4-05 · 07:38–07:49 · B · VO** (21 words)

> They kept building blocks 1 to 302 and removed the rest. A predicted structure is a useful model, not a photograph.

- Visual: [3D] the tail dissolves into [TD] particles that drain away like blood flow; the opened pocket is outlined in ink.
- Source: R23 (Met1-Ile302 used as input) (E09)

**4-06 · 07:49–08:08 · B · VO** (38 words)

> Next, imagine not searching a drawer of existing keys, but cutting brand-new ones for this keyhole. That's the second tool: generative design. The team used a platform called Chemistry42, which runs dozens of AI models side by side.

- Visual: Corner tag "Tool 2"; [INK] a drawer of old keys slides shut; [TD] dozens of parallel cyan flow lines each draw molecule skeletons in ink.
- Source: R23; I23 (ensemble of 40+ generative models) (E07, E10)

**4-07 · 08:08–08:18 · B · VO** (24 words)

> They gave it the pocket's shape and size, and one rule: every design must grip one particular spot in the pocket, called the hinge.

- Visual: [3D] pocket surface as ink wireframe; hinge residue Met84 marked with an ink pin "must bind here".
- Source: R23 (pocket-based generation; hinge Met84 defined as required binding point)

**4-08 · 08:18–08:37 · B · VO** (40 words)

> The platform also has built-in filters. They throw out designs with reactive, unstable or possibly toxic chemical groups, and score how drug-like each design is and how easy it is to make. These are early computer checks, not safety tests.

- Visual: [INK] a sieve: skeletons fall through; ones carrying flagged groups are struck out; small tags "drug-like? easy to make?".
- Source: I23 (medicinal-chemistry filters, drug-likeness, synthetic accessibility); R23 does not say which filters were on, flag F4

**4-09 · 08:37–09:01 · A · VO** (54 words)

> All this produced 8,918 new designs, far too many to make in a lab. So the team tried each key in a virtual lock. That's the third tool, docking: the computer predicts how each molecule might sit in the pocket and scores the fit. Doing this for a big batch is called virtual screening.

- Visual: Corner tag "Tool 3"; [2D] "8,918" large and clear; [TD] a wave sweeps across a wall of 8,918 ink dots, brightening some.
- Source: R23 (8,918; docking) (E11); L07 p.13 (docking definition); W23 Sec. 4.1 (virtual screening = docking + scoring)

**4-10 · 09:01–09:04 · A · ON-CAM** (10 words)

> But a good docking score is a clue, not proof.

- Visual: [CAM] A.
- Source: E10, E11

**4-11 · 09:04–09:18 · A · VO** (29 words)

> The team also grouped similar designs together, which is called clustering, so they could pick a varied set. They shortlisted 54, and chemists chose just seven to actually make.

- Visual: [TD] dots drift into clusters; 54 pull forward; 7 redrawn in heavy ink; [2D] funnel 8,918 → 54 → 7.
- Source: R23 (54 with diverse hinge cores; 7 selected for synthesis); Author contributions (E11, E26)

**4-12 · 09:18–09:40 · A · VO** (45 words)

> So, for our first objective, this case used four computer tools: mining disease data to pick a target, predicting the protein's shape, generating new molecules, and docking to rank them. Our course notes list others, like molecular dynamics, but this study doesn't report using them.

- Visual: [2D] summary card: four ink icons (data stream / folded ribbon / key-cutting / key-in-lock); greyed second row "molecular dynamics / quantum mechanics (not reported here)".
- Source: R23; GPI slide 47

`[09:40–09:42] 2 s music breath`

### S5 · Results: from 8,918 designs to one candidate (Objective 2 evidence) · 09:42–12:25 · lead C

*The case story with numbers: first hit 001 in 30 days (binding but weak blocking), second round to 048 (binding, enzyme and cell results), with each number's meaning and boundary.*

**5-01 · 09:42–10:00 · C · VO** (37 words)

> So, did any of the seven work? The team tested whether each one actually sticks to CDK20. Grip is measured as Kd: roughly, how much molecule it takes to grab half of the protein. Lower means tighter.

- Visual: Corner tag "Objective 2 / Results"; [INK] the seven real skeletons redrawn from Ren Fig. 5 in a row; a simple ink gauge "Kd: lower = tighter".
- Source: R23 Results, Fig. 5; Methods 'binding assay'

**5-02 · 10:00–10:04 · C · ON-CAM** (10 words)

> One of the seven stood out. Its name is 001.

- Visual: [CAM] C; ink "001" written beside her.
- Source: R23 Results

**5-03 · 10:04–10:24 · C · VO** (36 words)

> 001 bound CDK20 with a Kd of 9.2 micromolar: a real lab measurement, not a computer score. The paper reports this first hit took 30 days, counting from choosing the target, through design, making and testing.

- Visual: [3D] 001 rebuilt from its published 2D structure (Ren Fig. 5) in the paper's predicted pose (Fig. 6B), tagged "predicted pose"; [2D] "Kd = 9.2 ± 0.5 µM (n = 3)"; ink calendar "30 days".
- Source: R23 Abstract, Results, Conclusions, Fig. 6 (E13, E14)

**5-04 · 10:24–10:37 · C · VO** (32 words)

> Thirty days sounds fast. But it's 30 days to a first binder, not to a medicine. And with no comparison group working without AI, we can't say how much faster it was.

- Visual: [INK] a long ruler "10-17 years"; a tiny bracket at its start marked "30 days = first binding hit".
- Source: E13, E25; W23 p.1

**5-05 · 10:37–11:00 · C · VO** (46 words)

> Another catch: sticking to a lock isn't the same as jamming it. A second test asked how well 001 blocks CDK20's actual work. That's IC50: the amount needed to cut the enzyme's activity by half. Lower is better. For 001, it was above 6 micromolar. Weak.

- Visual: [INK] the key in the lock tries to turn, ink wobble lines; [2D] "Enzyme IC50 > 6 µM".
- Source: R23 Results (IC50 > 6,000 nM) (E15)

**5-06 · 11:00–11:04 · C · ON-CAM** (10 words)

> The key went into the lock. But it barely turned.

- Visual: [CAM] C.
- Source: E15

**5-07 · 11:04–11:21 · C · VO** (40 words)

> So the team used what it had learned. Lab data, plus the computer's guess of how 001 sat in the pocket, guided a second round: sixteen new designs, six made and tested, all within 30 days of the first hit.

- Visual: [TD] a loop vessel carries data from a lab icon back to the design node (circulation); [2D] "Round 2: 16 designed → 6 tested (within 30 days of first hit)".
- Source: R23 Results; Conclusions (E17)

**5-08 · 11:21–11:31 · C · VO** (16 words)

> One of them, 048, gripped about fifteen times more tightly: a Kd of about 570 nanomolar.

- Visual: [3D] 048 rebuilt from its published 2D structure (Ren Fig. 7) in its predicted pose (Fig. 8B); the new hydrogen bond to Lys33 drawn as an ink dash; [2D] "Kd 566.7 ± 256.2 nM (~15x tighter than 001)"; side note "049: 360.0 ± 14.1 nM, an even tighter binder, but only 048 was tested further in the paper".
- Source: R23 Results, Figs. 7-8 (E18, E19)

**5-09 · 11:31–11:40 · C · VO** (14 words)

> In the enzyme test, 048 cut CDK20's activity by half at just 33.4 nanomolar.

- Visual: [2D] "Enzyme IC50 = 33.4 ± 22.6 nM (n = 3)"; [INK] the key turns fully.
- Source: R23 Fig. 9A (E20)

**5-10 · 11:40–11:41 · C · ON-CAM** (5 words)

> This time, the key turned.

- Visual: [CAM] C.
- Source: E20

**5-11 · 11:41–12:08 · C · VO** (45 words)

> Then came living cells. After three days with 048, they measured a signal from living cells. In Huh7 liver cancer cells, which carry lots of CDK20, that signal halved at about 210 nanomolar. A comparison cell line, HEK293, needed about 1,700: roughly eight times more.

- Visual: [INK] two dishes of hand-drawn cells (labelled schematic), Huh7 thinning sooner than HEK293; [2D] bars "208.7 vs 1,706.7 nM"; footnote "~8x = our calculation".
- Source: R23 Results, Fig. 9B, Methods 'Cell viability assay' (E21); '8x' is our arithmetic, flag F5

**5-12 · 12:08–12:23 · D · VO** (27 words)

> So 048 hit these liver cancer cells harder. But HEK293 cells aren't normal liver cells, and one cell test can't prove the effect comes only from CDK20.

- Visual: [INK] arrows from 048 to "CDK20 only?" and "other proteins?" with question marks.
- Source: E21; T2 notes p.7

`[12:23–12:25] 2 s music breath`

### S6 · Evaluation: benefits and limits (Objective 2 judgement) · 12:25–14:59 · lead D

*Place the results on an evidence ladder; separate shown benefits from possible ones across health/economic/ethical/environmental angles; give four concrete limits (prediction error, no fair comparison, cells vs people, independence).*

**6-01 · 12:25–12:48 · D · VO** (48 words)

> Let's put the evidence on a ladder. Step one: computer predictions. Two: binding the protein. Three: blocking the enzyme. Four: effects in cells. 048 has reached step four. Steps five and six, animals and patients, are empty: the study reports no animal or human tests of these molecules.

- Visual: [INK] a ladder drawn bottom-up; rungs 1-4 fill with tiny icons (ribbon, key-in-lock, turning key, cells); rungs 5-6 stay dashed, labelled "not reported".
- Source: R23 Results, Conclusions, Methods (E23, E33)

**6-02 · 12:48–12:54 · D · ON-CAM** (11 words)

> So 048 is a drug candidate. It is not a medicine.

- Visual: [CAM] D.
- Source: E23

**6-03 · 12:54–13:07 · D · VO** (29 words)

> So what are the benefits? Our course notes suggest four angles: health, money, ethics and the environment. For each, we separate what this case shows from what's only possible.

- Visual: [2D] four-panel ink grid: Health / Economic / Ethical / Environmental, each split "shown | possible, not measured".
- Source: GPI slide 49

**6-04 · 13:07–13:32 · D · VO** (49 words)

> What it shows: design could start without a lab-measured structure of CDK20. The AI proposed genuinely new molecules: 048's core looks quite different from earlier CDK20 inhibitors. Only seven designs were made in round one, and six in round two. And a first binding hit came in 30 days.

- Visual: "Shown" column fills with ink ticks; [3D] 048 beside the outline of a previously reported CDK20 inhibitor (from Ren Fig. 2, labelled).
- Source: R23 Abstract, Fig. 2 (novel scaffold, low similarity) (E09-E13)

**6-05 · 13:32–13:37 · D · ON-CAM** (14 words)

> That's a smarter search. But is it a cheaper one? We don't know yet.

- Visual: [CAM] D.
- Source: E25

**6-06 · 13:37–13:55 · D · VO** (38 words)

> In theory, searches like this could mean fewer failed molecules, lower costs, fewer animal tests and less chemical waste, and one day, new treatments. But this study measured none of that. And computing has its own cost: electricity.

- Visual: "Possible" column: items drawn in dashed ink (not measured); [TD] a power-line flow pulses into a server icon.
- Source: GPI slide 49; E25

**6-07 · 13:55–14:10 · B · VO** (34 words)

> But there are real limits too. First, predictions can be wrong: we saw AlphaFold put a tail in the keyhole. Docking poses are guesses too, and a high score doesn't guarantee a working drug.

- Visual: [INK] the earlier tail and a docked pose redrawn in dashed lines with a "predicted" stamp.
- Source: E09, E10; L07 p.13

**6-08 · 14:10–14:22 · B · VO** (28 words)

> Second, there was no fair race. No matched team worked on the same target without AI. So please don't divide 8,918 by seven and call it a speed-up.

- Visual: [INK] a race track with only one runner; "8,918 / 7" written, then crossed out.
- Source: E11, E25

**6-09 · 14:22–14:25 · B · ON-CAM** (8 words)

> Third: cells in a dish are not people.

- Visual: [CAM] B.
- Source: T2 notes p.7; E23

**6-10 · 14:25–14:39 · B · VO** (34 words)

> We don't yet know how a body would absorb, spread and break down 048, whether it's toxic, or whether it hits other proteins too. The authors list some of these checks as next steps.

- Visual: [INK] a schematic human outline with blank organs and question marks; tags "ADME? / selectivity? / toxicity?".
- Source: R23 Results (last paragraph), Conclusions: ADME and kinase selectivity as next steps (E23)

**6-11 · 14:39–14:57 · B · VO** (31 words)

> Fourth, independence: the company that built the platforms ran this study. And a 2026 expert Perspective says evidence of AI making a real difference for patients is, so far, disappointingly limited.

- Visual: [2D] one-line paraphrase of the Bender 2026 abstract with an ink bracket "(abstract only)".
- Source: E28; B26 abstract (E27)

`[14:57–14:59] 2 s music breath`

### S7 · Future directions · 14:59–16:02 · lead A

*Three concrete, testable suggestions that answer the limits: a fair benchmark, stronger biology for 048, and checking the model against experiment with feedback of failures.*

**7-01 · 14:59–15:03 · A · ON-CAM** (10 words)

> So what should scientists do next? We suggest three things.

- Visual: [CAM] A; ink numerals 1-3 appear beside him.
- Source: -

**7-02 · 15:03–15:19 · A · VO** (40 words)

> One: run a fair race. Give an AI route and a conventional route the same target, the same budget and the same definition of a hit, agreed in advance. Then record time, cost and failures, not just the best result.

- Visual: [INK] two lanes from one start line; stopwatch, coin and cross icons tallied along each.
- Source: Our proposal (T2 worksheet Q3); B26 abstract (benchmarks should test better decisions); E30

**7-03 · 15:19–15:41 · A · VO** (39 words)

> Two: test 048 much harder, in more liver cancer cell types and in normal liver cells. Check whether the effect disappears when CDK20 is removed. Measure selectivity and how the body handles it, and only then consider animal studies.

- Visual: [INK] a grid of dishes multiplying; a CDK20 ribbon fades from one dish (knock-down test); ADME icons.
- Source: Our proposal (T2 worksheet Q3); R23 (ADME and selectivity listed as next steps)

**7-04 · 15:41–16:00 · A · VO** (35 words)

> Three: check the model against reality. When a lab-measured structure of CDK20 is available, compare it with the AlphaFold prediction. And feed every lab result, including the failures, back into the next round of design.

- Visual: [3D] predicted ribbon overlaid with an empty dashed "measured structure?" ghost; [TD] a loop vessel returns dim "failed" particles to the design node.
- Source: Our proposal; E09, E30; T2 notes p.16

`[16:00–16:02] 2 s music breath`

### S8 · Conclusion: answering the question · 16:02–17:33 · lead C

*Answer the research question, judge how well each objective was met, give two take-home messages (what computers do / how to read 'AI drug' headlines) and close with all four members on camera.*

**8-01 · 16:02–16:04 · C · ON-CAM** (5 words)

> So, back to our question.

- Visual: [CAM] C.
- Source: -

**8-02 · 16:04–16:30 · C · VO** (52 words)

> How can computer-aided methods help find and assess cancer drug candidates? In the CDK20 case, they helped at four points: picking a target from data, predicting its shape, designing new molecules, and ranking which to make. That meets our first objective for this case, though not for every method in cancer research.

- Visual: [TD] the five-branch map returns; the four tool icons light in turn; the Objective 1 tag gets an ink tick "(for this case)".
- Source: Summary of R23; T2 worksheet Q1

**8-03 · 16:30–16:53 · C · VO** (48 words)

> For our second objective: these methods helped narrow 8,918 ideas down to a handful of real molecules, reach a confirmed binder in 30 days, and improve it in a second round. What they haven't shown is how much time or money they save, or whether patients will benefit.

- Visual: [2D] one continuous ink stroke: 8,918 → 54 → 7 → 001 → 048; the ladder icon stops at rung 4; Objective 2 tag: tick + "partly".
- Source: R23 (E11, E13, E17-E21, E25)

**8-04 · 16:53–16:59 · C · ON-CAM** (11 words)

> Computers make the search smarter. Experiments still have the final say.

- Visual: [CAM] C.
- Source: -

**8-05 · 16:59–17:04 · B · ON-CAM** (13 words)

> So next time you see a headline like 'AI discovers a cancer drug'...

- Visual: [CAM] B; a hand-drawn phone outline with a blank headline bar (no real outlet's branding).
- Source: T2 worksheet Q5

**8-06 · 17:04–17:10 · D · ON-CAM** (12 words)

> ...ask how far the evidence got: computer, protein, cells, animals, or patients?

- Visual: [CAM] D; the ink ladder overlays the frame edge.
- Source: T2 worksheet Q5

**8-07 · 17:10–17:18 · A · ON-CAM** (15 words)

> And early lab results alone are no reason to change anyone's treatment. Thanks for watching.

- Visual: [CAM] A → 2x2 grid of all four talking heads on black (shot separately, composited) → END CARD.
- Source: T2 worksheet Q5

`[17:18–17:33] End card 15 s: references, credits, AI-use statement (no speech)`

## Part 4 · End card (15 s, no speech)

**References** (ACS style, as the Tutorial notes suggest)

1. Ren, F.; Ding, X.; Zheng, M.; Korzinkin, M.; Cai, X.; Zhu, W.; Mantsyzov, A.; Aliper, A.; Aladinskiy, V.; Cao, Z.; et al. AlphaFold Accelerates Artificial Intelligence Powered Drug Discovery: Efficient Discovery of a Novel CDK20 Small Molecule Inhibitor. *Chem. Sci.* **2023**, *14* (6), 1443–1452. DOI: 10.1039/D2SC05709C. (Including its Electronic Supplementary Information.)
2. Feng, H.; Cheng, A. S. L.; Tsang, D. P.; Li, M. S.; Go, M. Y.; Cheung, Y. S.; Zhao, G.-J.; Ng, S. S.; Lin, M. C.; Yu, J.; Lai, P. B.; To, K. F.; Sung, J. J. Y. Cell Cycle–Related Kinase Is a Direct Androgen Receptor–Regulated Gene That Drives β-Catenin/T Cell Factor–Dependent Hepatocarcinogenesis. *J. Clin. Invest.* **2011**, *121* (8), 3159–3175. DOI: 10.1172/JCI45967.
3. Wang, L.; Song, Y.; Wang, H.; Zhang, X.; Wang, M.; He, J.; Li, S.; Zhang, L.; Li, K.; Cao, L. Advances of Artificial Intelligence in Anti-Cancer Drug Design: A Review of the Past Decade. *Pharmaceuticals* **2023**, *16* (2), 253. DOI: 10.3390/ph16020253.
4. Jumper, J.; Evans, R.; Pritzel, A.; Green, T.; Figurnov, M.; Ronneberger, O.; Tunyasuvunakool, K.; Bates, R.; Žídek, A.; Potapenko, A.; et al. Highly Accurate Protein Structure Prediction with AlphaFold. *Nature* **2021**, *596* (7873), 583–589. DOI: 10.1038/s41586-021-03819-2.
5. Ivanenkov, Y. A.; Polykovskiy, D.; Bezrukov, D.; Zagribelnyy, B.; Aladinskiy, V.; Kamya, P.; Aliper, A.; Ren, F.; Zhavoronkov, A. Chemistry42: An AI-Driven Platform for Molecular Design and Optimization. *J. Chem. Inf. Model.* **2023**, *63* (3), 695–701. DOI: 10.1021/acs.jcim.2c01191.
6. Bender, A.; Thomas, M. C.; Scannell, J. W.; Shaywitz, D. A.; Ghiandoni, G. M.; Greener, J. G.; et al. Artificial Intelligence in Drug Discovery — What It Is, Where We Stand and the Path Forward. *Nat. Rev. Drug Discov.* **2026**. DOI: 10.1038/s41573-026-01496-2. (Published online 7 Aug 2026; abstract consulted.)
7. Lengauer, T. Bioinformatics — From Genomes to Therapies. In *Bioinformatics — From Genomes to Therapies*; Lengauer, T., Ed.; Wiley-VCH: Weinheim, 2007; Vol. 1, pp 1–24. DOI: 10.1002/9783527619368.ch1.
8. National Cancer Institute. Liver and Bile Duct Cancer. https://www.cancer.gov/types/liver (accessed 2026-10-03).

Course material: SCIE1007 Group Project Introduction, slides 45–49 (HKBU, 2026), including the Nobel Prize in Chemistry 2024 press release cited there (nobelprize.org).

**Data and image credits.** CDK20 predicted structure AF-Q8IZL9-F1, AlphaFold Protein Structure Database (EMBL-EBI and Google DeepMind); state the model version you actually render (the paper used model_v1). Molecule drawings and poses redrawn from Ren et al. 2023, Figs. 2 and 4–9. Music: titles and artists as used.

**Generative AI acknowledgement (draft; edit so it matches what the team really did).** "We used generative AI tools ([name the tools]) to help organise our reading notes, draft and edit this script, translate it for team discussion and plan visuals. Every fact and number was checked by our team against the original sources listed above. All narration is spoken by our team members; no AI voice-over was used." Add any AI-generated images, video or music here as well.

## Part 5 · Lip-sync and timing safety valves

- Film each ON-CAM line three times. Record the on-set sound as a guide track even if the final voice is re-recorded; re-record VO and ON-CAM lines in one quiet room with one microphone so the four voices match.
- If the rough cut runs **under 15:30**: hold the title card and the six music breaths longer, and let key visuals breathe (8,918 wall, tail removal, evidence ladder). Do not add new facts.
- If it runs **over 19:00**, drop in this order: 2-04 (Insilico Hong Kong office), the second sentence of 4-12 (other methods), the last sentence of 6-06 (electricity). Each cut is self-contained and saves about 20 seconds in total.

## Part 6 · If the team has five members

The latest message ("four people… four men, one woman") is ambiguous. If there are five, keep C as the female voice and add E. Each member then speaks about 420–430 words (about 3:15–3:30). To keep everyone at 3.5 minutes or more, the team can restore cut material and let the film run to about 18–18:30.

| Beats moving to E | From | Words | Why it fits |
|---|---|---|---|
| 2-01, 2-02, 2-06 | A | 78 | E opens the introduction with why liver cancer matters |
| 3-07, 3-08, 3-09 | B | 93 | E becomes the voice of the data: AI target ranking |
| 6-11 | B | 31 | E gives the fourth limit (independence), echoing E's source-evaluation part |
| 2-07, 2-08, 2-09 | C | 61 | E states the objectives and the method |
| 5-04 | C | 32 | E adds the caveat on the 30 days |
| 2-10, 2-11, 2-12 | D | 107 | E explains the sources and how we judged them |
| 6-03 | D | 29 | E frames the four benefit angles |

Resulting words: A 429, B 419, C 419, D 422, E 431.

E's ON-CAM moments (at least four, spread out): 2-07 "We set ourselves two objectives."; split 2-01 so E says "First, why liver cancer?" on camera; 3-09 "How do you design a key without a picture of the lock?"; 6-11 opening "Fourth: independence." on camera; and in the closing relay E says "…ask how far the evidence got," while D finishes "computer, protein, cells, animals, or patients?". After the move, A keeps 5 ON-CAM moments, B 4 (1-04, 4-04, 6-09, 8-05), C 6 and D 6.

## Part 7 · Flags: uncertain or simplified points

| Flag | Beat | Note |
|---|---|---|
| F1 | 1-04 | Wang 2023 writes "almost 2.8 billion dollars" with no currency. Reading it as US dollars is ours (and it cites references we have not read). If unsure, say "almost 2.8 billion dollars" and show "$2.8 billion". |
| F2 | 2-01, 2-02 | "6th most common, 3rd in cancer deaths" and "HCC about 75%" are GLOBOCAN 2020 figures quoted second-hand in Ren 2023; we did not open GLOBOCAN. No Hong Kong incidence figures are used because none were verified in our files. |
| F3 | 1-07 | The Nobel fact comes from course slide 48, which cites the nobelprize.org press release; we did not open the release. "Part of the prize" because David Baker shared it. That Hassabis and Jumper led AlphaFold rests on the author list of Jumper et al. 2021. |
| F4 | 4-08 | The filters (reactive / unstable / possibly toxic groups, drug-likeness, ease of synthesis) are described in the Chemistry42 platform paper. Ren 2023 does not say which filters or scores were switched on for the CDK20 run, so the line says what the platform has, not what this run filtered. The platform paper is by the same company. |
| F5 | 5-08, 5-11 | Speech rounds 566.7 to "about 570", 208.7 to "about 210" and 1,706.7 to "about 1,700"; the screen shows exact values with ± SD. "Roughly eight times" is our arithmetic (1,706.7 / 208.7 ≈ 8.2), not the paper's wording, and the HEK293 value has a large spread (± 670.0 nM). |
| F6 | 2-12, 6-11 | "Most authors work for Insilico Medicine": 21 of the 24 authors list Insilico Shanghai or Hong Kong; two of the others are declared Insilico advisors (Conflicts of interest section). |
| F7 | 6-11 | Bender 2026 was read as a public abstract only. "Disappointingly limited" is a two-word quote from that abstract; the rest is paraphrase. |
| F8 | 1-08, 2-04 | The paper does not say which steps were done in the Hong Kong office, so the script only says co-authors are based there. |
| F9 | 3-02, 3-03 | "Most drugs act by sticking tightly to one protein" and the century-old lock-and-key idea come from a 2007 textbook chapter. They are used as general principles, not as current statistics. |
| F10 | 4-02 | Simplified: AlphaFold also uses related sequences and templates, not only learned structures (Jumper 2021). |
| F11 | 5-03, 5-07 | "30 days" runs from target selection to the first confirmed binder (001). It does not include building the platforms, and round 2 took up to another 30 days. |
| F12 | 5-02 | The paper reports one binder among the seven compounds; it does not give the other six results, so the script says 001 "stood out", not that six failed. |
| F13 | visuals | The paper gives 2D structures and predicted poses as figures, not coordinate files. Any 3D model of 001 or 048 is our reconstruction from Figs. 5 and 7 and should be labelled as such. Check the AlphaFold DB terms and credit line before rendering. |
| F14 | whole film | Only this 2023 study is described. We have not checked whether newer CDK20 results exist (2024–2026); the script never claims there are none. |

Not used, by choice: the Lab Experiment 2 link ("we added a drug to cancer cells in our own lab") would be a strong audience hook, but its notes were not in the agreed source list. Add it only after checking those notes.
