import {AbsoluteFill, Img, staticFile} from "remotion";

// Three look-dev stills for the restyle: A vaporwave desktop, B synthwave night city, C Y2K web page.
// Same science beats, same 3D renders; only the visual language changes.

const UI = 'Tahoma, "Microsoft Sans Serif", "Segoe UI", sans-serif';
const DISPLAY = '"Arial Black", "Segoe UI Black", Impact, sans-serif';

// ---------- shared pieces ----------
const Sun = ({cx, cy, r, from, to, stripes = 7}) => (
  <svg style={{position: "absolute", left: 0, top: 0}} width="1920" height="1080">
    <defs>
      <linearGradient id={`sun-${cx}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={from}/><stop offset="1" stopColor={to}/></linearGradient>
      <mask id={`cut-${cx}`}>
        <rect x="0" y="0" width="1920" height="1080" fill="white"/>
        {Array.from({length: stripes}, (_, i) => <rect key={i} x="0" y={cy + r * 0.15 + i * (r * 0.13)} width="1920" height={4 + i * 2.2} fill="black"/>)}
      </mask>
    </defs>
    <circle cx={cx} cy={cy} r={r} fill={`url(#sun-${cx})`} mask={`url(#cut-${cx})`}/>
  </svg>
);

const GridFloor = ({color, glow, top = 640}) => (
  <div style={{position: "absolute", left: -600, right: -600, top, height: 900, perspective: 500, overflow: "hidden"}}>
    <div style={{position: "absolute", inset: 0, transform: "rotateX(68deg)", transformOrigin: "50% 0%",
      backgroundImage: `linear-gradient(${color} 2px, transparent 2px), linear-gradient(90deg, ${color} 2px, transparent 2px)`,
      backgroundSize: "80px 80px", filter: glow ? `drop-shadow(0 0 6px ${color})` : "none"}}/>
  </div>
);

const Scanlines = ({opacity = 0.12}) => (
  <AbsoluteFill style={{backgroundImage: "repeating-linear-gradient(0deg, rgba(0,0,0,0.6) 0 1px, transparent 1px 3px)", opacity, pointerEvents: "none"}}/>
);

// ---------- A: vaporwave desktop ----------
const Win = ({x, y, w, h, title, children, active = true}) => (
  <div style={{position: "absolute", left: x, top: y, width: w, height: h, background: "#c0c0c0", fontFamily: UI,
    borderTop: "3px solid #fff", borderLeft: "3px solid #fff", borderRight: "3px solid #404040", borderBottom: "3px solid #404040",
    boxShadow: "8px 10px 0 rgba(40,0,60,0.35)"}}>
    <div style={{height: 34, margin: 3, background: active ? "linear-gradient(90deg,#000080,#1084d0)" : "linear-gradient(90deg,#808080,#b5b5b5)",
      color: "#fff", fontWeight: 700, fontSize: 19, display: "flex", alignItems: "center", padding: "0 10px", justifyContent: "space-between"}}>
      <span>{title}</span>
      <span style={{display: "flex", gap: 4}}>{["_", "□", "×"].map(c => <span key={c} style={{width: 26, height: 24, background: "#c0c0c0", color: "#000",
        fontSize: 16, display: "grid", placeItems: "center", borderTop: "2px solid #fff", borderLeft: "2px solid #fff", borderRight: "2px solid #404040", borderBottom: "2px solid #404040"}}>{c}</span>)}</span>
    </div>
    <div style={{position: "absolute", left: 6, right: 6, top: 44, bottom: 6, overflow: "hidden"}}>{children}</div>
  </div>
);
const Btn = ({children}) => <span style={{display: "inline-block", padding: "6px 22px", background: "#c0c0c0", fontSize: 18, marginRight: 14,
  borderTop: "2px solid #fff", borderLeft: "2px solid #fff", borderRight: "2px solid #404040", borderBottom: "2px solid #404040"}}>{children}</span>;

export const StyleA = () => (
  <AbsoluteFill style={{background: "linear-gradient(180deg,#24104f 0%,#7b2cbf 38%,#ff6ec7 62%,#ffb86c 70%,#2a0f52 70.2%,#140726 100%)"}}>
    <Sun cx={960} cy={560} r={230} from="#ffe66d" to="#ff3e9d"/>
    <GridFloor color="#ff4fd8" top={756}/>
    <div style={{position: "absolute", left: 120, top: 60, fontFamily: UI, fontSize: 30, color: "#ffe9ff", letterSpacing: 10, opacity: 0.9}}>ワース・テスティング</div>
    <Win x={180} y={150} w={860} h={560} title="AlphaFold.exe — CDK20 (predicted)">
      <Img src={staticFile("style/keyhole.png")} style={{width: "100%", height: "100%", objectFit: "cover", filter: "hue-rotate(95deg) saturate(1.5) contrast(1.1)"}}/>
    </Win>
    <Win x={1000} y={330} w={720} h={250} title="Warning">
      <div style={{display: "flex", gap: 24, padding: "22px 20px", alignItems: "center"}}>
        <svg width="64" height="58"><polygon points="32,2 62,56 2,56" fill="#ffd400" stroke="#000" strokeWidth="2"/><text x="32" y="50" textAnchor="middle" fontSize="34" fontWeight="700">!</text></svg>
        <div style={{fontSize: 24, lineHeight: 1.35}}>A low-confidence tail is blocking the pocket (Arg305).</div>
      </div>
      <div style={{paddingLeft: 108}}><Btn>Cut it</Btn><Btn>Ignore</Btn></div>
    </Win>
    <div style={{position: "absolute", left: 0, right: 0, top: 800, textAlign: "center", fontFamily: DISPLAY, fontSize: 132, fontStyle: "italic",
      letterSpacing: 4, background: "linear-gradient(180deg,#e0fbff 0%,#7df9ff 45%,#ff71ce 55%,#ffdbf7 100%)", WebkitBackgroundClip: "text", color: "transparent",
      filter: "drop-shadow(4px 4px 0 #3a0ca3) drop-shadow(-3px 0 0 rgba(0,255,255,0.6))"}}>WORTH TESTING?</div>
    <div style={{position: "absolute", left: 0, right: 0, bottom: 0, height: 46, background: "#c0c0c0", borderTop: "3px solid #fff", display: "flex", alignItems: "center", padding: "0 8px", gap: 12, fontFamily: UI, fontSize: 19}}>
      <span style={{padding: "4px 14px", fontWeight: 700, borderTop: "2px solid #fff", borderLeft: "2px solid #fff", borderRight: "2px solid #404040", borderBottom: "2px solid #404040"}}>Start</span>
      <span style={{padding: "4px 14px", background: "#d8d8d8", borderTop: "2px solid #404040", borderLeft: "2px solid #404040"}}>AlphaFold.exe</span>
      <span style={{marginLeft: "auto", padding: "4px 14px", borderTop: "2px solid #808080", borderLeft: "2px solid #808080"}}>Day 30</span>
    </div>
    <Scanlines opacity={0.1}/>
  </AbsoluteFill>
);

// ---------- B: synthwave night city ----------
const Skyline = () => {
  const towers = [[0, 210, 120], [130, 300, 90], [230, 180, 140], [380, 360, 80], [470, 250, 120], [600, 420, 70], [680, 280, 110], [800, 330, 90],
    [1100, 300, 100], [1210, 400, 70], [1290, 240, 130], [1430, 350, 90], [1530, 220, 120], [1660, 310, 100], [1770, 260, 150]];
  return <svg style={{position: "absolute", left: 0, top: 0}} width="1920" height="1080">
    {towers.map(([x, h, w], i) => <g key={i}><rect x={x} y={700 - h} width={w} height={h} fill="#12052a"/>
      {Array.from({length: Math.floor(h / 26)}, (_, r) => Array.from({length: Math.floor(w / 22)}, (_, c) => ((r * 7 + c * 3 + i) % 5 === 0) ?
        <rect key={`${r}-${c}`} x={x + 8 + c * 22} y={700 - h + 12 + r * 26} width="9" height="12" fill={(r + c) % 3 ? "#ff3f8e" : "#3ff7ff"} opacity="0.8"/> : null))}</g>)}
  </svg>;
};
const neon = (c) => `0 0 6px ${c}, 0 0 18px ${c}, 0 0 42px ${c}`;
export const StyleB = () => (
  <AbsoluteFill style={{background: "linear-gradient(180deg,#05010f 0%,#1d0638 45%,#5b0f4f 64%,#0a0218 64.8%,#05010c 100%)"}}>
    <Sun cx={960} cy={520} r={260} from="#ffd319" to="#ff2975" stripes={8}/>
    <Skyline/>
    <GridFloor color="#ff2975" glow top={700}/>
    <div style={{position: "absolute", left: 560, top: 230, width: 800, height: 450, borderRadius: 12, overflow: "hidden", border: "2px solid #ff2975",
      boxShadow: "0 0 30px #ff2975, inset 0 0 30px rgba(255,41,117,0.5)"}}>
      <Img src={staticFile("style/wall.png")} style={{width: "100%", height: "100%", objectFit: "cover", mixBlendMode: "screen", filter: "hue-rotate(150deg) saturate(1.8) brightness(1.1)"}}/>
    </div>
    <div style={{position: "absolute", left: 0, right: 0, top: 90, textAlign: "center", fontFamily: DISPLAY, fontSize: 96, color: "#fff", fontStyle: "italic", textShadow: neon("#ff2975")}}>8,918 → 54 → 7</div>
    <div style={{position: "absolute", left: 0, right: 0, top: 860, textAlign: "center", fontFamily: DISPLAY, fontSize: 120, fontStyle: "italic",
      background: "linear-gradient(180deg,#ffffff 0%,#b8e8ff 48%,#2a2a6e 50%,#ff9ad5 100%)", WebkitBackgroundClip: "text", color: "transparent",
      filter: "drop-shadow(0 0 12px #3ff7ff)"}}>WORTH TESTING?</div>
    <div style={{position: "absolute", left: 80, top: 80, fontFamily: UI, fontSize: 26, color: "#3ff7ff", textShadow: neon("#3ff7ff"), letterSpacing: 6}}>HONG KONG · 2023</div>
    <Scanlines opacity={0.08}/>
  </AbsoluteFill>
);

// ---------- C: Y2K web page ----------
const Glossy = ({children, color = "#2f80ff"}) => <span style={{display: "inline-block", padding: "10px 26px", borderRadius: 22, color: "#fff", fontWeight: 700, fontSize: 20,
  background: `linear-gradient(180deg, rgba(255,255,255,0.7) 0%, ${color} 45%, ${color} 100%)`, boxShadow: `0 3px 0 rgba(0,0,0,0.2), inset 0 -3px 6px rgba(0,0,0,0.2)`}}>{children}</span>;
export const StyleC = () => (
  <AbsoluteFill style={{background: "radial-gradient(circle at 20% 15%, #ffffff 0%, #bfe9ff 30%, #6ec6ff 70%, #2b8de0 100%)", fontFamily: '"Trebuchet MS", Verdana, sans-serif'}}>
    {[[160, 900, 70], [1720, 180, 90], [1820, 860, 50], [90, 260, 40], [1580, 980, 60]].map(([x, y, r], i) =>
      <div key={i} style={{position: "absolute", left: x - r, top: y - r, width: 2 * r, height: 2 * r, borderRadius: "50%",
        background: "radial-gradient(circle at 30% 30%, rgba(255,255,255,0.95), rgba(255,255,255,0.15) 45%, rgba(120,200,255,0.25) 70%)", border: "1px solid rgba(255,255,255,0.7)"}}/>)}
    <div style={{position: "absolute", left: 140, top: 70, width: 1640, height: 930, borderRadius: 16, background: "#f3f6fb", boxShadow: "0 20px 60px rgba(0,40,90,0.35)", overflow: "hidden", border: "1px solid #9fb6d1"}}>
      <div style={{height: 56, background: "linear-gradient(180deg,#e9eef6,#c9d4e4)", display: "flex", alignItems: "flex-end", gap: 6, padding: "0 16px"}}>
        {["AlphaFold DB", "KeyFinder 2000", "Lab results"].map((t, i) => <div key={t} style={{padding: "10px 22px", borderRadius: "10px 10px 0 0", fontSize: 18,
          background: i === 1 ? "#f3f6fb" : "#d7e0ec", color: "#1c2b44", fontWeight: i === 1 ? 700 : 400}}>{t}</div>)}
      </div>
      <div style={{height: 50, display: "flex", alignItems: "center", gap: 14, padding: "0 20px", borderBottom: "1px solid #c9d4e4"}}>
        <span style={{fontSize: 22, color: "#5a6b85"}}>◀ ▶ ⟳</span>
        <div style={{flex: 1, height: 32, borderRadius: 16, background: "#fff", border: "1px solid #b7c6da", display: "flex", alignItems: "center", padding: "0 16px", fontSize: 18, color: "#2a3b55"}}>http://www.keyfinder2000.com/cdk20/round2</div>
      </div>
      <div style={{background: "#0b1f4d", color: "#ffe94d", fontWeight: 700, fontSize: 22, padding: "8px 20px", whiteSpace: "nowrap", overflow: "hidden"}}>
        *** BREAKING: "AI designs liver cancer drug in 30 days"?! *** Click to check which step it really reached ***</div>
      <div style={{display: "flex", gap: 30, padding: 30}}>
        <div style={{width: 760, height: 560, borderRadius: 14, overflow: "hidden", background: "#000", position: "relative", border: "4px solid #fff", boxShadow: "0 6px 20px rgba(0,0,0,0.25)"}}>
          <Img src={staticFile("style/pose_048.png")} style={{width: "100%", height: "100%", objectFit: "cover"}}/>
          <div style={{position: "absolute", right: -10, top: 24, transform: "rotate(10deg)", background: "#ff3d7f", color: "#fff", fontWeight: 800, fontSize: 30, padding: "10px 26px", borderRadius: 40, boxShadow: "0 4px 0 #b3004a"}}>NEW! 15× tighter</div>
        </div>
        <div style={{flex: 1, color: "#1c2b44"}}>
          <div style={{fontSize: 54, fontWeight: 800, color: "#0b3d91"}}>Molecule 048</div>
          <div style={{fontSize: 24, marginTop: 6, color: "#3c5174"}}>Round 2 design · grabs Lys33 · blocks the enzyme</div>
          <div style={{marginTop: 34, fontSize: 22}}>Screening 8,918 designs…</div>
          <div style={{marginTop: 10, height: 34, borderRadius: 17, background: "#dfe7f2", overflow: "hidden", border: "1px solid #aebfd6"}}>
            <div style={{width: "92%", height: "100%", background: "repeating-linear-gradient(45deg,#3fd16b 0 18px,#2fb556 18px 36px)"}}/>
          </div>
          <div style={{display: "flex", gap: 16, marginTop: 40}}><Glossy>Add to lab</Glossy><Glossy color="#ff8a00">Test in cells</Glossy></div>
          <div style={{marginTop: 44, padding: 18, borderRadius: 12, background: "#fff7cc", border: "2px dashed #e0b400", fontSize: 22}}>
            Evidence level: <b>step 4 of 6</b> — works in liver cancer cells. Not tested in animals or patients yet.</div>
        </div>
      </div>
    </div>
    <svg style={{position: "absolute", left: 1210, top: 690}} width="40" height="56"><path d="M2 2 L2 46 L13 35 L21 53 L28 50 L20 32 L36 32 Z" fill="#fff" stroke="#000" strokeWidth="2.5"/></svg>
  </AbsoluteFill>
);
