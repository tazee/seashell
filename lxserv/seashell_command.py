#python

'''

    Modeling command plugin to make seashell mesh polygons from
    a source profile polygon using Python script.

'''

import lx
import lxifc
import lxu.command
import lxu.select
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


class Seashell_Cmd(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
    
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

        '''
            Get UV texture name from selection packet if UV texture map is
            selected, otherwise we use a default texture name.
        '''
        sel_svc = lx.service.Selection()
        selTypeCode = sel_svc.LookupType(lx.symbol.sSELTYP_VERTEXMAP)
        transPacket = lx.object.VMapPacketTranslation(sel_svc.Allocate(lx.symbol.sSELTYP_VERTEXMAP))
        for i in range(sel_svc.Count(selTypeCode)):
            packet = sel_svc.ByIndex(selTypeCode, i)
            if transPacket.Type (packet) == lx.symbol.i_VMAP_TEXTUREUV:
                seashell.Settings.name = transPacket.Name(packet)
                break

    def cmd_DialogInit (self):
        if not self.dyna_IsSet (ATTR_AXIS.index):
            self.attr_SetInt (ATTR_AXIS.index, seashell.Settings.axis)
        if not self.dyna_IsSet (ATTR_NREP.index):
            self.attr_SetInt (ATTR_NREP.index, seashell.Settings.nrep)
        if not self.dyna_IsSet (ATTR_NSID.index):
            self.attr_SetInt (ATTR_NSID.index, seashell.Settings.nsid)
        if not self.dyna_IsSet (ATTR_OFF.index):
            self.attr_SetInt (ATTR_OFF.index, seashell.Settings.off)
        if not self.dyna_IsSet (ATTR_SCL.index):
            self.attr_SetFlt (ATTR_SCL.index, seashell.Settings.scl)
        if not self.dyna_IsSet (ATTR_TXUV.index):
            self.attr_SetInt (ATTR_TXUV.index, seashell.Settings.uvs)
        if not self.dyna_IsSet (ATTR_UWRP.index):
            self.attr_SetFlt (ATTR_UWRP.index, seashell.Settings.uwrp)
        if not self.dyna_IsSet (ATTR_VWRP.index):
            self.attr_SetFlt (ATTR_VWRP.index, seashell.Settings.vwrp)
        if not self.dyna_IsSet (ATTR_VROT.index):
            self.attr_SetInt (ATTR_VROT.index, seashell.Settings.vrot)
        if not self.dyna_IsSet (ATTR_NAME.index):
            self.attr_SetString (ATTR_NAME.index, seashell.Settings.name)

    def cmd_Flags(self):
        return lx.symbol.fCMD_MODEL | lx.symbol.fCMD_UNDO

    def basic_Enable(self, msg):
        item_sel = lxu.select.ItemSelection()
        for i in range(0, len(item_sel.current())):
            item_loc = lx.object.Item(item_sel.current()[i])

            if item_loc.test() == False:
                continue

            scn_svc = lx.service.Scene()
            mesh_type = scn_svc.ItemTypeLookup(lx.symbol.sITYPE_MESH)
            if item_loc.TestType(mesh_type):
                return True

        return False

    def arg_UIHints(self, index, hints):
        if index == ATTR_NREP.index or index == ATTR_NSID.index or index == ATTR_OFF.index:
            hints.MinInt(1) 

    def cmd_ArgEnable(self, index):
        if index == ATTR_UWRP.index or index == ATTR_VWRP.index or index == ATTR_VROT.index or index == ATTR_NAME.index:
            uvs = self.attr_GetInt(ATTR_TXUV.index)
            if uvs == False:
                lx.throw (lx.symbol.e_CMD_DISABLED)
                return False
        return True

    def basic_Execute(self, msg, flags):
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

'''
    "Blessing" the class promotes it to a fist class server. This basically
    means that modo will now recognize this plugin script as a command plugin.
'''
lx.bless(Seashell_Cmd, "seashell.command")