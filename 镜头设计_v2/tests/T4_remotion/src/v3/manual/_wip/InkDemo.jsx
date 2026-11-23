// HKBU SCIE1007 课程作业的科普视频：v2「铜版说明书页」样板图版（合成 id InkDemo，1920×1080 一张静态）。
// 这张图不是某一段的分镜，是给导演看「v2 该长什么样」的印刷样板：
// 页眉 kicker + folio + 细线 / 手绘锁（主角）/ 圆形网点照片插图 / 3 条编号引注 + 右栏图例 /
// 底部刻度 + 红指针 / −6° 红印章 / 两行小字图注 / 页脚细线 + 出处行。
// 所有道具都从 ./inkkit.jsx 取；Part 与四个颜色从 ../kit.jsx 取（kit 只读）。
import React from "react";
import {AbsoluteFill, Composition, registerRoot, useCurrentFrame} from "remotion";
import {PAPER, INK, SOFT, RED, Part} from "../kit.jsx";
import {
  PaperFrame, Kick, Folio, Rule, Caption, CircNum, Leader, Scale, Stamp,
  InkLock, InkKey, InkTail, lockGeo, hatch, halftoneStyle, wobblyPath, wob, linePts, arcPts,
} from "./inkkit.jsx";

const FAR = -1e4; // 静帧样板：全部道具一开始就印好了

// 版面坐标（BRIEF §3）
const L = 96, R = 1820, TOP = 176, HEAD = 140, FOOT = 1008;
const V1 = 306, V2 = 1000; // 两条竖规矩线

const LOCK = {cx: 560, cy: 560, w: 470};
const G = lockGeo(LOCK.cx, LOCK.cy, LOCK.w);
const SHOULDER = -50 * (Math.PI / 180); // 锁梁右肩，第 1 条引注落点
const shoulderPt = [LOCK.cx + G.ro * Math.cos(SHOULDER), G.ay + G.ro * Math.sin(SHOULDER)];
const INSET = {cx: 1450, cy: 350, r: 150};
// 尾巴控制点：从锁梁右足 (690,455) 垂下来，横过锁孔 (560,671)，收在锁体左面
// 尾巴控制点：从锁梁右足 (676,470) 垂下来，荡过锁体右下，横过锁孔，平摊在锁体左面
const TAIL = [[676, 470], [772, 590], [690, 700], [462, 676]];

const LegendRow = ({n, text, y, f}) => (
  <>
    <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
      <CircNum n={n} x={1200} y={y + 16} f={f} at={FAR} />
      <Rule x1={1180} y1={y + 44} x2={1790} y2={y + 44} op={0.35} f={f} at={FAR} />
    </svg>
    <Caption x={1232} y={y + 3} size={22} caps={false} color={INK} track={0} width={420} f={f} at={FAR}>
      {text}
    </Caption>
  </>
);

const Scene = () => {
  const f = useCurrentFrame();

  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <PaperFrame />

      {/* ── 版面骨架 + 主角 ── */}
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <Rule x1={L} y1={HEAD} x2={R} y2={HEAD} f={f} at={FAR} />
        <Rule x1={L} y1={FOOT} x2={R} y2={FOOT} f={f} at={FAR} />
        <Rule x1={V1} y1={TOP} x2={V1} y2={940} op={0.3} f={f} at={FAR} />
        <Rule x1={V2} y1={TOP} x2={V2} y2={940} op={0.3} f={f} at={FAR} />

        {/* 主角：手绘锁 */}
        <InkLock cx={LOCK.cx} cy={LOCK.cy} w={LOCK.w} f={f} at={FAR} />

        {/* 软塌的尾巴：从锁梁右足垂下来，横过锁孔（2 条 15% 残影） */}
        <InkTail pts={TAIL} w={15} f={f} at={FAR} />

        {/* 插图引线：锁孔 → 照片插图边缘（1.2px 虚线） */}
        <Leader from={[G.kh.x + 24, G.kh.y - 32]} to={[1305, 368]} dash="7 7" op={0.42} dot={false} f={f} at={FAR} />

        {/* 3 条编号引注 */}
        <Leader from={shoulderPt} to={[726, 250]} f={f} at={FAR} />
        <CircNum n={1} x={742} y={236} f={f} at={FAR} />
        <Leader from={[G.br - 1, 602]} to={[896, 634]} f={f} at={FAR} />
        <CircNum n={2} x={914} y={648} f={f} at={FAR} />
        <Leader from={[G.kh.x + 8, G.kh.y + G.kh.r + 26]} to={[648, 810]} f={f} at={FAR} />
        <CircNum n={3} x={666} y={826} f={f} at={FAR} />

        {/* ATP 小方块（手绘框 + 一条引线指到锁孔） */}
        <path
          d={wobblyPath(wob(f, [
            ...linePts(410, 802, 530, 802, 9), ...linePts(530, 802, 530, 844, 4),
            ...linePts(530, 844, 410, 844, 9), ...linePts(410, 844, 410, 802, 4),
          ], 1.0), true)}
          fill="none" stroke={INK} strokeWidth={2.4} strokeLinejoin="round"
        />
        <Leader from={[466, 798]} to={[544, 744]} op={0.45} f={f} at={FAR} />

        {/* 底部刻度 + 红指针（红 1/3）；两端小字旁白里有才写 */}
        <Scale x={L} y={940} w={640} ticks={5} pointer={1} left="sure" right="less sure" f={f} at={FAR} />

        {/* 页脚出处行 */}
        <Caption x={L} y={1030} size={17} color={SOFT} track={1.2} width={900} f={f} at={FAR}>
          Ren et al., Chem. Sci. 2023 · Illustration (not to scale)
        </Caption>
      </svg>

      {/* ── 页眉 ── */}
      <Kick f={f} at={FAR}>Ch. 4 — binding and blocking</Kick>
      <Folio f={f} at={FAR}>Plate 4-03</Folio>

      {/* ── 标题 ── */}
      <div style={{position: "absolute", left: L, top: 166, fontFamily: "Serif", fontSize: 54, lineHeight: "58px", color: INK}}>
        the lock
      </div>
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <Rule x1={L} y1={240} x2={268} y2={240} op={0.4} f={f} at={FAR} />
      </svg>

      {/* ── 页边：竖排书名线 + ×1 ── */}
      <div style={{position: "absolute", left: 106, top: 690, fontFamily: "Serif", fontSize: 18, letterSpacing: 3, color: SOFT, transform: "rotate(-90deg)", transformOrigin: "0 0", whiteSpace: "nowrap"}}>
        SCIE1007 · CH. 4
      </div>
      <Caption x={L} y={890} size={18} color={SOFT} track={2} width={120} f={f} at={FAR}>×1</Caption>

      {/* ── 两行小字图注（FIG. 2 = 手绘锁） ── */}
      <Caption x={L} y={806} size={20} caps={false} italic color={INK} width={300} f={f} at={FAR}>
        FIG. 2 — the lock, hand-drawn
      </Caption>
      <Caption x={L} y={852} size={17} caps={false} color={SOFT} width={320} f={f} at={FAR}>
        Hatching marks the shadow side.
      </Caption>

      {/* ── ATP 方块里的字 ── */}
      <div style={{position: "absolute", left: 410, top: 809, width: 120, textAlign: "center", fontFamily: "Serif", fontSize: 22, letterSpacing: 2, color: INK}}>ATP</div>

      {/* ── 右栏图例 ── */}
      <Caption x={1180} y={560} size={28} color={SOFT} track={2} width={480} f={f} at={FAR}>Key to the figure</Caption>
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <Rule x1={1000} y1={604} x2={1660} y2={604} op={0.45} f={f} at={FAR} />
      </svg>
      <LegendRow n={1} text="one end" y={626} f={f} />
      <LegendRow n={2} text="a floppy tail" y={698} f={f} />
      <LegendRow n={3} text="the ATP pocket" y={770} f={f} />

      {/* ── 照片插图：圆窗 + Part + 网点 ── */}
      <div
        style={{
          position: "absolute", left: INSET.cx - INSET.r, top: INSET.cy - INSET.r, width: INSET.r * 2, height: INSET.r * 2,
          borderRadius: "50%", border: `4px solid ${INK}`, boxSizing: "border-box", overflow: "hidden", background: PAPER,
        }}
      >
        <div style={{position: "absolute", inset: 4, borderRadius: "50%", overflow: "hidden", background: PAPER}}>
          <div style={{position: "absolute", inset: 0, filter: "grayscale(0.88) contrast(1.05) brightness(1.06)"}}>
            <Part name="lock" cx={INSET.r} cy={INSET.r - 4} w={232} at={FAR} f={f} />
          </div>
          <div style={halftoneStyle(3.6, 0.9, 0.28)} />
          <div style={{position: "absolute", inset: 0, background: PAPER, opacity: 0.2, mixBlendMode: "multiply"}} />
        </div>
      </div>

      {/* 插图：手绘圆环 + 四向定位刺（压在圆窗上） */}
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <path d={wobblyPath(wob(f, arcPts(INSET.cx, INSET.cy, INSET.r + 5, 0, Math.PI * 2, 60), 1.0), true)}
              fill="none" stroke={INK} strokeWidth={3} />
        {[0, 90, 180, 270].map((a, i) => {
          const r0 = INSET.r + 11, r1 = INSET.r + 23, t = (a * Math.PI) / 180;
          return <line key={i} x1={INSET.cx + Math.cos(t) * r0} y1={INSET.cy + Math.sin(t) * r0}
                       x2={INSET.cx + Math.cos(t) * r1} y2={INSET.cy + Math.sin(t) * r1} stroke={INK} strokeWidth={1.6} opacity={0.55} />;
        })}
      </svg>

      {/* 插图图注 */}
      <Caption x={INSET.cx} y={514} size={20} caps={false} italic color={SOFT} align="center" width={520} f={f} at={FAR}>
        FIG. 1 — the model
      </Caption>

      {/* ── 印章（红 2/3，带缺墨）── */}
      <Stamp x={1180} y={878} f={f} at={FAR}>Blocked</Stamp>

      {/* ── 右下：三把手绘钥匙，中间一把打红杠（红 3/3）── */}
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <InkKey cx={1490} cy={892} w={112} rot={-4} f={f} at={FAR} />
        <InkKey cx={1615} cy={892} w={112} rot={-7} f={f} at={FAR} />
        <InkKey cx={1740} cy={892} w={112} rot={-2} f={f} at={FAR} />
        <path d={wobblyPath(wob(f, linePts(1556, 906, 1672, 876, 9), 1.0))} fill="none" stroke={RED} strokeWidth={4} strokeLinecap="round" opacity={0.95} />
      </svg>
      <Caption x={1434} y={930} size={17} caps={false} color={SOFT} width={260} f={f} at={FAR}>
        FIG. 3 — three keys
      </Caption>
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="InkDemo" component={Scene} durationInFrames={120} fps={60} width={1920} height={1080} />;
registerRoot(Root);
