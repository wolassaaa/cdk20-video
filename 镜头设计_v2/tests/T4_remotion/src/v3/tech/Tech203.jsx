// HKBU SCIE1007 课程作业的科普视频：技术选型小测试（11-17）Remotion 一方。
// 2-03 一句（A 出镜）出镜旁动效小样：右半骨白展示台（CSS 3D 真透视，三个面），台面长出克莱因蓝 CDK20 示意体，
// 衬线字贴在展示台正面随词写出。时间直接 import 映射/keys/2-03.json（resolve.py 出），不经 export_remotion。
// 透明底，左半留给人。
//   node node_modules/@remotion/cli/remotion-cli.js render src/v3/tech/Tech203.jsx Tech203 OUT.mov --codec=prores --prores-profile=4444 \
//        --pixel-format=yuva444p10le --image-format=png --public-dir="<映射/_cache/remotion_public>"
import React from "react";
import {AbsoluteFill, Composition, Easing, registerRoot, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";
import K from "../../../../../../镜头设计_v3/映射/keys/2-03.json";

const BONE = "#ECE6DA", INK = "#2A2622", RED = "#B3261E", KLEIN = "#1F3FBF", CHROME = "#4A4D52";
const ease = Easing.bezier(0.33, 0, 0.2, 1);
const E = Object.fromEntries(K.events.map((e) => [e.id, e]));
const S1 = K.sentences[0];
const cl = (x) => Math.max(0, Math.min(1, x));
const span = (f, a, b, fn = (x) => x) => (f <= a ? 0 : f >= b ? 1 : fn((f - a) / Math.max(1, b - a)));
const prog = (e, f) => span(f, e.f_start, e.f_land, ease);
const sus = (e, f) => span(f, e.f_land, e.f_end);

const fontHandle = typeof window !== "undefined" ? delayRender("font") : null;
if (typeof window !== "undefined") {
  const ff = new FontFace("InstrumentSerif", `url(${staticFile("fonts/InstrumentSerif-Regular.ttf")})`);
  ff.load().then((x) => { document.fonts.add(x); continueRender(fontHandle); }).catch(() => continueRender(fontHandle));
}

// 写出：左→右软边遮罩
const Write = ({p, children, style}) => {
  const x = -8 + 116 * p;
  const m = `linear-gradient(90deg, #000 ${x - 6}%, transparent ${x}%)`;
  return <span style={{...style, WebkitMaskImage: m, maskImage: m, display: "inline-block"}}>{children}</span>;
};

const W = 900, H = 270, D = 330;            // 展示台宽、正面高、进深（px）

const Scene = () => {
  const f = useCurrentFrame();
  const slide = span(f, S1.f0, E.runner_flow.f_start, ease);
  const run = 0.15 * prog(E.runner_flow, f) + 0.85 * sus(E.runner_flow, f);
  const seat = prog(E.cavity_one, f);
  const cdk = prog(E.part_cdk20, f);
  const spin = span(f, E.part_cdk20.f_start, K.len_f - 1) * 95;
  const tc = E.tag_case, pc = E.part_cdk20, li = E.liver_in, ca = E.cancer_red;
  const w1 = span(f, tc.f_start, tc.f_end);
  const w2 = span(f, pc.f_start, pc.f_land + Math.floor((pc.f_end - pc.f_land) / 3));
  const w3 = span(f, li.f_start, li.f_land + 12);
  const w4 = span(f, ca.f_start, ca.f_end - 6);
  const glow = prog(ca, f) * 0.5 + 0.5 * sus(ca, f);
  const tx = (1 - slide) * 1500;
  return (
    <AbsoluteFill style={{perspective: 1700, perspectiveOrigin: "1200px 300px"}}>
      {/* 地面软影 */}
      <div style={{position: "absolute", left: 900 + tx * 0.9, top: 790, width: 980, height: 120, borderRadius: "50%",
                   background: "radial-gradient(closest-side, rgba(0,0,0,0.55), rgba(0,0,0,0))", filter: "blur(18px)"}} />
      <div style={{position: "absolute", left: 930, top: 560, width: W, height: H, transformStyle: "preserve-3d",
                   transform: `translateX(${tx}px) rotateX(-12deg) rotateY(-12deg)`}}>
        {/* 正面 */}
        <div style={{position: "absolute", width: W, height: H, borderRadius: 10,
                     background: `linear-gradient(180deg, #F1ECE2 0%, ${BONE} 45%, #D9D2C4 100%)`,
                     boxShadow: "inset 0 1px 0 rgba(255,255,255,0.8), inset 0 -18px 30px rgba(0,0,0,0.08)",
                     padding: "46px 0 0 48px", boxSizing: "border-box", fontFamily: "InstrumentSerif", color: INK}}>
          <div style={{fontSize: 92, lineHeight: 1}}><Write p={w1}>One case study</Write></div>
          <div style={{fontSize: 72, lineHeight: 1, marginTop: 28}}>
            <Write p={w2}>CDK20</Write>&nbsp;&nbsp;<Write p={w3}>in liver</Write>&nbsp;&nbsp;<Write p={w4} style={{color: RED}}>cancer.</Write>
          </div>
        </div>
        {/* 顶面 */}
        <div style={{position: "absolute", width: W, height: D, top: 0, transformOrigin: "top", transform: "rotateX(-90deg)",
                     background: "linear-gradient(0deg, #F6F2EA, #E3DCCF)", borderRadius: 10}}>
          {/* 流道：前沿红料 */}
          <div style={{position: "absolute", left: 22, top: 14, height: 9, width: (W - 44) * run, borderRadius: 5,
                       background: `linear-gradient(180deg, #D8473C, ${RED} 60%, #7E1712)`}} />
          {/* 托槽 */}
          <div style={{position: "absolute", left: 600 - 120, top: 165 - 120, width: 240, height: 240, borderRadius: "50%",
                       transform: `scale(${seat})`, background: `radial-gradient(circle at 40% 35%, #8A8E95, ${CHROME} 45%, #1E2024)`,
                       boxShadow: `0 0 0 4px rgba(179,38,30,${0.5 + 0.5 * glow}), 0 0 ${30 * glow}px ${8 * glow}px rgba(220,60,40,${0.6 * glow})`}} />
        </div>
        {/* 右侧面 */}
        <div style={{position: "absolute", width: D, height: H, left: W, transformOrigin: "left", transform: "rotateY(90deg)",
                     background: "linear-gradient(90deg, #BDB6A9, #9E978B)", borderRadius: 10}} />
        {/* CDK20 示意体：站在托槽中心上方，始终面向机位（伪三维球） */}
        <div style={{position: "absolute", left: 600 - 115, top: -230, width: 230, height: 230, transformStyle: "preserve-3d",
                     transform: `translateZ(${-165}px) rotateY(12deg) rotateX(12deg) scale(${cdk})`, transformOrigin: "50% 100%"}}>
          <div style={{position: "absolute", inset: 0, borderRadius: "48% 52% 50% 50% / 52% 46% 54% 48%",
                       background: `radial-gradient(circle at 34% 30%, #FFFFFF 0%, #7E95F0 7%, ${KLEIN} 38%, #0E1F6E 78%, #050A2A 100%)`,
                       boxShadow: "inset -18px -22px 40px rgba(0,0,0,0.45)"}} />
          <div style={{position: "absolute", inset: 0, borderRadius: "50%", transform: `rotate(${spin * 2}deg)`, opacity: 0.55,
                       background: "radial-gradient(circle at 70% 40%, rgba(80,110,230,0.9), rgba(0,0,0,0) 26%), radial-gradient(circle at 30% 72%, rgba(10,20,90,0.9), rgba(0,0,0,0) 30%), radial-gradient(circle at 62% 78%, rgba(60,90,220,0.7), rgba(0,0,0,0) 22%)"}} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Root = () => (
  <Composition id="Tech203" component={Scene} durationInFrames={K.len_f} fps={K.fps} width={1920} height={1080} />
);
registerRoot(Root);
