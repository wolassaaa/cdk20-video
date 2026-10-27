// Real-vessel colours: the blood is red in all three trees (hepatic artery brightest cinnabar, portal vein deep red,
// hepatic veins darkest), the vessel walls are white ink, the liver surface is faint dust, drug molecules are cyan sparks.
uniform vec4 uQ;
uniform vec4 uR;
out vec4 fragColor;

void main() {
    uint i = texelIndex();
    int kind = kindOf(i);
    vec4 st = texture(sTD2DInputs[0], vUV.st);
    float kick = uP.x, s = clamp(st.x, 0.0, 1.0), v = 0.6 + 0.4 * hash(i, 20u);
    float rowf = floor(hash(i, 60u) * uR.z);
    int grp = rowf < uR.x ? 0 : (rowf < uR.y ? 1 : 2);
    float pulse = exp(-pow((s - uQ.x * 0.55) / 0.035, 2.0));
    vec3 blood = grp == 2 ? vec3(1.0, 0.3, 0.15) * (0.7 + 1.0 * kick)      // hepatic artery: oxygen-rich, brightest
               : grp == 0 ? vec3(0.85, 0.12, 0.07) * (0.8 + 0.5 * kick)    // portal vein: deep red
               : vec3(0.5, 0.06, 0.04);                                     // hepatic veins: darkest, draining out
    vec3 c;
    if (kind == 0) c = blood * v * (0.14 + 0.1 * kick + 0.7 * pulse);
    else if (kind == 1) c = vec3(0.16, 0.94, 1.0) * (0.8 + 0.6 * kick);
    else if (kind == 2) c = vec3(0.03 * (1.0 + 1.2 * kick) + 0.2 * pulse);   // walls: thin white ink, dim so the red reads
    else c = vec3(0.07 * v);
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
