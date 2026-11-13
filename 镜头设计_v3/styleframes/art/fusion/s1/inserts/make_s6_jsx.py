"""HKBU SCIE1007 coursework science video. S6 review cut: makes src/v3/fusion/s6.jsx from entry.jsx's shared parts (everything before its Root: fonts, Ink, Note,
Keyed, Print, Source...) and s6_body.jsx (the S6 words over bl_s6.py's take), with the take's camera from s6_track.json. entry.jsx is read, never changed.
Run: python make_s6_jsx.py   (4K 60 fps pass: python make_s6_jsx.py 4k -> s6_4k.jsx with s6_track_4k.json, composition S6-4K, review off)"""
import sys
K4 = sys.argv[1:] == ["4k"]
A = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/fusion/"
s = open(A + "entry.jsx", encoding="utf8").read()
root = "const Root = () => <>"
assert s.count(root) == 1
s = s[:s.index(root)]
last_import = s.index("\n", s.rindex("\nimport ") + 1)
s = s[:last_import + 1] + 'import TRK6 from "./%s";' % ("s6_track_4k.json" if K4 else "s6_track.json") + '\n' + s[last_import + 1:]
s += open(A + "s6_body.jsx", encoding="utf8").read()
s += '''
const Root = () => <>
  <Composition id="S6-4K" component={S6Scene} durationInFrames={9060} fps={60} width={W} height={H} defaultProps={{file: "fusion_s1/s6_take_4k.mp4", review: false, fps: 60}}/>
</>;
registerRoot(Root);
''' if K4 else '''
const Root = () => <>
  <Composition id="S6" component={S6Scene} durationInFrames={4530} fps={30} width={W} height={H} defaultProps={{file: "fusion_s1/s6_take.mp4", review: false}}/>
</>;
registerRoot(Root);
'''
open(A + ("s6_4k.jsx" if K4 else "s6.jsx"), "w", encoding="utf8").write(s)
print("S6_JSX_OK")
