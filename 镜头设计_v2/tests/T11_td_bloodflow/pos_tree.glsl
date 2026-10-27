// Black-and-white stage version: one artery that keeps splitting into a branching tree across the frame.
// Each particle picks its branch at every split from its own hash bits, so the flow divides like real vasculature.
// uQ.x = seconds since the last strong kick: a bright pulse front runs down the tree after every beat.
uniform vec4 uQ;

const int SEG = 6;
const float LEN[SEG] = float[](58.0, 30.0, 24.0, 19.0, 15.0, 11.0);
const float TURN[SEG] = float[](0.0, 0.42, 0.38, 0.40, 0.45, 0.55);

// walk the tree to arclength fraction s; returns position, writes direction, radius and branch depth reached
vec3 treeWalk(uint i, float s, out vec3 dir, out float radius, out float depth) {
    float total = 0.0;
    for (int k = 0; k < SEG; k++) total += LEN[k];
    float d = s * total;
    vec3 p = vec3(-98.0, -4.0, 0.0);
    dir = vec3(1.0, 0.0, 0.0);
    radius = 6.5; depth = 0.0;
    uint path = 1u;   // which branch this particle took at every split so far (one bit per split)
    for (int k = 0; k < SEG; k++) {
        if (k > 0) {
            uint bit = hash(i, uint(30 + k)) < 0.5 ? 0u : 1u;
            path = path * 2u + bit;
            // the bend belongs to the branch, not the particle, so every particle on a branch follows the same vessel
            float a = (bit == 0u ? -1.0 : 1.0) * TURN[k] * (0.7 + 0.6 * hash(path, uint(40 + k)));
            float tilt = (hash(path, uint(50 + k)) - 0.5) * 0.5;      // a little depth so it is not flat
            dir = normalize(vec3(dir.x * cos(a) - dir.y * sin(a), dir.x * sin(a) + dir.y * cos(a), dir.z + tilt));
            radius *= 0.68;
        }
        float seg = min(d, LEN[k]);
        // gentle bow inside each segment
        vec3 side = normalize(cross(dir, vec3(0.0, 0.0, 1.0)));
        p += dir * seg + side * sin(seg / LEN[k] * 3.14159) * 1.6 * float(k > 0);
        d -= seg;
        depth = float(k) + seg / LEN[k];
        if (d <= 0.0) break;
    }
    return p;
}

out vec4 fragColor;

void main() {
    uint i = texelIndex();
    int kind = kindOf(i);
    vec4 st = texture(sTD2DInputs[0], vUV.st);
    float kick = uP.x, s = clamp(st.x, 0.0, 1.0);
    vec3 dir; float R, depth;
    vec3 c = treeWalk(i, s, dir, R, depth);
    vec3 n = normalize(cross(dir, vec3(0.0, 0.0, 1.0)));
    vec3 b = cross(dir, n);
    R *= 1.0 + 0.25 * kick;                      // vessels swell on the beat

    vec3 p;
    float size;
    if (kind == 3) {
        // faint tissue dust around the branch tips (where the liver would be)
        vec3 u = normalize(vec3(hash(i, 10u), hash(i, 11u), hash(i, 12u)) * 2.0 - 1.0) * pow(hash(i, 13u), 0.5);
        p = vec3(40.0, 0.0, 0.0) + u * vec3(48.0, 46.0, 22.0);
        size = 0.5;
    } else {
        float r = kind == 2 ? 1.0 : st.z;
        float ang = kind == 2 ? hash(i, 3u) * 6.2831853 : st.y;
        p = c + (n * cos(ang) + b * sin(ang)) * r * R;
        size = kind == 0 ? 0.45 : kind == 1 ? 1.1 : 0.28;
        if (kind == 1 && st.w > 0.0) p += vec3(hash(i, 14u) - 0.5, hash(i, 15u) - 0.5, 0.0) * 18.0 * smoothstep(0.0, 1.2, st.w);
    }
    // pulse front: how far down the tree the last beat has travelled (in path fraction)
    float front = uQ.x * 0.55;
    float pulse = exp(-pow((s - front) / 0.035, 2.0)) * (kind <= 2 ? 1.0 : 0.0);
    fragColor = TDOutputSwizzle(vec4(p, size * (1.0 + 1.2 * pulse)));
}
