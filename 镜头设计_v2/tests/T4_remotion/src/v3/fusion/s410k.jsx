// HKBU SCIE1007 coursework science video. 4-10 (09:49-10:14, A's voice-over) with the new lock: the type layer over the Blender pass (shot `s410k` in
// 镜头设计_v3/styleframes/art/fusion/s1/inserts/bl_s410k.py). Everything physical is the render; this layer is the title, the three counts, pen notes and the source line.
// Counts are the paper's (Ren 2023: 8,918 / 54 / 7, pp. 1444 and 1447; see s4/4-10_数字对照.md). Words follow script_v3.3.md and the earlier S410 in s5.jsx.
// Rules from the 11-10 review: type to be read is 28 px or taller at 1080p, the source line is one line at the bottom left, nothing sits on an object.
// Type lives in the bare strip of table along the top left (y < 235), above the cells; the lock's top edge starts at x 968. Nothing appears in the first second.
import React from "react";
import {registerRoot, Composition, AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";

const W = 1920, H = 1080;
const INK = "#111113", SOFT = "#545458", RED = "#E8190F", BONE = "#EDEBE4";
const SERIF = "Instrument Serif", SANS = "Inter Tight", HAND = "Caveat";

const faces = [new FontFace(SERIF, `url(${staticFile("fusion_s1/fonts/InstrumentSerif-Regular.ttf")})`), new FontFace(SANS, `url(${staticFile("fusion_s1/fonts/InterTight.ttf")})`, {weight: "100 900"}), new FontFace(HAND, `url(${staticFile("fusion_s1/fonts/Caveat.ttf")})`, {weight: "400 700"})];
const fontHandle = delayRender("fonts");
Promise.all(faces.map(f => f.load())).then(l => { l.forEach(f => document.fonts.add(f)); continueRender(fontHandle); });

const clamp = x => Math.min(1, Math.max(0, x));
const smooth = x => { x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10); };
const out = x => 1 - Math.pow(1 - clamp(x), 3);
const Clock = React.createContext(0);
const useT = () => React.useContext(Clock);
const after = (t, at, d = 0.5) => out((t - at) / d);

let wipeId = 0;
/** Words that print left to right, as if a press ran over them. */
const Ink = ({x, y, size, at, font = SANS, weight = 600, fill = INK, w, dur = 0.5, children}) => {
  const t = useT(), p = smooth((t - at) / dur);
  const id = React.useMemo(() => `wipe${wipeId++}`, []);
  if (p <= 0) return null;
  const width = w || String(children).length * size * 0.62 + 40;
  return <g>
    <clipPath id={id}><rect x={x - 20} y={y - size * 1.2} width={width * p} height={size * 1.6}/></clipPath>
    <text x={x} y={y} fontFamily={font} fontSize={size} fontWeight={font === SERIF ? 400 : weight} fill={fill} clipPath={`url(#${id})`}>{children}</text>
  </g>;
};

const ruler = document.createElement("canvas").getContext("2d");
/** A pen note in Caveat, written left to right at writing speed. Each "→" is drawn as a pen stroke (the hand has no arrow). */
const Note = ({x, y, size, at, fill = INK, rot = -2, children}) => {
  const t = useT(), text = String(children), p = smooth((t - at) / (0.3 + text.length * 0.03));
  const id = React.useMemo(() => `pen${wipeId++}`, []);
  if (p <= 0) return null;
  ruler.font = `600 ${size}px "${HAND}"`;
  const gap = size * 0.22, len = size * 0.95, bits = [];
  text.split("→").forEach((s, i, all) => {
    if (s.trim()) bits.push({s: s.trim(), w: ruler.measureText(s.trim()).width});
    if (i < all.length - 1) bits.push({w: len});
  });
  const total = bits.reduce((s, b) => s + b.w, 0) + gap * (bits.length - 1);
  let cx = x;
  const marks = bits.map((b, i) => {
    const a = cx;
    cx += b.w + gap;
    if (b.s) return <text key={i} x={a} y={y} fontFamily={HAND} fontSize={size} fontWeight={600} fill={fill}>{b.s}</text>;
    const h = y - size * 0.26, k = size * 0.2;
    return <path key={i} d={`M${a} ${h + 2} Q${a + b.w * 0.5} ${h - 3} ${a + b.w} ${h} M${a + b.w - k} ${h - k * 0.8} L${a + b.w} ${h} L${a + b.w - k * 0.95} ${h + k * 0.75}`} fill="none" stroke={fill} strokeWidth={size * 0.065} strokeLinecap="round" strokeLinejoin="round"/>;
  });
  return <g transform={`rotate(${rot} ${x} ${y})`}>
    <clipPath id={id}><rect x={x - 10} y={y - size * 1.1} width={(total + 20) * p} height={size * 1.5}/></clipPath>
    <g clipPath={`url(#${id})`}>{marks}</g>
  </g>;
};

const LINES = [[0, "It came back with 8,918 brand-new designs."], [3.1, "Way too many to make."], [5.3, "So each key gets tried in a virtual lock."], [10.4, "That's docking: the computer predicts how a molecule might sit in the pocket, and scores the fit."], [17.1, "Similar designs get grouped,"], [18.9, "54 make the shortlist,"], [20.9, "and chemists pick just seven to make."]];
const wrap = (s, n = 44) => s.split(" ").reduce((l, w) => { if ((l[l.length - 1] + " " + w).trim().length > n) l.push(w); else l[l.length - 1] = (l[l.length - 1] + " " + w).trim(); return l; }, [""]);

/** Second version (11-11): every key is different, and the keys tried in the lock rise out of the field. 0-18.2 s the lock close-up (W3 K's last view): the field of
 * 8,918 small keys lands on the left, then four of them are tried in the lock. 18.0-21.0 s the camera comes down onto the 54 that stay; 47 leave, seven slide into a
 * row and the camera closes in (the cell's rim runs through the bottom right, clear of the source line). Red: only the 7. */
const S410K = ({file = "fusion_s410k/s410k_3d.mp4", fps = 30, review = true}) => {
  const t = useCurrentFrame() / fps;
  const count = Math.round(8918 * smooth((t - 1.6) / 1.9));          // counts up while the keys land (1.5-3.5 s)
  const first = 1 - after(t, 17.9, 0.4);                             // the lock view's type leaves as the camera does
  const early = 1 - after(t, 5.0, 0.4), fit = after(t, 5.4, 0.1);    // the two opening notes make room for the two about the fit
  const vo = wrap("VO (A): " + [...LINES].reverse().find(([a]) => t >= a)[1]);
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <g opacity={after(t, 1.0)}><text x={1856} y={92} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK} textAnchor="end">Objective 1 / Tool: docking / virtual screening</text></g>
      {first > 0 && <g opacity={first}>
        <Ink x={104} y={178} size={120} at={1.6} font={SERIF} w={380} dur={0.5}>{count.toLocaleString("en-US")}</Ink>
        <Ink x={108} y={222} size={28} at={2.2} w={480}>designs came back from the AI</Ink>
        {early > 0 && <g opacity={early}>
          <Note x={540} y={128} size={46} at={2.6} rot={-1.5}>one design = one key</Note>
          <Note x={540} y={198} size={46} at={3.3} rot={-2}>way too many to make</Note>
        </g>}
        {fit > 0 && <g>
          <Note x={540} y={128} size={46} at={8.3} rot={-1.5}>good fit → bright</Note>
          <Note x={540} y={198} size={46} at={12.6} rot={-2}>poor fit → pushed back</Note>
        </g>}
      </g>}
      <Ink x={104} y={178} size={104} at={20.3} font={SERIF} w={220} dur={0.45}>54</Ink>
      <Ink x={108} y={222} size={28} at={20.7} w={300}>make the shortlist</Ink>
      <Ink x={540} y={178} size={104} at={21.4} font={SERIF} fill={RED} w={120} dur={0.45}>7</Ink>
      <Ink x={544} y={222} size={28} at={21.8} w={200}>to make</Ink>
      {review && t >= 1.0 && vo.map((l, i) => <text key={i} x={64} y={990 - (vo.length - 1 - i) * 36} fontFamily={SANS} fontSize={28} fontWeight={500} fill={SOFT}>{l}</text>)}
      <g opacity={after(t, 1.0)}><text x={64} y={1046} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT}>Illustration · Ren 2023, pp. 1444, 1447</text></g>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

const Root = () => <>
  <Composition id="S410K" component={S410K} durationInFrames={750} fps={30} width={W} height={H}/>
</>;
registerRoot(Root);
