"""Operators for VSE Guides addon"""

import bpy
from bpy.types import Operator
from bpy.props import IntProperty, EnumProperty

from .properties import update_all_areas, update_vse_areas, update_3d_areas


def get_settings_for_context(context):
    """Get the appropriate settings and custom guides based on context"""
    if context.area and context.area.type == 'VIEW_3D':
        camera = context.scene.camera
        if camera and hasattr(camera.data, 'camera_guides'):
            return camera.data.camera_guides, camera.data.custom_camera_guides, update_3d_areas
    
    # Default to VSE
    return context.scene.vse_guides, context.scene.custom_guides, update_vse_areas


class VSE_OT_add_custom_guide(Operator):
    """Add a guide line manually"""
    bl_idname = "vse.add_custom_guide"
    bl_label = "Add Guide Line"
    bl_options = {'REGISTER', 'UNDO'}
    
    orientation: EnumProperty(
        items=[('HORIZONTAL', "Horizontal", ""), ('VERTICAL', "Vertical", "")],
        default='VERTICAL'
    )
    
    def execute(self, context: bpy.types.Context) -> set[str]:
        settings, custom_guides, update_func = get_settings_for_context(context)
        
        guide = custom_guides.add()
        guide.orientation = self.orientation
        guide.position_x = 0.0
        guide.position_y = 0.0
        
        # Auto-number the guide
        guide.name = str(len(custom_guides))
        
        # Set the newly added guide as active
        settings.active_guide_index = len(custom_guides) - 1
        
        update_func()
        self.report({'INFO'}, f"Guide line {guide.name} added")
        return {'FINISHED'}


class VSE_OT_remove_custom_guide(Operator):
    """Remove a guide line"""
    bl_idname = "vse.remove_custom_guide"
    bl_label = "Remove Guide Line"
    bl_options = {'REGISTER', 'UNDO'}
    
    index: IntProperty()
    
    def execute(self, context: bpy.types.Context) -> set[str]:
        settings, custom_guides, update_func = get_settings_for_context(context)
        
        if 0 <= self.index < len(custom_guides):
            custom_guides.remove(self.index)
            update_func()
            self.report({'INFO'}, "Guide line removed")
        return {'FINISHED'}


class VSE_OT_clear_custom_guides(Operator):
    """Clear all guide lines"""
    bl_idname = "vse.clear_custom_guides"
    bl_label = "Clear All Guide Lines"
    bl_options = {'REGISTER', 'UNDO'}
    
    def invoke(self, context: bpy.types.Context, event) -> set[str]:
        settings, custom_guides, _ = get_settings_for_context(context)
        count = len(custom_guides)
        
        if count == 0:
            self.report({'INFO'}, "No guide lines to clear")
            return {'CANCELLED'}
        
        # Show confirmation dialog
        return context.window_manager.invoke_confirm(self, event)
    
    def execute(self, context: bpy.types.Context) -> set[str]:
        settings, custom_guides, update_func = get_settings_for_context(context)
        
        custom_guides.clear()
        settings.active_guide_index = 0
        update_func()
        self.report({'INFO'}, "All guide lines cleared")
        return {'FINISHED'}


class VSE_OT_move_guide_up(Operator):
    """Move guide line up in the list"""
    bl_idname = "vse.move_guide_up"
    bl_label = "Move Guide Line Up"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context: bpy.types.Context) -> set[str]:
        settings, custom_guides, update_func = get_settings_for_context(context)
        index = settings.active_guide_index
        
        if index > 0:
            custom_guides.move(index, index - 1)
            settings.active_guide_index = index - 1
            update_func()
        
        return {'FINISHED'}


class VSE_OT_move_guide_down(Operator):
    """Move guide line down in the list"""
    bl_idname = "vse.move_guide_down"
    bl_label = "Move Guide Line Down"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context: bpy.types.Context) -> set[str]:
        settings, custom_guides, update_func = get_settings_for_context(context)
        index = settings.active_guide_index
        
        if index < len(custom_guides) - 1:
            custom_guides.move(index, index + 1)
            settings.active_guide_index = index + 1
            update_func()
        
        return {'FINISHED'}


class VSE_OT_reset_guides(Operator):
    """Reset all guide settings to defaults"""
    bl_idname = "vse.reset_guides"
    bl_label = "Reset Guides"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context: bpy.types.Context) -> set[str]:
        settings, custom_guides, update_func = get_settings_for_context(context)
        
        # Reset all properties to defaults
        settings.show_thirds = False
        settings.show_golden = False
        settings.show_center = False
        settings.show_diagonals = False
        settings.show_rulers = False
        settings.show_grid = False
        settings.show_custom_guides = True
        
        # Reset newer guides
        settings.show_golden_spiral = False
        settings.show_golden_triangle = False
        settings.show_circular_thirds = False
        settings.show_radial_symmetry = False
        settings.show_vanishing_point = False
        settings.show_diagonal_reciprocals = False
        settings.show_harmony_triangles = False
        settings.show_diagonal_method = False
        
        settings.ruler_units = 'RESOLUTION'
        settings.grid_divisions = 8
        settings.grid_square = False
        settings.ruler_color = (1.0, 1.0, 1.0, 0.8)
        settings.line_width = 1.0
        settings.ruler_size = 30
        
        update_func()
        self.report({'INFO'}, "Guide settings reset to defaults")
        return {'FINISHED'}


class VSE_OT_toggle_all_guides(Operator):
    """Toggle all guides on/off"""
    bl_idname = "vse.toggle_all_guides"
    bl_label = "Toggle All Guides"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context: bpy.types.Context) -> set[str]:
        settings, custom_guides, update_func = get_settings_for_context(context)
        
        # List of all guide property names
        guide_props = [
            "show_thirds",
            "show_golden",
            "show_center",
            "show_diagonals",
            "show_rulers",
            "show_grid",
            "show_custom_guides",
            "show_golden_spiral",
            "show_golden_triangle",
            "show_circular_thirds",
            "show_radial_symmetry",
            "show_vanishing_point",
            "show_diagonal_reciprocals",
            "show_harmony_triangles",
            "show_diagonal_method"
        ]
        
        # Check if any guide is active
        any_active = False
        for prop in guide_props:
            if getattr(settings, prop):
                any_active = True
                break
        
        if any_active:
            # Toggling OFF: Save state and disable all
            active_guides = []
            for prop in guide_props:
                if getattr(settings, prop):
                    active_guides.append(prop)
                    setattr(settings, prop, False)
            
            # Store comma-separated list
            settings.stored_active_guides = ",".join(active_guides)
            self.report({'INFO'}, "Guides disabled")
            
        else:
            # Toggling ON: Restore state
            if settings.stored_active_guides:
                # Restore from saved state
                saved_guides = settings.stored_active_guides.split(",")
                count = 0
                for prop in saved_guides:
                    if hasattr(settings, prop):
                        setattr(settings, prop, True)
                        count += 1
                
                if count == 0:
                    # Fallback if saved state was somehow empty or invalid
                    settings.show_thirds = True
                    settings.show_custom_guides = True
            else:
                # No saved state (first run), enable defaults
                settings.show_thirds = True
                settings.show_custom_guides = True
                
            self.report({'INFO'}, "Guides enabled")
        
        update_func()
        return {'FINISHED'}




# Registration
classes = (
    VSE_OT_add_custom_guide,
    VSE_OT_remove_custom_guide,
    VSE_OT_clear_custom_guides,
    VSE_OT_move_guide_up,
    VSE_OT_move_guide_down,
    VSE_OT_reset_guides,
    VSE_OT_toggle_all_guides,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)



def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
