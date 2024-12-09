#python

import math
import lx
from lxifc import UIValueHints, Visitor

'''
	seashell parameters
'''
class Settings(object):
    axis = 1
    nrep = 4
    nsid = 20
    off = 1.0
    uvs = True
    uwrp = 0.2
    vwrp = 1.0
    scl = 0.6
    vrot = False
    name = 'Texture'


'''
    Store all profile polygons
'''
class PolygonVisitor (Visitor):
    def __init__ (self, polygon, vertex, map):
        self.polygon = polygon
        self.vertex = vertex;
        self.map = map
        self.faces = []
        self.verts = []
        self.front_p = []
        self.points = lx.object.storage('p', 4)
        self.uv = lx.object.storage()
        self.uv.setType('f')
        self.uv.setSize(2)
    
    def vis_Evaluate(self):
        nvert = self.polygon.VertexCount()
        for i in range(nvert):
            pointID = self.polygon.VertexByIndex(i)
            self.vertex.Select(pointID)
            self.front_p.append(pointID)
            self.verts.append(self.vertex.Pos())
        
        type = self.polygon.Type()
        self.faces.append((nvert, type, self.polygon.ID()))

'''
    Build seashell shape using given attributes
'''
def Build(vis):
    if Settings.scl < 1.0e-6:
        scl = 1.0e-6
    else:
        scl = Settings.scl
    n   = Settings.nsid * Settings.nrep
    rot = math.pi / Settings.nsid
    cen = Settings.off / scl
    scl = math.pow(Settings.scl, 1.0 / Settings.nsid)
    sc  = 1.0
    rt  = 0.0

    front_p = vis.front_p
    back_p = []

    usiz = n * Settings.uwrp

    for i in range(n):
        sc *= scl
        rt += rot
        sum = 0

        for nvert, type, id in vis.faces:
            '''
                Make new vertices on the current slice.
            '''
            for k in range(nvert):
                sco = vis.verts[sum + k]
                dco = TransPoint(Settings.axis, rt, sc, cen, sco)
                newID = vis.vertex.New(dco)
                back_p.append(newID)
            back_p.append(back_p[sum])

            for k in range(nvert):
                '''
                    Make new quadrangles around the current slice.
                '''
                l = (k + 1) % nvert
                vis.points[0] = front_p[sum + l]
                vis.points[1] = front_p[sum + k]
                vis.points[2] = back_p[sum + k]
                vis.points[3] = back_p[sum + l]
                polygonID = vis.polygon.NewProto(type,vis.points,4,0)
                '''
                    Make UVs to the quadrangles when UV option is enabled.
                '''
                if Settings.uvs:
                    vis.polygon.Select(polygonID)
                    vis.uv[0] = (1.0 - i / n) * usiz
                    vis.uv[1] = 1.0 - k / nvert * Settings.vwrp
                    vis.polygon.SetMapValue(front_p[sum + k], vis.map, vis.uv)
                    vis.uv[0] = (1.0 - i / n) * usiz
                    vis.uv[1] = 1.0 - (k + 1) / nvert * Settings.vwrp
                    vis.polygon.SetMapValue(front_p[sum + l], vis.map, vis.uv)
                    vis.uv[0] = (1.0 - (i + 1) / n) * usiz
                    vis.uv[1] = 1.0 - k / nvert * Settings.vwrp
                    vis.polygon.SetMapValue(back_p[sum + k], vis.map, vis.uv)
                    vis.uv[0] = (1.0 - (i + 1) / n) * usiz
                    vis.uv[1] = 1.0 - (k + 1) / nvert * Settings.vwrp
                    vis.polygon.SetMapValue(back_p[sum + l], vis.map, vis.uv)

            sum += nvert

        front_p = back_p
        back_p = []

'''
  Point translation function.
'''  
def TransPoint(axis, rot, scal, cen, sco):
    dco = []
    if axis == 0:
        dco.append((sco[0] - cen) * scal + cen)
        dco.append((sco[0] * scal * math.cos(rot) - sco[2] * scal * math.sin(rot)))
        dco.append(sco[1] * scal * math.sin(rot) + sco[2] * scal * math.cos(rot))
    elif axis == 1:
        dco.append(sco[0] * scal * math.cos(rot) - sco[2] * scal * math.sin(rot))
        dco.append((sco[1] - cen) * scal + cen)
        dco.append((sco[0] * scal * math.sin(rot) + sco[2] * scal * math.cos(rot)))
    elif axis == 2:
        dco.append((sco[0] * scal * math.cos(rot) - sco[1] * scal * math.sin(rot)))
        dco.append(sco[0] * scal * math.sin(rot) + sco[1] * scal * math.cos(rot))
        dco.append((sco[2] - cen) * scal + cen)
    return dco