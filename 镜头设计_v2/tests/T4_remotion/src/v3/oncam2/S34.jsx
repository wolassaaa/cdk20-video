// HKBU SCIE1007 coursework video: on-camera segments of S3-S4 in the approved layout (same kit as S12.jsx).
// Copy: 镜头设计_v3/script/oncam_graphics_v33.py, then the script's Visual lines. Word times: 素材流程_out/<who>/5_place/place.json.
// Times are clip frames at 30 fps; each graphic starts 3-8 f before its word. Ink props are adapted from ../oncam/props.jsx
// (PropLock, PropScissors, PropTrail) in screen coordinates and sample colours.
import React from "react";
import {ramp, outCubic, outBack, outExpo, handLine, loopPts, quad, hash} from "../core";
import {InkPath, InkLine} from "../ink";
import {W, H, INK, RED, CYAN, SERIF, wf, enter, exitK, Word, Full, textW, Segment, Reel, reelLen, segLen} from "./kit";

const PAPER = "#EAEAE1";

// ---- shared ink lock and key (from PropLock) ----
export const Key = ({progress, color = INK, seed = 40}) => <g>
  <InkPath points={handLine([0, 0], [170, 0], {bow: 2})} seed={seed} size={8} color={color} progress={progress} pressure="nib"/>
  <InkPath points={[[18, 0], [18, 24], [42, 24], [42, 10], [62, 10], [62, 0]]} seed={seed + 1} size={6} color={color} progress={progress} pressure="marker"/>
  <InkPath points={loopPts(212, 0, 42, 42, {seed: seed + 2, turns: 1.1})} seed={seed + 2} size={8} color={color} progress={progress}/>
</g>;
export const Lock = ({progress, color = INK, opacity = 1}) => <g opacity={opacity}>
  <InkPath points={[[-150, -40], [150, -40], [150, 210], [-150, 210], [-150, -40]]} seed={3} size={9} color={color} progress={progress} pressure="brush"/>
  <InkPath points={loopPts(0, -40, 100, 130, {a0: Math.PI, turns: 0.5, seed: 5, spiral: 0, wob: 0.02})} seed={4} size={9} color={color} progress={progress}/>
  <InkPath points={loopPts(0, 80, 16, 16, {seed: 6})} seed={6} size={6} color={color} progress={ramp(progress, 0.5, 1)}/>
</g>;

// ---- 3-01 D (left): "Okay. To get this, picture a lock and a key." lock on "lock", key on "key" ----
const G301 = ({f, out}) => {
  const tL = wf(3.696) - 6, tK = wf(5.539) - 6;
  return <Full opacity={exitK(f, out)}>
    {f >= tL && <g transform="translate(1330 400) scale(0.8)"><Lock progress={outCubic(ramp(f, tL, tL + 11))}/></g>}
    <Word x={1330} y={640} size={56} f={f} t0={tL + 2} anchor="middle">lock</Word>
    {f >= tK && <g transform="translate(1500 464) scale(1.13)"><Key progress={outCubic(ramp(f, tK, tK + 11))}/></g>}
    <Word x={1640} y={640} size={56} f={f} t0={tK + 2} anchor="middle">key</Word>
  </Full>;
};

// ---- 3-06 D (left): suspect file: CDK20 card, red SUSPECT stamp on "strong suspect", "not the only cause" ----
const G306 = ({f, out}) => {
  const tC = wf(2.435) - 6, tS = wf(2.896) - 5, tN = wf(5.26) - 5;
  const kc = outCubic(ramp(f, tC, tC + 11));
  const ks = outBack(ramp(f, tS, tS + 8), 2.2);
  return <Full opacity={exitK(f, out)}>
    {f >= tC && <g opacity={enter(f, tC)}>
      <InkPath points={[[1180, 330], [1700, 330], [1700, 640], [1180, 640], [1180, 330]]} color={INK} seed={301} size={7} progress={kc} pressure="nib"/>
      <InkLine from={[1210, 400]} to={[1420, 400]} color={INK} seed={302} size={4} progress={kc} pressure="marker"/>
      <text x={1215} y={385} fontFamily={SERIF} fontSize={40} fill={INK} opacity={0.6}>File</text>
      <text x={1215} y={520} fontFamily={SERIF} fontSize={120} fill={INK}>CDK20</text>
    </g>}
    {f >= tS && <g transform={`translate(1520 590) rotate(-9) scale(${0.6 + 0.4 * ks})`} opacity={Math.min(1, (f - tS) / 3)}>
      <InkPath points={[[-170, -52], [170, -52], [170, 40], [-170, 40], [-170, -52]]} color={RED} seed={305} size={7} pressure="marker"/>
      <text x={0} y={22} fontFamily={SERIF} fontSize={78} fill={RED} textAnchor="middle" letterSpacing={6}>SUSPECT</text>
    </g>}
    <Word x={1180} y={730} size={60} f={f} t0={tN}>not the only cause</Word>
  </Full>;
};

// ---- 3-09 B (left): lock drawn on "lock"; on "nobody can see" a radial ink vignette closes round the lock, leaving a warm
// lamp-like pool (r 0.12H) that darkens to 70 % ink over a further 0.3H; paper-white key on "key", "?" on "dark".
// The person is never darkened (the vignette is masked off the person side).
const LC = {x: 1400, y: 465}; // lock centre (lock drawn at translate(1400 420) scale 0.75)
const G309 = ({f, out}) => {
  const tL = wf(1.392) - 6, tD = wf(1.913) - 5, tK = wf(4.317) - 6, tQ = wf(4.878) - 5;
  const dk = outCubic(ramp(f, tD, tD + 12));
  return <Full opacity={exitK(f, out)}>
    <defs>
      <radialGradient id="s309-dark" cx={LC.x} cy={LC.y} r={0.42 * H} gradientUnits="userSpaceOnUse">
        <stop offset="0" stopColor={INK} stopOpacity={0}/>
        <stop offset={0.12 / 0.42} stopColor={INK} stopOpacity={0}/>
        <stop offset="1" stopColor={INK} stopOpacity={0.7}/>
      </radialGradient>
      <radialGradient id="s309-warm" cx={LC.x} cy={LC.y} r={0.12 * H} gradientUnits="userSpaceOnUse">
        <stop offset="0" stopColor="#FFE7B0" stopOpacity={0.45}/>
        <stop offset="1" stopColor="#FFE7B0" stopOpacity={0}/>
      </radialGradient>
      <linearGradient id="s309-fade" x1="990" x2="1300" y1="0" y2="0" gradientUnits="userSpaceOnUse">
        <stop offset="0" stopColor="#fff" stopOpacity={0}/><stop offset="1" stopColor="#fff" stopOpacity={1}/>
      </linearGradient>
      <mask id="s309-side"><rect x={0} y={0} width={W} height={H} fill="url(#s309-fade)"/></mask>
    </defs>
    {f >= tL && <g transform="translate(1400 420) scale(0.75)"><Lock progress={outCubic(ramp(f, tL, tL + 11))}/></g>}
    {dk > 0 && <g opacity={dk} mask="url(#s309-side)">
      <rect x={0} y={0} width={W} height={H} fill="url(#s309-dark)"/>
      <circle cx={LC.x} cy={LC.y} r={0.12 * H} fill="url(#s309-warm)"/>
    </g>}
    {f >= tK && <g transform="translate(1480 770) rotate(-12)"><Key progress={outCubic(ramp(f, tK, tK + 11))} color={PAPER} seed={44}/></g>}
    <Word x={1770} y={660} size={130} f={f} t0={tQ} color={PAPER}>?</Word>
  </Full>;
};

// ---- 4-04 C (left, turns to ask): big "?" and a small floppy red tail (the low-confidence tail) ----
const G404 = ({f, out}) => {
  const tQ = wf(0.463) - 6, tT = wf(1.064) - 5;
  const tail = Array.from({length: 40}, (_, i) => [1560 + i * 6, 520 + 34 * Math.sin(i * 0.45 + f * 0.25) * (i / 40)]);
  return <Full opacity={exitK(f, out)}>
    <Word x={1360} y={640} size={300} f={f} t0={tQ} anchor="middle">?</Word>
    {f >= tT && <InkPath points={tail} color={RED} seed={404} size={8} progress={outCubic(ramp(f, tT, tT + 10))} pressure="marker"/>}
  </Full>;
};

// ---- 4-05 B (left): ink scissors snip twice, the red tail drops (PropScissors); then "AI: made the guess" and
// "Human: caught the problem" with "problem" circled in red ----
export const Scissors = ({f, x, y, s}) => {
  if (f < 0) return null;
  const d = ramp(f, 0, 10);
  const open = f < 12 ? 1 : f < 16 ? 1 - outCubic(ramp(f, 12, 16)) : f < 20 ? outCubic(ramp(f, 16, 20)) : 1 - outCubic(ramp(f, 20, 24));
  const a = (6 + 20 * open) * Math.PI / 180;
  const blade = sgn => {
    const tip = [-Math.cos(sgn * a) * 300, -Math.sin(sgn * a) * 300];
    const ra = sgn * (a + 0.35), ring = [Math.cos(ra) * 160, Math.sin(ra) * 160];
    return <g key={sgn}>
      <InkPath points={handLine([0, 0], tip, {bow: sgn * 16})} color={INK} seed={30 + sgn} size={8} progress={d} pressure="nib"/>
      <InkPath points={handLine([0, 0], tip, {bow: sgn * 3})} color={INK} seed={32 + sgn} size={5} progress={d} pressure="nib"/>
      <InkPath points={handLine([0, 0], [ring[0] * 0.6, ring[1] * 0.6])} color={INK} seed={34 + sgn} size={8} progress={d}/>
      <InkPath points={loopPts(ring[0], ring[1], 48, 40, {seed: 36 + sgn, turns: 1.1, rot: ra})} color={INK} seed={36 + sgn} size={8} progress={d}/>
    </g>;
  };
  const cut = 24, fall = Math.max(0, f - cut), dy = 0.9 * fall * fall, fade = 1 - ramp(f, cut + 6, cut + 16);
  const tail = Array.from({length: 22}, (_, i) => [-200 + 26 * Math.sin(i * 0.9) + 10 * Math.sin(i * 2.3), 14 + i * 9]);
  return <g transform={`translate(${x} ${y}) scale(${s})`}>
    {fade > 0 && <g transform={`translate(${-fall * 3} ${dy}) rotate(${fall * 2} -200 14)`} opacity={fade}>
      <InkPath points={tail} color={RED} seed={50} size={7} progress={ramp(f, 0, 10)} pressure="marker"/>
    </g>}
    {blade(1)}{blade(-1)}
    <circle cx={0} cy={0} r={7} fill={INK}/>
  </g>;
};
// "problem" set a little apart so its red circle keeps a full space from "the"
const PX_ = () => 1180 + textW("Human: caught the ", 54) + 18;
const Tick = ({x, y, f, t0, seed}) => f < t0 ? null :
  <InkPath points={[[x, y - 18], [x + 16, y], [x + 50, y - 46]]} color={RED} seed={seed} size={8} progress={outCubic(ramp(f, t0, t0 + 8))} pressure="marker"/>;
const G405 = ({f, out}) => {
  const PX = PX_(), tS = wf(0.611) - 10, tA = wf(1.953) - 5, tH = wf(3.576) - 5, tP = wf(4.417) - 4;
  return <Full opacity={exitK(f, out)}>
    <Scissors f={f - tS} x={1640} y={380} s={0.8}/>
    <Word x={1180} y={650} size={54} f={f} t0={tA}>AI: made the guess</Word>
    <Word x={1180} y={750} size={54} f={f} t0={tH}>Human: caught the</Word>
    <Word x={PX} y={750} size={54} f={f} t0={tH}>problem</Word>
    {f >= tP && (() => { const x0 = PX, w = textW("problem", 54);
      return <InkPath points={loopPts(x0 + w / 2, 750 - 16, w / 2 + 8, 32, {seed: 453, turns: 1.1})} color={RED} seed={453} size={5}
        progress={outCubic(ramp(f, tP, tP + 10))} pressure="marker"/>; })()}
  </Full>;
};

// ---- 4-08 A (left): trial-and-error loop on "trial and error"; on "light speed" a cyan light trail (this segment's
// only cyan) sweeps from the person side into the loop and the loop spins fast. ----
const LOOP = {x: 1520, y: 470, r: 150};
const LOOP_WORDS = ["think", "make", "test", "fix"];
// reused by 8-07 (same loop, same trail)
export const TrialLoop = ({f, out, tL, tT}) => {
  const kl = outCubic(ramp(f, tL, tL + 11));
  const spin = f < tT ? 0 : 720 * outCubic(ramp(f, tT, tT + 24));
  // trail (from PropTrail): clean SIGNAL line, every frame
  const path = quad([1200, 640], [1330, 700], [LOOP.x - LOOP.r * 0.9, LOOP.y + 70], 60);
  const lf = f - tT, head = outExpo(ramp(lf, 0, 12)) * (path.length - 1), len = 26;
  const fade = 1 - ramp(lf, 14, 30);
  const segs = [];
  if (lf >= 0) for (let i = Math.max(1, Math.floor(head - len)); i <= Math.floor(head); i++) {
    const k = 1 - (head - i) / len;
    segs.push(<line key={i} x1={path[i - 1][0]} y1={path[i - 1][1]} x2={path[i][0]} y2={path[i][1]} stroke={CYAN} strokeWidth={2 + 12 * k} strokeLinecap="round" opacity={k}/>);
  }
  return <Full opacity={exitK(f, out)}>
    {f >= tL && <g opacity={enter(f, tL)}>
      <g transform={`rotate(${spin} ${LOOP.x} ${LOOP.y})`}>
        <InkPath points={loopPts(LOOP.x, LOOP.y, LOOP.r, LOOP.r, {a0: -1.3, turns: 0.9, seed: 81, spiral: 0})} color={INK} seed={81} size={6} progress={kl} pressure="nib"/>
        <InkPath points={(() => { const a = -1.3 + 0.9 * 2 * Math.PI, ex = LOOP.x + Math.cos(a) * LOOP.r, ey = LOOP.y + Math.sin(a) * LOOP.r;
          return [[ex - 26, ey - 8], [ex, ey], [ex - 6, ey + 26]]; })()} color={INK} seed={82} size={6} progress={ramp(kl, 0.8, 1)} pressure="marker"/>
      </g>
      {LOOP_WORDS.map((w, i) => {
        const a = (-90 + i * 90) * Math.PI / 180 + spin * Math.PI / 180;
        return <text key={w} x={LOOP.x + Math.cos(a) * (LOOP.r + 62)} y={LOOP.y + Math.sin(a) * (LOOP.r + 62) + 16} fontFamily={SERIF} fontSize={46}
          fill={INK} textAnchor="middle">{w}</text>;
      })}
    </g>}
    {segs.length > 0 && <g opacity={fade}>
      <filter id="s408-glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="8"/></filter>
      <g filter="url(#s408-glow)">{segs}</g>{segs}
      {Array.from({length: 8}, (_, i) => {
        const j = Math.max(0, Math.floor(head - hash(i, 3) * len * 1.4)), q = path[j];
        return <circle key={i} cx={q[0] + (hash(i, 4) - 0.5) * 30} cy={q[1] + (hash(i, 5) - 0.5) * 30} r={1.5 + hash(i, 6) * 3} fill={CYAN}/>;
      })}
    </g>}
  </Full>;
};

const G408 = ({f, out}) => <TrialLoop f={f} out={out} tL={wf(4.376) - 5} tT={wf(7.239) - 5}/>;

// ---- 4-11 D (right, interrupts): computer screen, trophy on "computer", "?" on "winners" (motion side = left, x <= 700) ----
const G411 = ({f, out}) => {
  const tM = wf(0.504) - 5, tT = wf(2.211) - 5, tQ = wf(3.195) - 5;
  const km = outCubic(ramp(f, tM, tM + 11)), kt = outCubic(ramp(f, tT, tT + 10));
  return <Full opacity={exitK(f, out)}>
    {f >= tM && <g opacity={enter(f, tM)}>
      <InkPath points={[[170, 340], [540, 340], [540, 590], [170, 590], [170, 340]]} color={INK} seed={411} size={8} progress={km} pressure="nib"/>
      <InkPath points={[[355, 590], [355, 640]]} color={INK} seed={412} size={7} progress={km} pressure="nib"/>
      <InkPath points={[[290, 645], [420, 645]]} color={INK} seed={413} size={7} progress={km} pressure="nib"/>
    </g>}
    {f >= tT && <g>
      <InkPath points={[[310, 400], [400, 400], [392, 460], [372, 486], [338, 486], [318, 460], [310, 400]]} color={RED} seed={414} size={6} progress={kt} pressure="marker"/>
      <InkPath points={loopPts(300, 425, 18, 22, {a0: -1.6, turns: 0.5, seed: 415, spiral: 0})} color={RED} seed={415} size={5} progress={kt} pressure="marker"/>
      <InkPath points={loopPts(410, 425, 18, 22, {a0: -1.6, turns: -0.5, seed: 416, spiral: 0})} color={RED} seed={416} size={5} progress={kt} pressure="marker"/>
      <InkPath points={[[355, 486], [355, 515], [325, 530], [385, 530]]} color={RED} seed={417} size={5} progress={kt} pressure="marker"/>
    </g>}
    <Word x={600} y={560} size={200} f={f} t0={tQ}>?</Word>
  </Full>;
};

// ---- 4-12 A (left): "A docking score is a clue, not proof." -> "docking score =", "a clue", "not proof"; on "not proof"
// a vermilion underline under "a clue" (proof itself is never struck) ----
const G412 = ({f, out}) => {
  const tD = wf(1.834) - 5, tC = wf(3.676) - 5, tP = wf(4.437) - 5, tX = tP + 11;
  return <Full opacity={exitK(f, out)}>
    <Word x={1180} y={380} size={58} f={f} t0={tD} opacity={0.75}>docking score =</Word>
    <Word x={1180} y={540} size={150} f={f} t0={tC}>a clue</Word>
    <Word x={1180} y={730} size={150} f={f} t0={tP}>not proof</Word>
    {f >= tX && <InkLine from={[1176, 572]} to={[1180 + textW("a clue", 150) + 6, 568]} bow={-4} over={6} seed={421} size={11} color={RED}
      progress={outCubic(ramp(f, tX, tX + 10))} pressure="marker"/>}
  </Full>;
};

// ---- segment configs, script order. src = 1080p30 copies of 5_place/<name>_wide.mp4 ----
export const S34_SEGS = [
  {id: "3-01", who: "D", side: "left", src: "oncam2/s34/D_cam_3-01.mp4", in: 0, out: 183, G: G301, trig: "lock / key"},
  {id: "3-06", who: "D", side: "left", src: "oncam2/s34/D_cam_3-06.mp4", in: 0, out: 334, G: G306, trig: "a / strong / Not"},
  {id: "3-09", who: "B", side: "left", src: "oncam2/s34/B_cam_3-09.mp4", in: 0, out: 165, G: G309, trig: "lock / nobody / key / dark"},
  {id: "4-04", who: "C", side: "left", src: "oncam2/s34/C_cam_4-04.mp4", in: 0, out: 54, G: G404, trig: "So / what"},
  {id: "4-05", who: "B", side: "left", src: "oncam2/s34/B_cam_4-05.mp4", in: 0, out: 153, G: G405, trig: "cut / AI / human"},
  {id: "4-08", who: "A", side: "left", src: "oncam2/s34/A_cam_4-08.mp4", in: 0, out: 246, G: G408, trig: "trial / light"},
  {id: "4-11", who: "D", side: "right", src: "oncam2/s34/D_cam_4-11.mp4", in: 0, out: 114, G: G411, trig: "Wait / computer / winners"},
  {id: "4-12", who: "A", side: "left", src: "oncam2/s34/A_cam_4-12.mp4", in: 0, out: 215, G: G412, trig: "docking / clue / not / proof"},
];
export const S34_GAP = 15;
export const S34_FRAMES = reelLen(S34_SEGS, S34_GAP);
export const V3OnCam2S34 = () => <Reel segs={S34_SEGS} gap={S34_GAP}/>;
export const S34_SINGLE = S34_SEGS.map(s => ({id: "V3-OnCam2-S34-" + s.id, frames: segLen(s), component: () => <Segment seg={s}/>}));
