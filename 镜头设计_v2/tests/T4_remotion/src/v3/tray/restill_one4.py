"""HKBU SCIE1007 课程作业的科普视频。只给一组托盘段换接头图（start/end.png）并重出 Remotion。用法：restill_one4.py <组名>"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
g = sys.argv[1]
sys.argv = [sys.argv[0], "--stage", "none"]
import prep4  # noqa: E402
import run_tray4 as RT  # noqa: E402

C = json.load(open(HERE / "_resolved" / f"{g}.json", encoding="utf-8"))
pub = RT.OUT / "_work" / f"pub_{g}"
if C.get("pull"):
    prep4.neighbour_still(C["prev"], False, pub / "start.png")
if C.get("push"):
    prep4.neighbour_still(C["next"], True, pub / "end.png")
RT.remotion(g)
print("RESTILL_ONE_DONE", g)
