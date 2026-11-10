// HKBU SCIE1007 coursework science video. End card for W5, test version 2: the same words as endcard.jsx (not one letter changed), but each page change is its own move, tied to the drawn liver cells of the background layer.
// Page 1 to 2 "carried": a cell is drifting to the right under the page; the lines leave to the right one after another, starting next to that cell, and the next page's lines arrive from the left.
// Page 2 to 3 "parting": three pressed cells let go of each other; the page opens along the seam between them and the next page shows in the gap. Later page changes still use the old upward glide (not designed yet).
// The cells themselves come from 镜头设计_v3/styleframes/art/fusion/end/bl_w5cells.py and are multiplied under this layer by comp_w5cells.py. Numbers marked "from the sim" are read off w5cells_sim.py.
// Render: npx remotion bundle src/v3/fusion/endcard_v2.jsx, then render W5CellsTest (30 fps, first three pages) as a png sequence.
import React from "react";
import {registerRoot, Composition, AbsoluteFill, staticFile, useCurrentFrame, useVideoConfig, continueRender, delayRender} from "remotion";

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
const TOTAL = STARTS[STARTS.length - 1];
const GLIDE = 0.8;
const TEST_SECONDS = 14;
const LINE_INK = "#B4B2B3";                       // the cells' pen line after the layer is paled

// from the sim: cell C drifts right and a little up under page 1 between 4.2 and 5.0 s
const CARRY = {dx: 0.99, dy: -0.15, out: 84, into: 56};
// from the sim: at 9.2 s cell E lets go of F and G; the gap between them runs through these points (top to bottom)
const SEAM = [[1296, -60], [1262, 150], [1228, 330], [1262, 470], [1302, 600], [1262, 760], [1236, 900], [1270, 1140]];

const ease = x => { x = clamp(x); return x * x * (3 - 2 * x); };

/** Points along a smooth curve through the seam, shifted sideways by dx; top to bottom. */
const seamPts = dx => {
  const pts = [[SEAM[0][0] + dx, SEAM[0][1]]];
  for (let i = 0; i < SEAM.length - 1; i++) for (let s = 1; s <= 12; s++) {
    const p0 = SEAM[Math.max(0, i - 1)], p1 = SEAM[i], p2 = SEAM[i + 1], p3 = SEAM[Math.min(SEAM.length - 1, i + 2)], t = s / 12, m = 1 - t;
    const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6], c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
    pts.push([m * m * m * p1[0] + 3 * m * m * t * c1[0] + 3 * m * t * t * c2[0] + t * t * t * p2[0] + dx, m * m * m * p1[1] + 3 * m * m * t * c1[1] + 3 * m * t * t * c2[1] + t * t * t * p2[1]]);
  }
  return pts;
};
const poly = pts => `polygon(${pts.map(([x, y]) => `${x.toFixed(1)}px ${y.toFixed(1)}px`).join(", ")})`;
const line = pts => "M " + pts.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join(" L ");

/** One page. lineStyle(k, n) may move or fade each block: k = 0 is the heading, then the lead, the entries and the foot. */
const Page = ({p, lineStyle}) => {
  const lh = p.prose ? 1.32 : 1.28;
  const n = 1 + (p.lead ? 1 : 0) + p.items.length + (p.foot ? 1 : 0);
  let k = 0;
  const ls = () => (lineStyle ? lineStyle(k++, n) : {});
  return <div style={{position: "absolute", left: 0, top: 0, width: W, height: H, boxSizing: "border-box", padding: "0 210px", display: "flex", flexDirection: "column", justifyContent: "center"}}>
    <div style={{display: "flex", alignItems: "baseline", gap: 28, marginBottom: 44, ...ls()}}>
      <div style={{fontFamily: SERIF, fontStyle: "italic", fontSize: 76, color: INK, lineHeight: 1, borderBottom: `5px solid ${RED}`, paddingBottom: 8}}>{p.head}</div>
      {p.sub && <div style={{fontFamily: SANS, fontSize: 24, fontWeight: 500, color: SOFT, letterSpacing: "0.08em"}}>{p.sub}</div>}
    </div>
    {p.lead && <div style={{fontFamily: SANS, fontSize: 25, color: SOFT, marginBottom: 30, ...ls()}}>{p.lead}</div>}
    {p.items.map((s, i) => <div key={i} style={{display: "flex", gap: 22, marginBottom: p.prose ? 30 : p.size * 0.62, fontFamily: SERIF, fontSize: p.size, lineHeight: lh, color: INK, ...ls()}}>
      {p.num && <div style={{fontFamily: SANS, fontSize: p.size * 0.72, fontWeight: 500, color: SOFT, minWidth: 34, textAlign: "right", paddingTop: p.size * 0.18}}>{p.num + i}</div>}
      {!p.num && !p.prose && <div style={{minWidth: 18, paddingTop: p.size * 0.5}}><div style={{width: 9, height: 9, background: RED, borderRadius: 9}}/></div>}
      <div><Rich s={s}/></div>
    </div>)}
    {p.foot && <div style={{fontFamily: SANS, fontSize: 22, color: SOFT, marginTop: 14, paddingLeft: 56, ...ls()}}>{p.foot}</div>}
  </div>;
};

/** Page 1 to 2. u runs 0 to 1 over GLIDE seconds. The blocks nearest the cell (the bottom ones) go first. */
const Carried = ({a, b, u}) => {
  const order = (k, n) => (n - 1 - k) / Math.max(1, n - 1);              // 0 for the bottom block, 1 for the heading
  const out = (k, n) => {
    const q = ease((u - order(k, n) * 0.18) / 0.32);
    return {transform: `translate(${CARRY.dx * CARRY.out * q * q}px, ${CARRY.dy * CARRY.out * q * q}px)`, opacity: 1 - q};
  };
  const into = (k, n) => {
    const q = ease((u - 0.46 - order(k, n) * 0.18) / 0.36);
    return {transform: `translate(${-CARRY.dx * CARRY.into * (1 - q) * (1 - q)}px, ${-CARRY.dy * CARRY.into * (1 - q) * (1 - q)}px)`, opacity: q};
  };
  return <>
    <Page p={a} lineStyle={out}/>
    <Page p={b} lineStyle={into}/>
  </>;
};

/** Page 2 to 3. The page splits along the seam; the two halves go the way the cells go and fade first, then the next page comes up, standing still, in the gap. */
const Parting = ({a, b, u}) => {
  const q = ease(u);
  const dl = -1420 * q - 4 * u, dr = 780 * q + 4 * u;                    // the seam sits right of the middle, so the left edge has further to go
  const L = seamPts(dl), R = seamPts(dr);
  const fade = 1 - ease((u - 0.04) / 0.46), rise = ease((u - 0.34) / 0.5), lineA = ease(u / 0.12) * (1 - ease((u - 0.8) / 0.2));
  return <>
    <AbsoluteFill style={{clipPath: poly([...L, ...R.slice().reverse()]), opacity: rise}}><Page p={b}/></AbsoluteFill>
    <AbsoluteFill style={{clipPath: poly([...L, [-80, 1140], [-80, -60]]), opacity: fade}}><div style={{position: "absolute", inset: 0, transform: `translateX(${dl * 0.10}px)`}}><Page p={a}/></div></AbsoluteFill>
    <AbsoluteFill style={{clipPath: poly([...R, [2000, 1140], [2000, -60]]), opacity: fade}}><div style={{position: "absolute", inset: 0, transform: `translateX(${dr * 0.10}px)`}}><Page p={a}/></div></AbsoluteFill>
    <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0, opacity: lineA}}>
      <path d={line(L)} fill="none" stroke={LINE_INK} strokeWidth={2.6} strokeLinecap="round"/>
      <path d={line(R)} fill="none" stroke={LINE_INK} strokeWidth={2.6} strokeLinecap="round"/>
    </svg>
  </>;
};

/** Old glide, kept for the page changes that have no move of their own yet. */
const Glide = ({a, b, u}) => {
  const y = smooth(u);
  return <>
    <div style={{position: "absolute", inset: 0, transform: `translateY(${-y * H}px)`}}><Page p={a}/></div>
    <div style={{position: "absolute", inset: 0, transform: `translateY(${(1 - y) * H}px)`}}><Page p={b}/></div>
  </>;
};
const MOVES = [Carried, Parting];

const W5End2 = () => {
  const {fps} = useVideoConfig();
  const t = useCurrentFrame() / fps;
  let i = 0;
  while (i < PAGES.length - 1 && t >= STARTS[i + 1]) i++;
  const u = i < PAGES.length - 1 ? (t - (STARTS[i + 1] - GLIDE)) / GLIDE : -1;
  const Move = MOVES[i] || Glide;
  return <AbsoluteFill style={{background: BONE, overflow: "hidden"}}>
    {t < GLIDE ? <div style={{position: "absolute", inset: 0, transform: `translateY(${(1 - smooth(t / GLIDE)) * H}px)`}}><Page p={PAGES[0]}/></div>
      : u > 0 ? <Move a={PAGES[i]} b={PAGES[i + 1]} u={u}/>
      : <Page p={PAGES[i]}/>}
    <div style={{position: "absolute", left: 210, bottom: 46, fontFamily: SANS, fontSize: 20, fontWeight: 500, color: SOFT, letterSpacing: "0.06em"}}>WORTH TESTING? · HKBU SCIE1007 · 2026</div>
  </AbsoluteFill>;
};

const Root = () => <>
  <Composition id="W5CellsTest" component={W5End2} durationInFrames={TEST_SECONDS * 30} fps={30} width={W} height={H}/>
  <Composition id="W5End2" component={W5End2} durationInFrames={Math.round(TOTAL * FPS)} fps={FPS} width={W} height={H}/>
</>;
registerRoot(Root);
