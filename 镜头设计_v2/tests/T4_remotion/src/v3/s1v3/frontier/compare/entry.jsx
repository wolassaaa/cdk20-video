// Four frontier tests side by side, in sync, for the director to compare (S1 opening, 10 s each).
import React from "react";
import {AbsoluteFill, Composition, OffthreadVideo, registerRoot, staticFile} from "remotion";

const TESTS = [["test_scan.mp4", "SCAN 断层数据"], ["test_grow.mp4", "GROW 自己长的血管"], ["test_pulse.mp4", "PULSE 1,412 盏灯"], ["test_splat.mp4", "SPLAT 高斯泼溅"]];

const Compare = () => <AbsoluteFill style={{background: "#060606"}}>
  {TESTS.map(([f, label], i) => <div key={f} style={{position: "absolute", left: (i % 2) * 960, top: (i >> 1) * 540, width: 960, height: 540, overflow: "hidden"}}>
    <OffthreadVideo src={staticFile(f)} muted style={{width: 960, height: 540}}/>
    <div style={{position: "absolute", left: 18, top: 14, color: "#EDEBE4", font: "500 20px 'Microsoft YaHei', sans-serif", textShadow: "0 0 6px #000"}}>{label}</div>
  </div>)}
  <div style={{position: "absolute", left: 959, top: 0, width: 2, height: 1080, background: "#2a2a2a"}}/>
  <div style={{position: "absolute", left: 0, top: 539, width: 1920, height: 2, background: "#2a2a2a"}}/>
</AbsoluteFill>;

registerRoot(() => <Composition id="Compare" component={Compare} durationInFrames={300} fps={30} width={1920} height={1080}/>);
