"""HKBU SCIE1007 课程作业的科普视频：P0 第 3 轮和 h20 检查图。"""
import json
import math
import sys
import time
from pathlib import Path

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
import kit_deep as D
import kit_deep_r2 as R
import kit_deep_r3 as M
import kit_h20 as H

OUT=Path("G:/cdk20/work/kit_deep")
QUEUE=(HERE.parents[1]/"_env"/"queue",Path.home()/"cdk20_guard")
args=sys.argv[sys.argv.index("--")+1:]
target=args[0]
testing="verify" in args
only={x[5:] for x in args if x.startswith("only:")}
dest=OUT
if testing:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene
else:
    sc=D.scene_base(40)
    sc.cycles.adaptive_threshold=.026
    sc.cycles.max_bounces=8
    D.backdrop()
    D.lights()
K=D.Kit()
data={"target":target,"renders":{}}


def visible(root):
    return [o for o in root.children_recursive if o.type in ("MESH","FONT","CURVE")
            and not o.hide_render and not o.hide_viewport]


def geom(ob,dg):
    eo=ob.evaluated_get(dg)
    m=eo.to_mesh()
    p=[eo.matrix_world@v.co for v in m.vertices]
    m.calc_loop_triangles()
    f=[tuple(t.vertices) for t in m.loop_triangles]
    eo.to_mesh_clear()
    return p,f


def vol(obs,want_tree=False):
    bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get()
    vertices,faces=[],[]
    for ob in obs:
        v,f=geom(ob,dg)
        n=len(vertices)
        vertices.extend(v)
        faces.extend(tuple(i+n for i in t) for t in f)
    if not vertices:
        raise RuntimeError("no evaluated mesh")
    box=[tuple(fn(v[i]/D.MM for v in vertices) for i in range(3)) for fn in (min,max)]
    tree=BVHTree.FromPolygons(vertices,faces,all_triangles=True) if want_tree else None
    return box,len(faces),tree


def render(label,look,axis,width,*,hd=False,f8=False):
    look,axis=Vector(look),Vector(axis).normalized()
    camera=sc.camera
    if camera is None:
        camera=D.camera(sc,D._mm(look),.6,0,0,lens=36)
    distance=width*1.85
    camera.location=D._mm(look+axis*distance)
    camera.rotation_euler=(-axis).to_track_quat("-Z","Y").to_euler()
    camera.data.type="PERSP" if f8 else "ORTHO"
    camera.data.ortho_scale=width*D.MM
    camera.data.clip_start=.1*D.MM
    camera.data.dof.use_dof=f8
    if f8:
        camera.data.sensor_width=1.5
        camera.data.lens=1.5*distance/width
        camera.data.dof.focus_distance=distance*D.MM
        camera.data.dof.aperture_fstop=8
    if hd:
        sc.render.resolution_x,sc.render.resolution_y=1920,1080
    elif target=="h01" and label in {"closed","half_open","open"}:
        sc.render.resolution_x,sc.render.resolution_y=1600,1200
    else:
        sc.render.resolution_x,sc.render.resolution_y=1600,900
    sc.render.resolution_percentage=100
    sc.render.image_settings.file_format="PNG"
    bpy.context.view_layer.update()
    data["renders"][label]={"width":sc.render.resolution_x,"height":sc.render.resolution_y,
                            "fstop":8 if f8 else None}
    if testing or (only and label not in only):
        return camera
    while any((base/mark).exists() for base in QUEUE for mark in ("GPU_HOLD","GPU_PAUSED")):
        print("WAIT_GPU",flush=True)
        time.sleep(12)
    suffix="_r3" if target in {"h01","h06"} else ""
    filename=dest/f"{target}_{label}{suffix}.png"
    print("FRAME",filename.name,flush=True)
    D.render(sc,str(filename),100)
    return camera


def model(root,default_target,view,width):
    if testing or only:
        return
    suffix="_r3" if target!="h20" else ""
    render_camera=sc.camera or D.camera(sc,D._mm(default_target),.75,0,0)
    look=Vector(default_target)
    render_camera.location=D._mm(look+Vector(view).normalized()*width*1.85)
    render_camera.rotation_euler=(D._mm(look)-render_camera.location).to_track_quat("-Z","Y").to_euler()
    render_camera.data.type="ORTHO"
    render_camera.data.ortho_scale=width*D.MM
    render_camera.data.dof.use_dof=False
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(dest/f"{target}{suffix}.blend"))


def chamber_light():
    lamp=bpy.data.lights.new("chamber_softbox_30deg","AREA")
    ob=D.link(bpy.data.objects.new(lamp.name,lamp))
    center=Vector((95,-4,-105))
    ob.location=D._mm(center+Vector((0,-.866,.5))*240)
    ob.rotation_euler=(D._mm(center)-ob.location).to_track_quat("-Z","Y").to_euler()
    lamp.shape="RECTANGLE"
    lamp.size=.43
    lamp.size_y=.19
    lamp.energy=4.5
    lamp.specular_factor=.16
    return ob


def h01():
    root=M.h01_cdk20_lockworks(K)
    front=next(o for o in M.rig(root)["shell"].children if "shell_front" in o.name and not o.hide_render)
    back=next(o for o in root.children if "shell_back" in o.name and not o.hide_render)
    data["closed_bounds_mm"]=vol([front,back])[0]
    area=lambda points:abs(sum(x*v-u*z for (x,z),(u,v) in zip(points,points[1:]+points[:1])))/2
    data["chamber_outline_area_mm2"]=area(M.CHAMBER)
    data["seam_area_mm2"]=root["seam_area_mm2"]
    data["chamber_cut_area_mm2"]=root["chamber_cut_area_mm2"]
    data["chamber_ratio"]=data["chamber_cut_area_mm2"]/max(1,data["seam_area_mm2"])
    data["chamber_depth_mm"]=M.DEPTH
    data["layer_span_mm"]=28-(-17.3)
    data["roles"]=list(M.rig(root))
    shell_tree=vol([back],True)[2]
    coverage=[]
    for step in range(11):
        M.pose(root,"shell",step*11)
        coverage.append(len(vol([front],True)[2].overlap(shell_tree)))
    data["shell_sweep_crossing_pairs"]=coverage
    print("H01_MEASURED",data,flush=True)
    lamp=chamber_light()
    bpy.data.objects.get("sweep") and setattr(bpy.data.objects["sweep"].location,"z",-.388)
    focus=(105,-4,-91)
    direction=(-.10,-1,.07)
    width=615
    M.pose(root,"shell",0)
    lamp.hide_render=True
    model(root,focus,direction,width)
    render("closed",focus,direction,width)
    lamp.hide_render=False
    M.pose(root,"shell",55)
    render("half_open",focus,direction,width)
    M.pose(root,"shell",110)
    cam=render("open",focus,direction,width)
    points=[world_to_camera_view(sc,cam,D._mm((x,-4.1,z))) for x,z in M.CHAMBER]
    data["chamber_outline_frame_area_ratio"]=area([(p.x,p.y) for p in points])
    data["outline_all_in_frame"]=all(0<=p.x<=1 and 0<=p.y<=1 for p in points)
    # 通过正面射线把壳体、遮挡的门和内部真实几何区分，不只用轮廓面积。
    chamber=[o for o in visible(root) if o not in (front,back)
             and not any(t in o.name for t in ("hinge_leaf","hinge_knuckle","red_mouth_rim"))]
    chamber_bvh=vol(chamber,True)[2]
    cover_bvh=vol([front,back],True)[2]
    frame=cam.data.view_frame(scene=sc)
    xmin,xmax=min(p.x for p in frame),max(p.x for p in frame)
    ymin,ymax=min(p.y for p in frame),max(p.y for p in frame)
    n=0
    for row in range(100):
        for col in range(132):
            orig=cam.matrix_world@Vector((xmin+(xmax-xmin)*(col+.5)/132,
                                          ymin+(ymax-ymin)*(row+.5)/100,0))
            ray=cam.matrix_world.to_3x3()@Vector((0,0,-1))
            hit=chamber_bvh.ray_cast(orig,ray)[3]
            cover=cover_bvh.ray_cast(orig,ray)[3]
            n+=int(hit is not None and (cover is None or hit<cover))
    data["visible_chamber_frame_fraction"]=n/13200
    render("open_threequarter",(113,0,-90),(-.37,-1,.32),730,hd=True)
    M.key_visible(root,True)
    # 保持同一机位、同一检视法显示毫米级输入端的五组销。
    back.hide_render=True
    for label,val in (("key_000",0),("key_050",2.5),("key_100",5)):
        M.pose(root,"key",val)
        render(label,(2,0,2),(.13,-1,.18),26,f8=True)
    back.hide_render=False
    M.pose(root,"plug",90)
    M.pose(root,"latch",-25)
    render("turn_latch",(61,-4,-102),(.14,-1,.13),264)
    M.key_visible(root,False)
    M.pose(root,"latch",0)
    M.pose(root,"arm",-32)
    M.pose(root,"crank",158)
    render("stamp",(11,-4,-124),(-.16,-1,.23),153)
    M.pose(root,"arm",0)
    M.pose(root,"strip",3.3)
    render("strip_step",(-15,-2,-126),(-.12,-1,.29),113)
    back.hide_render=True
    render("detail_pins",(-3.9,0,4),(.22,-1,.18),17.5,f8=True)
    back.hide_render=False
    render("detail_drive",(115,-5,-102),(.22,-1,.25),122,f8=True)
    M.pose(root,"arm",-32)
    render("detail_belt",(-12,-4,-124),(-.23,-1,.19),104,f8=True)


def h06():
    root=M.h06_pin_lock(K)
    objects=visible(root)
    sleeve=next(o for o in objects if "sleeve_9p" in o.name)
    case=next(o for o in objects if "inset_housing" in o.name)
    rotor=visible(D.rig(root)["plug"])
    fixed=[o for o in objects if o not in rotor and o not in visible(D.rig(root)["shackle"])]
    tree=vol(fixed,True)[2]
    sb,st,_=vol([sleeve])
    bc,_,_=vol([case])
    data.update(sleeve_mm=sb, sleeve_triangles=st, case_mm=bc,
                sleeve_protrusion_mm=bc[0][1]-sb[0][1])
    fail=[]
    for n in range(181):
        D.pose(root,"plug",n*.5)
        if vol(rotor,True)[2].overlap(tree):
            fail.append(n*.5)
    data["rotor_crossings_deg"]=fail
    print("H06_MEASURED",data,flush=True)
    D.pose(root,"plug",0)
    z=bc[0][2]-.02
    bpy.data.objects.get("sweep") and setattr(bpy.data.objects["sweep"].location,"z",z*D.MM)
    model(root,(0,0,3),(.85,-1,.57),32)
    render("aligned",(0,0,3),(.85,-1,.57),33)
    D.pose(root,"plug",90)
    D.pose(root,"shackle",4)
    render("turned",(0,0,5),(.85,-1,.57),35)
    D.pose(root,"plug",0)
    D.pose(root,"shackle",0)
    render("cut_threequarter",(1,-2.7,3.25),(1,-.59,.36),19,f8=True)

def h20():
    # 先评估整块板的网格包围盒（包括站牌、边框和所有支脚）。
    board_info=D.make_board(K)
    board=board_info["board"]
    bounds,faces,_=vol(visible(board))
    hb=bounds[1][2]
    data.update(board_bounds_mm=bounds,board_triangles=faces,
                board_highest_mm=hb,under_roof_margin_mm=61.5-hb)
    print("BOARD_MEASURED",data,flush=True)
    (OUT/"h20_board_height.json").write_text(json.dumps(data,indent=2),encoding="utf-8")
    if hb>57.5:
        raise RuntimeError(f"h20: board height {hb:.3f} mm exceeds 57.5 mm")
    try:
        H.h20_kit_box(K,names={"A":"A","B":"B","C":"C"})
    except ValueError as exc:
        data["missing_name_check"]=str(exc)
    else:
        raise RuntimeError("h20 did not reject absent D")
    lid=H.h20_kit_box(K,draft=True)
    lid.location.x=((board_info["xl"]+board_info["xr"])/2)*D.MM
    H.rest(lid)
    j=H.rig(lid)
    shell=next(o for o in visible(lid) if "_shell" in o.name)
    b,_,_=vol([shell])
    data.update(shell_bounds_mm=b,shell_size_mm=[b[1][i]-b[0][i] for i in range(3)],
                roles=list(j),triangles=vol(visible(lid))[1],
                subtitle_cap_mm=lid["subtitle_cap_mm"])
    if "subtitle_width_scale" in lid:
        data["subtitle_width_scale"]=lid["subtitle_width_scale"]
    box_b=Vector(bounds[0])-lid.location/D.MM
    box_t=Vector(bounds[1])-lid.location/D.MM
    min_wall=min(490.4-max(-box_b.x,box_t.x),163.4-max(-box_b.y,box_t.y))
    # 顶针槽不是凸起；侧壁和顶板的形面分离可由包围盒给下界。
    data["seat_clearance_lower_bound_mm"]=min(61.5-hb,min_wall)
    data["lift_board_lower_bounds_mm"]=[min(61.5-hb+8*n,min_wall) for n in range(11)]
    tilted=[]
    for step in range(11):
        H.pose(lid,"lid_lift",80)
        H.pose(lid,"lid_hinge",104*step/10)
        lo=vol([shell])[0][0][2]
        tilted.append({"angle":104*step/10,"shell_bottom_mm":lo,
                       "board_gap_lower_bound_mm":lo-hb})
    data["hinge_sweep"]=tilted
    H.rest(lid)
    slides={}
    for role in ["sec_plate"]+[f"tag_{i}" for i in range(8)]:
        # 顶面距离按评估后网格取；装配浇口与横杆本来设计为同一连接点，单独测。
        samples=[]
        for step in range(11):
            degrees=-90+9*step
            H.pose(lid,role,degrees)
            bounds1,_,_=vol(visible(j[role]))
            obs=[o for o in visible(j[role]) if "_trimmed_sprue_hinge" not in o.name]
            b1,_,_=vol(obs)
            samples.append([degrees,bounds1[0][2]-64,b1[0][2]-64,b1[1][1]])
        slides[role]=samples
        H.pose(lid,role,0)
    data["card_samples_angle_allZ_faceZ_maxY"]=slides
    print("H20_CHECK",dict((k,v) for k,v in data.items() if k!="card_samples_angle_allZ_faceZ_maxY"),flush=True)
    top=(0,-.173648,.984808)
    top_width=986/.90
    front=(.22,-1,1.6)
    half_width=1190
    floor=bpy.data.objects.get("sweep")
    if floor:
        floor.location.z=-.00004
    model(lid,(-4,0,47),top,top_width)
    H.pose(lid,"lid_lift",43)
    H.pose(lid,"badge",12)
    H.pose(lid,"sec_plate",-90)
    H.pose(lid,"qmark",10)
    H.pose(lid,"rule",.04)
    for i in range(8):
        H.pose(lid,f"tag_{i}",-90)
    render("lid_descending",(-4,0,64),front,half_width,hd=True)
    H.pose(lid,"lid_lift",0)
    render("plates_upright",(-4,0,72),top,top_width,hd=True)
    H.pose(lid,"sec_plate",-32)
    H.pose(lid,"badge",0)
    H.pose(lid,"qmark",0)
    H.pose(lid,"rule",.55)
    for i,angle in enumerate((0,0,-15,-37,-62,-82,-90,-90)):
        H.pose(lid,f"tag_{i}",angle)
    render("cards_midway",(-4,0,65),(.12,-1,2.0),half_width,hd=True)
    H.rest(lid)
    camera=render("all_seated",(-4,0,65),top,top_width,hd=True)
    data["nominal_title_cap_pixels"]=48*math.sin(math.radians(80))*1920/top_width
    data["nominal_subtitle_cap_pixels"]=lid["subtitle_cap_mm"]*math.sin(math.radians(80))*1920/top_width
    data["nominal_upright_tag_width_pixels"]=64*math.cos(math.radians(80))*1920/top_width
    for pos,label in ((-289,"plates_1_to_3"),(281,"plates_6_to_8")):
        render(label,(pos,-96,65),(0,-.258819,.965926),342,hd=True)
    H.pose(lid,"lid_lift",80)
    H.pose(lid,"lid_hinge",50)
    render("lid_open_50",(-4,-14,161),(.17,-1,1.20),1210,hd=True)
    H.pose(lid,"lid_hinge",100)
    render("lid_open_100",(-4,35,186),(.16,-1,1.35),1250,hd=True)


if target in {"h01","h06","h20"}:
    globals()[target]()
    (OUT/f"{target}_report_r3.json").write_text(json.dumps(data,indent=2),encoding="utf-8")
    print("R3_DONE",target,flush=True)
