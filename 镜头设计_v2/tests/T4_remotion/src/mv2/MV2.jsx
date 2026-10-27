import React from "react";
import {AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame} from "remotion";
import {plan, FPS, SI, C, ANTON, HAND, WorldTiles, clamp01, outCubic, outBack} from "./common";
import {Headline, Glitch, Term, SiClip, Montage, Scores, Numbers} from "./Silicon";
import {CClip, Cells, LockKey, Timeline, Flask, DishScene, Ladder, Verdict, Radio, Credits} from "./Carbon";
import {CloudScene} from "./Cloud";

// v2 5-minute music test, 'Carbon vs Silicon': the computer's world is cool and digital, the body and the lab are
// warm and hand-drawn, and they meet where the AI's molecules are tested on living cells.
// One pre-mixed track (mv_test/build_v2.py) carries the song transitions; every cut sits on a bar.
const KINDS = {headline: Headline, glitch: Glitch, term: Term, siclip: SiClip, montage: Montage, scores: Scores, numbers: Numbers,
  cloud: CloudScene, cclip: CClip, cells: Cells, lockkey: LockKey, timeline: Timeline, flask: Flask, dish: DishScene, ladder: Ladder,
  verdict: Verdict, radio: Radio, credits: Credits};

const Scene = ({s}) => {
  const fl = useCurrentFrame(), local = fl / FPS, t = s.at + local, f = Math.round(t * FPS);
  const K = KINDS[s.kind];
  return <AbsoluteFill>
    <K s={s} t={t} f={f} local={local}/>
    {s.kind !== "radio" ? <WorldTiles world={s.world}/> : null}
  </AbsoluteFill>;
};

// lyric-gist captions: silicon ones pop in as bold type, carbon ones are written on by hand
const Caption = ({c}) => {
  const local = useCurrentFrame() / FPS, dur = c.end - c.at;
  const out = clamp01((dur - local) / 0.2);
  if (c.world === "c") {
    const p = clamp01(local / 0.7);
    return <div style={{position: "absolute", left: 0, right: 0, bottom: 150, textAlign: "center", fontFamily: HAND, fontSize: 96, color: C.amber, opacity: out,
      clipPath: `inset(0 ${100 - p * 100}% 0 0)`, textShadow: "0 2px 30px rgba(0,0,0,0.9)"}}>{c.text}</div>;
  }
  const p = outBack(local / 0.18);
  return <div style={{position: "absolute", left: 0, right: 0, bottom: 150, textAlign: "center", fontFamily: ANTON, fontSize: 104, letterSpacing: 6, color: SI.ink,
    opacity: Math.min(clamp01(local / 0.05), out), transform: `scale(${0.8 + 0.2 * p})`, textShadow: "0 0 40px rgba(127,227,250,0.55), 0 4px 30px rgba(0,0,0,0.9)"}}>{c.text}</div>;
};

export const MV2 = () => (
  <AbsoluteFill style={{background: SI.bg}}>
    <Audio src={staticFile(plan.audio)}/>
    {plan.scenes.map((s, i) => (
      <Sequence key={"s" + i} from={Math.round(s.at * FPS)} durationInFrames={Math.max(1, Math.round((s.at + s.dur) * FPS) - Math.round(s.at * FPS))}>
        <Scene s={s}/>
      </Sequence>
    ))}
    {plan.captions.map((c, i) => (
      <Sequence key={"c" + i} from={Math.round(c.at * FPS)} durationInFrames={Math.max(1, Math.round((c.end - c.at) * FPS))}>
        <Caption c={c}/>
      </Sequence>
    ))}
  </AbsoluteFill>
);

export const MV2_FRAMES = Math.round(plan.duration * FPS);
