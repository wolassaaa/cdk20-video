#!/bin/bash
# rebuild every recoloured plate in the reel public dir from the original option plates (+ the reel's own fontana renders)
cd "/d/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code"; P=reel/public; mkdir -p $P/plates
R="python reel/py/recolor.py"; H="--hue 2.5"
for s in hit1 hit2 hit3 1-01; do python w0/post.py reel/raw/fontana_$s.png $P/fontana_$s.png >/dev/null; $R $P/fontana_$s.png $P/fontana_$s.png $H; done
$R s102/public/liver_hero.png $P/liver_hero.png $H --pull 0.5
$R s102/public/vitrine_row.png $P/vitrine_row.png $H --pull 0.5
for f in pigment_a_v2 pigment_b pigment_c; do $R s104/public/$f.png $P/$f.png $H --val 0.86; done
for f in neon_full neon_lit4 neon_lit2; do $R s108/public/plates/$f.png $P/plates/$f.png $H; done
for f in p_plddt m_bluesea m_bluesea_close; do $R s110/public/$f.png $P/$f.png $H; done
cp s110/public/w_pigment.png $P/; cp "../../../../remotion_public/placeholder_hand.mp4" $P/
python reel/py/redstats.py $P/*.png $P/plates/*.png
