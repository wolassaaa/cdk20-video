// State -> world position (rgb) and sprite size (a), for instancing.
out vec4 fragColor;

void main() {
    uint i = texelIndex();
    int kind = kindOf(i);
    vec4 st = texture(sTD2DInputs[0], vUV.st);
    float kick = uP.x, s = clamp(st.x, 0.0, 1.0);

    vec3 c = vesselC(s);
    vec3 t = normalize(vesselC(min(s + 0.01, 1.0)) - vesselC(max(s - 0.01, 0.0)));
    vec3 n = normalize(cross(t, vec3(0.0, 0.0, 1.0)));
    vec3 b = cross(t, n);
    float R = vesselR(s, kick);

    // past 70% the artery splits into branches that spread through the liver
    float fan = smoothstep(0.68, 1.0, s);
    float a = floor(hash(i, 8u) * 7.0) / 7.0 * 6.2831853 + 0.4;
    vec3 branch = (n * cos(a) + b * sin(a)) * fan * fan * 26.0 + t * fan * 6.0;
    R *= 1.0 - 0.55 * fan;

    vec3 p;
    float size;
    if (kind == 3) {
        // liver tissue: a lumpy lobe of cells round the end of the artery
        vec3 u = vec3(hash(i, 10u), hash(i, 11u), hash(i, 12u)) * 2.0 - 1.0;
        u = normalize(u) * pow(hash(i, 13u), 0.45);
        p = liverCenter() + u * vec3(30.0, 21.0, 20.0) + 2.5 * sin(u.yzx * 9.0);
        size = 0.75 * (1.0 + 0.25 * kick);
    } else {
        float r = kind == 2 ? 1.0 : st.z;
        float ang = kind == 2 ? hash(i, 3u) * 6.2831853 : st.y;
        p = c + (n * cos(ang) + b * sin(ang)) * r * R + branch;
        size = kind == 0 ? 0.6 : kind == 1 ? 1.6 : 0.32;
        if (kind == 1 && st.w > 0.0) {
            vec3 dest = liverCenter() + (vec3(hash(i, 14u), hash(i, 15u), hash(i, 16u)) - 0.5) * vec3(44.0, 30.0, 26.0);
            p = mix(p, dest, smoothstep(0.0, 1.2, st.w));
        }
    }
    fragColor = TDOutputSwizzle(vec4(p, size));
}
