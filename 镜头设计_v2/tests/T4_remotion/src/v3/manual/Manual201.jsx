// HKBU SCIE1007 课程作业的科普视频：第 2 章二维说明书页 2-01（A 画外音）。
// 两个步骤框按年份：2011（中大、肝肿瘤样本、威尔斯亲王医院、CDK20 升高、CCRK = CDK20）→ 2023（AI 研究，同一个蛋白飞过来，英矽智能科学园办公室）。
// 时间全读 keys_2-01.json（事件表 映射/events/2-01.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_2-01.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Tag, Arrow, Step, Legend, Bead, evMap, Title, Label, Pen, Placeholder, PageFrame, Source, Plate} from "./kit.jsx";

const E = evMap(K);
const AR = {hk: 1174 / 791, univ: 394 / 580, tube: 218 / 610, hospital: 347 / 544, cdk20: 1, chip: 1, tower: 184 / 677};
const BX = [96, 988], BY = 150, BW = 836, BH = 640;
const C1 = [BX[0] + 290, BY + 520], C2 = [BX[1] + 400, BY + 300];

const Scene = () => {
  const f = useCurrentFrame();
  const plate = span(f, E.plate.s, E.plate.s + 14, out);
  const mv = span(f, E.same.s, E.same.l, Easing.inOut(Easing.cubic));
  const lift = Math.sin(Math.PI * mv) * -120;
  const cx = C1[0] + (C2[0] - C1[0]) * mv, cy = C1[1] + (C2[1] - C1[1]) * mv + lift, cw = 190 - 40 * mv;
  const fly = f >= E.same.s;
  const alias = span(f, E.alias.s, E.alias.l + 8, out);
  const pulse = f >= E.pulse.s ? Math.exp(-(f - E.pulse.s) / 7) * Math.sin(Math.min(Math.PI, (f - E.pulse.s) / 3)) : 0;
  const land = f > E.same.l ? Math.exp(-(f - E.same.l) / 5) * Math.cos((f - E.same.l) / 2.6) * 5 : 0;
  const bead = [
    [0, 120, 96], [E.hk.l, 250, 96], [E.step1.l, BX[0] + 46, BY + 46], [E.univ.l, BX[0] + 150, BY + 200], [E.tubes.l, BX[0] + 410, BY + 210],
    [E.hospital.l, BX[0] + 640, BY + 200], [E.cdk20.l, C1[0], C1[1] - 120], [E.plate.l, BX[0] + 620, BY + 480], [E.step2.l, BX[1] + 46, BY + 46],
    [E.chip.l, BX[1] + 160, BY + 200], [E.same.l, C2[0], C2[1] - 100], [E.tower.l, BX[1] + 650, BY + 140], [E.park.l, BX[1] + 650, BY + 560], [K.len_f, BX[1] + 652, BY + 562],
  ];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("2-01.wav")} />
      <PageFrame />
      <Part name="hk" cx={160} cy={98} w={120} ar={AR.hk} at={E.hk.s + 2} f={f} gate={[0, 0]} wipe={8} flood={14} />
      <Pen x={236} y={66} p={span(f, E.hk.s + 4, E.hk.e)} size={46}>Hong Kong first</Pen>
      <Placeholder x={BX[1]} y={BY} w={BW} h={BH} show={span(f, E.step1.l, E.step1.l + 24)} hide={span(f, E.step2.l, E.step2.l + 30)} />

      <Step n="1" x={BX[0]} y={BY} w={BW} h={BH} at={E.step1.l} f={f}>
        <Title p={span(f, E.title1.s, E.title1.e)} size={56}>2011</Title>
        <Part name="univ" cx={150} cy={260} w={130} ar={AR.univ} at={E.univ.s + 2} f={f} gate={[0.5, 1]} />
        <Label x={150} y={352} w={250} size={22} p={span(f, E.univ.s, E.univ.e)}>The Chinese University</Label>
        <Label x={150} y={380} w={250} size={22} p={span(f, E.univ.s + 20, E.univ.e)}>of Hong Kong</Label>
        {[0, 1, 2].map((i) => (
          <Part key={i} name="tube" cx={360 + i * 52} cy={268} w={44} ar={AR.tube} at={E.tubes.s + 2 + i * 8} f={f} gate={[0.5, 1]} wipe={8} flood={14} />
        ))}
        <Label x={412} y={366} w={200} size={22} italic p={span(f, E.tubes.s, E.tubes.e)}>liver tumours</Label>
        <Part name="hospital" cx={660} cy={262} w={130} ar={AR.hospital} at={E.hospital.s + 2} f={f} gate={[0.5, 1]} />
        <Label x={660} y={366} w={240} size={22} p={span(f, E.hospital.s, E.hospital.e)}>Prince of Wales Hospital</Label>
        <svg width={BW} height={BH} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
          <Arrow d="M412,410 C412,440 330,430 304,416" tip={[300, 414]} ang={200} a={E.cdk20.s - 12} b={E.cdk20.s + 4} f={f} sw={3} />
          <Arrow d="M420,590 L420,470" tip={[420, 464]} ang={-90} a={E.raised.s} b={E.raised.e} f={f} color={RED} sw={5} />
        </svg>
        <Tag n="15" x={530} y={196} at={E.tubes.l + 16} f={f} />
        <Tag n="19" x={180} y={430} at={E.cdk20.l + 16} f={f} />
        <Plate x={450} y={490} w={360} p={plate}><span style={{fontSize: 52}}>CCRK</span><span style={{display: "inline-block", marginLeft: 14, opacity: alias, transform: `translateX(${50 * (1 - alias)}px)`}}><span style={{fontSize: 40, fontStyle: "italic"}}>=&nbsp;</span><span style={{fontSize: 52}}>CDK20</span></span></Plate>
        <Label x={630} y={562} w={360} size={22} color={SOFT} italic p={span(f, E.plate.l + 20, E.plate.e)}>raised in liver tumours</Label>
      </Step>

      <Step n="2" x={BX[1]} y={BY} w={BW} h={BH} at={E.step2.l} f={f}>
        <Title p={span(f, E.title2.s, E.title2.e)} size={56}>2023</Title>
        <Part name="chip" cx={160} cy={270} w={130} ar={AR.chip} at={E.chip.s + 2} f={f} gate={[0.5, 1]} />
        <Label x={160} y={350} w={250} size={22} p={span(f, E.chip.s, E.chip.e)}>AI drug-discovery study</Label>
        <Tag n="13" x={250} y={200} at={E.chip.l + 16} f={f} />
        <Label x={650} y={110} w={300} size={22} color={SOFT} italic p={span(f, E.coauth.s, E.coauth.e)}>co-authors at</Label>
        <Part name="tower" cx={650} cy={300} w={64} ar={AR.tower} at={E.tower.s + 2} f={f} gate={[0.5, 1]} />
        <Tag n="14" x={720} y={180} at={E.tower.l + 16} f={f} />
        <Label x={650} y={430} w={320} size={24} p={span(f, E.label_ins.s, E.label_ins.e)}>Insilico Medicine</Label>
        <Label x={650} y={462} w={320} size={22} color={SOFT} p={span(f, E.label_ins.s + 20, E.label_ins.e)}>Hong Kong office</Label>
        <Label x={650} y={500} w={320} size={26} italic p={span(f, E.park.s, E.park.e)}>Hong Kong Science Park</Label>
        <Label x={400} y={430} w={240} size={22} color={SOFT} italic p={span(f, E.same.l, E.same.l + 30)}>the same protein</Label>
      </Step>

      {/* CDK20：2011 框里长出并留在那里；说到 same protein 时飞出一个同样的件到 2023 框 */}
      <div style={{position: "absolute", inset: 0, transform: `scale(${1 + 0.1 * pulse})`, transformOrigin: `${C1[0]}px ${C1[1]}px`}}>
        <Part name="cdk20" cx={C1[0]} cy={C1[1]} w={190} ar={1} at={E.cdk20.s + 2} f={f} gate={[0.5, 1]} />
      </div>
      {fly && (
        <div style={{position: "absolute", left: cx - cw / 2, top: cy - cw / 2 + land, width: cw, height: cw, filter: `drop-shadow(0 ${18 * Math.sin(Math.PI * mv)}px 14px rgba(40,40,80,0.25))`}}>
          <Part name="cdk20" cx={cw / 2} cy={cw / 2} w={cw} ar={1} at={-100} f={f} gate={[0.5, 1]} />
        </div>
      )}

      <Legend x={BX[0]} y={820} w={BW} at={E.tubes.l} f={f} rows={[[["15", "liver tumour samples", E.tubes.l + 16], ["19", "CDK20, first called CCRK", E.cdk20.l + 16]]]} />
      <Legend x={BX[1]} y={820} w={BW} at={E.chip.l} f={f} rows={[[["13", "AI study, Ren et al. 2023", E.chip.l + 16], ["14", "Insilico Medicine", E.tower.l + 16]]]} />
      <Source p={span(f, E.hk.l, E.hk.l + 20)}>Feng et al., J. Clin. Invest. 2011; Ren et al., Chem. Sci. 2023 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual201" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
