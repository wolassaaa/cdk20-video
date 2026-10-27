import React, {useMemo} from "react";
import {AbsoluteFill, Audio, staticFile, useCurrentFrame, interpolate} from "remotion";
import {ThreeCanvas} from "@remotion/three";
import {useThree} from "@react-three/fiber";
import * as THREE from "three";
import {loadFont as loadMono} from "@remotion/google-fonts/JetBrainsMono";
import {loadFont as loadAnton} from "@remotion/google-fonts/Anton";
import rhythm from "./sacrifice_hook.rhythm.json";
import ligands from "./ligands.json";

// Motion test: 8,918 generated molecules move on the Sacrifice hook's individual hits ("silicon" look).
// kick -> the cloud contracts, strong synth stabs -> snap to a new arrangement, hats -> sparkles, snare -> scan flash.
// Story on the bars: library (1-4) -> latent space (5-8) -> filter 8,918 -> 54 -> 7 (9-12) -> first hit 001 (13-).
const {fontFamily: MONO} = loadMono();
const {fontFamily: ANTON} = loadAnton();
const FPS = rhythm.fps, T0 = rhythm.t0;
export const SAC_FRAMES = Math.floor((rhythm.t1 - T0) * FPS);
const N = 8918, COLS = 98, ROWS = 91; // 98 x 91 = 8,918
const CYAN = "#7FE3FA", ORANGE = "#FF8A4C", INK = "#EEF4F8", QUIET = "#6F8796", BG = "#02060B";
const DB = rhythm.downbeats;
const STABS = rhythm.layers.synth.filter(h => h.s > 0.8).map(h => h.t)
  .filter((t, i, a) => i === 0 || t - a[i - 1] >= 0.12);
const HATS = rhythm.layers.hat.map(h => h.t);
const SNARES = rhythm.layers.snare.filter(h => h.s > 0.5).map(h => h.t);

const clamp01 = x => Math.min(1, Math.max(0, x));
const outCubic = x => 1 - Math.pow(1 - clamp01(x), 3);
const inOut = x => { x = clamp01(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const hash = (a, b = 0) => { let h = Math.imul(a ^ 0x9e3779b9, 0x85ebca6b) ^ Math.imul(b + 0x7f4a7c15, 0xc2b2ae35); h ^= h >>> 15; h = Math.imul(h, 0x2c1b3c6d); h ^= h >>> 12; return (h >>> 0) / 4294967296; };
const countBefore = (arr, t) => { let n = 0; while (n < arr.length && arr[n] <= t) n++; return n; };
const envAt = (k, f) => rhythm.env[k][Math.min(rhythm.env[k].length - 1, Math.max(0, f))];

// counts on the bars; only the paper's numbers are shown
const ALIVE = [[DB[8], 54], [DB[10], 7], [DB[12], 1]];
const aliveAt = t => ALIVE.reduce((n, [at, k]) => (t >= at ? k : n), N);

// soft glowing points, additive
const pointMaterial = () => new THREE.ShaderMaterial({
  transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  vertexShader: `attribute float size; attribute vec3 color; varying vec3 vColor;
    void main(){ vColor = color; vec4 mv = modelViewMatrix * vec4(position,1.0);
      gl_PointSize = size * (900.0 / -mv.z); gl_Position = projectionMatrix * mv; }`,
  fragmentShader: `varying vec3 vColor;
    void main(){ float d = length(gl_PointCoord - 0.5) * 2.0; float a = smoothstep(1.0, 0.0, d);
      a = a * a; gl_FragColor = vec4(vColor * a, a); }`,
});

const Cam = ({pos, look}) => {
  const {camera} = useThree();
  camera.position.set(...pos);
  camera.lookAt(...look);
  camera.updateProjectionMatrix();
  return null;
};

const Cloud = ({t, f}) => {
  const seed = useMemo(() => {
    const grid = new Float32Array(N * 3), cloud = new Float32Array(N * 3), core = new Float32Array(N * 3);
    // rank: who survives (0 = the hit, 1..6 = the rest of the 7, 7..53 = the 54)
    const order = Array.from({length: N}, (_, i) => i).sort((a, b) => hash(a, 7) - hash(b, 7));
    const rank = new Int32Array(N); order.forEach((id, r) => { rank[id] = r; });
    const centers = Array.from({length: 14}, (_, c) => [(hash(c, 1) - 0.5) * 70, (hash(c, 2) - 0.5) * 38, (hash(c, 3) - 0.5) * 50]);
    for (let i = 0; i < N; i++) {
      grid[i * 3] = (i % COLS - (COLS - 1) / 2) * 1.25; grid[i * 3 + 1] = 0; grid[i * 3 + 2] = (Math.floor(i / COLS) - (ROWS - 1) / 2) * 1.25;
      const c = centers[Math.floor(hash(i, 4) * centers.length)], g = () => (hash(i, 5) + hash(i, 6) + hash(i, 8) - 1.5) * 9;
      cloud[i * 3] = c[0] + g(); cloud[i * 3 + 1] = c[1] + (hash(i, 9) + hash(i, 10) - 1) * 9; cloud[i * 3 + 2] = c[2] + (hash(i, 11) + hash(i, 12) - 1) * 9;
      const r = rank[i], a = r * 2.399963, rad = 3 + Math.sqrt(r) * 2.2; // the survivors pack into a golden-angle disc
      core[i * 3] = Math.cos(a) * rad; core[i * 3 + 1] = Math.sin(a) * rad; core[i * 3 + 2] = (hash(i, 13) - 0.5) * 4;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(N * 3), 3));
    geo.setAttribute("color", new THREE.BufferAttribute(new Float32Array(N * 3), 3));
    geo.setAttribute("size", new THREE.BufferAttribute(new Float32Array(N), 1));
    return {grid, cloud, core, rank, geo, mat: pointMaterial()};
  }, []);

  const {grid, cloud, core, rank, geo} = seed;
  const P = geo.attributes.position.array, C = geo.attributes.color.array, S = geo.attributes.size.array;
  const kick = envAt("kick", f), hat = envAt("hat", f);
  const hatIdx = countBefore(HATS, t) - 1;
  const stabN = countBefore(STABS, t), stabEase = stabN ? outCubic((t - STABS[stabN - 1]) / 0.09) : 0;

  // phase weights
  const intro = outCubic((t - T0) / 1.8);
  const toCloud = inOut((t - DB[4]) / 0.5);
  const toCore = inOut((t - DB[8] - 0.25) / 0.9);
  const alive = aliveAt(t);
  const lastCut = ALIVE.filter(([at]) => t >= at).map(([at]) => at).pop() ?? -1;

  // library phase: each strong stab slides every row sideways by a random whole number of columns (wraps)
  const rowShift = r => {
    let s = 0;
    for (let k = 0; k < stabN; k++) {
      if (STABS[k] >= DB[4]) break;
      const d = Math.round((hash(k, r) - 0.5) * 8) * 1.25;
      s += k === stabN - 1 ? d * stabEase : d;
    }
    return s;
  };
  const shifts = Array.from({length: ROWS}, (_, r) => rowShift(r));
  const W = COLS * 1.25;

  for (let i = 0; i < N; i++) {
    const r = Math.floor(i / COLS), rk = rank[i];
    let gx = grid[i * 3] + shifts[r]; gx = ((gx + W / 2) % W + W) % W - W / 2;
    const appear = clamp01(intro * 1.3 - (r / ROWS) * 0.3);
    const gy = (1 - appear) * -20 + kick * 1.6 * Math.sin(i * 0.37 + r);
    let x = gx + (cloud[i * 3] - gx) * toCloud, y = gy + (cloud[i * 3 + 1] - gy) * toCloud, z = grid[i * 3 + 2] + (cloud[i * 3 + 2] - grid[i * 3 + 2]) * toCloud;
    const contract = 1 - 0.09 * kick * toCloud;
    x *= contract; y *= contract; z *= contract;

    let size = 1.05 * appear, cr = 0.5, cg = 0.89, cb = 0.98, bright = 0.55;
    if (rk < 54 && toCore > 0) { x += (core[i * 3] - x) * toCore; y += (core[i * 3 + 1] - y) * toCore; z += (core[i * 3 + 2] - z) * toCore; }
    if (rk >= alive) {
      const since = t - lastCut, fall = since * since * 60 * (0.6 + hash(i, 14));
      y -= fall; x += (hash(i, 15) - 0.5) * since * 30;
      bright *= Math.max(0, 1 - since / 0.9) * (rk < 54 ? 1.6 : 1);
      if (bright <= 0) { size = 0; }
    } else if (t >= DB[8]) {
      const kept = clamp01((t - DB[8]) / 0.3);
      size *= 1 + kept * (rk < 7 && t >= DB[10] ? 9 : 3.5); bright = 0.55 + kept * 0.45;
      cr += (1.0 - cr) * kept; cg += (0.54 - cg) * kept; cb += (0.3 - cb) * kept; // survivors turn warm
    }
    if (rk === 0 && t >= DB[12]) bright *= Math.max(0, 1 - (t - DB[12]) / 0.4); // hands over to the 3D molecule
    if (hash(i, hatIdx + 99) < 0.035) { bright += hat * 1.6; size *= 1 + hat * 0.8; }
    bright += kick * 0.25;
    P[i * 3] = x; P[i * 3 + 1] = y; P[i * 3 + 2] = z;
    C[i * 3] = cr * bright; C[i * 3 + 1] = cg * bright; C[i * 3 + 2] = cb * bright; S[i] = size;
  }
  geo.attributes.position.needsUpdate = true; geo.attributes.color.needsUpdate = true; geo.attributes.size.needsUpdate = true;

  // latent phase: each strong stab snaps the whole cloud round by 28 degrees
  const latentStabs = STABS.filter(s => s >= DB[4] && s <= t);
  const snap = latentStabs.length ? latentStabs.length - 1 + outCubic((t - latentStabs[latentStabs.length - 1]) / 0.09) : 0;
  const rotY = toCloud * (0.25 * (t - DB[4]) + snap * 0.49) * (1 - toCore); // stops once the survivors gather
  return <points geometry={geo} material={seed.mat} rotation={[0, rotY, 0]} frustumCulled={false}/>;
};

// the first hit, 001, as ball-and-stick from our re-docked pose
const ELEMENT = {C: "#7FC4D8", N: "#4C8DFF", O: "#FF6A4C", H: "#FFFFFF"};
const Hero = ({t, f}) => {
  const mol = useMemo(() => {
    const atoms = ligands["001"].atoms.filter(a => a[0] !== "H");
    const keep = ligands["001"].atoms.map((a, i) => (a[0] !== "H" ? i : -1));
    const idx = new Map(keep.filter(i => i >= 0).map((orig, j) => [orig, j]));
    const c = [0, 1, 2].map(k => atoms.reduce((s, a) => s + a[k + 1], 0) / atoms.length);
    let pts = atoms.map(a => new THREE.Vector3(a[1] - c[0], a[2] - c[1], a[3] - c[2]).multiplyScalar(3.2));
    // lay the long axis (the two atoms furthest apart) along screen x so the molecule reads side-on
    let far = [0, 1, 0];
    pts.forEach((p, i) => pts.forEach((q, j) => { const d = p.distanceTo(q); if (d > far[2]) far = [i, j, d]; }));
    const turn = new THREE.Quaternion().setFromUnitVectors(pts[far[1]].clone().sub(pts[far[0]]).normalize(), new THREE.Vector3(1, 0, 0));
    pts = pts.map(p => p.applyQuaternion(turn));
    const bonds = ligands["001"].bonds.filter(([a, b]) => idx.has(a) && idx.has(b)).map(([a, b, o]) => [idx.get(a), idx.get(b), o]);
    return {atoms, pts, bonds};
  }, []);
  const enter = outCubic((t - DB[12]) / 0.6);
  if (enter <= 0) return null;
  const kick = envAt("kick", f), snare = envAt("snare", f);
  const stabs = STABS.filter(s => s >= DB[12] && s <= t);
  const snap = stabs.length ? stabs.length - 1 + outCubic((t - stabs[stabs.length - 1]) / 0.1) : 0;
  const up = new THREE.Vector3(0, 1, 0);
  return (
    <group scale={enter * (1 + 0.06 * kick)} rotation={[snap * 0.55 + (t - DB[12]) * 0.3, 0, 0]}>
      {mol.pts.map((p, i) => (
        <mesh key={"a" + i} position={p}>
          <sphereGeometry args={[mol.atoms[i][0] === "C" ? 1.15 : 1.3, 24, 16]}/>
          <meshStandardMaterial color={ELEMENT[mol.atoms[i][0]]} emissive={ELEMENT[mol.atoms[i][0]]} emissiveIntensity={0.08 + 0.6 * kick} roughness={0.35} metalness={0.1}/>
        </mesh>
      ))}
      {mol.bonds.map(([a, b], i) => {
        const pa = mol.pts[a], pb = mol.pts[b], mid = pa.clone().add(pb).multiplyScalar(0.5);
        const dir = pb.clone().sub(pa), len = dir.length();
        const q = new THREE.Quaternion().setFromUnitVectors(up, dir.normalize());
        return <mesh key={"b" + i} position={mid} quaternion={q}>
          <cylinderGeometry args={[0.32, 0.32, len, 10]}/>
          <meshStandardMaterial color="#9FB8C6" emissive={CYAN} emissiveIntensity={0.15 + 0.8 * snare} roughness={0.5}/>
        </mesh>;
      })}
    </group>
  );
};

// HUD: terminal lines type out on the hats, counter rolls on the cuts, meters show the four layers
const TERM = [
  [T0 + 0.2, "> load AF-Q8IZL9   # AlphaFold model of CDK20"],
  [DB[0], "> chemistry42 generate --pocket atp_site"],
  [DB[2], "  8,918 molecules"],
  [DB[4], "> embed --space latent   # similar ideas sit close"],
  [DB[8], "> score + filter  -> 54"],
  [DB[10], "> synthesize      -> 7"],
  [DB[12], "> assay           -> 001  Kd 9.2 uM  (day 30)"],
];
const Terminal = ({t}) => {
  const shown = TERM.filter(([at]) => t >= at).slice(-6);
  return <div style={{position: "absolute", left: 64, top: 120, width: 760, fontFamily: MONO, fontSize: 24, lineHeight: 1.55, color: CYAN}}>
    {shown.map(([at, text], i) => {
      const typed = countBefore(HATS, t) - countBefore(HATS, at); // hats type the characters
      const n = Math.min(text.length, 4 + typed * 5);
      const live = i === shown.length - 1;
      return <div key={at} style={{opacity: live ? 1 : 0.45, whiteSpace: "pre"}}>{text.slice(0, n)}{live && n < text.length ? "▋" : ""}</div>;
    })}
  </div>;
};

const Meters = ({f}) => (
  <div style={{position: "absolute", right: 64, bottom: 64, display: "flex", gap: 14, alignItems: "flex-end", fontFamily: MONO, fontSize: 15, color: QUIET}}>
    {["kick", "snare", "hat", "synth"].map(k => {
      const v = envAt(k, f);
      return <div key={k} style={{textAlign: "center", width: 54}}>
        <div style={{height: 90, display: "flex", alignItems: "flex-end", justifyContent: "center", borderBottom: `1px solid ${QUIET}`}}>
          <div style={{width: 12, height: 90 * v, background: k === "synth" ? ORANGE : CYAN, boxShadow: `0 0 ${12 * v}px ${CYAN}`}}/>
        </div>
        <div style={{marginTop: 6}}>{k}</div>
      </div>;
    })}
  </div>
);

const Counter = ({t}) => {
  const n = aliveAt(t), lastCut = ALIVE.filter(([at]) => t >= at).map(([at]) => at).pop();
  const flash = lastCut ? Math.exp(-(t - lastCut) * 4) : 0;
  const label = n === 1 ? "001" : n.toLocaleString("en-US");
  return <div style={{position: "absolute", right: 64, top: 96, textAlign: "right", fontFamily: MONO}}>
    <div style={{fontSize: 20, color: QUIET, letterSpacing: 4}}>{n === 1 ? "FIRST HIT" : "CANDIDATES"}</div>
    <div style={{fontSize: 120, fontWeight: 700, color: n < N ? ORANGE : INK, lineHeight: 1, transform: `scale(${1 + 0.12 * flash})`, transformOrigin: "right center",
      textShadow: `0 0 ${40 * flash}px ${ORANGE}`}}>{label}</div>
  </div>;
};

// lyric-gist echo (paraphrase of the song's idea of giving things up), lands on the cut bars
const CAPTIONS = [[DB[8], DB[10], "LET 8,864 GO."], [DB[10], DB[12], "KEEP SEVEN."], [DB[12] + 0.98, rhythm.t1, "ONE IS ENOUGH TO START."]];
const Caption = ({t}) => {
  const c = CAPTIONS.find(([a, b]) => t >= a && t < b);
  if (!c) return null;
  const p = outCubic((t - c[0]) / 0.18);
  return <div style={{position: "absolute", left: 0, right: 0, bottom: 110, textAlign: "center", fontFamily: ANTON, fontSize: 96, letterSpacing: 6, color: INK,
    opacity: p, transform: `translateY(${(1 - p) * 30}px) scale(${1.15 - 0.15 * p})`, textShadow: "0 0 40px rgba(127,227,250,0.5)"}}>{c[2]}</div>;
};

export const SacrificeMolecules = () => {
  const f = useCurrentFrame(), t = T0 + f / FPS;
  const snare = envAt("snare", f), kick = envAt("kick", f);
  // camera: tilted over the library table, pulls round into the cloud, then pushes in on the hit
  const toCloud = inOut((t - DB[4]) / 0.6), toHero = inOut((t - DB[12]) / 1.2);
  const camY = 60 * (1 - toCloud) + 6 * toCloud, camZ = 95 * (1 - toCloud) + 115 * toCloud - 40 * toHero;
  const shake = kick * 0.5;
  // scan line sweeps down on every snare
  const lastSnare = SNARES[countBefore(SNARES, t) - 1];
  const scan = lastSnare !== undefined ? (t - lastSnare) / 0.25 : 9;
  return (
    <AbsoluteFill style={{background: BG}}>
      <Audio src={staticFile("mv/song_b.wav")} trimBefore={Math.round(T0 * FPS)} volume={fr => interpolate(fr, [0, 6, SAC_FRAMES - 30, SAC_FRAMES], [0, 1, 1, 0])}/>
      <AbsoluteFill style={{background: `radial-gradient(ellipse at 50% 55%, rgba(30,80,120,${0.25 + 0.2 * kick}), ${BG} 70%)`}}/>
      <ThreeCanvas width={1920} height={1080} camera={{fov: 40, near: 0.1, far: 1000, position: [0, 60, 95]}} gl={{antialias: true}}>
        <Cam pos={[shake * Math.sin(f * 1.7), camY + shake * Math.cos(f * 2.3), camZ]} look={[0, 0, 0]}/>
        <ambientLight intensity={0.25}/>
        <directionalLight position={[30, 50, 60]} intensity={1.6}/>
        <pointLight position={[-40, -20, 40]} intensity={800} color={ORANGE}/>
        <Cloud t={t} f={f}/>
        <Hero t={t} f={f}/>
      </ThreeCanvas>
      {scan < 1 && <div style={{position: "absolute", left: 0, right: 0, top: `${scan * 100}%`, height: 3, background: CYAN, opacity: 0.5 * snare + 0.2,
        boxShadow: `0 0 30px 6px rgba(127,227,250,${0.4 * snare})`}}/>}
      <div style={{position: "absolute", left: 64, top: 56, fontFamily: MONO, fontSize: 18, color: QUIET, letterSpacing: 3}}>
        CDK20 / HIT DISCOVERY / RUN 01 &nbsp;·&nbsp; {(t - T0).toFixed(2)}s
      </div>
      <Terminal t={t}/>
      <Counter t={t}/>
      <Caption t={t}/>
      <Meters f={f}/>
      <AbsoluteFill style={{background: "#fff", opacity: 0.12 * Math.exp(-(t - (DB.filter(d => d <= t).pop() ?? -9)) * 10) * (t >= DB[8] ? 1 : 0.3)}}/>
    </AbsoluteFill>
  );
};
