// HKBU SCIE1007 课程作业的科普视频：出镜段共用外框（版式照 2-02：人在左，身后是大板近景，右边讲解位）。
// D = oncam_<段>.json：len_f（按素材实际覆盖截的出片长）、clips（seg, off：段帧 = 素材帧 + off, cut：从这一帧起用这条）、
//     nose（段帧上的鼻尖位置，素材坐标）、events（resolve.py 算出的事件帧）。
// 人物逐帧图：public/person_<seg>/NNNN.png（素材 _fg + _a 合成，1728×972）。声音：public/<段>.wav（cut_v8 里这段）。
// 跟头：鼻尖轨迹先高斯平滑，讲解位只跟 0.2 倍（导演 11-18：跟得太灵敏会晃）。
import React from "react";
import {AbsoluteFill, Audio, Img, staticFile} from "remotion";
import {PAPER, INK} from "./kit.jsx";

const SC = 1728 / 3328, PX = -301, PY = 108;
const HEAD = 0.2;
// 素材取景到右边就断了，手伸过去会被竖着切掉：右边缘 60 px 羽化成渐隐
const EDGE = "linear-gradient(90deg,#000 calc(100% - 60px),transparent 100%)";

const gauss = (arr, sig) => {
  let last = arr.find(Boolean);
  const a = arr.map((p) => (p ? (last = p) : last)), n = a.length, R = Math.ceil(sig * 3), o = [];
  for (let i = 0; i < n; i++) {
    let x = 0, y = 0, w = 0;
    for (let k = -R; k <= R; k++) { const j = Math.max(0, Math.min(n - 1, i + k)), g = Math.exp(-(k * k) / (2 * sig * sig)); x += a[j][0] * g; y += a[j][1] * g; w += g; }
    o.push([x / w, y / w]);
  }
  return o;
};

export const useOnCam = (D) => {
  const NOSE = gauss(D.nose, 10);
  const mean = NOSE.reduce((s, p) => [s[0] + p[0] / NOSE.length, s[1] + p[1] / NOSE.length], [0, 0]);
  const E = Object.fromEntries(D.events.map((e) => [e.id, {s: e.f_start, l: e.f_land, e: e.f_end}]));
  const head = (f) => {
    const p = NOSE[Math.max(0, Math.min(NOSE.length - 1, f))];
    return [(p[0] - mean[0]) * SC * HEAD, (p[1] - mean[1]) * SC * HEAD];
  };
  return {E, head};
};

export const OnCamFrame = ({D, f, wav, children}) => {
  let clip = D.clips[0];
  for (const c of D.clips) if (f >= c.cut) clip = c;
  const k = Math.max(0, Math.min(clip.n - 1, f - clip.off));
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile(wav)} />
      <Img src={staticFile("bg.jpg")} style={{position: "absolute", width: 1920, height: 1080}} />
      <AbsoluteFill style={{background: "linear-gradient(90deg, rgba(237,233,223,0.0) 0%, rgba(237,233,223,0.42) 62%, rgba(237,233,223,0.6) 100%)"}} />
      <Img src={staticFile(`person_${clip.seg}/${String(k).padStart(4, "0")}.png`)} style={{position: "absolute", left: PX, top: PY, width: 1728, height: 972, WebkitMaskImage: EDGE, maskImage: EDGE}} />
      {children}
    </AbsoluteFill>
  );
};

// 手在卡片前面（opt-in）：人物逐帧图再画一层，只留 x ≥ x0 - 24 的部分（多留 24 px 盖住跟头位移后的卡片描边），放在讲解卡之后。
// 人的身体到不了卡片，伸进卡片的只有手，所以这一层只是把手放回卡片前面（审片 11-19：卡片不许盖住手）。
export const PersonFront = ({D, f, x0}) => {
  let clip = D.clips[0];
  for (const c of D.clips) if (f >= c.cut) clip = c;
  const k = Math.max(0, Math.min(clip.n - 1, f - clip.off));
  return (
    <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, clipPath: `inset(0 0 0 ${x0 - 24}px)`}}>
      <Img src={staticFile(`person_${clip.seg}/${String(k).padStart(4, "0")}.png`)} style={{position: "absolute", left: PX, top: PY, width: 1728, height: 972, WebkitMaskImage: EDGE, maskImage: EDGE}} />
    </div>
  );
};
