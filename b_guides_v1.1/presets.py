"""Built-in preset support for Guides addon (Blender presets)."""

import bpy
from bl_operators.presets import AddPresetBase
from bpy.types import Menu, Operator

PRESET_VALUES = [
    "settings.show_thirds", "settings.show_golden", "settings.show_center",
    "settings.show_diagonals", "settings.show_golden_spiral", "settings.show_golden_triangle",
    "settings.show_radial_symmetry", "settings.show_vanishing_point", "settings.show_circular_thirds",
    "settings.show_diagonal_reciprocals", "settings.show_harmony_triangles", "settings.show_diagonal_method",
    "settings.show_rulers", "settings.show_grid", "settings.show_custom_guides",
    "settings.thirds_color", "settings.golden_color", "settings.center_color", "settings.diagonals_color",
    "settings.golden_spiral_color", "settings.golden_triangle_color", "settings.radial_symmetry_color",
    "settings.vanishing_point_color", "settings.circular_thirds_color", "settings.diagonal_reciprocals_color",
    "settings.harmony_triangles_color", "settings.diagonal_method_color", "settings.ruler_color",
    "settings.bg_color", "settings.grid_color",
    "settings.golden_spiral_flip_h", "settings.golden_spiral_flip_v",
    "settings.golden_spiral_length", "settings.golden_spiral_show_segments", "settings.golden_spiral_fit",
    "settings.golden_triangle_rotation", "settings.golden_triangle_scale", "settings.golden_triangle_count",
    "settings.radial_line_count",
    "settings.vanishing_point_x", "settings.vanishing_point_y", "settings.vanishing_point_lines",
    "settings.show_vanishing_point_grid", "settings.vanishing_point_grid_count",
    "settings.circular_thirds_count", "settings.circular_thirds_fit",
    "settings.harmony_triangles_flip", "settings.diagonal_method_angle",
    "settings.ruler_units", "settings.line_width", "settings.ruler_size",
    "settings.grid_divisions", "settings.grid_square", "settings.hide_guides_outside_frame",
    "settings.custom_guides_data",
]


class B_GUIDES_MT_presets(Menu):
    bl_label = "Guide Presets"
    preset_subdir = "b_guides"
    preset_operator = "b_guides.execute_preset"  # Use custom operator
    
    def draw(self, context):
        """Custom draw to display active preset name"""
        import os
        
        # Get the settings (VSE or Camera)
        is_vse = context.area and context.area.type == 'SEQUENCE_EDITOR'
        if is_vse:
            settings = context.scene.vse_guides
        else:
            cam = getattr(context.scene, 'camera', None)
            settings = cam.data.camera_guides if cam and hasattr(cam.data, 'camera_guides') else None
        
        # Get active preset name if available
        active_preset = ""
        if settings and hasattr(settings, 'active_preset'):
            active_preset = settings.active_preset
        
        # Get list of available presets
        preset_paths = bpy.utils.preset_paths(self.preset_subdir)
        preset_files = []
        for preset_path in preset_paths:
            if os.path.isdir(preset_path):
                for fn in os.listdir(preset_path):
                    if fn.endswith('.py'):
                        preset_files.append(os.path.splitext(fn)[0])
        
        layout = self.layout
        
        # Display presets
        if preset_files:
            for preset_name in sorted(preset_files):
                props = layout.operator(
                    self.preset_operator,
                    text=preset_name,
                    icon='RIGHTARROW_THIN' if preset_name == active_preset else 'NONE'
                )
                props.preset_name = preset_name
        else:
            layout.label(text="No Presets", icon='INFO')


class B_GUIDES_OT_execute_preset(Operator):
    """Execute a preset and track which one was loaded"""
    
    bl_idname = "b_guides.execute_preset"
    bl_label = "Execute Preset"
    
    preset_name: bpy.props.StringProperty(
        name="Preset Name",
        description="Name of the preset to execute",
        default=""
    )
    
    def execute(self, context):
        import os
        
        # Find the preset file
        preset_paths = bpy.utils.preset_paths("b_guides")
        preset_file = None
        
        for preset_path in preset_paths:
            filepath = os.path.join(preset_path, self.preset_name + ".py")
            if os.path.exists(filepath):
                preset_file = filepath
                break
        
        if not preset_file:
            self.report({'ERROR'}, f"Preset '{self.preset_name}' not found")
            return {'CANCELLED'}
        
        # Execute the preset
        try:
            with open(preset_file, 'r') as file:
                exec(compile(file.read(), preset_file, 'exec'))
        except Exception as e:
            self.report({'ERROR'}, f"Error executing preset: {str(e)}")
            return {'CANCELLED'}
        
        # Update the active preset property
        is_vse = context.area and context.area.type == 'SEQUENCE_EDITOR'
        if is_vse:
            context.scene.vse_guides.active_preset = self.preset_name
        else:
            cam = getattr(context.scene, 'camera', None)
            if cam and hasattr(cam.data, 'camera_guides'):
                cam.data.camera_guides.active_preset = self.preset_name
        
        return {'FINISHED'}


class B_GUIDES_OT_preset_add(AddPresetBase, Operator):
    """Add/remove guide presets using Blender's preset system."""

    bl_idname = "b_guides.preset_add"
    bl_label = "Add Guide Preset"
    preset_menu = "B_GUIDES_MT_presets"
    preset_defines = [
        "scene=bpy.context.scene",
        "is_vse=(bpy.context.area and bpy.context.area.type == 'SEQUENCE_EDITOR')",
        "cam=getattr(scene, 'camera', None)",
        "settings=(scene.vse_guides if is_vse else (cam.data.camera_guides if cam and hasattr(cam.data, 'camera_guides') else scene.vse_guides))",
    ]
    preset_values = PRESET_VALUES
    preset_subdir = "b_guides"
    
    def execute(self, context):
        result = super().execute(context)
        
        # If we successfully added a preset, update the active preset name
        if result == {'FINISHED'} and hasattr(self, 'name'):
            is_vse = context.area and context.area.type == 'SEQUENCE_EDITOR'
            if is_vse:
                context.scene.vse_guides.active_preset = self.name
            else:
                cam = getattr(context.scene, 'camera', None)
                if cam and hasattr(cam.data, 'camera_guides'):
                    cam.data.camera_guides.active_preset = self.name
        
        return result


classes = (
    B_GUIDES_MT_presets,
    B_GUIDES_OT_execute_preset,
    B_GUIDES_OT_preset_add,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
