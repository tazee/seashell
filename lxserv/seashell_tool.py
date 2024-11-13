#!python

'''

    Direct ool plugin to make seashell mesh polygons from
    a source profile polygon using Python script.

'''

import lx
import lxifc
import lxu.attributes
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

class Seashell_Tool(lxifc.Tool, lxifc.ToolModel, lxu.attributes.DynamicAttributes):

    def __init__(self):
        lxu.attributes.DynamicAttributes.__init__(self)

        self.dyna_Add(ATTR_AXIS.name, lx.symbol.sTYPE_AXIS)
        self.dyna_Add(ATTR_NREP.name, lx.symbol.sTYPE_INTEGER)
        self.dyna_Add(ATTR_NSID.name, lx.symbol.sTYPE_INTEGER)
        self.dyna_Add(ATTR_OFF.name, lx.symbol.sTYPE_INTEGER)
        self.dyna_Add(ATTR_SCL.name, lx.symbol.sTYPE_PERCENT)
        self.dyna_Add(ATTR_TXUV.name, lx.symbol.sTYPE_BOOLEAN)
        self.dyna_Add(ATTR_UWRP.name, lx.symbol.sTYPE_FLOAT)
        self.dyna_Add(ATTR_VWRP.name, lx.symbol.sTYPE_FLOAT)
        self.dyna_Add(ATTR_VROT.name, lx.symbol.sTYPE_BOOLEAN)
        self.dyna_Add(ATTR_NAME.name, lx.symbol.sTYPE_STRING)
    
        self.attr_SetInt (ATTR_AXIS.index, seashell.Settings.axis)
        self.attr_SetInt (ATTR_NREP.index, seashell.Settings.nrep)
        self.attr_SetInt (ATTR_NSID.index, seashell.Settings.nsid)
        self.attr_SetInt (ATTR_OFF.index, seashell.Settings.off)
        self.attr_SetFlt (ATTR_SCL.index, seashell.Settings.scl)
        self.attr_SetInt (ATTR_TXUV.index, seashell.Settings.uvs)
        self.attr_SetFlt (ATTR_UWRP.index, seashell.Settings.uwrp)
        self.attr_SetFlt (ATTR_VWRP.index, seashell.Settings.vwrp)
        self.attr_SetInt (ATTR_VROT.index, seashell.Settings.vrot)
        self.attr_SetString (ATTR_NAME.index, seashell.Settings.name)

        pkt_svc = lx.service.Packet()
        self.vec_type = pkt_svc.CreateVectorType(lx.symbol.sCATEGORY_TOOL)
        pkt_svc.AddPacket(self.vec_type, lx.symbol.sP_TOOL_VIEW_EVENT, lx.symbol.fVT_GET)

    def tool_Reset (self):
        self.attr_SetInt (ATTR_AXIS.index, 1)
        self.attr_SetInt (ATTR_NREP.index, 4)
        self.attr_SetInt (ATTR_NSID.index, 20)
        self.attr_SetInt (ATTR_OFF.index, 1)
        self.attr_SetFlt (ATTR_SCL.index, 0.6)
        self.attr_SetInt (ATTR_TXUV.index, True)
        self.attr_SetFlt (ATTR_UWRP.index, 0.2)
        self.attr_SetFlt (ATTR_VWRP.index, 1.0)
        self.attr_SetInt (ATTR_VROT.index, False)
        self.attr_SetString (ATTR_NAME.index, 'Texture')

    def tool_Evaluate(self,vts):
        seashell.Settings.axis = self.attr_GetInt(ATTR_AXIS.index)
        seashell.Settings.nrep = self.attr_GetInt(ATTR_NREP.index)
        seashell.Settings.nsid = self.attr_GetInt(ATTR_NSID.index)
        seashell.Settings.off = self.attr_GetInt(ATTR_OFF.index)
        seashell.Settings.scl = self.attr_GetFlt(ATTR_SCL.index)
        seashell.Settings.uvs = self.attr_GetInt(ATTR_TXUV.index)
        seashell.Settings.uwrp = self.attr_GetFlt(ATTR_UWRP.index)
        seashell.Settings.vwrp = self.attr_GetFlt(ATTR_VWRP.index)
        seashell.Settings.vrot = self.attr_GetInt(ATTR_VROT.index)
        seashell.Settings.name = self.attr_GetString(ATTR_NAME.index)

        layer_svc = lx.service.Layer()
        mesh_svc = lx.service.Mesh()

        '''
            Start the scan in edit-poly mode.
        '''
        layer_scan = lx.object.LayerScan(layer_svc.ScanAllocate(lx.symbol.f_LAYERSCAN_EDIT_POLYS))

        if layer_scan.test() == False:
            return

        for n in range(layer_scan.Count()):
            mesh_loc = lx.object.Mesh(layer_scan.MeshEdit(n))

            if mesh_loc.test() == False:
                continue

            if mesh_loc.PolygonCount() == 0:
                continue

            map = None
            if seashell.Settings.uvs:
                vmap_loc = lx.object.MeshMap(mesh_loc.MeshMapAccessor())
                map = vmap_loc.New(lx.symbol.i_VMAP_TEXTUREUV, seashell.Settings.name)

            polygon_loc = lx.object.Polygon(mesh_loc.PolygonAccessor())
            point_loc = lx.object.Point(mesh_loc.PointAccessor())

            if polygon_loc.test() == False:
                continue

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
            layer_scan.SetMeshChange(n, lx.symbol.f_MESHEDIT_GEOMETRY)

        '''
            Finally, we need to call apply on the LayerScan interface. This tells
            modo to perform all the mesh edits.
        '''
        layer_scan.Apply()

    def tool_VectorType(self):
        '''
            This function simply returns the tool VectorType that we created
            in the constructor.
        '''
        return self.vec_type

    def tool_Order(self):
        '''
            This sets the position of the tool in the toolpipe.
        '''
        return lx.symbol.s_ORD_ACTR

    def tool_Task(self):
        '''
            Simply defines the type of task performed by this tool. We set
            this to an Action tool, which basically means it will alter the
            state of modo.
        '''
        return lx.symbol.i_TASK_ACTR

    def tmod_Flags(self):
        '''
            This sets how we intend to interact with the tool. The symbol
            "fTMOD_I0_ATTRHAUL" basically says that we expect to haul an
            attribute when clicking and dragging with the left mouse button.
        '''
        return lx.symbol.fTMOD_I0_ATTRHAUL

    def tmod_Initialize(self,vts,adjust,flags):
    	pass

    def tmod_Haul(self,index):
        '''
            Hauling is dependent on the direction of the haul. So a vertical
            haul can drive a different parameter to a horizontal haul. The
            direction of the haul is represented by an index, with 0
            representing horizontal and 1 representing vertical. The function
            simply returns the name of the attribute to drive, given it's index.
            As we only have one attribute, we'll set horizontal hauling to
            control it and vertical hauling to do nothing.
        '''
        if index == 0:
            return ATTR_SCL.name
        else:
            return 0

    def TestPolygon(self):
        '''
            Start the scan in read-only mode.
        '''
        ok = False
        layer_svc = lx.service.Layer()

        layer_scan = lx.object.LayerScan(layer_svc.ScanAllocate(lx.symbol.f_LAYERSCAN_ACTIVE | lx.symbol.f_LAYERSCAN_MARKPOLYS))

        '''
            Count the polygons in all mesh layers.
        '''
        if layer_scan.test() == False:
            return ok

        for n in range(layer_scan.Count()):
            mesh_loc = lx.object.Mesh(layer_scan.MeshBase(n))

            if mesh_loc.test() == False:
                continue

            if mesh_loc.PolygonCount() > 0:
                ok = True
                break

        layer_scan.Apply()

        '''
            Return false if there is no polygons in any active layers.
        '''
        return ok

    def tmod_Enable(self, msg):
        if self.TestPolygon() == False:
            msg.SetCode(lx.symbol.e_CMD_DISABLED)
            msg.SetMessage("mesh.seashell", "NoPolygon", 0)
            return lx.symbol.e_DISABLED
        return lx.symbol.e_OK

    def arg_UIHints(self, index, hints):
        if index == ATTR_NREP.index or index == ATTR_NSID.index or index == ATTR_OFF.index:
            hints.MinInt(1)

    def arg_DisableMsg(self,index,msg):
        if index == ATTR_UWRP.index or index == ATTR_VWRP.index or index == ATTR_VROT.index or index == ATTR_NAME.index:
            uvs = self.attr_GetInt(ATTR_TXUV.index)
            if uvs == False:
                msg.SetMessage("mesh.seashell", "NeedMakeUVs", 0)
                lx.throw (lx.symbol.e_CMD_DISABLED)
                return lx.symbol.e_CMD_DISABLED
        return lx.symbol.e_OK

'''
    "Blessing" the class promotes it to a fist class server. This basically
    means that modo will now recognize this plugin script as a tool plugin.
'''
lx.bless(Seashell_Tool, "seashell.tool")