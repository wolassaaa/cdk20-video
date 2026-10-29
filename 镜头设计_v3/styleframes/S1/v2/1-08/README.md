# 1-08 · Time, money, one in ten (C, VO, 01:00–01:16)

Script (script_v3.3 1-08): "Start the search the year we were born, and it might only be ready now. It can cost almost 2.8 billion US dollars. And of drugs tested in people, only about one in ten reaches the market."

"The year we were born" is shown as 2006 and "now" as 2026 (members are about 19–20). All on-screen wording comes from the line above.

**Colour (fix pass 10-31):**
- Every plate is rendered with the Standard view transform. Red is crimson (#E8102A in Blender, #FF1A2E in overlays).
- Median G/R on red pixels is 0.11–0.18 (limit 0.35).

| Option | Idea | Why it fits | Draws on | Tool |
|---|---|---|---|---|
| opt1_fog-glass (a-time, b-one-in-ten) | A fogged window, near-black, lit by a single soft blue source behind it. Finger-wiped strokes read clear and glowing. (a) "2006 → 2026" and "US$2.8B" with drips. (b) Ten tally strokes; one stroke alone is red (a red light sits behind only that stroke), and it is the only red in the frame. | It is personal and human, and fogged-glass writing was on the director's liked list. The single source avoids the "police lights" read of v1. | Gerhard Richter's blurred photo-paintings; the fogged-glass reference board | Blender (mask-driven frosted glass, DOF) + PIL mask (`fogmask.py`) + Remotion captions |
| opt2_led-counter | A dark wall of seven-segment counters. Crimson 2,800,000,000 sits above blue "2006 —— 2026", with a field of ghost counters around. | Money and time become counters that animate naturally. | Tatsuo Miyajima (*Counter Void*, LED counters) | Blender + Remotion |
| opt3_cost-stair | 20 columns of blue glass cubes, one per year. Each cube is US$10M and the columns are a running total, so the last one (280 cubes) is US$2.8 billion. A red line runs along the years. | Time and money in one object. ILLUSTRATIVE, because even spend per year is assumed. | Felix Gonzalez-Torres (counted mass); Minimalist stacks | Blender + Remotion |
| opt4_ten-vials | Ten glass vials against black, rim-lit blue from the sides. Nine hold clouded grey liquid and one is crimson. The bright blue blocks at the vial tops are gone: there is now a black backdrop and the back light was removed. | "One in ten" reads at a glance. | Lab vitrines | Blender + Remotion |
| opt5_swiss-ledger (a, b, c) | A restrained Swiss typographic fallback: 2006 → 2026 on a 20-tick rule; US$2.8 BILLION beside 2,800 blue squares (US$1M each); ten circles, one red. | It is the most exact scale reading. Kept flat on purpose, because the type is the idea. | Josef Müller-Brockmann | Remotion |

Dropped:
- **fog-glass v1**: red and blue bokeh read as police lights.
- **`C-DotYears`**: the dots merged into a slab.
- **`C-Growth`**: door-frame height marks; the type collided.

## Code
- **Blender:** `_code/s108/road3d.py --scene fogblue|counter|stair|vials`.
- **Remotion comps:** `C-FogBlueTime`, `C-FogBlueTally`, `C-Counter`, `C-Stair`, `C-Vials`, `C-LedgerTime`, `C-LedgerMoney`, `C-LedgerTen`.
