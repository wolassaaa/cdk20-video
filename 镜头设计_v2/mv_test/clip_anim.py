"""Turn a still look-dev scene into a short moving clip (used by the 5-minute music test).

Scripts call render_clip() instead of their still render when CLIP_SECONDS is set:
  CLIP_SECONDS  length of the clip in seconds
  CLIP_OUT      folder for the PNG frames
  CLIP_MOVE     orbit (camera circles the target) | dolly (camera moves toward the target)
  CLIP_AMOUNT   orbit: total swing in degrees; dolly: fraction of the distance to travel
"""
import os, math
import bpy
from mathutils import Vector


def wanted():
    return bool(os.environ.get("CLIP_SECONDS"))


def _ease(obj, path, f0, v0, f1, v1):
    setattr(obj, path, v0)
    obj.keyframe_insert(path, frame=f0)
    setattr(obj, path, v1)
    obj.keyframe_insert(path, frame=f1)


def render_clip(scene, cam, target):
    seconds = float(os.environ["CLIP_SECONDS"])
    out = os.environ["CLIP_OUT"].rstrip("/\\")
    move = os.environ.get("CLIP_MOVE", "orbit")
    amount = float(os.environ.get("CLIP_AMOUNT", "40"))
    fps = 30
    scene.render.fps = fps
    scene.frame_start, scene.frame_end = 1, int(seconds * fps)
    scene.cycles.samples = int(os.environ.get("CLIP_SAMPLES", "128"))
    scene.render.use_persistent_data = True
    target = Vector(target)
    # matrix_world of objects created by the script is only filled in after a depsgraph update;
    # without this the orbit reads the camera at the origin and films nothing
    bpy.context.view_layer.update()

    aim = bpy.data.objects.new("clip_aim", None)
    aim.location = target
    scene.collection.objects.link(aim)
    if move == "orbit":
        # the camera rides on a pivot at the target, so it circles while staying aimed and in focus
        pivot = bpy.data.objects.new("clip_pivot", None)
        pivot.location = target
        scene.collection.objects.link(pivot)
        bpy.context.view_layer.update()  # the new pivot's matrix_world is stale (identity) until this
        cam.parent = pivot
        cam.matrix_parent_inverse = pivot.matrix_world.inverted()  # keep the camera exactly where it was
        swing = math.radians(amount) / 2
        _ease(pivot, "rotation_euler", scene.frame_start, (0, 0, -swing), scene.frame_end, (0, 0, swing))
    else:
        tc = cam.constraints.new("TRACK_TO")
        tc.target, tc.track_axis, tc.up_axis = aim, "TRACK_NEGATIVE_Z", "UP_Y"
        if cam.data.dof.use_dof:
            cam.data.dof.focus_object = aim
        start = cam.location.copy()
        _ease(cam, "location", scene.frame_start, start, scene.frame_end, start.lerp(target, amount))
    scene.render.filepath = f"{out}/f"
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(animation=True)
    print("CLIP DONE", out, scene.frame_end, "frames")
