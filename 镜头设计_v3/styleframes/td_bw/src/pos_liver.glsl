// Flow along a vessel tree grown inside the real liver shape.
// input 1: paths texture, 128 samples (x) by 256 root-to-leaf paths (y): xyz + vessel radius
// input 2: liver surface points, 200 per row: xyz (the real silhouette, drawn as faint dust)
uniform vec4 uQ;
out vec4 fragColor;

void main() {
    uint i = texelIndex();
    int kind = kindOf(i);
    vec4 st = texture(sTD2DInputs[0], vUV.st);
    float kick = uP.x, s = clamp(st.x, 0.0, 1.0);
    ivec2 ps = textureSize(sTD2DInputs[1], 0);

    vec3 p;
    float size;
    if (kind == 3) {
        ivec2 ss = textureSize(sTD2DInputs[2], 0);
        int k = int(i % uint(ss.x * ss.y));
        p = texelFetch(sTD2DInputs[2], ivec2(k % ss.x, k / ss.x), 0).xyz;
        size = 0.35;
    } else {
        float row = (floor(hash(i, 60u) * float(ps.y)) + 0.5) / float(ps.y);
        float u = (s * float(ps.x - 1) + 0.5) / float(ps.x);
        vec4 c = texture(sTD2DInputs[1], vec2(u, row));
        vec3 ahead = texture(sTD2DInputs[1], vec2(min(u + 1.0 / float(ps.x), 1.0), row)).xyz;
        vec3 t = normalize(ahead - c.xyz + vec3(1e-4, 0.0, 0.0));
        vec3 n = normalize(cross(t, abs(t.y) < 0.9 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0)));
        vec3 b = cross(t, n);
        float R = c.w * (1.0 + 0.25 * kick);
        float r = kind == 2 ? 1.0 : st.z * 0.6;   // blood keeps to the middle of the vessel so branches read as lines
        float ang = kind == 2 ? hash(i, 3u) * 6.2831853 : st.y;
        p = c.xyz + (n * cos(ang) + b * sin(ang)) * r * R;
        size = kind == 0 ? 0.32 : kind == 1 ? 0.9 : 0.2;
        if (kind == 1 && st.w > 0.0)   // the drug leaves the capillary into the tissue around it
            p += normalize(vec3(hash(i, 14u), hash(i, 15u), hash(i, 16u)) - 0.5) * 6.0 * smoothstep(0.0, 1.2, st.w);
    }
    float pulse = exp(-pow((s - uQ.x * 0.55) / 0.035, 2.0)) * (kind <= 2 ? 1.0 : 0.0);
    fragColor = TDOutputSwizzle(vec4(p, size * (1.0 + 1.0 * pulse)));
}
