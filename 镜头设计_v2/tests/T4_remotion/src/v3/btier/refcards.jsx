// HKBU SCIE1007 课程作业的科普视频：B 页占位返修（交接_B页占位返修_1123）新增的共用小件；bkit.jsx 不动，放这里。
import React from "react";
import {C, Slab, Engrave} from "./bkit.jsx";

// 11-23 B 页占位返修（P02/P04）：2-06、2-07 共用的六张文献卡，两行字（作者 32 px ink，期刊年份 30 px 灰），文字照 credits_v10.json
export const REFS = [
  ["Feng et al.", "J. Clin. Invest., 2011"],
  ["Jumper et al. (AlphaFold)", "Nature, 2021"],
  ["Ivanenkov et al. (Chemistry42)", "J. Chem. Inf. Model., 2023"],
  ["Wang et al.", "Pharmaceuticals, 2023"],
  ["Lengauer (ed.)", "Bioinformatics, Wiley-VCH, 2007"],
  ["Bender et al.", "Nat. Rev. Drug Discov., 2026"],
];
export const RefCard = ({x, y, w, h, ref2, op = 1, id, depth = 8, s1 = 32, s2 = 30, sheen = -1, children}) => (
  <Slab x={x} y={y} w={w} h={h} r={14} color={C.bone} depth={depth} op={op} id={id} sheen={sheen}>
    <div style={{width: w, height: h, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6, boxSizing: "border-box"}}>
      <Engrave size={s1}>{ref2[0]}</Engrave>
      <Engrave size={s2} color={C.grey}>{ref2[1]}</Engrave>
    </div>
    {children}
  </Slab>
);
