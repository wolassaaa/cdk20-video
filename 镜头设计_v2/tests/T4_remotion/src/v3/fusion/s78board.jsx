// HKBU SCIE1007 coursework science video. Storyboard sketch for S7 and S8 (15:15-17:10): twelve panels drawn as flat line art on the bone table.
// It follows 镜头设计_v3/styleframes/art/fusion/s7s8/00_S7S8分镜_v1.md. Sketch only: the real shots reuse the Blender table, the 3D inserts and the phone footage.
// Render: npx remotion bundle src/v3/fusion/s78board.jsx --out-dir=<dir> --public-dir=<镜头设计_v3/remotion_public>, then still S78Board.
import React from "react";
import {registerRoot, Composition, AbsoluteFill, staticFile, continueRender, delayRender} from "remotion";

const INK = "#111113", SOFT = "#545458", RED = "#E8190F", KLEIN = "#002FA7", BONE = "#EDEBE4", GREY = "#9A9AA0";
const SERIF = "Instrument Serif", SANS = "Inter Tight", HAND = "Caveat";
const faces = [new FontFace(SERIF, `url(${staticFile("fusion_s1/fonts/InstrumentSerif-Regular.ttf")})`), new FontFace(SERIF, `url(${staticFile("fusion_s1/fonts/InstrumentSerif-Italic.ttf")})`, {style: "italic"}), new FontFace(SANS, `url(${staticFile("fusion_s1/fonts/InterTight.ttf")})`, {weight: "100 900"}), new FontFace(HAND, `url(${staticFile("fusion_s1/fonts/Caveat.ttf")})`, {weight: "400 700"})];
const fontHandle = delayRender("fonts");
Promise.all(faces.map(f => f.load())).then(l => { l.forEach(f => document.fonts.add(f)); continueRender(fontHandle); });

const PW = 1920, PH = 1080;
const T = ({x, y, s = 40, f = SANS, c = INK, a = "start", w = 500, i, children}) => <text x={x} y={y} fontSize={s} fontFamily={f} fill={c} textAnchor={a} fontWeight={f === SANS ? w : 400} fontStyle={i ? "italic" : "normal"}>{children}</text>;
const Note = p => <T f={HAND} c={RED} s={54} w={600} {...p}/>;

/** The six-sphere route. fill is how many stations are red (3.5 = half of the fourth). */
const Route = ({x = 160, y = 540, w = 1600, fill = 3.5, r = 46, labels = true, dashFrom = 4}) => {
  const gap = w / 5, xr = x + gap * (fill - 0.5) + (fill % 1 ? r * 0 : 0);
  const names = ["Target", "Hit", "Improve", "Cells & animals", "Clinical trials", "Approval"];
  return <g>
    <rect x={x - 60} y={y - 14} width={w + 120} height={28} rx={14} fill="#E2E0D8" stroke="#C9C7BF"/>
    <rect x={x - 60} y={y - 14} width={Math.max(0, xr - x + 60)} height={28} rx={14} fill={RED}/>
    {names.map((n, k) => {
      const cx = x + gap * k, full = k + 1 <= fill, half = !full && k < fill;
      return <g key={k}>
        <circle cx={cx} cy={y} r={r} fill={full ? RED : "#F4F3EE"} stroke={k >= dashFrom ? GREY : INK} strokeWidth={4} strokeDasharray={k >= dashFrom ? "10 9" : "none"}/>
        {half && <path d={`M${cx} ${y - r} A${r} ${r} 0 0 0 ${cx} ${y + r} Z`} fill={RED}/>}
        {labels && <T x={cx} y={y + r + 50} s={30} a="middle" w={600}>{n}</T>}
      </g>;
    })}
  </g>;
};

const Print = ({x, y, w = 520, h = 624, who}) => <g>
  <rect x={x + 10} y={y + 14} width={w} height={h} fill="#00000018"/>
  <rect x={x} y={y} width={w} height={h} fill="#FBFAF6" stroke="#D6D3CA"/>
  <rect x={x + 26} y={y + 26} width={w - 52} height={h - 120} fill="#E6DFD3"/>
  <circle cx={x + w / 2} cy={y + h * 0.36} r={w * 0.13} fill="#C9B9A4"/>
  <path d={`M${x + w * 0.24} ${y + h - 94} Q${x + w / 2} ${y + h * 0.48} ${x + w * 0.76} ${y + h - 94} Z`} fill="#C9B9A4"/>
  <T x={x + w / 2} y={y + h - 38} s={30} a="middle" w={600} c={SOFT}>{who} · on camera</T>
</g>;

const Dish = ({x, y, tint}) => <g><ellipse cx={x} cy={y} rx={54} ry={20} fill={tint ? "#F3C9C4" : "#F4F3EE"} stroke={INK} strokeWidth={3}/><ellipse cx={x} cy={y - 6} rx={54} ry={20} fill="none" stroke={GREY} strokeWidth={2}/></g>;
const Key = ({x, y, s = 1, c = "#D9D4C7"}) => <g transform={`translate(${x} ${y}) scale(${s})`}><circle cx={0} cy={0} r={22} fill={c} stroke={INK} strokeWidth={3}/><rect x={20} y={-7} width={70} height={14} fill={c} stroke={INK} strokeWidth={3}/><rect x={70} y={6} width={10} height={16} fill={c} stroke={INK} strokeWidth={3}/></g>;
const Lock = ({x, y, s = 1, dashed}) => <path transform={`translate(${x} ${y}) scale(${s})`} d="M-150 40 C-170 -80 -60 -150 20 -130 C120 -150 180 -40 150 50 C130 140 20 160 -40 140 C-110 130 -140 100 -150 40 Z M-10 -20 L40 -20 L40 30 L10 60 L-10 30 Z" fill={dashed ? "none" : KLEIN} fillRule="evenodd" stroke={dashed ? GREY : "none"} strokeWidth={5} strokeDasharray={dashed ? "16 12" : "none"}/>;
const Watch = ({x, y, hand = 40}) => { const a = hand * Math.PI / 180; return <g><rect x={x - 12} y={y - 92} width={24} height={20} fill={INK}/><circle cx={x} cy={y} r={70} fill="#F4F3EE" stroke={INK} strokeWidth={6}/><line x1={x} y1={y} x2={x + 52 * Math.sin(a)} y2={y - 52 * Math.cos(a)} stroke={RED} strokeWidth={6} strokeLinecap="round"/><circle cx={x} cy={y} r={7} fill={INK}/></g>; };
const Tick = ({x, y, s = 1}) => <path transform={`translate(${x} ${y}) scale(${s})`} d="M0 20 L22 44 L70 -20" fill="none" stroke={RED} strokeWidth={9} strokeLinecap="round" strokeLinejoin="round"/>;
const Corner = ({n, done}) => <g><rect x={1450} y={60} width={380} height={64} fill="none" stroke={INK} strokeWidth={2}/><T x={1474} y={104} s={32} w={600}>Objective {n}</T>{done && <Tick x={1700} y={70} s={0.9}/>}{done && <Note x={1600} y={190} s={48}>(for this case)</Note>}</g>;
const Src = ({children}) => <T x={60} y={1050} s={24} c={SOFT}>{children}</T>;

const P = [
  ["7-01 · 15:15 · A on camera", "A holds up three fingers; the red pen writes 1, 2, 3 on the empty table where the three next steps will land.", <>
    <Print x={120} y={200} who="A"/>
    <Note x={900} y={560} s={150}>1</Note><Note x={1260} y={560} s={150}>2</Note><Note x={1620} y={560} s={150}>3</Note>
  </>],
  ["7-02 · 15:18 · next step one", "Same route as the end of S6. A red flag on station 4; its empty half gets a dashed red ring, \"next\". Nothing is filled in that has not been done.", <>
    <Route fill={3.5}/>
    <line x1={1120} y1={494} x2={1120} y2={300} stroke={INK} strokeWidth={5}/><path d="M1120 300 L1240 330 L1120 360 Z" fill={RED}/>
    <circle cx={1120} cy={540} r={64} fill="none" stroke={RED} strokeWidth={4} strokeDasharray="12 10"/>
    <Note x={1210} y={440} s={56}>next</Note>
    <T x={1000} y={260} s={96} f={SERIF} c={RED}>048</T>
    <Src>Illustration · Ren 2023 (Results, Conclusions)</Src>
  </>],
  ["7-02 · 15:26 · cells, then animals (3D insert)", "Dishes double in two rows; a pen drawing of a mouse further on; two tags with pen glosses. A small \"public\" stamp by the 048 tag.", <>
    {[0, 1, 2, 3, 4, 5].map(k => <Dish key={k} x={260 + k * 140} y={330} tint/>)}
    {[0, 1, 2, 3, 4, 5].map(k => <Dish key={k} x={260 + k * 140} y={520}/>)}
    <T x={200} y={250} s={34} w={600}>liver cancer cells</T><T x={200} y={440} s={34} w={600}>normal liver cells</T>
    <path d="M1260 420 C1300 360 1420 350 1480 400 C1520 380 1560 400 1550 430 C1600 440 1600 470 1560 470 L1290 470 C1250 470 1240 440 1260 420 Z M1290 470 C1240 500 1200 470 1180 500" fill="none" stroke={INK} strokeWidth={4}/>
    <T x={1260} y={560} s={34} w={600}>then animals</T>
    <T x={200} y={720} s={40} w={700}>ADME</T><Note x={360} y={720} s={46}>how the body handles it</Note>
    <T x={200} y={810} s={40} w={700}>selectivity</T><Note x={440} y={810} s={46}>what else it hits</Note>
    <rect x={1300} y={700} width={240} height={90} fill="none" stroke={RED} strokeWidth={5} transform="rotate(-6 1420 745)"/><T x={1420} y={762} s={46} a="middle" c={RED} w={800}>public</T>
    <Src>Illustration · Ren 2023 (Conclusions) · GEN 2023</Src>
  </>],
  ["7-03 · 15:37 · next step two", "The blue predicted CDK20 from S4 stands on the table; beside it the same shape as a grey dashed ghost: \"measured structure?\"", <>
    <Lock x={620} y={560} s={1.5}/><T x={620} y={860} s={36} a="middle" w={600}>predicted</T>
    <Lock x={1300} y={560} s={1.5} dashed/><T x={1240} y={860} s={36} a="middle" w={600} c={SOFT}>measured structure</T><Note x={1420} y={862} s={70}>?</Note>
    <Note x={160} y={180} s={120}>2</Note>
    <Src>Illustration · AlphaFold DB AF-Q8IZL9-F1 v6</Src>
  </>],
  ["7-03 · 15:44 · failures go back in (3D insert)", "The 4-09 bin of tossed keys tips over; the keys roll back along the belt into the AI screen, whose ring lights once.", <>
    <rect x={300} y={300} width={520} height={330} rx={16} fill={KLEIN}/>{[0, 1, 2].map(k => <circle key={k} cx={420 + k * 140} cy={465} r={44} fill="none" stroke={k === 1 ? "#FFFFFF" : "#5D7FD6"} strokeWidth={k === 1 ? 10 : 6}/>)}
    <rect x={820} y={700} width={760} height={30} fill="#CFCBC0" stroke={INK} strokeWidth={2}/>
    <path d="M1500 560 L1700 600 L1680 760 L1520 740 Z" fill="#D7D3C9" stroke={INK} strokeWidth={4} transform="rotate(-28 1600 660)"/>
    {[0, 1, 2, 3].map(k => <Key key={k} x={1000 + k * 120} y={670} s={0.8}/>)}
    {[0, 1, 2, 3].map(k => <circle key={k} cx={1090 + k * 120} cy={652} r={14} fill={RED}/>)}
    <path d="M1460 620 C1300 560 1000 560 840 620" fill="none" stroke={RED} strokeWidth={4} strokeDasharray="14 10" markerEnd="url(#arr)"/>
    <Note x={900} y={530} s={52}>every result, failures too</Note>
  </>],
  ["7-04 · 15:50 · next step three (stopwatches 3D)", "Pen draws one start line and two lanes. Both stopwatches start; the finish is dashed with a question mark: nobody has run this race yet.", <>
    <line x1={300} y1={330} x2={300} y2={760} stroke={RED} strokeWidth={8}/>
    <line x1={300} y1={470} x2={1600} y2={470} stroke={INK} strokeWidth={3}/><line x1={300} y1={620} x2={1600} y2={620} stroke={INK} strokeWidth={3}/><line x1={300} y1={760} x2={1600} y2={760} stroke={INK} strokeWidth={3}/>
    <line x1={1600} y1={330} x2={1600} y2={780} stroke={GREY} strokeWidth={6} strokeDasharray="16 12"/><Note x={1650} y={590} s={110}>?</Note>
    <Watch x={420} y={545} hand={70}/><Watch x={420} y={690} hand={70}/>
    <T x={540} y={560} s={40} w={600}>AI route</T><T x={540} y={705} s={40} w={600}>classic route</T>
    <T x={300} y={260} s={66} f={SERIF}><tspan fontStyle="italic">same</tspan> target · same budget · same definition of a hit</T>
    <rect x={300} y={274} width={112} height={6} fill={RED}/>
    <Note x={160} y={180} s={120}>3</Note>
    <Src>Our proposal · Bender 2026 (abstract)</Src>
  </>],
  ["16:02 · two-second breath", "The camera rises: everything from S1 to S7 is still lying on the one table, the route across the middle.", <>
    <Route x={300} y={560} w={1320} fill={3.5} r={30} labels={false}/>
    <rect x={160} y={160} width={260} height={180} fill="#FBFAF6" stroke="#D6D3CA"/><rect x={520} y={140} width={200} height={140} fill="#E7C9C2"/>
    <Lock x={900} y={260} s={0.6}/><rect x={1180} y={170} width={220} height={150} rx={10} fill={KLEIN}/>
    {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(k => <rect key={k} x={260 + k * 26} y={760} width={14} height={140} rx={7} fill="none" stroke={INK} strokeWidth={2}/>)}
    <Key x={800} y={820} s={0.9}/><Watch x={1200} y={840} hand={130}/><Watch x={1380} y={840} hand={130}/>
    <rect x={1560} y={720} width={180} height={220} fill="#FBFAF6" stroke="#D6D3CA"/>
  </>],
  ["8-01 / 8-02 · 16:04 · four points (C)", "Back to the question card from S2. Four old objects slide beside the first stations, each with a pen word; Objective 1 gets a drawn tick.", <>
    <rect x={160} y={110} width={1180} height={150} fill="#FBFAF6" stroke="#D6D3CA"/>
    <T x={200} y={175} s={44} f={SERIF}>How can computer-aided methods help scientists</T><T x={200} y={228} s={44} f={SERIF}>find and assess cancer drug candidates?</T>
    <Route x={240} y={720} w={1400} fill={3.5} r={36} labels={false}/>
    {[0, 1, 2, 3, 4].map(k => <rect key={k} x={180 + k * 22} y={430} width={12} height={120} rx={6} fill="none" stroke={INK} strokeWidth={2}/>)}
    <Note x={160} y={620} s={44}>target from data</Note>
    <Lock x={600} y={490} s={0.55}/><Note x={500} y={620} s={44}>the lock's shape</Note>
    <Key x={860} y={480}/><Note x={830} y={620} s={44}>new keys</Note>
    <rect x={1120} y={400} width={36} height={150} rx={18} fill="#2A2A2E"/><rect x={1180} y={430} width={36} height={120} rx={18} fill="#BDBDC2"/><Note x={1100} y={620} s={44}>ranking</Note>
    <Corner n={1} done/>
    <Src>Ren 2023 · T2 worksheet Q1</Src>
  </>],
  ["8-03 · 16:27 · objective two", "One red pen line: \"millions\", an arrow, 13 ink dots, \"13\". Then along the route: the first stretch measured as 30 days against 10-17 years.", <>
    <T x={200} y={330} s={110} f={SERIF}>millions</T>
    <path d="M700 300 L900 300" stroke={RED} strokeWidth={7}/><path d="M880 280 L910 300 L880 320" fill="none" stroke={RED} strokeWidth={7}/>
    {Array.from({length: 13}, (_, k) => <circle key={k} cx={980 + (k % 7) * 50} cy={270 + Math.floor(k / 7) * 54} r={14} fill={INK}/>)}
    <T x={1380} y={330} s={110} f={SERIF}>13</T>
    <Route x={240} y={720} w={1400} fill={3.5} r={36} labels={false}/>
    <path d="M240 800 L240 830 L520 830 L520 800" fill="none" stroke={RED} strokeWidth={5}/><Note x={250} y={900} s={48}>first hit in 30 days</Note>
    <path d="M240 600 L240 570 L1640 570 L1640 600" fill="none" stroke={SOFT} strokeWidth={3}/><T x={940} y={550} s={34} a="middle" c={SOFT} w={600}>10–17 years</T>
    <Corner n={2} done/>
    <Src>Ren 2023 · Wang 2023 p.1</Src>
  </>],
  ["8-05 · 16:51 · B on camera", "B holds up a hand like a phone; the pen draws a phone beside the print with a plain headline bar. No real outlet's logo or font.", <>
    <Print x={160} y={200} who="B"/>
    <rect x={1050} y={190} width={380} height={700} rx={50} fill="none" stroke={RED} strokeWidth={7}/><rect x={1090} y={330} width={300} height={130} fill="none" stroke={RED} strokeWidth={4}/>
    <text x={1240} y={385} fontFamily={HAND} fontSize={40} fill={RED} textAnchor="middle" fontWeight={600}>AI discovers</text><text x={1240} y={432} fontFamily={HAND} fontSize={40} fill={RED} textAnchor="middle" fontWeight={600}>a cancer drug</text>
    {[0, 1, 2, 3].map(k => <line key={k} x1={1100} y1={520 + k * 50} x2={1380} y2={520 + k * 50} stroke={RED} strokeWidth={3} opacity={0.5}/>)}
  </>],
  ["8-06 · 16:56 · D taps five points", "Each tap lights one place on the route with a pen word. 048's red stops at \"cells\", so viewers see the answer for themselves.", <>
    <Print x={90} y={70} w={360} h={432} who="D"/>
    <Route x={620} y={800} w={1150} fill={3.5} r={40} labels={false}/>
    {[["computer", 735], ["protein", 850], ["cells", 1278], ["animals", 1322], ["patients", 1540]].map(([wd, x], k) => <g key={k}><line x1={x} y1={746} x2={x} y2={690 - (k % 2) * 70} stroke={RED} strokeWidth={3}/><Note x={x + (k === 2 ? -10 : k === 3 ? 10 : 0)} y={676 - (k % 2) * 70} s={50} a={k === 2 ? "end" : k === 3 ? "start" : "middle"}>{wd}</Note></g>)}
    <T x={1230} y={930} s={70} f={SERIF} c={RED} a="middle">048</T>
  </>],
  ["8-07 · 17:03 · thanks, then the end card", "Four prints slide in from the four sides into a 2×2 with small gaps; the camera pushes down onto a blank sheet that becomes the W5 end card.", <>
    <Print x={500} y={70} w={430} h={440} who="A"/><Print x={990} y={70} w={430} h={440} who="B"/><Print x={500} y={570} w={430} h={440} who="C"/><Print x={990} y={570} w={430} h={440} who="D"/>
    <rect x={1560} y={600} width={300} height={400} fill="#F6F5F0" stroke="#D6D3CA"/><Note x={1560} y={570} s={44}>→ end card sheet</Note>
  </>],
];

const Panel = ({p: [title, cap, body], x, y, w}) => {
  const h = w * PH / PW;
  return <g transform={`translate(${x} ${y})`}>
    <svg x={0} y={0} width={w} height={h} viewBox={`0 0 ${PW} ${PH}`}>
      <defs><marker id="arr" markerWidth="10" markerHeight="10" refX="6" refY="5" orient="auto"><path d="M0 0 L10 5 L0 10 Z" fill={RED}/></marker></defs>
      <rect width={PW} height={PH} fill={BONE}/>{body}
    </svg>
    <rect x={0} y={0} width={w} height={h} fill="none" stroke="#B8B6AE" strokeWidth={2}/>
    <text x={0} y={h + 46} fontFamily={SANS} fontSize={32} fontWeight={700} fill={INK}>{title}</text>
    <foreignObject x={0} y={h + 60} width={w} height={120}><div style={{fontFamily: SANS, fontSize: 25, lineHeight: 1.3, color: SOFT}}>{cap}</div></foreignObject>
  </g>;
};

const SW = 3840, SH = 3740;
const S78Board = () => {
  const cols = 3, w = 1180, gx = (SW - cols * w) / (cols + 1), rowH = w * PH / PW + 210;
  return <AbsoluteFill style={{background: "#FFFFFF"}}>
    <svg width={SW} height={SH}>
      <text x={gx} y={110} fontFamily={SERIF} fontSize={84} fill={INK}>S7 · S8 storyboard v1 <tspan fontStyle="italic" fill={SOFT}>(sketch)</tspan></text>
      <text x={gx} y={165} fontFamily={SANS} fontSize={30} fill={SOFT}>HKBU SCIE1007 coursework video · 15:15–17:10 · old objects come back on the one table; next steps stay dashed</text>
      {P.map((p, k) => <Panel key={k} p={p} x={gx + (k % cols) * (w + gx)} y={220 + Math.floor(k / cols) * rowH} w={w}/>)}
    </svg>
  </AbsoluteFill>;
};

const Root = () => <Composition id="S78Board" component={S78Board} durationInFrames={1} fps={30} width={SW} height={SH}/>;
registerRoot(Root);
