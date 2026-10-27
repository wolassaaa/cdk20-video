// Brightness = AlphaFold confidence (sure atoms are solid white, unsure ones are dim and flicker); the drug is the one colour.
out vec4 fragColor;

void main() {
    uint i = texelIndex();
    ivec2 px = ivec2(gl_FragCoord.xy);
    vec4 a = texelFetch(sTD2DInputs[0], px, 0);
    vec4 m = texelFetch(sTD2DInputs[1], px, 0);
    float f = uP.z, t = f / 30.0, kick = uP.x, conf = a.w / 100.0;
    float stepN = floor(f / 3.0);
    vec3 c;
    if (m.y > 0.5) {
        float lock = exp(-max(t - 7.1, 0.0) * 3.0) * step(7.1, t);
        c = vec3(0.16, 0.94, 1.0) * (1.1 + 0.6 * kick + 2.5 * lock);            // electric cyan #29F0FF
    } else {
        float g = 0.05 + 0.32 * pow(conf, 3.0);
        g *= mix(0.4 + 1.2 * hash(i, uint(stepN) + 31u), 1.0, conf);           // uncertainty flickers
        if (m.x >= 303.0) g *= 1.0 - smoothstep(4.5, 6.0, t);
        float near = exp(-length(a.xyz) / 6.0) * smoothstep(7.0, 7.4, t);       // pocket lights up once the drug is in
        g += near * (0.35 + 0.4 * kick);
        c = vec3(g);
    }
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
