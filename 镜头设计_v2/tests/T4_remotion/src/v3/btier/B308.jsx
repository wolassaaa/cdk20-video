// HKBU SCIE1007 课程作业的科普视频：B 档 3-08（画外音）"But here's the problem. To design a key, you need to see the lock…"
// the problem：手写；To design a key：空插头落位（尖朝右）；see the lock：右边插座出现，磨砂看不清；no one had measured：插座更虚；CDK20's shape：红问号；
// That takes：插头、插座、问号往右退场；hard lab work：烧瓶和样本管落下，work 时烧瓶晃；only a small fraction：四十台磨砂小插座铺开；proteins：标签；
// have ever been measured：其中三台变清楚、灯亮，手写 measured；
// Without a 3D shape：清场，磨砂插座回来；computer predictions：一块黑芯片（不带牌子，标 computer）；of binding：插头去试，对不准，滑开；
// expensive：钞票；slow：日历；difficult：红问号 + 手写。
// 接点：开头 T2 从右甩进（3-07 是 B 页），结尾 T5 料杆擦除（3-09 出镜段）。L0 第 3 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_3-08.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Plate, Tag, camBreath, Stage, Sprite, Slab, Label, Pen, Engrave, Source, anchorOf, frost, evMapB, T5Out, whipX, impact} from "./bkit.jsx";
import {useGsapTimeline, idle, RULE} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 3;

const PLUG = {x: 480, y: 560, w: 300};
const SOCK = {x: 1360, y: 520, w: 620};
const [mdx, mdy] = anchorOf("socket/hero_34", "mouth", SOCK.w);
const [tipOX, tipOY] = anchorOf("plug/blank_34", "tip", PLUG.w);   // 翻过来以后尖在 (x − tipOX, y + tipOY)
const FLASK = {x: 760, y: 500, w: 380};
const TUBE = {x: 1160, y: 580, w: 440};
const COLS = 6, ROWS = 2;
const GRID = [...Array(COLS * ROWS)].map((_, i) => ({x: 410 + (i % COLS) * 221, y: 410 + Math.floor(i / COLS) * 211}));
const CLEAR = [3];   // P37：只有第 4 格是空的
const MINI_W = 143;
// 第 5 句：插座在右，芯片左上，插头在左
const SOCK2 = {x: 1380, y: 500, w: 600};
const [m2x, m2y] = anchorOf("socket/hero_34", "mouth", SOCK2.w);
const MOUTH2 = [SOCK2.x + m2x, SOCK2.y + m2y];
const PLUG2 = {x: 520, y: 640};

const mix = (a, b, t) => a + (b - a) * t;

const LabScene = ({x,y,a,scatter=0}) => !a ? null : <div style={{position:"absolute",left:0,top:0,opacity:a,transform:`translateY(${45*(1-a)}px)`}}>
  <Slab x={x-310} y={y+100} w={690} h={104} r={18} depth={14} id="measureDock"/>
  <Sprite name="dish/34" x={x-156} y={y+56} w={250}/>
  <Slab x={x+110} y={y-172} w={245} h={256} r={22} depth={13} id="diffraction">
    <svg width={245} height={256} style={{position:"absolute"}}>
      {Array.from({length:28},(_,i)=>{
        const t=i*2.39996, rd=33+(i%5)*12+scatter*((i*31)%19);
        return <circle key={i} cx={122+rd*Math.cos(t)} cy={128+rd*Math.sin(t)} r={4+i%3} fill={C.blue} opacity={.38+(i%7)*.075}/>;
      })}
    </svg>
  </Slab>
  <svg width={1920} height={1080} style={{position:"absolute",inset:0}}><path d={`M${x-140} ${y+43}L${x+111} ${y-36}`} stroke={C.blueHi} strokeWidth={5} opacity={.45+.35*Math.sin(scatter*3)}/></svg>
</div>;

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.land("plug", 0, 1, E.key.l, {antic: false});
    X.land("sock", 0, 1, E.lock.l, {antic: false});
    X.tw("blur", 0.5, 1, E.nobody.s - 4, E.nobody.e, "power2.out");
    X.tw("out1", 0, 1, E.takes.s - 6, E.takes.l + 20, "power2.in");
    X.land("flask", 0, 1, E.lab.l, {antic: false});
    X.land("tube", 0, 1, E.lab.l + 8, {antic: false});
    X.tw("work", 0, 1, E.work.s, E.work.e + 40, "none");
    X.tw("out2", 0, 1, E.grid.s - 8, E.grid.l + 10, "power3.in");
    X.group(GRID.map((_, i) => `g${i}`), 0, 1, E.grid.l, {step: 2, antic: false});
    X.tw("clr", 0, 1, E.meas.s, E.meas.l + 10, "power2.out");
    X.tw("out3", 0, 1, E.noshape.s - 8, E.noshape.l + 10, "power3.in");
    X.land("sock2", 0, 1, E.noshape.l + 6, {antic: false});
    X.land("plug2", 0, 1, E.noshape.l + 16, {antic: false});
    X.land("chip", 0, 1, E.comp.l, {antic: false});
    X.tw("try", 0, 1, E.bind.s, E.bind.l, "power2.in");
    X.tw("slip", 0, 1, E.bind.l, E.bind.e, "power2.out");
    X.tw("shrink", 0, 1, E.exp.s - 8, E.exp.l + 10, "power2.inOut");
    X.land("bill", 0, 1, E.exp.l + 4, {antic: false});
    X.land("cal", 0, 1, E.slow.l, {antic: false});
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const whip = f < 7 ? whipX(f, 0, "in", -1) : 0;
  const o1 = 2200 * S.out1, o2 = -2200 * S.out2, o3 = -2200 * S.out3;
  const shake = impact(f, E.bind.l);
  // 第 5 句收到左边、缩小，给 expensive / slow / difficult 让位
  const g5 = {s: mix(1, 0.62, S.shrink), x: mix(0, -330, S.shrink), y: mix(0, 40, S.shrink)};

  // 插头试插：尖从起点去插孔，差一点，碰到边沿滑下去
  const tip0 = [PLUG2.x - tipOX, PLUG2.y + tipOY];
  const miss = [MOUTH2[0] - 40, MOUTH2[1] + 70];
  const trial = Math.max(0, Math.min(60, f - E.bind.l + 40));
  const reach = trial < 60 ? Math.sin(Math.PI*(trial%20)/20) : 0;
  const tipX = mix(tip0[0], miss[0]-18, reach);
  const tipY = mix(tip0[1], miss[1] + 43*(Math.floor(trial/20)-1), reach) + 14*[E.exp,E.slow,E.diff].filter(e=>f>=e.l).length;
  const pRot = 20 * S.slip;

  return (
    <Lens plan={GP} f={f}>
      <Stage zoom={1+.10*Math.max(0,Math.min(1,(f-E.lock.s)/29))*(1-S.out1)} zoomAt={[1360,520]} zone={ZONE} f={f} cam={camBreath(f, K, [])} whip={whip} shakeX={shake} over={<T5Out name="runner" f={f} len={LEN} />}>
        {/* 第 1–3 句：插头和磨砂插座 */}
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${o1}px)`}}>
          <Layer id="plug">
            {S.plug > 0.01 && S.out1 < 1 && <Sprite name="plug/048_34" x={PLUG.x} y={PLUG.y - 40 * (1 - Math.min(1, S.plug)) + id(1).y} w={PLUG.w} sx={-1} op={Math.min(1, S.plug * 1.5)} rot={id(1).r} />}
          </Layer>
          <Layer id="socket">
            {S.sock > 0.01 && S.out1 < 1 && (
              <Sprite name="socket/hero_34" x={SOCK.x} y={SOCK.y - 40 * (1 - Math.min(1, S.sock)) + id(2).y} w={SOCK.w * (1 - 0.05 * (S.blur - 0.5))}
                      op={Math.min(1, S.sock * 1.5)} style={frost(S.blur)} />
            )}
          </Layer>
          <Layer id="txt1" exempt>
            <Pen text="the problem" x={760} y={150} at={E.prob.s - 6} out={E.key.s} size={92} />
            <Pen text="?" x={SOCK.x + mdx + 90} y={SOCK.y + mdy - 330} at={E.q.s - 8} dur={30} size={200} color={C.red} rot={6} />
          </Layer>
        </div>

        {/* 第 4 句：实验室，再是四十台小插座 */}
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${o2}px)`}}>
          <Layer id="lab">
            <LabScene x={883} y={495} a={S.flask} scatter={S.work}/>
          </Layer>
        </div>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${o3}px)`}}>
          <Layer id="grid">
            {GRID.map((g, i) => {
              const a = S[`g${i}`];
              if (a <= 0.01) return null;
              const on = CLEAR.includes(i) ? S.clr : 0;
              const y = g.y - 30 * (1 - Math.min(1, a)) + id(10 + i).y;
              return (
                <React.Fragment key={i}>
                  <Sprite name="mini/mface_off" x={g.x} y={y} w={MINI_W} op={Math.min(1, a * 1.5) * (1 - on)} style={frost(1 - on)} shadow={on < 0.5} />
                  {on > 0.01 && <Sprite name="mini/mface_on" x={g.x} y={y - 6 * on} w={MINI_W} op={on} lift={6 * on} />}
                </React.Fragment>
              );
            })}
          </Layer>
          <Layer id="txt4" exempt>
            <Label text="proteins" size={56} x={960} y={790} at={E.prot.l} align="center" />
            {f>=E.meas.s && <Tag x={1620} y={715} align="left" op={Math.min(1,(f-E.meas.s)/12)*(1-S.out3)}>not to scale</Tag>}
            <Pen text="measured" x={1440} y={250} at={E.meas.s} size={72} />
          </Layer>
        </div>

        {/* 第 5 句 */}
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translate(${g5.x}px, ${g5.y}px) scale(${g5.s})`, transformOrigin: "0px 540px"}}>
          <Layer id="socket">
            {S.sock2 > 0.01 && <Sprite name="socket/hero_34" x={SOCK2.x} y={SOCK2.y - 40 * (1 - Math.min(1, S.sock2)) + id(5).y} w={SOCK2.w} op={Math.min(1, S.sock2 * 1.5)} style={frost(0.85)} />}
          </Layer>
          <Layer id="chip">
            {S.plug2 > 0.01 && <Sprite name="plug/048_34" x={tipX + tipOX} y={tipY - tipOY - 40 * (1 - Math.min(1, S.plug2)) + id(7).y} w={PLUG.w} sx={-1} rot={pRot + id(7).r}
                                       op={Math.min(1, S.plug2 * 1.5) * (1 - Math.max(0, Math.min(1, (f - E.bind.e) / 12)))} lift={20 * Math.sin(Math.PI * S.try)} />}
          </Layer>
        </div>

        <Layer id="cost">
        </Layer>
        <Layer id="txt5" exempt>
          <Label text="hard lab work" size={52} x={960} y={760} at={E.lab.l} out={E.grid.s} align="center" />
          {[[E.exp,"expensive"],[E.slow,"slow"],[E.diff,"difficult"]].map(([e,t],i)=>{
            const a=Math.max(0,Math.min(1,(f-e.s)/Math.max(1,e.l-e.s)));
            return a>0 && <Plate key={t} x={795+i*305} y={198-58*(1-a)} w={276} h={108} text={t} size={51} op={a} id={t}/>;
          })}
          <Source>Illustration · data: Wang et al., Pharmaceuticals 2023; Ren et al., Chem. Sci. 2023</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B308" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
