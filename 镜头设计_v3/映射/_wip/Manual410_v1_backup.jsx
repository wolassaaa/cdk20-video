// HKBU SCIE1007 课程作业的科普视频：第 4 章二维说明书页 4-10（画外音）docking / virtual screening。
// 左上点阵墙（几百个点代表 8,918 个新设计），一道波从上往下扫，点被扫到就点亮；红笔 too many to make 把墙和数字压暗。
// 右边先留虚线空位，虚拟锁长出，钥匙从设计堆里飞进锁孔、红圈标出 the pocket，打分条长起来再闪一下。
// 下面 8,918 → 54 → 7 的漏斗：点飘成 8 簇、54 个挑出来、7 个变红、7 把钥匙重墨画出、to make。
// 时间全读 keys_4-10.json（事件表 映射/events/4-10.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_4-10.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, Pen, Placeholder, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const ink = (a) => `rgba(31,30,28,${a})`;

/* ---------- 左：点阵墙 + 8 个簇 ---------- */
const COLS = 24, ROWS = 12, DX0 = 112, DY0 = 200, DS = 28, DR = 24, DOTR = 7;
const CC = [[190, 266], [350, 266], [510, 266], [670, 266], [190, 402], [350, 402], [510, 402], [670, 402]];
const SP = 16;                                     // 簇内格距（比点径大，不叠）
const DOTS = [...Array(COLS * ROWS)].map((_, i) => {
  const c = i % COLS, r = Math.floor(i / COLS);
  const x = DX0 + c * DS, y = DY0 + r * DR;
  let ci = 0, best = 1e9;
  CC.forEach(([cx, cy], k) => { const d = Math.hypot(x - cx, y - cy); if (d < best) { best = d; ci = k; } });
  return {i, c, r, x, y, ci, d: best};
});
const CLU = CC.map((_, k) => DOTS.filter((d) => d.ci === k).sort((a, b) => a.d - b.d));
CLU.forEach((arr, k) => {
  const n = arr.length, cols = Math.ceil(Math.sqrt(n)), rows = Math.ceil(n / cols);
  const slot = [...Array(n)].map((_, j) => [((j % cols) - (cols - 1) / 2) * SP, (Math.floor(j / cols) - (rows - 1) / 2) * SP]);
  slot.sort((p, q) => Math.hypot(p[0], p[1]) - Math.hypot(q[0], q[1]));
  arr.forEach((d, j) => { d.tx = CC[k][0] + slot[j][0]; d.ty = CC[k][1] + slot[j][1]; });
});
const SHORT = new Set(DOTS.slice().sort((a, b) => a.d - b.d).slice(0, 54).map((d) => d.i));   // 54 个挑出来
const SEVEN = new Set(CLU.slice(0, 7).map((arr) => arr[0].i));                                // 7 个（正好七，跟旁白和 7 把钥匙对上）
// 画序：普通点 → 短名单 → 7 个红的，后画的压在上面
const RANK = (d) => (SHORT.has(d.i) ? 1 : 0) + (SEVEN.has(d.i) ? 2 : 0);
const DRAW = [...DOTS].sort((a, b) => RANK(a) - RANK(b));
const JX = (i) => Math.sin(i * 12.9898) * 2.6;
const JY = (i) => Math.cos(i * 78.233) * 2.6;
const comma = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");

/* ---------- 右：锁、钥匙、打分框 ---------- */
const LKW = 300, LKCX = 1105, LKCY = 470, LKH = LKW * 743 / 520;   // 300 × 429，box 955..1255 × 255..685
const KHCX = LKCX + 1, KHCY = LKCY + 0.139 * LKH;                  // 锁孔（按零件图 0.504 / 0.639 的位置）
const KWW = 240, KWH = KWW * 312 / 1096;
const PX = 1400, PY = 380, PW = 410, PH = 330;
const BARS = [0.44, 0.9, 0.62];

const Scene = () => {
  const f = useCurrentFrame();

  /* 墙 */
  const wallP = span(f, E.wall.s, E.wall.e, ease);
  const settle = span(f, E.new.s, E.new.l + 6, out);
  const pop = f >= E.new.s ? 0.3 * Math.sin(Math.PI * Math.min(1, (f - E.new.s) / 16)) : 0;
  const dim1 = span(f, E.many.s, E.many.l, ease);
  const undim = span(f, E.similar.s, E.similar.l + 24, ease);
  const wallOp = 1 - 0.5 * dim1 * (1 - undim);
  const bandP = span(f, E.num.s, E.num.s + 44);
  const bandY = DY0 + ((f - E.num.s) / 3.3) * DR - 10;
  const count = Math.round(8918 * span(f, E.num.s, E.num.l, ease));
  const e54 = span(f, E.n54.s, E.n54.l + 6, out);
  const n54P = span(f, E.n54.s, E.n54.l, out);
  const sevenP = span(f, E.seven.s, E.seven.l, out);
  const shortArrow = span(f, E.shortlist.s, E.shortlist.l + 8, ease);

  /* 锁、钥匙 */
  const p1 = span(f, E.key.s, E.key.l, Easing.inOut(Easing.cubic));
  const p2 = span(f, E.tried.s, E.tried.l, Easing.inOut(Easing.cubic));
  const p3 = span(f, E.molecule.s, E.molecule.l, Easing.inOut(Easing.cubic));
  const turnout = span(f, E.sit.s, E.sit.l + 10);
  const kx = 700 + 130 * p1 + 156 * p2 + 18 * p3;
  const ky = 810 + (650 - 810) * p1 + (530 - 650) * p2 + 4 * p3 - Math.sin(Math.PI * p1) * 44;
  const krot = -15 * Math.sin(Math.PI * turnout);
  const pocketP = span(f, E.predicts.s, E.predicts.l + 6, out);
  const leaderP = span(f, E.pocket.s, E.pocket.l + 8, ease);
  const panelP = span(f, E.computer.s, E.computer.l + 10, ease);
  const barP = span(f, E.scores.s, E.scores.l + 18, out);
  const flash = f >= E.fit.s && f < E.fit.l + 34 ? 0.5 + 0.5 * Math.cos((f - E.fit.s) / 3) : 0;

  // 红珠：每个落点先到位、停 16 帧再走（静帧抽在落地后 12 帧，正好停在落点上）
  const PTS = [[0, 92, 188], [E.wall.l, 92, 188], [E.title.l, 92, 188], [E.num.l, 776, 236], [E.new.l, 776, 300], [E.designs.l, 340, 690],
               [E.many.l, 600, 690], [E.make.l, 480, 506], [E.lock.l, 700, 620], [E.key.l, 860, 740],
               [E.tried.l, 1280, 320], [E.vlock.l, 1300, 740], [E.docking.l, 1700, 250], [E.computer.l, 1360, 470],
               [E.predicts.l, 1330, 350], [E.molecule.l, 1300, 800], [E.sit.l, 1330, 620], [E.pocket.l, 860, 380],
               [E.scores.l, 1360, 520], [E.fit.l, 1360, 660], [E.similar.l, 800, 500], [E.grouped.l, 700, 540],
               [E.n54.l, 520, 700], [E.shortlist.l, 600, 500], [E.pick.l, 420, 846], [E.seven.l, 500, 856],
               [E.tomake.l, 1120, 800], [K.len_f, 1121, 801]];
  const bead = PTS.flatMap(([t, x, y], i) => (i === 0 || i === PTS.length - 1 ? [[t, x, y]] : [[t, x, y], [Math.min(t + 16, PTS[i + 1][0] - 1), x, y]]));

  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("4-10.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56, lineHeight: "64px"}}><Write p={span(f, E.title.s, E.title.e)}>Docking</Write></div>
      <div style={{position: "absolute", left: 1420, top: 78, fontSize: 24, fontStyle: "italic", color: SOFT}}>
        <Write p={span(f, E.title.l, E.title.l + 26)}>Tool: docking / virtual screening</Write></div>

      {/* 点阵墙：8,918 个新设计 */}
      <div style={{position: "absolute", left: 0, top: 0, opacity: wallOp}}>
        {DRAW.map((d) => {
          const k = (d.c + d.r) / (COLS + ROWS - 2);
          const a = span(wallP, 0.8 * k, 0.8 * k + 0.2);
          if (a <= 0) return null;
          const lit = span(f, E.num.s + d.r * 3.3, E.num.s + d.r * 3.3 + 9);
          const drift = span(f, E.similar.s + d.i * 0.13, E.similar.s + d.i * 0.13 + 26, ease);
          const bx = d.x + JX(d.i) * (1 - settle), by = d.y + JY(d.i) * (1 - settle);
          const x = bx + (d.tx - bx) * drift, y = by + (d.ty - by) * drift;
          const isShort = SHORT.has(d.i);
          const pick = SEVEN.has(d.i) ? span(f, E.pick.s, E.pick.l + 6, out) : 0;
          const sc = 1 + pop - 0.45 * e54 * (isShort ? 0 : 1) + 0.3 * pick;
          return (
            <div key={d.i} style={{position: "absolute", left: x - DOTR, top: y - DOTR - 14 * pick, width: DOTR * 2, height: DOTR * 2,
                                   borderRadius: DOTR, boxSizing: "border-box", border: `2px solid ${pick > 0.12 ? RED : INK}`,
                                   background: pick > 0.12 ? RED : ink(lit * (0.5 + 0.5 * settle)),
                                   opacity: a * (isShort ? 1 : 1 - 0.68 * e54),
                                   transform: `scale(${sc})`}} />
          );
        })}
      </div>

      {/* 波：一条带从上往下扫，扫过的点变实 */}
      {bandP > 0 && bandP < 1 && (
        <div style={{position: "absolute", left: 100, top: bandY - 34, width: 672, height: 34, background: ink(0.05)}} />
      )}
      {bandP > 0 && bandP < 1 && (
        <div style={{position: "absolute", left: 100, top: bandY, width: 672, height: 2.5, background: ink(0.6)}} />
      )}

      {/* 8 个虚线圈 + 短名单箭头 */}
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {CC.map(([cx, cy], i) => {
          const p = span(f, E.grouped.s + i * 2.4, E.grouped.l + i * 2.4, ease);
          return p <= 0 ? null : <circle key={i} cx={cx} cy={cy} r={62} fill="none" stroke={INK} strokeWidth={2} strokeDasharray="8 8" opacity={0.5 * p} />;
        })}
        {shortArrow > 0 && (
          <g stroke={INK} strokeWidth={3} fill="none" strokeLinecap="round" opacity={0.85}>
            <path d={`M604,478 C616,520 ${560 - 20 * shortArrow},540 ${514 - 2 * shortArrow},548`} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - shortArrow} />
            {shortArrow > 0.9 && <path d="M528,534 L510,549 L532,558" />}
          </g>
        )}
      </svg>

      {/* 漏斗：8,918 → 54 → 7 */}
      <Placeholder x={414} y={558} w={96} h={96} show={span(f, E.num.l, E.num.l + 14)} hide={span(f, E.n54.s, E.n54.l)} />
      <Placeholder x={612} y={558} w={58} h={96} show={span(f, E.shortlist.l, E.shortlist.l + 14)} hide={span(f, E.seven.s, E.seven.l)} />
      <div style={{position: "absolute", left: 108, top: 566, fontSize: 76, lineHeight: "84px", opacity: (f >= E.num.s ? 1 : 0) * (1 - 0.25 * dim1)}}>{comma(count)}</div>
      {n54P > 0 && <div style={{position: "absolute", left: 420, top: 566, fontSize: 76, lineHeight: "84px", opacity: n54P,
                                transform: `scale(${1.2 - 0.2 * n54P})`, transformOrigin: "0 0"}}>54</div>}
      {sevenP > 0 && <div style={{position: "absolute", left: 620, top: 566, fontSize: 76, lineHeight: "84px", opacity: sevenP,
                                  transform: `scale(${1.2 - 0.2 * sevenP})`, transformOrigin: "0 0"}}>7</div>}
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {n54P > 0 && (
          <g stroke={INK} strokeWidth={3} fill="none" strokeLinecap="round">
            <line x1={320} y1={608} x2={320 + 72 * n54P} y2={608} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - n54P} />
            {n54P > 0.9 && <path d="M384,600 L398,608 L384,616" />}
          </g>
        )}
        {sevenP > 0 && (
          <g stroke={INK} strokeWidth={3} fill="none" strokeLinecap="round">
            <line x1={520} y1={608} x2={520 + 72 * sevenP} y2={608} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - sevenP} />
            {sevenP > 0.9 && <path d="M584,600 L598,608 L584,616" />}
          </g>
        )}
      </svg>
      <Label x={108} y={656} w={220} size={24} align="left" p={span(f, E.designs.s, E.designs.l + 10)}>brand-new designs</Label>
      <Label x={420} y={656} w={180} size={24} align="left" p={span(f, E.shortlist.s, E.shortlist.l + 10)}>the shortlist</Label>
      <Label x={620} y={656} w={110} size={24} align="left" p={span(f, E.tomake.s, E.tomake.l + 10)}>to make</Label>

      <Pen x={114} y={490} p={span(f, E.make.s, E.make.l + 10)} size={40} rot={-4}>too many to make</Pen>

      {/* 7 把钥匙：重墨、粗线 */}
      {[...Array(7)].map((_, i) => {
        const p = span(f, E.seven.s + i * 2.6, E.seven.l + i * 2.6, ease);
        if (p <= 0) return null;
        return (
          <svg key={i} width={96} height={76} style={{position: "absolute", left: 112 + i * 96, top: 730}}>
            <g fill="none" stroke={INK} strokeWidth={6} strokeLinecap="round" strokeLinejoin="round">
              <circle cx={17} cy={34} r={12} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />
              <path d="M29,34 H84 M56,34 V50 M68,34 V46" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />
            </g>
          </svg>
        );
      })}

      {/* 右边先留空位，锁后到 */}
      <Placeholder x={955} y={255} w={300} h={429} show={span(f, E.designs.l, E.designs.l + 14)} hide={span(f, E.lock.s, E.lock.l)} />

      {/* 虚拟锁 */}
      <Part name="lock" cx={LKCX} cy={LKCY} w={LKW} at={E.lock.s} f={f} gate={[0.5, 1]} />

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {/* the pocket：指到锁孔的红圈 */}
        {leaderP > 0 && <path d={`M${936},448 L${936 + 134 * leaderP},${448 + 76 * leaderP}`} stroke={INK} strokeWidth={1.5} strokeDasharray="5 5" opacity={0.6 * leaderP} />}
        {pocketP > 0 && <circle cx={KHCX} cy={KHCY} r={34 + 10 * (1 - pocketP)} fill="none" stroke={RED} strokeWidth={3} strokeDasharray="7 5" opacity={pocketP} />}
        {/* 打分的框 */}
        {panelP > 0 && (
          <rect x={PX} y={PY} width={PW} height={PH} rx={10} fill="none" stroke={INK} strokeWidth={2.5}
                pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - panelP} />
        )}
        {BARS.map((v, i) => {
          const g = span(barP, i * 0.2, i * 0.2 + 0.6);
          if (g <= 0) return null;
          return (
            <g key={i}>
              <rect x={1424} y={470 + i * 60} width={362} height={24} fill="none" stroke={INK} strokeWidth={2} />
              <rect x={1424} y={470 + i * 60} width={362 * v * g} height={24} fill={RED} opacity={0.8 + 0.2 * flash} />
            </g>
          );
        })}
      </svg>

      {/* 钥匙：从设计堆飞进锁孔 */}
      {f >= E.key.s && (
        <div style={{position: "absolute", left: kx - KWW / 2, top: ky - KWH / 2, width: KWW, height: KWH,
                     transform: `rotate(${krot}deg)`, transformOrigin: `${KWW / 2}px ${KWH / 2}px`}}>
          <Part name="key" cx={KWW / 2} cy={KWH / 2} w={KWW} at={E.key.s} f={f} gate={[0.1, 0.5]} />
        </div>
      )}

      <Label x={1105} y={700} w={260} size={26} p={span(f, E.vlock.s, E.vlock.l + 10)}>a virtual lock</Label>
      <Label x={800} y={430} w={140} size={26} align="left" p={span(f, E.pocket.s, E.pocket.l + 10)}>the pocket</Label>
      <Label x={1400} y={250} w={270} size={30} align="left" p={span(f, E.docking.s, E.docking.l + 12)}>That's docking</Label>
      <Label x={1424} y={402} w={300} size={26} align="left" p={span(f, E.computer.s + 4, E.computer.l + 14)}>the computer predicts</Label>
      <Label x={1424} y={640} w={240} size={26} align="left" p={span(f, E.fit.s, E.fit.l + 14)}>scores the fit</Label>

      {/* 簇说明 */}
      <Label x={776} y={330} w={180} size={22} align="left" p={span(f, E.similar.s, E.similar.l + 12)}>similar designs</Label>
      <Label x={776} y={360} w={180} size={22} align="left" p={span(f, E.grouped.s, E.grouped.l + 12)}>get grouped</Label>

      <Source p={span(f, 2, 22)}>Ren et al., Chem. Sci. 2023; Lengauer 2007; Wang et al., Pharmaceuticals 2023 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual410" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
