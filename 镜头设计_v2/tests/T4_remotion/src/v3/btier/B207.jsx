// HKBU SCIE1007 课程作业的科普视频：B 档 2-07（D 画外音）"For every source, we asked: what kind is it, how much did we read, and how strong is the evidence? …"
// For every source：左边七张来源卡落下；we asked：放大镜落到第一张卡上，右边核对表底板滑进来；
// what kind / how much / how strong / Who did the work / controls and repeats：核对表五行逐条刻出，放大镜跟着一张张卡扫过，每行写完打勾；
// One thing worth knowing：清场，主论文落到左边；most authors：一排八个小人；work for Insilico Medicine：底板滑进来，六个小人跳上去；
// which built its AI tools：两块芯片落到底板上；They say so openly：论文下挂 declared 名牌，打勾；Useful evidence：标签；not an independent check：手写。
// 接点：开头 T2 从右甩进（2-06 是 B 页），结尾 T2 往左甩（2-08 是 B 页）。L0 第 2 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_2-07.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, SERIF, Runner, Tag, camBreath, Stage, Sprite, Slab, Plate, Label, Pen, Source, Tick, LoupeRing, Person1, evMapB, whipX, Engrave} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";
import {REFS, RefCard} from "./refcards.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 2;

const pos = i => [120 + (i%2)*470, 200 + Math.floor(i/2)*190];   // P04：两列，卡 440×150
const CHECKS = [["kind","What kind is it?"],["much","How much did we read?"],["strong","How strong is the evidence?"],["who","Who did the work?"],["ctrl","Were there controls and repeats?"]];   // P07
const AUTHORS = ["Feng Ren","Xiao Ding","Min Zheng","Mikhail Korzinkin","Xin Cai","Wei Zhu","Alexey Mantsyzov","Alex Aliper","Vladimir Aladinskiy","Zhongying Cao","Shanshan Kong","Xi Long","Bonnie Hei Man Liu","Yingtao Liu","Vladimir Naumov","Anastasia Shneyderman","Ivan V. Ozerov","Ju Wang","Frank W. Pun","Daniil A. Polykovskiy","Chong Sun","Michael Levitt","Alán Aspuru-Guzik","Alex Zhavoronkov"];   // P09，论文 p.1443 顺序
const OUTSIDE = new Set([20, 21, 22]);   // 3 位不在 Insilico
const INS_ORDER = AUTHORS.map((_, i) => i).filter(i => !OUTSIDE.has(i));   // 21 人按名单顺序
const Scene = () => {
  const f = useCurrentFrame();
  const p = (a,b)=>Math.max(0,Math.min(1,(f-a)/Math.max(1,b-a)));
  const scan = p(E.kind.s,E.kind.e)*5.99, idx=Math.floor(scan), t=scan-idx;
  const [lx,ly] = pos(idx), [nx,ny] = pos(Math.min(5,idx+1));
  const reading=p(E.much.s,E.much.e), strength=p(E.strong.s,E.strong.e);
  const cardsOp=1-p(E.worth.s,E.worth.s+12), book=p(E.worth.l,E.worth.l+18), plateIn=p(E.authors.l+48,E.authors.l+66);
  const revealed=p(E.open.s,E.open.l);
  return <Lens plan={GP} f={f}>
    <Stage zone={ZONE} f={f} whip={f<7?whipX(f,0,"in",-1):whipX(f,LEN-7,"out",-1)} cam={camBreath(f,K,["s5"])}>
      <Layer id="cards" exempt>
        {cardsOp>0 && REFS.map((ref,i)=>{
          const [x,y]=pos(i), lit=idx===i&&f>=E.kind.s&&f<E.worth.s, k=lit?1.06:1;
          return <RefCard key={i} x={x-(k-1)*220} y={y+24*(1-p(E.src.s,E.src.l))-(k-1)*75} w={440*k} h={150*k} ref2={ref} op={cardsOp} id={`reference${i}`}/>;
        })}
        {f>=E.kind.s && f<E.much.l && <LoupeRing x={lx+220+(nx-lx)*t} y={ly+75+(ny-ly)*t} r={150} op={(1-p(E.much.s,E.much.l))*cardsOp}/>}
      </Layer>
      <Layer id="list">
        {cardsOp>0 && <Slab x={1090+60*(1-p(E.asked.s,E.asked.l))} y={200} w={720} h={530} id="checklist" op={p(E.asked.s,E.asked.l)*cardsOp}>
          {CHECKS.map(([ev,txt],i)=><React.Fragment key={ev}>
            <div style={{position:"absolute",left:40,top:40+i*96,opacity:p(E[ev].s,E[ev].l)}}><Engrave size={40}>{txt}</Engrave></div>
            <Tick x={640} y={40+i*96+22} s={44} p={p(E[ev].l,E[ev].l+14)}/>
          </React.Fragment>)}
        </Slab>}
      </Layer>
      <Layer id="list">
        {book>0 && <Slab x={120} y={200-65*(1-book)} w={760} h={420} id="paper" op={book}>
          <div data-role="engrave" data-on="paper" style={{position:"absolute",left:35,top:24,fontSize:53,fontFamily:SERIF,color:C.ink}}>Ren et al., Chem. Sci. 2023</div>
          <div style={{position:"absolute",left:30,top:110,width:700,lineHeight:"56px"}}>
            {/* Z14（11-23）：24 个名字字高只有 17 px 读不出，改成前 6 位（都在 Insilico，逐个变蓝）+ et al.，字号 42；"21 of 24" 由右边的牌和小人讲 */}
            {AUTHORS.slice(0,6).map((nm,i)=>{
              const blue=f>=E.authors.l+8*i;
              return <React.Fragment key={i}><Engrave size={42} color={blue?C.blue:C.ink}>{nm},</Engrave>{" "}</React.Fragment>;
            })}
            <Engrave size={42} color={C.ink}>et al.</Engrave>
          </div>
        </Slab>}
      </Layer>
      <Layer id="book" exempt>
        {plateIn>0 && <Plate x={1000} y={480} w={720} h={90} text="Insilico Medicine · 21 of 24 authors" size={40} op={plateIn} id="authors"/>}
        {revealed>0 && <Plate x={300} y={747-20*revealed} w={630} h={94} text="Conflicts of interest: declared" size={42} op={revealed} id="coi" rot={-12*(1-revealed)}><Tick x={594} y={48} s={40} p={revealed}/></Plate>}
      </Layer>
      <Layer id="auth" exempt>
        <Runner d="M1360 578 V600 H1200 M1360 600 H1520" width={14} draw={p(E.built.s,E.built.l)}/>
        {["pandaomics","chemistry42"].map((n,i)=>{
          const a=p(E.built.s+i*4,E.built.l+i*4);
          return a>0 && <React.Fragment key={n}><Sprite name={`chip_${n}/34`} x={1200+320*i} y={690+70*(1-a)} w={209} op={a}/>
            <Tag x={1200+320*i} y={690+70*(1-a)+70+20} op={a}>{["PandaOmics","Chemistry42"][i]}</Tag></React.Fragment>;
        })}
      </Layer>
      <Layer id="txt" exempt>
        {plateIn>0 && f<E.built.s && <Tag x={1360} y={400} op={plateIn}>3 other authors: Univ. of Toronto, Stanford</Tag>}
        <Label text="useful evidence" x={500} y={650} at={E.useful.l} size={44}/>
        <Pen text="not an independent check" x={1100} y={330} size={56} at={E.notind.l}/>
        <Source>{f<E.authors.l?"Illustration · how we graded our sources":"Illustration · author affiliations as declared in Ren et al., Chem. Sci. 2023"}</Source>
      </Layer>
    </Stage>
  </Lens>;
};

const Root = () => <Composition id="B207" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
