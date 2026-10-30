// SPLAT test drawn the way Gaussian splatting is meant to be drawn: sorted back to front and blended on the GPU, no ray tracing.
// State comes from v3_frontier/splat_fast/code/state_server.py (same 285k splats and motion as the Cycles version).
import React, {useLayoutEffect, useRef} from "react";
import {Composition, continueRender, delayRender, registerRoot, useCurrentFrame} from "remotion";

const URL_ = "http://127.0.0.1:8765", W = 1920, H = 1080, TEXW = 4096;

const VS = `#version 300 es
precision highp float; precision highp int; precision highp sampler2D;
layout(location=0) in vec2 corner;
layout(location=1) in uint id;
uniform sampler2D tS, tD;
uniform mat4 V;
uniform vec3 camPos;
uniform vec2 res;
uniform float fpx;
flat out vec3 E;
flat out float A;
out vec2 uv;
vec4 at(sampler2D t, int i){return texelFetch(t, ivec2(i % ${TEXW}, i / ${TEXW}), 0);}
float cl(float x){return clamp(x, 0.0, 1.0);}
float box(vec3 refl, vec3 d, vec3 up, float hw, float hh, float soft){
  d = normalize(d); up = normalize(up - dot(up, d) * d); vec3 rt = cross(d, up);
  float m = cl((hw + soft - abs(dot(refl, rt))) / (2.0 * soft)) * cl((hh + soft - abs(dot(refl, up))) / (2.0 * soft));
  return dot(refl, d) > 0.0 ? m : 0.0;
}
void main(){
  int i = int(id);
  vec4 S0 = at(tS, i * 4), S1 = at(tS, i * 4 + 1), S2 = at(tS, i * 4 + 2), S3 = at(tS, i * 4 + 3);
  vec4 D0 = at(tD, i * 3), D1 = at(tD, i * 3 + 1), D2 = at(tD, i * 3 + 2);
  vec3 pw = D0.xyz, s = D1.xyz, nrm = vec3(S0.w, S1.w, S2.w);
  vec3 pc = (V * vec4(pw, 1.0)).xyz;
  if (pc.z > -0.05) { gl_Position = vec4(2.0, 2.0, 2.0, 1.0); return; }
  // view-dependent colour: same terms as splatlib.splat_material
  vec3 I = normalize(camPos - pw);
  float ndotv = dot(nrm, I);
  float rim = pow(cl(1.0 - abs(ndotv)), 2.4) * S3.x;
  vec3 refl = reflect(-I, nrm);
  float spec = (box(refl, vec3(-0.80, -0.42, 0.42), vec3(0, 0, 1), 0.040, 0.60, 0.075)
    + 0.55 * box(refl, vec3(0.25, -0.30, 0.92), vec3(0, 1, 0), 0.40, 0.05, 0.09)) * S3.y;
  float lamb = 1.0 - S3.z + S3.z * max(dot(nrm, normalize(vec3(-0.45, -0.55, 0.70))), 0.0);
  float side = 0.38 + (ndotv > 0.0 ? 0.62 : 0.0);
  E = D2.rgb * (lamb + (rim + spec) * side) * D1.w;
  // the ellipsoid's footprint: project its axes, take the 2x2 covariance, draw that ellipse
  mat3 Rc = mat3(V) * mat3(S0.xyz, S1.xyz, S2.xyz);
  float k = fpx / -pc.z;
  vec2 b0 = (Rc[0] * s.x).xy * k, b1 = (Rc[1] * s.y).xy * k, b2 = (Rc[2] * s.z).xy * k;
  float a = dot(vec3(b0.x, b1.x, b2.x), vec3(b0.x, b1.x, b2.x)), d = dot(vec3(b0.y, b1.y, b2.y), vec3(b0.y, b1.y, b2.y));
  float c = dot(vec3(b0.x, b1.x, b2.x), vec3(b0.y, b1.y, b2.y));
  float t = 0.5 * (a + d), q = sqrt(max(0.25 * (a - d) * (a - d) + c * c, 0.0));
  float l1 = t + q, l2 = max(t - q, 0.0);
  vec2 v1 = abs(c) > 1e-12 ? normalize(vec2(c, l1 - a)) : (a >= d ? vec2(1, 0) : vec2(0, 1));
  vec2 v2 = vec2(-v1.y, v1.x);
  // splats under a pixel would drop between pixel centres and twinkle: hold them at a minimum size and keep their energy
  float L1 = sqrt(l1), L2 = sqrt(l2), m = 0.75, r = 1.0;
  if (L1 < m) { r *= L1 / m; L1 = m; }
  if (L2 < m) { r *= L2 / m; L2 = m; }
  A = D0.w * r;
  uv = corner;
  vec2 p = pc.xy * k + corner.x * L1 * v1 + corner.y * L2 * v2;
  gl_Position = vec4(p / (0.5 * res), 0.0, 1.0);
}`;

const FS = `#version 300 es
precision highp float;
flat in vec3 E;
flat in float A;
in vec2 uv;
out vec4 o;
void main(){
  float r2 = dot(uv, uv);
  if (r2 >= 1.0) discard;
  float a = min(A * exp(-5.0 * r2) * (1.0 - r2), 0.995);
  o = vec4(E * a, a);
}`;

const RVS = `#version 300 es
void main(){gl_Position = vec4(gl_VertexID == 1 ? 3.0 : -1.0, gl_VertexID == 2 ? 3.0 : -1.0, 0.0, 1.0);}`;

const RFS = `#version 300 es
precision highp float; precision highp sampler2D;
uniform sampler2D t;
uniform int ss;
out vec4 o;
void main(){
  ivec2 p = ivec2(gl_FragCoord.xy) * ss;
  vec3 c = vec3(0);
  for (int y = 0; y < ss; y++) for (int x = 0; x < ss; x++) c += texelFetch(t, p + ivec2(x, y), 0).rgb;
  c = clamp(c / float(ss * ss), 0.0, 1.0);
  o = vec4(mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)), 1.0);
}`;

const prog = (gl, vs, fs) => {
  const p = gl.createProgram();
  [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]].forEach(([k, src]) => {
    const s = gl.createShader(k);
    gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    gl.attachShader(p, s);
  });
  gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
  return p;
};

const dataTex = (gl, unit, data, texels) => {
  const h = Math.ceil(texels / TEXW), t = gl.createTexture(), full = new Float32Array(TEXW * h * 4);
  full.set(data);
  gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32F, TEXW, h, 0, gl.RGBA, gl.FLOAT, full);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  return {tex: t, h, full};
};

const init = async (canvas, ss) => {
  const gl = canvas.getContext("webgl2", {antialias: false, alpha: false, preserveDrawingBuffer: true, powerPreference: "high-performance"});
  if (!gl) throw new Error("no WebGL2");
  if (!gl.getExtension("EXT_color_buffer_float")) throw new Error("no float framebuffer");
  const dbg = gl.getExtension("WEBGL_debug_renderer_info");
  console.log("GL renderer:", dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : "?", "float blend:", !!gl.getExtension("EXT_float_blend"));
  const {n, focal} = await (await fetch(`${URL_}/meta`)).json();
  const stat = new Float32Array(await (await fetch(`${URL_}/static`)).arrayBuffer());
  const S = dataTex(gl, 0, stat, n * 4), D = dataTex(gl, 1, new Float32Array(0), n * 3);
  const P = prog(gl, VS, FS), R = prog(gl, RVS, RFS);
  const u = (p, k) => gl.getUniformLocation(p, k);
  const fbTex = gl.createTexture();
  gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, fbTex);
  gl.texStorage2D(gl.TEXTURE_2D, 1, gl.RGBA32F, W * ss, H * ss);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  const fb = gl.createFramebuffer();
  gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, fbTex, 0);
  const vao = gl.createVertexArray(), quad = gl.createBuffer(), ids = gl.createBuffer();
  gl.bindVertexArray(vao);
  gl.bindBuffer(gl.ARRAY_BUFFER, quad);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
  gl.bindBuffer(gl.ARRAY_BUFFER, ids);
  gl.bufferData(gl.ARRAY_BUFFER, n * 4, gl.DYNAMIC_DRAW);
  gl.enableVertexAttribArray(1); gl.vertexAttribIPointer(1, 1, gl.UNSIGNED_INT, 0, 0); gl.vertexAttribDivisor(1, 1);
  return {gl, n, focal, S, D, P, R, u, fb, fbTex, ids, vao, order: new Uint32Array(n), depth: new Float32Array(n), ss};
};

const draw = (c, buf) => {
  const {gl, n, focal, D, P, R, u, fb, ids, vao, order, depth, ss} = c;
  const m = buf.subarray(0, 16), d = buf.subarray(16);
  const pos = [m[3], m[7], m[11]], z = [m[2], m[6], m[10]];
  D.full.set(d);
  gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, D.tex);
  gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, TEXW, D.h, gl.RGBA, gl.FLOAT, D.full);
  // back-to-front, 16-bit counting sort of the visible splats
  let live = 0, lo = Infinity, hi = -Infinity;
  for (let i = 0; i < n; i++) {
    const k = i * 12;
    if (d[k + 3] <= 0 || d[k + 4] === 0) continue;
    const e = (d[k] - pos[0]) * z[0] + (d[k + 1] - pos[1]) * z[1] + (d[k + 2] - pos[2]) * z[2];
    order[live] = i; depth[live++] = e;
    if (e < lo) lo = e;
    if (e > hi) hi = e;
  }
  const bins = new Uint32Array(65537), sc = 65535 / Math.max(hi - lo, 1e-6), sorted = new Uint32Array(live);
  for (let i = 0; i < live; i++) bins[((depth[i] - lo) * sc | 0) + 1]++;
  for (let i = 0; i < 65536; i++) bins[i + 1] += bins[i];
  for (let i = 0; i < live; i++) sorted[bins[(depth[i] - lo) * sc | 0]++] = order[i];
  gl.bindBuffer(gl.ARRAY_BUFFER, ids); gl.bufferSubData(gl.ARRAY_BUFFER, 0, sorted);
  // world -> camera = inverse of the rigid camera matrix
  const V = new Float32Array([
    m[0], m[1], m[2], 0, m[4], m[5], m[6], 0, m[8], m[9], m[10], 0,
    -(m[0] * pos[0] + m[4] * pos[1] + m[8] * pos[2]), -(m[1] * pos[0] + m[5] * pos[1] + m[9] * pos[2]), -(m[2] * pos[0] + m[6] * pos[1] + m[10] * pos[2]), 1]);
  gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
  gl.viewport(0, 0, W * ss, H * ss);
  gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
  gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
  gl.useProgram(P); gl.bindVertexArray(vao);
  gl.uniform1i(u(P, "tS"), 0); gl.uniform1i(u(P, "tD"), 1);
  gl.uniformMatrix4fv(u(P, "V"), false, V);
  gl.uniform3f(u(P, "camPos"), pos[0], pos[1], pos[2]);
  gl.uniform2f(u(P, "res"), W * ss, H * ss);
  gl.uniform1f(u(P, "fpx"), W * ss * focal);
  gl.drawArraysInstanced(gl.TRIANGLE_STRIP, 0, 4, live);
  gl.disable(gl.BLEND);
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  gl.viewport(0, 0, W, H);
  gl.useProgram(R);
  gl.uniform1i(u(R, "t"), 2); gl.uniform1i(u(R, "ss"), ss);
  gl.drawArrays(gl.TRIANGLES, 0, 3);
  gl.finish();
};

const SplatFast = ({ss = 2}) => {
  const frame = useCurrentFrame(), ref = useRef(null), ctx = useRef(null);
  useLayoutEffect(() => {
    const h = delayRender(`splat ${frame}`, {timeoutInMilliseconds: 120000});
    (async () => {
      ctx.current = ctx.current || await init(ref.current, ss);
      const t0 = performance.now();
      const buf = new Float32Array(await (await fetch(`${URL_}/state/${frame}`)).arrayBuffer());
      const t1 = performance.now();
      draw(ctx.current, buf);
      console.log(`frame ${frame} state ${(t1 - t0).toFixed(0)} ms, draw ${(performance.now() - t1).toFixed(0)} ms`);
      continueRender(h);
    })().catch(e => { console.error(e); throw e; });
  }, [frame, ss]);
  return <canvas ref={ref} width={W} height={H} style={{width: W, height: H, display: "block", background: "#000"}}/>;
};

const Root = () => <Composition id="SplatFast" component={SplatFast} durationInFrames={300} fps={30} width={W} height={H} defaultProps={{ss: 2}}/>;
registerRoot(Root);
