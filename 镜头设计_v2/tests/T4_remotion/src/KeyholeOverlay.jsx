import {AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, interpolate, Easing} from "remotion";
import anchors from "./T3_anchors.json";

const CYAN = "#7FE3FA";
const ORANGE = "#FF8A4C";
const SANS = '"Segoe UI", "Microsoft YaHei", sans-serif';
const MONO = 'Consolas, "Cascadia Mono", monospace';

// fade + slide in over 12 frames starting at `from`, optional fade out at `to`
const useReveal = (from, to = 1e6) => {
  const f = useCurrentFrame();
  const inP = interpolate(f, [from, from + 12], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic)});
  const outP = interpolate(f, [to, to + 10], [1, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  return {opacity: inP * outP, transform: `translateY(${(1 - inP) * 10}px)`};
};

// Per-frame screen positions exported from the Blender scene (T3_keyhole_anim.py), so callouts stay on their 3D points.
const at = (frame, key) => {
  const a = anchors[Math.min(anchors.length - 1, Math.max(0, frame))][key];
  return [a[0] * 1920, a[1] * 1080];
};

const Callout = ({from, to, anchor, dx, dy, color, title, sub, strike}) => {
  const f = useCurrentFrame();
  const r = useReveal(from, to);
  const draw = interpolate(f, [from, from + 14], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const [ax, ay] = at(f, anchor);
  const ex = ax + dx, ey = ay + dy;
  const strikeP = strike ? interpolate(f, [strike, strike + 10], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"}) : 0;
  return (
    <>
      <svg width="1920" height="1080" style={{position: "absolute", opacity: r.opacity}}>
        <circle cx={ax} cy={ay} r="6" fill={color} />
        <circle cx={ax} cy={ay} r="14" fill="none" stroke={color} strokeWidth="1.5" />
        <line x1={ax} y1={ay} x2={ax + dx * draw} y2={ay + dy * draw} stroke={color} strokeWidth="1.5" />
      </svg>
      <div style={{position: "absolute", left: ex + (dx > 0 ? 14 : -14), top: ey - 22, transform: `${r.transform} translateX(${dx > 0 ? 0 : -100}%)`,
        opacity: r.opacity, textAlign: dx > 0 ? "left" : "right", fontFamily: SANS}}>
        <div style={{fontSize: 30, fontWeight: 600, color, position: "relative", display: "inline-block"}}>
          {title}
          {strike ? <span style={{position: "absolute", left: 0, top: "52%", height: 2, width: `${strikeP * 100}%`, background: color}} /> : null}
        </div>
        <div style={{fontFamily: MONO, fontSize: 18, color: "#B9CBD8", marginTop: 4}}>{sub}</div>
      </div>
    </>
  );
};

export const KeyholeOverlay = () => {
  const head = useReveal(8);
  const cite = useReveal(20);
  const sub1 = useReveal(15, 120);
  const sub2 = useReveal(132);
  return (
    <AbsoluteFill style={{background: "#000"}}>
      <OffthreadVideo src={staticFile("t3.mp4")} />
      <div style={{position: "absolute", left: 96, top: 80, fontFamily: MONO, color: CYAN, ...head}}>
        <div style={{fontSize: 18, letterSpacing: 3}}>PREDICTED STRUCTURE · NOT MEASURED</div>
        <div style={{fontFamily: SANS, fontSize: 44, fontWeight: 700, color: "#EAF4FA", marginTop: 6}}>CDK20</div>
        <div style={{fontSize: 18, color: "#9FB4C4"}}>AlphaFold DB · AF-Q8IZL9-F1</div>
      </div>
      <Callout from={100} to={225} anchor="arg305" dx={-330} dy={-170} color={ORANGE} title="Arg305 in the ATP pocket" sub="low-confidence tail · residues 303–346" strike={165} />
      <Callout from={196} anchor="pocket" dx={300} dy={150} color={CYAN} title="Pocket cleared" sub="model used: residues 1–302" />
      <Callout from={60} to={150} anchor="met84" dx={300} dy={-120} color="#C9F2FF" title="Met84" sub="hinge · where the design must hold on" />
      <div style={{position: "absolute", right: 96, bottom: 150, fontFamily: MONO, fontSize: 16, color: "#B5C6D3", padding: "4px 10px",
        background: "rgba(4,10,18,0.72)", borderRadius: 3, ...cite}}>Ren et al., Chem. Sci. 2023, 14, 1443</div>
      <div style={{position: "absolute", left: 0, right: 0, bottom: 64, textAlign: "center", fontFamily: SANS, fontSize: 38, color: "#F2F6F9", textShadow: "0 2px 8px #000"}}>
        <span style={{...sub1, display: "inline-block"}}>The prediction came with a problem built in.</span>
      </div>
      <div style={{position: "absolute", left: 0, right: 0, bottom: 64, textAlign: "center", fontFamily: SANS, fontSize: 38, color: "#F2F6F9", textShadow: "0 2px 8px #000"}}>
        <span style={{...sub2, display: "inline-block"}}>Its own low-confidence tail was sitting in the keyhole.</span>
      </div>
    </AbsoluteFill>
  );
};
