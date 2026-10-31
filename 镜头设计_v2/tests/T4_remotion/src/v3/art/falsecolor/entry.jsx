// HKBU SCIE1007 coursework science video. falsecolor art direction: the type and the colour bar over the picture layers.
// Pictures come from styleframes/art/falsecolor/code. Text here is verbatim from the art brief.
import React from "react";
import {AbsoluteFill, Composition, Img, registerRoot, staticFile, useCurrentFrame} from "remotion";
import {loadFont as loadMono} from "@remotion/google-fonts/IBMPlexMono";
import {loadFont as loadSerif} from "@remotion/google-fonts/IBMPlexSerif";
import LUTS from "./luts.json";

const MONO = loadMono("normal", {weights: ["400", "500", "600"], subsets: ["latin"]}).fontFamily;
const SERIF = loadSerif("normal", {weights: ["300", "400", "500"], subsets: ["latin"]}).fontFamily;

const INK = "#FFF4C4";          // top of every map in the family
const BAR = {x: 1752, y: 120, w: 50, h: 760};

// Evidence grades are line types, so they survive with the colour turned off. A plate and the frame of the bar always agree.
const line = (grade, ink = INK) => ({
  measured: {border: "none"},                         // solid plate, solid bar edge
  predicted: {border: `7px double ${ink}`},           // double rule
  ours: {border: `2px solid ${ink}`},                 // single rule
  schematic: {border: `2px dashed ${ink}`},           // dashed rule
})[grade];

const Plate = ({grade, x, y, right, bottom, size = 36, ink = INK, children}) => (
  <div style={{position: "absolute", left: x, top: y, right, bottom, fontFamily: MONO, fontWeight: 500, fontSize: size, lineHeight: 1.1, padding: "12px 20px",
    whiteSpace: "nowrap", color: grade === "measured" ? "#120008" : ink, background: grade === "measured" ? INK : "rgba(0,0,0,0.0)", ...line(grade, ink)}}>{children}</div>
);

// The colour bar: the one mark that is on screen in every shot of the film. Its label says what the colour means. Ticks sit at true positions on the map.
const ColourBar = ({map, grade, label, ticks = [], empty = false, ink = INK}) => {
  const stops = LUTS[map].map((c, i, a) => `${c} ${(i / (a.length - 1) * 100).toFixed(2)}%`).join(",");
  const frame = grade === "measured" ? {outline: `2px solid ${ink}`} : line(grade, ink);
  return (
    <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, pointerEvents: "none"}}>
      <div style={{position: "absolute", left: BAR.x, top: BAR.y, width: BAR.w, height: BAR.h, boxSizing: "border-box", background: empty ? "transparent" : `linear-gradient(to top,${stops})`, backgroundClip: "padding-box", backgroundOrigin: "padding-box", ...frame}} />
      {ticks.map(({at, text, strong}) => (
        <div key={text} style={{position: "absolute", right: 1920 - BAR.x + 14, top: BAR.y + BAR.h * (1 - at) - 26, fontFamily: MONO, fontWeight: strong ? 600 : 400, fontSize: 36, lineHeight: "52px", color: ink, display: "flex", alignItems: "center", gap: 10, textShadow: "0 0 10px rgba(0,0,0,0.75)"}}>
          {text}<span style={{display: "inline-block", width: 14, height: 3, background: ink}} />
        </div>
      ))}
      <div style={{position: "absolute", left: BAR.x + BAR.w + 18, top: BAR.y + BAR.h, width: BAR.h, height: 44, transformOrigin: "0 0", transform: "rotate(-90deg)", fontFamily: MONO, fontSize: 36, lineHeight: "44px", color: ink, textAlign: "center", whiteSpace: "nowrap"}}>{label}</div>
    </div>
  );
};

const Still = ({src, children, bg = "#000"}) => (
  <AbsoluteFill style={{background: bg}}>
    {src ? <Img src={staticFile(src)} style={{position: "absolute", width: 1920, height: 1080}} /> : null}
    {children}
  </AbsoluteFill>
);

const T1 = () => (
  <Still src="t1_bg.png">
    <div style={{position: "absolute", left: 1010, top: 640, width: 720, color: INK, fontFamily: SERIF}}>
      <div style={{fontSize: 184, lineHeight: 0.98, fontWeight: 300, letterSpacing: "-0.02em"}}>1,412</div>
      <div style={{fontSize: 52, lineHeight: 1.15, fontWeight: 400, marginTop: 10}}>deaths in Hong Kong, 2022</div>
    </div>
    <Plate grade="schematic" x={1010} y={914}>schematic · not patient data</Plate>
    <ColourBar map="s1_ember" grade="schematic" label="distance to nearest vessel, mm" ticks={[{at: 60 / 66, text: "60"}, {at: 40 / 66, text: "40"}, {at: 20 / 66, text: "20"}, {at: 0, text: "0"}]} />
  </Still>
);

const T2 = () => (
  <Still src="t2_bg.png">
    <div style={{position: "absolute", left: 96, top: 214, width: 800, color: INK, fontFamily: SERIF, fontWeight: 400, fontSize: 64, lineHeight: 1.2, textShadow: "0 0 24px rgba(10,4,30,0.55)"}}>
      How can computer-aided methods help scientists find and assess potential cancer drug candidates?
    </div>
    <ColourBar map="s2_iron" grade="ours" label="room brightness, not temperature" ticks={[{at: 1, text: "bright"}, {at: 0, text: "dark"}]} />
  </Still>
);

const LILAC = "#A794C8";
const T3 = () => (
  <Still>
    <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
      <defs>
        <filter id="g" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="10" /></filter>
        {/* the last of the signal: the outline dies away downward */}
        <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={LILAC} />
          <stop offset="0.5" stopColor="#6C5A94" />
          <stop offset="1" stopColor="#1C1430" />
        </linearGradient>
      </defs>
      <path filter="url(#g)" fill="none" stroke="url(#fade)" strokeWidth="7" opacity="0.5" d="M 856 720 L 906 482 A 130 130 0 1 1 1014 482 L 1064 720 Z" />
      <path fill="none" stroke="url(#fade)" strokeWidth="3.5" d="M 856 720 L 906 482 A 130 130 0 1 1 1014 482 L 1064 720 Z" />
    </svg>
    <div style={{position: "absolute", left: 0, width: 1920, top: 792, textAlign: "center", fontFamily: MONO, fontWeight: 400, fontSize: 40, lineHeight: 1.2, color: LILAC}}>no one had measured CDK20's shape</div>
    <Plate grade="schematic" x={96} y={932} ink={LILAC}>schematic</Plate>
    <ColourBar map="s3_dusk" grade="schematic" label="signal" empty ink={LILAC} ticks={[{at: 0, text: "0"}]} />
  </Still>
);

const T4 = () => (
  <Still src="t4_bg.png">
    <Plate grade="predicted" x={96} y={84} size={40}>AlphaFold DB v6 · predicted</Plate>
    <ColourBar map="s4_signal" grade="predicted" label="pLDDT, the model's own confidence" ticks={[{at: 0.81, text: "90", strong: true}, {at: 0.49, text: "70"}, {at: 0.25, text: "50"}, {at: 0, text: "0"}]} />
  </Still>
);

const T5 = () => (
  <Still src="t5_bg.png">
    <div style={{position: "absolute", left: 96, top: 150, width: 880, color: INK, fontFamily: MONO}}>
      <div style={{fontSize: 44, lineHeight: 1.2, fontWeight: 400}}>Enzyme IC50</div>
      <div style={{fontSize: 108, lineHeight: 1.12, fontWeight: 500, marginTop: 24, letterSpacing: "-0.04em", whiteSpace: "nowrap"}}>048 =<br />33.4 ± 22.6 nM</div>
      <div style={{fontFamily: SERIF, fontSize: 46, lineHeight: 1.22, fontWeight: 400, marginTop: 36, width: 760}}>Just this much cuts the enzyme's activity in half.</div>
    </div>
    <Plate grade="measured" x={96} y={786} size={38}>MEASURED · Ren 2023, Fig. 9A</Plate>
    <Plate grade="ours" x={888} y={964} size={36}>OUR RE-DOCKING</Plate>
    <ColourBar map="s5_contact" grade="ours" label="distance to 048, Å" ticks={[{at: 1, text: "2"}, {at: 1 - 2 / 4.5, text: "4"}, {at: 1 - 4 / 4.5, text: "6"}]} />
  </Still>
);

const NAMES = ["Target", "Hit", "Improve", "Cells & animals", ["Clinical", "trials", "1-2-3"], "Approval"];
const X0 = 96, X1 = 1660, Y0 = 56, Y1 = 660, CELL = (X1 - X0) / 6;
const T6 = () => (
  <Still src="t6_bg.png">
    <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
      {[1, 2].map((k) => <line key={k} x1={X0 + k * CELL} x2={X0 + k * CELL} y1={0} y2={Y1} stroke="#000" strokeWidth={4} />)}
      {[3, 4, 5].map((k) => <rect key={k} x={X0 + k * CELL + 6} y={Y0} width={CELL - 12} height={Y1 - Y0} fill="none" stroke="#FFF4C4" strokeWidth={2.5} strokeDasharray="12 10" opacity={0.75} />)}
      <line x1={X0 + 3 * CELL} x2={X0 + 3 * CELL} y1={0} y2={1080} stroke="#FFF4C4" strokeWidth={5} />
    </svg>
    <div style={{position: "absolute", left: X0 + 3 * CELL - 420, top: 524, width: 396, textAlign: "right", fontFamily: MONO, fontWeight: 600, fontSize: 112, lineHeight: 1, color: "#000"}}>048</div>
    {NAMES.map((n, k) => (
      <div key={k} style={{position: "absolute", left: X0 + k * CELL + (k > 2 ? 24 : 14), top: Y1 + 26, width: CELL - 20, fontFamily: MONO, fontWeight: 500, fontSize: 36, lineHeight: 1.16, color: INK, opacity: k > 2 ? 0.8 : 1}}>
        {Array.isArray(n) ? n.map((t) => <div key={t} style={{whiteSpace: "nowrap"}}>{t}</div>) : n}
      </div>
    ))}
    {[3, 4, 5].map((k) => <div key={k} style={{position: "absolute", left: X0 + k * CELL + 24, top: Y0 + 26, width: CELL - 40, fontFamily: MONO, fontWeight: 400, fontSize: 36, lineHeight: 1.16, color: INK, opacity: 0.8}}>not reported</div>)}
    <ColourBar map="s6_route" grade="schematic" label="stations reached" ticks={[{at: 1, text: "6"}, {at: 0.5, text: "3", strong: true}, {at: 0, text: "0"}]} />
  </Still>
);

const CS = [["S1", 141], ["S2", 142], ["S3", 129], ["S4", 213], ["S5", 139], ["S6", 151], ["S7", 49], ["S8", 99]];
const ColourScript = () => {
  const total = CS.reduce((a, b) => a + b[1], 0);
  let x = 0;
  return (
    <AbsoluteFill style={{background: "#000"}}>
      <Img src={staticFile("colour_script_bg.png")} style={{position: "absolute", width: 1920, height: 480}} />
      {CS.map(([n, s]) => {
        const left = x / total * 1920;
        x += s;
        return <div key={n} style={{position: "absolute", left: left + 10, top: 10, fontFamily: MONO, fontWeight: 600, fontSize: 30, color: INK, textShadow: "0 0 8px #000"}}>{n}</div>;
      })}
    </AbsoluteFill>
  );
};

// Motion test: the bar fills from the top as the surface lights, most certain residues first, so the tail arrives last and cold.
const Reveal = () => {
  const f = useCurrentFrame();
  const R = LUTS.reveal;
  const cut = R[Math.min(f, R.length - 1)];
  const y = BAR.h * (1 - cut ** 2);
  return (
    <Still src={`mo/f${String(f).padStart(3, "0")}.jpg`}>
      <ColourBar map="s4_signal" grade="predicted" label="pLDDT, the model's own confidence" ticks={[{at: 0.81, text: "90", strong: true}, {at: 0.49, text: "70"}, {at: 0.25, text: "50"}, {at: 0, text: "0"}]} />
      <div style={{position: "absolute", left: BAR.x + 7, top: BAR.y + y, width: BAR.w - 14, height: BAR.h - y - 7, background: LUTS.floorSeq[Math.min(f, 179)]}} />
      <Plate grade="predicted" x={96} y={84} size={40}>AlphaFold DB v6 · predicted</Plate>
    </Still>
  );
};

const Root = () => (
  <>
    {[["T1", T1], ["T2", T2], ["T3", T3], ["T4", T4], ["T5", T5], ["T6", T6]].map(([id, C]) => <Composition key={id} id={id} component={C} durationInFrames={1} fps={30} width={1920} height={1080} />)}
    <Composition id="ColourScript" component={ColourScript} durationInFrames={1} fps={30} width={1920} height={480} />
    <Composition id="Reveal" component={Reveal} durationInFrames={180} fps={30} width={1920} height={1080} />
  </>
);

registerRoot(Root);
