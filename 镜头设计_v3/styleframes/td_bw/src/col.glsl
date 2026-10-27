// Per-particle colour: warm fluorescence for the body (carbon), cyan for the drug (silicon).
out vec4 fragColor;

void main() {
    uint i = texelIndex();
    int kind = kindOf(i);
    vec4 st = texture(sTD2DInputs[0], vUV.st);
    float kick = uP.x, v = 0.6 + 0.4 * hash(i, 20u);
    vec3 c;
    if (kind == 0) c = vec3(1.0, 0.14, 0.2) * v * (0.10 + 0.10 * kick);         // red cells
    else if (kind == 1) c = vec3(0.45, 0.92, 1.0) * (0.8 + 0.7 * kick + 1.0 * smoothstep(0.6, 1.4, st.w)); // drug
    else if (kind == 2) c = vec3(1.0, 0.62, 0.28) * 0.30 * (1.0 + 1.5 * kick);   // vessel wall
    else c = vec3(1.0, 0.5, 0.18) * 0.16 * v * (1.0 + 0.8 * kick);               // liver tissue
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
