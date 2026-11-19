// HKBU SCIE1007 课程作业的科普视频：二维说明书页样片 2-05（两个目标，C 画外音）。
// 样子：拼装模型说明书的一页——暖纸色、步骤号方框、零件线稿加平涂色、圈号、手画箭头。
// 零件图取自零件库正上方渲染（G:/cdk20/work/kit/flat/），线稿由透明通道和明暗边描出（prep 在 工作记录 里）。
// 所有时间由 words_2-05.json（映射/master_v1.json 导出）的词帧算出，不写死。
//   node node_modules/@remotion/cli/remotion-cli.js render src/v3/manual/Manual205.jsx Manual205 OUT.mp4 --public-dir=G:/cdk20/work/manual205/public
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, Img, registerRoot, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";
import T from "./words_2-05.json";
import {Lens, guidePlan, useGuideLook, nudge} from "./kit.jsx";

const PAPER = "#EDE9DF", INK = "#1F1E1C", SOFT = "#6E6B63", RED = "#C8102E";
const W = Object.fromEntries(T.words.map((w, i) => [i + 1, w]));      // W[3].f0 = identify
const ease = Easing.bezier(0.33, 0, 0.2, 1);
const out = Easing.out(Easing.cubic);
const span = (f, a, b, fn = (x) => x) => (f <= a ? 0 : f >= b ? 1 : fn((f - a) / Math.max(1, b - a)));

const fh = typeof window !== "undefined" ? delayRender("fonts") : null;
if (typeof window !== "undefined") {
  Promise.all([["Serif", "InstrumentSerif-Regular.ttf", "normal"], ["Serif", "InstrumentSerif-Italic.ttf", "italic"], ["Hand", "Caveat.ttf", "normal"]]
    .map(([n, file, st]) => new FontFace(n, `url(${staticFile("fonts/" + file)})`, {style: st}).load().then((x) => document.fonts.add(x))))
    .then(() => continueRender(fh)).catch(() => continueRender(fh));
}

// 零件：线稿先画出（左→右），平涂色从浇口点漫开，前沿一圈亮料，长满轻微过冲
const Part = ({name, gid, cx, cy, w, ar, at, gate = [0.5, 1], f, wipe = 12, flood = 24, children}) => {
  const h = w / ar;
  const L = useGuideLook(gid ?? name, at);            // 视线引导（11-20）：没被点名略虚，被点名带轮廓光
  const ndg = L && L.nudge ? nudge(f, L.nudge.land, {dir: [gate[0] - 0.5, gate[1] - 0.5], R: Math.hypot(w, h) / 2}) + " " : "";
  const pl = span(f, at - 2, at - 2 + wipe, out);
  const pc = span(f, at + 3, at + 3 + flood, Easing.inOut(Easing.quad));
  const r = pc * 150;
  const bump = f > at + 3 + flood ? 0.028 * Math.exp(-(f - at - 3 - flood) / 5) * Math.cos((f - at - 3 - flood) / 3.2) : 0;
  const lx = -6 + 112 * pl;
  const g = `${gate[0] * 100}% ${gate[1] * 100}%`;
  const mLine = `linear-gradient(90deg,#000 ${lx - 5}%,transparent ${lx}%)`;
  const mCol = `radial-gradient(circle at ${g},#000 ${r - 6}%,transparent ${r}%)`;
  const mRing = `radial-gradient(circle at ${g},transparent ${r - 16}%,#000 ${r - 5}%,transparent ${r}%)`;
  const box = {position: "absolute", left: 0, top: 0, width: w, height: h};
  return (
    <div style={{position: "absolute", left: cx - w / 2, top: cy - h / 2, width: w, height: h, transform: `${ndg}scale(${1 + bump})`, ...(L ? L.style : null)}}>
      <Img src={staticFile(`parts/${name}_c.png`)} style={{...box, WebkitMaskImage: mCol, maskImage: mCol}} />
      {pc > 0 && pc < 1 && <Img src={staticFile(`parts/${name}_c.png`)} style={{...box, WebkitMaskImage: mRing, maskImage: mRing, filter: "brightness(1.7) saturate(0.55)"}} />}
      <Img src={staticFile(`parts/${name}_l.png`)} style={{...box, opacity: 1 - 0.55 * pc, WebkitMaskImage: mLine, maskImage: mLine}} />
      {children}
    </div>
  );
};

// 圈号：盖章一样落下
const Tag = ({n, x, y, at, f}) => {
  const p = span(f, at, at + 6, out);
  return p <= 0 ? null : (
    <div style={{position: "absolute", left: x - 23, top: y - 23, width: 46, height: 46, borderRadius: 23, border: `2.5px solid ${INK}`, boxSizing: "border-box",
                 font: "28px/41px Serif", textAlign: "center", color: INK, opacity: p, transform: `scale(${1.25 - 0.25 * p})`, background: PAPER}}>{n}</div>
  );
};

// 手画箭头：路径描出来，箭头尖在最后长出
const Arrow = ({d, tip, ang, a, b, f, color = INK, sw = 4, dash}) => {
  const p = span(f, a, b, ease);
  if (p <= 0) return null;
  const k = span(p, 0.8, 1);
  return (
    <g fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round">
      <path d={d} pathLength={1} strokeDasharray={dash ? undefined : "1 1"} strokeDashoffset={dash ? undefined : 1 - p}
            style={dash ? {strokeDasharray: dash, clipPath: `inset(0 ${100 - p * 100}% 0 0)`} : undefined} />
      <g transform={`translate(${tip[0]},${tip[1]}) rotate(${ang}) scale(${k})`}><path d="M-20,-11 L0,0 L-20,11" /></g>
    </g>
  );
};

const Write = ({p, children, style}) => {
  const x = -8 + 116 * p;
  const m = `linear-gradient(90deg,#000 ${x - 6}%,transparent ${x}%)`;
  return <span style={{...style, WebkitMaskImage: m, maskImage: m, display: "inline-block", whiteSpace: "pre"}}>{children}</span>;
};

// 步骤框：边框一笔画出，步骤号落章
const Step = ({n, x, y, w, h, at, f, children}) => {
  const p = span(f, at - 4, at + 30, ease);
  const s = span(f, at, at + 6, out);
  const per = 2 * (w + h);
  return (
    <div style={{position: "absolute", left: x, top: y, width: w, height: h}}>
      <svg width={w} height={h} style={{position: "absolute", overflow: "visible"}}>
        <rect x={0} y={0} width={w} height={h} rx={10} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray={per} strokeDashoffset={per * (1 - p)} opacity={0.85} />
      </svg>
      <div style={{position: "absolute", left: -2, top: -2, width: 92, height: 92, background: INK, color: PAPER, borderRadius: "10px 0 10px 0",
                   font: "78px/90px Serif", textAlign: "center", opacity: s, transform: `scale(${1.2 - 0.2 * s})`, transformOrigin: "0 0"}}>{n}</div>
      {children}
    </div>
  );
};

// 零件说明栏（导演 11-18：图要有文字配合）：说明书的零件表，圈号对上框里的圈号，跟着零件出现
const Legend = ({x, y, w, at, rows, f}) => {
  const p = span(f, at - 4, at + 26, ease);
  return (
    <div style={{position: "absolute", left: x, top: y, width: w}}>
      <svg width={w} height={4} style={{position: "absolute", left: 0, top: 0}}>
        <path d={`M0,2 L${w},2`} stroke={INK} strokeWidth={1.5} opacity={0.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />
      </svg>
      {rows.map((row, r) => (
        <div key={r} style={{position: "absolute", left: 0, top: 22 + r * 62, display: "flex", gap: 38, whiteSpace: "nowrap"}}>
          {row.map(([n, text, a]) => {
            const q = span(f, a, a + 14, out);
            return (
              <div key={n} style={{display: "flex", alignItems: "center", gap: 12, opacity: q, transform: `translateY(${8 * (1 - q)}px)`}}>
                <div style={{width: 40, height: 40, borderRadius: 20, border: `2px solid ${INK}`, boxSizing: "border-box", font: "24px/36px Serif", textAlign: "center"}}>{n}</div>
                <Write p={span(f, a + 2, a + 18)} style={{font: "32px Serif", color: INK}}>{text}</Write>
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
};

// 料珠：红色的一小颗料，沿页面一路走，说到哪到哪；每样东西都在它到的那一帧开始长。位置只由词帧决定。
const beadKeys = () => [
  [0, 150, 60], [W[1].f0, 188, 130], [W[3].f0, 216, 414], [W[5].f0, 311, 302], [W[6].f0, 521, 312], [W[7].f0, 731, 321],
  [W[8].f0, 521, 530], [W[10].f0 - 4, 521, 606], [W[10].f0 + 6, 491, 688], [W[11].f0, 626, 716], [W[12].f0 + 26, 574, 716],
  [W[13].f0, 1080, 130], [W[15].f0, 1598, 417], [W[17].f0, 1084, 226], [W[19].f0 - 2, 1350, 320], [W[19].f0 + 20, 1494, 320],
  [W[20].f0, 1148, 534], [W[21].f0, 1224, 654], [W[21].f0 + 20, 1316, 654], [W[22].f0, 1340, 530], [W[24].f0 + 10, 1716, 530],
  [T.sentences[1].f1 - 2, 1611, 462], [T.len_f, 1611, 458],
];
const beadAt = (f) => {
  const K = beadKeys();
  for (let i = 0; i < K.length - 1; i++) {
    if (f <= K[i + 1][0]) {
      const p = span(f, K[i][0], K[i + 1][0], Easing.inOut(Easing.sin));
      const dx = K[i + 1][1] - K[i][1], dy = K[i + 1][2] - K[i][2];
      const arc = Math.sin(Math.PI * p) * Math.min(26, Math.hypot(dx, dy) * 0.08);     // 路线带一点弧，不走死直线
      const L = Math.hypot(dx, dy) || 1;
      return [K[i][1] + dx * p + (dy / L) * arc, K[i][2] + dy * p - (dx / L) * arc];
    }
  }
  return [K[K.length - 1][1], K[K.length - 1][2]];
};
const Bead = ({f}) => (
  <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
    {[...Array(14)].map((_, i) => {
      const [x, y] = beadAt(f - (13 - i) * 0.75);
      return <circle key={i} cx={x} cy={y} r={2 + (i / 13) * 6} fill={RED} opacity={i === 13 ? 1 : 0.05 + 0.03 * i} />;
    })}
    {(() => { const [x, y] = beadAt(f); return <circle cx={x - 2.2} cy={y - 2.4} r={2.2} fill="#fff" opacity={0.75} />; })()}
  </svg>
);

const AR = {chip: 1, racks: 935 / 736, sieve: 959 / 654, magnifier: 483 / 735, liver: 1055 / 795, key: 1099 / 315, dial: 617 / 751, person: 438 / 729, keys: 1179 / 758, mol: 566 / 635};

// 视线引导（11-20，替代红色料珠）：这页没有事件表，按"零件长出的那个词"生成同样规则的引导（grow → focus，太近的合并、每句最多 3 次）
const GP = guidePlan({len_f: T.len_f, sentences: T.sentences, events: [
  ["tools1", "chip", 5], ["tools2", "racks", 6], ["tools3", "sieve", 7], ["liver", "liver", 10], ["key", "key", 11],
  ["dial", "dial", 15], ["ref", "ref", 17], ["person", "person", 20],
].map(([id, t, n]) => ({id, obj: t, verb: "grow", f_start: W[n].f0 - 4, f_land: W[n].f0, f_end: W[n].f0 + 60, guide: {kind: "focus", target: t}}))});

const Scene = () => {
  const f = useCurrentFrame();
  const S1 = T.sentences[0], S2 = T.sentences[1];
  // ---- 第 1 步 ----
  const tools = [["chip", 215, 13, W[5].f0], ["racks", 425, 33, W[6].f0], ["sieve", 635, 36, W[7].f0]];
  // 放大镜：identify 落下，随后依次滑过三样工具（焦点先到：每次在词前 4 帧到位），最后停到右上角
  const mk = [[W[3].f0 + 14, 120, 300], [W[5].f0 - 4, 215, 330], [W[6].f0 - 4, 425, 330], [W[7].f0 - 4, 625, 330], [W[8].f0 + 10, 762, 236]];
  let mx = mk[0][1], my = mk[0][2];
  for (let i = 0; i < mk.length - 1; i++) {
    const p = span(f, mk[i][0], mk[i + 1][0], Easing.inOut(Easing.cubic));
    if (f > mk[i][0]) { mx = mk[i][1] + (mk[i + 1][1] - mk[i][1]) * p; my = mk[i][2] + (mk[i + 1][2] - mk[i][2]) * p; }
  }
  const drift = Math.sin(f / 37) * 3;                       // 到位后也不停死
  const meet = span(f, W[12].f0, W[12].f0 + 26, Easing.in(Easing.quad));   // discovery：钥匙被肝吸过去
  const click = f > W[12].f0 + 26 ? Math.exp(-(f - W[12].f0 - 26) / 5) * Math.cos((f - W[12].f0 - 26) / 2.6) : 0;
  // ---- 第 2 步 ----
  const refIn = span(f, W[17].f0, W[18].f0 + 10, out);
  const bars = [0.52, 0.86, 0.34, 0.68, 0.95, 0.45];
  const keysP = span(f, W[22].f0 - 2, W[24].f0 + 16);       // potential → candidates：小钥匙一列列出现
  const pick = span(f, W[24].f0 + 14, S2.f1 - 2, out);

  return (
    <Lens plan={GP} f={f}>
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("2-05.wav")} />
      {/* 纸页：细边和装订角标 */}
      <div style={{position: "absolute", inset: "34px 40px 44px 40px", border: `1.5px solid rgba(31,30,28,0.22)`, borderRadius: 4}} />

      {/* ============ 第 1 步 ============ */}
      <Step n="1" x={96} y={84} w={836} h={716} at={W[1].f0} f={f}>
        <div style={{position: "absolute", left: 122, top: 10, fontSize: 62, lineHeight: "76px"}}>
          <Write p={span(f, W[3].f0, W[3].f1 + 4)}>Identify </Write>
          <Write p={span(f, W[5].f0, W[7].f1)} style={{fontStyle: "italic"}}>the major methods</Write>
        </div>
        {tools.map(([n, x, no, at]) => (
          <React.Fragment key={n}>
            <Part name={n} cx={x} cy={300} w={n === "chip" ? 164 : 184} ar={AR[n]} at={at} f={f} gate={[0.5, 0]} />
            <Tag n={no} x={x} y={420} at={at + 20} f={f} />
          </React.Fragment>
        ))}
        <div style={{position: "absolute", left: 68, top: 150, width: 700, textAlign: "center", font: "34px Hand", color: SOFT, opacity: span(f, W[6].f0 + 6, W[6].f0 + 16)}}>
          computer-aided
        </div>
        {/* 放大镜 */}
        <div style={{position: "absolute", left: mx - 60, top: my - 62 + drift, transform: `rotate(${-18 + (mx - 120) * 0.012}deg)`, transformOrigin: "60px 62px"}}>
          <Part name="magnifier" cx={60} cy={92} w={120} ar={AR.magnifier} at={W[3].f0} f={f} gate={[0.5, 1]} flood={18} />
        </div>
        <svg width={836} height={716} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
          {/* used in：三样工具汇成一支箭头往下 */}
          <Arrow d="M215,446 C215,490 425,468 425,502 M635,446 C635,490 425,468 425,502 M425,446 L425,522" tip={[425, 526]} ang={90} a={W[8].f0} b={W[10].f0 - 2} f={f} />
          {/* discovery：钥匙 → 肝 */}
          <Arrow d="M520,632 L432,632" tip={[426, 632]} ang={180} a={W[12].f0 - 4} b={W[12].f0 + 16} f={f} color={RED} />
        </svg>
        <Part name="liver" cx={270} cy={616} w={250} ar={AR.liver} at={W[10].f0} f={f} gate={[1, 0.45]} />
        <div style={{position: "absolute", left: 0, top: 0, transform: `translate(${-52 * meet + 5 * click}px,0)`}}>
          <Part name="key" cx={648} cy={632} w={236} ar={AR.key} at={W[11].f0} f={f} gate={[0, 0.5]} flood={16} />
        </div>
        <Tag n="04" x={150} y={520} at={W[10].f0 + 18} f={f} />
        <Tag n="22" x={760 - 52 * meet} y={570} at={W[11].f0 + 14} f={f} />
      </Step>

      <div style={{position: "absolute", left: 988, top: 84, width: 836, height: 716, border: "2px dashed rgba(31,30,28,0.16)", borderRadius: 10, boxSizing: "border-box", opacity: 1 - span(f, W[13].f0, W[13].f0 + 30)}} />
      {/* ============ 第 2 步 ============ */}
      <Step n="2" x={988} y={84} w={836} h={716} at={W[13].f0} f={f}>
        <div style={{position: "absolute", left: 122, top: 10, fontSize: 62, lineHeight: "76px"}}>
          <Write p={span(f, W[15].f0, W[15].f1 + 4)}>Evaluate </Write>
          <Write p={span(f, W[16].f0, W[19].f1)} style={{fontStyle: "italic"}}>how they help</Write>
        </div>
        {/* 打分表：evaluate 时长出；assess 时读数（外圈红弧扫过） */}
        <Part name="dial" cx={610} cy={236} w={160} ar={AR.dial} at={W[15].f0} f={f} gate={[0.5, 1]}>
          <svg width={160} height={195} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
            <circle cx={80} cy={80} r={88} fill="none" stroke={RED} strokeWidth={5} strokeLinecap="round" pathLength={1}
                    strokeDasharray="1 1" strokeDashoffset={1 - 0.62 * span(f, W[21].f0, W[21].f0 + 34, ease) - 0.1 * pick} transform="rotate(-215 80 80)" />
          </svg>
        </Part>
        <Tag n="38" x={724} y={176} at={W[15].f0 + 22} f={f} />
        {/* these methods：第 1 步的成果装在虚线框里拿过来 */}
        <div style={{position: "absolute", left: 96 - 40 * (1 - refIn), top: 142, width: 250, height: 190, opacity: span(f, W[17].f0, W[17].f0 + 8)}}>
          <svg width={250} height={190} style={{position: "absolute", overflow: "visible"}}>
            <rect x={0} y={0} width={250} height={190} rx={8} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="10 8" />
          </svg>
          <div style={{position: "absolute", left: -2, top: -2, width: 44, height: 44, background: INK, color: PAPER, font: "36px/42px Serif", textAlign: "center", borderRadius: "8px 0 8px 0"}}>1</div>
          {[["chip", 66, 78, 82], ["racks", 170, 70, 96], ["sieve", 122, 140, 104]].map(([n, x, y, w], i) => (
            <Part key={n} name={n} gid="ref" cx={x} cy={y} w={w} ar={AR[n]} at={W[17].f0 + 4 + i * 9} f={f} gate={[0.5, 0]} wipe={8} flood={14} />
          ))}
        </div>
        <Part name="person" cx={160} cy={560} w={132} ar={AR.person} at={W[20].f0} f={f} gate={[0.5, 0]} />
        <Tag n="03" x={76} y={470} at={W[20].f0 + 22} f={f} />
        <svg width={836} height={716} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
          {/* help：方法 → 打分表 */}
          <Arrow d="M362,236 L500,236" tip={[506, 236]} ang={0} a={W[19].f0 - 2} b={W[19].f0 + 20} f={f} />
          {/* assess：人去看候选 */}
          <Arrow d="M236,570 L322,570" tip={[328, 570]} ang={0} a={W[21].f0} b={W[21].f0 + 20} f={f} />
          {/* 候选的打分柱：自己长高，最高的一根变红 */}
          {bars.map((v, i) => {
            const at = W[22].f0 + 10 + i * ((W[24].f0 + 10 - W[22].f0) / 6);
            const g = span(f, at, S2.f1 - 4 - (5 - i) * 2, out);
            const x = 360 + 360 * [0.055, 0.225, 0.39, 0.56, 0.73, 0.9][i] - 13, best = i === 4;
            return <rect key={i} x={x} y={444 - 64 * v * g} width={26} height={64 * v * g} rx={3} fill={best && pick > 0 ? RED : INK} opacity={best ? 1 : 1 - 0.45 * pick} />;
          })}
          <path d="M352,446 L728,446" stroke={INK} strokeWidth={2.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - span(f, W[22].f0, W[22].f0 + 20, ease)} />
        </svg>
        <div style={{position: "absolute", left: 360, top: 462, width: 360, height: 360 / AR.keys, WebkitMaskImage: `linear-gradient(90deg,#000 ${keysP * 112 - 8}%,transparent ${keysP * 112}%)`,
                     maskImage: `linear-gradient(90deg,#000 ${keysP * 112 - 8}%,transparent ${keysP * 112}%)`}}>
          <Img src={staticFile("parts/keys_c.png")} style={{position: "absolute", width: "100%", height: "100%"}} />
          <Img src={staticFile("parts/keys_l.png")} style={{position: "absolute", width: "100%", height: "100%", opacity: 0.45}} />
        </div>
        <Tag n="37" x={768} y={500} at={W[24].f0 + 4} f={f} />
      </Step>
      <Legend x={96} y={830} w={836} at={W[5].f0} f={f} rows={[
        [["13", "AI structure prediction", W[5].f0 + 20], ["33", "biological databases", W[6].f0 + 20]],
        [["36", "virtual screening", W[7].f0 + 20], ["04", "liver cancer", W[10].f0 + 18], ["22", "drug candidate", W[11].f0 + 14]],
      ]} />
      <Legend x={988} y={830} w={836} at={W[15].f0} f={f} rows={[
        [["38", "score", W[15].f0 + 22], ["03", "scientists", W[20].f0 + 22]],
        [["37", "potential drug candidates", W[24].f0 + 4]],
      ]} />
      {/* 红柱旁的笔记：分数最高 */}
      <div style={{position: "absolute", left: 1700, top: 452, font: "30px Hand", color: RED, transform: "rotate(-4deg)"}}>
        <Write p={span(f, W[24].f0 + 22, W[24].f0 + 40)}>top score</Write>
      </div>
      {/* 11-20：红色料珠去掉（导演：全片不要带路红点），换成上面的视线引导 */}
    </AbsoluteFill>
    </Lens>
  );
};

const Root = () => <Composition id="Manual205" component={Scene} durationInFrames={T.len_f} fps={T.fps} width={1920} height={1080} />;
registerRoot(Root);
