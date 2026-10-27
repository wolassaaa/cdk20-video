// Real AlphaFold CDK20 atoms. input 0: atoms (xyz Å around the pocket, w = pLDDT), input 1: meta (residue, kind, element, isCA)
// 0-4 s  the low-confidence C-terminal tail (res >= 303) boils unsteadily where it sits in the pocket
// 4-6 s  the tail peels away (the study removed it before designing drugs)
// 6-7 s  our re-docked 048 drops into the opened pocket and locks on
out vec4 fragColor;

void main() {
    uint i = texelIndex() ;
    ivec2 px = ivec2(gl_FragCoord.xy);
    vec4 a = texelFetch(sTD2DInputs[0], px, 0);
    vec4 m = texelFetch(sTD2DInputs[1], px, 0);
    float f = uP.z, t = f / 30.0, kick = uP.x;
    if (m.y < -0.5) { fragColor = TDOutputSwizzle(vec4(0.0, 0.0, 0.0, 0.0)); return; }   // padding

    vec3 p = a.xyz;
    float conf = a.w / 100.0, size = m.w > 0.5 ? 0.7 : 0.42;
    // hand-drawn boil: low-confidence atoms jump to a new spot every 3 frames, the more uncertain the further
    float stepN = floor(f / 3.0);
    vec3 j = vec3(hash(i, uint(stepN)), hash(i, uint(stepN) + 7u), hash(i, uint(stepN) + 13u)) - 0.5;
    p += j * 2.0 * pow(1.0 - conf, 2.0) * 3.0;

    if (m.y < 0.5 && m.x >= 303.0) {                       // the tail
        float peel = smoothstep(4.0, 6.0, t);
        p += normalize(p + vec3(0.0, 0.01, 0.0)) * peel * 34.0 + vec3(0.0, -22.0, 6.0) * peel * peel;
        size *= 1.0 - 0.8 * peel;
    }
    if (m.y > 0.5) {                                        // the ligand
        float arrive = clamp((t - 6.0) / 1.1, 0.0, 1.0);
        float e = 1.0 + 2.7 * pow(arrive - 1.0, 3.0) + 1.7 * pow(arrive - 1.0, 2.0);   // ease out with a little overshoot
        p += vec3(4.0, 30.0, 22.0) * (1.0 - e);
        size = t < 6.0 ? 0.0 : 1.15;
    }
    p *= 1.0 + 0.015 * kick;
    fragColor = TDOutputSwizzle(vec4(p, size));
}
