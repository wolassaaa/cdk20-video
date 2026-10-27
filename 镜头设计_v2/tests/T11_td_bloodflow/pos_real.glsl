// Flow along the REAL liver vessels (BodyParts3D v4 centrelines). input 1: paths (128 samples x P rows, xyz + radius),
// input 2: liver surface points. uR = row ranges: [0, uR.x) portal vein, [uR.x, uR.y) hepatic veins, [uR.y, uR.z) hepatic artery.
// Hepatic veins carry blood OUT of the liver, so their particles run from the tips back to the root.
uniform vec4 uQ;
uniform vec4 uR;
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
        size = 0.3;
    } else {
        float rowf = floor(hash(i, 60u) * uR.z);
        float sp = (rowf >= uR.x && rowf < uR.y) ? 1.0 - s : s;   // veins drain outward
        float row = (rowf + 0.5) / float(ps.y);
        float u = (sp * float(ps.x - 1) + 0.5) / float(ps.x);
        vec4 c = texture(sTD2DInputs[1], vec2(u, row));
        vec3 ahead = texture(sTD2DInputs[1], vec2(min(u + 1.0 / float(ps.x), 1.0), row)).xyz;
        vec3 t = normalize(ahead - c.xyz + vec3(1e-4, 0.0, 0.0));
        vec3 n = normalize(cross(t, abs(t.y) < 0.9 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0)));
        vec3 b = cross(t, n);
        float R = max(c.w, 0.25) * (1.0 + 0.25 * kick);
        float r = kind == 2 ? 1.0 : st.z * 0.7;
        float ang = kind == 2 ? hash(i, 3u) * 6.2831853 : st.y;
        p = c.xyz + (n * cos(ang) + b * sin(ang)) * r * R;
        size = kind == 0 ? 0.26 : kind == 1 ? 0.8 : 0.16;
        if (kind == 1 && st.w > 0.0)
            p += normalize(vec3(hash(i, 14u), hash(i, 15u), hash(i, 16u)) - 0.5) * 5.0 * smoothstep(0.0, 1.2, st.w);
    }
    float pulse = exp(-pow((s - uQ.x * 0.55) / 0.035, 2.0)) * (kind <= 2 ? 1.0 : 0.0);
    fragColor = TDOutputSwizzle(vec4(p, size * (1.0 + 1.0 * pulse)));
}
