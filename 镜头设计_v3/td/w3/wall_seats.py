"""HKBU SCIE1007 coursework science video. 4-10 in TouchDesigner: the same 8,918 dots from W3 drift into groups, 54 move to the ring, 7 stay. Writes wall_a.npy and wall_b.npy for TouchDesigner.

8,918, 54 and 7 are the paper's numbers. The number of groups and each dot's score are drawn for the picture, so the shot is tagged schematic.
Run after seats.py: python wall_seats.py
"""
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SHORT, PICK = 54, 7          # real: Ren 2023
GROUPS = 140
SQUEEZE = 0.24
R = 290

rng = np.random.default_rng(1007)
seat = np.load(os.path.join(HERE, "seats.npy"))[0, :, :2].astype(np.float64)
N = len(seat)

centres = seat[rng.choice(N, GROUPS, replace=False)]
for _ in range(4):
    who = ((seat[:, None] - centres[None]) ** 2).sum(2).argmin(1)
    centres = np.stack([seat[who == k].mean(0) if (who == k).any() else centres[k] for k in range(GROUPS)])
who = ((seat[:, None] - centres[None]) ** 2).sum(2).argmin(1)
group = centres[who] + (seat - centres[who]) * SQUEEZE + rng.normal(0, 5, (N, 2))

chosen = np.array([rng.choice(np.flatnonzero(who == k)) for k in rng.choice(GROUPS, SHORT, replace=False)])
chosen = chosen[np.argsort(np.arctan2(seat[chosen, 1], seat[chosen, 0]))]  # keep their order round the ring, so paths do not cross
slots = 2 * np.pi * (np.arange(SHORT) + 0.5) / SHORT - np.pi
ring = np.zeros((N, 2))
ring[chosen] = np.stack([np.cos(slots), np.sin(slots)], axis=1) * R

role = np.zeros(N)
role[chosen] = 1
role[chosen[np.round(np.arange(PICK) * SHORT / PICK).astype(int)]] = 2
score = rng.uniform(0, 1, N) ** 1.6
score[chosen] = 1

order = np.argsort(role, kind="stable")  # the ones that matter draw last, on top
a = np.concatenate([seat, group], axis=1)[order]
b = np.column_stack([ring, role, score])[order]
np.save(os.path.join(HERE, "wall_a.npy"), a.astype(np.float32)[None])
np.save(os.path.join(HERE, "wall_b.npy"), b.astype(np.float32)[None])
print("dots", N, "groups", len(set(who)), "sizes", np.bincount(who).min(), np.bincount(who).max(), "roles", np.bincount(role.astype(int)))
