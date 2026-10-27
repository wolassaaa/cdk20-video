import {AbsoluteFill, Img, staticFile} from "remotion";
import {loadFont as loadPixel} from "@remotion/google-fonts/PressStart2P";
import {loadFont as loadType} from "@remotion/google-fonts/SpecialElite";
import {loadFont as loadAnton} from "@remotion/google-fonts/Anton";
import {loadFont as loadMarker} from "@remotion/google-fonts/PermanentMarker";
import {loadFont as loadBungee} from "@remotion/google-fonts/Bungee";

// Three concept stills where the style comes from the study itself:
// Heist (the lock-and-key analogy), Arcade (the evidence ladder as levels), Infomercial (the "AI discovers a drug" hype).
const PIXEL = loadPixel().fontFamily, TYPE = loadType().fontFamily, ANTON = loadAnton().fontFamily;
const MARKER = loadMarker().fontFamily, BUNGEE = loadBungee().fontFamily;

// ---------------- Heist: the planning board ----------------
const Pin = ({x, y, color = "#d62828"}) => <div style={{position: "absolute", left: x - 11, top: y - 11, width: 22, height: 22, borderRadius: "50%",
  background: `radial-gradient(circle at 35% 35%, #fff8, ${color} 45%, #5a0000)`, boxShadow: "2px 4px 4px rgba(0,0,0,0.45)", zIndex: 5}}/>;
const Polaroid = ({x, y, w, rot, src, filter, caption, children}) => (
  <div style={{position: "absolute", left: x, top: y, width: w, padding: "14px 14px 64px", background: "#f7f4ec", transform: `rotate(${rot}deg)`,
    boxShadow: "6px 10px 18px rgba(0,0,0,0.45)"}}>
    <div style={{position: "relative", width: "100%", aspectRatio: "16/10", overflow: "hidden", background: "#000"}}>
      <Img src={staticFile(src)} style={{width: "100%", height: "100%", objectFit: "cover", filter}}/>{children}
    </div>
    <div style={{position: "absolute", left: 16, bottom: 14, fontFamily: MARKER, fontSize: 26, color: "#1d1d1d"}}>{caption}</div>
  </div>
);
const Sticky = ({x, y, rot, color = "#ffe45c", children, w = 230}) => <div style={{position: "absolute", left: x, top: y, width: w, padding: 18, background: color,
  transform: `rotate(${rot}deg)`, fontFamily: MARKER, fontSize: 28, lineHeight: 1.15, color: "#222", boxShadow: "4px 8px 12px rgba(0,0,0,0.35)"}}>{children}</div>;

export const ConceptHeist = () => (
  <AbsoluteFill style={{background: "#a8743f"}}>
    <AbsoluteFill style={{backgroundImage: "radial-gradient(rgba(60,30,5,0.35) 1.2px, transparent 1.6px), radial-gradient(rgba(255,230,190,0.18) 1px, transparent 1.4px)",
      backgroundSize: "7px 7px, 11px 11px", backgroundPosition: "0 0, 3px 5px"}}/>
    <AbsoluteFill style={{background: "radial-gradient(ellipse at 50% 45%, transparent 45%, rgba(20,8,0,0.65) 100%)"}}/>
    <svg style={{position: "absolute", left: 0, top: 0, zIndex: 4}} width="1920" height="1080">
      {[[330, 250, 960, 300], [960, 300, 1500, 380], [960, 300, 1080, 720], [1500, 380, 1600, 760], [330, 250, 300, 720]].map(([a, b, c, d], i) =>
        <path key={i} d={`M${a} ${b} Q${(a + c) / 2} ${Math.max(b, d) + 50} ${c} ${d}`} stroke="#c1121f" strokeWidth="3" fill="none"/>)}
    </svg>
    <div style={{position: "absolute", left: 640, top: 40, padding: "10px 34px", background: "#111", color: "#f1f1f1", fontFamily: ANTON, fontSize: 84, letterSpacing: 4,
      transform: "rotate(-1.5deg)", boxShadow: "6px 8px 0 rgba(0,0,0,0.35)", zIndex: 6}}>THE CDK20 JOB</div>
    <Polaroid x={110} y={170} w={430} rot={-4} src="style/body_liver.png" caption="the place: liver (HCC)"/>
    <Pin x={330} y={180}/>
    <Polaroid x={700} y={190} w={560} rot={2} src="style/keyhole.png" filter="grayscale(1) sepia(1) hue-rotate(175deg) saturate(3.2) brightness(0.95)" caption="vault blueprint (AI guess)">
      <svg style={{position: "absolute", inset: 0}} viewBox="0 0 560 350"><ellipse cx="290" cy="150" rx="70" ry="58" fill="none" stroke="#e63946" strokeWidth="6"/></svg>
    </Polaroid>
    <Pin x={960} y={200}/>
    <Polaroid x={1330} y={290} w={420} rot={5} src="style/pose_048.png" caption="key #048: fits AND turns">
      <div style={{position: "absolute", right: 14, bottom: 14, padding: "4px 14px", border: "5px solid #e63946", color: "#e63946", fontFamily: ANTON, fontSize: 44,
        transform: "rotate(-12deg)", background: "rgba(255,255,255,0.15)"}}>15×</div>
    </Polaroid>
    <Pin x={1500} y={300}/>
    <div style={{position: "absolute", left: 160, top: 640, width: 520, padding: "26px 30px", background: "#fbfaf4", transform: "rotate(1.5deg)", fontFamily: TYPE, fontSize: 27,
      color: "#1b1b1b", lineHeight: 1.45, boxShadow: "6px 10px 16px rgba(0,0,0,0.4)", backgroundImage: "repeating-linear-gradient(0deg, transparent 0 38px, #b8d4f0 38px 39px)"}}>
      <div style={{color: "#c1121f", fontSize: 30}}>CASE FILE · HONG KONG</div>
      OBJECTIVE: a key that turns lock CDK20<br/>TOOLS: 8,918 AI-designed keys<br/>MADE: 7 · FITS: 1 · TURNS: #048
    </div>
    <Pin x={300} y={650}/>
    <Sticky x={880} y={690} rot={-6}>30 days to the first fit!</Sticky>
    <Sticky x={1180} y={780} rot={4} color="#ff9ec7">not tried on patients yet</Sticky>
    <Pin x={1080} y={705} color="#2a6f97"/>
    <Pin x={1600} y={770} color="#2a6f97"/>
    {["THE BRIEFER", "THE MAPMAKER", "THE LOCKSMITH", "THE SKEPTIC"].map((r, i) => (
      <div key={r} style={{position: "absolute", left: 1500 + (i % 2) * 190, top: 40 + Math.floor(i / 2) * 120, width: 170, height: 100, background: "#222", color: "#eee",
        fontFamily: TYPE, fontSize: 18, padding: 10, transform: `rotate(${i % 2 ? 3 : -3}deg)`, boxShadow: "4px 6px 10px rgba(0,0,0,0.45)"}}>
        <div style={{width: 34, height: 34, borderRadius: "50%", background: "#777", marginBottom: 6}}/>{"ABCD"[i]} · {r}
      </div>))}
  </AbsoluteFill>
);

// ---------------- Arcade: the evidence ladder as levels ----------------
const Bar = ({label, value, color}) => <div style={{marginTop: 22}}>
  <div style={{fontFamily: PIXEL, fontSize: 18, color: "#cfd8ff"}}>{label}</div>
  <div style={{display: "flex", gap: 4, marginTop: 8}}>{Array.from({length: 10}, (_, i) => <div key={i} style={{width: 26, height: 22, background: i < value ? color : "#26264a"}}/>)}</div>
</div>;
const Level = ({x, y, n, name, state}) => {
  const done = state === "done", stop = state === "stop", locked = state === "locked";
  return <div style={{position: "absolute", left: x, top: y, width: 230, textAlign: "center"}}>
    <div style={{width: 110, height: 110, margin: "0 auto", border: `6px solid ${locked ? "#44446a" : stop ? "#ff3b6b" : "#3df5a6"}`, background: locked ? "#16162e" : "#101030",
      display: "grid", placeItems: "center", fontFamily: PIXEL, fontSize: 40, color: locked ? "#55557a" : "#fff", boxShadow: locked ? "none" : `0 0 18px ${stop ? "#ff3b6b" : "#3df5a6"}`}}>
      {locked ? <svg width="46" height="52" style={{imageRendering: "pixelated"}}><rect x="6" y="22" width="34" height="28" fill="#55557a"/><rect x="12" y="4" width="22" height="22" fill="none" stroke="#55557a" strokeWidth="6"/></svg> : n}
    </div>
    <div style={{fontFamily: PIXEL, fontSize: 16, color: locked ? "#55557a" : "#e8ecff", marginTop: 14, lineHeight: 1.6}}>{name}</div>
    {done || stop ? <div style={{fontFamily: PIXEL, fontSize: 14, color: stop ? "#ff3b6b" : "#3df5a6", marginTop: 6}}>{stop ? "STAGE CLEAR!" : "★ CLEAR"}</div> : null}
  </div>;
};
export const ConceptArcade = () => (
  <AbsoluteFill style={{background: "#07071a"}}>
    <AbsoluteFill style={{backgroundImage: "linear-gradient(#1a1a40 2px, transparent 2px), linear-gradient(90deg, #1a1a40 2px, transparent 2px)", backgroundSize: "48px 48px", opacity: 0.5}}/>
    <div style={{position: "absolute", left: 60, right: 60, top: 40, display: "flex", justifyContent: "space-between", fontFamily: PIXEL, fontSize: 30}}>
      <span style={{color: "#ff3b6b"}}>1UP <span style={{color: "#fff"}}>048</span></span>
      <span style={{color: "#ffd23f"}}>HI-SCORE <span style={{color: "#fff"}}>8918 → 7</span></span>
      <span style={{color: "#3df5ff"}}>DAY <span style={{color: "#fff"}}>30</span></span>
    </div>
    <div style={{position: "absolute", left: 0, right: 0, top: 130, textAlign: "center", fontFamily: PIXEL, fontSize: 64, color: "#ffd23f", textShadow: "6px 6px 0 #ff3b6b"}}>WORTH TESTING?</div>
    <div style={{position: "absolute", left: 80, top: 300, width: 420, padding: 26, border: "6px solid #3df5ff", background: "#0d0d2b", boxShadow: "0 0 24px #3df5ff66"}}>
      <div style={{fontFamily: PIXEL, fontSize: 22, color: "#3df5ff"}}>PLAYER: 048</div>
      <div style={{marginTop: 18, width: 360, height: 220, overflow: "hidden", imageRendering: "pixelated", border: "4px solid #26264a"}}>
        <Img src={staticFile("style/pose_048.png")} style={{width: 90, height: 55, transform: "scale(4)", transformOrigin: "0 0", imageRendering: "pixelated"}}/>
      </div>
      <Bar label="BIND" value={8} color="#3df5a6"/><Bar label="BLOCK ENZYME" value={9} color="#ffd23f"/><Bar label="LIVER CELLS" value={6} color="#ff3b6b"/>
    </div>
    <svg style={{position: "absolute", left: 0, top: 0}} width="1920" height="1080">
      <path d="M690 465 H1480 V705 H690" fill="none" stroke="#3df5a6" strokeWidth="8" strokeDasharray="20 14"/>
      <path d="M1480 705 H690" fill="none" stroke="#44446a" strokeWidth="8" strokeDasharray="20 14"/>
    </svg>
    <Level x={580} y={410} n="1" name="PREDICT" state="done"/>
    <Level x={830} y={410} n="2" name="BIND" state="done"/>
    <Level x={1080} y={410} n="3" name="ENZYME" state="done"/>
    <Level x={1330} y={410} n="4" name="CELLS" state="stop"/>
    <Level x={1080} y={650} n="5" name="ANIMALS" state="locked"/>
    <Level x={830} y={650} n="6" name="PATIENTS" state="locked"/>
    <div style={{position: "absolute", left: 580, top: 930, fontFamily: PIXEL, fontSize: 20, color: "#ff3b6b", lineHeight: 1.8}}>
      001: FITS BUT CAN'T TURN — GAME OVER<br/><span style={{color: "#fff"}}>CONTINUE? ▶ ROUND 2</span></div>
    <div style={{position: "absolute", right: 70, bottom: 50, fontFamily: PIXEL, fontSize: 22, color: "#ffd23f"}}>INSERT COIN</div>
    <AbsoluteFill style={{backgroundImage: "repeating-linear-gradient(0deg, rgba(0,0,0,0.5) 0 2px, transparent 2px 4px)", opacity: 0.35}}/>
    <AbsoluteFill style={{background: "radial-gradient(ellipse at center, transparent 60%, rgba(0,0,0,0.75) 100%)"}}/>
  </AbsoluteFill>
);

// ---------------- Infomercial: the hype, with the science in the fine print ----------------
export const ConceptInfomercial = () => (
  <AbsoluteFill style={{background: "repeating-conic-gradient(from 0deg at 50% 60%, #1b3fd1 0deg 10deg, #2c5cff 10deg 20deg)"}}>
    <AbsoluteFill style={{background: "radial-gradient(circle at 50% 60%, rgba(255,255,255,0.25), transparent 55%)"}}/>
    <div style={{position: "absolute", left: 60, top: 40, fontFamily: BUNGEE, fontSize: 70, color: "#ffe600", lineHeight: 1.05,
      WebkitTextStroke: "3px #c8102e", textShadow: "6px 6px 0 #0b1a6b"}}>TIRED OF<br/>17-YEAR DRUG HUNTS?</div>
    <div style={{position: "absolute", left: 60, top: 300, padding: "10px 24px", background: "#fff", color: "#0b1a6b", fontFamily: ANTON, fontSize: 54, transform: "rotate(-2deg)"}}>
      INTRODUCING AI-DESIGNED™ KEYS</div>
    <div style={{position: "absolute", left: 980, top: 140, width: 820, height: 560, borderRadius: 30, overflow: "hidden", border: "10px solid #fff", boxShadow: "0 20px 40px rgba(0,0,40,0.5)"}}>
      <Img src={staticFile("style/pose_048.png")} style={{width: "100%", height: "100%", objectFit: "cover"}}/>
      {[[120, 90], [690, 120], [420, 470], [740, 420]].map(([x, y], i) => <svg key={i} style={{position: "absolute", left: x, top: y}} width="60" height="60">
        <path d="M30 0 L36 24 L60 30 L36 36 L30 60 L24 36 L0 30 L24 24 Z" fill="#fff" opacity="0.9"/></svg>)}
    </div>
    <svg style={{position: "absolute", left: 1560, top: 60}} width="300" height="300">
      <polygon points={Array.from({length: 32}, (_, i) => { const a = (i / 32) * Math.PI * 2, r = i % 2 ? 110 : 145; return `${150 + r * Math.cos(a)},${150 + r * Math.sin(a)}`; }).join(" ")} fill="#ffe600" stroke="#c8102e" strokeWidth="6"/>
      <text x="150" y="140" textAnchor="middle" fontFamily={BUNGEE} fontSize="40" fill="#c8102e">ONLY</text>
      <text x="150" y="190" textAnchor="middle" fontFamily={BUNGEE} fontSize="40" fill="#c8102e">30 DAYS*</text>
    </svg>
    <div style={{position: "absolute", left: 60, top: 440, fontFamily: ANTON, fontSize: 46, color: "#fff", lineHeight: 1.35}}>
      ✓ 8,918 designs in the box<br/>✓ fits the CDK20 lock<br/>✓ 15× tighter grip (#048)</div>
    <div style={{position: "absolute", left: 60, top: 760, padding: "16px 40px", background: "#c8102e", color: "#fff", fontFamily: BUNGEE, fontSize: 52, borderRadius: 14,
      boxShadow: "0 8px 0 #7a0016"}}>CALL NOW · 1-800-WORTH-TESTING</div>
    <div style={{position: "absolute", left: 0, right: 0, bottom: 0, height: 120, background: "rgba(0,0,30,0.85)", color: "#fff", fontFamily: '"Arial Narrow", Arial, sans-serif',
      fontSize: 22, padding: "16px 40px", lineHeight: 1.4}}>
      *30 days to a first binding hit, not to a medicine. Tested on the enzyme and in liver-cancer cells only. Not tested in animals or patients.
      Speed-up versus other methods was not measured. Study run by the company that built the AI. Source: Ren et al., Chem. Sci. 2023.</div>
    <div style={{position: "absolute", right: 50, top: 28, fontFamily: ANTON, fontSize: 30, color: "#fff", padding: "4px 14px", background: "#c8102e"}}>● LIVE</div>
  </AbsoluteFill>
);
