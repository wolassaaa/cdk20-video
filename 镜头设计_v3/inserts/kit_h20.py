"""HKBU SCIE1007 课程作业的科普视频：W1/W5 套件盒盖（mm，默认检查图只用空白名牌）。"""
import json
import math

import bpy
from mathutils import Vector
import kit_deep as D
import kit_parts as KP
from kit_deep_r2 import _box, _tube

WIDTH, LENGTH, HEIGHT = 986., 332., 64.
TOP = HEIGHT
TITLES=("Four a day","Our question","The lock","AI helps cut a key",
        "In the lab","How much did computers help?","What next?","The answer")
PEOPLE=((), ("A","C"), ("D","B"), ("B","A"), ("C",), ("D","B"), ("A",), ("C",))


def _cut(obj, tool):
    return D._boolean(obj,tool)


def _rect(P,name,x,y,w,h,z,t,m,r=2,bevel=.2):
    return _box(P,name,(x,y,z),w/2,h/2,t,m,r,bevel)


def _frame(P,name,x,y,w,h,r,line,z,depth,mat):
    # 同一截面生成真槽刀具或凸唇，不用表面画线替代。
    ext=KP.rrect(x,y,w/2,h/2,r)
    inner=KP.rrect(x,y,w/2-line,h/2-line,max(r-line,.1))
    n=len(ext)
    pts=[(a,b,c) for c in (z-depth/2,z+depth/2) for a,b in ext+inner]
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces += [(j,i,2*n+i,2*n+j),(n+i,n+j,3*n+j,3*n+i),
                  (i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j)]
    return D._mesh(P,name,pts,faces,mat)


def _text(P,body,height,x,y,z,mat,*,italic=False,align="LEFT",relief=.3,bevel=0):
    ob=P.text("H",height,x,y,z,mat,italic=italic,align=align)
    cu=ob.data
    cu.align_y="BASELINE"
    cu.extrude=cu.bevel_depth=0.
    bpy.context.view_layer.update()
    cap=ob.dimensions.y
    if cap>0:
        cu.size*=height*D.MM/cap
    cu.body=body
    cu.resolution_u=6
    cu.extrude=(relief/2-min(bevel,relief/3))*D.MM
    cu.bevel_depth=min(bevel,relief/3)*D.MM
    cu.bevel_resolution=1
    ob.location.z=(z+relief/2-.008)*D.MM
    bpy.context.view_layer.update()
    return ob


def _width(ob):
    bpy.context.view_layer.update()
    return ob.dimensions.x/D.MM


def _fit(ob, height, width, minimum, label):
    factor=min(1.,width/max(_width(ob),1e-4))
    target=max(minimum,height*factor)
    ob.data.size*=target/height
    if target>height*factor+1e-4:
        raise ValueError(f"h20: {label} exceeds width at {minimum:.1f} mm")
    return target


def _shell(P):
    K=P.K
    shell=_rect(P,"shell",0,0,WIDTH,LENGTH,32,64,K.white,6,.6)
    # 2.5 mm 壁与顶板。腔口略外放 0.1 mm，留出实际内腔宽度。
    _cut(shell,_rect(P,"negative_cavity",0,0,980.8,326.8,30.25,62.5,K.white,3.4,.0))
    _cut(shell,_frame(P,"side_seam",0,0,987,333,6.5,.65,58,.15,K.white))
    _cut(shell,_frame(P,"top_trim_groove",0,0,962,308,5,.6,64,.40,K.white))
    _cut(shell,_rect(P,"badge_socket",-399,130,129,41,64.4,2.,K.white,4.4,.06))
    _cut(shell,_rect(P,"illustration_tray",296.5,35,333,130,64.4,3.2,K.white,5,.12))
    _cut(shell,_frame(P,"illustration_groove",296.5,35,330,127,4,.6,62.8,.4,K.white))
    for x in (-430,-145,145,430):
        for y in (-127,127):
            _cut(shell,P.cyl(x,y,61.49,.4,.42,K.white,bevel=0))
    for x in (-471,471):
        _cut(shell,P.cyl(x,-143,64,.4,.40,K.white,bevel=0))
    # 加强肋在凹进的侧面浅槽里，肋高 0.8 但不突破盒盖外形限界。
    for sign in (-1,1):
        for x in (-373,373):
            y=sign*166
            _cut(shell,_rect(P,"long_rib_recess",x,y,7,1.8,32,43,K.white,.2,0))
            _rect(P,"long_side_rib",x,y-sign*.53,3,.82,32,40,K.white,.26,.14)
        for y in (-46,46):
            x=sign*493
            _cut(shell,_rect(P,"short_rib_recess",x,y,1.8,7,32,43,K.white,.2,0))
            _rect(P,"short_side_rib",x-sign*.53,y,.82,3,32,40,K.white,.26,.14)
    side=_text(P,"SCIE1007 · Section 20007 · Group 3B",7,0,0,0,K.ink,align="CENTER")
    side.location=D._mm((0,-166.085,27))
    side.rotation_euler.x=math.pi/2
    return shell


def _label_rig(P,role,value):
    if role=="art":
        return D._move(P,value,"loc",(0,3),axis=D.Z if hasattr(D,"Z") else (0,0,1))
    return D._move(P,value,"rot",(-90,0),pivot=role,axis=(1,0,0))


def _top(P):
    K=P.K
    badge=D._move(P,"badge","loc",(0,12))
    D._adopt(badge,_rect(P,"course_badge",-399,130,128,40,64.2,1.6,K.red,4,.4),
             _text(P,"SCIE1007",18,-399,123,65.,K.inkw,align="CENTER"))
    _text(P,"Molecular Science in Daily Life",16,-320,122,TOP,K.ink,italic=True)
    title=_text(P,"WORTH TESTING",48,-463,48,TOP,K.ink,relief=1.,bevel=.2)
    bpy.context.view_layer.update()
    title_end=max((title.matrix_world@Vector(v)).x for v in title.bound_box)/D.MM
    q=D._move(P,"qmark","loc",(0,10))
    question=_text(P,"?",48,title_end+6,48,TOP,K.red,relief=1.)
    D._adopt(q,question)
    bpy.context.view_layer.update()
    end=max((question.matrix_world@Vector(v)).x for v in question.bound_box)/D.MM
    line=D._empty("h20__rule",P.root)
    line["role"]="rule"
    D._place(line,(-463,36,64))
    D._adopt(line,_rect(P,"red_rule",(-463+end)/2,36,end+463,1.4,64.19,.40,K.red,.65,.12))
    spec=json.loads(P.root["rig"])
    spec["rule"]=dict(type="scale",axis="X",min=0,max=1,rest=1,unit="ratio")
    P.root["rig"]=json.dumps(spec)
    subtitle=_text(P,"How computers help find cancer drug candidates: the CDK20 story",
                   16,-463,10,TOP,K.ink,italic=True)
    if _width(subtitle)>600:
        # 保留最小字高，轻微调窄字面而不是截断原文。
        subtitle.data.size*=14/16
        if _width(subtitle)>600:
            subtitle.scale.x=600/_width(subtitle)
        P.root["subtitle_cap_mm"]=14.
        P.root["subtitle_width_scale"]=subtitle.scale.x
    else:
        P.root["subtitle_cap_mm"]=16.
    _text(P,"Inside this kit · who presents each part",9,-463,-44,TOP,K.ink,italic=True)


def _illustrations(P):
    K=P.K
    factories=(KP.p04_liver,KP.p19_cdk20,lambda k:KP.p22_key(k,48))
    for i,factory in enumerate(factories):
        joint=D._move(P,f"art_{i}","loc",(0,3))
        part=factory(K)
        if "span" in part:
            del part["span"]
        cell=KP.make_cell(K,part,296.5+(i-1)*66*1.6,35,65.2,name=f"box_art_{i}")
        cell.scale=(1.6,)*3
        D._adopt(joint,cell)
        # 轮廓保持原比例，只对超面数的盒绘网格做无纹理拓扑简化。
        for obj in part.children:
            if obj.type=="MESH" and not obj.hide_render and len(obj.data.polygons)>12000:
                lod=obj.modifiers.new("box illustration mesh budget","DECIMATE")
                lod.ratio=min(.98,12000/len(obj.data.polygons))


def _rear_detail(P,plate,x,y,n,w,h):
    K=P.K
    for offset in (-w*.28,w*.28):
        _cut(plate,_rect(P,"recessed_rib_bed",x+offset,y,2.6,h*.72,64.22,.88,K.white,.4,0))
    for offset in (-w*.32,w*.32):
        _cut(plate,P.cyl(x+offset,y+8,64.21,.4,.42,K.white,bevel=0))
    reverse=_text(P,f"No. {n}",3,x,0,0,K.inkg,align="CENTER",relief=.12)
    reverse.rotation_euler.x=math.pi
    reverse.location=D._mm((x,y+4,64.14))
    return [_rect(P,"rear_recess_rib",x+offset,y,.8,h*.70,64.47,.4,K.white,.22,.12)
            for offset in (-w*.28,w*.28)]+[reverse]


def _tags(P,names):
    K=P.K
    runner=D._cyl(P,(0,-58,64),(1,0,0),3,920,K.white,.07)
    runner.name=P.nm("sprue_runner_relief")
    runner.pass_index=20
    for x in (-460,460):
        cap=P.ball(x,-58,64,3,K.white,seg=32)
        cap.pass_index=20
    for k,title in enumerate(TITLES):
        x,y=-399+114*k,-95.5
        j=D._move(P,f"tag_{k}","rot",(-90,0),pivot=(x,-63.5,65),axis=(1,0,0))
        plate=_rect(P,"chapter_plate",x,y,104,64,65,1.6,K.white,3,.4)
        lip=_frame(P,"chapter_plate_lip",x,y,103.4,63.4,2.68,.8,65.98,.42,K.white)
        num=_text(P,str(k+1),12,x-44,y+14,65.8,K.ink)
        label=_text(P,title,6.5,x-30,y+18,65.8,K.ink)
        if _width(label)>78:
            words=title.split()
            for n in range(len(words)-1,0,-1):
                label.data.body=" ".join(words[:n])
                if _width(label)<=78:
                    break
            second=_text(P," ".join(words[n:]),6.5,x-30,y+8,65.8,K.ink)
            D._adopt(j,second)
        sep=_rect(P,"chapter_divider",x,y+2,92,.4,65.90,.20,K.inkg,.12,.04)
        for line in range(max(1,len(PEOPLE[k]))):
            yy=y-10-12*line
            if names and PEOPLE[k]:
                letter=PEOPLE[k][line]
                tx=_text(P,names[letter],6,x-46,yy-2,65.8,K.ink,italic=True)
                _fit(tx,6,92,5.2,f"plate {k+1} / member {letter}")
                D._adopt(j,tx)
            else:
                D._adopt(j,_rect(P,"blank_name_plate",x,yy,92,8,65.91,.22,K.white,1.5,.08))
        # 在可动牌一侧保留浇口锥；轴心偏上方使它倒起时不扫进顶板。
        bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=.8*D.MM,radius2=.4*D.MM,
                                       depth=2.5*D.MM,location=D._mm((x,-62.15,67.04)))
        sprue=bpy.context.object
        sprue.name=P.nm("trimmed_sprue_hinge")
        sprue.rotation_euler.x=math.pi/2
        sprue.data.materials.append(K.white)
        D._adopt(j,plate,lip,num,label,sep,sprue,*_rear_detail(P,plate,x,y,k+1,104,64))
    j=D._move(P,"sec_plate","rot",(-90,0),pivot=(338,150,65),axis=(1,0,0))
    plate=_rect(P,"section_plate",338,133,250,34,65,1.6,K.black,3,.4)
    tx=_text(P,"Section 20007 · Group 3B",16,338,127,65.8,K.inkw,align="CENTER")
    for off in (-1,0,1):
        y=133+5*off
        _cut(plate,_rect(P,"section_recess",338,y,225,2.4,64.19,.86,K.black,.4,0))
        D._adopt(j,_rect(P,"section_back_rib",338,y,221,.8,64.46,.4,K.black,.3,.10))
    for x in (232,444):
        _cut(plate,P.cyl(x,141,64.21,.4,.42,K.black,bevel=0))
        D._cyl(P,(x,150.6,64.48),(0,0,1),.8,.96,K.white,.09)
    D._adopt(j,plate,tx)


def h20_kit_box(K,names=None,draft=False):
    if not draft and (not names or any(not names.get(key) for key in "ABCD")):
        raise ValueError("h20: names required for final render")
    # 本轮检查素材不读外部姓名；调用方之后可在本地提供四个名字。
    names=None if draft else names
    P=D.Part(K,"h20_kit_box","white")
    lift=D._move(P,"lid_lift","loc",(0,80))
    hinge=D._move(P,"lid_hinge","rot",(0,104),pivot=(0,166,0),axis=(-1,0,0))
    _shell(P)
    _top(P)
    _illustrations(P)
    _tags(P,names)
    for ob in tuple(P.root.children):
        if ob not in {lift,hinge}:
            # 保留其它角色的局部轴；_adopt 会覆盖其枢轴，故逐物体组合父逆矩阵。
            ob.parent=hinge
            ob.matrix_parent_inverse=hinge.matrix_parent_inverse.inverted()@ob.matrix_parent_inverse
    hinge.parent=lift
    return P.done()


def rig(root):
    return {ob["role"]:ob for ob in root.children_recursive if ob.get("role")}


def pose(root,role,value):
    cfg=json.loads(root["rig"])[role]
    j=rig(root)[role]
    value=max(cfg["min"],min(cfg["max"],value))
    if cfg["type"]=="rot":
        j.rotation_euler.x=math.radians(value)
    elif cfg["type"]=="loc":
        j.location.z=value*D.MM
    else:
        j.scale.x=value
    j["pose_value"]=value
    return value


def rest(root):
    for role,spec in json.loads(root["rig"]).items():
        pose(root,role,spec["rest"])
