// reel2/motion: three beats from v1 stills turned into real animation (W0 + 1-01 Fontana cuts, 1-08 Swiss ledger, 1-09 neon metro).
// Assets: public/motion/fontana/*.jpg (Blender, fontana_anim.py + post_seq.py), public/motion/neon/*.png (neon_layers.py).
// Code for the renders: 镜头设计_v3/styleframes/S1/v2/_code/reel2/motion/.
import {C} from "../../../core";
import {P as P108} from "../../s108/common";

// s108 keeps its red in a shared palette object (#FF1A2E, pinkish): point it at blood red, as reel/entry.jsx does.
P108.red = C.verm;

export {BeatW0, Beat101Bg, DUR_W0, DUR_101} from "./fontana";
export {Beat108, DUR_108} from "./ledger";
export {Beat109, DUR_109} from "./neon";
