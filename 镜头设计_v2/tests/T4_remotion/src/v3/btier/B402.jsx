// HKBU SCIE1007 课程作业的科普视频：B 档 4-02（B 画外音）"Before, you'd need a lab-measured structure. Now? The team just downloaded a prediction…"
// 左栏 Before：you'd need：日历落下（一直翻页）；lab-measured：烧瓶落下，下面的进度条开始很慢地爬；structure：标 lab-measured structure；
// 右栏 Now?：数据架落下，手写 Now?；downloaded a prediction：从数据架里抽出一张预测模型卡，右边进度条一下满格；for free：价签 free；public database：标签；
// According to the paper：清场，论文书落下；this was：书一抖；first time：手写；AlphaFold：芯片落下；had been used：预测模型卡从芯片滑出来；find a hit：001 插头落下打勾。
// 接点：开头 T2 从右甩进（4-01 是 B 页），结尾 T2 往左甩（4-03 是 B 页）。L0 第 4 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_4-02.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Tag, Calendar1, camBreath, Stage, Sprite, Slab, Plate, Label, Pen, Source, Tick, evMapB, whipX, impact} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 4;

const CAL = {x: 640, y: 330, w: 300};
const FLASK = {x: 300, y: 400, w: 210};
const BAR = (side) => ({x: side ? 1040 : 140, y: 640, w: 720, h: 44});
const RACK = {x: 1360, y: 451, w: 678};
const MODEL0 = {x: 1320, y: 530, w: 120}, MODEL1 = {x: 820, y: 495, w: 169};
const PRICE = {x: 1600, y: 160, w: 150, h: 64};
const BOOK = {x: 460, y: 440, w: 520};
const AF = {x: 1180, y: 430, w: 380};
const HIT = {x: 1640, y: 470, w: 280};

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
    X.land("cal", 0, 1, E.need.l, {antic: false});
    X.land("flask", 0, 1, E.lab.l, {antic: false});
    X.tw("slow", 0, 0.34, E.lab.s, E.paper.s, "none");
    X.land("rack", 0, 1, E.now.l, {antic: false});
    X.tw("dl", 0, 1, E.dl.s, E.dl.l + 20, "power2.inOut");
    X.tw("fast", 0, 1, E.dl.l, E.dl.l + 22, "power3.out");
    X.land("price", 0, 1, E.free.l, {antic: false});
    X.tw("clear", 0, 1, E.paper.s - 6, E.paper.l + 20, "power2.in");
    X.land("book", 0, 1, E.paper.l + 6, {antic: false});
    X.jiggle("bookJ", E.this.l, 7, 0);
    X.land("af", 0, 1, E.af.l, {antic: false});
    X.tw("used", 0, 1, E.used.s, E.used.l + 20, "power2.out");
    X.land("hit", 0, 1, E.hit.l, {antic: false});
    X.tw("tick", 0, 1, E.hit.l + 8, E.hit.l + 28, "power2.out");
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const mix = (a, b, t) => a + (b - a) * t;
  const whip = f < 7 ? whipX(f, 0, "in", -1) : whipX(f, LEN - 7, "out", -1);
  const cx = -2000 * S.clear;
  // 日历：每 40 帧翻一页（Before 的慢）
  const flip = S.cal > 0.9 ? Math.max(0, 1 - ((f - E.need.l) % 40) / 8) : 0;
  const m = {x: mix(MODEL0.x, MODEL1.x, S.dl), y: mix(MODEL0.y, MODEL1.y, S.dl) - 90 * Math.sin(Math.PI * S.dl), w: mix(MODEL0.w, MODEL1.w, S.dl)};


  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} whip={whip} shakeX={impact(f, E.dl.l + 20)} cam={camBreath(f, K, ["s1"])}>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${cx}px)`}}>
          <Layer id="before">
            <div style={{position:"absolute",inset:0,transformOrigin:"509px 454px",transform:`translateX(${-160*S.rack}px) scale(${1-.36*S.rack})`}}><LabScene x={509} y={404} a={S.cal} scatter={S.slow}/></div>
          </Layer>
          <Layer id="now">
            {S.rack > 0.01 && <Sprite name="dbrack/34" x={RACK.x} y={RACK.y - 40 * (1 - Math.min(1, S.rack)) + id(3).y} w={RACK.w} op={Math.min(1, S.rack * 1.5)} />}
            {S.rack > .01 && <Slab x={1240-160*S.dl} y={593} w={222} h={32} color={C.grey} op={Math.min(1,S.rack)} id="drawer"/>}
            {S.price > 0.01 && <Plate x={PRICE.x - PRICE.w / 2} y={PRICE.y - 30 * (1 - Math.min(1, S.price))} w={PRICE.w} h={PRICE.h} text="free" size={48} color={C.gold} op={Math.min(1, S.price * 1.5)} rot={-6} id="price" />}
          </Layer>
          <Layer id="model">
            {S.dl > .001 && <Slab x={m.x-180} y={m.y-130} w={360} h={260} r={18} op={Math.min(1,S.dl*4)} id="modelcard"/>}
            {S.dl > 0.001 && <Sprite name="af/front305" x={m.x} y={m.y + id(4).y} w={m.w} op={Math.min(1, S.dl * 4)} lift={20 * Math.sin(Math.PI * S.dl)} rim={S.fast > 0 && S.fast < 1 ? 1 - S.fast : 0} />}
          </Layer>
        </div>

        <Layer id="paper">
          {S.book > 0.01 && <Sprite name="book/34" x={BOOK.x} y={BOOK.y - 40 * (1 - Math.min(1, S.book)) - (S.bookJ || 0) + id(5).y} w={BOOK.w} op={Math.min(1, S.book * 1.5)} rot={id(5).r} />}
          {S.af > 0.01 && <Sprite name="chip_alphafold/34" x={AF.x} y={AF.y - 40 * (1 - Math.min(1, S.af)) + id(6).y} w={AF.w} op={Math.min(1, S.af * 1.5)} />}
          {S.used > 0.001 && <Sprite name="af/front305" x={mix(AF.x, AF.x + 40, S.used)} y={mix(AF.y, AF.y - 230, S.used)} w={mix(80, 190, S.used)} op={Math.min(1, S.used * 4)} lift={10} />}
          {S.hit > 0.01 && <Sprite name="plug/001_34" x={HIT.x} y={HIT.y - 40 * (1 - Math.min(1, S.hit)) + id(7).y} w={HIT.w} op={Math.min(1, S.hit * 1.5)} />}
          
        </Layer>

        <Layer id="txt" exempt>
          <Label text="lab-measured structure" size={52} x={500 + cx} y={720} at={E.struct.l} out={E.paper.s} align="center" />
          <Pen text="Now?" x={1080 + cx} y={150} at={E.now.l - 4} out={E.paper.s} size={84} />
          <Label text="public database" size={52} x={1400 + cx} y={720} at={E.db.l} out={E.paper.s} align="center" />
          <Label text="Ren et al., Chem. Sci. 2023" size={36} x={BOOK.x} y={BOOK.y + 185} at={E.paper.l + 16} align="center" />
          {f >= E.dl.l && <Tag x={820 + cx} y={640} op={Math.min(1, (f - E.dl.l) / 12) * (1 - Math.max(0, Math.min(1, (f - E.paper.s) / 12)))}>AlphaFold prediction</Tag>}
          <Pen text="first time" x={760} y={170} at={E.first.l} size={72} />
          <Label text="a hit" size={56} x={HIT.x} y={640} at={E.hit.l + 6} align="center" />
          <Source>Illustration · data: Ren et al., Chem. Sci. 2023 · structure: AlphaFold DB (free, public)</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B402" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
