// HKBU SCIE1007 coursework science video. cut_v7 word accents: small Remotion layers over the retimed voice-over pieces
// (_render_tmp/cut6/vo/<seg>.mp4), each landing on a spoken word (times = piece seconds from 对时/beats/<seg>.json).
// 2-06: red rule under "Chemical Science · 2023" on "Chemical"; a supplementary page slides out from under the paper on "supplementary".
// 2-08: Target, Hit and Improve pulse together on "computers".
// 4-01: a dashed ghost outline of the protein draws on from "AI" and settles on "shape" (the AI's guess), gone before the camera moves.
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

const A206 = ({t, w, track}) => {
  const u = out((t - w.chemical) / 0.55);
  const s = smooth((t - w.supplementary) / 0.45);
  const x = 470 + 260 * s;
  // the camera starts to move at 16.13 s: the layer rides the paper (affine fitted to the paper, 生成于 accent_v7.py) and is gone by 16.5 s
  let M = "matrix(1 0 0 1 0 0)", fade = 1;
  if (track && t >= track.t0) {
    const i = Math.min(track.A.length - 1, Math.round((t - track.t0) * 30));
    let a = null;
    for (let k = i; k >= 0 && !a; k--) if (track.A[k] && track.A[k][6] >= 40) a = track.A[k];
    if (a) M = `matrix(${a[0]} ${a[3]} ${a[1]} ${a[4]} ${a[2]} ${a[5]})`;
    fade = 1 - smooth((t - 16.25) / 0.25);
  }
  return <svg width={W} height={H} style={{position: "absolute"}}><g transform={M} opacity={fade}>
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

const LAYERS = {"2-06": A206, "2-08": A208, "4-01": A401};

const Accent = ({seg, file, w, ghost, track}) => {
  const t = useCurrentFrame() / 30;
  const L = LAYERS[seg];
  return <AbsoluteFill>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <L t={t} w={w} ghost={ghost} track={track}/>
  </AbsoluteFill>;
};

const Root = () => <Composition id="Accent" component={Accent} fps={30} width={W} height={H} durationInFrames={300}
  defaultProps={{seg: "2-08", file: "vo/2-08.mp4", w: {}, ghost: null}}
  calculateMetadata={({props}) => ({durationInFrames: props.frames})}/>;
registerRoot(Root);
