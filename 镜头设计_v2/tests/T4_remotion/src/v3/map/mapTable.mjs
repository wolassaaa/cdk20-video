// HKBU SCIE1007 课程作业的科普视频：Remotion 读总表（映射/master_v1.json 经 映射/export_remotion.py 转出的 table/<段>.json）。
// 帧号都是段内 60 fps 帧；组件用 useCurrentFrame() 的帧直接比，不写死任何时间。
// 纯函数，不依赖 React，node 里也能跑（check_map.mjs 用它核对）。

export const word = (T, wid) => {
  const w = T.words.find((x) => x.wid === wid);
  if (!w) throw new Error(`${T.group}: 没有词 ${wid}`);
  return w;
};

// 'only#2' 这种 key，或 wid
export const wf = (T, k) => (T.words.find((x) => x.wid === k || x.key === k) || word(T, k)).f0;

export const event = (T, eid) => {
  const e = T.events.find((x) => x.eid === eid);
  if (!e) throw new Error(`${T.group}: 没有事件 ${eid}`);
  return e;
};

// 0 → 1：f_start 起动，f_land 到位（落点 = 词开口）；ease 可传 remotion 的 Easing
export const progress = (e, f, ease = (x) => x) => {
  if (f <= e.f_start) return 0;
  if (f >= e.f_land) return 1;
  return ease((f - e.f_start) / Math.max(1, e.f_land - e.f_start));
};

// 持续段：f_land → f_end 的 0 → 1（"持续到哪个词 / 句尾"）
export const sustain = (e, f, ease = (x) => x) => {
  if (f <= e.f_land) return 0;
  if (f >= e.f_end) return 1;
  return ease((f - e.f_land) / Math.max(1, e.f_end - e.f_land));
};

export const active = (e, f) => f >= e.f_start && f <= Math.max(e.f_land, e.f_end);
