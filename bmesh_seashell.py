'''
    Blender Edit-mode operator to make seashell mesh polygons from
    a source profile polygon using Python script.
'''

import math
import bpy
import bmesh

from bpy.props import BoolProperty, FloatProperty, EnumProperty, IntProperty, StringProperty

bl_info = {
    "name": "SeaShell",
    "author": "Yoshiaki Tazaki",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "description": "Make seashell mesh polygons from a source profile polygon.",
    "doc_url": "",
    "tracker_url": "",
    "category": "Mesh"
}


class MESH_OT_SeaShell(bpy.types.Operator):
    """Make seashell shape"""
    bl_idname = "mesh.seashell"
    bl_label = "SeaShell"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(
        name="Axis",
        description="Axis",
        default='Z',
        items=[
            ('X', "X", "X-Axis"),
            ('Y', "Y", "Y-Axis"),
            ('Z', "Z", "Z-Axis")
        ]
    )
    nrep: IntProperty(
        name="N of Loops",
        description="N of Loops",
        min=1,
        default=4,
    )
    sides: IntProperty(
        name="Sides per Loop",
        description="Sides per Loop",
        min=1,
        default=20,
    )
    offset: FloatProperty(
        name="Offset",
        description="Offset",
        min=1.0,
        default=1.0,
    )
    scale: FloatProperty(
        name="Scale",
        description="Scale",
        min=0.0,
        default=0.6,
    )
    uvs: BoolProperty(
        name="Make UVs",
        description="Make UVs",
        default=True,
    )
    uwrp: FloatProperty(
        name="U Wrap Amount",
        description="U wrap amount.",
        min=0.0,
        default=0.2,
    )
    vwrp: FloatProperty(
        name="V Wrap Amount",
        description="V wrap amount.",
        min=0.0,
        default=1.0,
    )
    vrot: BoolProperty(
        name="Rotate V Wrap",
        description="Rotate V wrap.",
        default=False,
    )
    uv_map_name: StringProperty(
        name="Texture",
        description="Texture UV name.",
        default='UVMap',
    )

    def SeaShell_Build(self, bm, face):
        front_p = []
        verts = []
        for v in face.verts:
            front_p.append(v)
            verts.append(v.co)

        if self.scale < 1.0e-6:
            scl = 1.0e-6
        else:
            scl = self.scale
        n   = self.sides * self.nrep
        rot = math.pi / self.sides
        cen = self.offset / scl
        scl = math.pow(scl, 1.0 / self.sides)
        sc  = 1.0
        rt  = 0.0

        back_p = []

        usiz = n * self.uwrp

        nvert = len(face.verts)

        quads = []

        # print("SeaShell_Build: n {} nvert {} face {} select {}".format(n,nvert,face.index,face.select))
        for i in range(n):
            sc *= scl
            rt += rot

            '''
                Make new vertices on the current slice.
            '''
            for sco in verts:
                x, y, z = TransPoint(self.axis, rt, sc, cen, sco)
                newID = bm.verts.new((x, y, z))
                back_p.append(newID)

            for k in range(nvert):
                '''
                    Make new quadrangles around the current slice.
                '''
                l = (k + 1) % nvert
                v1 = front_p[l]
                v2 = front_p[k]
                v3 = back_p[k]
                v4 = back_p[l]

                try:
                    quad = bm.faces.new([v1, v2, v3, v4])
                    quads.append(quad)
                except ValueError:
                    print("A face with these vertices already exists.")
        
            front_p = back_p[:]
            back_p = []

        '''
            Make UVs to the quadrangles when UV option is enabled.
        '''
        if self.uvs:
            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()
            iterator = iter(quads)
            for i in range(n):
                for k in range(nvert):
                    quad = next(iterator)
                    for iv, loop in enumerate(quad.loops):
                        match iv:
                            case 0:
                                u = (1.0 - i / n) * usiz
                                v = 1.0 - k / nvert * self.vwrp
                                loop[uv_layer].uv = (u, v)
                            case 1:
                                u = (1.0 - i / n) * usiz
                                v = 1.0 - (k + 1) / nvert * self.vwrp
                                loop[uv_layer].uv = (u, v)
                            case 3:
                                u = (1.0 - (i + 1) / n) * usiz
                                v = 1.0 - k / nvert * self.vwrp
                                loop[uv_layer].uv = (u, v)
                            case 2:
                                u = (1.0 - (i + 1) / n) * usiz
                                v = 1.0 - (k + 1) / nvert * self.vwrp
                                loop[uv_layer].uv = (u, v)
        


    def execute(self, context):
        mesh = context.object.data

        # Ensure we are in Edit Mode
        if context.mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')

        # Get a BMesh representation
        bm = bmesh.from_edit_mesh(mesh)

        # Make new UV map if there is no UV map with the given name
        if self.uvs:
            if self.uv_map_name not in mesh.uv_layers:
                mesh.uv_layers.new(name=self.uv_map_name)
    
        mesh.uv_layers.active = mesh.uv_layers[self.uv_map_name]
    
        selected = [face for face in bm.faces if face.select]
        #print("Edit Mesh faces {} selected {} uv_map_name {}".format(len(bm.faces), len(selected), self.uv_map_name))
    
        '''
            Operate all faces if nothing is selected. Otherwise, operate selected faces.
        '''
        if len(selected) == 0:
            for face in bm.faces[:]:
                self.SeaShell_Build(bm, face)
        else:
            for face in selected[:]:
                self.SeaShell_Build(bm, face)

        bm.normal_update()
        bmesh.update_edit_mesh(mesh)

        return {'FINISHED'}

'''
    Point translation function.
'''  
def TransPoint(axis, rot, scal, cen, sco):
    if axis == 'X':
        x = (sco[0] - cen) * scal + cen
        y = (sco[0] * scal * math.cos(rot) - sco[2] * scal * math.sin(rot))
        z = sco[1] * scal * math.sin(rot) + sco[2] * scal * math.cos(rot)
        return x, y, z
    elif axis == 'Y':
        x = sco[0] * scal * math.cos(rot) - sco[2] * scal * math.sin(rot)
        y = (sco[1] - cen) * scal + cen
        z = (sco[0] * scal * math.sin(rot) + sco[2] * scal * math.cos(rot))
        return x, y, z
    elif axis == 'Z':
        x = (sco[0] * scal * math.cos(rot) - sco[1] * scal * math.sin(rot))
        y = sco[0] * scal * math.sin(rot) + sco[1] * scal * math.cos(rot)
        z = (sco[2] - cen) * scal + cen
        return x, y, z
    else:
        return sco[0], sco[1], sco[2]

def menu_func(self, context):
    self.layout.operator(MESH_OT_SeaShell.bl_idname, icon='PLUGIN')


# Register and add to the "Face" menu in edit-mesh mode.
def register():
    bpy.utils.register_class(MESH_OT_SeaShell)
    bpy.types.VIEW3D_MT_edit_mesh_faces.append(menu_func)


def unregister():
    bpy.utils.unregister_class(MESH_OT_SeaShell)
    bpy.types.VIEW3D_MT_edit_mesh_faces.remove(menu_func)


if __name__ == "__main__":
    register()

