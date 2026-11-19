"""HKBU SCIE1007 课程作业的科普视频：P0 第 3 轮盖章机和销子锁。"""
import json
import math

import bpy
from mathutils import Matrix, Vector
import kit_deep as D
import kit_deep_r2 as R
from kit_deep_r2 import X, Y, Z, _box, _tube, _rod, _lower_carrier

def h06_pin_lock(K,preset="own",cut=True):
    if preset not in D._LOCK_PRESETS:
        raise ValueError(preset)
    P=D.Part(K,"h06_pin_lock","blue")
    _,shackle=D._lock_case(P,False)
    # 换掉旧壳，保留同一锁梁。加厚只发生在高度，包住原来的销簧组。
    for ob in list(P.root.children):
        if ob != shackle:
            ob.hide_render=ob.hide_viewport=True
    body=_box(P,"inset_housing",(0,0,1.2),10,8,14,K.blue,1.6,.48)
    w=Vector((0,-1,0))
    for x in (-5.75,5.75):
        D._boolean(body,D._cyl(P,(x,0,5.1),Z,1.033,9,K.blue,0))
    for x in (-7.7,7.7):
        D._screw(P,(x,-8,-2.8),w,.49,K.gold_satin)
    # 沿锁芯轴剖去右上象限；后壁和锁梁导向孔保持完整。
    def quadrant(name, y0, y1, edge=0.0):
        return _box(P,name,(10+edge,(y0+y1)/2,9.45),10,(y1-y0)/2,
                    20,K.blue,0,0)
    if cut:
        D._boolean(body,quadrant("frontal_quadrant",-9,.88))
    w,u=Vector((0,-1,0)),Vector(Z)
    q=lambda a,b,c=0: Vector((c,-1.5-a,-.55+b))
    s=1.3
    rad=2.3*s
    # 14 mm 锁体保留，座孔 Ø9.30 容纳 Ø9.10 外套；外套内径
    # Ø8.20，内端两道轴承把 Ø5.98 的转子定位，不能靠悬空定位。
    D._boolean(body,D._cyl(P,q(2.5,0),w,4.65,9.0,K.blue,0))
    sleeve=_tube(P,"sleeve_9p10_ID8p20",q(2.61,0),w,4.55,4.10,7.8,K.white)
    # Front Y = -8.0；0.3 mm 同心浅倒角环，外套深埋在座孔中。
    ring=_tube(P,"front_bevel_ring",(0,-7.89,-.55),w,4.91,4.61,.38,K.gold_satin)
    ring.modifiers.new("ring chamfer","BEVEL").width=.15*D.MM
    if cut:
        D._boolean(sleeve,quadrant("sleeve_quadrant",-9,-.36))
        D._boolean(ring,quadrant("collar_quadrant",-9,-6))
    for a in (-1.0,6.21):
        bearing=_tube(P,"sleeve_centering_bearing",q(a,0),w,4.14,rad+.045,.46,K.white)
        if cut and a>0:
            D._boolean(bearing,quadrant("bearing_quadrant",-9,-6))
    plug=D._move(P,"plug","rot",(0,90),pivot=q(0,0),axis=w)
    core=D._cyl(P,q(2.6,0),w,rad,7.8,K.gold_satin,.16)
    core.name=P.nm("turning_core")
    D._boolean(core,D._local_box(P,q(3.31,.2*s),w,u,3.37,1.5*s,.5*s*2,K.white,0))
    if cut:
        # 只露出薄薄的轴向截面，不移出或放大下销。
        D._boolean(core,quadrant("core_quadrant",-7.62,-1.72,.016))
    D._adopt(plug,core)
    for i,length in enumerate(D._LOCK_PRESETS[preset]):
        a=(i+.5)*s
        delta=length-D._LOCK_PRESETS["own"][i]
        # 中心剪切线 +2.99 mm；上下销之间留 0.06 mm 可动间隙。
        hi0=rad+.037+delta
        lo0=rad-.019+delta
        D._boolean(core,D._cyl(P,q(a,rad-.74),u,.502*s,2.06*s,K.white,0))
        D._adopt(plug,core.modifiers[0].object)
        if not cut:
            D._boolean(sleeve,D._cyl(P,q(a,4.4),u,.502*s,1.8,K.white,0))
        D._boolean(body,D._cyl(P,q(a,3.4),u,.701,8.7,K.blue,0))
        bridge=_tube(P,f"upper_fixed_guide_{i}",q(a,4.55),u,.76,.655,3.06,K.white)
        # Guide lower face is rad + .03, outside the turning core.
        bridge.location.z+=.012*D.MM
        if cut:
            D._boolean(bridge,_box(P,"guide_check_window",q(a,4.63,.76),.76,.40,3.03,K.white,0,0))
        pin=D._move(P,f"pin_{i}","loc",(0,3.1),pivot=q(a,rad),axis=u)
        low=D._cyl(P,q(a,lo0-length/2),u,.451*s,length,K.gold,.055)
        low.name=P.nm(f"lower_pin_{i}")
        if preset=="own":
            rounding=D._cyl(P,q(2.6,0),w,rad-.018,7.85,K.white,0)
            D._boolean(low,rounding,"INTERSECT")
        _lower_carrier(P,plug,pin,low,q(a,rad),u)
        high=D._cyl(P,q(a,hi0+1.25),u,.448*s,2.5,K.white,.05)
        high.name=P.nm(f"upper_pin_{i}")
        spring=P.tube([q(a+.48*math.cos(t*math.tau/10),hi0+2.51+t*.016,
                         .48*math.sin(t*math.tau/10)) for t in range(61)],.068,K.white)
        spring.data.bevel_resolution=2
        D._adopt(pin,high,spring)
    if cut:
        _tube(P,"shackle_guide",(-5.75,0,8.17),Z,1.20,1.025,.29,K.blue)
    rail=D._move(P,"shackle","loc",(0,4),pivot=(-5.75,0,-.8),axis=Z)
    D._adopt(rail,shackle)
    P.root["front_face_mm"]=-8.0
    P.root["preset"]=preset
    P.root["lower_pins_mm"]=D._LOCK_PRESETS[preset]
    P.root["sleeve_id_mm"]=8.2
    P.root["seat_clearance_mm"]=.2
    P.root["shear_line_mm"]=rad
    P.gate(-10,3,"-x")
    P.gate(10,3,"+x")
    return P.done()

# 分件面机舱轮廓（X/Z）。左上保留原尺寸孔口；右前角让过铰链。
CHAMBER = [(-121,36),(-94,107),(-38,118),(59,111),(107,79),(144,68),
           (197,102),(224,79),(238,-44),(289,-55),(324,-93),(360,-172),
           (357,-245),(300,-253),(237,-243),(194,-273),(121,-297),
           (24,-303),(-11,-292),(-33,-227),(-51,-198),(-71,-164),(-91,-104),
           (-93,-25),(-117,5)]
PIVOT = (428., R.SEAM, -154.)
DEPTH = 74.
MACHINE_SCALE = 3.25
MACHINE_OFFSET = Vector((217., 0., -105.))


def _xz(P, points, y0, y1, mat, bevel=0):
    plate=P.slab(points,y1-y0,mat,bevel=bevel)
    plate.rotation_euler.x=math.pi/2
    plate.location.y=(y0+y1)/2*D.MM
    return plate


def _painted_label(P, words, size, x, y, z, mat):
    ob=D._label(P,words,size,x,0,0,mat)
    ob.rotation_euler.x=math.pi/2
    ob.location=D._mm((x,y,z))
    return ob


def _bearing(P, name, x, z, y, axle, r):
    K=P.K
    housing=_box(P,name,(x,y,z),r+1,2.5,2*r+2,K.white,1.1,.45)
    D._boolean(housing,D._cyl(P,(x,y,z),Y,axle+.35,9,K.white,0))
    _tube(P,name+"_bushing",(x,y,z),Y,axle+.78,axle+.18,5.8,K.gold_satin)
    _tube(P,name+"_washer",(x,y-3.1,z),Y,axle+1.2,axle+.1,.7,K.white)
    _tube(P,name+"_retaining_ring",(x,y-3.75,z),Y,axle+.55,axle+.09,.35,K.ink)


def _cassette(P):
    K=P.K
    # 同一个腔形用于后框、底板和壳体。装配面不再是细长矩形。
    center=Vector((93.,-92.))
    contour=lambda f:[tuple(center+(Vector(q)-center)*f) for q in CHAMBER]
    base=_xz(P,contour(.967),22,28,K.inkg,.84)
    base.name=P.nm("structural_backplate")
    inner=_xz(P,contour(.898),-8,32,K.white)
    edge=_xz(P,contour(.989),-4,26,K.white,.45)
    edge.name=P.nm("chamber_liner")
    D._boolean(edge,inner)
    for x in (-50,-19,12,43,74,105,136,167,198,229,260,291,322):
        if x<=229:
            z=-170 if x<0 else -226
            _box(P,"back_panel_rib",(x,20,z),2.4,2.5,44,K.white,1.1,.45)
    for x,z in ((-68,-21),(27,84),(201,70),(255,-88),(309,-183),(251,-223),
                (111,-260),(15,-252),(-54,-139)):
        _tube(P,"screw_pillar",(x,17,z),Y,5.8,2.5,12,K.white)
        D._screw(P,(x,10.9,z),(0,-1,0),3.2,K.gold_satin)
    # 前后承载件与盖板在位置上错层，不靠在底板上印图。
    for x,z,w,h in ((71,68,131,38),(196,-207,105,45),(296,-181,61,62)):
        _box(P,"structural_service_cover",(x,13,z),w/2,4.8,h,K.blue,4,1.4)
        for sx in (x-w*.40,x+w*.40):
            for sz in (z-h*.32,z+h*.32):
                D._screw(P,(sx,8,sz),(0,-1,0),2.0,K.white)
        for n in range(5):
            _box(P,"raised_vent_rib",(x+(n-2)*w*.105,7.4,z),
                  w*.021,1.1,h*.46,K.white,1.0,.37)
    _box(P,"drive_module_bed",(91,16,-114),136,3.6,78,K.blue,4.,1.2)
    for x,z in ((-36,-145),(218,-145),(-36,-83),(218,-83)):
        D._screw(P,(x,12.2,z),(0,-1,0),3.1,K.gold_satin)
    # Separate grooves read as cable channels, with two independent flexible runs.
    for i in (.845,.885):
        xy=contour(i)
        ob=P.tube([(x,14.3,z) for x,z in xy+[xy[0]]],1.12,K.inkg)
        ob.data.bevel_resolution=2
    for path,mat in (
        ([(-4,4,4),(-19,11,17),(-43,14,24),(-64,14,13),(-67,10,-30),
          (-59,13,-75),(-51,14,-146),(-31,15,-192),(40,13,-226),(66,10,-215)],K.red),
        ([(-6,6,-3),(-17,12,6),(-38,15,15),(-53,16,-5),(-57,14,-58),(-45,15,-121),
          (-35,17,-167),(-13,14,-203),(51,11,-217),(71,9,-207)],K.blue)):
        hose=P.tube(path,2.1,mat)
        hose.data.bevel_resolution=4
        for x,y,z in (path[0],path[-1]):
            D._cyl(P,(x,y,z),Y,3.1,4,K.gold_satin,.45)
    for x,z,txt in ((44,55,"CDK20-01"),(170,-23,"CDK20-02"),(126,-199,"CDK20-03")):
        badge=_box(P,"numbered_panel",(x,20,z),27,2.2,13,K.blue,1.8,.65)
        _painted_label(P,txt,8,x,17.71,z-.7,K.inkw)


def _filter(P, keep):
    for ob in list(P.root.children):
        if not keep(ob):
            ob.hide_render=ob.hide_viewport=True
            for child in ob.children_recursive:
                child.hide_render=child.hide_viewport=True


def _machine(P):
    # 用上一轮丝毫不变的 048 / 销簧 / 口轴建立输入检具，并将原传动放大到新底板。
    port=D.Part(P.K,"port_048","blue")
    R._works(port)
    r=port.done()
    r.parent=P.root
    pins=tuple(f"pin_{i}" for i in range(5))
    port_roles={"plug","key",*pins}
    port_mesh=("fixed_sleeve","barrel_mount","fixed_pin_guide","pin_bridge")
    _filter(port,lambda o:o.get("role") in port_roles or
            any(t in o.name for t in port_mesh))
    R.key_visible(r,False)
    r["section"]="048"
    machine=D.Part(P.K,"scaled_works","white")
    R._works(machine)
    mech=machine.done()
    mech.parent=P.root
    mech["section"]="drive"
    _filter(machine,lambda o:o.get("role") not in port_roles and
            not any(t in o.name for t in port_mesh) and
            "cam_link_rest" not in o.name and not
            (o.type=="MESH" and o.name.startswith(machine.name+"_cy") and
             abs(o.location.x/D.MM+14.625)<.07))
    mech.scale=(MACHINE_SCALE,3.8,MACHINE_SCALE)
    mech.location=D._mm(MACHINE_OFFSET)
    K=P.K
    # 后板 → 传动 → 前轴座。每端轴承、垫圈与挡圈独立建网格。
    for j,x0,z0 in (("crank",-24,0),("latch",-42,0),("arm",-54,0),
                    ("roller_input",-62,R.ROLL_Z),("roller_output",-82,R.ROLL_Z)):
        x,_,z=MACHINE_OFFSET+MACHINE_SCALE*Vector((x0,0,z0))
        _rod(P,(x,-17,z),(x,21,z),1.36,K.gold_satin)
        _bearing(P,j+"_front",x,z,-13,1.5,4.2)
        _bearing(P,j+"_rear",x,z,17,1.5,5.1)
    # 正面齿轮键固定在同一曲柄轴，凸销和编号跟着运动。
    crank=D.rig(mech)["crank"]
    x=-24.; z=0.
    for ob in list(crank.children):
        if "_crank_8_tooth" in ob.name:
            ob.data.materials[0]=K.gold_satin
            ob.scale=(1.29,1.29,1)
    for n in range(3):
        a=n*math.tau/3
        tick=D._cyl(machine,(x+2.25*math.cos(a),-.71,z+2.25*math.sin(a)),
                    Y,.21,.21,K.ink,.04)
        D._adopt(crank,tick)
    for role,x0 in (("arm",-58.),("latch",-47.6)):
        joint=D.rig(mech)[role]
        tag=_painted_label(machine,{"arm":"03","latch":"02"}[role],
                           1.,x0,-1.23,.25,K.ink)
        D._adopt(joint,tag)
    # 辊罩是带观察窗的桥架，纸上的印记在罩中间仍可见。
    for x in (-49.,15.):
        for z in (-143,-124):
            rib=_box(P,"roller_guard",(x,-14,z),6,3.3,4,K.blue,1.8,.61)
            D._screw(P,(x,-17.2,z),(0,-1,0),1.5,K.white)
    for x in (-49.,15.):
        _box(P,"roller_guard_end",(x,-14,-134),1.5,2.6,21,K.blue,1.3,.51)
    for a,b,rad in (((-8.6,0,0),(-23,0,0),1.05),
                    ((-23,0,0),(-35,3,-26),2.6),
                    ((-35,3,-26),(121,3,-52),3.35),
                    ((121,3,-52),(139,3,-105),3.6)):
        va,vb=Vector(a),Vector(b)
        _rod(P,va,vb,rad,K.gold_satin)
        _tube(P,"transition_socket",(va+vb)/2,(vb-va),rad+1.2,rad-.05,11,K.white)
        P.ball(*b,rad+1.1,K.gold_satin,seg=24)
    return r,mech


def h01_cdk20_lockworks(K,lod="hero"):
    if lod=="mini":
        return R.h01_cdk20_lockworks(K,lod)
    if lod!="hero":
        raise ValueError(lod)
    P=D.Part(K,"h01_lockworks_r3","blue")
    back,_=R._surface(P)
    front=D._copy(back,P.nm("shell_front"))
    back.name=P.nm("shell_back")
    for ob,sign,y0,y1 in ((back,1,-4.4,34),(front,-1,-40,-3.9)):
        seam=_box(P,"split_plane",(0,R.SEAM+sign*501+sign*.075,0),1000,501,
                  2000,K.blue,0,0)
        R._apply_cut(ob,seam,"INTERSECT")
        def seam_area():
            ob.data.calc_loop_triangles()
            return sum(tri.area/D.MM**2 for tri in ob.data.loop_triangles
                       if all(abs(ob.data.vertices[i].co.y/D.MM-(R.SEAM+.075))<.008
                              for i in tri.vertices))
        if sign==1:
            P.root["seam_area_mm2"]=seam_area()
        R._apply_cut(ob,_xz(P,CHAMBER,y0,y1,K.blue))
        if sign==1:
            P.root["chamber_cut_area_mm2"]=P.root["seam_area_mm2"]-seam_area()

        for x,r,length in ((249.68,4.62,500.64),(-7.25,3.57,11.7),(-6,2.50,20)):
            R._apply_cut(ob,D._cyl(P,(x,0,0),X,r,length,K.blue,0))
    door=D._move(P,"shell","rot",(0,110),pivot=PIVOT,axis=Z)
    hinge=_tube(P,"moving_hinge_knuckle",(428,R.SEAM,-151),Z,10,5.8,42,K.white)
    strap=_box(P,"moving_hinge_leaf",(399,-8,-177),29,3,15,K.blue,2,.7)
    D._adopt(door,front,hinge,strap)
    _rod(P,(428,R.SEAM,-207),(428,R.SEAM,-110),5.4,K.gold_satin)
    for z in (-195,-116):
        _tube(P,"fixed_hinge_knuckle",(428,R.SEAM,z),Z,10,5.8,17,K.white)
        _box(P,"fixed_hinge_leaf",(398,6,z),30,3,11,K.blue,2,.7)
    _cassette(P)
    r,mech=_machine(P)
    spec=json.loads(P.root["rig"])
    for child in (mech,r):
        for name,role in json.loads(child["rig"]).items():
            if not D.rig(child)[name].hide_render:
                spec[name]=role
    P.root["rig"]=json.dumps(spec)
    P.root["chamber_depth_mm"]=DEPTH
    P.root["works_scale"]=MACHINE_SCALE
    return P.done()


def rig(root):
    result=D.rig(root)
    for sub in root.children:
        if sub.get("section") in {"048","drive"}:
            result.update((name,ob) for name,ob in D.rig(sub).items() if not ob.hide_render)
    return result


def pose(root,role,value):
    joint=rig(root)[role]
    if joint.parent != root:
        return R.pose_h01(joint.parent,role,value)
    return D.pose(root,role,value)


def rest(root):
    for role,spec in json.loads(root["rig"]).items():
        pose(root,role,spec["rest"])


def key_visible(root,visible):
    R.key_visible(rig(root)["key"].parent,visible)
