// HKBU SCIE1007 课程作业的科普视频：大板样片 2-03 的二维叠加层（透明底）：底部字幕和左下角出处行。
// 时间全部读 table/2-03.json（映射/export_remotion.py 从总表转出）里的事件 sub_a、sub_b、source_line，不写帧号。
// 画面是板的近景，字幕带下面躲不开料杆和前排零件，所以字幕印在一块骨白小牌上（和板上的字牌同一种做法），压在什么上面都看得清。
// 用法（在 T4_remotion 里，出透明 PNG 序列，再由 镜头设计_v3/inserts/finish_s203.sh 叠到 Blender 帧上）：
//   node node_modules/@remotion/cli/remotion-cli.js render src/v3/map/Sample203.jsx Sample203 <outdir> --sequence --image-format=png \
//        --public-dir="D:/。hkbu/molecular science/镜头设计_v3/映射/_cache/remotion_public"
import React from "react";
import {AbsoluteFill, Composition, registerRoot, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";
import T from "./table/2-03.json";
import {event} from "./mapTable.mjs";

const INK = "#1F1E1C", BONE = "#F4F1EA", GREY = "#5E5B54";
const FADE = 6;

const fontHandle = typeof window !== "undefined" ? delayRender("font") : null;
if (typeof window !== "undefined") {
  const ff = new FontFace("InstrumentSerif", `url(${staticFile("fonts/InstrumentSerif-Regular.ttf")})`);
  ff.load().then((f) => { document.fonts.add(f); continueRender(fontHandle); }).catch(() => continueRender(fontHandle));
}

// 一条字幕：f_start 淡入，f_end 淡出
const alpha = (e, f, out = true) => {
  const a = Math.min(1, Math.max(0, (f - e.f_start + 1) / FADE));
  const b = out ? Math.min(1, Math.max(0, (e.f_end - f + 1) / FADE)) : 1;
  return Math.min(a, b);
};

const CUES = [["sub_a", "And we\u2019ll answer it with one case study:"], ["sub_b", "CDK20 in liver cancer."]];

const Overlay = ({showSubtitles = true, standardSource = false}) => {
  const f = useCurrentFrame();
  const src = event(T, "source_line");
  return (
    <AbsoluteFill style={{fontFamily: "InstrumentSerif"}}>
      {showSubtitles && CUES.map(([id, text]) => {
        const e = event(T, id);
        const a = alpha(e, f, id !== "sub_b" || e.f_end < T.len_f - 1);
        if (a <= 0) return null;
        return (
          <div key={id} style={{position: "absolute", left: 0, right: 0, bottom: 62, display: "flex", justifyContent: "center", opacity: a}}>
            <div style={{background: "rgba(244,241,234,0.94)", color: INK, fontSize: 46, lineHeight: "58px", padding: "7px 30px 9px", borderRadius: 16,
                         boxShadow: "0 2px 0 rgba(255,255,255,0.9) inset, 0 6px 18px rgba(60,50,40,0.22), 0 1px 2px rgba(60,50,40,0.25)"}}>
              {text}
            </div>
          </div>
        );
      })}
      {f >= src.f_start && (
        <div style={{position: "absolute", left: standardSource ? 64 : 40, top: standardSource ? 886 : undefined, bottom: standardSource ? undefined : 26, opacity: Math.min(1, (f - src.f_start + 1) / Math.max(1, src.f_end - src.f_start)),
                     background: standardSource ? "rgba(244,241,234,0.8)" : "rgba(244,241,234,0.86)", color: standardSource ? INK : GREY, fontSize: standardSource ? 30 : 25, lineHeight: standardSource ? "42px" : "32px", padding: standardSource ? "0 14px" : "2px 14px 4px", borderRadius: 10}}>
          {standardSource ? "Illustration · Ren et al., Chem. Sci. 2023" : "Ren et al., Chem. Sci. 2023 · Illustration"}
        </div>
      )}
    </AbsoluteFill>
  );
};

const Root = () => (
  <Composition id="Sample203" component={Overlay} durationInFrames={T.len_f} fps={60} width={1920} height={1080} />
);
registerRoot(Root);
