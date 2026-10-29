// 1-04 (00:31-00:52, D VO): treatment switch -> "~3 in 10" 5-year relative survival -> huge unmet need.
// Five options, three key frames each (part a = switch, b = survival, c = unmet need). Script v3.3 wording.
import React from "react";
import {AbsoluteFill, Img, staticFile} from "remotion";
import {W, H} from "../../core";
import {K, T, M, GROT, SERIF, Tags, Print, FieldDefs} from "./common";

const SW_OLD = "Nexavar", SW_NEW = "atezolizumab + bevacizumab", SW_CTX = "(first-line, advanced HCC)";
const SV_A = "5-year relative survival", SV_B = "~3 in 10", SV_C = "(HK, 2010-2021)";
const SRC_SV = "HKCaR 2022 LIVER FACTSHEET (HOSPITAL AUTHORITY, OCT 2024) · HKCaR 2023 OVERVIEW";
const SRC_R23 = "R23 · TARGET SELECTION AND IDENTIFICATION";
const LIT = [1, 4, 8];

const Svg = ({children, style}) => <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0, ...style}}>{children}</svg>;
const Bg = ({src, op = 1, filter}) => <Img src={staticFile(src)} style={{position: "absolute", width: W, height: H, opacity: op, filter}}/>;

// ---------------------------------------------------------------- opt1 glass-row (Blender Cycles + type)
const O1 = ({part}) => <AbsoluteFill style={{background: K.bg}}>
  {part === "a" ? <>
    <Bg src="vials_low_empty.png" op={0.55} filter="blur(3px)"/>
    <Svg>
      <M x={120} y={250} size={16} color={K.dim} ls={4}>{SW_CTX}</M>
      <T x={116} y={360} size={84} w={200} color={K.dim}>{SW_OLD}</T>
      <line x1={112} y1={332} x2={470} y2={332} stroke={K.ink} strokeWidth={2} opacity={0.7}/>
      <T x={116} y={470} size={60} w={200} color={K.ink}>→</T>
      <T x={116} y={580} size={104} w={500} color={K.ink} ls={-2}>{SW_NEW}</T>
      <Tags illustrative opt="opt1 glass-row"/>
    </Svg></> : null}
  {part === "b" ? <>
    <Bg src="vials_row.png" filter="saturate(1.25) contrast(1.05)"/>
    <Svg>
      <T x={300} y={905} size={150} w={700} color={K.ink} ls={-4}><tspan fill={K.verm}>~3</tspan> in 10</T>
      <M x={306} y={970} size={20} color={K.ink} ls={3}>{SV_A}</M>
      <M x={306} y={1004} size={16} color={K.dim} ls={3}>{SV_C}</M>
      <Tags illustrative source={SRC_SV} opt="opt1 glass-row"/>
    </Svg></> : null}
  {part === "c" ? <>
    <Bg src="vials_low.png" filter="saturate(1.25) contrast(1.05)"/>
    <AbsoluteFill style={{background: "linear-gradient(90deg, rgba(6,6,6,0) 45%, rgba(6,6,6,0.75) 85%)"}}/>
    <Svg>
      <T x={1820} y={300} size={30} w={300} anchor="end" color={K.dim}>The study we follow calls it</T>
      <T x={1820} y={420} size={116} w={200} anchor="end" color={K.ink} font={SERIF} style={{fontStyle: "italic"}}>a huge</T>
      <T x={1820} y={540} size={116} w={200} anchor="end" color={K.ink} font={SERIF} style={{fontStyle: "italic"}}>unmet need.</T>
      <Tags illustrative source={SRC_R23} opt="opt1 glass-row"/>
    </Svg></> : null}
  <Print grain={0.2} dark={0.25} band={0.06} vignette={0.35}/>
</AbsoluteFill>;

const Switch = ({x = 116, y = 250, big = 104, color = K.ink, dim = K.dim}) => <g>
  <M x={x + 4} y={y} size={16} color={dim} ls={4}>{SW_CTX}</M>
  <T x={x} y={y + 110} size={big * 0.8} w={200} color={dim}>{SW_OLD}</T>
  <line x1={x - 4} y1={y + 82} x2={x + big * 3.3} y2={y + 82} stroke={color} strokeWidth={2} opacity={0.7}/>
  <T x={x} y={y + 220} size={big * 0.58} w={200} color={color}>→</T>
  <T x={x} y={y + 330} size={big} w={500} color={color} ls={-2}>{SW_NEW}</T>
</g>;
const Survival = ({x, y, size = 150, anchor = "start", color = K.ink, ms = 20, mls = 3}) => <g>
  <T x={x} y={y} size={size} w={700} anchor={anchor} color={color} ls={-4}><tspan fill={K.verm}>~3</tspan> in 10</T>
  <M x={x + 6} y={y + size * 0.43} size={ms} color={color} ls={mls} anchor={anchor}>{SV_A}</M>
  <M x={x + 6} y={y + size * 0.43 + ms * 1.6} size={ms * 0.8} color={K.dim} ls={mls} anchor={anchor}>{SV_C}</M>
</g>;
const Unmet = ({x, y, size = 116, anchor = "end", color = K.ink}) => <g>
  <T x={x} y={y} size={30} w={300} anchor={anchor} color={K.dim}>The study we follow calls it</T>
  <T x={x} y={y + 120} size={size} w={200} anchor={anchor} color={color} font={SERIF} style={{fontStyle: "italic"}}>a huge</T>
  <T x={x} y={y + 120 + size} size={size} w={200} anchor={anchor} color={color} font={SERIF} style={{fontStyle: "italic"}}>unmet need.</T>
</g>;

// ---------------------------------------------------------------- opt2 pigment-field (Blender: dry pigment bed split 3:7, vermilion | IKB)
const O2 = ({part, v}) => <AbsoluteFill style={{background: K.bg}}>
  {part === "a" && !v ? <Bg src="pigment_top.png" op={0.4} filter="blur(6px)"/> : null}
  {part === "a" && v ? <Bg src="pigment_a_v2.png"/> : null}
  {part === "b" ? <Bg src="pigment_b.png"/> : null}
  {part === "c" ? <Bg src="pigment_c.png"/> : null}
  {part === "c" ? <AbsoluteFill style={{background: "linear-gradient(180deg, rgba(6,6,6,0.85) 0%, rgba(6,6,6,0) 45%)"}}/> : null}
  <Svg>
    {part === "a" && !v ? <Switch/> : null}
    {part === "a" && v ? <g>
      <M x={114} y={110} size={16} color={K.dim} ls={4}>{SW_CTX}</M>
      <T x={110} y={200} size={64} w={200} color={K.ink} op={0.28}>{SW_OLD}</T>
      <T x={110} y={300} size={84} w={500} color={K.ink} ls={-2}>atezolizumab</T>
      <T x={110} y={392} size={84} w={500} color={K.ink} ls={-2}><tspan fontWeight={200} fill={K.dim}>+ </tspan>bevacizumab</T>
    </g> : null}
    {part === "b" ? <Survival x={116} y={230} size={130}/> : null}
    {part === "c" ? <Unmet x={1820} y={120} size={100}/> : null}
    <Tags illustrative={part !== "a"} source={part === "b" ? SRC_SV : part === "c" ? SRC_R23 : null} opt="opt2 pigment-field"/>
  </Svg>
  <Print grain={0.2} dark={0.25} band={0.05} vignette={0.3}/>
</AbsoluteFill>;

// ---------------------------------------------------------------- opt3 ten-beams (Blender volumetrics: ten shafts of light in haze)
const O3 = ({part}) => <AbsoluteFill style={{background: K.bg}}>
  <Bg src={`beams_${part}.png`} op={part === "a" ? 0.55 : 1}/>
  {part === "c" ? <AbsoluteFill style={{background: "linear-gradient(270deg, rgba(6,6,6,0.9) 10%, rgba(6,6,6,0) 55%)"}}/> : null}
  <Svg>
    {part === "a" ? <Switch x={116} y={300}/> : null}
    {part === "b" ? <Survival x={1870} y={150} size={92} anchor="end" ms={16} mls={1.5}/> : null}
    {part === "c" ? <Unmet x={1820} y={300} size={110}/> : null}
    <Tags illustrative={part !== "a"} source={part === "b" ? SRC_SV : part === "c" ? SRC_R23 : null} opt="opt3 ten-beams"/>
  </Svg>
  <Print grain={0.2} dark={0.25} band={0.05} vignette={0.3}/>
</AbsoluteFill>;

// ---------------------------------------------------------------- opt4 fog-glass (Blender: frosted pane, finger-wiped strokes, neon behind)
const O4 = ({part, v}) => <AbsoluteFill style={{background: K.bg}}>
  <Bg src={`fog_${part}${v ? "_v2" : ""}.png`}/>
  <Svg>
    {part === "a" ? <M x={216} y={800} size={18} color={K.ink} ls={4} op={0.75}>{SW_CTX}</M> : null}
    {part === "b" ? <Survival x={80} y={150} size={96}/> : null}
    {part === "c" ? <T x={W / 2} y={1010} size={64} w={200} anchor="middle" color={K.ink} font={SERIF} style={{fontStyle: "italic"}}>a huge unmet need.</T> : null}
    <Tags illustrative={part !== "a"} source={part === "b" ? SRC_SV : part === "c" ? SRC_R23 : null} opt="opt4 fog-glass"/>
  </Svg>
  <Print grain={0.18} dark={0.22} band={0.04} vignette={0.3}/>
</AbsoluteFill>;

// ---------------------------------------------------------------- opt5 numeral (gallery poster: halftone numerals, misregistered plates)
const DotPat = ({id, color, cell = 13, r = 5.2, angle = 18}) =>
  <pattern id={id} width={cell} height={cell} patternUnits="userSpaceOnUse" patternTransform={`rotate(${angle})`}>
    <circle cx={cell / 2} cy={cell / 2} r={r} fill={color}/>
  </pattern>;
const O5 = ({part}) => <AbsoluteFill style={{background: K.bg}}>
  <Svg>
    <defs>
      <DotPat id="dv" color={K.verm}/>
      <DotPat id="db" color={K.blue} cell={11} r={3.6} angle={-24}/>
    </defs>
    <FieldDefs id="f5" seed={11} scale={6}/>
    {part === "a" ? <g filter="url(#f5)">
      <T x={-30} y={500} size={430} w={800} color="none" stroke={K.ink} strokeWidth={2.5} ls={-18} op={0.55}>{SW_OLD}</T>
      <rect x={-40} y={330} width={W + 80} height={9} fill={K.ink}/>
      <T x={1856} y={760} size={96} w={700} anchor="end" color={K.ink} ls={-3}>{SW_NEW}</T>
      <M x={1856} y={820} size={18} anchor="end" color={K.dim} ls={4}>{SW_CTX}</M>
    </g> : null}
    {part === "b" ? <g>
      <g filter="url(#f5)">
        <T x={1880} y={990} size={600} w={800} anchor="end" color="none" stroke={K.blue} strokeWidth={4} ls={-30}>10</T>
        <T x={1880} y={990} size={600} w={800} anchor="end" color="url(#db)" ls={-30} op={0.55}>10</T>
        <line x1={760} y1={1000} x2={1080} y2={160} stroke={K.blue} strokeWidth={14}/>
        <T x={92} y={990} size={1000} w={800} color={K.verm} op={0.9} ls={-40} style={{mixBlendMode: "screen"}}>3</T>
        <T x={80} y={980} size={1000} w={800} color="url(#dv)" ls={-40}>3</T>
        <T x={40} y={420} size={260} w={300} color={K.verm}>~</T>
      </g>
      <M x={1100} y={120} size={20} color={K.ink} ls={4} w={700}>{SV_A.toUpperCase()}</M>
      <M x={1100} y={156} size={20} color={K.ink} ls={4}>{SV_B} {SV_C}</M>
    </g> : null}
    {part === "c" ? <g>
      <g filter="url(#f5)">
        <T x={-40} y={600} size={560} w={800} color="url(#db)" ls={-30}>UNMET</T>
        <T x={-40} y={600} size={560} w={800} color="none" stroke={K.blue} strokeWidth={3} ls={-30}>UNMET</T>
        <T x={W + 40} y={1060} size={420} w={800} anchor="end" color={K.ink} ls={-20}>need</T>
      </g>
      <M x={64} y={120} size={20} color={K.ink} ls={4}>THE STUDY WE FOLLOW CALLS IT A HUGE UNMET NEED.</M>
    </g> : null}
    <Tags illustrative={false} source={part === "b" ? SRC_SV : part === "c" ? SRC_R23 : null} opt="opt5 numeral"/>
  </Svg>
  <Print grain={0.36} dark={0.45} band={0.14} vignette={0.3}/>
</AbsoluteFill>;

export const OPTIONS_104 = [
  {id: "O1", C: O1, slug: "opt1_glass-row"},
  {id: "O2", C: O2, slug: "opt2_pigment-field"},
  {id: "O3", C: O3, slug: "opt3_ten-beams"},
  {id: "O4", C: O4, slug: "opt4_fog-glass"},
  {id: "O5", C: O5, slug: "opt5_numeral"},
];
