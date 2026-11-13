// ---------------------------------------------------------------- S6 (12:44-15:15): the scorecard on the table, then the road. HKBU SCIE1007 coursework science video.
// make_s6_jsx.py puts this after entry.jsx's shared parts (fonts, Ink, Note, Keyed, Print, Source...) into s6.jsx; entry.jsx is read, never changed.
// The picture under it is bl_s6.py's take. Its camera comes in s6_track.json (eye, look-at, lens per frame at 30 fps), so every word here is placed in table units,
// measured from the board's middle, and drawn where that point lands on screen, at the size the table has there. Times are seconds on the film's clock.
const S6 = TRK6.T, G6 = TRK6.geo;
const S6_LINES = [
  [764.0, "6-01 · D", "So, the big question. How much did the computers actually help? Let's line up before and now."],
  [771.0, "6-02 · D", "Seeing the lock. Before: hard lab experiments, and without a 3D shape, design was expensive, slow and difficult."],
  [778.6, "6-02 · D", "Now: a free prediction, downloaded from a public database."],
  [785.0, "6-03 · D", "Finding a hit. Before: screening real compounds by the millions, an approach a 2023 review says has hit a costly bottleneck."],
  [794.6, "6-03 · D", "Now: 8,918 designs inside a computer, and just 13 molecules actually made."],
  [805.0, "6-04 · D on camera", "Millions of compounds screened before. Here? Thirteen made."],
  [808.0, "6-05 · B on camera", "Thirteen. That's honestly wild."],
  [811.0, "6-06 · D", "Time. Before: a ten-to-seventeen-year road, with finding a hit just the opening stretch."],
  [817.4, "6-06 · D", "Now: 30 days to the first hit, and a better key within another 30."],
  [824.0, "6-07 · D", "Improving the key. Before: every change meant another costly lab round."],
  [830.0, "6-07 · D", "Now: a predicted picture of the first key guided sixteen designs, and the grip got about fifteen times tighter."],
  [838.0, "6-08 · D", "To be fair, these pairs come from different studies: they compare scale and speed, not one race run side by side."],
  [845.0, "6-08 · D", "But the paper itself calls the work cost- and time-efficient."],
  [851.0, "6-09 · B", "Now imagine this keeps working further down the road. Fewer failed molecules, lower costs, fewer animal tests, less chemical waste."],
  [860.5, "6-09 · B", "Computing costs electricity too. And the real prize? New treatments for patients."],
  [868.0, "6-10 · B", "So where's 048 on the road? Target: found. Hit: found. Improving it: started. Cells: first tests, done. Animals and clinical trials: not yet."],
  [878.0, "6-11 · B", "And here's what the end of that road can look like. Some AI-assisted cancer drugs have walked much further."],
  [884.5, "6-11 · B", "In September 2026, one of them, lirafugratinib, was approved in the US for a bile duct cancer. Others failed along the way."],
  [894.0, "6-11 · B", "And 048? Its makers chose not to take it to trials, and shared it with other researchers instead."],
  [906.0, "6-12 · B on camera", "048 is at the very start of the road. But for this case, that start took weeks, not years."],
  [913.0, "breath", "(two-second music breath, then S7)"],
];
const CYAN = "#0E8C9A", GREY6 = "#9A9AA0";
const Cam6 = React.createContext(null);

/** Where a table point (board units, from the board's middle) lands on screen this frame, and how many pixels a table unit is there. */
const camera6 = f => {
  const c = TRK6.cam[Math.max(0, Math.min(TRK6.cam.length - 1, f))];
  const e = c.slice(0, 3), a = c.slice(3, 6), F = c[6] / 36 * W;
  const sub = (p, q) => [p[0] - q[0], p[1] - q[1], p[2] - q[2]], dot = (p, q) => p[0] * q[0] + p[1] * q[1] + p[2] * q[2];
  const norm = p => { const l = Math.hypot(...p); return p.map(v => v / l); };
  const d = norm(sub(a, e)), r = norm([d[1], -d[0], 0]), u = [r[1] * d[2] - r[2] * d[1], r[2] * d[0] - r[0] * d[2], r[0] * d[1] - r[1] * d[0]];
  const el = Math.asin(Math.max(-1, Math.min(1, -d[2]))) * 180 / Math.PI;
  const proj = (x, y, z = 0) => {
    const p = sub([G6.BC[0] + x, G6.BC[1] + y, z], e), k = dot(p, d);
    return [W / 2 + F * dot(p, r) / k, H / 2 - F * dot(p, u) / k];
  };
  const ppu = (x, y) => { const p = proj(x, y), q = proj(x + 0.05, y); return Math.hypot(q[0] - p[0], q[1] - p[1]) / 0.05; };
  return {proj, ppu, flat: clamp((el - 72) / 12)};
};

/** Things drawn on the table at (x, y): children are laid out in pixels at 200 to the table unit, the film's own scale, around 0, 0. */
const On = ({x, y, children, fade = 1}) => {
  const c = React.useContext(Cam6), [px, py] = c.proj(x, y), k = c.ppu(x, y) / 200, o = fade * c.flat;
  return o > 0.001 ? <g transform={`translate(${px} ${py}) scale(${k})`} opacity={o}>{children}</g> : null;
};
const Stay = (t, a, b, d = 0.3) => after(t, a, d) * (1 - after(t, b, d));

/** A dimension line: ticks at both ends, the words in a gap in the middle. Drawn from the left. */
const Span = ({w, at, label, size = 32, fill = INK, dur = 0.8}) => {
  const t = useT(), p = smooth((t - at) / dur);
  if (p <= 0) return null;
  ruler.font = `400 ${size}px "${SERIF}"`;
  const gap = ruler.measureText(label).width / 2 + 12, L = w * p;
  return <g stroke={fill} strokeWidth={3} strokeLinecap="round">
    <line x1={0} y1={-12} x2={0} y2={12}/>
    <line x1={0} y1={0} x2={Math.min(L, w / 2 - gap)} y2={0}/>
    {L > w / 2 + gap && <line x1={w / 2 + gap} y1={0} x2={L} y2={0}/>}
    {p >= 1 && <line x1={w} y1={-12} x2={w} y2={12}/>}
    <text x={w / 2} y={size * 0.32} fontFamily={SERIF} fontSize={size} fill={fill} stroke="none" textAnchor="middle" opacity={after(t, at + dur * 0.5, 0.3)}>{label}</text>
  </g>;
};

/** A box drawn round by pen, dashed (possible, not measured) or solid. */
const DrawBox = ({w, h, at, dashed, fill = INK, dur = 0.7, children}) => {
  const t = useT(), p = smooth((t - at) / dur), L = 2 * (w + h);
  if (p <= 0) return null;
  return <g>
    <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={14} fill="none" stroke={fill} strokeWidth={dashed ? 3.5 : 4.5}
      strokeDasharray={dashed ? "16 11" : `${L * p} ${L}`} opacity={dashed ? p : 1}/>
    <g opacity={after(t, at + dur * 0.6, 0.3)}>{children}</g>
  </g>;
};

const RowName = ({r, at, lines}) => {
  const y = G6.ROWS[r];
  return <On x={-2.47} y={y}><g>{lines.map((s, i) => <Note key={i} x={0} y={-6 + (i - (lines.length - 1) / 2) * 44} size={44} at={at + 0.25 * i} fill={INK} anchor="end" rot={0}>{s}</Note>)}</g></On>;
};

const Board6 = ({t}) => {
  const [b, n] = G6.COLS, R = G6.ROWS, cw = G6.CW * 200;
  const notes = 1 - after(t, S6.oncam[0], 0.3);
  return <g>
    <On x={b} y={2.45}><Ink x={0} y={30} size={96} at={S6.hdr_b} font={SERIF} fill={SOFT} anchor="middle" w={420}>BEFORE</Ink></On>
    <On x={n} y={2.45}><Ink x={0} y={30} size={96} at={S6.hdr_n} font={SERIF} anchor="middle" w={340}>NOW</Ink></On>
    <On x={3.45} y={2.45} fade={1 - after(t, S6.row1 + 1.5, 0.4)}><Note x={0} y={16} size={40} at={S6.ask} fill={DARK}>the big question:</Note><Note x={0} y={60} size={40} at={S6.ask + 0.8} fill={DARK}>how much did computers help?</Note></On>

    {/* row 1 */}
    <RowName r={0} at={S6.row1} lines={["seeing", "the lock"]}/>
    <On x={b - 0.47} y={R[0]}><Note x={0} y={-22} size={34} at={S6.lab} fill={SOFT} anchor="middle" rot={0}>hard lab experiments</Note><Note x={0} y={30} size={34} at={S6.noshape} fill={DARK} anchor="middle" rot={0}>no 3D shape yet</Note></On>
    <On x={n + 0.2} y={R[0]}>
      <g opacity={after(t, S6.afdb)}><circle cx={14} cy={-44} r={12} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5"/>
        <text x={36} y={-35} fontFamily={SANS} fontSize={26} fontWeight={600} fill={INK}>predicted</text>
        <text x={2} y={2} fontFamily={SANS} fontSize={21} fontWeight={500} fill={SOFT}>AlphaFold DB v6</text></g>
      <Note x={0} y={58} size={38} at={S6.free} fill={DARK} rot={-2}>free download</Note>
    </On>

    {/* row 2 */}
    <RowName r={1} at={S6.row2} lines={["finding", "a hit"]}/>
    <On x={3.45} y={R[1]} fade={notes}>
      <Keyed x={0} y={14} size={80} at={S6.slam} dur={0.45} w={460} parts={["millions → ", "13", ""]}/>
      <Ink x={2} y={58} size={26} at={S6.made} weight={500} fill={SOFT} w={400}>8,918 designed · 13 made</Ink>
    </On>

    {/* 6-04: the number in vermilion beside the print */}
    <On x={3.55} y={-2.05} fade={1 - after(t, S6.row3 - 0.4, 0.3)}><Note x={0} y={0} size={130} at={S6.print_d + 1.2} fill={RED} rot={-4}>13</Note></On>

    {/* row 3 */}
    <RowName r={2} at={S6.row3} lines={["time"]}/>
    <On x={b - 1.05} y={R[2] + 0.31}><Span w={2.1 * 200} at={S6.tape_b[0]} dur={S6.tape_b[1]} label="10–17 years" size={30}/></On>
    <On x={b - 1.05 + 0.21} y={R[2] + 0.08}><PenLoop x={0} y={0} rx={52} ry={34} at={S6.ring_b} rot={-6}/></On>
    <On x={b - 1.22} y={R[2] - 0.3}><Note x={0} y={6} size={34} at={S6.start_b} fill={DARK}>finding a hit: just the start</Note></On>
    <On x={n - 1.05} y={R[2] + 0.31}><Span w={0.42 * 200} at={S6.tape_n} dur={0.5} label="" size={24} fill={RED}/></On>
    <On x={n - 1.05 + 0.42} y={R[2] + 0.31}><Span w={0.21 * 200} at={S6.plus} dur={0.4} label="" size={24} fill={DARK}/></On>
    <On x={n - 1.22} y={R[2] - 0.3}><Note x={0} y={6} size={34} at={S6.tape_n + 0.2} fill={DARK}>30 days → first hit</Note></On>
    <On x={3.45} y={R[2]} ><Note x={0} y={-8} size={38} at={S6.plus + 0.2} fill={DARK}>+30 days →</Note><Note x={0} y={38} size={38} at={S6.plus + 0.9} fill={DARK}>a better key</Note></On>

    {/* row 4 */}
    <RowName r={3} at={S6.row4} lines={["improving", "the key"]}/>
    <On x={b + 0.22} y={R[3]}><Note x={0} y={-12} size={34} at={S6.round} fill={DARK}>every change =</Note><Note x={0} y={30} size={34} at={S6.round + 0.6} fill={DARK}>another lab round</Note></On>
    {/* now: the predicted pose of the first key, sixteen designs from it, the grip about fifteen times tighter */}
    <On x={n} y={R[3]}>
      <g opacity={after(t, S6.slot, 0.4)}>
        <circle cx={-186} cy={-14} r={42} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5"/>
        <KeyMark x={-186} y={-14}/>
        <text x={-186} y={64} fontFamily={SANS} fontSize={20} fontWeight={500} fill={SOFT} textAnchor="middle">predicted</text>
      </g>
      <Note x={-134} y={-4} size={40} at={S6.slot + 2.0} fill={INK} rot={0}>→</Note>
      {Array.from({length: 16}, (_, i) => <circle key={i} cx={-90 + 20 * (i % 4)} cy={-44 + 20 * Math.floor(i / 4)} r={6.5 * after(t, S6.slot + 2.5 + 0.07 * i, 0.25)} fill={INK}/>)}
      <text x={-60} y={64} fontFamily={SANS} fontSize={20} fontWeight={500} fill={SOFT} textAnchor="middle" opacity={after(t, S6.slot + 3.0, 0.4)}>16 designs</text>
      <Note x={-12} y={-4} size={40} at={S6.slot + 4.3} fill={INK} rot={0}>→</Note>
      <Keyed x={48} y={12} size={84} at={S6.slot + 4.7} dur={0.6} w={240} parts={["", "~15×", ""]}/>
      <text x={120} y={64} fontFamily={SANS} fontSize={20} fontWeight={500} fill={SOFT} textAnchor="middle" opacity={after(t, S6.slot + 5.3, 0.4)}>tighter grip</text>
    </On>

    {/* 6-08 */}
    <On x={-2.35} y={-2.78}><Note x={0} y={0} size={42} at={S6.sources} fill={DARK} rot={-1}>different sources · scale and speed, not one race</Note></On>
    <On x={4.85} y={-2.0} fade={after(t, S6.quote, 0.4)}>
      <rect x={-250} y={-74} width={500} height={150} fill="#FBFAF6" stroke="#D6D3CA"/>
      <text x={0} y={-6} fontFamily={SERIF} fontSize={44} fill={INK} textAnchor="middle">“cost- and time-efficient”</text>
      <text x={0} y={44} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="middle">Ren et al. 2023</text>
    </On>
  </g>;
};

/** A small key in ink: bow, shaft, two teeth. */
const KeyMark = ({x, y}) => <g transform={`translate(${x} ${y})`} stroke={INK} strokeWidth={4} fill="none" strokeLinecap="round" strokeLinejoin="round">
  <circle cx={-15} cy={0} r={10}/><path d="M-5 0 H25 M13 0 V9 M22 0 V9"/>
</g>;

/** The plug at the end of the screen's wire and the socket it goes to: a ring with a red bolt, so it reads as mains power. */
const Plug = ({at}) => {
  const t = useT(), ring = smooth((t - at - 0.3) / 0.5), L = 2 * Math.PI * 38;
  return <g strokeLinecap="round" strokeLinejoin="round">
    <g stroke={INK} strokeWidth={4} fill="none" opacity={after(t, at, 0.3)}><rect x={0} y={-26} width={50} height={52} rx={8}/><line x1={50} y1={-12} x2={74} y2={-12}/><line x1={50} y1={12} x2={74} y2={12}/></g>
    {ring > 0 && <circle cx={134} cy={0} r={38} fill="none" stroke={INK} strokeWidth={4} strokeDasharray={`${L * ring} ${L}`} transform="rotate(180 134 0)"/>}
    <path d="M141 -25 L119 5 H132 L127 25 L149 -5 H136 Z" fill={RED} opacity={after(t, at + 0.7, 0.25)}/>
  </g>;
};

/** Current on the wire: a short red stroke runs from the plug to the screen, three times. */
const Current = ({w, at, n = 3, every = 0.9}) => {
  const t = useT();
  return <g>{Array.from({length: n}, (_, i) => {
    const q = (t - at - every * i) / every;
    if (q <= 0 || q >= 1) return null;
    const x = w * (1 - smooth(q));
    return <line key={i} x1={x - 23} y1={0} x2={x + 23} y2={0} stroke={RED} strokeWidth={5} strokeLinecap="round" opacity={Math.sin(Math.PI * q)}/>;
  })}</g>;
};

const Corner6 = ({t}) => {
  const E = G6.EX, B6 = S6.boxes, words = ["health", "cost", "animals", "waste"];
  return <g>
    {words.map((w, i) => <On key={i} x={E - 4.2 + 2.0 * i} y={-1.3}><DrawBox w={340} h={150} at={B6[i]} dashed><text x={0} y={16} fontFamily={SERIF} fontSize={52} fill={INK} textAnchor="middle">{w}</text></DrawBox></On>)}
    <On x={E - 5.1} y={-2.25}><Note x={0} y={0} size={40} at={S6.maybe} fill={DARK}>dashed = possible, not yet measured</Note></On>
    <On x={E - 2.55} y={1.0}><Pen from={[0, 0]} to={[560, 0]} at={S6.plug} fill={INK} dur={0.5}/></On>
    <On x={E - 2.55} y={1.0}><Current w={560} at={S6.plug + 1.3}/></On>
    <On x={E + 0.25} y={1.0}><Plug at={S6.plug + 0.4}/></On>
    <On x={E + 1.22} y={1.0}><Note x={0} y={14} size={42} at={S6.power + 0.5} fill={DARK}>computing costs electricity too</Note></On>
    <On x={E + 3.8} y={-1.3}><DrawBox w={420} h={170} at={S6.prize}><text x={0} y={-8} fontFamily={SERIF} fontSize={46} fill={INK} textAnchor="middle">new treatments</text><text x={0} y={40} fontFamily={SERIF} fontSize={46} fill={INK} textAnchor="middle">for patients</text></DrawBox></On>
  </g>;
};

const Road6 = ({t}) => {
  const X = G6.ST.map(s => G6.RX + s), y = -0.3, names = ["Target", "Hit", "Improving", "Cells & animals", "Clinical trials", "Approval"];
  const rr = G6.RR * 200, lab = after(t, S6.slide_r[0] + 1.6, 0.4);
  const tagAt = S6.tag048;
  const cyanP = smooth((t - S6.cyan[0]) / S6.cyan[1]), exsP = smooth((t - S6.exs[0]) / S6.exs[1]);
  return <g>
    {[4, 5].map(i => <On key={i} x={X[i]} y={y}><circle r={rr} fill="none" stroke={GREY6} strokeWidth={4} strokeDasharray="12 10" opacity={lab}/></On>)}
    <On x={X[3]} y={y}><path d={`M0 ${-rr} A${rr} ${rr} 0 0 1 0 ${rr}`} fill="none" stroke={GREY6} strokeWidth={4} strokeDasharray="12 10" opacity={lab}/></On>
    {names.map((s, i) => <On key={i} x={X[i]} y={y - 0.56}><text x={0} y={0} fontFamily={SANS} fontSize={30} fontWeight={600} fill={i < 4 ? INK : SOFT} textAnchor="middle" opacity={lab}>{s}</text></On>)}
    {[[3, "animals: not reported"], [4, "not reported"], [5, "not reported"]].map(([i, s]) => <On key={i} x={X[i]} y={y - 0.76}><text x={0} y={0} fontFamily={SANS} fontSize={23} fontWeight={500} fill={SOFT} textAnchor="middle" opacity={after(t, S6.notyet, 0.4)}>{s}</text></On>)}
    {/* 048's tag over the cells station */}
    <On x={X[3]} y={y + 0.95} fade={after(t, tagAt, 0.35)}>
      <line x1={0} y1={44} x2={0} y2={0.95 * 200 - rr - 8} stroke={INK} strokeWidth={2.5}/>
      <rect x={-78} y={-44} width={156} height={88} rx={12} fill="#FBFAF6" stroke={INK} strokeWidth={3}/>
      <text x={0} y={22} fontFamily={SERIF} fontSize={64} fill={RED} textAnchor="middle">048</text>
    </On>
    <On x={X[3] + 0.5} y={y + 1.55}><Note x={0} y={0} size={42} at={S6.public} fill={DARK}>made public for other researchers</Note></On>
    {/* the cyan tag runs to the last station; the other stops at trials and is struck through */}
    <On x={X[0]} y={y - 1.12} fade={t > S6.cyan[0] ? 1 : 0}>
      <line x1={0} y1={0} x2={(X[5] - X[0]) * 200 * cyanP} y2={0} stroke={CYAN} strokeWidth={6} strokeLinecap="round"/>
      <circle cx={(X[5] - X[0]) * 200 * cyanP} cy={0} r={11} fill={CYAN}/>
    </On>
    <On x={X[5]} y={y - 1.12} fade={after(t, S6.cyan_tag, 0.4)}>
      <rect x={-640} y={18} width={660} height={96} rx={12} fill="#FBFAF6" stroke={CYAN} strokeWidth={3}/>
      <text x={-620} y={56} fontFamily={SANS} fontSize={27} fontWeight={700} fill={INK}>lirafugratinib (RLY-4008)</text>
      <text x={-620} y={94} fontFamily={SANS} fontSize={23} fontWeight={500} fill={SOFT}>FDA approved, 23 Sep 2026 · bile duct cancer</text>
    </On>
    <On x={X[0]} y={y - 1.92} fade={t > S6.exs[0] ? 1 : 0}>
      <line x1={0} y1={0} x2={(X[4] - X[0]) * 200 * exsP} y2={0} stroke={GREY6} strokeWidth={6} strokeLinecap="round"/>
      <circle cx={(X[4] - X[0]) * 200 * exsP} cy={0} r={11} fill={GREY6}/>
    </On>
    <On x={X[4]} y={y - 1.92} fade={after(t, S6.exs[0] + S6.exs[1], 0.3)}>
      <rect x={30} y={-30} width={350} height={60} rx={10} fill="#FBFAF6" stroke={GREY6} strokeWidth={3}/>
      <text x={48} y={9} fontFamily={SANS} fontSize={25} fontWeight={600} fill={SOFT}>EXS-21546 · stopped 2023</text>
      <Pen from={[22, 4]} to={[392, -6]} at={S6.strike} fill={RED} dur={0.35}/>
    </On>
    {/* 6-12: weeks, not years: the first stretch glows */}
    <On x={X[0]} y={y} fade={Stay(t, S6.weeks, 914.0, 0.4)}>
      <line x1={-10} y1={0} x2={(X[1] - X[0]) * 200 + 10} y2={0} stroke={RED} strokeWidth={40} strokeLinecap="round" opacity={0.28} style={{filter: "blur(10px)"}}/>
    </On>
    <On x={X[1] + 0.35} y={y + 0.42}><Note x={0} y={0} size={40} at={S6.weeks + 0.3} fill={DARK}>weeks, not years</Note></On>
  </g>;
};

const SRC6 = [
  [771.6, 785.0, "Illustration · Wang 2023 p.3 · Ren 2023 · AlphaFold DB v6"],
  [786.0, 804.6, "Illustration · Wang 2023 pp.4–5 · Ren 2023"],
  [811.6, 824.0, "Illustration · Wang 2023 p.1 · Ren 2023"],
  [824.6, 838.0, "Illustration · Lengauer 2007 p.13 · Ren 2023"],
  [845.0, 851.0, "Ren et al. 2023"],
  [853.6, 867.6, "Illustration"],
  [869.8, 878.0, "Illustration · Ren 2023 (Results, Conclusions)"],
  [881.5, 915.0, "Illustration · Wang 2023 Table 8 · FDA 2026 · Business Wire 2023 · GEN 2023"],
];

const S6Scene = ({file = "fusion_s1/s6_take.mp4", review = true, from = 0, fps = 30}) => {          // fps 60 with the 60 fps track (S6_STEP=1) for the 4K pass
  const f = useCurrentFrame() + from, t = S6.start + f / fps, cam = camera6(Math.round(f * (TRK6.fps || 30) / fps));
  const line = [...S6_LINES].reverse().find(l => t >= l[0]);
  return <Clock.Provider value={t}><Cam6.Provider value={cam}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}} startFrom={from}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      {t < 856 && <Board6 t={t}/>}
      {t > 849 && t < 871 && <Corner6 t={t}/>}
      {t > 865 && <Road6 t={t}/>}
      {/* screen-fixed notes while the camera is down among the sample tubes */}
      <g opacity={Stay(t, S6.millions, S6.climb2[0] + 0.3, 0.3)}>
        <Note x={96} y={150} size={60} at={S6.millions} fill={DARK}>millions screened</Note>
        <Note x={96} y={226} size={46} at={S6.neck} fill={DARK}>“a costly bottleneck” (2023 review)</Note>
      </g>
      {/* and down among the keys, and at the turntable */}
      <g opacity={Stay(t, S6.designed, S6.climb_k[0] + 0.3, 0.3)}>
        {/* in the strip of table between the two cells' rims, along their slope */}
        <Note x={300} y={816} size={50} at={S6.designed} fill={DARK} rot={3.7}>8,918 designs inside a computer</Note>
        <Note x={980} y={860} size={50} at={S6.dots[0]} fill={DARK} rot={3.7}>→ just 13 made</Note>
      </g>
      <g opacity={Stay(t, S6.round, S6.climb_t[0] + 0.3, 0.3)}>
        <Note x={1350} y={560} size={56} at={S6.round} fill={DARK}>every change =</Note>
        <Note x={1350} y={630} size={56} at={S6.round + 0.6} fill={DARK}>another lab round</Note>
      </g>
      {/* 6-04 and 6-05: the on-camera prints, placeholders until the footage of 11-12 */}
      {t > S6.print_d - 0.1 && t < S6.row3 + 0.4 && <On x={5.35} y={0.25} fade={1 - after(t, S6.row3 - 0.4, 0.3)}><Print who="D" x={-260} y={-312} w={520} h={624} at={S6.print_d} rot={-1.5}/></On>}
      {t > S6.print_b - 0.1 && t < S6.row3 + 0.4 && <On x={9.5} y={0.25} fade={1 - after(t, S6.row3 - 0.4, 0.3)}><Print who="B" x={-260} y={-312} w={520} h={624} at={S6.print_b} rot={1.5}/></On>}
      {t > S6.print_b2 - 0.1 && <On x={G6.RX - 3.7} y={1.45}><Print who="B" x={-180} y={-216} w={360} h={432} at={S6.print_b2} rot={-1.5}/></On>}
      {SRC6.map(([a, b, s]) => <Source key={a} x={96} y={1062} at={a} until={b}>{s}</Source>)}
      {review && line && <g>
        <rect x={0} y={0} width={W} height={58} fill={BONE} opacity={0.82}/>
        <text x={28} y={38} fontFamily={SANS} fontSize={24} fontWeight={700} fill={SOFT}>{line[1]}</text>
        <text x={300} y={38} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT}>{line[2].length > 120 ? line[2].slice(0, 118) + "…" : line[2]}</text>
      </g>}
    </svg>
  </AbsoluteFill></Cam6.Provider></Clock.Provider>;
};
