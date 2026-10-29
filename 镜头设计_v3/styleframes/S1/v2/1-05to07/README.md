# 1-05 to 1-07 · 00:52–01:00 · D asks, B answers, C caps it

The lines (script v3.3): D "So... why not just make a better one?" / B "Because that's way harder than it sounds." / C "Like, ten-to-seventeen-years hard." (Source W23 p.1)

Every layout uses the real card (`v3/oncam/Card.jsx`, frozen in its grown state and placed with an outer transform) with `placeholder_hand.mp4`. Each option has three frames: `_1-05_D`, `_1-06_B`, `_1-07_C`. On-screen quotes and the bottom beat tag are only for layout review; drop them in the edit. Built in Remotion (the tool split puts on-cam cards in Remotion): `src/v3/s1v2/s104/Talk.jsx`.

| Option | Layout and eye-line | 10–17 YEARS device at C's line |
|---|---|---|
| **opt1_corner-relay** | Each print stays in its own corner (A's corner stays empty, marked "A · OFF"). The speaker's print grows and leans in while the others dim and shrink. A thin ink arc runs from the speaker to the person addressed (D→B, then B→D). | The timeline (`TimelineG`: the same ink line, ticks and bracket as the existing `PropTimeline`, lettered in Inter Tight + Martian Mono) is pulled out of C's print and runs through the gap between B's and D's prints. |
| **opt2_table** | The three prints are dropped on a black table, tilted toward the empty centre and overlapping. The speaker's print is lifted to the top. It reads like a conversation among photographs. | The timeline (`TimelineG`) is laid across all three prints like a ruler. |
| **opt3_conversation-line** | Strict three-up split screen, C · B · D, staggered by corner (B high), all on one hairline at eye height. A vermilion tick on the line points to the person addressed. | A strip of 17 small date-painting panels (years 1–17, with 10–17 painted vermilion) runs under all three prints. After On Kawara's date paintings. Grotesk lettering, the same type system as the other three. |
| **opt4_shot-reverse** | Classic shot/reverse-shot: the speaker fills their half and the other two shrink to chips in their own corners, with a short ink eye-line from the chip. It is closest to the existing card system and the cheapest to cut. | The timeline (`TimelineG`) is pulled out across the empty half, between B's and D's chips. |

## 10-31 fix pass
- The Knewave "10–17 YEARS" lettering is gone from opt1, opt2 and opt4. `TimelineG` in `Talk.jsx` keeps the hand-inked line from `oncam/props.jsx` but sets the lettering in Inter Tight 700 + Martian Mono numerals, so all four layouts share one type system. `oncam/props.jsx` itself is untouched.
- The red is crimson-biased (`#F5142B`), matching the 1-04 red pass.
