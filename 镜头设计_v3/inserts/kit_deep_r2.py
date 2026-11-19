"""HKBU SCIE1007 课程作业的科普视频：P0 第 2 轮，H01 盖章机道具。"""
import math
import json

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
import kit_deep as D

X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
SCALE = 20.
SEAM = -4.1
ROLLER_R = 1.5
BELT_R = 1.6
ROLL_X = -62.
ROLL_Z = -6.65
LOOP = 40 + math.tau * BELT_R


def _tube(P, name, xyz, axis, ro, ri, length, color):
    obj = D._tube_axis(P, xyz, axis, ro, ri, length, color, n=48)
    obj.name = P.nm(name)
    return obj


def _box(P, name, xyz, hx, hy, h, color, r=.35, bevel=.12):
    x,y,z = xyz
    obj = P.box(x,y,hx,hy,h,color,z=z,r=r,bevel=bevel)
    obj.name = P.nm(name)
    return obj


def _rod(P, a, b, radius, color):
    a,b = Vector(a), Vector(b)
    return D._cyl(P,(a+b)/2,(b-a),radius,(b-a).length,color,.025)


def _apply_cut(obj, tool, op="DIFFERENCE"):
    D._apply(obj,D._boolean(obj,tool,op))


def _surface(P):
    # 只重网格施工副本，缩放后把 W / V / U 分别转入局部 X / Y / Z。
    body,seat,w = D._shell_source(P)
    peg = next(o for o in P.root.children if o != body)
    bpy.data.objects.remove(peg,do_unlink=True)
    rem=body.modifiers.new("source manifold","REMESH")
    rem.mode,rem.voxel_size,rem.use_smooth_shade="VOXEL",.16*D.MM,True
    D._apply(body,rem)
    bpy.context.view_layer.update()
    u=(Vector(Z)-w.z*w).normalized()
    v=u.cross(w)
    origin=D._tree(body).ray_cast(D._mm(seat+45*w),-w)[0]
    body.data.transform(Matrix((w,v,u)).to_4x4() @ Matrix.Translation(-origin))
    body.data.transform(Matrix.Diagonal((SCALE,SCALE,SCALE,1.)))
    bpy.context.view_layer.update()
    surface=D._tree(body)
    # 85.5 mm 圆角机舱，最薄余量取 1 mm 格距采样；止口在分件线上单独切。
    outer_wall = 1e3
    for i in range(87):
        for y in (-8,-4,0,4,7):
            for z in (-9,-6,0,6,9):
                pt=D._mm((-12.0-85.5*i/86,y,z))
                near,n,_,dist=surface.find_nearest(pt)
                outer_wall=min(outer_wall,dist/D.MM*(1 if (near-pt).dot(n)>=0 else -1))
    P.root["shell_scale"] = SCALE
    P.root["cavity_length_mm"] = 85.5
    P.root["mouth_center_mm"] = [0.,0.,0.]
    P.root["mouth_axis"] = list(X)
    P.root["cavity_wall_grid_min_mm"] = outer_wall
    # 贴合原表面起伏的红色口缘。投射同一 W，不把孔挪到壳上另一处。
    vs,fs=[],[]
    n=96
    for j in range(n):
        a=j*math.tau/n
        for r,off in ((2.51,-.17),(3.22,-.17),(3.36,.21),(3.25,.45),(2.68,.45),(2.51,.20)):
            y,z=r*math.cos(a),r*math.sin(a)
            hit=surface.ray_cast(D._mm((500,y,z)),Vector((-1,0,0)))[0]
            vs.append((min(hit.x/D.MM,-.64)+off,y,z))
    for j in range(n):
        for k in range(6):
            l=(k+1)%6
            fs.append((j*6+k,j*6+l,((j+1)%n)*6+l,((j+1)%n)*6+k))
    D._mesh(P,"red_mouth_rim",vs,fs,P.K.red,True)
    return body, surface


def _case(P):
    K=P.K
    body, src = _surface(P)
    front=D._copy(body,P.nm("shell_front"))
    body.name=P.nm("shell_back")
    for obj,sign in ((body,1),(front,-1)):
        side=_box(P,"seam_plane",(0,SEAM+sign*501.+sign*.075,0),1000,501.,2000,
                  K.blue,0,0)
        _apply_cut(obj,side,"INTERSECT")
        chamber=_box(P,"cavity",(-54.75,-.5,0),42.75,7.5,18,K.blue,1.45,.25)
        bv=next(m for m in chamber.modifiers if m.type=="BEVEL")
        D._apply(chamber,bv)
        _apply_cut(obj,chamber)
    # 凹槽外圈也沉到原口袋内，留出原尺寸钥匙柄的运动空间，中心仍为 Ø5 通口。
    for obj in (body,front):
        _apply_cut(obj,D._cyl(P,(249.68,0,0),X,4.62,500.64,K.blue,0))
    # 孔后放大为轴肩沉孔，不从外表面切出第二个口。
    _apply_cut(body,D._cyl(P,(-7.25,0,0),X,3.57,11.7,K.blue,0))
    bay=P.slab([(-15,-1.3),(-9.3,-1.3),(-4.3,1.5),(-1.1,3.2),
                (-1.1,7.9),(-15,7.9)],9.3,K.blue,bevel=0)
    bay.rotation_euler.x=math.pi/2
    _apply_cut(body,bay)
    _apply_cut(front,D._copy(bay,P.nm("front_check_cut")))
    # 通口最后加工：前一级沉台和检查窗先成形，避免共面布尔在孔口留下封片。
    _apply_cut(body,D._cyl(P,(-6,0,0),X,2.50,20,K.blue,0))
    # 分件处的 1.2 mm 法兰和 0.4 mm 厚定位止口。长边避开轨道导套。
    cover=[]
    for z in (-8.63,8.63):
        cover.append(_box(P,"front_1p2_flange",(-54,SEAM-.675,z),40.3,.60,.80,K.blue,.18,.07))
        cover.append(_box(P,"front_0p4_rabbet",(-54,SEAM+.065,z),40,.20,.37,K.blue,.14,.04))
    travel=D._move(P,"shell","loc",(0,30),axis=(0,-1,0))
    front["role_name"]="shell_front"
    D._adopt(travel,front,*cover)
    for x in (-14.5,-94):
        for z in (-7.1,7.1):
            # 端位仍有 3 mm 啮合，导轨和盖上的轴孔沿同一 Y 轴。
            _apply_cut(front,D._cyl(P,(x,SEAM-18,z),Y,.85,36,K.blue,0))
            fixed=D._cyl(P,(x,SEAM-15.9,z),Y,.72,36,K.white,.12)
            fixed.name=P.nm("cover_guide")
            _rod(P,(x,SEAM+2.02,z),(x,4.21,z),.73,K.white)
            ferrule=_tube(P,"cover_bushing",(x,SEAM-.84,z),Y,1.07,.845,1.35,K.blue)
            D._adopt(travel,ferrule)
    for x in range(-93,-13,3):
        _box(P,"bulkhead_rib",(x,6.84,0),.25,.35,17.2,K.blue,.17,.055)
    for x in (-17,-91):
        for z in (-6.6,6.6):
            _tube(P,"chassis_boss",(x,5.85,z),Y,1.12,.52,2.3,K.blue)
            D._screw(P,(x,4.10,z),(0,-1,0),.61,K.white)
    _box(P,"chassis",(-54,4.55,0),39.5,.45,15.6,K.white,.35,.16)
    for y,z in ((6.,-3.5),(8.,0.),(6.,3.5)):
        hit=src.ray_cast(D._mm((-450,y,z)),Vector(X))[0]
        if hit:
            x=hit.x/D.MM
            _apply_cut(body,D._cyl(P,(x-.035,y,z),X,.4,.27,K.blue,0))
    idplate=D._local_box(P,(-38,4.015,6.6),X,Z,3,1,.37,K.blue,.06)
    idplate.name=P.nm("nameplate")
    mark=D._label(P,"CDK20",1.2,-38,0,0,K.inkw)
    mark.location=D._mm((-38,3.809,6.6))
    mark.rotation_euler.x=math.pi/2
    return body,front,travel


def _belt_frame(s):
    s=s%LOOP
    if s<20:
        x,z,a=ROLL_X-s,ROLL_Z+BELT_R,0.
    elif s<20+math.pi*BELT_R:
        a=(s-20)/BELT_R
        x,z=ROLL_X-20-BELT_R*math.sin(a),ROLL_Z+BELT_R*math.cos(a)
    elif s<40+math.pi*BELT_R:
        a=math.pi
        x,z=ROLL_X-20+s-20-math.pi*BELT_R,ROLL_Z-BELT_R
    else:
        a=math.pi+(s-40-math.pi*BELT_R)/BELT_R
        x,z=ROLL_X-BELT_R*math.sin(a),ROLL_Z+BELT_R*math.cos(a)
    return x,z,a


def _paper(P):
    K=P.K
    j=D._move(P,"strip","belt",(0,40))
    spec=json.loads(P.root["rig"])
    spec["strip"]["unit"]="mm"
    P.root["rig"]=json.dumps(spec)
    vertices,faces=[],[]
    for i in range(256):
        x,z,a=_belt_frame(LOOP*i/256)
        for dr,y in ((-.10,-2),(-.10,2),(.10,2),(.10,-2)):
            vertices.append((x-dr*math.sin(a),y,z+dr*math.cos(a)))
        for k in range(4):
            l=(k+1)%4
            faces.append((4*i+k,4*i+l,4*((i+1)%256)+l,4*((i+1)%256)+k))
    D._mesh(P,"continuous_paper",vertices,faces,K.white,True)
    # 印记分成细片贴合滚轮曲率，而不是在滚轮端点用一整张刚性方片。
    for i in range(12):
        mesh=D._mesh(P,"stamp_{}".format(i),[(0,0,0)]*22,
                     [(2*k,2*k+1,2*k+3,2*k+2) for k in range(10)],K.ink)
        mesh.name="stamp_{}".format(i)
        mesh.parent=j
        mesh["stamp_index"]=i
    for x in (ROLL_X,ROLL_X-20):
        roll=_tube(P,"paper_roller",(x,0,ROLL_Z),Y,ROLLER_R,.56,4,K.white)
        roll.parent=j
        roll["roller"]=True
        _rod(P,(x,-2.48,ROLL_Z),(x,4.1,ROLL_Z),.52,K.white)
        ring=_tube(P,"roller_cap",(x,-2.06,ROLL_Z),Y,1.24,.56,.12,K.white)
        dial=_box(P,"roller_index",(x,-2.13,ROLL_Z+.84),.14,.063,.36,K.ink,.03,.02)
        D._adopt(j,ring,dial)
        dial.parent=roll
        dial.matrix_parent_inverse=roll.matrix_basis.inverted()
        ring.parent=roll
        ring.matrix_parent_inverse=roll.matrix_basis.inverted()
        _tube(P,"roller_bearing",(x,2.23,ROLL_Z),Y,.83,.55,.47,K.white)
    _box(P,"print_anvil",(-72,0,-5.33),6.2,2.05,.20,K.white,.14,.035)
    _box(P,"belt_stanchion",(-72,2.95,-5.33),5.95,1.2,.26,K.white,.16,.07)
    paper_pose(j,0)


def paper_pose(j,s):
    for obj in j.children:
        if obj.get("roller"):
            # 局部 Z 已作为滚轮轴，保持其初始安装矩阵，附加旋转。
            if "axle_rest" not in obj:
                obj["axle_rest"] = list(obj.rotation_euler)
            from mathutils import Euler
            obj.rotation_euler=(Euler(obj["axle_rest"]).to_matrix() @
                                Matrix.Rotation(-s/ROLLER_R,3,"Z")).to_euler()
        if "stamp_index" in obj:
            for k in range(11):
                x,z,a=_belt_frame(1.3+obj["stamp_index"]*3.3+s+k*.2-1.)
                for q,y in enumerate((-1,1)):
                    obj.data.vertices[2*k+q].co=D._mm((x-.108*math.sin(a),y,z+.108*math.cos(a)))
            obj.data.update()
    j["roller_angle_deg"]=math.degrees(s/ROLLER_R)


def _drive(P, name, pivot, angle, span, color, radius):
    K=P.K
    j=D._move(P,name,"rot",angle,pivot=pivot,axis=Y)
    x,y,z=pivot
    _rod(P,(x,y-.9,z),(x,4.15,z),radius*.51,K.white)
    _tube(P,name+"_journal",(x,2.45,z),Y,radius,.53*radius,2.6,K.white)
    collar=_tube(P,name+"_hub",pivot,Y,radius,.53*radius,1.2,color)
    D._adopt(j,collar)
    if span is not None:
        D._adopt(j,_box(P,name+"_body",(x+span/2,y,z),abs(span)/2+.3,.8,1.6,color,.3,.12))
    return j


def _works(P):
    K=P.K
    # 外套头在表面之后 1.4 mm；槽口基准向上 .2 mm 适配原比例钥匙。
    q=lambda a,b,c: Vector((-6.4+a,c,b))
    plug=D._barrel(P,q,Vector(X),Vector(Z),Vector(Y),D._PIN_LENGTHS)
    core=next(o for o in plug.children if not o.hide_render)
    slot=next(m.object for m in core.modifiers if m.object.type=="MESH"
              and max(m.object.dimensions)/D.MM>3)
    slot.location.z += .18*D.MM
    plug["key_home_x"] = 5.1
    sleeve=next(o for o in P.root.children if o.type=="MESH" and
                max(abs(o.location.x/D.MM+4.4),abs(o.location.z/D.MM))<.01 and o!=core)
    sleeve.name=P.nm("fixed_sleeve")
    # 前侧开检查窗，同时保留完整的最前端箍。
    D._boolean(sleeve,_box(P,"sleeve_cutaway",(-4.72,-3.3,2.75),2.30,2.4,4.6,K.white,0,0))
    _box(P,"barrel_mount",(-7.3,3.82,2.1),1.2,.62,3.9,K.white,.29,.12)
    for i in range(5):
        pin=D.rig(P.root)[f"pin_{i}"]
        xpos=-5.9+i
        guide=_tube(P,"fixed_pin_guide",(xpos,0,5.5),Z,.485,.462,3.15,K.blue)
        D._boolean(guide,_box(P,"guide_window",(xpos,-.49,5.57),.33,.39,2.55,K.blue,0,0))
        lo=next(o for o in pin.children if o.type=="MESH" and o.data.materials[0]==K.gold)
        hi=next(o for o in pin.children if o.type=="MESH" and o.data.materials[0]==K.white)
        hi.location.z+=.032*D.MM
        rounding=D._cyl(P,q(2,0,0),X,2.283,6.2,K.white,0)
        D._boolean(lo,rounding,"INTERSECT")
        _lower_carrier(P,plug,pin,lo,q(.5+i,2.3,0),Vector(Z))
        _box(P,"pin_bridge",(xpos,2.19,6.84),.42,2,1.,K.white,.16,.08)
    D._adopt(plug,_box(P,"eccentric_cam",(-8.1,0,.55),.5,.5,2.,K.gold_satin,.16,.08))
    _rod(P,(-8.65,0,0),(-20.6,0,0),.45,K.white)
    _box(P,"cam_link_rest",(-16,2.0,0),.42,2.1,1.1,K.white,.2,.08)
    crank=_drive(P,"crank",(-24,0,0),(0,360),None,K.white,1.22)
    tooth=[(rr*math.cos(i*math.tau/32),rr*math.sin(i*math.tau/32))
           for i,rr in enumerate((3.,3.,2.5,2.5)*8)]
    gear=P.slab(tooth,1.2,K.white,bevel=.13,holes=[(0,0,.68)])
    gear.name=P.nm("crank_8_tooth")
    gear.location=D._mm((-24,0,0))
    gear.rotation_euler.x=math.pi/2
    D._adopt(crank,gear,D._cyl(P,(-25.7,-.78,0),Y,.4,.49,K.white,.08))
    latch=_drive(P,"latch",(-42,0,0),(-25,0),-11.4,K.red,1.13)
    lr=Matrix.Rotation(math.radians(25),3,"Y")
    lc=Vector((-42,0,0))
    dog=lc+lr@(Vector((-58.55,0,-2.97))-lc)
    dogtip=D._cyl(P,dog,Y,.55,1.55,K.red,.05)
    dogtip.name=P.nm("latch_stop_tip")
    D._adopt(latch,dogtip,_rod(P,(-53.35,0,0),dog,.60,K.red))
    arm=_drive(P,"arm",(-54,0,0),(-32,0),None,K.white,1.2)
    a=math.radians(32)
    R=Matrix.Rotation(a,3,"Y")
    p=Vector((-54,0,0))
    def lift(x,y,z): return p+R@(Vector((x,y,z))-p)
    arm_body=_box(P,"stamp_arm",(0,0,0),7,1,2,K.white,.30,.14)
    arm_body.rotation_euler.y=a
    arm_body.location=D._mm(lift(-61,0,-2.8))
    # 末端印头到印带第一处上表面 0.022 mm。
    head=D._cyl(P,lift(-67.9,0,-4.323),R@Vector(Z),1.5,1.2,K.white,.075)
    head.name=P.nm("stamp_head")
    D._adopt(arm,arm_body,head,_rod(P,(-54,0,0),lift(-55,0,-2.9),.52,K.white))
    # 装配态连杆以两端可动销为基准：穿过画面前方，尾端可见。
    for tag,x0,x1,z,y in (("crank_to_latch",-25.7,-42,0,-1.55),
                           ("latch_to_arm",-53.4,-54,0,-1.76)):
        link=_rod(P,(x0,y,z),(x1,y,z),.44,K.white)
        link.name=P.nm(tag)
        link["drive_link"]=tag
        k0,k1=("crank","latch") if tag=="crank_to_latch" else ("latch","arm")
        for x,k in ((x0,k0),(x1,k1)):
            D._adopt(D.rig(P.root)[k],_rod(P,(x,y-.36,z),(x,.12,z),.35,K.white))
    _paper(P)
    # 料珠和杯座留在底板支撑的开放式导轨，装在机舱内而非壳外。
    bead=D._move(P,"bead","loc",(-12,0),pivot=(-26,0,-6),axis=(-1,0,0),initial=-12)
    for yy,zz in ((-1.8,-6.5),(1.8,-6.5),(0,-7.81)):
        _rod(P,(-27,yy,zz),(-13.2,yy,zz),.29,K.white)
    _tube(P,"feed_cup",(-26.55,0,-6),X,2.7,2.10,2.3,K.white)
    _box(P,"feed_cup_mount",(-27,2.74,-7.35),.80,1.41,1.2,K.white,.16,.08)
    _box(P,"feed_rail_mount",(-15,2.15,-7.52),.42,2.1,.55,K.white,.15,.08)
    D._adopt(bead,P.ball(-26,0,-6,1.8,K.white,seg=24))
    key=D._move(P,"key","loc",(0,5),axis=(-1,0,0))
    tool=D.h02_key(K)
    tool.location=D._mm((5.1,0,.18))
    tool.rotation_euler=(0,0,0)
    tool.matrix_basis=Matrix.Translation(tool.location) @ Matrix(((-1,0,0),(0,0,-1),(0,-1,0))).transposed().to_4x4()
    D._adopt(key,tool)
    # 逆向滑套的空物体和导轨允许分开拆装钥匙；默认合盖模型不带外置钥匙。
    key["accessory"]=True


def h01_cdk20_lockworks(K,lod="hero"):
    if lod=="mini":
        return D.h01_cdk20_lockworks(K,lod)
    if lod!="hero":
        raise ValueError(lod)
    P=D.Part(K,"h01_cdk20_lockworks","blue")
    body,front,door=_case(P)
    _works(P)
    P.gates=[]
    P.root["sleeve_end_x_mm"]=-1.4
    P.root["mouth_relief_floor_x_mm"]=-.64
    P.root["sleeve_to_relief_floor_mm"]=.76
    P.root["press_target_gap_mm"]=.023
    P.root["roll_center_distance_mm"]=20.
    P.root["belt_loop_mm"]=LOOP
    P.root["stamp_count"]=12
    P.root["guide_clear_at_open_mm"]=4.0
    root=P.done()
    key_visible(root,False)
    return root



def _link_motion(root):
    rig=D.rig(root)
    links={"crank_to_latch":("crank",(-25.7,-1.55,0),"latch",(-42,-1.55,0)),
           "latch_to_arm":("latch",(-53.4,-1.76,0),"arm",(-54,-1.76,0))}
    bpy.context.view_layer.update()
    for ob in root.children:
        tag=ob.get("drive_link")
        if not tag:
            continue
        ka,pa,kb,pb=links[tag]
        def point(k,p):
            j=rig[k]
            return j.matrix_parent_inverse @ j.matrix_basis @ j.matrix_parent_inverse.inverted() @ D._mm(p)
        a,b=point(ka,pa),point(kb,pb)
        rest=math.dist(pa,pb)*D.MM
        ob.location=(a+b)/2
        ob.rotation_euler=(b-a).to_track_quat("Z","Y").to_euler()
        ob.scale.z=(b-a).length/rest


def pose_h01(root, role, value):
    rig=D.rig(root)
    if role=="strip":
        value=max(0.,min(40.,value))
        paper_pose(rig[role],value)
        rig[role]["pose_value"]=value
        return value
    value=D.pose(root,role,value)
    if role in ("crank","arm","latch"):
        _link_motion(root)
    if role in ("plug","key"):
        key=rig["key"]
        # 钥匙随锁芯转，但插入轴仍保持直线。
        target=next(o for o in key.children if o.type=="EMPTY")
        if "rest_matrix" not in target:
            target["rest_matrix"]=[n for r in target.matrix_basis for n in r]
        t=list(target["rest_matrix"])
        rest=Matrix([t[i:i+4] for i in (0,4,8,12)])
        theta=rig["plug"].rotation_euler.x
        target.matrix_basis=Matrix.Rotation(theta,4,"X")@rest
    return value


def key_visible(root, visible):
    key=D.rig(root)["key"]
    for o in key.children_recursive:
        if not o.hide_viewport:
            o.hide_render=not visible



def h06_pin_lock(K,preset="own",cut=True):
    if preset not in D._LOCK_PRESETS:
        raise ValueError(preset)
    P=D.Part(K,"h06_pin_lock","blue")
    body,shackle=D._lock_case(P,cut)
    w,u=Vector((0,-1,0)),Vector(Z)
    q=lambda a,b,c=0: Vector((c,-1.5-a,-.55+b))
    s=1.3
    rad=2.3*s
    # 8 mm 锁体保留，座孔 Ø9.30 容纳 Ø9.10 外套；外套内径
    # Ø8.20，内端两道轴承把 Ø5.98 的转子定位，不能靠悬空定位。
    D._boolean(body,D._cyl(P,q(2.5,0),w,4.65,9.0,K.blue,0))
    sleeve=_tube(P,"sleeve_9p10_ID8p20",q(2.6,0),w,4.55,4.10,7.8,K.white)
    if cut:
        win=P.box(12,-12,12,12,24,K.white,r=0,bevel=0)
        D._boolean(sleeve,win)
    for a in (-1.0,6.21):
        _tube(P,"sleeve_centering_bearing",q(a,0),w,4.14,rad+.045,.46,K.white)
    plug=D._move(P,"plug","rot",(0,90),pivot=q(0,0),axis=w)
    core=D._cyl(P,q(2.6,0),w,rad,7.8,K.gold_satin,.16)
    core.name=P.nm("turning_core")
    D._boolean(core,D._local_box(P,q(3.31,.2*s),w,u,3.37,1.5*s,.5*s*2,K.white,0))
    D._adopt(plug,core)
    for i,length in enumerate(D._LOCK_PRESETS[preset]):
        a=(i+.5)*s
        delta=length-D._LOCK_PRESETS["own"][i]
        # 中心剪切线 +2.99 mm；上下销之间留 0.06 mm 可动间隙。
        hi0=rad+.037+delta
        lo0=rad-.019+delta
        D._boolean(core,D._cyl(P,q(a,rad-.74),u,.502*s,2.06*s,K.white,0))
        D._adopt(plug,core.modifiers[0].object)
        D._boolean(sleeve,D._cyl(P,q(a,4.4),u,.502*s,1.8,K.white,0))
        D._boolean(body,D._cyl(P,q(a,3.4),u,.701,8.7,K.blue,0))
        bridge=_tube(P,f"upper_fixed_guide_{i}",q(a,4.55),u,.76,.655,3.06,K.white)
        # Guide lower face is rad + .03, outside the turning core.
        bridge.location.z+=.012*D.MM
        if cut:
            D._boolean(bridge,_box(P,"guide_check_window",q(a,4.65,.68),.44,.43,2.92,K.white,0,0))
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
        _tube(P,"shackle_guide",(-5.75,0,3.87),Z,1.20,1.025,.29,K.blue)
    rail=D._move(P,"shackle","loc",(0,4),pivot=(-5.75,0,-.8),axis=Z)
    D._adopt(rail,shackle)
    P.root["preset"]=preset
    P.root["lower_pins_mm"]=D._LOCK_PRESETS[preset]
    P.root["sleeve_id_mm"]=8.2
    P.root["seat_clearance_mm"]=.2
    P.root["shear_line_mm"]=rad
    P.gate(-10,3,"-x")
    P.gate(10,3,"+x")
    return P.done()


def _add_to(root,K):
    P=D.Part(K,root.name,"white")
    bpy.data.objects.remove(P.root,do_unlink=True)
    P.root=root
    return P


def h03_loop_track(K,lod="hero"):
    root=D.h03_loop_track(K,lod)
    if lod=="mini":
        return root
    P=_add_to(root,K)
    order=[]
    for k in range(8):
        for sid in range(4):
            for label in ("coin","clock"):
                order.append(f"{label}_s{sid}_{k}")
    root["token_order"]=json.dumps(order)
    for x,y in ((9,-3.5),(-9,-3.5),(-9,3.5),(9,3.5)):
        sign=1 if y>0 else -1
        for offset,title in ((-3.13,"COST"),(3.13,"TIME")):
            px,py=x+offset,y+sign*2.17
            _box(P,f"plate_{title}",(px,py,2.43),3,1.5,.86,K.blue,.25,.12)
            caption=D._label(P,title,1.70,px+math.copysign(.44,offset),py+sign*.25,2.865,K.inkw)
            if sign>0:
                caption.rotation_euler.z=math.pi
    return root


def pose_tokens(root, value):
    """把 64 枚代币分成互不重叠的时间窗，0 = 等待，1 = 全部落位。"""
    order=json.loads(root["token_order"])
    frame=max(0.,min(1.,value))*len(order)
    roles=D.rig(root)
    for i,role in enumerate(order):
        fraction=max(0.,min(1.,frame-i))
        fraction=fraction*fraction*(3-2*fraction)
        joint=roles[role]
        joint.location.z=6*(1-fraction)*D.MM
        joint["pose_value"]=6*(1-fraction)


def h04_chem42_chip(K,screen_seq=None):
    root=D.h04_chem42_chip(K,screen_seq)
    P=_add_to(root,K)
    scale=.109
    index=0
    zfloor=.601
    xfirst=-14
    for i in range(6):
        y=(i-2.5)*3.4
        for c in range(6):
            if i in (2,3) and c in (2,3):
                continue
            x=xfirst+c*5.6
            plate=_box(P,f"loop_{index}_foot",(x,y,zfloor+scale),
                       25*scale,15*scale,2*scale,K.white,3*scale,.28*scale)
            start=set(root.children)
            D._oval(P,scale)
            guide=next(o for o in root.children if o not in start)
            guide.location=D._mm((x,y,zfloor))
            guide.name=P.nm(f"loop_{index}_track")
            path=D._ellipse_path(scale,(x,y,zfloor))
            j=D._move(P,f"loop_{index}__car","path",(0,1),path=path)
            j.matrix_parent_inverse=D._path_frame(path,0.)
            for o in D._trolley(P,scale):
                o.parent=j
            index+=1
        side=1 if y>0 else -1
        # 回流管绕网格 −X 侧的走线沟，按行进首轨；跨轨部分抬至车顶以上。
        # 六支管分别进出中央插座，端点不悬在空中。
        xman=-17.69+.34*abs(i-2.5)
        branch_y=side*(.68+.76*(i%3))
        zpipe=1.73+.56*(i%3)
        q=[(-2.94,branch_y,zpipe),(-3.35,branch_y,zpipe),
           (xman+.17,branch_y,zpipe),(xman,branch_y+side*.17,zpipe),
           (xman,y,zpipe),(-16.76,y,zpipe),(-16.71,y,.91)]
        pipe=P.tube(q,.25,K.clear0)
        pipe.name=P.nm(f"reflow_row_{i}")
        pipe.data.bevel_resolution=2
    del root["preview_status"]
    root["loop_scale"]=scale
    root["track_count"]=index
    return root



def _lower_carrier(P,rotor,upper,mesh,pivot,axis):
    carrier=D._empty(upper["role"]+"_rotor_slider",rotor)
    ref=Matrix.Translation(D._mm(pivot))@axis.to_track_quat("Z","Y").to_matrix().to_4x4()
    carrier.matrix_parent_inverse=rotor.matrix_parent_inverse.inverted()@ref
    for ob in [mesh]+[m.object for m in mesh.modifiers if m.type=="BOOLEAN"]:
        ob.parent=carrier
        ob.matrix_parent_inverse=ref.inverted()
    driver=carrier.driver_add("location",2).driver
    driver.type="AVERAGE"
    variable=driver.variables.new()
    variable.type="SINGLE_PROP"
    variable.targets[0].id=upper
    variable.targets[0].data_path="location.z"



h02_key=D.h02_key
rig=D.rig


def pose(root,role,value):
    if "shell_scale" in root:
        return pose_h01(root,role,value)
    return D.pose(root,role,value)


def rest(root):
    for role,desc in json.loads(root["rig"]).items():
        pose(root,role,desc["rest"])
