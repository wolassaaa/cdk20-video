// Shared by the blood-flow shaders. Particle state lives in a 512x256 float texture, one texel per particle:
// x = s (0..1 along the vessel), y = angle round the vessel, z = radius fraction, w = drug escape progress.
// Each particle's kind comes from a hash of its texel index, so it never needs storing.
uniform vec4 uP;   // x = kick envelope, y = time (s), z = frame, w = reset

uint hashu(uint x) { x ^= x >> 16; x *= 0x7feb352du; x ^= x >> 15; x *= 0x846ca68bu; x ^= x >> 16; return x; }
float hash(uint i, uint k) { return float(hashu(i * 0x9E3779B9u + k * 0x85EBCA6Bu)) / 4294967296.0; }
uint texelIndex() { ivec2 p = ivec2(gl_FragCoord.xy); return uint(p.y * 512 + p.x); }

// kinds: 0 red blood cell, 1 drug molecule, 2 vessel wall, 3 liver tissue
int kindOf(uint i) {
    float h = hash(i, 1u);
    return h < 0.66 ? 0 : h < 0.668 ? 1 : h < 0.80 ? 2 : 3;   // ~1,000 drug molecules
}

// the artery: sweeps in from the left and fans into the liver on the right
vec3 vesselC(float s) {
    return vec3(-75.0 + 115.0 * s, -14.0 + 22.0 * s - 10.0 * sin(s * 3.6), -18.0 * sin(s * 2.4 + 0.3));
}
float vesselR(float s, float kick) {
    float taper = mix(7.0, 4.4, smoothstep(0.0, 0.75, s));
    return taper * (1.0 + 0.22 * kick);   // the wall dilates on each beat
}
vec3 liverCenter() { return vesselC(1.0) + vec3(18.0, 2.0, -4.0); }
