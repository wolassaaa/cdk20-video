import {AbsoluteFill, OffthreadVideo, Loop, staticFile, useCurrentFrame, interpolate} from "remotion";
import data from "./hands_cut.json";

// T1 feasibility test: holograms driven by MediaPipe hand tracking on real footage.
// Each palm gets a ring; with both hands visible the CDK20 hologram floats between them and scales with their spread;
// a pinch (thumb tip close to index tip) lights a spark.
const CYAN = "#7FE3FA";
const ORANGE = "#FF8A4C";
const MONO = 'Consolas, "Cascadia Mono", monospace';
const PINCH = 0.35;

// presence of a hand, faded over a few frames so rings do not pop on and off
const presence = (frame, side) => {
  let n = 0;
  for (let k = -3; k <= 3; k++) {
    const f = data.frames[frame + k];
    if (f && f[side]) n++;
  }
  return n / 7;
};

const PalmRing = ({hand, frame, alpha}) => {
  const [x, y] = hand.palm;
  const r = hand.size * 0.75;
  const spin = frame * 2;
  const pinched = hand.pinch < PINCH;
  const [tx, ty] = hand.pts[4];
  const [ix, iy] = hand.pts[8];
  return (
    <g opacity={alpha}>
      <circle cx={x} cy={y} r={r} fill="none" stroke={CYAN} strokeWidth="2" opacity="0.9" />
      <circle cx={x} cy={y} r={r * 1.18} fill="none" stroke={CYAN} strokeWidth="1" strokeDasharray="6 10"
        transform={`rotate(${spin} ${x} ${y})`} opacity="0.7" />
      {[4, 8, 12, 16, 20].map((k) => (
        <g key={k}>
          <line x1={x} y1={y} x2={hand.pts[k][0]} y2={hand.pts[k][1]} stroke={CYAN} strokeWidth="1" opacity="0.35" />
          <circle cx={hand.pts[k][0]} cy={hand.pts[k][1]} r="5" fill={CYAN} />
        </g>
      ))}
      {pinched ? (
        <g>
          <circle cx={(tx + ix) / 2} cy={(ty + iy) / 2} r="16" fill={ORANGE} opacity="0.9" />
          <circle cx={(tx + ix) / 2} cy={(ty + iy) / 2} r="34" fill="none" stroke={ORANGE} strokeWidth="2" />
          <text x={(tx + ix) / 2 + 40} y={(ty + iy) / 2 + 6} fill={ORANGE} fontFamily={MONO} fontSize="22">PINCH</text>
        </g>
      ) : null}
    </g>
  );
};

export const HandHolo = () => {
  const frame = useCurrentFrame();
  const hands = data.frames[frame] || {};
  const L = hands.Left, R = hands.Right;
  const both = L && R;
  // hologram between the palms: centre, spread and tilt from the two palm points
  let holo = null;
  if (both) {
    const [ax, ay] = L.palm, [bx, by] = R.palm;
    const spread = Math.hypot(bx - ax, by - ay);
    const size = Math.max(160, spread * 1.05);
    const angle = (Math.atan2(by - ay, bx - ax) * 180) / Math.PI;
    const tilt = angle > 90 ? angle - 180 : angle < -90 ? angle + 180 : angle;
    holo = {cx: (ax + bx) / 2, cy: (ay + by) / 2 - size * 0.2, size, tilt};
  }
  const holoAlpha = Math.min(presence(frame, "Left"), presence(frame, "Right"));
  return (
    <AbsoluteFill style={{background: "#000"}}>
      <OffthreadVideo src={staticFile("hand_cut.mp4")} />
      {/* darken the room a little so the hologram reads, like the holo-lab lighting would */}
      <AbsoluteFill style={{background: "rgba(4,10,18,0.35)"}} />
      {holo ? (
        <>
          {/* light spill on the hands and wall */}
          <AbsoluteFill style={{mixBlendMode: "screen", opacity: holoAlpha,
            background: `radial-gradient(circle at ${holo.cx}px ${holo.cy}px, rgba(90,200,250,0.28), rgba(0,0,0,0) ${holo.size * 0.9}px)`}} />
          <div style={{position: "absolute", left: holo.cx - holo.size / 2, top: holo.cy - (holo.size * 9) / 32, width: holo.size,
            height: (holo.size * 9) / 16, transform: `rotate(${holo.tilt * 0.5}deg)`, mixBlendMode: "screen", opacity: holoAlpha}}>
            <Loop durationInFrames={240}>
              <OffthreadVideo src={staticFile("t3.mp4")} muted style={{width: "100%", height: "100%"}} />
            </Loop>
          </div>
        </>
      ) : null}
      {/* hands-only layer (alpha from tracked landmarks) goes over the hologram, so fingers pass in front of it */}
      <OffthreadVideo src={staticFile("hands_only.webm")} transparent muted
        style={{position: "absolute", width: 720, height: 1280, filter: "brightness(0.66) saturate(0.95)"}} />
      <svg width="720" height="1280" style={{position: "absolute", mixBlendMode: "screen"}}>
        {L ? <PalmRing hand={L} frame={frame} alpha={presence(frame, "Left")} /> : null}
        {R ? <PalmRing hand={R} frame={frame} alpha={presence(frame, "Right")} /> : null}
      </svg>
      <div style={{position: "absolute", left: 32, top: 40, fontFamily: MONO, fontSize: 20, color: CYAN, letterSpacing: 2}}>
        T1 HAND-TRACKING TEST · {L && R ? "2 HANDS" : L || R ? "1 HAND" : "NO HAND"}
      </div>
    </AbsoluteFill>
  );
};
