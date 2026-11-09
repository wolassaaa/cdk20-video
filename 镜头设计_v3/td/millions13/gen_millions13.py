# HKBU SCIE1007 coursework science video. Data for the "millions -> 13" dot sample: a computer screening millions of candidates down to 13 (S6 6-02, S8 8-03 will use it; the sample is only a drawing).
# Makes the real point set: 2,097,152 dots (a 2048 x 1024 table, one dot per texel), each with a position on the 1920 x 1080 table and the wave that screens it out.
# Prints the counts. Run: python gen_millions13.py   ->  C:/render_tmp/td_m13/m13_data.npy (float32, 1024 x 2048 x 4: x, y in px from the centre, y up; stage 0-4; a random 0-1) and m13_meta.json.
import json
import numpy as np

W, H = 1920, 1080
NX, NY = 2048, 1024
N = NX * NY
KEEP = [150_000, 7_500, 380, 13]       # how many dots are still there after each of the four waves
rng = np.random.default_rng(1307)

# every dot sits at a jittered grid point, so the table is covered evenly and no two lie on top of each other
ix, iy = np.meshgrid(np.arange(NX), np.arange(NY))
x = ((ix + rng.random((NY, NX))) / NX - 0.5) * W
y = ((iy + rng.random((NY, NX))) / NY - 0.5) * H
rand = rng.random((NY, NX))

# which dots survive which wave: a random order, the first 13 last through all four
order = rng.permutation(N)
stage = np.zeros(N, dtype=np.int32)           # stage k: screened out by wave k+1; stage 4: never screened out
for k, keep in enumerate(KEEP):
    stage[order[:keep]] = k + 1
flat_x, flat_y = x.reshape(-1).copy(), y.reshape(-1).copy()

# the last 13 sit in the middle of the table, not too close to each other (Poisson-disc style), the 380 before them in a wider middle
final = []
while len(final) < 13:
    c = np.array([rng.uniform(-620, 620), rng.uniform(-300, 300)])
    if all(np.hypot(*(c - f)) > 150 for f in final):
        final.append(c)
final = np.array(final)
fin_idx = order[:13]
flat_x[fin_idx], flat_y[fin_idx] = final[:, 0], final[:, 1]
s3 = order[13:KEEP[2]]
flat_x[s3] = rng.normal(0, 360, len(s3)).clip(-850, 850)
flat_y[s3] = rng.normal(0, 190, len(s3)).clip(-470, 470)

data = np.stack([flat_x.reshape(NY, NX), flat_y.reshape(NY, NX), stage.reshape(NY, NX).astype(np.float64), rand], axis=-1).astype(np.float32)
np.save("C:/render_tmp/td_m13/m13_data.npy", data)
counts = {int(k): int((stage == k).sum()) for k in range(5)}
alive = [int((stage >= k).sum()) for k in range(5)]           # dots still there before wave 1, after wave 1 ... after wave 4
json.dump(dict(total=N, grid=[NX, NY], stage_counts=counts, alive_after_wave=alive, final_xy=final.tolist()), open("C:/render_tmp/td_m13/m13_meta.json", "w"))
print("dots at the start:", N)
print("dots still there after each wave:", alive[1:])
print("dots left at the end (stage 4):", counts[4])
assert N >= 2_000_000 and counts[4] == 13
