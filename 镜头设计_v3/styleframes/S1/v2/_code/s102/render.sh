#!/bin/sh
# Bundle the s102 Remotion entry and render every still. Usage: sh render.sh [compId ...]
R="D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion"
CODE="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s102"
OUT="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2"
BUNDLE="$CODE/bundle"
cd "$R"
npx remotion bundle src/v3/s1v2/s102/entry.jsx --out-dir="$BUNDLE" --public-dir="$CODE/public" >/dev/null || exit 1
still() { npx remotion still "$BUNDLE" "$1" "$2" --frame="${3:-0}" --log=error; }
ALL="${*:-all}"
want() { [ "$ALL" = all ] || echo " $ALL " | grep -q " $1 "; }
want fog         && still s102-fog         "$OUT/1-02/opt1_fog-tally.png"
want tally       && still s102-tally       "$OUT/1-02/opt1_fog-tally_b-2d-ink.png"
want liver       && still s102-liver       "$OUT/1-02/opt2_liver.png"
want liver-world && still s102-liver-world "$OUT/1-02/opt2_liver_b-world.png"
want beads       && still s102-beads       "$OUT/1-02/opt3_year-beads.png"
want year        && still s102-year        "$OUT/1-02/opt3_year-beads_b-2d.png"
want ikeda       && still s102-ikeda       "$OUT/1-02/opt4_ikeda.png"
want ikeda-world && still s102-ikeda-world "$OUT/1-02/opt4_ikeda_b-world.png"
want globe3d     && still s102-globe3d     "$OUT/1-02/opt5_globe.png"
want globe       && still s102-globe       "$OUT/1-02/opt5_globe_b-2d.png"
want chain       && still s102-chain       "$OUT/1-02/opt6_chain.png"
want capsules    && still s103-capsules    "$OUT/1-03/opt1_ink-capsules.png" 70
want beaker3d    && still s103-beaker3d    "$OUT/1-03/opt2_beaker.png" 70
want vessel      && still s103-vessel      "$OUT/1-03/opt2_beaker_b-ink.png" 70
want capsule3d   && still s103-capsule3d   "$OUT/1-03/opt3_glass-capsule.png" 70
want words       && still s103-words       "$OUT/1-03/opt4_words.png" 70
