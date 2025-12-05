"""Preset management for VSE Guides addon"""

import bpy
import json
import os
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper


from .operators import get_settings_for_context


# Properties to save/load in presets
PRESET_PROPERTIES = [
    # Guide visibility
    'show_thirds', 'show_golden', 'show_center', 'show_diagonals',
    'show_golden_spiral', 'show_golden_triangle', 'show_radial_symmetry',
    'show_vanishing_point', 'show_circular_thirds', 'show_diagonal_reciprocals',
    'show_harmony_triangles', 'show_diagonal_method', 'show_rulers', 'show_grid',
    'show_custom_guides',
    
    # Colors
    'thirds_color', 'golden_color', 'center_color', 'diagonals_color',
    'golden_spiral_color', 'golden_triangle_color', 'radial_symmetry_color',
    'vanishing_point_color', 'circular_thirds_color', 'diagonal_reciprocals_color',
    'harmony_triangles_color', 'diagonal_method_color', 'ruler_color', 'bg_color',
    'grid_color',
    
    # Golden spiral settings
    'golden_spiral_flip_h', 'golden_spiral_flip_v', 'golden_spiral_length',
    'golden_spiral_show_segments', 'golden_spiral_fit',
    
    # Golden triangle settings
    'golden_triangle_rotation', 'golden_triangle_fit',
    
    # Radial symmetry settings
    'radial_line_count',
    
    # Vanishing point settings
    'vanishing_point_x', 'vanishing_point_y',
    
    # Circular thirds settings
    'circular_thirds_count', 'circular_thirds_fit',
    
    # Ruler settings
    'ruler_units', 'line_width', 'ruler_size',
    
    # Grid settings
    'grid_divisions', 'grid_square',
    
    # Frame clipping
    'hide_guides_outside_frame',
]


def get_presets_dir():
    """Get the directory where presets are stored"""
    # Store in Blender's config directory for the addon
    config_dir = bpy.utils.user_resource('CONFIG')
    presets_dir = os.path.join(config_dir, 'vse_guides_presets')
    
    if not os.path.exists(presets_dir):
        os.makedirs(presets_dir)
    
    return presets_dir


def get_preset_path(name):
    """Get the full path for a preset file"""
    return os.path.join(get_presets_dir(), f"{name}.json")


def list_presets():
    """Return a list of available preset names"""
    presets_dir = get_presets_dir()
    presets = []
    
    if os.path.exists(presets_dir):
        for filename in os.listdir(presets_dir):
            if filename.endswith('.json'):
                presets.append(filename[:-5])  # Remove .json extension
    
    return sorted(presets)


def get_preset_items(self, context):
    """Dynamic enum items for preset dropdown"""
    items = [('NONE', '-- Select Preset --', '')]
    
    for preset_name in list_presets():
        items.append((preset_name, preset_name, f"Load preset: {preset_name}"))
    
    return items


def settings_to_dict(settings):
    """Convert VSEGuidesSettings to a dictionary"""
    data = {}
    
    for prop_name in PRESET_PROPERTIES:
        if hasattr(settings, prop_name):
            value = getattr(settings, prop_name)
            
            # Handle different property types
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # Color or vector property - convert to list
                data[prop_name] = list(value)
            else:
                data[prop_name] = value
    
    return data


def dict_to_settings(data, settings):
    """Apply dictionary values to VSEGuidesSettings"""
    for prop_name, value in data.items():
        if prop_name in PRESET_PROPERTIES and hasattr(settings, prop_name):
            try:
                if isinstance(value, list):
                    # Color or vector property
                    prop = getattr(settings, prop_name)
                    for i, v in enumerate(value):
                        prop[i] = v
                else:
                    setattr(settings, prop_name, value)
            except Exception as e:
                print(f"Warning: Could not set property {prop_name}: {e}")


class VSE_OT_save_preset(Operator):
    """Save current guide settings as a named preset"""
    bl_idname = "vse.save_preset"
    bl_label = "Save Preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_name: StringProperty(
        name="Preset Name",
        description="Name for the preset",
        default=""
    )
    
    def invoke(self, context, event):
        # Get name from properties
        settings, custom_guides, update_func = get_settings_for_context(context)
        self.preset_name = settings.new_preset_name
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "preset_name")
    
    def execute(self, context):
        if not self.preset_name:
            self.report({'ERROR'}, "Please enter a preset name")
            return {'CANCELLED'}
        
        # Sanitize name
        name = "".join(c for c in self.preset_name if c.isalnum() or c in "_ -")
        if not name:
            self.report({'ERROR'}, "Invalid preset name")
            return {'CANCELLED'}
        
        settings, custom_guides_list, update_func = get_settings_for_context(context)
        data = settings_to_dict(settings)
        
        # Add custom guides
        custom_guides = []
        for guide in custom_guides_list:
            custom_guides.append({
                'position_x': guide.position_x,
                'position_y': guide.position_y,
                'rotation': guide.rotation,
                'orientation': guide.orientation,
                'color': list(guide.color),
            })
        data['custom_guides'] = custom_guides
        
        # Save to file
        preset_path = get_preset_path(name)
        try:
            with open(preset_path, 'w') as f:
                json.dump(data, f, indent=2)
            self.report({'INFO'}, f"Saved preset: {name}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save preset: {e}")
            return {'CANCELLED'}
        
        # Clear the new preset name field
        settings.new_preset_name = ""
        
        return {'FINISHED'}


class VSE_OT_load_preset(Operator):
    """Load a saved preset"""
    bl_idname = "vse.load_preset"
    bl_label = "Load Preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_name: StringProperty(
        name="Preset Name",
        description="Name of the preset to load",
        default=""
    )
    
    def execute(self, context):
        if not self.preset_name or self.preset_name == 'NONE':
            self.report({'WARNING'}, "No preset selected")
            return {'CANCELLED'}
        
        preset_path = get_preset_path(self.preset_name)
        
        if not os.path.exists(preset_path):
            self.report({'ERROR'}, f"Preset not found: {self.preset_name}")
            return {'CANCELLED'}
        
        try:
            with open(preset_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load preset: {e}")
            return {'CANCELLED'}
        
        settings, custom_guides, update_func = get_settings_for_context(context)
        
        # Load custom guides first (clear existing)
        if 'custom_guides' in data:
            custom_guides.clear()
            for guide_data in data['custom_guides']:
                guide = custom_guides.add()
                guide.position_x = guide_data.get('position_x', 0.0)
                guide.position_y = guide_data.get('position_y', 0.0)
                guide.rotation = guide_data.get('rotation', 0.0)
                guide.orientation = guide_data.get('orientation', 'HORIZONTAL')
                if 'color' in guide_data:
                    for i, v in enumerate(guide_data['color']):
                        guide.color[i] = v
        
        # Load main settings
        dict_to_settings(data, settings)
        
        # Set active preset name
        settings.active_preset = self.preset_name
        
        update_func()
        
        self.report({'INFO'}, f"Loaded preset: {self.preset_name}")
        return {'FINISHED'}


class VSE_OT_delete_preset(Operator):
    """Delete a saved preset"""
    bl_idname = "vse.delete_preset"
    bl_label = "Delete Preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_name: StringProperty(
        name="Preset Name",
        description="Name of the preset to delete",
        default=""
    )
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
    
    def execute(self, context):
        if not self.preset_name or self.preset_name == 'NONE':
            self.report({'WARNING'}, "No preset selected")
            return {'CANCELLED'}
        
        preset_path = get_preset_path(self.preset_name)
        
        if not os.path.exists(preset_path):
            self.report({'ERROR'}, f"Preset not found: {self.preset_name}")
            return {'CANCELLED'}
        
        try:
            os.remove(preset_path)
            self.report({'INFO'}, f"Deleted preset: {self.preset_name}")
            
            # Reset selection
            settings, custom_guides, update_func = get_settings_for_context(context)
            if hasattr(settings, 'active_preset'):
                settings.active_preset = ""
        except Exception as e:
            self.report({'ERROR'}, f"Failed to delete preset: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class VSE_OT_export_preset(Operator, ExportHelper):
    """Export current settings to a JSON file"""
    bl_idname = "vse.export_preset"
    bl_label = "Export Preset"
    bl_options = {'REGISTER'}
    
    filename_ext = ".json"
    
    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    
    def execute(self, context):
        settings, custom_guides_list, update_func = get_settings_for_context(context)
        data = settings_to_dict(settings)
        
        # Add custom guides
        custom_guides = []
        for guide in custom_guides_list:
            custom_guides.append({
                'position_x': guide.position_x,
                'position_y': guide.position_y,
                'rotation': guide.rotation,
                'orientation': guide.orientation,
                'color': list(guide.color),
            })
        data['custom_guides'] = custom_guides
        
        try:
            with open(self.filepath, 'w') as f:
                json.dump(data, f, indent=2)
            self.report({'INFO'}, f"Exported preset to: {self.filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export preset: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class VSE_OT_import_preset(Operator, ImportHelper):
    """Import settings from a JSON file"""
    bl_idname = "vse.import_preset"
    bl_label = "Import Preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    filename_ext = ".json"
    
    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    
    def execute(self, context):
        if not os.path.exists(self.filepath):
            self.report({'ERROR'}, "File not found")
            return {'CANCELLED'}
        
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read file: {e}")
            return {'CANCELLED'}
        
        settings, custom_guides, update_func = get_settings_for_context(context)
        
        # Load custom guides first (clear existing)
        if 'custom_guides' in data:
            custom_guides.clear()
            for guide_data in data['custom_guides']:
                guide = custom_guides.add()
                guide.position_x = guide_data.get('position_x', 0.0)
                guide.position_y = guide_data.get('position_y', 0.0)
                guide.rotation = guide_data.get('rotation', 0.0)
                guide.orientation = guide_data.get('orientation', 'HORIZONTAL')
                if 'color' in guide_data:
                    for i, v in enumerate(guide_data['color']):
                        guide.color[i] = v
        
        # Load main settings
        dict_to_settings(data, settings)
        
        update_func()
        
        self.report({'INFO'}, f"Imported preset from: {self.filepath}")
        return {'FINISHED'}


# Registration
classes = (
    VSE_OT_save_preset,
    VSE_OT_load_preset,
    VSE_OT_delete_preset,
    VSE_OT_export_preset,
    VSE_OT_import_preset,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
