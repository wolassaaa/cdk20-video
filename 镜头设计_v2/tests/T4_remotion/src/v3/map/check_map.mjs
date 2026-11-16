// HKBU SCIE1007 课程作业的科普视频：核对 Remotion 侧读到的帧号和总表一致（mapTable.mjs 的 wf/event/progress）。
// 用法：node src/v3/map/check_map.mjs 2-03   → 退出码 0 = 全对
import fs from "fs";
import path from "path";
import {fileURLToPath} from "url";
import {wf, event, progress, sustain} from "./mapTable.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const g = process.argv[2] || "2-03";
const T = JSON.parse(fs.readFileSync(path.join(here, "table", `${g.replace("+", "_")}.json`), "utf-8"));
const master = JSON.parse(fs.readFileSync(path.join(here, "../../../../../../镜头设计_v3/映射/master_v1.json"), "utf-8"));
const M = master.groups.find((x) => x.group === g);
let bad = 0;
for (const w of M.words) if (wf(T, w.wid) !== w.f0) { bad++; console.log("词不一致", w.wid); }
for (const e of M.events) {
  const r = event(T, e.eid);
  if (r.f_start !== e.f_start || r.f_land !== e.f_land || r.f_end !== e.f_end) { bad++; console.log("事件不一致", e.eid); }
  if (progress(r, e.f_start) !== 0 || progress(r, e.f_land) !== 1) { bad++; console.log("progress 端点不对", e.eid); }
  if (e.f_end > e.f_land && (sustain(r, e.f_land) !== 0 || sustain(r, e.f_end) !== 1)) { bad++; console.log("sustain 端点不对", e.eid); }
}
console.log(JSON.stringify({group: g, words: M.words.length, events: M.events.length, mismatches: bad}));
process.exit(bad ? 1 : 0);
