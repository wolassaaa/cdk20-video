// HKBU SCIE1007 coursework science video. W5 end credits, v10: the whole credits column (19 doc, 5.3 layout, 5.4 text) set once as one tall transparent sheet.
// The roll itself is done by comp_w5roll.py: it moves this sheet up by exactly v whole pixels a frame over the W5 parts layer (19 doc, 5.2), so every frame
// shows the very same glyph pixels, only shifted (no sub-pixel shimmer, check W3). Changing N (12 or 10 bars) only reruns the composite, not this render.
// Text comes from credits_v10.json (built from 19 doc 5.4 by 镜头设计_v3/styleframes/art/fusion/end/credits_v10_data.py).
// Member names arrive only as input props at local render time ({names: {A, B, C, D}}); nothing here or in the json holds them.
// After layout the page prints one line "W5META|{...}" (block positions in sheet pixels, fonts and sizes used); comp_w5roll.py reads it to work out H, R, stop frame.
// Render (comp_w5roll.py sheet does this): remotion still src/v3/fusion/credits_v10.jsx W5RollSheet OUT.png --image-format=png --log=verbose --props=...
import React, {useEffect} from "react";
import {registerRoot, Still, AbsoluteFill, staticFile, delayRender, continueRender, getInputProps} from "remotion";
import DATA from "./credits_v10.json";

export const SHEET_W = 1020, SHEET_H = 6000;       // text area x 160–1180 (19 doc 5.3); height is cropped afterwards by the composite
const INK = "#1F1E1C", RED = "#C8102E", SMALL = "#6E6B63";
const FAM = "InstrumentSerifW5";
const SERIF = `'${FAM}'`;                           // no generic fallback on purpose: a missing font shows up as a check failure, not as Times
const GREEK = "'Times New Roman', serif";           // Instrument Serif has no β (U+03B2); only that one glyph uses this
const BODY = 26, LH = 34, GAP = 14, SMALLPX = 22, HEAD = 40;
const COLW = 480, COLGAP = 60, ONEW = 900;

const fontHandle = delayRender("Instrument Serif");
Promise.all([["InstrumentSerif-Regular.ttf", "normal"], ["InstrumentSerif-Italic.ttf", "italic"]]
  .map(([f, st]) => new FontFace(FAM, `url(${staticFile("fonts/" + f)})`, {style: st}).load().then((x) => document.fonts.add(x))))
  .then(() => continueRender(fontHandle))
  .catch((e) => { throw new Error("Instrument Serif failed to load: " + e); });

/** β set in the fallback serif. */
const greek = (t, key) => t.split(/(β)/).map((q, j) => q === "β" ? <span key={key + "g" + j} data-greek="1" style={{fontFamily: GREEK, fontSize: "0.92em"}}>β</span> : q);
/** Words with a hyphen or dash (DOIs, dates, page ranges) never break at the hyphen: "03819-" / "2" on two lines reads as a different DOI. */
const nobreak = (t, key) => t.split(/(\S*[-–]\S*)/).map((q, j) => /[-–]/.test(q) && !/\s/.test(q)
  ? <span key={key + "n" + j} style={{whiteSpace: "nowrap"}}>{greek(q, key + j)}</span> : greek(q, key + j));
/** *italic* inside one entry. */
const Rich = ({s}) => s.split(/(\*[^*]+\*)/).map((p, i) => {
  const it = p.startsWith("*") && p.endsWith("*") && p.length > 2;
  const parts = nobreak(it ? p.slice(1, -1) : p, "k" + i);
  return it ? <i key={i}>{parts}</i> : <React.Fragment key={i}>{parts}</React.Fragment>;
});

const Head = ({text, align}) => <div style={{textAlign: align, marginBottom: 24}}>
  <div data-head="1" style={{display: "inline-block", fontStyle: "italic", fontSize: HEAD, lineHeight: "48px", color: INK, borderBottom: `3px solid ${RED}`, paddingBottom: 2}}>{text}</div>
</div>;

const Item = ({it, numbered, align}) => {
  const base = {fontSize: BODY, lineHeight: `${LH}px`, color: INK, marginBottom: GAP, breakInside: "avoid", textAlign: align};
  if (numbered) return <div style={{...base, display: "flex"}}>
    <div style={{flex: "0 0 40px", color: SMALL}}>{it.n}.</div><div style={{flex: 1}}><Rich s={it.text}/></div></div>;
  if (it.bullet && align === "left") return <div style={{...base, display: "flex"}}>
    <div style={{flex: "0 0 26px", color: RED}}>•</div><div style={{flex: 1}}><Rich s={it.text}/></div></div>;
  if (it.note) return <div style={{...base, fontSize: SMALLPX, color: SMALL, marginBottom: GAP + 6}}><Rich s={it.text}/></div>;
  return <div style={base}><Rich s={it.text}/></div>;
};

const Section = ({sec}) => {
  const two = sec.columns === 2;
  const w = two ? SHEET_W : ONEW;
  return <div data-k={sec.head} style={{width: w, marginLeft: (SHEET_W - w) / 2, paddingTop: 60}}>
    <Head text={sec.head} align={sec.align}/>
    <div style={two ? {columnCount: 2, columnGap: COLGAP, columnWidth: COLW, columnFill: "balance"} : {}}>
      {sec.items.map((it, i) => <Item key={i} it={it} numbered={sec.numbered} align={sec.align}/>)}
    </div>
  </div>;
};

const Title = ({names}) => {
  const [t, sub, course, section, by, ...ph] = DATA.title;
  const fill = (s) => s.replace(/\{NAME_([A-D])\}/, (_, m) => names[m] || `Member ${m}`);
  const line = (s, px, lh, extra = {}) => <div style={{fontSize: px, lineHeight: `${lh}px`, color: INK, whiteSpace: "nowrap", ...extra}}>{s}</div>;
  return <div data-k="title" style={{width: ONEW, marginLeft: (SHEET_W - ONEW) / 2, textAlign: "center"}}>
    {line(t, 96, 104)}
    <div style={{height: 18}}/>
    {line(sub, 40, 50)}
    <div style={{height: 30}}/>
    {line(course, 34, 44)}
    {line(section, 34, 44)}
    <div style={{height: 30}}/>
    {line(by, 34, 44)}
    <div style={{height: 12}}/>
    {ph.map((p, i) => <div key={i} data-name="1">{line(fill(p), 44, 56)}</div>)}
  </div>;
};

const AI = () => <div style={{width: ONEW, marginLeft: (SHEET_W - ONEW) / 2, paddingTop: 60}}>
  <div data-k="ai">
    <Head text="Use of generative AI" align="left"/>
    {DATA.ai.map((p, i) => <div key={i} style={{fontSize: BODY, lineHeight: `${LH}px`, color: INK, marginBottom: i < DATA.ai.length - 1 ? GAP : 0}}><Rich s={p}/></div>)}
  </div>
</div>;

const Sheet = () => {
  const names = (getInputProps() || {}).names || {};
  const [h] = React.useState(() => delayRender("measure"));
  useEffect(() => {
    document.fonts.ready.then(() => requestAnimationFrame(() => {
      const root = document.getElementById("w5sheet").getBoundingClientRect();
      const box = (el) => { const r = el.getBoundingClientRect(); return {top: Math.round(r.top - root.top), bottom: Math.round(r.bottom - root.top), left: Math.round(r.left - root.left), right: Math.round(r.right - root.left)}; };
      const blocks = {};
      document.querySelectorAll("[data-k]").forEach((el) => { blocks[el.getAttribute("data-k")] = box(el); });
      // fonts and sizes actually used by every element that holds text directly
      const fams = {}, sizes = {};
      document.querySelectorAll("#w5sheet *").forEach((el) => {
        if (![...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) return;
        const cs = getComputedStyle(el);
        const fam = el.getAttribute("data-greek") ? "greek:" + cs.fontFamily : cs.fontFamily;
        fams[fam] = (fams[fam] || 0) + 1;
        sizes[cs.fontSize] = (sizes[cs.fontSize] || 0) + 1;
      });
      const loaded = document.fonts.check(`26px ${SERIF}`) && document.fonts.check(`italic 40px ${SERIF}`);
      const content = box(document.getElementById("w5content"));
      // the widest real line in the title block (the subtitle must not wrap)
      console.log("W5META|" + JSON.stringify({blocks, content, fams, sizes, loaded, nameCount: document.querySelectorAll("[data-name]").length}));
      continueRender(h);
    }));
  }, []);
  return <AbsoluteFill style={{background: "transparent"}}>
    <div id="w5sheet" style={{position: "absolute", left: 0, top: 0, width: SHEET_W, fontFamily: SERIF, color: INK, fontKerning: "normal", textRendering: "geometricPrecision"}}>
      <div id="w5content">
        <Title names={names}/>
        {DATA.sections.map((s) => <Section key={s.head} sec={s}/>)}
        <AI/>
      </div>
    </div>
  </AbsoluteFill>;
};

const Root = () => <Still id="W5RollSheet" component={Sheet} width={SHEET_W} height={SHEET_H}/>;
registerRoot(Root);
