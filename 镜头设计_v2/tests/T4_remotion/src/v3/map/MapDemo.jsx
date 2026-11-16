// HKBU SCIE1007 课程作业的科普视频：总表 → Remotion 接入验证（不是成片设计）。2-03 一句，每个事件的起动/落点/持续全部读 table/2-03.json。
// 用法（在 T4_remotion 里）：
//   node node_modules/@remotion/cli/remotion-cli.js render src/v3/map/MapDemo.jsx MapDemo-2-03 <out.mp4> \
//        --public-dir="D:/。hkbu/molecular science/镜头设计_v3/映射/_cache/remotion_public" --codec=h264 --crf=16
// 原生 60 fps，段长 = 总表 len_f；声音是 cut_v8 里这段原样截出。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";
import T203 from "./table/2-03.json";
import {event, progress, sustain} from "./mapTable.mjs";

const BONE = "#ECE6DA", INK = "#2A2622", RED = "#B3261E", KLEIN = "#1F3FBF", CHROME = "#4A4D52";
const ease = Easing.bezier(0.33, 0, 0.2, 1);

const fontHandle = typeof window !== "undefined" ? delayRender("font") : null;
if (typeof window !== "undefined") {
  const ff = new FontFace("InstrumentSerif", `url(${staticFile("fonts/InstrumentSerif-Regular.ttf")})`);
  ff.load().then((f) => { document.fonts.add(f); continueRender(fontHandle); }).catch(() => continueRender(fontHandle));
}

const RUNNER = "M 120 600 C 420 600 460 420 760 420 S 1100 600 1320 560";
const LIVER = "M 1380 470 C 1440 380 1640 360 1760 400 C 1840 430 1830 520 1760 560 C 1680 610 1560 640 1470 610 C 1400 590 1350 540 1380 470 Z";

const Demo = ({T}) => {
  const f = useCurrentFrame();
  const E = (id) => event(T, id);
  const flow = E("runner_flow"), cav = E("cavity_one"), tag = E("tag_case"), cdk = E("part_cdk20"), liv = E("liver_in"), can = E("cancer_red");
  // 流：起动到落点走前 15%，之后一直流到 until（study 说完）
  const head = 0.15 * progress(flow, f, ease) + 0.85 * sustain(flow, f);
  const cavS = progress(cav, f, ease);
  const tagY = 120 * (1 - progress(tag, f, ease)) - 6 * sustain(tag, f);
  const cdkS = progress(cdk, f, ease), cdkGlow = sustain(cdk, f);
  const livD = progress(liv, f, ease);
  const red = progress(can, f, ease) * 0.25 + 0.55 * sustain(can, f);
  const cur = [...T.words].reverse().find((w) => w.f0 <= f);
  return (
    <AbsoluteFill style={{background: BONE}}>
      <Audio src={staticFile(`map/${T.group}.wav`)} />
      <svg width={1920} height={1080} viewBox="0 0 1920 1080">
        {/* 流道槽（骨白模具上的凹槽） */}
        <path d={RUNNER} stroke="#D6CFC2" strokeWidth={30} fill="none" strokeLinecap="round" />
        <path d={RUNNER} pathLength={1} stroke={RED} strokeWidth={20} fill="none" strokeLinecap="butt"
              strokeDasharray={`${head} 1`} />
        {/* one：一个腔 */}
        <g transform={`translate(760 420) scale(${cavS})`}>
          <rect x={-150} y={-120} width={300} height={240} rx={34} fill="#DDD6C9" stroke={CHROME} strokeWidth={4} />
          {/* CDK20：克莱因蓝件在腔里长满 */}
          <rect x={-120} y={-90} width={240} height={180} rx={26} fill={KLEIN} opacity={0.15 + 0.85 * cdkS}
                transform={`scale(${0.2 + 0.8 * cdkS})`} />
          {cdkGlow > 0 && cdkGlow < 1 && <circle r={10} fill={RED}
              cx={Math.cos(-Math.PI / 2 + 2 * Math.PI * cdkGlow) * 120 * 1.0} cy={Math.sin(-Math.PI / 2 + 2 * Math.PI * cdkGlow) * 90} />}
          {cdkS > 0.6 && <text x={0} y={18} textAnchor="middle" fontFamily="InstrumentSerif" fontSize={64}
                               fill={BONE} opacity={Math.min(1, (cdkS - 0.6) / 0.4)}>CDK20</text>}
        </g>
        {/* case study：标签从腔下面被顶出，贴在腔的下沿 */}
        <g transform={`translate(760 ${560 + tagY})`} opacity={tag.f_start <= f ? 1 : 0}>
          <rect x={-110} y={-26} width={220} height={52} rx={6} fill="#F6F1E7" stroke={CHROME} strokeWidth={2} />
          <text x={0} y={12} textAnchor="middle" fontFamily="InstrumentSerif" fontSize={34} fill={INK}>case study</text>
        </g>
        {/* liver：轮廓长出；cancer：红料灌进去，一直到句尾 */}
        <path d={LIVER} fill={RED} opacity={red} />
        <path d={LIVER} pathLength={1} fill="none" stroke={INK} strokeWidth={5} strokeDasharray={`${livD} 1`} />
        {/* 接入验证的标识和当前词（验证用，不进片） */}
        <text x={40} y={1040} fontFamily="InstrumentSerif" fontSize={30} fill={CHROME}>Mapping test · {T.group} · {T.cut} · frame {f} · word: {cur ? cur.w : "—"}</text>
        {T.words.map((w) => <line key={w.wid} x1={40 + 1840 * w.f0 / T.len_f} x2={40 + 1840 * w.f0 / T.len_f} y1={990} y2={1005} stroke={w.f0 <= f ? RED : "#BDB5A6"} strokeWidth={3} />)}
      </svg>
    </AbsoluteFill>
  );
};

const Root = () => (
  <Composition id="MapDemo-2-03" component={Demo} defaultProps={{T: T203}} durationInFrames={T203.len_f} fps={60} width={1920} height={1080} />
);
registerRoot(Root);
