// 把 oncam_template.aep 里的 ONCAM_DEMO 渲染出来（AE 默认的无损输出模块），之后用 ffmpeg 转成小 mp4
var ROOT = File($.fileName).parent;
var OUT = new Folder(ROOT.fsName + "/_out"); if (!OUT.exists) OUT.create();
var msg = [];
try {
  var comp = null;
  for (var i = 1; i <= app.project.numItems; i++) if (app.project.item(i).name === "ONCAM_DEMO") comp = app.project.item(i);
  if (!comp) throw new Error("ONCAM_DEMO not in open project");
  var rq = app.project.renderQueue;
  while (rq.numItems > 0) rq.item(1).remove();
  var it = rq.items.add(comp);
  var om = it.outputModule(1);
  om.file = new File(OUT.fsName + "/ONCAM_DEMO_master");
  rq.render();
  msg.push("rendered " + om.file.fsName);
} catch (e) { msg.push("ERROR " + e.line + ": " + e); }
var f = new File(OUT.fsName + "/render_log.txt"); f.encoding = "UTF-8"; f.open("w"); f.write(msg.join("\n") + "\nDONE\n"); f.close();
