// 30-based clock: the S1 modules keep every timing constant in frames at 30 fps, so the same code renders at any composition fps.
// useFrame30() stands in for useCurrentFrame() and counts in those frames: fractional above 30 fps, the plain integer frame at 30.
// Seq30 and toFps() convert for what Remotion counts itself (Sequence, OffthreadVideo startFrom).
// Per-frame assets and seeds floor the clock, so at 60 fps a 30 fps plate holds each of its frames twice until it is re-rendered.
import React from "react";
import {Freeze, Sequence, useCurrentFrame, useVideoConfig} from "remotion";

const BASE = 30;

/** 30-based frames -> real frames at `fps`. */
export const toFps = (n, fps) => Math.round(n * fps / BASE);

/** The current frame, counted at 30 fps. */
export const useFrame30 = () => useCurrentFrame() * BASE / useVideoConfig().fps;

/** Sequence with from and durationInFrames in 30-based frames. The end is rounded on its own, so back-to-back shots stay flush at any fps. */
export const Seq30 = ({from = 0, durationInFrames, ...rest}) => {
  const {fps} = useVideoConfig(), a = toFps(from, fps);
  return <Sequence from={a} durationInFrames={durationInFrames === undefined ? undefined : toFps(from + durationInFrames, fps) - a} {...rest}/>;
};

/** Holds a 30 fps video plate on the 30 fps grid, so it stays in step with per-frame data that floors the clock. Not for 60 fps footage. */
export const Hold30 = ({children}) => {
  const f = useFrame30(), {fps} = useVideoConfig();
  return fps === BASE ? children : <Freeze frame={toFps(Math.floor(f), fps)}>{children}</Freeze>;
};
