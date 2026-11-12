"""HKBU SCIE1007 coursework video: person-matting models behind one interface (footage pipeline, step 4).

Every model: m = Model(); alpha = m.frame(bgr_uint8) -> uint8 alpha, same size as the frame. Frames are
fed one at a time in order (never the whole clip in memory); m.reset() starts a new clip.
composite() puts the person on a flat backdrop.
"""
import numpy as np
import torch

import common as C


class RVM:
    """RobustVideoMatting (resnet50): recurrent, made for video, carries memory from frame to frame."""
    name = "rvm_resnet50"

    def __init__(self):
        self.model = torch.hub.load("PeterL1n/RobustVideoMatting", "resnet50", trust_repo=True).eval().cuda().half()
        self.reset()

    def reset(self):
        self.rec = [None] * 4

    @torch.inference_mode()
    def alpha_t(self, rgb):
        """rgb: 1x3xHxW float 0..1 on the GPU -> HxW float alpha 0..1 on the GPU (nothing leaves the card)."""
        h, w = rgb.shape[-2:]
        ratio = min(1.0, 512 / max(h, w))          # the authors' advice: inner resolution around 512 px
        fgr, pha, *self.rec = self.model(rgb.half(), *self.rec, downsample_ratio=ratio)
        return pha[0, 0].float().clamp(0, 1)

    def frame(self, bgr):
        x = torch.from_numpy(bgr[:, :, ::-1].copy()).cuda().permute(2, 0, 1)[None].float() / 255
        return (self.alpha_t(x) * 255).round().byte().cpu().numpy()


class BiRefNet:
    """BiRefNet matting weights: per-frame, no memory between frames, fine edges."""
    name = "birefnet_matting"

    def __init__(self, repo="ZhengPeng7/BiRefNet-matting", size=1024):
        from transformers import AutoModelForImageSegmentation
        self.model = AutoModelForImageSegmentation.from_pretrained(repo, trust_remote_code=True).eval().cuda().half()
        self.size = size
        self.mean = torch.tensor([0.485, 0.456, 0.406], device="cuda").view(1, 3, 1, 1)
        self.std = torch.tensor([0.229, 0.224, 0.225], device="cuda").view(1, 3, 1, 1)

    def reset(self):
        pass

    @torch.inference_mode()
    def alpha_t(self, rgb):
        """rgb: 1x3xHxW float 0..1 on the GPU -> HxW float alpha 0..1 on the GPU."""
        h, w = rgb.shape[-2:]
        x = torch.nn.functional.interpolate(rgb.float(), (self.size, self.size), mode="bilinear", antialias=True)
        x = ((x - self.mean) / self.std).half()
        p = self.model(x)[-1].sigmoid().float()
        p = torch.nn.functional.interpolate(p, (h, w), mode="bilinear")
        return p[0, 0].clamp(0, 1)

    def frame(self, bgr):
        x = torch.from_numpy(bgr[:, :, ::-1].copy()).cuda().permute(2, 0, 1)[None].float() / 255
        return (self.alpha_t(x) * 255).round().byte().cpu().numpy()


class BiRefNetHR(BiRefNet):
    """BiRefNet_HR matting weights, 2048 px inside: slower, more memory, finer hair."""
    name = "birefnet_hr_matting"

    def __init__(self):
        super().__init__("ZhengPeng7/BiRefNet_HR-matting", 2048)


MODELS = {"rvm_resnet50": RVM, "birefnet_matting": BiRefNet, "birefnet_hr_matting": BiRefNetHR}


def hex_bgr(s):
    s = s.lstrip("#")
    return np.array([int(s[4:6], 16), int(s[2:4], 16), int(s[0:2], 16)], dtype=np.float32)


def composite(bgr, alpha, backdrop="#E2CDB0"):
    a = alpha.astype(np.float32)[:, :, None] / 255
    return (bgr.astype(np.float32) * a + hex_bgr(backdrop) * (1 - a)).round().astype(np.uint8)
