// HKBU SCIE1007 coursework science video. W3 (09:34-09:50, 15.87 s, no speech): the music window between 4-09 and 4-10, over Blender shot w3 (bl_inserts.py).
// It picks up 4-09's overlay as it ends and keeps only what the picture still shows: the predicted tag and the source lines, since the lock's outline and its blue
// Met84 dot are the AlphaFold DB v6 model's. No captions: segment C of the song (bar 104 on) is not sung (音乐/W3 notes), and captions go only where it is sung.
// Kept apart from entry.jsx so the 4K finishing script that bundles entry.jsx is not touched.
// Render: npx remotion bundle src/v3/fusion/w3.jsx --out-dir=<dir> --public-dir=<镜头设计_v3/remotion_public>, then render W3 (test, 30 fps) or W3-4K (--scale=2).
import React from "react";
import {registerRoot, Composition, AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";

const W = 1920, H = 1080;
const INK = "#111113", SOFT = "#545458", BONE = "#EDEBE4";
const SANS = "Inter Tight";
const faces = [new FontFace(SANS, `url(${staticFile("fusion_s1/fonts/InterTight.ttf")})`, {weight: "100 900"})];
const fontHandle = delayRender("fonts");
Promise.all(faces.map(f => f.load())).then(l => { l.forEach(f => document.fonts.add(f)); continueRender(fontHandle); });
const ruler = document.createElement("canvas").getContext("2d");

const clamp = x => Math.min(1, Math.max(0, x));
const smooth = x => { x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10); };
const after = (t, a, d = 0.3) => smooth((t - a) / d);
const BEAT = 60 / 121, BAR = 4 * BEAT;

const W3 = ({file = "fusion_s1/w3_test_1.mp4", fps = 30, review = true}) => {
  const t = useCurrentFrame() / fps;
  ruler.font = `600 28px "${SANS}"`;
  const tagW = ruler.measureText("AlphaFold DB v6 · predicted").width;
  return <AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <g opacity={1 - after(t, 0.1, 0.5)}><text x={1856} y={92} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK} textAnchor="end">Objective 1 / Tool: generative design</text></g>
      <circle cx={W - 72 - tagW - 26} cy={986 - 10} r={14} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5"/>
      <text x={W - 72} y={986} fontFamily={SANS} fontSize={28} fontWeight={600} fill={INK} textAnchor="end">AlphaFold DB v6 · predicted</text>
      <text x={W - 72} y={1024} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">Illustration · pocket and hinge Met84: Ren 2023</text>
      <g opacity={1 - after(t, 0.3, 0.5)}><text x={W - 72} y={1054} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">filters: Ivanenkov 2023 · structure AlphaFold DB v6</text></g>
      <g opacity={after(t, 0.5, 0.5)}><text x={W - 72} y={1054} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">lock and keys drawn · structure AlphaFold DB v6</text></g>
      {review && <text x={64} y={1018} fontFamily={SANS} fontSize={24} fontWeight={500} fill={SOFT}>W3 · Take My Breath from bar 104 · bar {1 + Math.min(7, Math.floor(t / BAR))} of 8 · not sung here, no captions</text>}
    </svg>
  </AbsoluteFill>;
};

const Root = () => <>
  <Composition id="W3" component={W3} durationInFrames={476} fps={30} width={W} height={H}/>
  <Composition id="W3-4K" component={W3} durationInFrames={952} fps={60} width={W} height={H} defaultProps={{file: "fusion_s1/w3_4k.mp4", fps: 60, review: false}}/>
</>;
registerRoot(Root);
