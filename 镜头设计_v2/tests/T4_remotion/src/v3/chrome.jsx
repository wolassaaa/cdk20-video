// Frame furniture: the clean, digital layer (registration marks, mono slugs, SMILES strip, frame counter).
import React from "react";
import {useCurrentFrame} from "remotion";
import {C, MONO, W, H} from "./core";
import {Crosshair} from "./marks";
import {M048} from "./molecule";

export const Chrome = ({fig = "01", title = "CDK20 × LIVER CANCER", smiles = true, opacity = 1, counter = true}) => {
  const f = useCurrentFrame();
  const m = 56;
  return <g opacity={opacity}>
    {[[m, m], [W - m, m], [m, H - m], [W - m, H - m]].map(([x, y], i) => <Crosshair key={i} x={x} y={y}/>)}
    <text x={m + 34} y={m + 6} fontFamily={MONO} fontSize={15} fill={C.dim} letterSpacing={2}>HKBU · MOLECULAR SCIENCE</text>
    <text x={m + 34 + 420} y={m + 6} fontFamily={MONO} fontSize={15} fontWeight={700} fill={C.cyan} letterSpacing={2}>FIG.{fig}</text>
    <text x={W - m - 34} y={m + 6} fontFamily={MONO} fontSize={15} fill={C.dim} letterSpacing={2} textAnchor="end">{title}</text>
    {smiles ? <text x={m + 34} y={H - m + 6} fontFamily={MONO} fontSize={13} fill={C.dim} letterSpacing={1}>048 · {M048.smiles}</text> : null}
    {counter ? <text x={W - m - 34} y={H - m + 6} fontFamily={MONO} fontSize={13} fill={C.dim} letterSpacing={2} textAnchor="end">120 BPM · F{String(f).padStart(4, "0")}</text> : null}
  </g>;
};
