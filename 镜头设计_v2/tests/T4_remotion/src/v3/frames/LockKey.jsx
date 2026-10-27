// V3-LockKey: hand-drawn CDK20 "lock" with the real 048 skeleton sitting in its pocket as the "key".
import React from "react";
import {C, W, H} from "../core";
import {HandArrow, HandCircle, Highlight, ScanBox} from "../marks";
import {HandText, Mono, DataTag} from "../type";
import {Stage, InkDefs, Dust} from "../texture";
import {Chrome} from "../chrome";
import {InkMolecule, M048, NEW_048, molPoints, pocketPoints} from "../molecule";
import {ProteinLock} from "../protein";

export const LOCK = {cx: 1240, cy: 560, rx: 520, ry: 365};
export const KEY = {x: 1010, y: 590, scale: 62};
export const LOCK_RIBBONS = [
  {kind: "helix", a: [830, 430], b: [985, 262], turns: 6, amp: 24},
  {kind: "loop", pts: [[985, 262], [1090, 236], [1210, 296], [1330, 268]]},
  {kind: "helix", a: [1330, 268], b: [1590, 380], turns: 6, amp: 24},
  {kind: "loop", pts: [[1590, 380], [1665, 470], [1615, 560], [1500, 600]]},
  {kind: "strand", a: [1450, 700], b: [1660, 640], w: 26},
  {kind: "strand", a: [1650, 720], b: [1440, 780], w: 26},
  {kind: "strand", a: [1450, 850], b: [1640, 790], w: 26},
  {kind: "helix", a: [850, 770], b: [1030, 905], turns: 5, amp: 24},
  {kind: "loop", pts: [[1030, 905], [1160, 885], [1310, 860], [1440, 780]]},
];

export const V3LockKey = () => {
  const P = molPoints(M048, KEY.x, KEY.y, KEY.scale);
  const pocket = pocketPoints(M048, P);
  const pyr = M048.newAtoms.map(i => P[i]);
  const pc = pyr.reduce((s, p) => [s[0] + p[0] / pyr.length, s[1] + p[1] / pyr.length], [0, 0]);
  return <Stage>
    <svg width={W} height={H} style={{position: "absolute"}}>
      <InkDefs/>
      <g filter="url(#v3-ink)">
        <ProteinLock {...LOCK} pocket={pocket} pocketR={52} ribbons={LOCK_RIBBONS}/>
      </g>
      <g filter="url(#v3-ink)">
        <InkMolecule mol={M048} {...KEY} seed={48} tint={i => NEW_048.has(i) ? C.cyan : C.ink} size={8}/>
        <HandCircle cx={pc[0] + 14} cy={pc[1] + 4} rx={118} ry={100} size={6} color={C.cyan} seed={9} rot={0.2}/>
      </g>
      {/* pyrazole callout */}
      <line x1={pc[0] + 60} y1={pc[1] - 60} x2={pc[0] + 150} y2={pc[1] - 150} stroke={C.cyan} strokeWidth={2}/>
      <rect x={pc[0] + 150} y={pc[1] - 186} width={300} height={56} fill={C.bg}/>
      <Mono x={pc[0] + 162} y={pc[1] - 162} size={18} weight={700} color={C.cyan}>+ PYRAZOLE</Mono>
      <Mono x={pc[0] + 162} y={pc[1] - 139} size={15} color={C.cyan}>added in round 2</Mono>

      {/* left column */}
      <Mono x={120} y={200} size={20} weight={700} color={C.cyan} letterSpacing={5}>LOCK & KEY · SCHEMATIC</Mono>
      <HandText x={112} y={340} size={150} seed={4} split={5}>IT FITS.</HandText>
      <DataTag x={124} y={520} label="BINDS · Kd" value="566.7" unit="nM" size={58}/>
      <DataTag x={124} y={690} label="BLOCKS THE ENZYME · IC50" value="33.4" unit="nM" size={58} hl={1} seed={12}/>
      <Mono x={124} y={740} size={16} color={C.dim}>nM = nanomolar · lower = stronger</Mono>

      <HandText x={112} y={930} size={150} seed={6}>048</HandText>
      <Mono x={124} y={972} size={18} color={C.dim} letterSpacing={2}>THE KEY · DESIGNED BY AI</Mono>
      <g filter="url(#v3-ink)">
        <HandArrow from={[400, 870]} to={[P[0][0] - 20, P[0][1] + 40]} bend={0.25} size={7} head={28} seed={14}/>
      </g>

      {/* the lock label */}
      <HandText x={1500} y={176} size={104} seed={8} color={C.verm}>CDK20</HandText>
      <Mono x={1506} y={212} size={17} color={C.dim} letterSpacing={2}>THE LOCK · A KINASE</Mono>
      <g filter="url(#v3-ink)">
        <HandArrow from={[1480, 150]} to={[1330, 222]} bend={0.35} size={6} head={22} seed={16}/>
      </g>
      <Dust/>
      <Chrome fig="02"/>
    </svg>
  </Stage>;
};
