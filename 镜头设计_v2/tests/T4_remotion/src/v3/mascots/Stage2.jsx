// HKBU SCIE1007 coursework video: AI mascot insert v2 (11-21). three.js stage for the Codex character art
// (1:1 from the fan reference sheets, transparent 1536 PNGs: open / blink / wink / talk_a / talk_o / wave).
// Dark theatre stage: far lattice backdrop, soft bokeh, stage beams per character, glossy floating molecules,
// colour rim glow around each character (alpha-dilate shader), foreground sparkles. Camera is driven by Show2.
import React, {useMemo, useLayoutEffect, useState} from "react";
import {continueRender, delayRender, staticFile} from "remotion";
import {ThreeCanvas} from "@remotion/three";
import {useThree} from "@react-three/fiber";
import * as THREE from "three";

export const STATES = ["open", "blink", "wink", "talk_a", "talk_o", "wave"];
export const DIR = {Claude: "claude", GPT: "gpt", DeepSeek: "deepseek"};
export const ACCENT = {Claude: "#ff9a4d", GPT: "#c8b8ff", DeepSeek: "#58b4ff"};

const rnd = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

// ---------- load all 18 character textures once
function useCharTextures() {
  const {advance} = useThree();
  const [tex] = useState(() => {
    const out = {};
    const handle = delayRender("mascot textures");
    let left = Object.keys(DIR).length * STATES.length;
    const loader = new THREE.TextureLoader();
    for (const who of Object.keys(DIR)) {
      out[who] = {};
      for (const s of STATES) {
        out[who][s] = loader.load(staticFile(`m/${DIR[who]}/${s}.png`), (t) => {
          t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t.needsUpdate = true;
          if (--left === 0) { advance(performance.now()); requestAnimationFrame(() => { advance(performance.now()); continueRender(handle); }); }
        }, undefined, () => { if (--left === 0) continueRender(handle); });
      }
    }
    return out;
  });
  return tex;
}

// alpha-dilate rim glow: samples the character alpha in a ring, outputs the accent colour
const glowVS = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`;
const glowFS = `
uniform sampler2D map; uniform vec3 color; uniform float opacity; uniform float radius; varying vec2 vUv;
void main(){
  float a = 0.0;
  for (int i = 0; i < 16; i++) {
    float th = 6.2831853 * float(i) / 16.0;
    vec2 d = vec2(cos(th), sin(th));
    a += texture2D(map, vUv + d * radius).a;
    a += texture2D(map, vUv + d * radius * 0.5).a;
  }
  a /= 32.0;
  float inside = texture2D(map, vUv).a;
  a *= smoothstep(0.03, 0.12, vUv.y);
  gl_FragColor = vec4(color, a * opacity * (1.0 - inside * 0.85));
}`;

const Character = ({tex, who, st}) => {
  const map = tex[who][st.frame] || tex[who].open;
  const glowMat = useMemo(() => new THREE.ShaderMaterial({
    uniforms: {map: {value: map}, color: {value: new THREE.Color(ACCENT[who])}, opacity: {value: 0.5}, radius: {value: 0.004}},
    vertexShader: glowVS, fragmentShader: glowFS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  }), [who]);
  glowMat.uniforms.map.value = map;
  glowMat.uniforms.opacity.value = st.glow;
  glowMat.uniforms.radius.value = 0.0025 + st.glow * 0.003;
  const H = st.h;
  const c = st.bright;
  return (
    <group position={[st.x, st.y, st.z]} rotation={[0, 0, st.rotZ]} scale={[st.s * st.sx, st.s * st.sy, 1]}>
      {/* stage beam behind the character */}
      <mesh position={[0, H * 0.32, -0.6]} renderOrder={1}>
        <planeGeometry args={[H * 0.62, H * 1.6]} />
        <meshBasicMaterial map={BEAM()} color={ACCENT[who]} transparent opacity={st.beam} depthWrite={false} blending={THREE.AdditiveBlending} toneMapped={false} />
      </mesh>
      <mesh position={[0, 0, -0.02]} renderOrder={2} material={glowMat}><planeGeometry args={[H * 1.04, H * 1.04]} /></mesh>
      <mesh renderOrder={3}>
        <planeGeometry args={[H, H]} />
        <meshBasicMaterial map={map} alphaMap={FADE()} transparent alphaTest={0.01} toneMapped={false} color={new THREE.Color(c, c, c)} />
      </mesh>
    </group>
  );
};

// ---------- shared soft textures
let _beam = null, _dot = null, _ring = null, _star = null, _fade = null;
function FADE() { // alpha ramp: transparent at the bottom 3%, opaque above 12% (hides the knee crop line)
  if (_fade) return _fade;
  const c = document.createElement("canvas"); c.width = 4; c.height = 256;
  const g = c.getContext("2d"), gr = g.createLinearGradient(0, 256, 0, 0);
  gr.addColorStop(0, "#000"); gr.addColorStop(0.03, "#000"); gr.addColorStop(0.12, "#fff"); gr.addColorStop(1, "#fff");
  g.fillStyle = gr; g.fillRect(0, 0, 4, 256);
  _fade = new THREE.CanvasTexture(c); return _fade;
}
function BEAM() {
  if (_beam) return _beam;
  const c = document.createElement("canvas"); c.width = 128; c.height = 512;
  const g = c.getContext("2d");
  for (let y = 0; y < 512; y++) {
    const v = y / 511, w = 0.18 + 0.82 * v; // narrow at top, wide at bottom
    const gr = g.createLinearGradient(0, 0, 128, 0);
    const a = Math.pow(1 - v, 0.6) * 0.9 * Math.min(1, v * 6);
    gr.addColorStop(0, "rgba(255,255,255,0)"); gr.addColorStop(0.5 - w / 2, "rgba(255,255,255,0)");
    gr.addColorStop(0.5, `rgba(255,255,255,${a})`);
    gr.addColorStop(0.5 + w / 2, "rgba(255,255,255,0)"); gr.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = gr; g.fillRect(0, 511 - y, 128, 1);
  }
  _beam = new THREE.CanvasTexture(c); return _beam;
}
function DOT() {
  if (_dot) return _dot;
  const c = document.createElement("canvas"); c.width = c.height = 128;
  const g = c.getContext("2d"), gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.35, "rgba(255,255,255,0.55)"); gr.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  _dot = new THREE.CanvasTexture(c); return _dot;
}
function RING() { // bokeh disc: flat core with a slightly brighter rim
  if (_ring) return _ring;
  const c = document.createElement("canvas"); c.width = c.height = 128;
  const g = c.getContext("2d"), gr = g.createRadialGradient(64, 64, 0, 64, 64, 62);
  gr.addColorStop(0, "rgba(255,255,255,0.35)"); gr.addColorStop(0.82, "rgba(255,255,255,0.45)"); gr.addColorStop(0.93, "rgba(255,255,255,0.7)"); gr.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = gr; g.beginPath(); g.arc(64, 64, 62, 0, 7); g.fill();
  _ring = new THREE.CanvasTexture(c); return _ring;
}
function STAR() { // four-point sparkle
  if (_star) return _star;
  const c = document.createElement("canvas"); c.width = c.height = 128;
  const g = c.getContext("2d");
  const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.15, "rgba(255,255,255,0.6)"); gr.addColorStop(0.5, "rgba(255,255,255,0)");
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  g.fillStyle = "rgba(255,255,255,0.95)";
  g.beginPath(); g.moveTo(64, 0); g.quadraticCurveTo(68, 60, 128, 64); g.quadraticCurveTo(68, 68, 64, 128); g.quadraticCurveTo(60, 68, 0, 64); g.quadraticCurveTo(60, 60, 64, 0); g.fill();
  _star = new THREE.CanvasTexture(c); return _star;
}

// ---------- backdrop: deep navy with a faint hexagon/molecule lattice and a warm horizon glow
const Backdrop = ({t}) => {
  const tex = useMemo(() => {
    const W = 2048, H = 1152, c = document.createElement("canvas"); c.width = W; c.height = H;
    const g = c.getContext("2d");
    const bg = g.createRadialGradient(W * 0.5, H * 0.62, 50, W * 0.5, H * 0.55, W * 0.75);
    bg.addColorStop(0, "#28285e"); bg.addColorStop(0.4, "#141638"); bg.addColorStop(1, "#05060f");
    g.fillStyle = bg; g.fillRect(0, 0, W, H);
    // hex lattice (benzene-like rings), very faint
    const r = 46, dx = r * Math.sqrt(3), dy = r * 1.5;
    g.lineWidth = 2;
    for (let row = -1; row < H / dy + 1; row++) for (let col = -1; col < W / dx + 1; col++) {
      const cx = col * dx + (row % 2 ? dx / 2 : 0), cy = row * dy;
      const fade = Math.max(0, 1 - Math.hypot(cx - W / 2, cy - H * 0.45) / (W * 0.62));
      g.strokeStyle = `rgba(150,170,255,${0.012 + 0.04 * fade * fade})`;
      g.beginPath();
      for (let k = 0; k < 7; k++) { const a = Math.PI / 6 + k * Math.PI / 3; g[k ? "lineTo" : "moveTo"](cx + r * Math.cos(a), cy + r * Math.sin(a)); }
      g.stroke();
      if (rnd(row * 97 + col) > 0.93) { g.fillStyle = `rgba(190,205,255,${0.04 + 0.12 * fade})`; g.beginPath(); g.arc(cx + r * Math.cos(Math.PI / 6), cy + r * Math.sin(Math.PI / 6), 5, 0, 7); g.fill(); }
    }
    // horizon glow
    const hz = g.createLinearGradient(0, H * 0.58, 0, H);
    hz.addColorStop(0, "rgba(255,170,120,0)"); hz.addColorStop(0.5, "rgba(255,160,130,0.10)"); hz.addColorStop(1, "rgba(120,140,255,0.06)");
    g.fillStyle = hz; g.fillRect(0, H * 0.58, W, H * 0.42);
    const t2 = new THREE.CanvasTexture(c); t2.colorSpace = THREE.SRGBColorSpace; return t2;
  }, []);
  return <mesh position={[0, 0.3, -14]} rotation={[0, 0, Math.sin(t * 0.08) * 0.01]}><planeGeometry args={[52, 29.25]} /><meshBasicMaterial map={tex} toneMapped={false} /></mesh>;
};

const BOKEH_COL = ["#ff9a4d", "#c8b8ff", "#58b4ff", "#ffd27a", "#ff7fb0"];
const Bokeh = ({t}) => {
  const items = useMemo(() => Array.from({length: 34}).map((_, i) => ({
    x: (rnd(i + 1) - 0.5) * 34, y: (rnd(i + 11) - 0.5) * 16, z: -11 + rnd(i + 21) * 5, s: 0.7 + rnd(i + 31) * 2.2,
    c: BOKEH_COL[i % BOKEH_COL.length], o: 0.06 + rnd(i + 41) * 0.12, ph: rnd(i + 51) * 6.28, sp: 0.05 + rnd(i + 61) * 0.12,
  })), []);
  return items.map((b, i) => (
    <mesh key={i} position={[b.x + Math.sin(t * b.sp + b.ph) * 0.8, b.y + Math.cos(t * b.sp * 0.8 + b.ph) * 0.5, b.z]}>
      <planeGeometry args={[b.s, b.s]} />
      <meshBasicMaterial map={RING()} color={b.c} transparent opacity={b.o * (0.8 + 0.2 * Math.sin(t * 1.3 + b.ph))} depthWrite={false} blending={THREE.AdditiveBlending} toneMapped={false} />
    </mesh>
  ));
};

const MOL_COLORS = ["#ff9a4d", "#e9ecff", "#8fd0ff", "#c8b8ff", "#ffd27a"];
const Molecules = ({t}) => {
  const items = useMemo(() => Array.from({length: 12}).map((_, i) => {
    const n = 3 + Math.floor(rnd(i * 3) * 4);
    return {
      x: (i % 2 ? 1 : -1) * (6.5 + rnd(i + 1) * 7), y: (rnd(i + 21) - 0.35) * 9, z: -5 - rnd(i + 41) * 4, ph: rnd(i + 9) * 6.28, s: 0.3 + rnd(i + 13) * 0.35,
      atoms: Array.from({length: n}).map((_, a) => ({p: a === 0 ? [0, 0, 0] : [Math.cos(a * 2.1 + i) * 0.62, Math.sin(a * 2.1 + i) * 0.62, (rnd(i * 5 + a) - 0.5) * 0.6], r: a === 0 ? 0.26 : 0.15 + rnd(i * 7 + a) * 0.1, c: MOL_COLORS[Math.floor(rnd(i * 11 + a) * MOL_COLORS.length)]})),
    };
  }), []);
  return items.map((m, i) => (
    <group key={i} position={[m.x + Math.sin(t * 0.2 + m.ph) * 0.4, m.y + Math.sin(t * 0.33 + m.ph) * 0.35, m.z]} rotation={[t * 0.25 + m.ph, t * 0.31, t * 0.17]} scale={m.s * 1.6}>
      {m.atoms.map((a, j) => (
        <mesh key={j} position={a.p}><sphereGeometry args={[a.r, 28, 20]} /><meshPhysicalMaterial color={a.c} roughness={0.18} metalness={0.05} clearcoat={1} clearcoatRoughness={0.08} /></mesh>
      ))}
      {m.atoms.slice(1).map((a, j) => {
        const v = new THREE.Vector3(...a.p), len = v.length(), mid = v.clone().multiplyScalar(0.5);
        const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), v.clone().normalize());
        return <mesh key={"b" + j} position={mid.toArray()} quaternion={q}><cylinderGeometry args={[0.055, 0.055, len, 10]} /><meshPhysicalMaterial color="#dfe4ff" roughness={0.25} clearcoat={1} /></mesh>;
      })}
    </group>
  ));
};

// dust motes mid-depth, sparkles in front (out of focus = large and faint)
const Motes = ({t}) => {
  const N = 160;
  const geom = useMemo(() => new THREE.BufferGeometry().setAttribute("position", new THREE.BufferAttribute(new Float32Array(N * 3), 3)), []);
  const pos = geom.attributes.position;
  for (let i = 0; i < N; i++) {
    const sp = 0.08 + rnd(i + 3) * 0.12;
    const y = ((rnd(i + 33) * 14 + t * sp * 1.2) % 14) - 7;
    pos.setXYZ(i, (rnd(i + 3) - 0.5) * 26 + Math.sin(t * 0.4 + i) * 0.3, y, -8 + rnd(i + 63) * 11);
  }
  pos.needsUpdate = true;
  return <points geometry={geom}><pointsMaterial map={DOT()} size={0.12} transparent opacity={0.6} depthWrite={false} blending={THREE.AdditiveBlending} color="#fff1d6" sizeAttenuation toneMapped={false} /></points>;
};

// burst of sparkles at a point (wink / punch accents); spark = {x,y,z,age,color}
const Sparks = ({sparks}) => sparks.map((s, i) => {
  const k = s.age / 0.7; if (k < 0 || k > 1) return null;
  return Array.from({length: 7}).map((_, j) => {
    const a = j * 0.9 + i, r = 0.25 + k * (0.7 + rnd(j + i) * 0.5);
    const sz = (0.16 + rnd(j * 3 + i) * 0.16) * Math.sin(Math.PI * Math.min(1, k * 1.3));
    return (
      <mesh key={i + "_" + j} position={[s.x + Math.cos(a) * r, s.y + Math.sin(a) * r * 0.8 + k * 0.2, s.z + 0.3]} rotation={[0, 0, k * 2 + j]}>
        <planeGeometry args={[sz, sz]} />
        <meshBasicMaterial map={STAR()} color={s.color} transparent opacity={1 - k * 0.6} depthWrite={false} blending={THREE.AdditiveBlending} toneMapped={false} />
      </mesh>
    );
  });
});

const Rig = ({cam}) => {
  const {camera} = useThree();
  camera.position.set(cam.x + cam.shx, cam.y + cam.shy, cam.z);
  camera.lookAt(cam.x * 0.92, cam.ly, 0);
  camera.rotation.z += cam.roll;
  camera.fov = cam.fov; camera.updateProjectionMatrix();
  return null;
};

const Chars = ({chars}) => {
  const tex = useCharTextures();
  return [...chars].sort((a, b) => a.z - b.z).map((c) => <Character key={c.who} tex={tex} who={c.who} st={c} />);
};

export const Stage2 = ({width, height, t, cam, chars, sparks}) => {
  return (
    <ThreeCanvas width={width} height={height} camera={{fov: 30, position: [0, 0, 12], near: 0.1, far: 80}} gl={{antialias: true}}
      onCreated={({gl}) => { try { const c = gl.getContext(); const e = c.getExtension("WEBGL_debug_renderer_info"); console.log("GL_RENDERER " + c.getParameter(e.UNMASKED_RENDERER_WEBGL)); } catch (err) {} }}>
      <Rig cam={cam} />
      <ambientLight intensity={0.55} />
      <directionalLight position={[4, 6, 6]} intensity={2.4} color="#fff2e4" />
      <pointLight position={[-6, 1, 2]} intensity={30} color="#ff9a4d" />
      <pointLight position={[7, 2, 0]} intensity={30} color="#58b4ff" />
      <Backdrop t={t} />
      <Bokeh t={t} />
      <Molecules t={t} />
      <Motes t={t} />
      <Chars chars={chars} />
      <Sparks sparks={sparks} />
    </ThreeCanvas>
  );
};
