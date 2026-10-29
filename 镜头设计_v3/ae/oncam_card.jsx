// M3 出镜卡模板（AE 2026，ExtendScript）
// 用法：AE 开着时运行  AfterFX.exe -r oncam_card.jsx
// 生成 oncam_template.aep：
//   PIC_A..D   每人的画面（860×920 竖幅裁切，换素材只换这一层）
//   CARD_A..D  照片纸：暖白纸边 + 毛边每 2 帧抖一次 + 暖色调色
//   ONCAM_DEMO 1-01（A 长到左半屏）+ 1-05/1-06/1-07（D → B → C 一问一答）
// 卡片动画全部由卡片图层上的 4 个滑块控制，导演可以直接在 AE 里拖关键帧：
//   Corner 1 左上 A · 2 右上 B · 3 左下 C · 4 右下 D
//   Show   0–100 出现 / 消失（带回弹）
//   Grow   0 = 角落小卡，100 = 半屏
//   Full   0–100 再从半屏推到全屏（关键句）

var ROOT = File($.fileName).parent;           // 镜头设计_v3/ae
var REPO = ROOT.parent.parent;                // 仓库根目录
var OUT = new Folder(ROOT.fsName + "/_out");
if (!OUT.exists) OUT.create();
var LOG = [];
function log(s) { LOG.push(s); }

var FPS = 24, W = 1920, H = 1080;
var PIC_W = 860, PIC_H = 920, EDGE = 24;      // 照片 + 纸边
var CARD_W = PIC_W + EDGE * 2, CARD_H = PIC_H + EDGE * 2;
var F = 1 / FPS;

function rgb(hex) { return [parseInt(hex.substr(1, 2), 16) / 255, parseInt(hex.substr(3, 2), 16) / 255, parseInt(hex.substr(5, 2), 16) / 255]; }
var COL = {bg: "#060606", paper: "#EFE7D6", lift: "#1C130C", ink: "#EDEBE4"};

// ---------- 素材 ----------
var PLACEHOLDER = new File(REPO.fsName + "/镜头设计_v2/tests/T1_hand/hand_raw.mp4"); // 镜头设计_v2 里的手机实拍，只是占位

function findItem(name) {
  for (var i = 1; i <= app.project.numItems; i++) if (app.project.item(i).name === name) return app.project.item(i);
  return null;
}
function folder(name) { return findItem(name) || app.project.items.addFolder(name); }

function fx(layer, match, name) { var e = layer.property("ADBE Effect Parade").addProperty(match); if (name) e.name = name; return e; }
function slider(layer, name, v) { var e = fx(layer, "ADBE Slider Control", name); e.property(1).setValue(v); return e.property(1); }

// ---------- PIC：裁成竖幅，铺满 ----------
function makePic(who, footage) {
  var c = app.project.items.addComp("PIC_" + who, PIC_W, PIC_H, 1, 30, FPS);
  c.parentFolder = folder("_pics");
  var L = c.layers.add(footage);
  L.name = "FOOTAGE (replace me)";
  // 铺满：按高或宽取大的那一边（换素材后重跑 fitPic 或手动调 Scale）
  var fs = Math.max(PIC_W / footage.width, PIC_H / footage.height) * 100;
  L.transform.scale.setValue([fs, fs]);
  // 暖色：暖片滤镜 + 黑位抬成暖褐（像冲印照片，不是死黑）
  var pf = fx(L, "ADBE Photo Filter");
  try { pf.property("ADBE Photo Filter-0001").setValue(1); } catch (e) { log("photo filter preset: " + e); }
  try { pf.property("ADBE Photo Filter-0003").setValue(45); } catch (e) { log("photo filter density: " + e); }
  var vib = fx(L, "ADBE Vibrance");
  try { vib.property("ADBE Vibrance-0001").setValue(12); vib.property("ADBE Vibrance-0002").setValue(-8); } catch (e) { log("vibrance: " + e); }
  var lift = c.layers.addSolid(rgb(COL.lift), "black lift", PIC_W, PIC_H, 1);
  lift.blendingMode = BlendingMode.LIGHTEN;
  // 暗角
  var vig = c.layers.addSolid([0, 0, 0], "vignette", PIC_W, PIC_H, 1);
  var m = vig.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
  var sh = new Shape(); var k = 0.5523;
  var cx = PIC_W / 2, cy = PIC_H / 2, rx = PIC_W * 0.62, ry = PIC_H * 0.6;
  sh.vertices = [[cx, cy - ry], [cx + rx, cy], [cx, cy + ry], [cx - rx, cy]];
  sh.inTangents = [[-rx * k, 0], [0, -ry * k], [rx * k, 0], [0, ry * k]];
  sh.outTangents = [[rx * k, 0], [0, ry * k], [-rx * k, 0], [0, -ry * k]];
  sh.closed = true;
  m.property("ADBE Mask Shape").setValue(sh);
  m.inverted = true;
  m.property("ADBE Mask Feather").setValue([260, 260]);
  vig.opacity.setValue(38);
  lift.moveToBeginning(); vig.moveToBeginning();
  return c;
}

// ---------- CARD：纸 + 照片 ----------
function makeCard(who, pic) {
  var c = app.project.items.addComp("CARD_" + who, CARD_W, CARD_H, 1, 30, FPS);
  c.parentFolder = folder("_cards");
  var paper = c.layers.addSolid(rgb(COL.paper), "paper", CARD_W, CARD_H, 1);
  var re = fx(paper, "ADBE Roughen Edges");
  try {
    re.property("ADBE Roughen Edges-0002").setValue(4);
    re.property("ADBE Roughen Edges-0003").setValue(2);
    re.property("ADBE Roughen Edges-0005").setValue(30);
    // 毛边每 2 帧换一次（一拍二），和墨线的抖动同频
    re.property("ADBE Roughen Edges-0009").expression = "Math.floor(time*" + (FPS / 2) + ")*97";
  } catch (e) { log("roughen: " + e); }
  var nz = fx(paper, "ADBE Noise");
  try { nz.property("ADBE Noise-0001").setValue(5); nz.property("ADBE Noise-0002").setValue(0); } catch (e) { log("paper noise: " + e); }
  var P = c.layers.add(pic);
  P.name = "photo";
  P.moveToBeginning();
  return c;
}

// ---------- 卡片图层：4 个滑块 + 表达式 ----------
var EXP_HEAD =
  "function io(x){x=Math.max(0,Math.min(1,x));return x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2;}\n" +
  "var c=Math.round(effect('Corner')(1).value);\n" +
  "var g=io(effect('Grow')(1).value/100), fu=io(effect('Full')(1).value/100);\n" +
  "var left=(c==1||c==3), top=(c==1||c==2);\n";

var EXP_POS = EXP_HEAD +
  "var chip=[left?182:1738, top?186:894], half=[left?490:1430,540], full=[960,540];\n" +
  "var p=[chip[0]+(half[0]-chip[0])*g, chip[1]+(half[1]-chip[1])*g];\n" +
  "[p[0]+(full[0]-p[0])*fu, p[1]+(full[1]-p[1])*fu];";

var EXP_SCALE = EXP_HEAD +
  "var x=Math.max(0,Math.min(1,effect('Show')(1).value/100));\n" +
  "var b=x<=0?0:1+2.7*Math.pow(x-1,3)+1.7*Math.pow(x-1,2);\n" +   // 出现时回弹一下
  "var s=24+(96-24)*g; s=s+(108-s)*fu; s*=b; [s,s];";

var EXP_ROT = EXP_HEAD +
  "var base=left?-1.1:0.9;\n" +
  "var t=Math.floor(time*" + (FPS / 2) + ")/" + (FPS / 2) + ";\n" +       // 手放上去的轻微晃动，也是一拍二
  "base*(1-0.5*fu)+0.15*noise(t*2.3+c*10);";

var EXP_OPA = "Math.min(100, effect('Show')(1).value*5);";

var CORNER = {A: 1, B: 2, C: 3, D: 4};

function key(prop, t, v) { prop.setValueAtTime(t, v); }

// 一张卡在 [tIn, tOut] 里出场：角落弹出 → 长到半屏 → 停住 → 缩回角落 → 消失
function placeCard(comp, card, who, tIn, tOut, opt) {
  opt = opt || {};
  var L = comp.layers.add(card);
  L.name = who + " card";
  L.inPoint = tIn; L.outPoint = tOut;
  // 加效果会让之前拿到的属性引用失效，所以先全部加完再重新取
  slider(L, "Corner", CORNER[who]); slider(L, "Show", 0); slider(L, "Grow", 0); slider(L, "Full", 0);
  var fxp = L.property("ADBE Effect Parade");
  var show = fxp.property("Show").property(1), grow = fxp.property("Grow").property(1), full = fxp.property("Full").property(1);
  key(show, tIn, 0); key(show, tIn + 6 * F, 100);
  key(grow, tIn + 3 * F, 0); key(grow, tIn + 13 * F, 100);
  if (opt.full) { key(full, opt.full[0], 0); key(full, opt.full[0] + 10 * F, 100); key(full, opt.full[1] - 10 * F, 100); key(full, opt.full[1], 0); }
  key(grow, tOut - 12 * F, 100); key(grow, tOut - 3 * F, 0);
  key(show, tOut - 5 * F, 100); key(show, tOut, 0);
  L.transform.position.expression = EXP_POS;
  L.transform.scale.expression = EXP_SCALE;
  L.transform.rotation.expression = EXP_ROT;
  L.transform.opacity.expression = EXP_OPA;
  // 黑底上只要一圈很淡的暖光，让纸"浮"起来
  var gl = fx(L, "ADBE Drop Shadow");
  try {
    gl.property("ADBE Drop Shadow-0001").setValue(rgb("#3A2412"));
    gl.property("ADBE Drop Shadow-0002").setValue(160);
    gl.property("ADBE Drop Shadow-0004").setValue(0);
    gl.property("ADBE Drop Shadow-0005").setValue(60);
  } catch (e) { log("shadow: " + e); }
  return L;
}

function stage(comp) {
  var bg = comp.layers.addSolid(rgb(COL.bg), "stage", W, H, 1);
  var gr = comp.layers.addSolid([0, 0, 0], "grain (12 fps)", W, H, 1);
  var n = fx(gr, "ADBE Noise");
  try { n.property("ADBE Noise-0001").setValue(100); n.property("ADBE Noise-0002").setValue(0); } catch (e) { log("grain: " + e); }
  var pt = fx(gr, "ADBE Posterize Time");
  try { pt.property(1).setValue(FPS / 2); } catch (e) { log("posterize: " + e); }
  gr.blendingMode = BlendingMode.ADD;
  gr.opacity.setValue(7);
  bg.moveToEnd();
  return gr;
}

function label(comp, txt, pos, size, op) {
  var t = comp.layers.addText(txt);
  var d = t.property("ADBE Text Properties").property("ADBE Text Document").value;
  d.fontSize = size; d.fillColor = rgb(COL.ink); d.applyFill = true; d.justification = ParagraphJustification.CENTER_JUSTIFY;
  try { d.font = "Consolas"; } catch (e) {}
  t.property("ADBE Text Properties").property("ADBE Text Document").setValue(d);
  t.transform.position.setValue(pos);
  t.opacity.setValue(op || 35);
  return t;
}

// ---------- 主流程 ----------
app.beginUndoGroup("oncam card template");
try {
  // 每次重建都从空工程开始；不保存旧的，避免弹"是否保存"对话框把脚本卡住
  app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
  app.newProject();
  var ft = app.project.importFile(new ImportOptions(PLACEHOLDER));
  ft.name = "PLACEHOLDER hand_raw (replace per member)";
  ft.parentFolder = folder("_footage");

  var cards = {};
  var who = ["A", "B", "C", "D"];
  for (var i = 0; i < 4; i++) cards[who[i]] = makeCard(who[i], makePic(who[i], ft));

  var demo = app.project.items.addComp("ONCAM_DEMO", W, H, 1, 9, FPS);
  var grain = stage(demo);
  // A 1-01：长到左半屏，右半边是图解区
  label(demo, "DIAGRAM HALF\n(Remotion render goes here)", [1430, 540], 30, 30).inPoint = 0;
  demo.layer(1).outPoint = 3.6;
  placeCard(demo, cards.A, "A", 0.25, 3.6);
  // 1-05 D → 1-06 B → 1-07 C：右下 → 右上 → 左下，眼神方向一问一答
  placeCard(demo, cards.D, "D", 3.5, 5.3);
  placeCard(demo, cards.B, "B", 5.1, 6.9);
  placeCard(demo, cards.C, "C", 6.7, 9.0, {full: [7.6, 8.7]});
  var l2 = label(demo, "DIAGRAM HALF", [490, 540], 30, 30); l2.inPoint = 3.6; l2.outPoint = 6.9;
  var l3 = label(demo, "DIAGRAM HALF", [1430, 540], 30, 30); l3.inPoint = 6.9; l3.outPoint = 7.6;
  grain.moveToBeginning();

  app.project.save(new File(ROOT.fsName + "/oncam_template.aep"));
  log("saved " + ROOT.fsName + "/oncam_template.aep");

  // 预览静帧
  var shots = [0.12, 0.6, 1.8, 3.35, 4.4, 6.0, 8.2];
  for (var s = 0; s < shots.length; s++) {
    var f = new File(OUT.fsName + "/demo_" + ("0" + Math.round(shots[s] * 100)).slice(-4) + ".png");
    demo.saveFrameToPng(shots[s], f);
  }
  log("frames requested: " + shots.length);
} catch (err) {
  log("ERROR line " + err.line + ": " + err.toString());
}
app.endUndoGroup();

var lf = new File(OUT.fsName + "/build_log.txt");
lf.encoding = "UTF-8"; lf.open("w"); lf.write(LOG.join("\n") + "\nDONE\n"); lf.close();
