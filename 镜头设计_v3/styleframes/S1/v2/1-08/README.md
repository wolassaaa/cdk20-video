# 1-08 · Time, money, one in ten (C, VO, 01:00–01:16)

Script (script_v3.3 1-08): "Start the search the year we were born, and it might only be ready now. It can cost almost 2.8 billion US dollars. And of drugs tested in people, only about one in ten reaches the market."

"The year we were born" is shown as 2006 and "now" as 2026 (members are about 19–20). All on-screen wording is taken from the line above.

| Option | Idea | Why it fits | Draws on | Tool |
|---|---|---|---|---|
| opt1_fog-glass (a-time, b-one-in-ten) | A fogged window at night with blurred blue city lights and two red ones. (a) "2006 → 2026" and "US$2.8B" are wiped into the condensation with a finger, and drips run down. (b) Ten finger tally strokes; only one stroke lines up with a red light behind the glass. | It is personal and human (someone counting years on a window) and was on the director's liked list (writing on fogged glass). Red against blue. | Gerhard Richter's blurred photo-paintings; the fogged-glass reference board | Blender Cycles (mask-driven frosted glass, DOF) + PIL mask + Remotion captions |
| opt2_led-counter | A dark wall of LED counters. Big red seven-segment digits read 2,800,000,000, with blue counters "2006 —— 2026" below and a field of small ghost counters around. | Money and time become counters, and the idea animates naturally (digits roll up). It is a cold, machine-like contrast to opt1. | Tatsuo Miyajima (LED counters, *Counter Void*) | Blender + Remotion |
| opt3_cost-stair | 20 columns of blue glass cubes, one per year from 2006 to 2026. Each cube is US$10M and the columns are a running total, so the last column (280 cubes) is US$2.8 billion. A red line runs along the years. | Time and money in one object, which grows as we grow up. Marked ILLUSTRATIVE (even spend per year is assumed). | Felix Gonzalez-Torres (counted mass as meaning, candy spills); Minimalist stacks | Blender + Remotion |
| opt4_ten-vials | Ten glass vials lit blue from behind on a mirror floor. Nine hold clouded grey liquid and one holds vermilion. A header strip carries the time and money facts. | One image answers "one in ten" at a glance. | Damien Hirst-style lab vitrines, toned down; lab glass | Blender + Remotion |
| opt5_swiss-ledger (a, b, c) | Restrained Swiss typography in three frames: 2006 → 2026 on a 20-tick rule; US$2.8 BILLION beside a 70×40 grid of 2,800 blue squares (US$1M each); ten circles, one red. | It is the clean fallback and the most accurate scale reading. Kept flat on purpose, because the type is the idea. | Josef Müller-Brockmann / Swiss style | Remotion |

## Code
- Blender: `_code/s108/road3d.py --scene fog|counter|stair|vials`; fog masks: `_code/s108/fogmask.py`.
- Remotion: `src/v3/s1v2/s108/` comps `C-FogTime`, `C-FogTally`, `C-Counter`, `C-Stair`, `C-Vials`, `C-LedgerTime`, `C-LedgerMoney`, `C-LedgerTen`.
- Dropped drafts: `C-DotYears` (the dots merged into a slab) and `C-Growth` (door-frame height marks; the type collided and it read as a 2D chart).
