// HKBU SCIE1007 课程作业的科普视频：第 2 章二维说明书页 2-08（A 画外音）：路线图回来。
// 七站的路；锁落在 Target 上方、芯片和钥匙落在 Hit 上方、烧瓶落在 Improve 上方；前三站红线框起来 today's route；最后大问题字牌。
// 时间全读 keys_2-08.json（事件表 映射/events/2-08.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_2-08.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Tag, Bead, evMap, Label, Pen, PageFrame, Source, Plate, Write} from "./kit.jsx";

const E = evMap(K);
const AR = {lock: 1, key: 1099 / 315, chip: 1, flask: 1};
const ST = ["Target", "Hit", "Improve", "Cells", "Animals", "Trials", "Approval"];
const RX0 = 230, RX1 = 1690, RY = 600;
const sx = (i) => RX0 + ((RX1 - RX0) * i) / (ST.length - 1);

const Scene = () => {
  const f = useCurrentFrame();
  const road = span(f, E.road.s, E.road.e, ease);
  const route = span(f, E.route.s, E.route.e, ease);
  const big = span(f, E.big.s, E.big.s + 16, out);
  const bead = [
    [0, RX0 - 120, RY], [E.road.l, RX0 - 60, RY - 40], [E.lock.l, sx(0), RY - 280], [E.chip.l, sx(1) - 60, RY - 250], [E.key.l, sx(1) + 40, RY - 190],
    [E.flask.l, sx(2), RY - 290], [E.route.l, sx(1), RY + 110], [E.big.l, 1500, 850], [K.len_f, 1502, 852],
  ];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("2-08.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.road.s, E.road.e)}>Where we're going</Write></div>
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {/* today's route：前三站 */}
        <rect x={sx(0) - 90} y={RY - 360} width={sx(2) - sx(0) + 180} height={460} rx={22} fill="none" stroke={RED} strokeWidth={5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - route} />
        <path d={`M${RX0 - 110},${RY} L${RX1 + 60},${RY}`} stroke={INK} strokeWidth={7} strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - road} />
        {ST.map((s, i) => {
          const p = span(road, (i + 0.4) / (ST.length + 0.6), (i + 1.2) / (ST.length + 0.6), out);
          return <circle key={s} cx={sx(i)} cy={RY} r={16 * p} fill={i < 3 && route > 0.5 ? RED : PAPER} stroke={i < 3 ? INK : "#9A968C"} strokeWidth={4} />;
        })}
      </svg>
      {ST.map((s, i) => (
        <Label key={s} x={sx(i)} y={RY + 30} w={180} size={30} color={i < 3 ? INK : "#8A867C"} p={span(road, (i + 0.6) / (ST.length + 0.6), (i + 1.4) / (ST.length + 0.6))}>{s}</Label>
      ))}
      <Part name="lock" cx={sx(0)} cy={RY - 170} w={150} ar={AR.lock} at={E.lock.s + 2} f={f} gate={[0.5, 1]} />
      <Label x={sx(0)} y={RY - 80} w={200} size={24} italic p={span(f, E.lock.l, E.lock.l + 20)}>the lock</Label>
      <Part name="chip" cx={sx(1) - 60} cy={RY - 230} w={90} ar={1} at={E.chip.s + 2} f={f} gate={[0.5, 1]} flood={16} />
      <Part name="key" cx={sx(1) + 30} cy={RY - 140} w={210} ar={AR.key} at={E.key.s + 2} f={f} gate={[0, 0.5]} />
      <div style={{position: "absolute", left: sx(1) - 60 - 26, top: RY - 230 - 8, width: 52, height: 16, background: "#2B2B2D", color: "#C9C6BE", fontSize: 8, textAlign: "center", lineHeight: "16px", opacity: span(f, E.chip.s + 6, E.chip.s + 14)}}>Chemistry42</div>
      <Label x={sx(1)} y={RY - 80} w={240} size={24} italic p={span(f, E.key.l, E.key.l + 20)}>AI cuts a key</Label>
      <Part name="flask" cx={sx(2)} cy={RY - 180} w={140} ar={AR.flask} at={E.flask.s + 2} f={f} gate={[0.5, 1]} />
      <Label x={sx(2)} y={RY - 80} w={240} size={24} italic p={span(f, E.flask.l, E.flask.l + 20)}>in the lab</Label>
      <Pen x={sx(2) + 120} y={RY - 360} p={span(f, E.route.s + 10, E.route.e + 10)} size={46}>today's route</Pen>
      <Tag n="21" x={sx(0) - 55} y={RY - 300} at={E.lock.l + 16} f={f} />
      <Tag n="22" x={sx(1) + 150} y={RY - 210} at={E.key.l + 16} f={f} />
      <Tag n="34" x={sx(2) + 54} y={RY - 300} at={E.flask.l + 16} f={f} />
      <Plate x={260} y={790} w={1400} p={big}><span style={{fontSize: 60, fontStyle: "italic"}}>How much did the computers really help?</span></Plate>
      <Source p={span(f, E.road.l, E.road.l + 20)}>Our structure for this review · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual208" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
