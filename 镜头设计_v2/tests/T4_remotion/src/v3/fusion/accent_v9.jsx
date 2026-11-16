// HKBU SCIE1007 coursework science video. cut_v8 fix pass (11-16 night): accent_v8.jsx plus word-landing actions for the voice-over
// pieces that the cut_v8 machine check found standing still (2-06, 5-04, 6-11, 7-04, 8-02, 8-03) or stopping before the sentence ends (3-08).
// Director rule: the picture keeps moving until the sentence ends, every move lands on a spoken word, no post zoom / push.
// Three kinds of action, each started by a word (times = piece seconds from 对时/beats_v8/<seg>.json, passed in as w):
//   pulse  — two red (or ink) rings open out from the thing being named (as in the 2-08 accent);
//   card   — a paper note card is dealt onto the table on its word; a later card in the same slot pushes it off;
//   runner — a dot runs along a lane between two words (7-04 race).
import React from "react";
import {registerRoot, Composition, AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";

const W = 1920, H = 1080;
const INK = "#111113", SOFT = "#8a8a8e", RED = "#E8190F", PAPER = "#F4F0E8";
const SERIF = "Instrument Serif", HAND = "Caveat";
const faces = [new FontFace(SERIF, `url(${staticFile("fusion_s1/fonts/InstrumentSerif-Regular.ttf")})`), new FontFace(HAND, `url(${staticFile("fusion_s1/fonts/Caveat.ttf")})`, {weight: "400 700"})];
const fontHandle = delayRender("fonts");
Promise.all(faces.map(f => f.load())).then(l => { l.forEach(f => document.fonts.add(f)); continueRender(fontHandle); });

const clamp = x => Math.min(1, Math.max(0, x));
const smooth = x => { x = clamp(x); return x * x * (3 - 2 * x); };
const out = x => 1 - Math.pow(1 - clamp(x), 3);
const win = (t, a, b, fi = 0.3, fo = 0.3) => out((t - a) / fi) * (1 - smooth((t - b) / fo));
const at = (w, k) => w[k] ?? null;

// ---------- v8 layers (unchanged) ----------
const A206 = ({t, w}) => {
  const u = out((t - w.chemical) / 0.55);
  const s = smooth((t - w.supplementary) / 0.45);
  const x = 470 + 260 * s;
  const fade = w.camgo !== undefined ? 1 - smooth((t - w.camgo + 0.3) / 0.3) : 1;
  return <svg width={W} height={H} style={{position: "absolute"}}><g opacity={fade}>
    <line x1={134} y1={186} x2={134 + 212 * u} y2={186} stroke={RED} strokeWidth={4} strokeLinecap="round" opacity={u > 0 ? 1 : 0}/>
    <defs><clipPath id="right"><rect x={697} y={0} width={W} height={H}/></clipPath></defs>
    <g clipPath="url(#right)" opacity={s > 0.001 ? 1 : 0}>
      <g transform={`translate(${x} 600) rotate(-3)`}>
        <rect x={0} y={0} width={230} height={300} fill={PAPER} stroke="#d8d2c6" strokeWidth={1.5}/>
        <text x={20} y={44} fontFamily={SERIF} fontSize={30} fill={INK}>Supplementary</text>
        <text x={20} y={78} fontFamily={SERIF} fontSize={30} fill={INK}>information</text>
        {[110, 130, 150, 170, 200, 220, 240].map((y, i) => <rect key={i} x={20} y={y} width={i % 3 === 2 ? 120 : 190} height={7} fill="#d6d1c6"/>)}
      </g>
    </g>
  </g></svg>;
};

const A208 = ({t, w}) => {
  const st = [228, 512, 790];
  return <svg width={W} height={H} style={{position: "absolute"}}>
    {[0, 1].map(k => st.map((cx, i) => {
      const p = clamp((t - w.computers - i * 0.09 - k * 0.45) / 0.9);
      return p > 0 && p < 1 ? <circle key={`${k}${i}`} cx={cx} cy={517} r={88 + 70 * out(p)} fill="none" stroke={RED} strokeWidth={5 * (1 - p) + 1} opacity={0.85 * (1 - p)}/> : null;
    }))}
  </svg>;
};

const A401 = ({t, w, ghost}) => {
  const draw = smooth((t - w.AI) / (w.guess - w.AI + 0.2));
  const settle = smooth((t - w.guess) / (w.shape - w.guess + 0.25));
  const a = win(t, w.AI, w.end - 0.45, 0.3, 0.35);
  const sc = 1.07 - 0.07 * settle, dx = 26 * (1 - settle), dy = -14 * (1 - settle);
  const note = win(t, w.guess, w.end - 0.45, 0.35, 0.35);
  return <svg width={W} height={H} style={{position: "absolute"}}>
    <defs><mask id="draw"><rect x={0} y={0} width={W} height={H} fill="black"/><circle cx={ghost.cx} cy={ghost.cy} r={20 + 420 * draw} fill="white"/></mask></defs>
    <g opacity={a} mask="url(#draw)" transform={`translate(${ghost.cx + dx} ${ghost.cy + dy}) scale(${sc}) translate(${-ghost.cx} ${-ghost.cy})`}>
      <path d={ghost.d} fill="none" stroke={INK} strokeWidth={3.5} strokeDasharray="14 11" strokeLinejoin="round"/>
    </g>
    <text x={850} y={250} fontFamily={HAND} fontSize={48} fontWeight={600} fill={RED} opacity={note} transform="rotate(-3 850 250)">the AI's guess</text>
  </svg>;
};

// ---------- v9 actions ----------
const PULSE_T = 0.7;
const Pulse = ({t, t0, x, y, r0 = 60, grow = 170, ink = false, gone = 1}) => {
  if (t0 === null) return null;
  return <g>{[0, 0.22].map(d => {
    const p = clamp((t - t0 - d) / PULSE_T);
    if (p <= 0 || p >= 1) return null;
    return <circle key={d} cx={x} cy={y} r={r0 + grow * out(p)} fill="none" stroke={ink ? INK : RED} strokeWidth={9 * (1 - 0.6 * p)} opacity={0.9 * (1 - p) * gone}/>;
  })}</g>;
};

const CARD_W = 470, CARD_H = 150;
const Card = ({t, t0, t1, x, y, text, sub, red}) => {
  if (t0 === null || t < t0) return null;
  const a = out((t - t0) / 0.24);
  const e = t1 === null ? 0 : smooth((t - t1) / 0.32);
  if (e >= 1) return null;
  const dy = -46 * (1 - a), dx = 70 * e, sc = 1.07 - 0.07 * a;
  const cx = x + CARD_W / 2, cy = y + CARD_H / 2;
  return <g opacity={a * (1 - e)} transform={`translate(${dx} ${dy}) translate(${cx} ${cy}) scale(${sc}) rotate(${(text.length % 3) - 1}) translate(${-cx} ${-cy})`}>
    <rect x={x + 6} y={y + 12} width={CARD_W} height={CARD_H} fill="#000" opacity={0.16 * a} filter="url(#soft)"/>
    <rect x={x} y={y} width={CARD_W} height={CARD_H} fill={PAPER} stroke="#d2ccbf" strokeWidth={1.5}/>
    <text x={x + 30} y={y + (sub ? 70 : 92)} fontFamily={SERIF} fontSize={52} fill={red ? RED : INK}>{text}</text>
    {sub && <text x={x + 30} y={y + 118} fontFamily={SERIF} fontSize={30} fill={SOFT}>{sub}</text>}
  </g>;
};

const Runner = ({t, t0, t1, a, b, ink, gone = 1}) => {
  if (t0 === null || t1 === null || t < t0) return null;
  const u = smooth((t - t0) / (t1 - t0));
  const x = a[0] + (b[0] - a[0]) * u, y = a[1] + (b[1] - a[1]) * u;
  return <g opacity={gone}>
    <line x1={a[0]} y1={a[1]} x2={x} y2={y} stroke={ink ? INK : RED} strokeWidth={6} strokeLinecap="round"/>
    <circle cx={x} cy={y} r={17} fill={ink ? INK : RED}/>
  </g>;
};

// per piece: cards [word, slot, x, y, text, sub?, red?], pulses [word, x, y, r0?, ink?], runners [word0, word1, [x,y], [x,y], ink?], fade: word (all v9 marks go before it)
const CFG = {
  "2-06": {fade: "camgo", cards: [
    ["read", "A", 800, 230, "we read"], ["lot", "B", 1330, 230, "a lot"],
    ["lab", "A", 800, 420, "no lab work"], ["literature", "B", 1330, 420, "literature review"],
    ["centre", "A", 800, 230, "at the centre:"], ["original", "B", 1330, 230, "1 original study", null, true],
    ["ren", "A", 800, 420, "Ren et al."], ["chemical", "B", 1330, 420, "Chemical Science", "2023"],
    ["with", "A", 800, 230, "+ its data"]]},
  "5-04": {fade: "from", cards: [["001", "A", 70, 520, "001 …"], ["stop", "B", 70, 700, "stops CDK20?", null, true]],
           pulses: [["actually", 305, 595, 70], ["working", 305, 775, 80]]},
  "6-11": {pulses: [
    ["walked", 1374, 500], ["further", 1652, 500], ["september", 1652, 698, 40], ["2026", 1652, 698, 40], ["one", 1384, 756, 150],
    ["lirafugratinib", 1384, 756, 150], ["approved", 1652, 500], ["us", 1652, 500], ["bile", 1384, 756, 150], ["cancer", 1384, 756, 150],
    ["others", 1374, 500, 60, true], ["failed", 1374, 500, 60, true], ["way", 820, 500, 60, true], ["048", 1098, 340],
    ["chose", 1098, 340], ["not", 1374, 500, 60, true], ["trials", 1374, 500, 60, true], ["shared", 1098, 500], ["researchers", 1098, 500, 90],
    ["instead", 1098, 500, 120]]},
  "7-04": {fade: "really", pulses: [["definition", 1660, 720, 80, true], ["hit", 1660, 720, 80, true], ["know", 1740, 680], ["exactly", 1740, 680],
                    ["faster", 1740, 680]],
           runners: [["then", "really", [420, 600], [1560, 600]], ["then", "really", [420, 840], [1420, 840], true]]},
  "8-02": {pulses: [["lock's", 690, 530, 90], ["shape", 600, 760], ["designing", 956, 530, 90], ["keys", 870, 760], ["ranking", 1210, 530, 90],
                    ["make", 1142, 760], ["first", 1670, 80, 50], ["objective", 1670, 80, 50], ["met", 1670, 80, 50], ["met", 1670, 80, 90]]},
  "8-03": {pulses: [["methods", 1650, 80, 60], ["helped", 1650, 80, 60], ["team", 1650, 80, 60], ["assess", 1650, 80, 60], ["fast", 1650, 80, 80], ["years", 1000, 290, 80, true], ["first", 592, 440], ["hit", 592, 440], ["30", 490, 610, 70], ["days", 490, 610, 70],
                    ["round", 868, 440], ["two", 868, 440], ["key", 868, 440], ["turn", 868, 440, 90]]},
  "3-08": {pulses: [["expensive", 720, 560, 90], ["slow", 1320, 540, 160], ["difficult", 1320, 540, 160]]},
};

const V9 = ({seg, t, w}) => {
  const C = CFG[seg];
  if (!C) return null;
  const tf = C.fade ? at(w, C.fade) : null;
  const gone = tf === null ? 1 : 1 - smooth((t - tf + 0.35) / 0.3);
  const cards = (C.cards || []).map(([k, slot, x, y, text, sub, red], i, all) => {
    const t0 = at(w, k);
    const nxt = all.slice(i + 1).find(c => c[1] === slot);
    const t1 = nxt ? at(w, nxt[0]) : (tf === null ? null : tf - 0.35);
    return <Card key={i} t={t} t0={t0} t1={t1} x={x} y={y} text={text} sub={sub} red={red}/>;
  });
  return <svg width={W} height={H} style={{position: "absolute"}}>
    <defs><filter id="soft" x="-20%" y="-20%" width="140%" height="160%"><feGaussianBlur stdDeviation="10"/></filter></defs>
    {cards}
    {(C.runners || []).map(([k0, k1, a, b, ink], i) => <Runner key={i} t={t} t0={at(w, k0)} t1={at(w, k1)} a={a} b={b} ink={ink} gone={gone}/>)}
    {(C.pulses || []).map(([k, x, y, r0, ink], i) => <Pulse key={i} t={t} t0={at(w, k)} x={x} y={y} r0={r0} ink={ink} gone={gone}/>)}
  </svg>;
};

const LAYERS = {"2-06": A206, "2-08": A208, "4-01": A401};

const Accent = ({seg, file, w, ghost, track}) => {
  const t = useCurrentFrame() / 30;
  const L = LAYERS[seg];
  return <AbsoluteFill>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    {L && <L t={t} w={w} ghost={ghost} track={track}/>}
    <V9 seg={seg} t={t} w={w}/>
  </AbsoluteFill>;
};

const Root = () => <Composition id="Accent" component={Accent} fps={30} width={W} height={H} durationInFrames={300}
  defaultProps={{seg: "2-08", file: "vo/2-08.mp4", w: {}, ghost: null}}
  calculateMetadata={({props}) => ({durationInFrames: props.frames})}/>;
registerRoot(Root);
