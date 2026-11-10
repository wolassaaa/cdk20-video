// HKBU SCIE1007 coursework science video. End card for W5, version 2: the same words as endcard.jsx (not one letter changed), but each of the six page changes is its own move, tied to the drawn liver cells of the background layer.
// 1 to 2 "carried": the lines leave with a cell that drifts right under the page, moving exactly as far as it moves.  2 to 3 "parting": three pressed cells let go; the page opens along the gap between them.
// 3 to 4 "ripple": the outline of one cell spreads out as a ring; the next page is inside it.  4 to 5 "closing": two cells meet; the page shuts along the line where they touch and opens again as the next page.
// 5 to 6 "pushed": a cell rises from below and the page goes up and out with it.  6 to 7 "turned": a cell is set turning; the page turns about that cell and the next one turns in. Every move is 0.8 s; a page that has arrived does not move.
// The cells come from 镜头设计_v3/styleframes/art/fusion/end/bl_w5cells2.py and are multiplied under this layer by comp_w5cells2.py. Where the cells are is read from w5cells2_moves.json, written by w5cells2_sim.py.
// Render: npx remotion bundle src/v3/fusion/endcard_v2.jsx, then render W5Cells2 (30 fps, 33 s) as a png sequence; W5End2 is the same at 60 fps.
import React from "react";
import {registerRoot, Composition, AbsoluteFill, staticFile, useCurrentFrame, useVideoConfig, continueRender, delayRender} from "remotion";
import MV from "./w5cells2_moves.json";

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
const LINE_INK = "#B4B2B3";                       // the pen line of the cells after the layer is paled

const ease = x => { x = clamp(x); return x * x * (3 - 2 * x); };
/** Where a cell is at film time t (s): centre in px and turn in rad, read from the motion file. */
const cellAt = (name, t) => {
  const i = MV.names.indexOf(name), x = Math.min(MV.pos.length - 1, Math.max(0, t * MV.fps)), f = Math.floor(x), g = Math.min(MV.pos.length - 1, f + 1), a = x - f;
  return {x: MV.pos[f][i][0] * (1 - a) + MV.pos[g][i][0] * a, y: MV.pos[f][i][1] * (1 - a) + MV.pos[g][i][1] * a, psi: MV.psi[f][i] * (1 - a) + MV.psi[g][i] * a};
};
const poly = (pts, rule) => `polygon(${rule ? rule + ", " : ""}${pts.map(([x, y]) => `${x.toFixed(1)}px ${y.toFixed(1)}px`).join(", ")})`;
const line = (pts, close) => "M " + pts.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join(" L ") + (close ? " Z" : "");
const Pen = ({d, o}) => <path d={d} fill="none" stroke={LINE_INK} strokeWidth={2.6} strokeLinecap="round" strokeLinejoin="round" opacity={o}/>;
const Ink = ({children}) => <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0}}>{children}</svg>;

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

/** Page 1 to 2. u runs 0 to 1 over GLIDE seconds. Each block lets go a little later than the one below it (the bottom ones are nearest the cell) and from then on moves exactly as the cell moves, fading. */
const Carried = ({a, b, u, t0}) => {
  const at = v => cellAt("C", t0 + v * GLIDE);
  const order = (k, n) => (n - 1 - k) / Math.max(1, n - 1);              // 0 for the bottom block, 1 for the heading
  const end = at(1), bef = at(0.8), sp = Math.hypot(end.x - bef.x, end.y - bef.y) || 1, dir = [(end.x - bef.x) / sp, (end.y - bef.y) / sp];
  const out = (k, n) => {
    const uk = order(k, n) * 0.22, c0 = at(Math.min(u, uk)), c1 = at(u);
    return {transform: `translate(${(c1.x - c0.x).toFixed(2)}px, ${(c1.y - c0.y).toFixed(2)}px)`, opacity: 1 - ease((u - uk - 0.08) / 0.42)};
  };
  const into = (k, n) => {
    const q = ease((u - 0.42 - order(k, n) * 0.2) / 0.38), back = 64 * (1 - q) * (1 - q);
    return {transform: `translate(${(-dir[0] * back).toFixed(2)}px, ${(-dir[1] * back).toFixed(2)}px)`, opacity: q};
  };
  return <>
    <Page p={a} lineStyle={out}/>
    <Page p={b} lineStyle={into}/>
  </>;
};

/** Page 2 to 3. The seam is the real gap between cell E and cells F and G when they let go. The old page fades first, then the two pieces go apart whole (nothing is cut after the first split) and the next page shows in the opening. */
const Parting = ({a, b, u}) => {
  const q = Math.pow(ease(u), 1.5);
  const dl = -1920 * q, dr = 460 * q;
  const L = MV.seam.map(([x, y]) => [x + dl, y]), R = MV.seam.map(([x, y]) => [x + dr, y]);
  const fade = 1 - ease(u / 0.42), rise = ease((u - 0.2) / 0.4), lineA = ease(u / 0.1) * (1 - ease((u - 0.85) / 0.15));
  return <>
    <AbsoluteFill style={{clipPath: poly([...L, ...R.slice().reverse()]), opacity: rise}}><Page p={b}/></AbsoluteFill>
    <AbsoluteFill style={{clipPath: poly([...L, [-2100, 1160], [-2100, -80]]), opacity: fade}}><div style={{position: "absolute", inset: 0, transform: `translateX(${dl.toFixed(2)}px)`}}><Page p={a}/></div></AbsoluteFill>
    <AbsoluteFill style={{clipPath: poly([...R, [2600, 1160], [2600, -80]]), opacity: fade}}><div style={{position: "absolute", inset: 0, transform: `translateX(${dr.toFixed(2)}px)`}}><Page p={a}/></div></AbsoluteFill>
    <Ink><Pen d={line(L)} o={lineA}/><Pen d={line(R)} o={lineA}/></Ink>
  </>;
};

/** Page 3 to 4. The outline of cell B (as it is at the start of the move) spreads out from the cell as two rings; the old page is outside the first, the next page inside the second, clean paper between. */
const Ripple = ({a, b, u, t}) => {
  const c = cellAt("B", t), d1 = 1460 * (0.35 * u + 0.65 * u * u), d2 = d1 - 90;
  const ring = d => MV.ripple.th.map((th, i) => { const r = Math.max(0, MV.ripple.r[i] + d); return [c.x + r * Math.cos(th), c.y + r * Math.sin(th)]; });
  const r1 = ring(d1), r2 = ring(d2), box = [[-10, -10], [W + 10, -10], [W + 10, H + 10], [-10, H + 10], [-10, -10]];
  const lineA = ease(u / 0.08) * (1 - ease((u - 0.55) / 0.4));
  return <>
    <AbsoluteFill style={{clipPath: poly([...box, ...r1, r1[0], box[0]], "evenodd")}}><Page p={a}/></AbsoluteFill>
    <AbsoluteFill style={{clipPath: poly(r2)}}><Page p={b}/></AbsoluteFill>
    <Ink><Pen d={line(r1, true)} o={lineA}/>{d2 > 0 && <Pen d={line(r2, true)} o={lineA * 0.7}/>}</Ink>
  </>;
};

/** Page 4 to 5. Cells F and G come together; the line where they touch is the line the page shuts on. The old page is only seen between two bowed edges that close onto that line, then they open again on the next page. */
const Closing = ({a, b, u}) => {
  const {p, d} = MV.close, n = [-d[1], d[0]], A = 760;
  const gap = u < 0.5 ? A * (1 - ease(u / 0.46)) : A * ease((u - 0.54) / 0.46);
  // each edge is bowed like the rim of a very large cell: nearest the line where F and G touch, further off to the sides; the bow flattens to that line as the edges meet
  const edge = s => Array.from({length: 49}, (_, i) => { const x = (i - 24) * 100, off = gap * s * (1 + 0.5 * (x / 900) * (x / 900)); return [p[0] + d[0] * x + n[0] * off, p[1] + d[1] * x + n[1] * off]; });
  const up = edge(-1), dn = edge(1), lineA = ease(u / 0.1) * (1 - ease((u - 0.86) / 0.14));
  return <>
    <AbsoluteFill style={{clipPath: poly([...up, ...dn.slice().reverse()])}}><Page p={u < 0.5 ? a : b}/></AbsoluteFill>
    <Ink><Pen d={line(up)} o={lineA}/><Pen d={line(dn)} o={lineA}/></Ink>
  </>;
};

/** Page 5 to 6. Cell U rises from the bottom edge; the page goes up and out ahead of it and the next page comes up behind. */
const Pushed = ({a, b, u}) => {
  const y = smooth(u);
  return <>
    <div style={{position: "absolute", inset: 0, transform: `translateY(${(-y * H).toFixed(2)}px)`}}><Page p={a}/></div>
    <div style={{position: "absolute", inset: 0, transform: `translateY(${((1 - y) * H).toFixed(2)}px)`}}><Page p={b}/></div>
  </>;
};

/** Page 6 to 7. Cell W brushes cell U and sets it turning. The page turns about the centre of U, the same way and at a fixed share of the turn of U, and fades; the next page turns in to level. */
const Turned = ({a, b, u, t0}) => {
  const c = cellAt("U", t0), SHARE = 0.42;
  const turn = v => cellAt("U", t0 + v * GLIDE).psi - c.psi;
  const origin = `${c.x.toFixed(1)}px ${c.y.toFixed(1)}px`;
  return <>
    <div style={{position: "absolute", inset: 0, transformOrigin: origin, transform: `rotate(${(SHARE * turn(u)).toFixed(5)}rad)`, opacity: 1 - ease(u / 0.6)}}><Page p={a}/></div>
    <div style={{position: "absolute", inset: 0, transformOrigin: origin, transform: `rotate(${(-SHARE * (turn(1) - turn(u))).toFixed(5)}rad)`, opacity: ease((u - 0.3) / 0.62)}}><Page p={b}/></div>
  </>;
};
const MOVES = [Carried, Parting, Ripple, Closing, Pushed, Turned];

const W5End2 = () => {
  const {fps} = useVideoConfig();
  const t = useCurrentFrame() / fps;
  let i = 0;
  while (i < PAGES.length - 1 && t >= STARTS[i + 1]) i++;
  const u = i < PAGES.length - 1 ? (t - (STARTS[i + 1] - GLIDE)) / GLIDE : -1;
  const Move = MOVES[i];
  return <AbsoluteFill style={{background: BONE, overflow: "hidden"}}>
    {t < GLIDE ? <div style={{position: "absolute", inset: 0, transform: `translateY(${(1 - smooth(t / GLIDE)) * H}px)`}}><Page p={PAGES[0]}/></div>
      : u > 0 ? <Move a={PAGES[i]} b={PAGES[i + 1]} u={u} t={t} t0={STARTS[i + 1] - GLIDE}/>
      : <Page p={PAGES[i]}/>}
    <div style={{position: "absolute", left: 210, bottom: 46, fontFamily: SANS, fontSize: 20, fontWeight: 500, color: SOFT, letterSpacing: "0.06em"}}>WORTH TESTING? · HKBU SCIE1007 · 2026</div>
  </AbsoluteFill>;
};

const Root = () => <>
  <Composition id="W5Cells2" component={W5End2} durationInFrames={Math.round(TOTAL * 30)} fps={30} width={W} height={H}/>
  <Composition id="W5End2" component={W5End2} durationInFrames={Math.round(TOTAL * FPS)} fps={FPS} width={W} height={H}/>
</>;
registerRoot(Root);
