#python

'''

    Mesh operator plugin to make seashell mesh polygons from
    a source profile polygon using Python script.

'''

import lx
import lxifc
import lxu.attributes
import lxu.vector
from lxifc import UIValueHints, Visitor

import seashell

from collections import namedtuple
DynamicAttribute = namedtuple('DynamicAttribute', ['name', 'index'])

ATTR_AXIS = DynamicAttribute('axis',   0)
ATTR_NREP = DynamicAttribute('nrep',   1)
ATTR_NSID = DynamicAttribute('sides',  2)
ATTR_OFF  = DynamicAttribute('offset', 3)
ATTR_SCL  = DynamicAttribute('scale',  4)
ATTR_TXUV = DynamicAttribute('uvs',    5)
ATTR_UWRP = DynamicAttribute('uwrap',  6)
ATTR_VWRP = DynamicAttribute('vwrap',  7)
ATTR_VROT = DynamicAttribute('vrot',   8)
ATTR_NAME = DynamicAttribute('name',   9)

class Seashell_MeshOp(lxifc.MeshOperation, lxu.attributes.DynamicAttributes):
    def __init__(self):
        lxu.attributes.DynamicAttributes.__init__(self)
    
        self.dyna_Add(ATTR_AXIS.name, lx.symbol.sTYPE_AXIS)
        self.dyna_Add(ATTR_NREP.name, lx.symbol.sTYPE_INTEGER)
        self.dyna_Add(ATTR_NSID.name, lx.symbol.sTYPE_INTEGER)
        self.dyna_Add(ATTR_OFF.name, lx.symbol.sTYPE_DISTANCE)
        self.dyna_Add(ATTR_SCL.name, lx.symbol.sTYPE_PERCENT)
        self.dyna_Add(ATTR_TXUV.name, lx.symbol.sTYPE_BOOLEAN)
        self.dyna_Add(ATTR_UWRP.name, lx.symbol.sTYPE_FLOAT)
        self.dyna_Add(ATTR_VWRP.name, lx.symbol.sTYPE_FLOAT)
        self.dyna_Add(ATTR_VROT.name, lx.symbol.sTYPE_BOOLEAN)
        self.dyna_Add(ATTR_NAME.name, lx.symbol.sTYPE_STRING)
    
        self.attr_SetInt (ATTR_AXIS.index, seashell.Settings.axis)
        self.attr_SetInt (ATTR_NREP.index, seashell.Settings.nrep)
        self.attr_SetInt (ATTR_NSID.index, seashell.Settings.nsid)
        self.attr_SetFlt (ATTR_OFF.index, seashell.Settings.off)
        self.attr_SetFlt (ATTR_SCL.index, seashell.Settings.scl)
        self.attr_SetInt (ATTR_TXUV.index, seashell.Settings.uvs)
        self.attr_SetFlt (ATTR_UWRP.index, seashell.Settings.uwrp)
        self.attr_SetFlt (ATTR_VWRP.index, seashell.Settings.vwrp)
        self.attr_SetInt (ATTR_VROT.index, seashell.Settings.vrot)
        self.attr_SetString (ATTR_NAME.index, seashell.Settings.name)
         

    def mop_Evaluate(self, mesh_obj, type, mode):
        '''
            Get all attributes
        '''
        seashell.Settings.axis = self.attr_GetInt(ATTR_AXIS.index)
        seashell.Settings.nrep = self.attr_GetInt(ATTR_NREP.index)
        seashell.Settings.nsid = self.attr_GetInt(ATTR_NSID.index)
        seashell.Settings.off = self.attr_GetFlt(ATTR_OFF.index)
        seashell.Settings.scl = self.attr_GetFlt(ATTR_SCL.index)
        seashell.Settings.uvs = self.attr_GetInt(ATTR_TXUV.index)
        seashell.Settings.uwrp = self.attr_GetFlt(ATTR_UWRP.index)
        seashell.Settings.vwrp = self.attr_GetFlt(ATTR_VWRP.index)
        seashell.Settings.vrot = self.attr_GetInt(ATTR_VROT.index)
        seashell.Settings.name = self.attr_GetString(ATTR_NAME.index)

        mesh_svc = lx.service.Mesh()
        mesh_loc = lx.object.Mesh (mesh_obj)

        if mesh_loc.PolygonCount() == 0:
            return

        map = None
        if seashell.Settings.uvs:
            vmap_loc = lx.object.MeshMap(mesh_loc.MeshMapAccessor())
            map = vmap_loc.New(lx.symbol.i_VMAP_TEXTUREUV, seashell.Settings.name)

        polygon_loc = lx.object.Polygon(mesh_loc.PolygonAccessor())
        point_loc = lx.object.Point(mesh_loc.PointAccessor())
        
        if polygon_loc.test() == False:
            return
        
        '''
            Store the shape in the foreground mesh layer as the
            profile.
        '''
        mark_mode_selected = mesh_svc.ModeCompose (lx.symbol.sMARK_SELECT, None)
        vis = seashell.PolygonVisitor (polygon_loc, point_loc, map)
        polygon_loc.Enumerate (mark_mode_selected, vis, 0)
        
        '''
            Build seashell polygons
        '''
        seashell.Build(vis)

        '''
        Before we move on to the next layer, we need to tell modo that we
        have made edits to this mesh.
        '''
        mesh_loc.SetMeshEdits (lx.symbol.f_MESHEDIT_GEOMETRY)

'''
    "Blessing" the class promotes it to a fist class server. This basically
    means that modo will now recognize this plugin script as a command plugin.
'''
tags = {lx.symbol.sMESHOP_PMODEL: "."}
lx.bless(Seashell_MeshOp, "seashell.meshop", tags)