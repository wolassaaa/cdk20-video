// Particle update, one texel per particle, fed back into itself every frame.
// Flow is faster in the middle of the vessel (parabolic profile) and surges on each kick, like a pulse.
out vec4 fragColor;

vec4 initState(uint i) {
    return vec4(hash(i, 2u), hash(i, 3u) * 6.2831853, sqrt(hash(i, 4u)), 0.0);
}

void main() {
    uint i = texelIndex();
    int kind = kindOf(i);
    vec4 st = texture(sTD2DInputs[0], vUV.st);
    // reset on the first frames, or when the texel still holds the seed sentinel (-1)
    if (uP.w > 0.5 || st.w < -0.5) { fragColor = TDOutputSwizzle(initState(i)); return; }
    if (kind >= 2) { fragColor = TDOutputSwizzle(st); return; }   // wall and tissue stay put

    float dt = 1.0 / 30.0, kick = uP.x;
    float profile = 1.0 - 0.65 * st.z * st.z;
    float v = 0.045 * (0.55 + 2.6 * pow(kick, 1.4)) * profile;
    st.x += v * dt * (kind == 1 ? 0.9 : 1.0);
    st.y += dt * (0.25 + 0.6 * kick) * (hash(i, 5u) - 0.5);           // slow swirl
    st.z = clamp(st.z + dt * 0.08 * (hash(i + uint(uP.z), 6u) - 0.5), 0.0, 1.0);

    if (kind == 1 && st.x > 0.82) st.w += dt * (0.35 + 0.8 * kick);   // drug leaves the vessel into liver tissue
    if (st.x > 1.0 || st.w > 1.6) {                                   // re-enter at the start
        st = vec4(st.x - floor(st.x), hash(i + uint(uP.z), 3u) * 6.2831853, sqrt(hash(i + uint(uP.z), 4u)), 0.0);
        if (kind == 1) st.x = hash(i + uint(uP.z), 7u) * 0.2;
    }
    fragColor = TDOutputSwizzle(st);
}
