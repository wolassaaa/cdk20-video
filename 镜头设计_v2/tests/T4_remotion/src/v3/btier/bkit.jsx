// HKBU SCIE1007 课程作业的科普视频：B 档页面套件（Remotion + SVG + GSAP），规格见 镜头设计_v3/深化/11_铺开排序.md 第五节。
// 画面五层：L0 Blender 渲的虚化大板（BoardPlate）→ L1 接触阴影 → L2 零件贴图（Sprite，Blender 渲的透明 PNG）和 SVG 机构（Slab、Runner、Gauge…）
// → L3 标签、出处行（Instrument Serif）→ L4 手写批注（Caveat）；最上面一层颗粒（Grain，和出镜段合成同一个颗粒函数，b_page.py 生成）。
// 动作一律 GSAP 暂停时间线 + 逐帧 seek（gsapFrame.js）；时间从事件表 keys_<段>.json 读。视线引导用 manual/kit.jsx 的 Lens / Layer / guidePlan / nudge。
import React from "react";
import {AbsoluteFill, Img, staticFile, useCurrentFrame, delayRender, continueRender, getInputProps} from "remotion";
import {useGsapTimeline, FPS, RULE} from "./gsapFrame.jsx";
import SM from "./bsprite_meta.json";

// ---------------------------------------------------------------- 5.2 配色（只许用这些，取自 kit_parts.py）
export const C = {
  table: "#F3EEE6",      // 背景台面
  bone: "#F4F1EA",       // 骨白：料杆、白件、路
  blue: "#002FA7",       // 克莱因蓝：CDK20、插座
  blueHi: "#3D6BE6",     // 蓝高光
  red: "#C8102E",        // 红：插孔红环、描红、红尾巴、"?"
  gold: "#E2CFA0",       // 金：钥匙、假插头
  black: "#1E1E20",      // 黑：芯片
  ink: "#1F1E1C",        // 字（深）
  inkLight: "#F7F4EE",   // 字（浅，印在深色件上）
  grey: "#9A968C",       // 灰字、未达成
  green: "#5E8A64",      // 绿：打勾
  soft: "#6E6B63",       // 次要说明字
  yellow: "#FFF33F",     // ATP 透明黄：kit_parts.py K.yellow 线性 (1.0, 0.90, 0.05) 转 sRGB；只给真插头和插座灯
};
export const PALETTE = Object.values(C);

// 颜色明暗：亮面塑料的侧面、暗部由底色算出来（不另选色）
const hex = (c) => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
const toHex = (a) => "#" + a.map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, "0")).join("");
export const shade = (c, k) => toHex(hex(c).map((v) => v * (1 - k)));          // 暗 k（0.22 = 侧面）
export const tint = (c, k) => toHex(hex(c).map((v) => v + (255 - v) * k));     // 亮 k

// ---------------------------------------------------------------- 字（5.7）
// Instrument Serif 的大写字母高约 0.70 em：标签 44 px → 大写约 31 px（≥ 28）；出处行 28 px → 约 19.6 px（≥ 18）。
// 11-21 B 档视觉规则 v2 R04：标签 ≥ 36 px（默认仍 44）、出处行 22 px、批注 Caveat 34–44 px；字幕区 y ≥ 940
export const LABEL_MIN = 36, LABEL_PX = 44, SOURCE_PX = 30, SUB_TOP = 940;   // 出处行：规则 v2 写 22 px，Gemini 6-01/6-02 两次说看不清（26 也说小），取 30（R04 下限 22 之上）
// 11-20 晚查出：以前写 fontFamily "Serif"（不带引号）在 CSS 里就是通用族 serif，浏览器用的是 Times New Roman，Instrument Serif 根本没上。
// 这里用一个不会撞通用族名的名字自己装载（装不上就抛错，页面渲不出来，不会悄悄换成 Times）。
export const SERIF = "'InstrumentSerifB', serif";
if (typeof window !== "undefined" && !window.__bSerif) {
  window.__bSerif = true;
  const h = delayRender("Instrument Serif");
  Promise.all([["InstrumentSerif-Regular.ttf", "normal"], ["InstrumentSerif-Italic.ttf", "italic"]]
    .map(([file, st]) => new FontFace("InstrumentSerifB", `url(${staticFile("fonts/" + file)})`, {style: st}).load().then((x) => document.fonts.add(x))))
    .then(() => continueRender(h))
    .catch((e) => { throw new Error("Instrument Serif 装载失败：" + e); });
}

// ---------------------------------------------------------------- 检查探针（b_page.py check 用 --props='{"bprobe":6}' 渲一遍半分辨率）
// 开着时：不铺 L0 大板和颗粒（只剩前景，帧差量"前景静止"），每 bprobe 帧把字和零件的框打到浏览器日志（BPROBE|{...}），
// b_page.py 读日志查字体、字号、同屏标签数、标签框和零件掩码的重叠。正式渲染不开，不影响画面。
export const PROBE = (() => { try { return Number(getInputProps().bprobe || 0); } catch (e) { return 0; } })();
const effOp = (el) => { let o = 1; for (let e = el; e && e.nodeType === 1; e = e.parentElement) { const cs = getComputedStyle(e); o *= Number(cs.opacity); if (cs.visibility === "hidden" || cs.display === "none") return 0; } return o; };
const rnd = (v) => Math.round(v);
export const probeScan = (f) => {
  const T = [], P = [];
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = tw.nextNode(); n; n = tw.nextNode()) {
    const t = n.textContent.trim();
    if (!t) continue;
    const el = n.parentElement;
    if (el.closest("[data-role=counter]")) continue;      // 数字轮：整个计数器记一条（下面），不记轮上每个数字
    const op = effOp(el);
    if (op < 0.1) continue;
    const rg = document.createRange();
    rg.selectNodeContents(n);
    const b = rg.getBoundingClientRect();
    if (b.width < 1 || b.right < 0 || b.left > 1920 || b.bottom < 0 || b.top > 1080) continue;
    const cs = getComputedStyle(el);
    const r = ["label", "pen", "tag", "source"].find((q) => el.closest(`[data-role=${q}]`)) || (el.closest("[data-role=engrave]") ? "engrave" : "raw");
    const roleEl = el.closest(`[data-role=${r}]`), own = el.closest("[data-pid]");
    T.push({t: t.slice(0, 40), role: r, rid: roleEl ? roleEl.dataset.rid || "" : "", on: roleEl ? roleEl.dataset.on || "" : "", ff: cs.fontFamily, fs: parseFloat(cs.fontSize),
            x: rnd(b.left), y: rnd(b.top), w: rnd(b.width), h: rnd(b.height), op: Math.round(op * 100) / 100, own: own ? own.dataset.pid : ""});
  }
  document.querySelectorAll("[data-role=counter]").forEach((el) => {
    const op = effOp(el), b = el.getBoundingClientRect(), cs = getComputedStyle(el);
    if (op >= 0.1 && b.width >= 1) T.push({t: "#counter", role: "counter", rid: "", ff: cs.fontFamily, fs: parseFloat(cs.fontSize), x: rnd(b.left), y: rnd(b.top), w: rnd(b.width), h: rnd(b.height), op: Math.round(op * 100) / 100, own: ""});
  });
  document.querySelectorAll("[data-pid]").forEach((el) => {
    const op = effOp(el);
    if (op < 0.1) return;
    const b = el.getBoundingClientRect();
    if (b.width < 1 || b.right < 0 || b.left > 1920 || b.bottom < 0 || b.top > 1080) return;
    const up = el.parentElement && el.parentElement.closest("[data-pid]");
    P.push({pid: el.dataset.pid, name: el.dataset.part, x: rnd(b.left), y: rnd(b.top), w: rnd(b.width), h: rnd(b.height), op: Math.round(op * 100) / 100, up: up ? up.dataset.pid : ""});
  });
  console.log("BPROBE|" + JSON.stringify({f, T, P}));
};
const ProbeTap = ({f}) => {
  React.useEffect(() => { if (PROBE && f % PROBE === 0) probeScan(f); }, [f]);
  return null;
};
let PID = 0;
const pidOf = (name) => `${name}#${(PID = (PID + 1) % 1000000)}`;

// ---------------------------------------------------------------- 事件表
export const evMapB = (K) => Object.fromEntries(K.events.map((e) => [e.id, {s: e.f_start, l: e.f_land, e: e.f_end}]));

// ---------------------------------------------------------------- L0 背景大板（Blender 渲，720 帧来回播放）
export const PLATE_N = 720;
export const pingpong = (f, n = PLATE_N) => { const p = 2 * (n - 1); const m = ((f % p) + p) % p; return m < n ? m : p - m; };
export const BoardPlate = ({zone, f, offset = 0, veil = 0.3}) => {
  const i = pingpong(f + offset);
  return (
    <>
      <Img src={staticFile(`bplate/zone${zone}/${String(i).padStart(4, "0")}.jpg`)} style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080}} />
      {/* 台面色薄纱 30%：大板上的蓝、金、红件退后一层，前景零件和字跳出来（11-20 试渲：不加纱时背景和前景一样艳，抢主体） */}
      <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, background: C.table, opacity: veil}} />
    </>
  );
};

// ---------------------------------------------------------------- 颗粒（全画面最上层；b_page.py 用 shot_oncam._grain 同一个函数出 24 张灰底颗粒图，overlay 叠）
export const Grain = ({f, n = 24, opacity = 1}) => (
  <Img src={staticFile(`grain/${String(((f % n) + n) % n).padStart(2, "0")}.png`)}
       style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, mixBlendMode: "overlay", opacity, pointerEvents: "none"}} />
);

// ---------------------------------------------------------------- L1 接触阴影
// 椭圆，模糊 14 px，不透明度 0.28，相对零件偏移 (+6, +10)；零件每升高 10 px 阴影放大 4%、淡 0.03。
export const Shadow = ({cx, cy, rx, ry, lift = 0, op = 1}) => {
  const k = Math.max(0, lift) / 10;
  const s = 1 + 0.04 * k, o = Math.max(0, 0.28 - 0.03 * k) * op;
  return (
    <div style={{position: "absolute", left: cx + 6 - rx * s, top: cy + 10 + lift - ry * s, width: 2 * rx * s, height: 2 * ry * s,
                 borderRadius: "50%", background: "#000", opacity: o, filter: "blur(14px)"}} />
  );
};

// ---------------------------------------------------------------- L2 零件贴图
// name = "<零件>/<姿态>"（bsprite_meta.json：裁边后的宽高、锚点）。x, y 是贴图中心（或 anchor 指定的锚点）落在画面的位置，w 是显示宽。
// 贴图按 2 倍出，放大不超过 1.6 倍（显示宽 ≤ 原图宽 × 0.8）。lift：离开板面的高度（影子跟着变）。rim：轮廓光（引导点名时 +0.3 档亮边）。
export const spriteMeta = (name) => {
  const m = SM[name];
  if (!m) throw new Error(`没有贴图 ${name}（先跑 b_page.py post）`);
  return m;
};
export const anchorOf = (name, key, w) => {
  const m = spriteMeta(name);
  const a = m.anchors[key];
  if (!a) throw new Error(`${name} 没有锚点 ${key}`);
  const k = w / m.w;
  return [(a[0] - m.w / 2) * k, (a[1] - m.h / 2) * k];
};
export const Sprite = ({name, x, y, w, rot = 0, sx = 1, sy = 1, op = 1, lift = 0, shadow = true, shadowSq = 0.22, rim = 0, anchor, style, children}) => {
  const m = spriteMeta(name);
  if (w > m.w * 0.8 + 1) throw new Error(`${name} 放大超过 1.6 倍：显示宽 ${w}，原图 ${m.w}`);
  const h = (w * m.h) / m.w;
  let ox = 0, oy = 0;
  if (anchor) [ox, oy] = anchorOf(name, anchor, w);
  const cx = x - ox, cy = y - oy;
  const fl = [];
  if (rim > 0.002) fl.push(`drop-shadow(0 0 3px rgba(255,250,235,${(0.95 * rim).toFixed(3)}))`, `brightness(${(1 + 0.08 * rim).toFixed(3)})`);
  return (
    <>
      {shadow && op > 0.01 && <Shadow cx={cx} cy={cy + h * 0.5 - h * shadowSq * 0.5} rx={w * 0.42} ry={h * shadowSq * 0.5} lift={lift} op={op} />}
      <div data-part={name} data-pid={PROBE ? pidOf(name) : undefined} style={{position: "absolute", left: cx - w / 2, top: cy - h / 2 - lift, width: w, height: h, opacity: op,
                   transform: `rotate(${rot}deg) scale(${sx},${sy})`, filter: fl.length ? fl.join(" ") : undefined, ...style}}>
        <Img src={staticFile(`bsprite/${name}.png`)} style={{width: w, height: h, display: "block"}} />
        {children}
      </div>
    </>
  );
};

// ---------------------------------------------------------------- SVG 件的材质感（5.3）：一块亮面塑料牌，不是色块
// 1 厚度：底下 depth px 侧面，比正面暗 22%；2 倒角高光：上、左内缩 1.5 px 白线 0.6；3 镜面带：左上→右下，宽 12%，0.35→0，件动时滑过（sheen 0→1）；
// 4 暗部：右下内阴影，正片叠底 0.18；5 接触阴影（Shadow）。不画黑描边。字是"刻"上去的：字色 + 下方 1 px 亮线。
let SLAB_ID = 0;
export const Slab = ({x, y, w, h, r = 14, color = C.bone, depth = 8, sheen = -1, lift = 0, op = 1, shadow = true, rot = 0, gate, children, id}) => {
  const uid = id || `slab${(SLAB_ID = (SLAB_ID + 1) % 100000)}`;
  const side = shade(color, 0.22);
  const s0 = sheen < 0 ? -1 : -0.2 + 1.4 * sheen;   // 镜面带中心（对角线上的位置）
  return (
    <>
      {shadow && op > 0.01 && <Shadow cx={x + w / 2} cy={y + h / 2 + depth / 2} rx={w * 0.5} ry={h * 0.5} lift={lift} op={op} />}
      <div data-part="slab" data-pid={PROBE ? pidOf("slab") : undefined} style={{position: "absolute", left: x, top: y - lift, width: w, height: h + depth, opacity: op, transform: rot ? `rotate(${rot}deg)` : undefined}}>
        <svg width={w + 2} height={h + depth + 2} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
          <defs>
            <linearGradient id={`${uid}s`} x1="0" y1="0" x2="1" y2="1">
              <stop offset={Math.max(0, s0 - 0.06)} stopColor="#fff" stopOpacity="0" />
              <stop offset={Math.min(1, Math.max(0, s0))} stopColor="#fff" stopOpacity={sheen < 0 ? 0 : 0.35} />
              <stop offset={Math.min(1, s0 + 0.06)} stopColor="#fff" stopOpacity="0" />
            </linearGradient>
            <linearGradient id={`${uid}d`} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0.55" stopColor="#000" stopOpacity="0" />
              <stop offset="1" stopColor="#000" stopOpacity="0.18" />
            </linearGradient>
            <linearGradient id={`${uid}t`} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#fff" stopOpacity="0.16" />
              <stop offset="0.5" stopColor="#fff" stopOpacity="0" />
            </linearGradient>
          </defs>
          <rect x={0} y={depth} width={w} height={h} rx={r} fill={side} />
          <rect x={0} y={0} width={w} height={h} rx={r} fill={color} />
          <rect x={0} y={0} width={w} height={h} rx={r} fill={`url(#${uid}t)`} />
          <rect x={0} y={0} width={w} height={h} rx={r} fill={`url(#${uid}d)`} style={{mixBlendMode: "multiply"}} />
          {sheen >= 0 && <rect x={0} y={0} width={w} height={h} rx={r} fill={`url(#${uid}s)`} />}
          <path d={`M${1.5},${h - r} L${1.5},${r} Q${1.5},${1.5} ${r},${1.5} L${w - r},${1.5}`} fill="none" stroke="#fff" strokeOpacity="0.6" strokeWidth="1.5" />
        </svg>
        <div style={{position: "absolute", left: 0, top: 0, width: w, height: h}}>{children}</div>
      </div>
      {gate && <Gate {...gate} />}
    </>
  );
};

// 浇口：一个小锥，从料杆接到件上；broken 0→1 时在件这一头断开、锥尖往回缩
export const Gate = ({x1, y1, x2, y2, w = 9, broken = 0, color = C.bone}) => {
  const L = Math.hypot(x2 - x1, y2 - y1), a = (Math.atan2(y2 - y1, x2 - x1) * 180) / Math.PI;
  const len = L * (1 - 0.35 * broken);
  return (
    <svg style={{position: "absolute", left: 0, top: 0, overflow: "visible"}} width={1} height={1}>
      <g transform={`translate(${x1},${y1}) rotate(${a})`}>
        <path d={`M0,${-w / 2} L${len},${-w * 0.18} L${len},${w * 0.18} L0,${w / 2} Z`} fill={shade(color, 0.06)} />
        <path d={`M0,${-w / 2} L${len},${-w * 0.18}`} stroke="#fff" strokeOpacity="0.55" strokeWidth="1.2" />
        {broken > 0 && broken < 1 && <circle cx={len} cy={0} r={w * 0.4 * (1 - broken)} fill="#fff" opacity={0.7 * (1 - broken)} />}
      </g>
    </svg>
  );
};

// 料杆 / 路：骨白圆杆（下暗边、上高光线），d 是 SVG 路径；draw 0→1 描出
export const Runner = ({d, width = 16, draw = 1, color = C.bone, op = 1}) => (
  <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, opacity: op, overflow: "visible"}}>
    <path d={d} fill="none" stroke="#000" strokeOpacity="0.16" strokeWidth={width + 2} strokeLinecap="round" transform="translate(6,10)" style={{filter: "blur(6px)"}}
          pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - draw} />
    <path d={d} fill="none" stroke={shade(color, 0.22)} strokeWidth={width} strokeLinecap="round" transform="translate(0,3)" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - draw} />
    <path d={d} fill="none" stroke={color} strokeWidth={width - 2} strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - draw} />
    <path d={d} fill="none" stroke="#fff" strokeOpacity="0.7" strokeWidth={2.2} strokeLinecap="round" transform={`translate(0,${-width * 0.22})`} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - draw} />
  </svg>
);

// 刻字：字色 + 下方 1 px 亮线（"刻"进件里）
export const Engrave = ({children, size = 44, color = C.ink, light = false, style, italic}) => (
  <span data-role="engrave" style={{fontFamily: SERIF, fontSize: size, color: light ? C.inkLight : color, fontStyle: italic ? "italic" : "normal",
                textShadow: light ? "0 1px 0 rgba(0,0,0,0.35)" : "0 1px 0 rgba(255,255,255,0.65)", whiteSpace: "nowrap", lineHeight: 1, ...style}}>{children}</span>
);

// ---------------------------------------------------------------- L3 标签：按词拆，每词错开 3 帧、上移 12 px 淡入（SplitText 的做法，补间普通对象）
// at = 第一个词落定的帧（一般是事件 f_land）；out = 收起的帧（可不给）。字号不小于 44（大写约 31 px）。
export const Label = ({text, x, y, at, out, size = LABEL_PX, color = C.ink, align = "left", italic, w, plate, on}) => {
  if (size < LABEL_MIN) throw new Error(`标签字号 ${size} 小于 ${LABEL_MIN}`);
  if (y + size * 1.1 > SUB_TOP) throw new Error(`标签 "${text}" 压进字幕区（y=${y}）`);
  const words = String(text).split(" ");
  const S = useGsapTimeline((tl, S) => {
    S.w = words.map(() => ({o: 0, y: RULE.rise}));
    S.out = 0;
    tl.fromTo(S.w, {o: 0, y: RULE.rise}, {o: 1, y: 0, duration: 12 / FPS, ease: "power2.out", stagger: RULE.word / FPS, immediateRender: false}, (at - 10) / FPS);
    if (out != null) tl.fromTo(S, {out: 0}, {out: 1, duration: 12 / FPS, ease: "power2.in", immediateRender: false}, out / FPS);
  }, [text, at, out]);
  const tx = align === "center" ? "-50%" : align === "right" ? "-100%" : "0";
  const body = (
    <div style={{display: "inline-flex", gap: size * 0.26, whiteSpace: "nowrap"}}>
      {words.map((wd, i) => (
        <span key={i} style={{display: "inline-block", opacity: S.w[i].o * (1 - S.out), transform: `translateY(${S.w[i].y - 8 * S.out}px)`}}>
          <Engrave size={size} color={color} italic={italic} light={plate && plate !== C.bone && plate !== C.gold}>{wd}</Engrave>
        </span>
      ))}
    </div>
  );
  return <div data-role="label" data-rid={text} data-on={on} style={{position: "absolute", left: x, top: y, transform: `translateX(${tx})`, width: w}}>{body}</div>;
};

// ---------------------------------------------------------------- L4 手写批注：Caveat，从左到右描出 24–36 帧（遮罩前沿是一支笔的走势，带一点起伏）
export const Pen = ({text, x, y, at, out, dur = 30, size: size0 = 40, color = C.ink, rot = -3, on}) => {
  const size = Math.max(34, Math.min(44, size0));      // R04：Caveat 批注 34–44 px（老页面写的 52 在这里收到 44）
  const S = useGsapTimeline((tl, S) => {
    S.p = 0;
    S.o = 1;
    tl.fromTo(S, {p: 0}, {p: 1, duration: Math.max(RULE.pen[0], Math.min(RULE.pen[1], dur)) / FPS, ease: "power1.inOut", immediateRender: false}, at / FPS);
    if (out != null) tl.fromTo(S, {o: 1}, {o: 0, duration: 12 / FPS, ease: "power2.in", immediateRender: false}, out / FPS);
  }, [at, dur, out]);
  if (y + size > SUB_TOP) throw new Error(`批注 "${text}" 压进字幕区`);
  const lx = -6 + 112 * S.p;
  const m = `linear-gradient(90deg,#000 ${lx - 4}%,transparent ${lx}%)`;
  return (
    <div data-role="pen" data-rid={text} data-on={on} style={{position: "absolute", left: x, top: y, opacity: S.p > 0 ? S.o : 0, transform: `rotate(${rot}deg)`, font: `${size}px Hand`, color, whiteSpace: "nowrap",
                 WebkitMaskImage: m, maskImage: m, padding: "0 0.3em", margin: "0 -0.3em"}}>{text}</div>
  );
};

// ---------------------------------------------------------------- 出处行（5.7）：Instrument Serif，≥ 28 px（大写约 20 px），在字幕区上面
export const Source = ({children, op = 1, x = 64, y}) => {
  // 规则 v2 R09：左下 x = 64、底边 y = 924（字幕区 940 之上），Instrument Serif 22 px，字 #6E6B63（C.soft），骨白磨砂底 0.78、圆角 4、左右内边距 12
  const top = y != null ? Math.min(y, 928 - 42) : 928 - 42;
  if (top + 42 > SUB_TOP) throw new Error("出处行压进字幕区");
  return <div data-role="source" style={{position: "absolute", left: x, top, height: 42, boxSizing: "border-box", padding: "5px 12px 0", borderRadius: 4, background: "rgba(244,241,234,0.86)",
                      fontFamily: SERIF, fontSize: SOURCE_PX, letterSpacing: 0.3, color: C.ink, opacity: op, whiteSpace: "nowrap", lineHeight: 1.1}}>{children}</div>;
};

// 图注小牌（PREDICTED MODEL、OUR RE-DOCKING 这类）：和出处行同一套底，30 px，大写字距 1
export const Tag = ({children, x, y, op = 1, align = "center", on}) => (
  <div data-role="tag" data-on={on} style={{position: "absolute", left: x, top: y, transform: align === "center" ? "translateX(-50%)" : align === "right" ? "translateX(-100%)" : undefined,
               padding: "3px 12px 5px", borderRadius: 10, background: "rgba(243,238,230,0.80)", fontFamily: SERIF, fontSize: 30, letterSpacing: 1,
               color: C.ink, opacity: 0.88 * op, whiteSpace: "nowrap", lineHeight: 1.2}}>{children}</div>
);

// ---------------------------------------------------------------- 插座灯：灯位锚点上的一团暖黄光晕（ATP 透明黄，只给插座灯和真插头）。on 0→1
export const Lamp = ({name, x, y, w, on = 1, r}) => {
  if (on <= 0.01) return null;
  const [dx, dy] = anchorOf(name, "lamp_on", w);
  const rr = r || Math.max(8, w * 0.07);
  return <div style={{position: "absolute", left: x + dx - rr, top: y + dy - rr, width: 2 * rr, height: 2 * rr, borderRadius: rr, background: C.yellow,
                      opacity: 0.75 * on, filter: `blur(${(rr * 0.45).toFixed(1)}px)`, mixBlendMode: "screen"}} />;
};

// ---------------------------------------------------------------- 计数轮：数字一位一位滚，停的那一帧落在词上（value 由页面的时间线给）
export const Counter = ({value, digits = 2, decimals = 0, size = 96, color = C.ink, x, y, align = "left", comma = false}) => {
  const n = Math.max(0, value) * Math.pow(10, decimals);
  const total = digits + decimals, h = size * 1.05, cw = size * 0.5;
  const cols = [];
  for (let i = total - 1; i >= 0; i--) {
    const p = Math.pow(10, i);
    // 里程表：个位连续转；高位只在低一位 9→0 的那一格里转过去
    const pos = i === 0 ? n % 10 : (Math.floor(n / p) % 10) + Math.min(1, Math.max(0, (n % p) - (p - 1)));
    const hide = i > decimals && n < p - 0.5;           // 不显示前导零
    cols.push({pos, hide, dot: i === decimals && decimals > 0, comma: comma && i === decimals + 2 && n >= 999.5 * Math.pow(10, decimals)});   // 千分位逗号在百位前
  }
  return (
    <div data-role="counter" style={{position: "absolute", left: x, top: y, display: "flex", transform: align === "right" ? "translateX(-100%)" : align === "center" ? "translateX(-50%)" : undefined,
                 fontFamily: SERIF, fontSize: size, color, lineHeight: `${h}px`, height: h, overflow: "hidden", textShadow: "0 1px 0 rgba(255,255,255,0.65)"}}>
      {cols.map((c, i) => (
        <React.Fragment key={i}>
          {c.comma && !c.hide && <span>,</span>}
          <span style={{display: "inline-block", width: c.hide ? 0 : cw, height: h, overflow: "hidden", position: "relative"}}>
            <span style={{position: "absolute", left: 0, top: -c.pos * h, display: "flex", flexDirection: "column"}}>
              {[...Array(11)].map((_, k) => <span key={k} style={{height: h, textAlign: "center", width: cw}}>{k % 10}</span>)}
            </span>
          </span>
          {c.dot && <span>.</span>}
        </React.Fragment>
      ))}
    </div>
  );
};

// ---------------------------------------------------------------- 表盘（SVG 件）：圆形亮面牌 + 刻度 + 指针；angle 由页面给
export const Dial = ({cx, cy, r, color = C.bone, ticks = [], needle = 0, ghost, label, labelSize = 44, needleColor = C.ink, sheen = -1, lift = 0, op = 1}) => {
  const a2 = (a) => ((a - 90) * Math.PI) / 180;
  return (
    <>
      <Slab x={cx - r} y={cy - r} w={2 * r} h={2 * r} r={r} color={color} depth={10} sheen={sheen} lift={lift} op={op} />
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: -lift, overflow: "visible", opacity: op}}>
        {ticks.map(([ang, txt, big], i) => (
          <g key={i}>
            <line x1={cx + (r - 14) * Math.cos(a2(ang))} y1={cy + (r - 14) * Math.sin(a2(ang))} x2={cx + (r - (big ? 34 : 24)) * Math.cos(a2(ang))} y2={cy + (r - (big ? 34 : 24)) * Math.sin(a2(ang))}
                  stroke={C.ink} strokeWidth={big ? 4 : 2.5} strokeLinecap="round" />
            {txt && <text x={cx + (r - 66) * Math.cos(a2(ang))} y={cy + (r - 66) * Math.sin(a2(ang)) + 12} textAnchor="middle" fontFamily={SERIF} fontSize={34} fill={C.ink}>{txt}</text>}
          </g>
        ))}
        {ghost != null && <g opacity={0.45}><line x1={cx} y1={cy} x2={cx + (r - 30) * Math.cos(a2(ghost))} y2={cy + (r - 30) * Math.sin(a2(ghost))} stroke={C.grey} strokeWidth={7} strokeLinecap="round" /></g>}
        <line x1={cx + 3} y1={cy + 5} x2={cx + 3 + (r - 30) * Math.cos(a2(needle))} y2={cy + 5 + (r - 30) * Math.sin(a2(needle))} stroke="#000" strokeOpacity="0.18" strokeWidth={8} strokeLinecap="round" style={{filter: "blur(3px)"}} />
        <line x1={cx} y1={cy} x2={cx + (r - 30) * Math.cos(a2(needle))} y2={cy + (r - 30) * Math.sin(a2(needle))} stroke={needleColor} strokeWidth={7} strokeLinecap="round" />
        <circle cx={cx} cy={cy} r={14} fill={C.black} />
        <circle cx={cx - 4} cy={cy - 4} r={4} fill="#fff" opacity={0.5} />
        {label && <text x={cx} y={cy + r * 0.48} textAnchor="middle" fontFamily={SERIF} fontSize={labelSize} fill={C.ink} style={{textShadow: "0 1px 0 rgba(255,255,255,0.65)"}}>{label}</text>}
      </svg>
    </>
  );
};

// ---------------------------------------------------------------- 打勾（绿）：描出
export const Tick = ({x, y, s = 60, p = 0, color = C.green, sw = 10}) => (
  <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
    <path d={`M${x - s * 0.45},${y} L${x - s * 0.1},${y + s * 0.35} L${x + s * 0.5},${y - s * 0.4}`} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round"
          pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />
  </svg>
);

// ---------------------------------------------------------------- 路径（MotionPath 的做法）：Catmull-Rom 过点，按弧长取位置；速度不超过每秒 0.6 个画面宽
export const pathOf = (pts, n = 400) => {
  const P = (i) => pts[Math.max(0, Math.min(pts.length - 1, i))];
  const smp = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = P(i - 1), p1 = P(i), p2 = P(i + 1), p3 = P(i + 2);
    const m = Math.max(2, Math.round(n / (pts.length - 1)));
    for (let k = 0; k < m; k++) {
      const t = k / m, t2 = t * t, t3 = t2 * t;
      smp.push([0, 1].map((j) => 0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)));
    }
  }
  smp.push(pts[pts.length - 1]);
  const L = [0];
  for (let i = 1; i < smp.length; i++) L.push(L[i - 1] + Math.hypot(smp[i][0] - smp[i - 1][0], smp[i][1] - smp[i - 1][1]));
  const at = (u) => {
    const s = Math.max(0, Math.min(1, u)) * L[L.length - 1];
    let i = 1;
    while (i < L.length - 1 && L[i] < s) i++;
    const q = (s - L[i - 1]) / Math.max(1e-6, L[i] - L[i - 1]);
    const a = smp[i - 1], b = smp[i];
    return [a[0] + (b[0] - a[0]) * q, a[1] + (b[1] - a[1]) * q, (Math.atan2(b[1] - a[1], b[0] - a[0]) * 180) / Math.PI];
  };
  const d = "M" + smp.map((p) => p.map((v) => v.toFixed(1)).join(",")).join(" L");
  return {at, d, length: L[L.length - 1]};
};
export const maxPathFrames = (length) => Math.ceil(length / (0.6 * 1920) * FPS);   // 0.6 画面宽 / 秒的下限时长

// ---------------------------------------------------------------- 转场（5.6）
// T5 焦点擦除：Blender 预渲 34 帧（bwipe/<名>/0000–0033），第 17 帧盖满。页首放 17–33（出），页尾放 0–17（进，最后一帧盖满）。
export const WIPE_N = 34, WIPE_COVER = 17;
export const T5In = ({name, f}) => (f < 0 || f > WIPE_N - 1 - WIPE_COVER ? null :
  <Img src={staticFile(`bwipe/${name}/${String(WIPE_COVER + f).padStart(4, "0")}.png`)} style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080}} />);
export const T5Out = ({name, f, len}) => {
  const i = f - (len - 1 - WIPE_COVER);
  return i < 0 || i > WIPE_COVER ? null :
    <Img src={staticFile(`bwipe/${name}/${String(i).padStart(4, "0")}.png`)} style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080}} />;
};
// T6 光扫：240 px 宽、斜 20° 的白色渐变带，16 帧扫过，峰值不透明度 0.55，最亮处不过曝（screen 叠，白底处只到 0.55）
export const T6Sweep = ({f, at}) => {
  const p = (f - at) / 16;
  if (p < 0 || p > 1) return null;
  const x = -400 + p * (1920 + 800);
  return (
    <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, overflow: "hidden", pointerEvents: "none", mixBlendMode: "screen"}}>
      <div style={{position: "absolute", left: x - 120, top: -300, width: 240, height: 1680, transform: "rotate(20deg)",
                   background: "linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,250,240,0.55) 50%, rgba(255,255,255,0) 100%)"}} />
    </div>
  );
};
// T2 甩镜：整个舞台横移 1.2 个画面宽，7 帧，横向模糊（feGaussianBlur "40 0"）。dir=-1 往左甩出；mode="in" 从右边甩进
export const whipX = (f, at, mode = "out", dir = -1) => {
  const p = mode === "out" ? (f - at) / 7 : 1 - (f - at) / 7;
  if (p <= 0 || p >= 1) return mode === "out" ? (p >= 1 ? dir * 1.2 * 1920 : 0) : (p >= 1 ? -dir * 1.2 * 1920 : 0);
  const e = mode === "out" ? p * p : p * p;
  return (mode === "out" ? dir : -dir) * 1.2 * 1920 * e;
};
export const WhipFilter = () => (
  <svg width={0} height={0} style={{position: "absolute"}}>
    <defs><filter id="whipblur" x="-20%" y="0" width="140%" height="100%"><feGaussianBlur stdDeviation="40 0" /></filter></defs>
  </svg>
);
// T7 落位冲击：那一帧起舞台抖 2 帧、±6 px
export const impact = (f, at) => (f === at ? 6 : f === at + 1 ? -6 : 0);

// ---------------------------------------------------------------- 舞台：L0 + 内容 + 颗粒 + 擦除，页面只填内容
// 裁一块贴图：box = [左, 上, 右, 下]（占贴图宽高的比例）。(x, y) 是裁出那块的中心，w 是整张贴图的显示宽。
// capsule/34 是三粒叠放 → Capsule1 取最前面那一粒；person/34 是白、红两个小人 → Person1 取一个。
export const SpriteCrop = ({name, box, x, y, w, rot = 0, op = 1, lift = 0, sx = 1, sy = 1, shadow = true, round = 0, style}) => {
  const m = spriteMeta(name);
  if (w > m.w * 0.8 + 1) throw new Error(`${name} 放大超过 1.6 倍：显示宽 ${w}，原图 ${m.w}`);
  const h = (w * m.h) / m.w;
  const [l, t, r, b] = box;
  const fx = (l + r) / 2, fy = (t + b) / 2;
  const cx = x - (fx - 0.5) * w, cy = y - (fy - 0.5) * h;
  return (
    <>
      {shadow && op > 0.01 && <Shadow cx={x} cy={y + (b - t) * h * 0.38} rx={(r - l) * w * 0.42} ry={(b - t) * h * 0.12} lift={lift} op={op} />}
      <div style={{position: "absolute", left: cx - w / 2, top: cy - h / 2 - lift, width: w, height: h, opacity: op, transformOrigin: `${fx * w}px ${fy * h}px`,
                   transform: `rotate(${rot}deg) scale(${sx},${sy})`, clipPath: `inset(${t * 100}% ${(1 - r) * 100}% ${(1 - b) * 100}% ${l * 100}%${round ? ` round ${(round * h).toFixed(1)}px` : ""})`, ...style}}>
        <Img src={staticFile(`bsprite/${name}.png`)} style={{width: w, height: h, display: "block"}} />
      </div>
    </>
  );
};
// 前面那一粒：圆角裁成药丸形，后面那粒露不出来
// 日历：calendar/34 贴图下面连着一把尺子（Gemini 初审 11-20：尺子和"天数"不搭）。按日历轮廓裁掉尺子；x, y 是日历本身的中心，w 按原来整张图的宽给，内部放大 1.3 倍补回尺寸
export const Calendar1 = ({x, y, w, ...p}) => {
  const W = Math.min(671, w * 1.3), k = W / 839;
  return <Sprite name="calendar/34" x={x + 89.5 * k} y={y + 75 * k} w={W} shadow={false} {...p}
                 style={{clipPath: "polygon(11.5% 13%, 19% 4%, 55% 0%, 67% 8%, 66% 52%, 64.5% 56.5%, 28% 67.5%, 23% 65%, 11.5% 38%)"}} />;
};
// 刻字牌：一块 Slab，正中刻一行字（站牌、来源卡、核对表行都用它）。x, y 是左上角
export const Plate = ({x, y, w, h, text, size = 44, color = C.bone, light = false, op = 1, id, depth = 8, r = 14, rot = 0, sheen = -1, lift = 0, align = "center", pad = 22, shadow = true, children}) => (
  <Slab x={x} y={y} w={w} h={h} r={r} color={color} depth={depth} op={op} id={id} rot={rot} sheen={sheen} lift={lift} shadow={shadow}>
    <div style={{width: w, height: h, display: "flex", alignItems: "center", justifyContent: align === "left" ? "flex-start" : "center", paddingLeft: align === "left" ? pad : 0, boxSizing: "border-box"}}>
      <Engrave size={size} light={light}>{text}</Engrave>
    </div>
    {children}
  </Slab>
);
// 放大镜（骨白框 + 柄，镜片一层亮光）：x, y 是镜片中心
export const LoupeRing = ({x, y, r = 80, op = 1, rot = 45}) => (
  <div style={{position: "absolute", left: x, top: y, width: 0, height: 0, opacity: op}}>
    <div style={{position: "absolute", left: 0, top: -r * 0.17, width: r * 1.9, height: r * 0.34, borderRadius: r * 0.17, background: C.bone,
                 transform: `rotate(${rot}deg) translateX(${r * 0.95}px)`, transformOrigin: `0 ${r * 0.17}px`, boxShadow: `0 10px 14px rgba(40,30,20,0.25), inset 0 -5px 0 ${shade(C.bone, 0.22)}`}} />
    <div style={{position: "absolute", left: -r, top: -r, width: 2 * r, height: 2 * r, borderRadius: r, background: "radial-gradient(circle at 32% 28%, rgba(255,255,255,0.55), rgba(255,255,255,0.08) 55%, rgba(61,107,230,0.10))"}} />
    <div style={{position: "absolute", left: -r - 12, top: -r - 12, width: 2 * r + 24, height: 2 * r + 24, borderRadius: r + 12, border: `12px solid ${C.bone}`, boxSizing: "border-box",
                 boxShadow: `0 12px 18px rgba(40,30,20,0.28), inset 0 3px 0 rgba(255,255,255,0.7), 0 -2px 0 ${shade(C.bone, 0.22)} inset`}} />
  </div>
);
export const Capsule1 = (p) => <SpriteCrop name="capsule/34" box={[0.26, 0.535, 0.935, 0.865]} round={0.165} {...p} />;
export const Person1 = ({red, ...p}) => <SpriteCrop name="person/34" box={red ? [0.5, 0.0, 1, 1] : [0, 0.08, 0.5, 1]} {...p} />;

// 磨砂：插座"看不清"（3-08、4-01）。k 0–1：虚焦 + 一层台面色磨砂
export const frost = (k) => (k > 0.01 ? {filter: `blur(${(10 * k).toFixed(1)}px) saturate(${1 - 0.5 * k})`, opacity: 1 - 0.35 * k} : undefined);

// 句尾机位：说完一句时，画面里最后落位的件已经停了，按规矩"动作接到句尾"，这时让机位横移一小段（L0 大板 0.35 倍视差，像真机位从台面上滑过）。
// 只给自然动作接不到句尾的句子用（check_sync S2 不过的句子），sids 例 ["s1", "s3"]；每段 ±A px，sine.inOut，峰值速度落在句末那一帧，方向逐句交替。
export const camBreath = (f, K, sids = [], A = 44, half = 45) => {
  let x = 0;
  sids.forEach((sid, j) => {
    const s = K.sentences.find((q) => q.sid.endsWith("." + sid));
    if (!s) throw new Error(`camBreath：找不到句子 ${sid}`);
    const u = Math.max(0, Math.min(1, (f - (s.f1 - half)) / (2 * half)));
    x += (j % 2 ? 1 : -1) * A * (0.5 - 0.5 * Math.cos(Math.PI * u));
  });
  return x;
};

export const Stage = ({zone, f, shakeX = 0, shakeY = 0, whip = 0, cam = 0, children, over}) => (
  <AbsoluteFill style={{background: C.table, overflow: "hidden"}}>
    <WhipFilter />
    <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translate(${whip + shakeX}px, ${shakeY}px)`,
                 filter: Math.abs(whip) > 1 ? "url(#whipblur)" : undefined}}>
      <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${(0.35 * cam).toFixed(2)}px) scale(1.02)`, transformOrigin: "960px 540px"}}>
        {!PROBE && <BoardPlate zone={zone} f={f} />}
        {/* 甩镜时板面是连着的：在甩来的那一侧再铺一块同一帧的大板，画面里不露出空台面 */}
        {Math.abs(whip) > 1 && [1, 2].map((k) => (
          <div key={k} style={{position: "absolute", left: (whip > 0 ? -1920 : 1920) * k, top: 0, width: 1920, height: 1080}}><BoardPlate zone={zone} f={f} /></div>))}
      </div>
      <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: cam ? `translateX(${cam.toFixed(2)}px)` : undefined}}>
        {children}
      </div>
    </div>
    {over}
    {!PROBE && <Grain f={f} />}
    {PROBE > 0 && <ProbeTap f={f} />}
  </AbsoluteFill>
);
