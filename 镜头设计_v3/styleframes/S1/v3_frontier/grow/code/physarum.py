"""GROW / physarum: Jones (2010) multi-agent transport network, numpy, one process, deterministic.

Agents: position + heading, three forward sensors (left / centre / right at +-SA, distance SO).
Each step: sense trail -> turn by RA toward the strongest -> step SS (blocked by the allowed mask: pick a new
heading instead) -> deposit -> 3x3 mean diffuse -> multiply by (1 - DECAY).  Food (a chemo-attractant map) is
added to the trail every step.  Trail lives on a crop of the 1920x1080 frame at 1:1 pixels (no upscaling).
"""
import numpy as np


class Physarum:
    def __init__(self, allowed, seed=11, SA=22.5, RA=45.0, SO=9.0, SS=1.0, DEP=1.0, DECAY=0.1, DIFF=1.0):
        self.h, self.w = allowed.shape
        self.allowed = allowed.astype(np.float32)
        self.rng = np.random.default_rng(seed)
        self.SA, self.RA = np.deg2rad(SA), np.deg2rad(RA)
        self.SO, self.SS, self.DEP, self.DECAY, self.DIFF = SO, SS, DEP, DECAY, DIFF
        self.T = np.zeros((self.h, self.w), np.float32)
        self.keep_map = self.allowed.copy()   # per-pixel multiplier applied to the trail every step
        self.x = np.zeros(0, np.float32); self.y = np.zeros(0, np.float32); self.a = np.zeros(0, np.float32)

    def spawn(self, xs, ys):
        n = len(xs)
        self.x = np.concatenate([self.x, xs.astype(np.float32)])
        self.y = np.concatenate([self.y, ys.astype(np.float32)])
        self.a = np.concatenate([self.a, (self.rng.random(n) * 2 * np.pi).astype(np.float32)])

    def keep(self, sel):
        self.x, self.y, self.a = self.x[sel], self.y[sel], self.a[sel]

    def _sample(self, x, y):
        xi = np.clip(x.astype(np.int32), 0, self.w - 1)
        yi = np.clip(y.astype(np.int32), 0, self.h - 1)
        return self.T.ravel()[yi * self.w + xi]

    def step(self, food=None, food_gain=0.0, ss=None):
        ss = self.SS if ss is None else ss
        x, y, a = self.x, self.y, self.a
        n = len(x)
        if n:
            SO = self.SO
            c, s = np.cos(a), np.sin(a)
            F = self._sample(x + SO * c, y + SO * s)
            al, ar = a - self.SA, a + self.SA
            Lv = self._sample(x + SO * np.cos(al), y + SO * np.sin(al))
            Rv = self._sample(x + SO * np.cos(ar), y + SO * np.sin(ar))
            rnd = self.rng.random(n, dtype=np.float32)
            turn = np.zeros(n, np.float32)
            both = (F < Lv) & (F < Rv)
            turn[both] = np.where(rnd[both] < 0.5, -1.0, 1.0)
            one = ~both & ~((F >= Lv) & (F >= Rv))
            turn[one] = np.where(Lv[one] > Rv[one], -1.0, 1.0)
            a = a + turn * self.RA
            c, s = np.cos(a), np.sin(a)
            nx, ny = x + ss * c, y + ss * s
            xi = np.clip(nx.astype(np.int32), 0, self.w - 1)
            yi = np.clip(ny.astype(np.int32), 0, self.h - 1)
            ok = self.allowed.ravel()[yi * self.w + xi] > 0.5
            x = np.where(ok, nx, x); y = np.where(ok, ny, y)
            a = np.where(ok, a, (rnd * 7919.0) % (2 * np.pi)).astype(np.float32)
            self.x, self.y, self.a = x.astype(np.float32), y.astype(np.float32), a
            idx = np.clip(y.astype(np.int32), 0, self.h - 1) * self.w + np.clip(x.astype(np.int32), 0, self.w - 1)
            dep = np.bincount(idx, minlength=self.h * self.w).astype(np.float32).reshape(self.h, self.w)
            self.T += dep * self.DEP
        if food is not None and food_gain:
            self.T += food * food_gain
        # 3x3 mean diffuse (separable, edge-replicate)
        T = self.T
        p = np.pad(T, 1, mode="edge")
        hsum = p[:, :-2] + p[:, 1:-1] + p[:, 2:]
        B = (hsum[:-2] + hsum[1:-1] + hsum[2:]) * (1.0 / 9.0)
        T = T + (B - T) * self.DIFF
        T *= (1.0 - self.DECAY)
        T *= self.keep_map
        self.T = T
