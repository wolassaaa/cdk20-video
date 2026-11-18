// HKBU SCIE1007 课程作业的科普视频：出镜 1-01（A）"Every day in Hong Kong, about four people die of liver cancer."
// 讲解位：香港地图、四个小人（说到 die 流成红色）、~4 a day、肝。时间全读 oncam_1-01.json（事件表 映射/events/1-01.json）。
//   node node_modules/@remotion/cli/remotion-cli.js render src/v3/manual/OnCam101.jsx OnCam101 <帧目录> --sequence --public-dir=<映射/_cache/ch1/public>
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_1-01.json";
import {INK, RED, out, span, Part, Tag, Write} from "./kit.jsx";
import {OnCamFrame, useOnCam} from "./oncam.jsx";

const AR = {hk: 1174 / 791, person_w: 413 / 682, liver: 1052 / 792};
const PEOPLE = [1250, 1352, 1454, 1556];

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  const red = span(f, E.die.s, E.die.e, out);
  const plate = span(f, E.plate.s, E.plate.s + 14, out);
  return (
    <OnCamFrame D={D} f={f} wav="1-01.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        <div style={{position: "absolute", left: 1150, top: 140, font: "46px Hand", color: RED, transform: "rotate(-4deg)"}}>
          <Write p={span(f, E.note_day.s, E.note_day.e)}>every day</Write>
        </div>
        <Part name="hk" cx={1500} cy={330} w={430} ar={AR.hk} at={E.hk.s + 2} f={f} gate={[0, 0]} />
        <Tag n="07" x={1748} y={160} at={E.hk.l + 16} f={f} />
        {PEOPLE.map((x, i) => {
          const at = E.people.s + 2 + i * ((E.people.e - E.people.s) / 5);
          return (
            <React.Fragment key={i}>
              <Part name="person_w" cx={x} cy={640} w={80} ar={AR.person_w} at={at} f={f} gate={[0.5, 0]} wipe={8} flood={14} />
              <div style={{position: "absolute", left: 0, top: 0, opacity: span(red, i * 0.12, 0.64 + i * 0.12)}}>
                <Part name="person_r" cx={x} cy={640} w={80} ar={AR.person_w} at={-100} f={f} gate={[0.5, 0]} />
              </div>
            </React.Fragment>
          );
        })}
        <Tag n="03" x={1196} y={560} at={E.people.e} f={f} />
        <div style={{position: "absolute", left: 1170, top: 734, width: 480, textAlign: "center", opacity: plate, transform: `scale(${1.08 - 0.08 * plate})`}}>
          <span style={{fontSize: 76}}>~4</span><span style={{fontSize: 44, fontStyle: "italic"}}> a day</span>
        </div>
        <Part name="liver" cx={1752} cy={640} w={190} ar={AR.liver} at={E.liver.s + 2} f={f} gate={[1, 0.45]} />
        <Tag n="04" x={1838} y={540} at={E.liver.l + 16} f={f} />
      </div>
      <div style={{position: "absolute", right: 44, top: 1046, fontSize: 17, color: "#6E6B63"}}>Hong Kong Cancer Registry, 2022 · Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam101" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
