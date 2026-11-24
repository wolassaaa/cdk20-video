// HKBU SCIE1007 课程作业的科普视频：B 档 3-05（D 画外音）"Why this lock?"
// CDK20 插座落位 + 红色问号；插座让到左边，香港地图滑进来（Hong Kong team）；
// 样本盘 52 个孔，36 个变蓝（计数停在 36，刻 of 52）；玻璃肝；肿瘤 / 旁边正常组织两根条，肿瘤高；
// 两块牌子从料杆上弹下：later-stage tumours、shorter survival；
// 最后小插座的旋钮往下拧，右边肝癌细胞的分裂节拍从 60 帧变 120 帧（插座灯一直亮：是调低，不是药堵住）。
// 接点：开头 T5 插座擦除（3-04 是 A 段插座），结尾 T5 料杆擦除（3-06 出镜段段首是料杆）。L0 第 3 区大板。
// 数字照旁白：36、52。出处 Feng et al., J. Clin. Invest. 2011（香港大学团队）。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import {gsap} from "gsap";
import K from "./keys_3-05.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Tag, shade, tint, camBreath, Stage, Sprite, Slab, Gate, Runner, Label, Pen, Source, Counter, Dial, Engrave, evMapB, T5In, T5Out} from "./bkit.jsx";
import {useGsapTimeline, idle, RULE} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 3;
const backOut = gsap.parseEase(RULE.landEase);

// ---- 样本盘：13 × 4 个孔，变蓝的 36 个按固定乱序
const TRAY = {x: 362, y: 353, w: 1100, h: 420};
const WELL = 65, PITCH = 82;
const ORDER = [...Array(52).keys()].sort((a, b) => ((a * 37) % 52) - ((b * 37) % 52));
const RANK = Object.fromEntries(ORDER.map((d, k) => [d, k]));
// ---- 两根条（肿瘤 / 旁边正常组织）
const BAR = {base: 640, w: 110, xs: [1530, 1710], tall: 290, short: 120};
// ---- 牌子
const PLQ = [{x: 600, w: 410, text: "later-stage tumours"}, {x: 1050, w: 350, text: "shorter survival"}];
const PLQ_Y = 724;
// ---- 第五句：分裂的细胞（中心）和芽
// 两组对照（Gemini 初审 11-20：只画一组，分裂反而像在长得快）：上面一组 CDK20 照常，45 帧分一次；下面一组 CDK20 调低，down 之后 150 帧才分一次
const CELL_U = [1300, 410], CELL_D = [1300, 730];
const BUDS = [[-210, -120], [190, -150], [230, 110], [-220, 120], [10, 210], [-40, -210], [300, -20], [-300, 0]].map(([x, y]) => [x * 0.55, y * 0.55]);
const BEAT_U = 45, BEAT_D0 = 45, BEAT_D1 = 360;   // 调低以后几乎不再分裂（Gemini 二审：两组差太少）

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.land("sock", 0, 1, E.sock.l + 6, {antic: false});
    X.tw("rem", 0, 1, E.rem.s, E.rem.l + 18, "power3.inOut");
    X.land("hk", 0, 1, E.hk.l);
    X.tw("out1", 0, 1, E.tray.s - 6, E.tray.l + 8, "power3.in");
    X.land("tray", 0, 1, E.tray.l);
    X.count("n36", 0, 36, E.n36.l, 34);
    X.tw("of52", 0, 1, E.of52.s, E.of52.l + 6, "power2.out");
    X.land("liver", 0, 1, E.liver.l);
    X.tw("bars", 0, 1, E.hi.s - 30, E.hi.s, "power2.out");
    X.tw("hi", 0, 1, E.hi.s, E.hi.l, "power3.out");
    X.tw("near", 0, 1, E.near.s, E.near.l + 10, "power3.out");
    X.jiggle("highJ", E.high.l - 4, 5, 0);
    X.tw("glow", 0, 1, E.high.s, E.high.l + 8, "power2.out");
    X.tw("glow", 1, 0, E.high.e, E.high.e + 30, "power2.inOut");
    X.tw("feed", 0, 1, E.late.s - 30, E.late.s, "power2.inOut");
    X.land("p0", 0, 1, E.late.l);
    X.land("p1", 0, 1, E.surv.l);
    X.jiggle("p0J", E.late.l, 3);
    X.jiggle("p1J", E.surv.l, 3);
    X.tw("cmp", 0, 1, E.near.l + 6, E.near.e - 4, "power1.inOut");
    X.tw("tum", 0, 1, E.late.s, E.late.e, "power2.out");
    X.tw("shorten", 0, 1, E.surv.l, E.surv.e, "power2.inOut");
    X.tw("clear", 0, 1, E.clear.s, E.knob.s + 4, "power2.in");
    X.land("knob", 0, 1, E.knob.l);
    X.tw("turn", 0, 1, E.down.s, E.down.l, "power2.inOut");
    X.jiggle("turnJ", E.down.l, 3);
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const mix = (a, b, t) => a + (b - a) * t;

  // 插座：中间 → 左边 → 往左出去
  const sockX = mix(960, 400, S.rem) - 900 * S.out1 * S.out1;
  const sockW = mix(620, 430, S.rem);
  const sockY = mix(480, 500, S.rem) + id(1).y + (1 - Math.min(1, S.sock)) * 40;
  const hkX = mix(2300, 1250, S.hk) - 1300 * S.out1 * S.out1;
  const trayDX = (1 - S.tray) * 1300;
  const clearX = -2200 * S.clear * S.clear;
  const trayGone = Math.max(0, Math.min(1, (f - E.high.s) / Math.max(1, E.high.l + 20 - E.high.s)));   // P30：托盘和计数器从 high 起淡出

  // 第五句：两组细胞。上：一直 45 帧一拍；下：down 落定之前 45 帧，之后 150 帧
  const t0 = E.knob.s, td = E.down.l;
  const grp = (slow) => {
    const ph = (g) => g < t0 ? 0 : !slow || g < td ? (g - t0) / BEAT_U : (td - t0) / BEAT_D0 + (g - td) / BEAT_D1;
    const phase = ph(f), fr = phase - Math.floor(phase);
    const pulse = f < t0 ? 0 : Math.pow(Math.sin(Math.PI * fr), 6);
    const nBud = Math.min(BUDS.length, Math.floor(phase));
    const pre = (td - t0) / BEAT_D0;
    const budAt = (i) => { const p = i + 1; return !slow ? t0 + p * BEAT_U : p <= pre ? t0 + p * BEAT_D0 : td + (p - pre) * BEAT_D1; };
    return {pulse, nBud, budAt};
  };
  const GU = grp(false), GD = grp(true);

  const wells = [...Array(52)].map((_, i) => {
    const c = i % 13, r = Math.floor(i / 13);
    const blue = RANK[i] < 36 ? Math.max(0, Math.min(1, S.n36 - RANK[i])) : 0;
    return {x: TRAY.x + 32 + c * PITCH, y: TRAY.y + 26 + r * PITCH, blue, grey: RANK[i] >= 36};
  });

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, ["s1", "s3", "s4"])} over={<><T5In name="socket_bore" f={f} /><T5Out name="runner" f={f} len={LEN} /></>}>
        <Layer id="sock">
          {S.sock > 0.01 && S.out1 < 1 && <Sprite name="socket/hero_34" hero x={sockX} y={sockY} w={sockW} op={Math.min(1, S.sock * 1.5)} rot={id(1).r}
                                                sx={0.85 + 0.15 * S.sock} sy={0.85 + 0.15 * S.sock} />}
        </Layer>
        <Layer id="hk">
          {S.hk > 0.001 && S.out1 < 1 && <Sprite name="hkmap/34" x={hkX} y={470 + id(2).y} w={700} rot={id(2).r * 0.5} />}
        </Layer>

        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${clearX}px)`}}>
          <Layer id="tray">
            {S.tray > 0.001 && (
              <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${trayDX}px)`, opacity: 1 - trayGone}}>
                <Slab x={TRAY.x} y={TRAY.y} w={TRAY.w} h={TRAY.h} r={22} color={C.bone} depth={10} sheen={S.tray < 1 ? S.tray : -1} id="tray" />
                <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
                  {wells.map((w, i) => (
                    <g key={i}>
                      <rect x={w.x} y={w.y} width={WELL} height={WELL} rx={12} fill="#000" opacity={0.10} transform="translate(1.5,2)" />
                      <rect x={w.x} y={w.y} width={WELL} height={WELL} rx={12} fill={C.table} />
                      {w.blue > 0 && <rect x={w.x + 3} y={w.y + 3} width={WELL - 6} height={WELL - 6} rx={10} fill={C.blue} opacity={w.blue} />}
                      {w.blue > 0 && <rect x={w.x + 8} y={w.y + 6} width={14} height={4} rx={2} fill="#fff" opacity={0.45 * w.blue} />}
                      {w.grey && S.of52 > 0 && <rect x={w.x + 3} y={w.y + 3} width={WELL - 6} height={WELL - 6} rx={10} fill={C.grey}
                                                      opacity={0.55 * S.of52 * (1 - 0.6 * Math.max(0, Math.min(1, (f - E.of52.l - 10) / 30)))} />}
                    </g>
                  ))}
                </svg>
              </div>
            )}
          </Layer>
          <Layer id="liver">
            {S.liver > 0.01 && <Sprite name="liver/34" x={225} y={600 + id(3).y} w={270} op={Math.min(1, S.liver * 1.5)} sx={0.8 + 0.2 * S.liver} sy={0.8 + 0.2 * S.liver} rot={id(3).r} />}
          </Layer>
          <Layer id="bars">
            {S.bars > 0.01 && (
              <div style={{position: "absolute", left: 0, top: 0, opacity: S.bars}}>
                {BAR.xs.map((x, i) => {
                  const h = i === 0 ? 40 + (BAR.tall - 40) * S.hi : 40 + (BAR.short - 40) * S.near;
                  return (
                    <React.Fragment key={i}>
                      <Slab x={x-BAR.w/2-19} y={BAR.base-320} w={BAR.w+38} h={320} r={57} color={C.bone} depth={10} id={`tube${i}`}/>
                      <Slab x={x - BAR.w / 2} y={BAR.base - h - (i === 0 ? S.highJ : 0)} w={BAR.w} h={h} r={34} color={C.blue} depth={8}
                            sheen={i === 0 ? (S.hi < 1 ? S.hi : S.glow > 0 ? S.glow : -1) : S.near < 1 ? S.near : -1} id={`bar${i}`} />
                      <Slab x={x - 85} y={BAR.base + 14} w={170} h={58} r={12} color={C.bone} depth={6} id={`base${i}`}>
                        <div style={{width: 170, height: 58, display: "flex", alignItems: "center", justifyContent: "center"}}>
                          <Engrave size={34}>{i === 0 ? "tumour" : "non-tumour"}</Engrave>
                        </div>
                      </Slab>
                    </React.Fragment>
                  );
                })}
              </div>
            )}
          </Layer>
          <Layer id="cmp">
            {S.cmp > 0.01 && (
              <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
                <path d={`M${BAR.xs[1] - 70},${BAR.base - BAR.short} L${BAR.xs[1] - 70},${BAR.base - BAR.tall}`} fill="none" stroke={C.ink} strokeWidth={4} strokeLinecap="round"
                      pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - S.cmp} />
                <path d={`M${BAR.xs[1] - 84},${BAR.base - BAR.tall + 16} L${BAR.xs[1] - 70},${BAR.base - BAR.tall} L${BAR.xs[1] - 56},${BAR.base - BAR.tall + 16}`} fill="none" stroke={C.ink}
                      strokeWidth={4} strokeLinecap="round" strokeLinejoin="round" opacity={S.cmp > 0.95 ? 1 : 0} />
                <path d={`M${BAR.xs[0] + BAR.w / 2 + 6},${BAR.base - BAR.tall} L${BAR.xs[1] - 50},${BAR.base - BAR.tall}`} stroke={C.ink} strokeWidth={2.5} strokeDasharray="8 8" opacity={0.7 * S.cmp} />
              </svg>
            )}
          </Layer>
          <Layer id="stage">
            {/* later-stage tumours：肝上一块红色肿瘤长大；shorter survival：一根生存时间条从长缩短 */}
            {S.p0 > 0.01 && (
              <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: id(3).y, overflow: "visible"}}>
                <defs>
                  <radialGradient id="tum" cx="0.38" cy="0.34" r="0.7"><stop offset="0" stopColor={tint(C.red, 0.3)} /><stop offset="0.6" stopColor={C.red} /><stop offset="1" stopColor={shade(C.red, 0.4)} /></radialGradient>
                </defs>
                <ellipse cx={209.4} cy={574} rx={(22 + 46 * S.tum) * 0.519} ry={(18 + 36 * S.tum) * 0.519} fill="url(#tum)" opacity={0.92 * Math.min(1, S.p0 * 2)} />
                <ellipse cx={203.2} cy={566.8} rx={(22 + 46 * S.tum) * 0.3 * 0.519} ry={(18 + 36 * S.tum) * 0.22 * 0.519} fill="#fff" opacity={0.5 * Math.min(1, S.p0 * 2)} />
              </svg>
            )}
            {/* 生存时间两根条对比（Gemini 二审：一根条看不出意思）：灰 = CDK20 低的病人，蓝 = CDK20 高的病人，蓝条缩短 */}
            {S.p1 > 0.01 && (
              <>
                <Slab x={PLQ[1].x} y={PLQ_Y + 66} w={PLQ[1].w} h={24} r={12} color={C.grey} depth={6} op={Math.min(1, S.p1 * 2)} id="survlow" />
                <Slab x={PLQ[1].x} y={PLQ_Y + 106} w={PLQ[1].w * (1 - 0.55 * S.shorten)} h={24} r={12} color={C.blue} depth={6} op={Math.min(1, S.p1 * 2)} id="survbar" />
                <Tag x={PLQ[1].x + PLQ[1].w + 16} y={PLQ_Y + 58} align="left" op={Math.min(1, S.p1 * 2)}>low CDK20</Tag>
                <Tag x={PLQ[1].x + PLQ[1].w * (1 - 0.55 * S.shorten) + 16} y={PLQ_Y + 98} align="left" op={Math.min(1, S.p1 * 2)}>high CDK20</Tag>
              </>
            )}
          </Layer>
          <Layer id="plaques">
            {S.feed > 0.001 && <Runner d={`M${BAR.xs[0]},${BAR.base + 80} C${BAR.xs[0]},${PLQ_Y + 40} 1460,${PLQ_Y + 40} 1410,${PLQ_Y + 40} L600,${PLQ_Y + 40}`} draw={S.feed} width={14} />}
            {PLQ.map((p, i) => {
              const a = S[`p${i}`];
              return (
                <React.Fragment key={i}>
                  {S.feed > 0.5 && <Gate x1={p.x + p.w / 2} y1={PLQ_Y + 40} x2={p.x + p.w / 2} y2={PLQ_Y + 40 - 26 * Math.min(1, a)} w={10} broken={Math.min(1, a)} />}
                  {a > 0.01 && <Slab x={p.x} y={PLQ_Y - 70 * (1 - a) + (S[`p${i}J`] || 0) - 58} w={p.w} h={78} r={16} color={C.bone} depth={9} sheen={a < 1 ? a : -1}
                                     op={Math.min(1, a * 2)} id={`plq${i}`} />}
                </React.Fragment>
              );
            })}
          </Layer>
        </div>

        {/* 第五句：小插座 + 旋钮，右边肝癌细胞 */}
        <Layer id="knob">
          {S.knob > 0.01 && (
            <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: Math.min(1, S.knob * 1.5), transform: `translateX(${(1 - S.knob) * -200}px)`}}>
              <Runner d="M470,520 L470,610" width={14} />
              <Sprite name="mini/m34_on" x={470} y={380 + id(5).y} w={330} rot={id(5).r} />
              <Runner d={`M590,${CELL_D[1]} L1080,${CELL_D[1]}`} width={12} draw={Math.min(1, S.turn * 1.4)} />
              <Dial cx={470} cy={CELL_D[1]} r={120} ticks={[[-70, null, true], [-35, null], [0, null, true], [35, null], [70, null, true]]}
                    needle={62 - 124 * S.turn + S.turnJ} label="CDK20" sheen={S.turn > 0 && S.turn < 1 ? S.turn : -1} />
            </div>
          )}
        </Layer>
        <Layer id="cells">
          {S.knob > 0.01 && (
            <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: Math.min(1, S.knob * 1.5), transform: `translateX(${(1 - S.knob) * 200}px)`}}>
              {[[GU, CELL_U, 0], [GD, CELL_D, 1]].map(([G, CC, k]) => (
                <React.Fragment key={k}>
                  {BUDS.slice(0, G.nBud).map(([bx, by], i) => {
                    const u = Math.max(0, Math.min(1, (f - G.budAt(i)) / RULE.land));
                    const s = backOut(u);
                    return <Sprite key={i} name="cell/34" x={CC[0] + bx * s} y={CC[1] + by * s + id(10 + i + 10 * k).y} w={100 * Math.max(0.05, s)} rot={id(10 + i + 10 * k).r * 3} />;
                  })}
                  <Sprite name="cell/34" x={CC[0]} y={CC[1] + id(6 + k).y} w={190} sx={1 + 0.06 * G.pulse} sy={1 + 0.06 * G.pulse} rot={id(6 + k).r} />
                </React.Fragment>
              ))}
              {/* 两组各挂一块题注（Gemini 二审：上面那块小表看不出是对照组） */}
              <Tag x={CELL_U[0] + 230} y={CELL_U[1] - 20} align="left">CDK20 normal</Tag>
              <Tag x={CELL_D[0] + 230} y={CELL_D[1] - 20} align="left" op={Math.min(1, S.turn * 2)}>CDK20 turned down</Tag>
            </div>
          )}
        </Layer>

        <Layer id="txt" exempt>
          <Pen text="?" x={1240} y={110} at={E.q.l - 16} out={E.rem.s} size={240} color={C.red} rot={8} dur={32} />
          <Label text="Hong Kong, 2011" size={56} x={hkX} y={750} at={E.hk.l + 6} out={E.tray.s - 4} align="center" />
          <div style={{position: "absolute", left: TRAY.x + trayDX + clearX, top: 262, display: "flex", alignItems: "baseline", opacity: S.tray > 0.01 ? 1 - trayGone : 0}}>
            <Counter value={S.n36} digits={2} size={110} x={0} y={0} />
            <div style={{position: "absolute", left: 128, top: 46, opacity: S.of52, transform: `translateY(${(1 - S.of52) * 12}px)`}}><Engrave size={64}>of 52</Engrave></div>
          </div>
          {PLQ.map((p, i) => (
            <div key={i} style={{position: "absolute", left: clearX, top: (S[`p${i}J`] || 0) - 70 * (1 - Math.min(1, S[`p${i}`]))}}>
              <Label text={p.text} x={p.x + p.w / 2} y={PLQ_Y - 53} at={i === 0 ? E.late.l : E.surv.l} align="center" out={E.clear.s} />
            </div>
          ))}
          <Label text="liver cancer cells" size={56} x={CELL_U[0]} y={182} at={E.cellsL.l} align="center" />
          <Label text="CDK20 level" size={52} x={(BAR.xs[0] + BAR.xs[1]) / 2} y={230} at={E.hi.l} out={E.clear.s} align="center" />
          <Pen text="slowed" x={1530} y={790} at={E.slow.l} size={84} />
          <Source>Illustration · data: Feng et al., J. Clin. Invest. 2011</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B305" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
