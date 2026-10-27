import React, {useMemo} from "react";
import {AbsoluteFill} from "remotion";
import {ThreeCanvas} from "@remotion/three";
import {useThree} from "@react-three/fiber";
import * as THREE from "three";
import ligands from "../mv/ligands.json";
import {plan, SI, MONO, SiBack, clamp01, outCubic, outBack, inOut, hash, countBefore, hits, env, stepper, nthBeat} from "./common";

// The 8,918 designs as one continuous 3D world across act B. Every cloud shot reads the same clock (markers from
// the plan), so cutting away and back finds it where the music left it.
// gen: they appear on the synth hits | library: rows slide on strong stabs | latent: clusters, snap-rotate on stabs
// cut54 / cut7: the rest fall away | hero: 001 in 3D | r2: 16 variants -> 6 -> 048
const M = plan.markers;
const N = 8918, COLS = 98, ROWS = 91;
const STABS = hits("synth", 0.6).filter((t, i, a) => i === 0 || t - a[i - 1] >= 0.12);
const HATS = hits("hat");
const GEN_HITS = hits("synth").filter(t => t >= M.gen && t < M.gen + 5.5);

const STAGES = [[M.cut54, 54], [M.cut7, 7], [M.hero, 1], [M.r2, 16], [M.r2cut, 6], [M.hero2, 1]];
export const countAt = t => {
  if (t < M.gen) return 0;
  const shown = Math.round(N * clamp01(countBefore(GEN_HITS, t) / GEN_HITS.length));
  return STAGES.reduce((n, [at, k]) => (t >= at ? k : n), shown);
};
const lastStage = t => STAGES.filter(([at]) => t >= at).map(([at]) => at).pop() ?? -9;

const pointMaterial = () => new THREE.ShaderMaterial({
  transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  vertexShader: `attribute float size; attribute vec3 color; varying vec3 vColor;
    void main(){ vColor = color; vec4 mv = modelViewMatrix * vec4(position,1.0);
      gl_PointSize = size * (900.0 / -mv.z); gl_Position = projectionMatrix * mv; }`,
  fragmentShader: `varying vec3 vColor;
    void main(){ float d = length(gl_PointCoord - 0.5) * 2.0; float a = smoothstep(1.0, 0.0, d);
      a = a * a; gl_FragColor = vec4(vColor * a, a); }`,
});

const Cam = ({pos}) => {
  const {camera} = useThree();
  camera.position.set(...pos); camera.lookAt(0, 0, 0); camera.updateProjectionMatrix();
  return null;
};

const Points = ({t, f}) => {
  const seed = useMemo(() => {
    const grid = new Float32Array(N * 3), cloud = new Float32Array(N * 3), core = new Float32Array(N * 3);
    const order = Array.from({length: N}, (_, i) => i).sort((a, b) => hash(a, 7) - hash(b, 7));
    const rank = new Int32Array(N); order.forEach((id, r) => { rank[id] = r; });
    const centers = Array.from({length: 14}, (_, c) => [(hash(c, 1) - 0.5) * 70, (hash(c, 2) - 0.5) * 38, (hash(c, 3) - 0.5) * 50]);
    for (let i = 0; i < N; i++) {
      grid[i * 3] = (i % COLS - (COLS - 1) / 2) * 1.25; grid[i * 3 + 2] = (Math.floor(i / COLS) - (ROWS - 1) / 2) * 1.25;
      const c = centers[Math.floor(hash(i, 4) * centers.length)];
      cloud[i * 3] = c[0] + (hash(i, 5) + hash(i, 6) + hash(i, 8) - 1.5) * 9;
      cloud[i * 3 + 1] = c[1] + (hash(i, 9) + hash(i, 10) - 1) * 9;
      cloud[i * 3 + 2] = c[2] + (hash(i, 11) + hash(i, 12) - 1) * 9;
      const r = rank[i], a = r * 2.399963, rad = 3 + Math.sqrt(r) * 2.2; // survivors pack into a golden-angle disc
      core[i * 3] = Math.cos(a) * rad; core[i * 3 + 1] = Math.sin(a) * rad; core[i * 3 + 2] = (hash(i, 13) - 0.5) * 4;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(N * 3), 3));
    geo.setAttribute("color", new THREE.BufferAttribute(new Float32Array(N * 3), 3));
    geo.setAttribute("size", new THREE.BufferAttribute(new Float32Array(N), 1));
    return {grid, cloud, core, rank, geo, mat: pointMaterial()};
  }, []);
  const {grid, cloud, core, rank, geo} = seed;
  const P = geo.attributes.position.array, Cc = geo.attributes.color.array, S = geo.attributes.size.array;
  const kick = env("kick", f), hat = env("hat", f), hatIdx = countBefore(HATS, t);
  const shown = countAt(Math.min(t, M.cut54 - 0.01));
  const toCloud = inOut((t - M.latent) / 0.5), toCore = inOut((t - M.cut54 - 0.25) / 0.9);
  const alive = countAt(t), cutAt = lastStage(t);
  const W = COLS * 1.25;
  // library: each strong stab slides every row sideways by whole columns (wraps round)
  const libStabs = STABS.filter(s => s >= M.gen + 2 && s < M.latent);
  const nLib = countBefore(libStabs, t), libEase = nLib ? outCubic((t - libStabs[nLib - 1]) / 0.09) : 0;
  const shifts = Array.from({length: ROWS}, (_, r) => {
    let s = 0;
    for (let k = 0; k < nLib; k++) { const d = Math.round((hash(k, r) - 0.5) * 8) * 1.25; s += k === nLib - 1 ? d * libEase : d; }
    return s;
  });
  const r2 = t >= M.r2;

  for (let i = 0; i < N; i++) {
    const row = Math.floor(i / COLS), rk = rank[i];
    let gx = grid[i * 3] + shifts[row]; gx = ((gx + W / 2) % W + W) % W - W / 2;
    // appear in reading order as the synth plays; each point drops in
    const born = i < shown ? 1 : 0, bornEase = born ? clamp01((shown - i) / 900) : 0;
    const gy = (1 - outCubic(bornEase)) * 14 + kick * 1.6 * Math.sin(i * 0.37 + row);
    let x = gx + (cloud[i * 3] - gx) * toCloud, y = gy + (cloud[i * 3 + 1] - gy) * toCloud, z = grid[i * 3 + 2] + (cloud[i * 3 + 2] - grid[i * 3 + 2]) * toCloud;
    const contract = 1 - 0.09 * kick * toCloud;
    x *= contract; y *= contract; z *= contract;
    let size = 1.05 * born, cr = 0.5, cg = 0.89, cb = 0.98, bright = 0.55;

    if (r2) {
      // round 2: a fresh ring of 16 variants of 001 around the centre; 10 of them fall at r2cut, the 6 fold into 048
      const v = rk - 100;
      if (v < 0 || v >= 16) { S[i] = 0; continue; }
      const a = v / 16 * Math.PI * 2 + (t - M.r2) * 0.3, rad = 24 + 2 * Math.sin(v);
      const pop = outCubic((t - nthBeat(M.r2, v % 8) ) / 0.25);
      x = Math.cos(a) * rad; y = Math.sin(a) * rad * 0.55; z = Math.sin(a) * 6;
      size = 7 * pop; bright = 1.1; cr = 0.5; cg = 0.89; cb = 0.98;
      if (v >= 6 && t >= M.r2cut) { const s = t - M.r2cut; y -= s * s * 60; bright *= Math.max(0, 1 - s / 0.9); }
      if (t >= M.hero2) { const g = inOut((t - M.hero2) / 0.5); x *= 1 - g; y *= 1 - g; z *= 1 - g; bright *= 1 - g; }
    } else {
      if (rk < 54 && toCore > 0) { x += (core[i * 3] - x) * toCore; y += (core[i * 3 + 1] - y) * toCore; z += (core[i * 3 + 2] - z) * toCore; }
      if (rk >= alive) {
        const since = t - cutAt;
        y -= since * since * 60 * (0.6 + hash(i, 14)); x += (hash(i, 15) - 0.5) * since * 30;
        bright *= Math.max(0, 1 - since / 0.9) * (rk < 54 ? 1.6 : 1);
        if (bright <= 0) size = 0;
      } else if (t >= M.cut54) {
        const kept = clamp01((t - M.cut54) / 0.3);
        size *= 1 + kept * (rk < 7 && t >= M.cut7 ? 9 : 3.5); bright = 0.55 + kept * 0.45;
        cr += (1.0 - cr) * kept; cg += (0.54 - cg) * kept; cb += (0.3 - cb) * kept; // survivors turn warm
      }
      if (rk === 0 && t >= M.hero) bright *= Math.max(0, 1 - (t - M.hero) / 0.4);
    }
    if (hash(i, hatIdx + 99) < 0.035) { bright += hat * 1.6; size *= 1 + hat * 0.8; }
    bright += kick * 0.25;
    P[i * 3] = x; P[i * 3 + 1] = y; P[i * 3 + 2] = z;
    Cc[i * 3] = cr * bright; Cc[i * 3 + 1] = cg * bright; Cc[i * 3 + 2] = cb * bright; S[i] = size;
  }
  geo.attributes.position.needsUpdate = geo.attributes.color.needsUpdate = geo.attributes.size.needsUpdate = true;
  const latentStabs = STABS.filter(s => s >= M.latent);
  const rotY = toCloud * (0.25 * (t - M.latent) + stepper(latentStabs, M.latent, t) * 0.49) * (1 - toCore);
  return <points geometry={geo} material={seed.mat} rotation={[0, rotY, 0]} frustumCulled={false}/>;
};

// ball-and-stick ligand from our re-docked poses, long axis laid along x
const ELEMENT = {C: "#7FC4D8", N: "#4C8DFF", O: "#FF6A4C", H: "#FFFFFF"};
const useMolecule = name => useMemo(() => {
  const all = ligands[name].atoms, keepIdx = all.map((a, i) => (a[0] !== "H" ? i : -1)).filter(i => i >= 0);
  const idx = new Map(keepIdx.map((orig, j) => [orig, j])), atoms = keepIdx.map(i => all[i]);
  const c = [0, 1, 2].map(k => atoms.reduce((s, a) => s + a[k + 1], 0) / atoms.length);
  let pts = atoms.map(a => new THREE.Vector3(a[1] - c[0], a[2] - c[1], a[3] - c[2]).multiplyScalar(3.0));
  let far = [0, 1, 0];
  pts.forEach((p, i) => pts.forEach((q, j) => { const d = p.distanceTo(q); if (d > far[2]) far = [i, j, d]; }));
  const turn = new THREE.Quaternion().setFromUnitVectors(pts[far[1]].clone().sub(pts[far[0]]).normalize(), new THREE.Vector3(1, 0, 0));
  pts = pts.map(p => p.applyQuaternion(turn));
  const up = new THREE.Vector3(0, 1, 0);
  const bonds = ligands[name].bonds.filter(([a, b]) => idx.has(a) && idx.has(b)).map(([a, b]) => {
    const pa = pts[idx.get(a)], pb = pts[idx.get(b)], dir = pb.clone().sub(pa);
    return {mid: pa.clone().add(pb).multiplyScalar(0.5), len: dir.length(), q: new THREE.Quaternion().setFromUnitVectors(up, dir.normalize())};
  });
  return {atoms, pts, bonds};
}, [name]);

const Molecule = ({name, t, f, from, scale}) => {
  const mol = useMolecule(name);
  if (scale <= 0.001) return null;
  const kick = env("kick", f), snare = env("snare", f);
  const spin = stepper(STABS, from, t, 0.1) * 0.55 + (t - from) * 0.3;
  return <group scale={scale * (1 + 0.06 * kick)} rotation={[spin, 0, 0]}>
    {mol.pts.map((p, i) => <mesh key={"a" + i} position={p}>
      <sphereGeometry args={[mol.atoms[i][0] === "C" ? 1.1 : 1.25, 24, 16]}/>
      <meshStandardMaterial color={ELEMENT[mol.atoms[i][0]]} emissive={ELEMENT[mol.atoms[i][0]]} emissiveIntensity={0.08 + 0.6 * kick} roughness={0.35} metalness={0.1}/>
    </mesh>)}
    {mol.bonds.map((b, i) => <mesh key={"b" + i} position={b.mid} quaternion={b.q}>
      <cylinderGeometry args={[0.3, 0.3, b.len, 10]}/>
      <meshStandardMaterial color="#9FB8C6" emissive={SI.accent} emissiveIntensity={0.15 + 0.8 * snare} roughness={0.5}/>
    </mesh>)}
  </group>;
};

const Counter = ({t}) => {
  const n = countAt(t), at = lastStage(t), flash = at > 0 ? Math.exp(-(t - at) * 4) : 0;
  const hero = t >= M.hero && (t < M.r2 || t >= M.hero2);
  const label = hero ? (t >= M.hero2 ? "048" : "001") : n.toLocaleString("en-US");
  const head = hero ? (t >= M.hero2 ? "ROUND 2 HIT" : "FIRST HIT") : t >= M.r2 ? "ROUND 2 · VARIANTS" : "CANDIDATES";
  return <div style={{position: "absolute", right: 64, top: 80, textAlign: "right", fontFamily: MONO}}>
    <div style={{fontSize: 20, color: SI.quiet, letterSpacing: 4}}>{head}</div>
    <div style={{fontSize: 120, fontWeight: 700, color: t >= M.cut54 ? SI.hot : SI.ink, lineHeight: 1, transform: `scale(${1 + 0.12 * flash})`,
      transformOrigin: "right center", textShadow: `0 0 ${40 * flash}px ${SI.hot}`}}>{label}</div>
  </div>;
};

const Term = ({lines, t, at}) => {
  const hatsSince = countBefore(HATS, t) - countBefore(HATS, at);
  let budget = 6 + hatsSince * 5;
  return <div style={{position: "absolute", left: 64, top: 80, fontFamily: MONO, fontSize: 26, lineHeight: 1.55, color: SI.accent}}>
    {lines.map((line, i) => {
      const n = Math.max(0, Math.min(line.length, budget)); budget -= line.length;
      if (!n) return null;
      return <div key={i} style={{whiteSpace: "pre", color: line.startsWith(">") ? SI.accent : SI.ink}}>{line.slice(0, n)}{n < line.length ? "▋" : ""}</div>;
    })}
  </div>;
};

export const CloudScene = ({s, t, f, local}) => {
  const toCloud = inOut((t - M.latent) / 0.6), toHero = inOut((t - M.hero) / 1.2), toR2 = inOut((t - M.r2) / 0.8);
  const camY = 60 * (1 - toCloud) + 6 * toCloud, camZ = 95 * (1 - toCloud) + 115 * toCloud - 40 * toHero + 25 * toR2;
  const kick = env("kick", f), shake = kick * 0.5;
  // 001 shows from hero, shrinks aside for round 2, and 048 takes its place at hero2
  const s001 = t < M.hero ? 0 : outCubic((t - M.hero) / 0.6) * (1 - 0.65 * toR2) * (1 - inOut((t - M.hero2) / 0.4));
  const s048 = t < M.hero2 ? 0 : outBack((t - M.hero2) / 0.6);
  return <SiBack f={f} local={local} grid={false}>
    <AbsoluteFill style={{background: `radial-gradient(ellipse at 50% 55%, rgba(30,80,120,${0.25 + 0.2 * kick}), transparent 70%)`}}/>
    <ThreeCanvas width={1920} height={1080} camera={{fov: 40, near: 0.1, far: 1000, position: [0, 60, 95]}} gl={{antialias: true}}>
      <Cam pos={[shake * Math.sin(f * 1.7), camY + shake * Math.cos(f * 2.3), camZ]}/>
      <ambientLight intensity={0.25}/>
      <directionalLight position={[30, 50, 60]} intensity={1.6}/>
      <pointLight position={[-40, -20, 40]} intensity={800} color={SI.hot}/>
      <Points t={t} f={f}/>
      <Molecule name="001" t={t} f={f} from={M.hero} scale={s001}/>
      <Molecule name="048" t={t} f={f} from={M.hero2} scale={s048}/>
    </ThreeCanvas>
    <Term lines={s.props.term || []} t={t} at={s.at}/>
    <Counter t={t}/>
  </SiBack>;
};
