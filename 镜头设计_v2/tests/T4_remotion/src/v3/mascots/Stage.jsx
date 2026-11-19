// HKBU SCIE1007 coursework video: AI mascot insert. three.js stage: SVG characters on flat cards (SVG -> canvas texture each frame),
// drifting molecule balls, soft glow particles, 3D info board, slow camera push + parallax.
// Character layer is replaceable: pass pngDir to use a PNG frame sequence (public/mascots/png/<who>/0001.png ...) instead of the SVG.
import React, {useMemo, useLayoutEffect, useRef} from "react";
import {continueRender, delayRender, staticFile} from "remotion";
import {ThreeCanvas} from "@remotion/three";
import {useThree} from "@react-three/fiber";
import * as THREE from "three";
import {loadFont} from "@remotion/google-fonts/InstrumentSerif";
const fontLoad = loadFont();
import {characterToSvgString, VB_W, VB_H} from "./Character";

const TEX_W = 640, TEX_H = Math.round(640 * VB_H / VB_W); // 640 x 896

// ---------- texture helpers
function makeCanvasTex(w, h) {
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

function useImageTexture(src, w, h, key) {
  const {advance} = useThree();
  const tex = useMemo(() => makeCanvasTex(w, h), [w, h]);
  useLayoutEffect(() => {
    const handle = delayRender("mascot tex");
    const img = new Image();
    img.onload = () => {
      const ctx = tex.image.getContext("2d");
      ctx.clearRect(0, 0, w, h);
      ctx.drawImage(img, 0, 0, w, h);
      tex.needsUpdate = true;
      advance(performance.now());
      continueRender(handle);
    };
    img.onerror = () => { continueRender(handle); };
    img.src = src;
  }, [key]);
  return tex;
}

const CharCard = ({who, state, pos, scale, rot, pngDir, frame, height}) => {
  const src = pngDir ? staticFile(`${pngDir}/${String(Math.min(frame, 99999) + 1).padStart(4, "0")}.png`)
    : "data:image/svg+xml;charset=utf-8," + encodeURIComponent(characterToSvgString({who, ...state}));
  const tex = useImageTexture(src, TEX_W, TEX_H, src);
  const h = height, w = height * VB_W / VB_H;
  return (
    <group position={pos} rotation={rot} scale={scale}>
      <mesh position={[0, -h / 2 + 0.02, -0.02]} rotation={[-Math.PI / 2, 0, 0]} scale={[1.5, 1, 1]}>
        <circleGeometry args={[w * 0.26, 32]} />
        <meshBasicMaterial color="#5b4a8a" transparent opacity={0.16} />
      </mesh>
      <mesh position={[0, 0, 0]}>
        <planeGeometry args={[w, h]} />
        <meshBasicMaterial map={tex} transparent toneMapped={false} alphaTest={0.02} />
      </mesh>
    </group>
  );
};

// ---------- info board with canvas text
const BOARD_W = 6.6, BOARD_H = 2.15;
function drawBoard(canvas, card, accent) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  const r = 46;
  ctx.fillStyle = "#fffaf3";
  ctx.beginPath(); ctx.roundRect(0, 0, W, H, r); ctx.fill();
  ctx.fillStyle = accent;
  ctx.beginPath(); ctx.roundRect(0, 0, 30, H, [r, 0, 0, r]); ctx.fill();
  ctx.fillStyle = "#2a2433";
  ctx.textBaseline = "alphabetic";
  ctx.font = "104px 'Instrument Serif', serif";
  ctx.fillText(card.title, 78, 160);
  ctx.font = "58px 'Instrument Serif', serif";
  ctx.fillStyle = "#4a4258";
  wrapText(ctx, card.sub, 78, 250, W - 150, 66);
  if (card.src) {
    ctx.font = "italic 40px 'Instrument Serif', serif";
    ctx.fillStyle = "#8a7f99";
    ctx.fillText("Source: " + card.src, 78, H - 36);
  }
}
function wrapText(ctx, text, x, y, maxW, lh) {
  const words = text.split(" "); let line = "", yy = y;
  for (const w of words) {
    const test = line ? line + " " + w : w;
    if (ctx.measureText(test).width > maxW && line) { ctx.fillText(line, x, yy); line = w; yy += lh; } else line = test;
  }
  if (line) ctx.fillText(line, x, yy);
}

const Board = ({card, cardKey, age, accent, appear}) => {
  const {advance} = useThree();
  const tex = useMemo(() => makeCanvasTex(1584, 516), []);
  useLayoutEffect(() => {
    const handle = delayRender("board");
    const go = () => { drawBoard(tex.image, card, accent); tex.needsUpdate = true; advance(performance.now()); continueRender(handle); };
    fontLoad.waitUntilDone().catch(() => {}).then(() => (document.fonts && document.fonts.load ? document.fonts.load("92px 'Instrument Serif'").catch(() => {}) : null)).then(go);
  }, [cardKey]);
  // flip-in on card change: rotate about X from -80deg to 0 with overshoot
  const k = Math.min(1, age / 0.45);
  const ease = 1 - Math.pow(1 - k, 3);
  const rotX = (1 - ease) * -1.2 + Math.sin(k * Math.PI) * 0.04;
  const s = 0.9 + 0.1 * ease;
  return (
    <group position={[0, 2.15, -0.9]} rotation={[rotX, 0, 0]} scale={s * appear}>
      <mesh position={[0, 0, -0.06]}><boxGeometry args={[BOARD_W + 0.12, BOARD_H + 0.12, 0.1]} /><meshStandardMaterial color="#ffffff" roughness={0.25} metalness={0} /></mesh>
      <mesh><planeGeometry args={[BOARD_W, BOARD_H]} /><meshBasicMaterial map={tex} transparent toneMapped={false} /></mesh>
    </group>
  );
};

// ---------- floating molecules + glow particles
const rnd = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const MOL_COLORS = ["#f2711f", "#8bd8cf", "#a99be0", "#4a8fe0", "#ffd34d", "#ff8fb0"];

const Molecules = ({t, P, drift}) => {
  const items = useMemo(() => Array.from({length: 16}).map((_, i) => {
    const atoms = 3 + Math.floor(rnd(i * 3) * 3);
    return {
      x: (rnd(i + 1) - 0.5) * 17, y: (rnd(i + 21) - 0.5) * 7.4, z: -2.5 - rnd(i + 41) * 5,
      k: 1 + Math.floor(rnd(i + 5) * 2), ph: rnd(i + 9), s: 0.35 + rnd(i + 13) * 0.45,
      atoms: Array.from({length: atoms}).map((_, a) => ({p: [Math.cos(a * 2.2 + i) * 0.55, Math.sin(a * 1.7 + i) * 0.5, Math.sin(a * 2.9) * 0.3], r: 0.18 + rnd(i * 7 + a) * 0.14, c: MOL_COLORS[Math.floor(rnd(i * 11 + a) * MOL_COLORS.length)]})),
    };
  }), []);
  return items.map((m, i) => {
    const th = 2 * Math.PI * (m.k * t / P + m.ph);
    const A = 0.9 * drift;
    return (
      <group key={i} position={[m.x + Math.sin(th) * A, m.y + Math.cos(th * 1) * A * 1.1, m.z]} rotation={[th * 1.0, th * 2.0 / m.k, th]} scale={m.s * 1.5}>
        {m.atoms.map((a, j) => (
          <mesh key={j} position={a.p}><sphereGeometry args={[a.r, 20, 14]} /><meshStandardMaterial color={a.c} roughness={0.22} metalness={0.05} /></mesh>
        ))}
        {m.atoms.slice(1).map((a, j) => {
          const b = m.atoms[0].p, v = new THREE.Vector3(...a.p).sub(new THREE.Vector3(...b));
          const len = v.length(), mid = new THREE.Vector3(...b).add(v.clone().multiplyScalar(0.5));
          const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), v.clone().normalize());
          return <mesh key={"b" + j} position={mid.toArray()} quaternion={q}><cylinderGeometry args={[0.05, 0.05, len, 8]} /><meshStandardMaterial color="#ffffff" roughness={0.3} /></mesh>;
        })}
      </group>
    );
  });
};

const Glow = ({t, P, drift}) => {
  const N = 140;
  const tex = useMemo(() => {
    const c = document.createElement("canvas"); c.width = c.height = 64;
    const g = c.getContext("2d"), gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.4, "rgba(255,255,255,0.5)"); gr.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
    return new THREE.CanvasTexture(c);
  }, []);
  const geom = useMemo(() => {
    const pos = new Float32Array(N * 3);
    return new THREE.BufferGeometry().setAttribute("position", new THREE.BufferAttribute(pos, 3));
  }, []);
  const pos = geom.attributes.position;
  for (let i = 0; i < N; i++) {
    const th = 2 * Math.PI * ((1 + (i % 3)) * t / P + rnd(i + 70));
    pos.setXYZ(i, (rnd(i + 3) - 0.5) * 18 + Math.sin(th) * 0.5 * drift, (rnd(i + 33) - 0.5) * 9 + Math.cos(th) * 0.7 * drift, -1 - rnd(i + 63) * 7);
  }
  pos.needsUpdate = true;
  return <points geometry={geom}><pointsMaterial map={tex} size={0.34} transparent opacity={0.75} depthWrite={false} blending={THREE.AdditiveBlending} color="#fff2d8" sizeAttenuation /></points>;
};

const Backdrop = () => {
  const tex = useMemo(() => {
    const c = document.createElement("canvas"); c.width = 16; c.height = 256;
    const g = c.getContext("2d"), gr = g.createLinearGradient(0, 0, 0, 256);
    gr.addColorStop(0, "#c9d6ff"); gr.addColorStop(0.55, "#f3e4ff"); gr.addColorStop(1, "#ffe8dc");
    g.fillStyle = gr; g.fillRect(0, 0, 16, 256);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
  }, []);
  return <mesh position={[0, 0, -9]}><planeGeometry args={[40, 22]} /><meshBasicMaterial map={tex} toneMapped={false} /></mesh>;
};

const Rig = ({t, P, total, drift, dolly}) => {
  const {camera} = useThree();
  const th = 2 * Math.PI * t / P;
  const k = Math.min(1, t / total);
  const z = dolly ? 10.8 - 0.9 * (k * k * (3 - 2 * k)) : 10.8 + Math.sin(th) * 0.1 * drift * 10;
  camera.position.set(Math.sin(th) * 0.4 * (dolly ? 1 : 1), 0.3 + Math.cos(th) * 0.1, z);
  camera.lookAt(0, 0.1, 0);
  camera.fov = 35; camera.updateProjectionMatrix();
  return null;
};

/**
 * props: width,height, t (sec), frame, chars: [{who, state, x, z, scale, rotY, y, pngDir}], card, cardKey, cardAge, accent, P (period sec), loop
 */
export const Stage = ({width, height, t, frame, chars, card, cardKey, cardAge, boardAppear = 1, P = 60, total = 60, loop = false, charHeight = 3.0}) => {
  const drift = loop ? P / 60 : 1;
  return (
    <ThreeCanvas width={width} height={height} camera={{fov: 35, position: [0, 0.3, 10.8], near: 0.1, far: 60}} gl={{antialias: true}} onCreated={({gl}) => { try { const c = gl.getContext(); const e = c.getExtension("WEBGL_debug_renderer_info"); console.log("GL_RENDERER " + c.getParameter(e.UNMASKED_RENDERER_WEBGL)); } catch (err) {} }}>
      <Rig t={t} P={P} total={total} drift={drift} dolly={!loop} />
      <ambientLight intensity={1.15} />
      <directionalLight position={[3, 5, 6]} intensity={2.2} />
      <pointLight position={[-4, 2, 3]} intensity={12} color="#ffd9b8" />
      <Backdrop />
      <Molecules t={t} P={P} drift={drift} />
      <Glow t={t} P={P} drift={drift} />
      {card && <Board card={card} cardKey={cardKey} age={cardAge} accent={card.accent} appear={boardAppear} />}
      {chars.map((c) => (
        <CharCard key={c.who} who={c.who} state={c.state} pos={[c.x, c.y ?? -0.45, c.z ?? 0]} scale={c.scale ?? 1} rot={[0, c.rotY ?? 0, c.rotZ ?? 0]} pngDir={c.pngDir} frame={frame} height={charHeight} />
      ))}
    </ThreeCanvas>
  );
};
