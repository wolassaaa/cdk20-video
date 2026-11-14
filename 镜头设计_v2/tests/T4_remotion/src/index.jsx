import {registerRoot, Composition, Still} from "remotion";
import {StyleA, StyleB, StyleC} from "./style/StyleFrames";
import {ConceptHeist, ConceptArcade, ConceptInfomercial} from "./style/ConceptFrames";
import {KeyholeOverlay} from "./KeyholeOverlay";
import {HandHolo} from "./HandHolo";
import {MV, MV_FRAMES} from "./mv/MV";
import {SacrificeMolecules, SAC_FRAMES} from "./mv/SacrificeMolecules";
import {MV2, MV2_FRAMES} from "./mv2/MV2";
import {V3Title, V3LockKey, V3Funnel, V3Ladder, V3Demo, V3_DEMO_FRAMES} from "./v3";
import {V3Reel, REEL_FRAMES} from "./v3reel/Reel";
import {V3OnCam, ONCAM_FRAMES} from "./v3reel/OnCam";
import {V3OnCamCards, ONCAM_CARDS_FRAMES} from "./v3/oncam/Demo";
import {V3S1Open, S1_OPEN_FRAMES} from "./v3/s1/Open";
import {V3S1Heat, S1_HEAT_FRAMES} from "./v3/s1/Heat";
import {V3OnCam2Test, ONCAM2_FRAMES} from "./v3/oncam2/OnCam2Test";
import {V3OnCam2S12, S12_FRAMES, S12_SINGLE} from "./v3/oncam2/S12";
import {V3OnCam2S34, S34_FRAMES, S34_SINGLE} from "./v3/oncam2/S34";
import {V3OnCam2S58, S58_FRAMES, S58_SINGLE} from "./v3/oncam2/S58";
import {BEAT_COMPS} from "./v3/oncam2/Beats";
import {BEAT2_COMPS} from "./v3/oncam2/V2";

// T4: 2D labels, citation and subtitle composited over the T3 Blender render.
// T1: holograms driven by hand tracking on the test footage (398 frames cut from the phone clip).
const Root = () => (
  <>
    <Composition id="T4" component={KeyholeOverlay} durationInFrames={240} fps={30} width={1920} height={1080} />
    <Composition id="T1" component={HandHolo} durationInFrames={398} fps={30} width={720} height={1280} />
    <Composition id="MV" component={MV} durationInFrames={MV_FRAMES} fps={30} width={1920} height={1080} />
    <Composition id="SacMol" component={SacrificeMolecules} durationInFrames={SAC_FRAMES} fps={30} width={1920} height={1080} />
    <Composition id="MV2" component={MV2} durationInFrames={MV2_FRAMES} fps={30} width={1920} height={1080} />
    <Still id="StyleA" component={StyleA} width={1920} height={1080} />
    <Still id="StyleB" component={StyleB} width={1920} height={1080} />
    <Still id="StyleC" component={StyleC} width={1920} height={1080} />
    <Still id="Heist" component={ConceptHeist} width={1920} height={1080} />
    <Still id="Arcade" component={ConceptArcade} width={1920} height={1080} />
    <Still id="Infomercial" component={ConceptInfomercial} width={1920} height={1080} />
    <Still id="V3-Title" component={V3Title} width={1920} height={1080} />
    <Still id="V3-LockKey" component={V3LockKey} width={1920} height={1080} />
    <Still id="V3-Funnel" component={V3Funnel} width={1920} height={1080} />
    <Still id="V3-Ladder" component={V3Ladder} width={1920} height={1080} />
    <Composition id="V3-Demo" component={V3Demo} durationInFrames={V3_DEMO_FRAMES} fps={30} width={1920} height={1080} />
    <Composition id="V3-Reel" component={V3Reel} durationInFrames={REEL_FRAMES} fps={30} width={1920} height={1080} />
    <Composition id="V3-OnCam" component={V3OnCam} durationInFrames={ONCAM_FRAMES} fps={30} width={1920} height={1080} />
    <Composition id="V3-OnCamCards" component={V3OnCamCards} durationInFrames={ONCAM_CARDS_FRAMES} fps={30} width={1920} height={1080} />
    <Composition id="V3-S1-Heat" component={V3S1Heat} durationInFrames={S1_HEAT_FRAMES} fps={30} width={1920} height={1080} />
    <Composition id="V3-S1-Open" component={V3S1Open} durationInFrames={S1_OPEN_FRAMES} fps={30} width={1920} height={1080} />
    <Composition id="V3-OnCam2-Test" component={V3OnCam2Test} durationInFrames={ONCAM2_FRAMES} fps={30} width={1920} height={1080} />
    <Composition id="V3-OnCam2-S12" component={V3OnCam2S12} durationInFrames={S12_FRAMES} fps={30} width={1920} height={1080} />
    {S12_SINGLE.map(c => <Composition key={c.id} id={c.id} component={c.component} durationInFrames={c.frames} fps={30} width={1920} height={1080} />)}
    <Composition id="V3-OnCam2-S34" component={V3OnCam2S34} durationInFrames={S34_FRAMES} fps={30} width={1920} height={1080} />
    {S34_SINGLE.map(c => <Composition key={c.id} id={c.id} component={c.component} durationInFrames={c.frames} fps={30} width={1920} height={1080} />)}
    <Composition id="V3-OnCam2-S58" component={V3OnCam2S58} durationInFrames={S58_FRAMES} fps={30} width={1920} height={1080} />
    {S58_SINGLE.map(c => <Composition key={c.id} id={c.id} component={c.component} durationInFrames={c.frames} fps={30} width={1920} height={1080} />)}
    {BEAT_COMPS.map(c => <Composition key={c.id} id={c.id} component={c.component} durationInFrames={c.frames} fps={30} width={1920} height={1080} />)}
    {BEAT2_COMPS.map(c => <Composition key={c.id} id={c.id} component={c.component} durationInFrames={c.frames} fps={30} width={1920} height={1080} />)}
  </>
);

registerRoot(Root);
