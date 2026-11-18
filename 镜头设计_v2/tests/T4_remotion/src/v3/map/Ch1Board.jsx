// HKBU SCIE1007 课程作业的科普视频：第 1 章三段大板（1-02、1-09、1-10）的二维叠加层（透明底）：底部字幕和左下角出处行。
// 和样片 2-03 的 Sample203.jsx 同一种做法：字幕印在一块骨白小牌上（Instrument Serif 正体），出处行在左下角。
// 时间全部读 table/<段>.json（映射/export_remotion.py 从总表转出）：字幕按句、长句按标点和长度切成几块，每块从它第一个词开口时出来，
// 到下一块开口前换掉；出处行从事件 source_line 起一直在。不写帧号。
// 用法（在 T4_remotion 里出透明 PNG 序列，再由 镜头设计_v3/inserts/finish_ch1.sh 叠到 Blender 帧上）：
//   node node_modules/@remotion/cli/remotion-cli.js render src/v3/map/Ch1Board.jsx Ch1-102 <outdir> --sequence --image-format=png \
//        --public-dir="D:/。hkbu/molecular science/镜头设计_v3/映射/_cache/remotion_public"
import React from "react";
import {AbsoluteFill, Composition, registerRoot, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";
import T102 from "./table/1-02.json";
import T109 from "./table/1-09.json";
import T110 from "./table/1-10.json";
import {event} from "./mapTable.mjs";

const INK = "#1F1E1C", GREY = "#5E5B54";
const FADE = 6, MAXC = 44, PRE = 3, HOLD = 24;
const SOFT = new Set(["and", "for", "that", "an", "went", "alongside", "then"]);

const SOURCE = {
  "1-02": "Hong Kong Cancer Registry 2022; GLOBOCAN 2022 (Bray et al. 2024) \u00b7 Illustration",
  "1-09": "Illustration",
  "1-10": "The Nobel Prize in Chemistry 2024, NobelPrize.org \u00b7 Illustration",
};

const fontHandle = typeof window !== "undefined" ? delayRender("font") : null;
if (typeof window !== "undefined") {
  const ff = new FontFace("InstrumentSerif", `url(${staticFile("fonts/InstrumentSerif-Regular.ttf")})`);
  ff.load().then((f) => { document.fonts.add(f); continueRender(fontHandle); }).catch(() => continueRender(fontHandle));
}

const pretty = (s) => s.replace(/'/g, "\u2019");

// 一句切成几块：块长不超过 MAXC 个字；到了逗号、冒号而且已经够长就先断
const cues = (T) => {
  const out = [];
  for (const s of T.sentences) {
    const ws = T.words.filter((w) => w.sid === s.sid);
    let cur = [];
    const flush = () => { if (cur.length) out.push({sid: s.sid, words: cur}); cur = []; };
    for (const w of ws) {
      const len = cur.map((x) => x.w).join(" ").length;
      if (cur.length && len + 1 + w.w.length > MAXC) {
        // 太长了：往回找一个好断的地方（标点后面，或者 and、for、that 这类词前面），名字和词组不拆开
        let j = -1;
        for (let k = cur.length - 1; k >= 2 && j < 0; k--) if (/[,:;]$/.test(cur[k - 1].w)) j = k;
        for (let k = cur.length - 1; k >= 2 && j < 0; k--) if (SOFT.has(cur[k].w.toLowerCase())) j = k;
        if (j > 0) { const rest = cur.slice(j); cur = cur.slice(0, j); flush(); cur = rest; } else flush();
      }
      cur.push(w);
      const l2 = cur.map((x) => x.w).join(" ").length;
      if (/[,:;]$/.test(w.w) && l2 >= 18) flush();
    }
    flush();
  }
  return out.map((c, i) => {
    const f0 = c.words[0].f0 - PRE;
    const next = out[i + 1];
    const s = T.sentences.find((x) => x.sid === c.sid);
    const last = c.words[c.words.length - 1].f1;
    let f1 = next ? (next.sid === c.sid ? next.words[0].f0 - PRE - 1 : Math.min(last + HOLD, next.words[0].f0 - PRE - 1)) : Math.max(last + HOLD, s.f1 + HOLD);
    f1 = Math.min(f1, T.len_f - 1 + FADE);
    return {text: pretty(c.words.map((x) => x.w).join(" ")), f0, f1, cut: next && next.sid === c.sid};
  });
};

const Overlay = ({T}) => {
  const f = useCurrentFrame();
  const src = event(T, "source_line");
  const C = cues(T);
  return (
    <AbsoluteFill style={{fontFamily: "InstrumentSerif"}}>
      {C.map((c, i) => {
        // 同一句里换块是直接换（不闪）；一句的第一块淡入，最后一块淡出
        const prevCut = i > 0 && C[i - 1].cut;
        const fin = prevCut ? 1 : Math.min(1, Math.max(0, (f - c.f0 + 1) / FADE));
        const fout = c.cut ? 1 : Math.min(1, Math.max(0, (c.f1 - f + 1) / FADE));
        const al = f < c.f0 || f > c.f1 ? 0 : Math.min(fin, fout);
        if (al <= 0) return null;
        return (
          <div key={i} style={{position: "absolute", left: 0, right: 0, bottom: 62, display: "flex", justifyContent: "center", opacity: al}}>
            <div style={{background: "rgba(244,241,234,0.94)", color: INK, fontSize: 46, lineHeight: "58px", padding: "7px 30px 9px", borderRadius: 16,
                         boxShadow: "0 2px 0 rgba(255,255,255,0.9) inset, 0 6px 18px rgba(60,50,40,0.22), 0 1px 2px rgba(60,50,40,0.25)"}}>
              {c.text}
            </div>
          </div>
        );
      })}
      {f >= src.f_start && (
        <div style={{position: "absolute", left: 40, bottom: 18, opacity: Math.min(1, (f - src.f_start + 1) / Math.max(1, src.f_end - src.f_start)),
                     background: "rgba(244,241,234,0.86)", color: GREY, fontSize: 24, lineHeight: "30px", padding: "2px 14px 4px", borderRadius: 10}}>
          {SOURCE[T.group]}
        </div>
      )}
    </AbsoluteFill>
  );
};

const Root = () => (
  <>
    <Composition id="Ch1-102" component={Overlay} defaultProps={{T: T102}} durationInFrames={T102.len_f} fps={60} width={1920} height={1080} />
    <Composition id="Ch1-109" component={Overlay} defaultProps={{T: T109}} durationInFrames={T109.len_f} fps={60} width={1920} height={1080} />
    <Composition id="Ch1-110" component={Overlay} defaultProps={{T: T110}} durationInFrames={T110.len_f} fps={60} width={1920} height={1080} />
  </>
);
registerRoot(Root);
