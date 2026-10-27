// Black stage: blood is cinnabar red (#FF3B1F) so it reads as blood, vessel walls stay white ink, a bright pulse front
// runs down the tree after each beat, drug molecules are hard white sparks.
uniform vec4 uQ;
out vec4 fragColor;

void main() {
    uint i = texelIndex();
    int kind = kindOf(i);
    vec4 st = texture(sTD2DInputs[0], vUV.st);
    float kick = uP.x, s = clamp(st.x, 0.0, 1.0), v = 0.6 + 0.4 * hash(i, 20u);
    float pulse = exp(-pow((s - uQ.x * 0.55) / 0.035, 2.0));
    const vec3 BLOOD = vec3(1.0, 0.23, 0.12);
    vec3 c;
    if (kind == 0) c = BLOOD * v * (0.09 + 0.08 * kick + 0.7 * pulse) * mix(0.25, 1.0, smoothstep(0.25, 0.5, s));   // trunk is crowded: dim it so it reads as a tube
    else if (kind == 1) c = vec3(0.9 + 0.6 * kick);
    else if (kind == 2) c = vec3(0.035 * (1.0 + 1.2 * kick) + 0.25 * pulse);   // thin white wall, kept dim so piled-up walls do not wash the red out
    else c = vec3(0.07 * v);   // faint dust: the real liver outline (or tissue)
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
