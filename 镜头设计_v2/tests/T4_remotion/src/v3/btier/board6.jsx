// HKBU SCIE1007 课程作业的科普视频：第 6 章共用的实体翻牌记分板（6-01、6-02、6-03、6-06、6-07、6-08 都用这一块）。
// 骨白外壳（Slab 五要素）+ 炭黑翻牌槽（真翻牌：上半片绕中轴往下翻、下半片翻开，翻 3 次乱码再停在字上）+ NOW 栏克莱因蓝框。
// 11-22 改白板（18 文档 1.9 G8，整屏黑板平均亮度只有 0.28–0.35）：板体骨白、圆角 28、厚 18，外沿一圈克莱因蓝料框；
// BEFORE 栏（栏头和牌）底 #1F1E1C 字 #F7F4EE；NOW 栏头和 NOW 栏的牌底 #002FA7 字 #F7F4EE；没翻的空牌 #9A968C 不透明 0.35；
// 行号牌、行名牌骨白深字；凹位 shade(bone, 0.08) 加内阴影；压暗非焦点行的 Dim 改成骨白 0.72 加模糊 3 px。
// B2（18 的 3.3）：翻牌中缝只在牌的左右两端各画 14 px 短线，字的范围内不画（以前整条横贯，压在字上像被划掉）。
// 顶栏 HOW MUCH DID COMPUTERS HELP? 逐字翻牌；4 行 × 3 列：行名 | BEFORE（左凹位 + 主翻牌 + 副翻牌）| NOW（右凹位 + 主翻牌 + 副翻牌）。
// 板面坐标 = 镜头 1 倍时的画面坐标；页面用 cam={x, y, z}（看的中心、倍数）推拉，凹位里的零件由页面在板面坐标里画（children）。
// 规则 v2：翻牌字 Instrument Serif，主行 36 px、副行 28 px（次级 ≥ 26）；翻牌是几何连续变形（≥ 18 帧），算主动作。
import React from "react";
import {C, SERIF, Slab, Sprite, shade, frost} from "./bkit.jsx";

export const BOARD = {x: 120, y: 36, w: 1680, h: 842};
export const TITLE = "HOW MUCH DID COMPUTERS ACTUALLY HELP?";
export const COL = {name: {x: 160, w: 310}, B: {x: 486, w: 620}, N: {x: 1126, w: 640}};
export const ROW_Y = (i) => 216 + i * 162;
export const ROW_H = 152;
export const ROWS = [
  {n: "1.", name: ["SEEING", "THE LOCK"], B: "HARD LAB EXPERIMENTS", Bs: ["EXPENSIVE", "SLOW", "DIFFICULT"], N: "FREE PREDICTION", Ns: ["PUBLIC DATABASE"]},
  {n: "2.", name: ["FINDING", "A HIT"], B: "MILLIONS SCREENED", Bs: ["COSTLY BOTTLENECK"], N: "8,918 DESIGNS", Ns: ["13 MOLECULES MADE"]},
  {n: "3.", name: ["TIME", ""], B: "10–17 YEARS", Bs: ["HIT = OPENING STRETCH"], N: "30 DAYS (1ST HIT)", Ns: ["+30 DAYS (BETTER KEY)"]},
  {n: "4.", name: ["IMPROVING", "THE KEY"], B: "ANOTHER COSTLY LAB ROUND", Bs: [], N: "16 GUIDED DESIGNS", Ns: ["~15× TIGHTER GRIP"]},
];
// 一格的几何：凹位（放零件）、主翻牌、副翻牌
export const cell = (i, side) => {
  const c = COL[side], y = ROW_Y(i);
  const subs = ROWS[i][side + "s"];
  const sx = c.x + 200, sw = c.w - 212;
  const n = Math.max(1, subs.length), g = 8, ew = (sw - g * (n - 1)) / n;
  return {x: c.x, y, w: c.w, h: ROW_H, slot: {x: c.x + 10, y: y + 10, w: 178, h: 132, cx: c.x + 99, cy: y + 76},
          main: {x: sx, y: y + 14, w: sw, h: 62}, sub: subs.map((_, k) => ({x: sx + k * (ew + g), y: y + 88, w: ew, h: 50}))};
};
// 镜头：先看 BEFORE（行名 + 左栏），说到 Now 再横移到右栏
export const FOCUS = (i, side, z = 1.6) => ({x: side === "N" ? 1440 : 640, y: ROW_Y(i) + 76 + 185, z});   // 行在画面上部，顶栏整条出画（Gemini：半截字）
// 弹出台：这一行的零件从凹位里升起、飞到行下面的空处放大演（那几行还空着，盖一层暗纱当舞台），这一栏演完再缩回凹位
export const POP = (i, side) => ({x: side === "N" ? 1440 : 700, y: ROW_Y(i) + 76 + 290});
// G8：骨白 0.72 加模糊 3 px（以前是 0.95 的炭黑纱）
const DIM_BG = "rgba(244,241,234,0.72)";
export const Dim = ({i, v}) => (v < 0.01 ? null :
  <div style={{position: "absolute", left: BOARD.x + 16, top: ROW_Y(i) + ROW_H + 4, width: BOARD.w - 32, height: BOARD.y + BOARD.h - 14 - ROW_Y(i) - ROW_H - 4,
               borderRadius: 12, background: DIM_BG, backdropFilter: "blur(3px)", WebkitBackdropFilter: "blur(3px)", opacity: Math.min(1, v)}} />
);

// 第 4 行在板底，弹出台改在它上面：前三行盖暗纱
export const DimUp = ({i, v}) => (v < 0.01 ? null :
  <div style={{position: "absolute", left: BOARD.x + 16, top: BOARD.y + 120, width: BOARD.w - 32, height: ROW_Y(i) - BOARD.y - 124,
               borderRadius: 12, background: DIM_BG, backdropFilter: "blur(3px)", WebkitBackdropFilter: "blur(3px)", opacity: Math.min(1, v)}} />
);
// 小孔板（6-03 起第 2 行 BEFORE 凹位里的件）：骨白板 + 8 × 12 个带色的孔
const DOTC = [C.blueHi, C.gold, C.green, C.blue, C.grey];
const hr = (k) => { const x = Math.sin(k * 12.9898) * 43758.5453; return x - Math.floor(x); };
export const MiniPlate = ({x, y, s = 1, op = 1, seed = 0}) => (
  <div style={{position: "absolute", left: 0, top: 0, opacity: op}}>
    <Slab x={x - 100 * s} y={y - 67 * s} w={200 * s} h={134 * s} r={10 * s} color={C.bone} depth={7 * s} id={`mp${seed}_${Math.round(x)}`} shadow={false}>
      {[...Array(96)].map((_, k) => (
        <div key={k} style={{position: "absolute", left: (16 + (k % 12) * 15.2 - 5.5) * s, top: (14 + Math.floor(k / 12) * 15.2 - 5.5) * s, width: 11 * s, height: 11 * s, borderRadius: 6 * s,
                             background: DOTC[Math.floor(hr(k + seed * 97 + 1) * 5)], opacity: 0.55 + 0.45 * hr(k * 3 + seed + 2)}} />
      ))}
    </Slab>
  </div>
);

const ALPH = "ABCDEFGHIKLMNOPRSTUVWXYZ0123456789";
const scr = (t, k, seed) => t.split("").map((ch, j) => (ch === " " ? " " : ALPH[Math.floor(Math.abs(Math.sin((j + 1) * 12.9898 + (k + 1) * 78.233 + seed * 37.7) * 43758.5453)) % ALPH.length])).join("");
// 字宽按 0.62 em 一个字估；两端各留 14 px 中缝短线 + 4 px（B2：中缝不进字的范围）
const SEAM = 14;
const fitFs = (t, w, base, m = 2 * SEAM + 8) => Math.max(26, Math.min(base, (w - m) / Math.max(1, t.length * 0.62)));

// 半片：只露上半或下半的字
const Half = ({text, w, h, fs, color, top, style}) => (
  <div style={{position: "absolute", left: 0, top: top ? 0 : h / 2, width: w, height: h / 2, overflow: "hidden", ...style}}>
    <div style={{position: "absolute", left: 0, top: top ? 0 : -h / 2, width: w, height: h, display: "flex", alignItems: "center", justifyContent: "center",
                 fontFamily: SERIF, fontSize: fs, letterSpacing: 1.2, color, whiteSpace: "nowrap", lineHeight: 1}}>{text}</div>
  </div>
);

// 一块翻牌：at = 停在 text 上的那一帧（落位帧）；之前 flips 次乱码，每次 dur 帧。prev = 翻之前的字（空白牌为 ""）
// blank：给了颜色时，还没翻（或不翻）的空牌用这个颜色、整块不透明 0.35（G8）；不给保持老样子（6-06 的日历格直接用 Flap）
export const Flap = ({f, x, y, w, h, text, at, flips = 3, dur = 6, fs = 36, color = C.ink, bg = C.bone, seed = 0, prev = "", hot = 0, jig = 0, blank = null}) => {
  const t0 = at == null ? Infinity : at - flips * dur;
  const T = text || "";
  const size = fitFs(T || prev || "X", w, fs, blank != null ? 2 * SEAM + 8 : 12);   // 直接用 Flap 的老格子（6-06 日历）字号照旧
  let from = prev, to = prev, p = 1;
  if (f >= t0) {
    if (f >= at) { from = T; to = T; }
    else {
      const k = Math.floor((f - t0) / dur);
      p = ((f - t0) % dur) / dur;
      // 整行字的翻牌中间翻出空白面（Gemini：乱码像没删干净的占位字）；顶栏单个字母照旧乱翻
      const mid = (j) => (T.length > 2 ? "" : scr(T, j, seed));
      from = k === 0 ? prev : mid(k - 1);
      to = k === flips - 1 ? T : mid(k);
    }
  }
  const moving = f >= t0 && f < at;
  const r = Math.min(8, h * 0.12);
  const empty = blank != null && !prev && (at == null || f < t0);
  const face = hot > 0 ? C.blue : empty ? blank : bg;
  const ink = hot > 0 ? C.inkLight : color;
  // 中缝短线长：两端各 14 px，窄牌（顶栏单字母）按字宽收短，不进字的范围
  const tw = 0.62 * size * Math.max(1, (to || from || T || prev || "X").length);
  const seam = Math.max(3, Math.min(SEAM, (w - tw) / 2 - 3));
  const dark = face === C.ink || face === C.black || face === C.blue;
  const settle = f >= at && f < at + 10 ? Math.sin(((f - at) / 10) * Math.PI * 2) * (1 - (f - at) / 10) * 2.2 : 0;
  return (
    <div style={{position: "absolute", left: x, top: y + settle + jig, width: w, height: h, borderRadius: r, background: face, opacity: empty ? 0.35 : 1,
                 boxShadow: "0 3px 0 rgba(0,0,0,0.30), inset 0 1.5px 0 rgba(255,255,255,0.6), inset 0 -4px 6px rgba(0,0,0,0.12)"}}>
      <Half text={moving ? to : to} w={w} h={h} fs={size} color={ink} top />
      <Half text={moving ? from : to} w={w} h={h} fs={size} color={ink} top={false} />
      {moving && p < 0.5 && (
        <div style={{position: "absolute", left: 0, top: 0, width: w, height: h / 2, transformOrigin: `50% ${h / 2}px`, transform: `scaleY(${(1 - 2 * p).toFixed(3)})`,
                     background: face, borderRadius: `${r}px ${r}px 0 0`, filter: `brightness(${(1 - 0.5 * p).toFixed(3)})`}}>
          <Half text={from} w={w} h={h} fs={size} color={ink} top />
        </div>
      )}
      {moving && p >= 0.5 && (
        <div style={{position: "absolute", left: 0, top: h / 2, width: w, height: h / 2, transformOrigin: "50% 0", transform: `scaleY(${(2 * p - 1).toFixed(3)})`,
                     background: face, borderRadius: `0 0 ${r}px ${r}px`, filter: `brightness(${(0.75 + 0.5 * (p - 0.5)).toFixed(3)})`, overflow: "hidden"}}>
          <div style={{position: "absolute", left: 0, top: -h / 2, width: w, height: h}}><Half text={to} w={w} h={h} fs={size} color={ink} top={false} style={{top: h / 2}} /></div>
        </div>
      )}
      {/* 中轴：两端各一小段暗缝 + 下沿亮线（B2：字的范围内不画） */}
      {[0, w - seam].map((sx, k) => (
        <React.Fragment key={k}>
          <div style={{position: "absolute", left: sx, top: h / 2 - 1, width: seam, height: 2, background: dark ? "rgba(0,0,0,0.55)" : "rgba(0,0,0,0.30)"}} />
          <div style={{position: "absolute", left: sx, top: h / 2 + 1, width: seam, height: 1, background: dark ? "rgba(255,255,255,0.14)" : "rgba(255,255,255,0.7)"}} />
        </React.Fragment>
      ))}
    </div>
  );
};

// 凹位：板面上压下去的一个方槽（G8：shade(bone, 0.08) 加内阴影），亮起时槽沿一圈蓝高光
const Recess = ({x, y, w, h, lit = 0}) => (
  <div style={{position: "absolute", left: x, top: y, width: w, height: h, borderRadius: 14, background: shade(C.bone, 0.08),
               boxShadow: `inset 0 6px 10px rgba(0,0,0,0.22), inset 0 -1.5px 0 rgba(255,255,255,0.8)${lit > 0.01 ? `, 0 0 0 ${(3 * lit).toFixed(1)}px rgba(61,107,230,${(0.9 * lit).toFixed(2)})` : ""}`}} />
);

// 填好的行：凹位里留着这一行演过的零件（小号，静止）
const DECO = [
  {B: {name: "socket/hero_34", w: 118, style: frost(0.4)}, N: {name: "af/front305", w: 104}},
  {B: {plate: true}, N: {name: "plug/001_34", w: 120}},
  {B: {tape: true}, N: {name: "plug/048_34", w: 120}},
  {B: {name: "loop/34", w: 140}, N: {name: "mini/m34_001", w: 118}},
];
// 卷尺盒（自绘塑料件：骨白壳 + 克莱因蓝转盘 + 金色尺头），x、y 是盒心
export const TapeCase = ({x, y, s = 1, op = 1, spin = 0}) => (
  <div style={{position: "absolute", left: 0, top: 0, opacity: op}}>
    <Slab x={x - 75 * s} y={y - 75 * s} w={150 * s} h={150 * s} r={34 * s} color={C.bone} depth={10 * s} id={`tcase${Math.round(x)}`} />
    <Slab x={x - 44 * s} y={y - 46 * s} w={88 * s} h={88 * s} r={44 * s} color={C.blue} depth={5 * s} shadow={false} id={`thub${Math.round(x)}`}>
      <div style={{position: "absolute", left: 44 * s - 4, top: 8 * s, width: 8, height: 30 * s, borderRadius: 4, background: C.blueHi, transformOrigin: `4px ${36 * s}px`, transform: `rotate(${spin}deg)`}} />
    </Slab>
  </div>
);
export const SlotDeco = ({i, side, op = 1}) => {
  const d = DECO[i][side], g = cell(i, side).slot;
  if (d.tape) return <TapeCase x={g.cx} y={g.cy} s={0.72} op={op} />;
  if (d.plate) return <MiniPlate x={g.cx} y={g.cy} s={0.78} op={op} seed={1} />;
  return <Sprite name={d.name} x={g.cx} y={g.cy} w={d.w} op={op} shadow={false} style={d.style} />;
};

// 卷帘：骨白偏灰的底上一条条横肋（收起时从左往右卷走）。11-22 白板后不用炭黑，免得四行卷帘一盖就是一大片黑（黑 ≤ 35%）
const Shutter = ({x, y, w, h}) => (w < 1 ? null :
  <div style={{position: "absolute", left: x, top: y, width: w, height: h, borderRadius: 10, overflow: "hidden", background: shade(C.bone, 0.16),
               boxShadow: "0 4px 8px rgba(0,0,0,0.22)"}}>
    {[...Array(Math.floor(h / 14))].map((_, k) => (
      <div key={k} style={{position: "absolute", left: 0, top: k * 14 + 2, width: w, height: 10, borderRadius: 3,
                           background: "linear-gradient(180deg, rgba(255,255,255,0.55), rgba(255,255,255,0.10) 60%, rgba(0,0,0,0.10))"}} />
    ))}
    <div style={{position: "absolute", left: 0, top: 0, width: 14, height: h, background: "rgba(255,255,255,0.45)"}} />
  </div>
);

// 整块板。rows[i]：true = 这一行已经填好（静止）；对象 = 这一行正在填（各翻牌的落位帧 {name, B, Bs:[…], N, Ns:[…]}，没给的保持空白）；false = 空白
// G8 各栏牌面：BEFORE 炭黑浅字，NOW 克莱因蓝浅字，行号和行名骨白深字；没翻的空牌一律灰 0.35
const FACE = {B: {bg: C.ink, color: C.inkLight, blank: C.grey}, N: {bg: C.blue, color: C.inkLight, blank: C.grey}, name: {bg: C.bone, color: C.ink, blank: C.grey}};
export const Board6 = ({f, cam = {x: 960, y: 457, z: 1}, rise = 1, title = -999, titleLand = null, titleFrom = null, help = -999, hdr = {B: -999, N: -999}, cols = 1, rows = [false, false, false, false],
                        lit = {}, jig = null, nowFrame = 1, hideB = 0, subFsN = 28, children, over}) => {
  const tx = 960 - cam.x * cam.z, ty = 540 - cam.y * cam.z;
  const ry = 60 * (1 - rise);
  const jg = (seed) => (jig != null && f >= jig && f < jig + 14 ? Math.sin(((f - jig - seed) / 14) * Math.PI * 3) * 3 * (1 - (f - jig) / 14) : 0);
  const tw = 41, tg = 2, tx0 = 960 - (TITLE.length * (tw + tg) - tg) / 2;
  return (
    <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: "0 0", transform: `translate(${tx.toFixed(2)}px, ${ty.toFixed(2)}px) scale(${cam.z.toFixed(4)})`}}>
      <div style={{position: "absolute", left: 0, top: ry, width: 1920, height: 1080, opacity: Math.min(1, rise * 1.6)}}>
        {/* G8：外沿一圈克莱因蓝料框（宽 14，离板边 12 px，带下暗边和上高光线） */}
        <div style={{position: "absolute", left: BOARD.x - 26, top: BOARD.y - 26 - (rise < 1 ? 20 * (1 - rise) : 0), width: BOARD.w + 52, height: BOARD.h + 18 + 52, borderRadius: 28 + 26,
                     border: `14px solid ${C.blue}`, boxSizing: "border-box", boxShadow: `0 4px 0 ${shade(C.blue, 0.22)}, 0 12px 26px rgba(0,0,0,0.18), inset 0 2px 0 rgba(255,255,255,0.35)`}} />
        <Slab x={BOARD.x} y={BOARD.y} w={BOARD.w} h={BOARD.h} r={28} color={C.bone} depth={18} sheen={rise < 1 ? rise : -1} id="board6" lift={rise < 1 ? 20 * (1 - rise) : 0}>
          {/* 骨白板面（以前嵌一块炭黑面板），顶栏一道分隔肋 */}
          <div style={{position: "absolute", left: 40, top: 112, width: BOARD.w - 80, height: 3, borderRadius: 2, background: shade(C.bone, 0.14), boxShadow: "0 1px 0 rgba(255,255,255,0.8)"}} />
          {/* NOW 栏的克莱因蓝框（凸起的一圈） */}
          <div style={{position: "absolute", left: COL.N.x - BOARD.x - 8, top: 122, width: COL.N.w + 16, height: BOARD.h - 136, borderRadius: 18,
                       boxShadow: `0 0 0 6px ${C.blue}, 0 3px 0 6px ${shade(C.blue, 0.22)}`, opacity: Math.min(1, Math.max(0, nowFrame))}} />
        </Slab>
        {/* 顶栏逐字翻牌 */}
        {TITLE.split("").map((ch, i) => (
          <Flap key={i} f={f} x={tx0 + i * (tw + tg)} y={BOARD.y + 22} w={tw} h={80} text={ch} fs={52} seed={i} blank={C.grey}
                at={ch === " " ? null : ch === "?" ? help : titleLand ? titleLand[i] : title - (TITLE.length - 1 - i)}
                flips={titleFrom != null && titleLand && ch !== " " ? Math.max(3, Math.floor(((ch === "?" ? help : titleLand[i]) - titleFrom - i * 0.7) / 6)) : 3} color={C.inkLight} bg={ch === "?" && f >= help ? C.red : C.ink} jig={jg(i)} />
        ))}
        {/* 栏头 */}
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: 1 - hideB}}>
          <Flap f={f} x={COL.B.x + COL.B.w / 2 - 150} y={158} w={300} h={50} text="BEFORE" at={hdr.B} fs={36} seed={50} jig={jg(3)} {...FACE.B} />
        </div>
        <Flap f={f} x={COL.N.x + COL.N.w / 2 - 150} y={158} w={300} h={50} text="NOW" at={hdr.N} fs={36} seed={51} jig={jg(5)} {...FACE.N} />
        {/* 4 行 */}
        {ROWS.map((R, i) => {
          const st = rows[i];
          const full = st === true, live = st && st !== true ? st : {};
          const y = ROW_Y(i);
          const open = Math.max(0, Math.min(1, cols * 1.6 - i * 0.2));
          const at = (k) => (full ? -999 : live[k]);
          const atS = (k, j) => (full ? -999 : (live[k] || [])[j]);
          const B = cell(i, "B"), N = cell(i, "N");
          return (
            <div key={i} style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080}}>
              {/* 行名：号码牌 + 两行翻牌（hideB：镜头移到 NOW 栏后淡出，免得左半截字被屏左缘切） */}
              <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: 1 - hideB}}>
              <Flap f={f} x={COL.name.x} y={y + 10} w={70} h={132} text={R.n} at={at("name")} fs={56} seed={i * 10 + 1} jig={jg(i)} {...FACE.name} />
              <Flap f={f} x={COL.name.x + 80} y={y + 10} w={COL.name.w - 80} h={62} text={R.name[0]} at={at("name")} fs={34} seed={i * 10 + 2} jig={jg(i + 1)} {...FACE.name} />
              <Flap f={f} x={COL.name.x + 80} y={y + 80} w={COL.name.w - 80} h={62} text={R.name[1]} at={R.name[1] ? at("name") : null} fs={34} seed={i * 10 + 3} jig={jg(i + 2)} {...FACE.name} />
              </div>
              {[["B", B], ["N", N]].map(([sd, g]) => (
                <div key={sd} style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: sd === "B" ? 1 - hideB : 1}}>
                  <Recess {...g.slot} lit={(lit[`${i}${sd}`] || 0)} />
                  <Flap f={f} {...g.main} text={R[sd]} at={at(sd)} fs={36} seed={i * 10 + (sd === "B" ? 4 : 6)} jig={jg(i + 3)} {...FACE[sd]} />
                  {g.sub.map((b, j) => (R[sd + "s"][j] ? <Flap key={j} f={f} {...b} text={R[sd + "s"][j]} at={atS(sd + "s", j)} fs={sd === "N" ? subFsN : 28} seed={i * 10 + 7 + j} jig={jg(i + 4 + j)} {...FACE[sd]} /> : null))}
                  {!g.sub.length && <Flap f={f} x={g.main.x} y={g.y + 88} w={g.main.w} h={50} text="" at={null} {...FACE[sd]} />}
                </div>
              ))}
              {full && <div style={{opacity: 1 - hideB}}><SlotDeco i={i} side="B" /></div>}
              {full && <SlotDeco i={i} side="N" />}
              {open < 0.999 && <Shutter x={COL.name.x - 6 + (COL.N.x + COL.N.w - COL.name.x + 12) * open} y={y + 4} w={(COL.N.x + COL.N.w - COL.name.x + 12) * (1 - open)} h={ROW_H - 8} />}
            </div>
          );
        })}
        {children}
      </div>
      {over}
    </div>
  );
};
