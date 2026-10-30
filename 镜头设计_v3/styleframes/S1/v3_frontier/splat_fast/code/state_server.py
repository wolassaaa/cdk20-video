"""Serves splat state to the WebGL renderer over localhost, so nothing per-frame has to be stored on disk.
python state_server.py [--port 8765]
  /meta        -> JSON {n, focal}
  /static      -> float32, 16 per splat: rotation columns (each followed by one normal component), rim, spec, dif, 0
  /state/<f>   -> float32, 16 (camera matrix, row-major) + 12 per splat: pos+alpha, scale+glow, col+0
"""
import argparse, json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import numpy as np
import splat_state as st

ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8765); A = ap.parse_args()

E = np.concatenate([st.E0, np.zeros((st.NN, 3), np.float32)]).astype(np.float64)
NRM = np.concatenate([st.NRM, np.tile([0, 0, 1.0], (st.NN, 1))])
RIM = np.concatenate([st.RIM, np.zeros(st.NN)]); SPEC = np.concatenate([st.SPEC, np.zeros(st.NN)]); DIF = np.concatenate([st.DIF, np.zeros(st.NN)])


def rot_cols(e):
    """Blender XYZ euler: R = Rz Ry Rx, returned as its three columns"""
    cx, sx, cy, sy, cz, sz = np.cos(e[:, 0]), np.sin(e[:, 0]), np.cos(e[:, 1]), np.sin(e[:, 1]), np.cos(e[:, 2]), np.sin(e[:, 2])
    return (np.stack([cz * cy, sz * cy, -sy], 1),
            np.stack([cz * sy * sx - sz * cx, sz * sy * sx + cz * cx, cy * sx], 1),
            np.stack([cz * sy * cx + sz * sx, sz * sy * cx - cz * sx, cy * cx], 1))


c0, c1, c2 = rot_cols(E)
STATIC = np.concatenate([c0, NRM[:, :1], c1, NRM[:, 1:2], c2, NRM[:, 2:], RIM[:, None], SPEC[:, None], DIF[:, None], np.zeros((st.TOTAL, 1))], 1).astype(np.float32).tobytes()
print("ready", st.TOTAL, flush=True)


class H(BaseHTTPRequestHandler):
    def reply(self, body, ctype="application/octet-stream"):
        self.send_response(200); self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        p = self.path
        if p == "/meta":
            self.reply(json.dumps({"n": st.TOTAL, "focal": st.LENS / st.SENSOR}).encode(), "application/json")
        elif p == "/static":
            self.reply(STATIC)
        elif p.startswith("/state/"):
            f = int(p.split("/")[2])
            P, S, Co, Al, Gl = st.state(f)
            d = np.concatenate([P, Al[:, None], S, Gl[:, None], Co, np.zeros((st.TOTAL, 1))], 1).astype(np.float32)
            self.reply(np.array(st.cam_matrix(f), np.float32).tobytes() + d.tobytes())
        else:
            self.send_error(404)

    def log_message(self, *a):
        pass


ThreadingHTTPServer(("127.0.0.1", A.port), H).serve_forever()
