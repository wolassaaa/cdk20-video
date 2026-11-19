"""HKBU SCIE1007 课程作业的科普视频：P0 第 2 轮，Blender 验收与出图。"""
import json
import math
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import kit_deep as D
import kit_deep_r2 as R

OUT = Path("G:/cdk20/work/kit_deep")
QUEUE = [HERE.parents[1]/"_env"/"queue", Path.home()/"cdk20_guard"]
flags = sys.argv[sys.argv.index("--")+1:]
target = flags[0]
preview = "preview" in flags
verify = "verify" in flags
dest = OUT/"tmp"/"r2" if preview else OUT
selected = {x[5:] for x in flags if x.startswith("only:")}
if not verify:
    while any((base/mark).exists() for base in QUEUE for mark in ("GPU_HOLD","GPU_PAUSED")):
        print("WAIT_GPU",flush=True)
        time.sleep(12)
if verify:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene
else:
    sc=D.scene_base(16 if preview else 64)
    sc.cycles.max_bounces=8
    sc.cycles.adaptive_threshold=.018
    D.backdrop()
    D.lights()
K=D.Kit()
data={"target":target,"renders":{}}


def geom(ob, dg=None):
    dg=dg or bpy.context.evaluated_depsgraph_get()
    e=ob.evaluated_get(dg)
    me=e.to_mesh()
    points=[e.matrix_world@v.co for v in me.vertices]
    me.calc_loop_triangles()
    faces=[tuple(f.vertices) for f in me.loop_triangles]
    e.to_mesh_clear()
    return points,faces


def objects(root, visible=True):
    return [o for o in root.children_recursive if o.type in ("MESH","CURVE","FONT")
            and not o.hide_viewport and (not visible or not o.hide_render)]


def tree(obs):
    gg,ff=[],[]
    dg=bpy.context.evaluated_depsgraph_get()
    for ob in obs:
        vv,polys=geom(ob,dg)
        ff.extend(tuple(i+len(gg) for i in row) for row in polys)
        gg.extend(vv)
    return BVHTree.FromPolygons(gg,ff)


def _light(name, xyz, towards, watts):
    l=bpy.data.lights.new(name,"AREA")
    o=D.link(bpy.data.objects.new(name,l))
    o.location=D._mm(xyz)
    o.rotation_euler=(D._mm(towards)-o.location).to_track_quat("-Z","Y").to_euler()
    l.energy=watts
    l.specular_factor=.07
    l.shape="DISK"
    l.size=.018
    return o


def pic(name, at, look, width, close=False, clip=.3):
    if verify or (selected and name not in selected):
        return
    out=dest/f"{target}_{name}_r2.png"
    if out.exists() and "replace" not in flags:
        return
    while any((base/mark).exists() for base in QUEUE for mark in ("GPU_HOLD","GPU_PAUSED")):
        print("WAIT_GPU",flush=True)
        time.sleep(12)
    sc.render.resolution_x, sc.render.resolution_y=((832,468) if preview else (1600,900))
    sc.render.image_settings.file_format="PNG"
    sc.render.resolution_percentage=100
    addr=lambda n: D._mm(n)+root.location
    a,b=addr(at),addr(look)
    d=(b-a).length
    cam=D.camera(sc,b,d,0,0,lens=35)
    cam.location=a
    cam.rotation_euler=(b-a).to_track_quat("-Z","Y").to_euler()
    cam.data.clip_start=clip*D.MM
    if close:
        # 1 mm 有效感光宽度，保 f/8 且将毫米级特写散焦压低。
        cam.data.sensor_width=1.
        cam.data.lens=max(1.,d/(width*D.MM))
        w=(b-a).normalized()
        t=tree(objects(root))
        hit=t.ray_cast(a+w*(clip*D.MM+.00001),w)[0]
        if hit is None:
            right=(b-a).to_track_quat("-Z","Y")@Vector((1,0,0))
            up=(b-a).to_track_quat("-Z","Y")@Vector((0,1,0))
            offsets=sorted((x*x+y*y,x,y) for x in (-.30,-.22,-.15,-.08,0,.08,.15,.22,.30)
                           for y in (-.14,-.08,0,.08,.14))
            for _,x,y in offsets:
                dr=(w+(x*right+y*up)*(width*D.MM/d)).normalized()
                hit=t.ray_cast(a+dr*(clip*D.MM+.00001),dr)[0]
                if hit is not None:
                    break
            if hit is None:
                raise RuntimeError(f"No centre surface in {name}")
        probe=D.link(bpy.data.objects.new("surface_focus_"+name,None))
        probe.location=hit
        cam.data.dof.use_dof=True
        cam.data.dof.focus_object=probe
        cam.data.dof.focus_distance=(hit-a).dot(w)
        cam.data.dof.aperture_fstop=8
        bpy.context.view_layer.update()
        fr=cam.data.view_frame(scene=sc)
        x0,x1=min(x.x for x in fr),max(x.x for x in fr)
        y0,y1=min(x.y for x in fr),max(x.y for x in fr)
        z=fr[0].z
        depth=[]
        for i in range(64):
            for j in range(36):
                direction=(cam.matrix_world.to_3x3() @ Vector((x0+(i+.5)*(x1-x0)/64,
                                  y0+(j+.5)*(y1-y0)/36,z))).normalized()
                s=t.ray_cast(a+direction*(clip*D.MM+.00001),direction)[0]
                if s is not None:
                    depth.append((s-a).dot(w))
        f=cam.data.lens/1000
        dd=cam.data.dof.focus_distance
        coc=max((f*f*abs(z-dd)/(8*z*(dd-f))*(sc.render.resolution_x/.001)
                 for z in depth),default=0)
        optics=dict(fstop=8, focus_mm=list((hit-root.location)/D.MM),
                    coverage=len(depth)/2304, estimated_coc_px=coc)
    else:
        optics={}
        cam.data.type="ORTHO"
        cam.data.ortho_scale=width*D.MM
    data["renders"][name]=optics
    print("R2_FRAME",out.name,optics,flush=True)
    D.render(sc,str(out),100)


def stand(root, width, depth, height=1.6, y=0):
    bpy.context.view_layer.update()
    z=min(p.z for ob in objects(root) for p in geom(ob)[0])/D.MM
    root.location.z=(height-z)*D.MM
    obj=D.Part(K,"presentation_base","white")
    R._box(obj,"plinth",(0,y,height/2),width/2,depth/2,height,K.white,2,.24)


def save_report():
    (dest/f"{target}_report_r2.json").write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")


def h01():
    global root
    root=R.h01_cdk20_lockworks(K)
    props=("shell_scale","cavity_length_mm","cavity_wall_grid_min_mm","mouth_center_mm",
           "mouth_axis","sleeve_end_x_mm","roll_center_distance_mm","belt_loop_mm","stamp_count")
    for k in props:
        v=root[k]
        data[k]=list(v) if hasattr(v,"to_list") else v
    j=D.rig(root)
    data["rig"]=json.loads(root["rig"])
    def p(**poses):
        for role,val in poses.items():
            R.pose_h01(root,role,val)
        bpy.context.view_layer.update()
    def find(parent, token):
        return next(o for o in parent if token in o.name and not o.hide_viewport)
    front=find(j["shell"].children,"shell_front")
    back=find(root.children,"shell_back")
    bpy.context.view_layer.update()
    original=front.matrix_world.translation.copy()
    p(shell=30,strip=40)
    data["measured_cover_mm"]=(front.matrix_world.translation-original).length/D.MM
    data["roller_40_deg"]=j["strip"]["roller_angle_deg"]
    p(strip=3.3)
    data["roller_one_step_deg"]=j["strip"]["roller_angle_deg"]
    p(arm=-32)
    head=find(j["arm"].children,"stamp_head")
    m=geom(head)[0]
    data["stamp_gap_mm"]=min(v.z for v in m)/D.MM-(R.ROLL_Z+R.BELT_R+.1)
    p(shell=0,strip=0,arm=0)
    # Actual evaluated bore-length ray along the chamber, separate from the key port.
    chamber=tree([back])
    z0=7.95
    stop=chamber.ray_cast(D._mm((-54,2.8,z0)),Vector((-1,0,0)))[0]
    start=chamber.ray_cast(D._mm((-54,2.8,z0)),Vector((1,0,0)))[0]
    if stop is not None and start is not None:
        data["evaluated_chamber_chord_mm"]=(start-stop).length/D.MM
    # Narrow footprint sample of the real key blade: compare against evaluated core mesh.
    core=next(o for o in j["plug"].children if o.type=="MESH" and not o.hide_viewport)
    R.key_visible(root,True)
    keymesh=[o for o in objects(j["key"]) if "bevelled_blade" in o.name]
    rim=find(root.children,"red_mouth_rim")
    sleeve=find(root.children,"fixed_sleeve")
    ft,rt=tree([front]),tree([rim])
    data["sleeve_end_x_evaluated_mm"]=max(v.x/D.MM for v in geom(sleeve)[0])
    relief=chamber.ray_cast(D._mm((500,0,3.15)),Vector((-1,0,0)))[0]
    data["relief_floor_sample_x_mm"]=relief.x/D.MM
    keychecks=[]
    for step in range(11):
        p(key=.5*step)
        kv=tree(keymesh)
        whole=tree(objects(j["key"]))
        keychecks.append({"insertion_mm":step*.5,"core_overlap_pairs":len(tree([core]).overlap(kv)),
                          "full_key_back_crossings":len(chamber.overlap(whole)),
                          "full_key_front_crossings":len(ft.overlap(whole)),
                          "full_key_rim_crossings":len(rt.overlap(whole))})
    data["key_blade_sweep"]=keychecks
    p(key=0)
    R.key_visible(root,False)
    p(latch=-25)
    stop_tip=find(j["latch"].children,"latch_stop_tip")
    arm_mesh=[o for o in objects(j["arm"]) if "stamp_arm" in o.name]
    stop_tree=tree([stop_tip])
    data["first_stop_overlap_deg"]=None
    for s in range(129):
        value=-s*.25
        p(arm=value)
        if stop_tree.overlap(tree(arm_mesh)):
            data["first_stop_overlap_deg"]=value
            break
    p(arm=0,latch=0)
    save_report()
    if verify:
        print("H01_R2_OK",data["measured_cover_mm"],data["evaluated_chamber_chord_mm"],
              data["stamp_gap_mm"],keychecks,flush=True)
        return
    # 使用两个托轨搭住前后壳的最低点；前轨随滑盖平移，仍在同一底座上。
    lo,hi=[None]*3,[None]*3
    pts=[p for ob in (front,back) for p in geom(ob)[0]]
    lo=[min(v[i] for v in pts)/D.MM for i in range(3)]
    hi=[max(v[i] for v in pts)/D.MM for i in range(3)]
    center=[(a+b)/2 for a,b in zip(lo,hi)]
    zbase=lo[2]-12
    base=D.Part(K,"machine_plinth","white")
    R._box(base,"common_plinth",(center[0],center[1]-15,zbase-9),
           (hi[0]-lo[0])/2+19,(hi[1]-lo[1])/2+44,18,K.white,12,2.5)
    for ob in (front,back):
        points=geom(ob)[0]
        foot=min(points,key=lambda v:v.z)/D.MM
        h=foot.z-zbase
        sk=R._box(R.D.Part(K,"skid","white"),"support_skid",(foot.x,foot.y,zbase+h/2),
                  24,12,h,K.white,5,1.6)
        if ob==front:
            D._adopt(j["shell"],sk)
        else:
            sk.parent=root
    bpy.data.objects["sweep"].location.z=(zbase-18.1)*D.MM
    view=Vector((.56,-1.,.24)).normalized()
    right=Vector((0,0,1)).cross(view).normalized()
    up=view.cross(right).normalized()
    bounds=pts+[v for ob in base.root.children for v in geom(ob)[0]]
    bounds += [v+Vector((0,-.030,0)) for v in geom(front)[0]]
    proj=lambda axis: [v.dot(axis)/D.MM for v in bounds]
    xx,zz=proj(right),proj(up)
    width=max(max(xx)-min(xx),(max(zz)-min(zz))*16/9)*1.10
    b=right*((max(xx)+min(xx))/2)+up*((max(zz)+min(zz))/2)+view*Vector(center).dot(view)
    a=b+1200*view
    # 口袋集中照明只在 30 mm 滑盖打开后启用。
    lamps=[_light("interior_softbox_top",(-50,-26,21),(-49,0,0),.153),
           _light("interior_softbox_bounce",(-48,-28,-18),(-47,1,0),.061)]
    for l in lamps:
        l.data.shape="RECTANGLE"
        l.data.size,l.data.size_y=.112,.017
        l.visible_glossy=False
    for l in lamps:
        l.hide_render=True
    if not preview and not selected:
        D.camera(sc,D._mm(b),1.27,21.,29.,ortho=width*D.MM)
        sc.camera.location=D._mm(a)
        sc.camera.rotation_euler=(D._mm(b)-sc.camera.location).to_track_quat("-Z","Y").to_euler()
        # 第 1 帧合盖、第 31 帧滑盖开到位；可通过 role 操作其它关节。
        sc.frame_start,sc.frame_end=1,120
        for frame,v in ((1,0),(31,30)):
            p(shell=v)
            j["shell"].keyframe_insert(data_path="location",frame=frame)
        for frame,name in ((1,"CLOSED"),(31,"SLIDE OPEN"),(46,"KEY SEATS"),
                           (63,"LATCH TURNS"),(84,"STAMP"),(101,"PAPER ADVANCES")):
            sc.timeline_markers.new(name,frame=frame)
        sc.frame_set(1)
        bpy.ops.file.pack_all()
        bpy.context.preferences.filepaths.save_version=0
        bpy.ops.wm.save_as_mainfile(filepath=str(dest/f"{target}_r2.blend"))
        j["shell"].animation_data_clear()
    pic("closed",a,b,width)
    spot=_light("mouth_inspection",(31,0,0),(-1,0,0),.041)
    pic("port",(510,.15,0),(-.5,0,0),13.)
    spot.hide_render=True
    p(shell=30)
    pic("open_wide",a,b,width)
    for l in lamps:
        l.hide_render=False
    pic("open",(-47,-31,5.9),(-47,0,.6),112)
    R.key_visible(root,True)
    back.hide_render=rim.hide_render=True  # 插钥匙定位三图使用检查剖视，合盖透视另出。
    for label,value in (("key_000",0.),("key_050",2.5),("key_100",5.)):
        p(key=value)
        pic(label,(1.5,-28,3.75),(.4,0,.4),25.5,True)
    back.hide_render=rim.hide_render=False
    p(key=5,plug=90,latch=-25)
    pic("turn_latch",(-30,-31,2.6),(-30,0,1),62.)
    p(key=0,plug=0,latch=0)
    R.key_visible(root,False)
    p(arm=-32,crank=158,bead=0)
    pic("stamp",(-68,-29,-.5),(-68,0,-3.5),49.)
    p(arm=0,strip=3.3)
    pic("strip_step",(-72,-29,-2.6),(-72,0,-5),31.)
    p(strip=0,crank=0,bead=-12)
    pic("detail_pins",(-7.5,-27,7.2),(-4.0,0,3.8),14.5,True)
    pic("detail_drive",(-34,-29,5),(-31,0,.2),29.5,True)
    p(arm=-32)
    pic("detail_belt",(-72,-29,-.2),(-70,0,-5.05),28,True)
    save_report()
    print("H01_R2_DONE",len(data["renders"]),flush=True)


if target=="h01":
    h01()



def overlaps(a,b):
    return bool(a.overlap(b))


def h06():
    global root
    root=R.h06_pin_lock(K)
    bpy.context.view_layer.update()
    j=D.rig(root)
    rotor=objects(j["plug"])
    statics=[o for o in objects(root) if o not in rotor and o not in objects(j["shackle"])]
    groups={"upper_pins_and_springs":[o for n in range(5) for o in objects(j[f"pin_{n}"])],
            "case_and_bearings":[o for o in statics if all(o not in objects(j[f"pin_{n}"]) for n in range(5))]}
    fixed={k:tree(obs) for k,obs in groups.items()}
    fail=[]
    # 0.5° 间隔，既核对锁芯，也把五根实际随转的下销纳入移动组。
    for step in range(181):
        deg=step*.5
        D.pose(root,"plug",deg)
        bpy.context.view_layer.update()
        mobile=tree(rotor)
        tags=[k for k,st in fixed.items() if overlaps(mobile,st)]
        if tags:
            if len(fail)<2:
                pairs=[[m.name,o.name] for m in rotor for o in statics if overlaps(tree([m]),tree([o]))]
                print("H06_CONTACT",deg,pairs,flush=True)
            fail.append([deg,tags])
    D.pose(root,"plug",0)
    bpy.context.view_layer.update()
    hi=[min(v.z for v in geom(o)[0])/D.MM+.55 for o in groups["upper_pins_and_springs"] if "upper_pin" in o.name]
    lo=[max(v.z for v in geom(o)[0])/D.MM+.55 for o in rotor if "lower_pin" in o.name]
    data.update({"angles":181,"crossings":fail,"lower_edge_mm":lo,"upper_edge_mm":hi,
                 "sleeve_id_mm":root["sleeve_id_mm"],"seat_clearance_mm":root["seat_clearance_mm"]})
    # 和上一轮同一网格检具：从 048 实体齿面射线读取，不以销长配置代替钥匙验证。
    w,u,v=map(Vector,((0,-1,0),R.Z,R.X))
    origin=Vector((0,-1.5,-.55))
    key=D.h02_key(K,which="048",scale=1.3)
    rot=R.Matrix((-w,-u,-v)).transposed()
    key.rotation_euler=rot.to_euler()
    key.location=D._mm(origin+key["insertion_offset_u_mm"]*u-rot@Vector((8.45,0,0)))
    bpy.context.view_layer.update()
    kt=tree(objects(key))
    heights=[]
    for i in range(5):
        at=origin+(.5+i)*1.3*w
        hit=kt.ray_cast(D._mm(at+4*u),-u)[0]
        heights.append((hit/D.MM-at).dot(u))
    data["key_shear_error_mm"]={p:[round(h+length-root["shear_line_mm"],4)
                                 for h,length in zip(heights,lengths)]
                               for p,lengths in D._LOCK_PRESETS.items()}
    for o in objects(key):
        o.hide_render=True
    print("H06_CHECK",len(fail),data["key_shear_error_mm"],flush=True)
    if not verify:
        stand(root,28,24)
        for x in (-6,6):
            R._box(D.Part(K,"lock_perch","white"),"rest",(x,0,2.16),2.15,5.8,1.12,K.white)
        pic("aligned",(22,-47,25),(0,0,4.3),40)
        pic("detail_aligned",(26,-17,8),(.25,-4.4,2.75),17.2,True)
        D.pose(root,"plug",90)
        D.pose(root,"shackle",4)
        bpy.context.view_layer.update()
        pic("turned",(22,-47,25),(0,0,5.4),44)
        pic("detail_shear",(25,-17,7),(.2,-4.4,2.35),17.2,True)
    save_report()


def bbox(oblist):
    points=[p/D.MM for o in oblist for p in geom(o)[0]]
    return ([min(p[i] for p in points) for i in range(3)],
            [max(p[i] for p in points) for i in range(3)])


def h03():
    global root
    root=R.h03_loop_track(K)
    order=json.loads(root["token_order"])
    rig=D.rig(root)
    bpy.context.view_layer.update()
    mech=[o for role in order for o in objects(rig[role])]
    # 先复用同一局部网格，再仅平移 6 mm。固定台座与导轨不跟扫掠重算。
    b=[bbox(objects(rig[role])) for role in order]
    gap=min(b[i+8][0][2]-b[i][1][2] for i in range(56))
    static=tree([o for o in objects(root) if o not in mech])
    crossings=[]
    for index,role in enumerate(order):
        obs=objects(rig[role])
        local=[geom(o) for o in obs]
        for k in range(11):
            offset=Vector((0,0,6*(1-k/10)*D.MM))
            for vs,fs in local:
                if overlaps(BVHTree.FromPolygons([v+offset for v in vs],fs),static):
                    crossings.append((role,k))
                    break
    plate=[o for o in objects(root) if "_plate_COST" in o.name or "_plate_TIME" in o.name]
    data.update({"schedule_order":order,"moving_samples":len(order)*11,
                 "stack_min_axial_clearance_mm":gap,"token_static_crossings":crossings,
                 "plates":len(plate),"plate_bounds_mm":[bbox([o]) for o in plate]})
    print("H03_CHECK",len(order),gap,len(crossings),flush=True)
    if not verify:
        stand(root,55,36)
        pic("overview",(1,-5,78),(0,0,4),63)
        pic("detail_cost_time",(10,-11,27),(9,-4.8,4.55),17.5,True)
        R.pose_tokens(root,.5)
        bpy.context.view_layer.update()
        pic("token_sequence_mid",(6,-36,41),(0,0,5.5),60)
    save_report()


def h04():
    global root
    root=R.h04_chem42_chip(K)
    rig=D.rig(root)
    cars=[r for r in rig if r.startswith("loop_")]
    standin=[o for o in objects(root) if "_foot" in o.name]
    array_guide=[o for o in objects(root) if "_track" in o.name or "reflow_row" in o.name]
    D.pose(root,"lid",120)
    bpy.context.view_layer.update()
    bounds=[bbox([o]) for o in standin]
    gaps=[]
    for i,(lo,hi) in enumerate(bounds):
        for lo2,hi2 in bounds[i+1:]:
            sep=max(lo2[0]-hi[0],lo[0]-hi2[0],lo2[1]-hi[1],lo[1]-hi2[1])
            gaps.append(sep)
    # 检查每部小车：自身轨道 / 板脚、邻轨、回流管、中央插座。
    socket=[o for o in objects(root) if "__socket" in o.name]
    rails=tree(standin+array_guide+socket)
    hits=[]
    for k in cars:
        obs=objects(rig[k])
        for i in range(25):
            D.pose(root,k,i/24)
            bpy.context.view_layer.update()
            if overlaps(tree(obs),rails):
                hits.append([k,i])
                if len(hits)==1:
                    print("H04_FIRST_CONTACT",k,i,[o.name for o in standin+array_guide+socket
                                                   if overlaps(tree(obs),tree([o]))],flush=True)
        D.pose(root,k,0)
    for i,digit in enumerate((8,9,1,8)):
        D.pose(root,f"odo_{i}",36*digit)
    bpy.context.view_layer.update()
    code="".join(max((o for o in rig[f"odo_{i}"].children if o.type=="FONT"),
                     key=lambda o:(o.matrix_world.to_3x3()@Vector(R.Z)).z).data.body
                 for i in range(4))
    data.update({"tracks":len(cars),"scale":root["loop_scale"],"foot_count":len(standin),
                 "min_foot_gap_mm":min(gaps),"car_samples":len(cars)*25,
                 "contacts":hits,"odo":code,"return_lines":sum("reflow_row" in o.name for o in array_guide)})
    print("H04_CHECK",len(cars),min(gaps),len(hits),code,flush=True)
    if not verify:
        stand(root,54,47,y=-4.4)
        pic("array_wide",(0,-13,87),(0,-4,2.6),84)
        pic("array_detail",(0,-3,58),(0,0,1.25),46.5,True)
        pic("detail_odo",(25,-8,22),(19.1,0,3.62),13.5,True)
    save_report()


{"h06":h06,"h03":h03,"h04":h04}.get(target,lambda:None)()
