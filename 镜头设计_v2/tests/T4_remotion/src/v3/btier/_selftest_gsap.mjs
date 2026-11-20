// HKBU SCIE1007 课程作业的科普视频：B 档套件自检——GSAP 在 node 里对普通对象逐帧寻址（不碰 DOM），乱序 seek 结果一致。
import {gsap, MotionPathPlugin} from "gsap/all";
gsap.registerPlugin(MotionPathPlugin);
const S = {x: 0, y: 0, a: 0};
const tl = gsap.timeline({paused: true});
tl.fromTo(S, {a: 0}, {a: 1, duration: 0.3, ease: "back.out(1.6)"}, 0.1);
tl.to(S, {motionPath: {path: "M0,0 C100,0 200,100 300,100"}, duration: 1, ease: "none"}, 0.2);
const out = {};
for (const t of [0.5, 0.1, 0.25, 1.3, 0.7, 0.5]) { tl.seek(t, true); const v = `${S.a.toFixed(3)} ${S.x.toFixed(1)} ${S.y.toFixed(1)}`; if (out[t] && out[t] !== v) throw new Error("seek 不一致 " + t); out[t] = v; console.log(t, v); }
console.log("OK");
