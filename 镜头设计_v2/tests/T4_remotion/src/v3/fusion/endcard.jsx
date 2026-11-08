// HKBU SCIE1007 coursework science video. End card for W5 (17:10-17:43, 33 s, no speech): references, data and image credits, music, tools and the generative-AI note.
// Words follow 镜头设计_v3/script/片尾卡_W5_v1.md; change them there first. The pages sit on one strip of bone-white paper that glides up and holds, so there is time to read and no cut between pages.
// Render: npx remotion bundle src/v3/fusion/endcard.jsx --out-dir=<dir> --public-dir=<镜头设计_v3/remotion_public>, then render or still composition W5End (--scale=2 for 4K).
import React from "react";
import {registerRoot, Composition, AbsoluteFill, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";

const FPS = 60, W = 1920, H = 1080;
const INK = "#111113", SOFT = "#545458", RED = "#E8190F", BONE = "#EDEBE4";
const SERIF = "Instrument Serif", SANS = "Inter Tight";

const faces = [new FontFace(SERIF, `url(${staticFile("fusion_s1/fonts/InstrumentSerif-Regular.ttf")})`), new FontFace(SERIF, `url(${staticFile("fusion_s1/fonts/InstrumentSerif-Italic.ttf")})`, {style: "italic"}), new FontFace(SANS, `url(${staticFile("fusion_s1/fonts/InterTight.ttf")})`, {weight: "100 900"})];
const fontHandle = delayRender("fonts");
Promise.all(faces.map(f => f.load())).then(l => { l.forEach(f => document.fonts.add(f)); continueRender(fontHandle); });

const clamp = x => Math.min(1, Math.max(0, x));
const smooth = x => { x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10); };

/** *italic* and **bold** inside one entry. */
const Rich = ({s}) => s.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/).map((p, i) =>
  p.startsWith("**") ? <b key={i} style={{fontWeight: 400, fontFamily: SANS, fontSize: "0.82em", letterSpacing: "0.01em"}}>{p.slice(2, -2)}</b>
  : p.startsWith("*") ? <i key={i}>{p.slice(1, -1)}</i> : <React.Fragment key={i}>{p}</React.Fragment>);

const PAGES = [
  {dur: 5.0, head: "References", sub: "1 / 3", size: 27, num: 1, items: [
    "Ren, F.; Ding, X.; Zheng, M.; Korzinkin, M.; Cai, X.; Zhu, W.; Mantsyzov, A.; Aliper, A.; Aladinskiy, V.; Cao, Z.; et al. AlphaFold Accelerates Artificial Intelligence Powered Drug Discovery: Efficient Discovery of a Novel CDK20 Small Molecule Inhibitor. *Chem. Sci.* **2023**, *14* (6), 1443–1452. DOI: 10.1039/D2SC05709C. Including its Electronic Supplementary Information.",
    "Feng, H.; Cheng, A. S. L.; Tsang, D. P.; Li, M. S.; Go, M. Y.; Cheung, Y. S.; Zhao, G.-J.; Ng, S. S.; Lin, M. C.; Yu, J.; et al. Cell Cycle–Related Kinase Is a Direct Androgen Receptor–Regulated Gene That Drives β-Catenin/T Cell Factor–Dependent Hepatocarcinogenesis. *J. Clin. Invest.* **2011**, *121* (8), 3159–3175. DOI: 10.1172/JCI45967.",
    "Wang, L.; Song, Y.; Wang, H.; Zhang, X.; Wang, M.; He, J.; Li, S.; Zhang, L.; Li, K.; Cao, L. Advances of Artificial Intelligence in Anti-Cancer Drug Design: A Review of the Past Decade. *Pharmaceuticals* **2023**, *16* (2), 253. DOI: 10.3390/ph16020253.",
    "Jumper, J.; Evans, R.; Pritzel, A.; Green, T.; Figurnov, M.; Ronneberger, O.; Tunyasuvunakool, K.; Bates, R.; Žídek, A.; Potapenko, A.; et al. Highly Accurate Protein Structure Prediction with AlphaFold. *Nature* **2021**, *596* (7873), 583–589. DOI: 10.1038/s41586-021-03819-2.",
  ]},
  {dur: 5.0, head: "References", sub: "2 / 3", size: 26, num: 5, items: [
    "Varadi, M.; Bertoni, D.; Magana, P.; Paramval, U.; Pidruchna, I.; Radhakrishnan, M.; Tsenkov, M.; Nair, S.; Mirdita, M.; Yeo, J.; et al. AlphaFold Protein Structure Database in 2024: Providing Structure Coverage for over 214 Million Protein Sequences. *Nucleic Acids Res.* **2024**, *52* (D1), D368–D375. DOI: 10.1093/nar/gkad1011.",
    "Ivanenkov, Y. A.; Polykovskiy, D.; Bezrukov, D.; Zagribelnyy, B.; Aladinskiy, V.; Kamya, P.; Aliper, A.; Ren, F.; Zhavoronkov, A. Chemistry42: An AI-Driven Platform for Molecular Design and Optimization. *J. Chem. Inf. Model.* **2023**, *63* (3), 695–701. DOI: 10.1021/acs.jcim.2c01191.",
    "Bender, A.; Thomas, M. C.; Scannell, J. W.; Shaywitz, D. A.; Ghiandoni, G. M.; Greener, J. G.; et al. Artificial Intelligence in Drug Discovery — What It Is, Where We Stand and the Path Forward. *Nat. Rev. Drug Discov.* **2026**. DOI: 10.1038/s41573-026-01496-2. Published online 7 Aug 2026; abstract only consulted.",
    "Lengauer, T. Bioinformatics — From Genomes to Therapies. In *Bioinformatics — From Genomes to Therapies*; Lengauer, T., Ed.; Wiley-VCH: Weinheim, 2007; Vol. 1, pp 1–24. DOI: 10.1002/9783527619368.ch1.",
    "Mitsuhashi, N.; Fujieda, K.; Tamura, T.; Kawamoto, S.; Takagi, T.; Okubo, K. BodyParts3D: 3D Structure Database for Anatomical Concepts. *Nucleic Acids Res.* **2009**, *37* (Database issue), D782–D785. DOI: 10.1093/nar/gkn613.",
  ]},
  {dur: 4.5, head: "References", sub: "3 / 3", size: 27, num: 10, items: [
    "Hong Kong Cancer Registry, Hospital Authority. Liver Cancer in 2022. October 2024. www3.ha.org.hk/Cancereg/pdf/factsheet/2022/liver_2022.asp",
    "Hong Kong Cancer Registry, Hospital Authority. Overview of Hong Kong Cancer Statistics of 2023.",
    "National Cancer Institute. Liver and Bile Duct Cancer. www.cancer.gov/types/liver (accessed 2026-10-03).",
    "U.S. Food and Drug Administration. FDA Approves Lirafugratinib for Previously Treated Unresectable Locally Advanced or Metastatic Cholangiocarcinoma. September 23, 2026. www.fda.gov",
    "Exscientia. Exscientia Details Pipeline Prioritisation Strategy. *Business Wire*, October 3, 2023. www.businesswire.com/news/home/20231003722128/en",
    "First Application of AlphaFold in Identifying Potential Liver Cancer Drug. *Genetic Engineering & Biotechnology News*, January 24, 2023. www.genengnews.com",
  ], foot: "Course material: SCIE1007 Group Project Introduction, slides 45–49. Hong Kong Baptist University, 2026."},
  {dur: 4.5, head: "Data and images", size: 32, items: [
    "CDK20 predicted structure AF-Q8IZL9-F1, model v6, AlphaFold Protein Structure Database (EMBL-EBI and Google DeepMind), CC BY 4.0. The paper used model v1.",
    "Liver, vessels and body outline: BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International.",
    "Molecule structures redrawn from Ren et al. 2023, Figs. 2, 5 and 7.",
    "3D poses of 001 and 048: our own AutoDock Vina re-docking, shown as an illustration.",
    "All other drawings, 3D scenes and animation: made by our team. Scenes marked *Illustration* are drawn, not measured.",
  ]},
  {dur: 4.0, head: "Music", size: 38, lead: "Short excerpts, used for this coursework only. All rights belong to their owners.", items: [
    "NewJeans — *Supernatural*",
    "Daft Punk — *Harder, Better, Faster, Stronger*",
    "Holly Herndon — *Godmother* (feat. Jlin and Spawn)",
    "The Weeknd — *Dancing in the Flames*",
    "The Weeknd — *Wake Me Up* (feat. Justice)",
  ]},
  {dur: 4.0, head: "Made with", size: 38, items: [
    "Blender, Remotion, TouchDesigner, FFmpeg.",
    "Fonts: Instrument Serif, Inter Tight and Caveat, under the SIL Open Font License 1.1.",
    "Footage: filmed by each of us on our own phones.",
  ]},
  {dur: 6.0, head: "Use of generative AI", size: 40, prose: true, items: [
    "We used Claude (Anthropic), through Claude Code, to help organise our reading notes, draft and edit the script, translate it for team discussion, plan the visuals and write the code that renders the animation. [TEAM: add any other AI tool you used, or delete this bracket.]",
    "We checked the facts and numbers against the sources listed. No AI image or video generator was used.",
    "All narration is spoken by our team members; *no AI voice-over was used.*",
  ]},
];
const STARTS = PAGES.reduce((a, p) => [...a, a[a.length - 1] + p.dur], [0]);
export const W5_FRAMES = Math.round(STARTS[STARTS.length - 1] * FPS);
const GLIDE = 0.8;

/** Where the strip is: page i holds, and in its last GLIDE seconds glides up to page i+1. The first page rises in from below. */
const stripPos = t => {
  if (t < GLIDE) return -1 + smooth(t / GLIDE);
  let i = 0;
  while (i < PAGES.length - 1 && t >= STARTS[i + 1]) i++;
  const end = STARTS[i + 1];
  return i < PAGES.length - 1 ? i + smooth((t - (end - GLIDE)) / GLIDE) : i;
};

const Page = ({p}) => {
  const lh = p.prose ? 1.32 : 1.28;
  return <div style={{width: W, height: H, boxSizing: "border-box", padding: "0 210px", display: "flex", flexDirection: "column", justifyContent: "center"}}>
    <div style={{display: "flex", alignItems: "baseline", gap: 28, marginBottom: 44}}>
      <div style={{fontFamily: SERIF, fontStyle: "italic", fontSize: 76, color: INK, lineHeight: 1, borderBottom: `5px solid ${RED}`, paddingBottom: 8}}>{p.head}</div>
      {p.sub && <div style={{fontFamily: SANS, fontSize: 24, fontWeight: 500, color: SOFT, letterSpacing: "0.08em"}}>{p.sub}</div>}
    </div>
    {p.lead && <div style={{fontFamily: SANS, fontSize: 25, color: SOFT, marginBottom: 30}}>{p.lead}</div>}
    {p.items.map((s, k) => <div key={k} style={{display: "flex", gap: 22, marginBottom: p.prose ? 30 : p.size * 0.62, fontFamily: SERIF, fontSize: p.size, lineHeight: lh, color: INK}}>
      {p.num && <div style={{fontFamily: SANS, fontSize: p.size * 0.72, fontWeight: 500, color: SOFT, minWidth: 34, textAlign: "right", paddingTop: p.size * 0.18}}>{p.num + k}</div>}
      {!p.num && !p.prose && <div style={{minWidth: 18, paddingTop: p.size * 0.5}}><div style={{width: 9, height: 9, background: RED, borderRadius: 9}}/></div>}
      <div><Rich s={s}/></div>
    </div>)}
    {p.foot && <div style={{fontFamily: SANS, fontSize: 22, color: SOFT, marginTop: 14, paddingLeft: 56}}>{p.foot}</div>}
  </div>;
};

const W5End = () => {
  const t = useCurrentFrame() / FPS, y = stripPos(t);
  return <AbsoluteFill style={{background: BONE, overflow: "hidden"}}>
    <div style={{position: "absolute", left: 0, top: 0, transform: `translateY(${-y * H}px)`}}>
      {PAGES.map((p, i) => <Page key={i} p={p}/>)}
    </div>
    <div style={{position: "absolute", left: 210, bottom: 46, fontFamily: SANS, fontSize: 20, fontWeight: 500, color: SOFT, letterSpacing: "0.06em"}}>WORTH TESTING? · HKBU SCIE1007 · 2026</div>
  </AbsoluteFill>;
};

const Root = () => <Composition id="W5End" component={W5End} durationInFrames={W5_FRAMES} fps={FPS} width={W} height={H}/>;
registerRoot(Root);
