// HKBU SCIE1007 课程作业的科普视频：B 档页面的 GSAP 逐帧寻址（11_铺开排序.md 5.4）。
// 规则：时间线一律 paused，每帧用 useCurrentFrame() 驱动 seek(frame / fps)；不自动播放，不用 CSS transition / animation，不用没种子的随机数。
// GSAP 只补间普通对象（状态表 S），不碰 DOM：Remotion 多个标签页乱序渲帧时，每帧都由 seek 重新算出，结果和渲染顺序无关。
// 时间一律用帧写，进时间线时除以 FPS；所有起点从事件表（keys_<段>.json）读，页面里不写死帧号。
import {useMemo} from "react";
import {useCurrentFrame} from "remotion";
import {gsap} from "gsap";

export const FPS = 60;
export const sec = (f) => f / FPS;

// 只用纯函数缓动，GSAP 自带的 ease 名字都能用
gsap.config({nullTargetWarn: false});

// build(tl, S, X)：往暂停的时间线里加补间，S 是状态表（初值在 build 里写），X 是帧制辅助函数（见下）。
// 返回当前帧的 S（只读）。deps 变了才重建（一般不用传）。
export function useGsapTimeline(build, deps = []) {
  const frame = useCurrentFrame();
  const ref = useMemo(() => {
    const S = {};
    const tl = gsap.timeline({paused: true, defaults: {ease: "power2.inOut"}});
    build(tl, S, helpers(tl, S));
    tl.seek(0, true);
    return {tl, S};
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  ref.tl.seek(frame / FPS, true);
  return ref.S;
}

// 帧制辅助：统一的缓动和时长（11_铺开排序.md 5.4 的表）
export const RULE = {
  antic: 6,          // 预备：主动作前 6 帧，反方向走行程的 8%
  anticAmt: 0.08,
  land: 18,          // 落位：18 帧 back.out(1.6)，过冲约 9%，只回弹一次
  landEase: "back.out(1.6)",
  cross: 7,          // back.out(1.6) 在第 0.385 × 18 ≈ 7 帧第一次到达终点：主动作从 词帧 − 7 起，词开口时刚好到位
  stagger: 4,        // 一组东西依次出现，每个错开 4 帧
  word: 3,           // 标签按词拆，每词错开 3 帧
  rise: 12,          // 标签字上移 12 px 淡入
  pen: [24, 36],     // 手写批注描出 24–36 帧
  secondary: 6,      // 次级动作在主动作落位后 6 帧内，幅度 ≤ 3 px
  idle: 150,         // 相邻两个事件间隔不超过 2.5 秒（150 帧）
};

export const helpers = (tl, S) => {
  const put = (key, v) => { if (!(key in S)) S[key] = v; };
  // 普通补间：key 从 a 到 b，f0 → f1（帧）
  const tw = (key, a, b, f0, f1, ease = "power2.inOut") => {
    put(key, a);
    tl.fromTo(S, {[key]: a}, {[key]: b, duration: Math.max(1, f1 - f0) / FPS, ease, immediateRender: false}, f0 / FPS);
  };
  // 落位：预备 6 帧反向 8% → 18 帧 back.out(1.6)，第一次到达终点的那一帧 = fLand（词开口）
  const land = (key, a, b, fLand, {antic = true, dur = RULE.land, ease = RULE.landEase} = {}) => {
    put(key, a);
    const f0 = fLand - RULE.cross;
    if (antic) {
      const back = a - (b - a) * RULE.anticAmt;
      tl.fromTo(S, {[key]: a}, {[key]: back, duration: RULE.antic / FPS, ease: "power1.inOut", immediateRender: false}, (f0 - RULE.antic) / FPS);
      tl.fromTo(S, {[key]: back}, {[key]: b, duration: dur / FPS, ease, immediateRender: false}, f0 / FPS);
    } else {
      tl.fromTo(S, {[key]: a}, {[key]: b, duration: dur / FPS, ease, immediateRender: false}, f0 / FPS);
    }
  };
  // 次级动作：落位后 delay 帧内一个衰减的小抖（幅度 amp px，两次以内），key 是一个偏移量（平时 0）
  const jiggle = (key, fLand, amp = 3, delay = 4) => {
    put(key, 0);
    const f0 = fLand + delay;
    tl.fromTo(S, {[key]: 0}, {[key]: amp, duration: 3 / FPS, ease: "power1.out", immediateRender: false}, f0 / FPS);
    tl.to(S, {[key]: -amp * 0.45, duration: 4 / FPS, ease: "power1.inOut"}, (f0 + 3) / FPS);
    tl.to(S, {[key]: 0, duration: 5 / FPS, ease: "power1.out"}, (f0 + 7) / FPS);
  };
  // 计数轮：值从 a 滚到 b，停的那一帧 = fStop（词开口）
  const count = (key, a, b, fStop, dur = 36, ease = "power3.out") => {
    put(key, a);
    tl.fromTo(S, {[key]: a}, {[key]: b, duration: dur / FPS, ease, immediateRender: false}, (fStop - dur) / FPS);
  };
  // 一组依次：keys[i] 从 a 到 b，第 i 个在 fLand + i × 4 帧落位
  const group = (keys, a, b, fLand, opts = {}) => keys.forEach((k, i) => land(k, a, b, fLand + i * (opts.step ?? RULE.stagger), opts));
  return {put, tw, land, jiggle, count, group};
};

// 待机微动（每个零件登记一个）：慢转 ±2°、上下浮 2 px，周期按种子错开。纯函数，帧决定一切。
export const idle = (f, seed = 0, {rot = 2, bob = 2, period = 300} = {}) => {
  const ph = seed * 1.7;
  return {r: rot * Math.sin((2 * Math.PI * f) / period + ph), y: bob * Math.sin((2 * Math.PI * f) / (period * 0.77) + ph * 1.3)};
};

// 有种子的伪随机（不许用 Math.random）
export const rand = (seed) => {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};
