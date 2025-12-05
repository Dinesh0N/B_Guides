"""UI panels and lists for VSE Guides addon"""

import bpy
from bpy.types import Panel, UIList
from . import presets


def draw_preset_section(layout, settings):
    """Draw the preset management UI section"""
    box = layout.box()
    box.label(text="Presets", icon='PRESET')
    col = box.column(align=True)
    
    # Get available presets
    preset_list = presets.list_presets()
    
    # Preset dropdown menu
    if preset_list:
        # Display preset list as menu
        row = col.row(align=True)
        row.menu("VSE_MT_preset_menu", text=settings.active_preset if settings.active_preset else "Select Preset", icon='COLLAPSEMENU')
        
        # Load and Delete buttons (only enabled if a preset is selected)
        sub = row.row(align=True)
        sub.enabled = bool(settings.active_preset)
        op = sub.operator("vse.load_preset", text="", icon='FILE_REFRESH')
        op.preset_name = settings.active_preset
        op = sub.operator("vse.delete_preset", text="", icon='REMOVE')
        op.preset_name = settings.active_preset

    else:
        col.label(text="No saved presets", icon='INFO')
    
    col.separator()
    
    # Save current settings as new preset
    row = col.row(align=True)
    row.operator("vse.save_preset", text="Save Current", icon='ADD')
    
    col.separator()
    
    # Export/Import presets
    row = col.row(align=True)
    row.operator("vse.export_preset", text="Export", icon='EXPORT')
    row.operator("vse.import_preset", text="Import", icon='IMPORT')
    
    col.separator()
    
    # Export guides as image
    row = col.row(align=True)
    row.operator("vse.export_guides_image", text="Export Image", icon='IMAGE_DATA')


class VSE_MT_preset_menu(bpy.types.Menu):
    """Preset selection menu"""
    bl_label = "Select Preset"
    bl_idname = "VSE_MT_preset_menu"
    
    def draw(self, context):
        layout = self.layout
        preset_list = presets.list_presets()
        
        if preset_list:
            for preset_name in preset_list:
                op = layout.operator("vse.load_preset", text=preset_name)
                op.preset_name = preset_name
        else:
            layout.label(text="No presets saved")


class VSE_UL_custom_guides(UIList):
    """UIList for guide lines"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        guide = item
        
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            
            # Icon based on orientation
            icon = 'TRIA_DOWN' if guide.orientation == 'HORIZONTAL' else 'TRIA_RIGHT'
            row.label(text="", icon=icon)
            
            # Guide name
            row.prop(guide, "name", text="", emboss=False)
            
            # Color picker
            row.prop(guide, "color", text="", icon_only=True)
            
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            icon = 'TRIA_DOWN' if guide.orientation == 'HORIZONTAL' else 'TRIA_RIGHT'
            layout.label(text="", icon=icon)


class VIEW3D_PT_composition_guides(Panel):
    """Creates a Panel in the 3D Viewport sidebar"""
    bl_label = "Composition Guides"
    bl_idname = "VIEW3D_PT_composition_guides"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Guides"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        region_data = context.region_data
        
        # Camera selection
        row = layout.row()
        row.label(text="Camera:", icon='CAMERA_DATA')
        row.prop(scene, "camera", text="")
        
        camera = scene.camera
        
        # Show warning if no camera or not in camera view
        if not camera:
            layout.label(text="No Camera in Scene", icon='ERROR')
            return
            
        if not region_data or region_data.view_perspective != 'CAMERA':
            layout.label(text="Enter Camera View", icon='INFO')
            layout.separator()
        
        # Use camera settings
        if hasattr(camera.data, 'camera_guides'):
            settings = camera.data.camera_guides
            custom_guides = camera.data.custom_camera_guides
        else:
            layout.label(text="Select a Camera", icon='INFO')
            return
        
        # Toggle all guides button at top
        any_active = self.any_guides_active(settings)
        row = layout.row()
        row.scale_y = 1.2
        row.operator(
            "vse.toggle_all_guides",
            text="All Guides ON" if not any_active else "All Guides OFF",
            icon='HIDE_OFF' if any_active else 'HIDE_ON',
            depress=any_active
        )
        layout.separator()
        
        # Grid
        box = layout.box()
        row = box.row()
        row.label(text="Grid", icon='GRID')
        row.prop(settings, "show_grid", text="")
        if settings.show_grid:
            col = box.column(align=True)
            col.prop(settings, "grid_divisions")
            row = col.row()
            row.prop(settings, "grid_square")
            row.prop(settings, "grid_color", text="")
        
        # Guide Lines
        box = layout.box()
        row = box.row()
        row.label(text="Guide Lines", icon='DRIVER')
        row.prop(settings, "show_custom_guides", text="")
        
        if settings.show_custom_guides:
            col = box.column(align=True)
            col.operator("vse.add_custom_guide", text="Add Line", icon='ADD')
            
            if len(custom_guides) > 0:
                col.separator()
                row = col.row()
                row.label(text=f"Lines ({len(custom_guides)})")
                row.operator("vse.clear_custom_guides", text="", icon='TRASH')
                
                row = col.row()
                row.template_list(
                    "VSE_UL_custom_guides",
                    "",
                    camera.data,
                    "custom_camera_guides",
                    settings,
                    "active_guide_index",
                    rows=min(len(custom_guides), 5)
                )
                
                col_ops = row.column(align=True)
                col_ops.operator("vse.remove_custom_guide", text="", icon='REMOVE').index = settings.active_guide_index
                
                if 0 <= settings.active_guide_index < len(custom_guides):
                    active_guide = custom_guides[settings.active_guide_index]
                    col.separator()
                    box = col.box()
                    row = box.row()
                    row.label(text="Transform", icon='OBJECT_ORIGIN')
                    col_props = box.column(align=True)
                    row = col_props.row(align=True)
                    row.prop(active_guide, "position_x", text="X")
                    row.prop(active_guide, "position_y", text="Y")
                    col_props.separator()
                    row = col_props.row(align=True)
                    row.prop(active_guide, "rotation", text="Rotation")
        
        # Composition Guides
        box = layout.box()
        box.label(text="Guides", icon='PIVOT_CURSOR')
        col = box.column(align=True)
        
        row = col.row(align=True)
        row.prop(settings, "show_thirds", icon='SELECT_SUBTRACT')
        row.prop(settings, "thirds_color", text="")
        
        row = col.row(align=True)
        row.prop(settings, "show_golden", icon='SORTBYEXT')
        row.prop(settings, "golden_color", text="")
        
        col.separator(factor=0.5)
        
        row = col.row(align=True)
        row.prop(settings, "show_center", icon='PIVOT_MEDIAN')
        row.prop(settings, "center_color", text="")
        row = col.row(align=True)
        row.prop(settings, "show_diagonals", icon='CON_TRACKTO')
        row.prop(settings, "diagonals_color", text="")
        
        col.separator(factor=0.5)
        
        row = col.row(align=True)
        row.prop(settings, "show_golden_spiral", icon='FORCE_VORTEX')
        row.prop(settings, "golden_spiral_color", text="")
        if settings.show_golden_spiral:
            row = col.row(align=True)
            row.prop(settings, "golden_spiral_flip_h", text="Flip H", toggle=True)
            row.prop(settings, "golden_spiral_flip_v", text="Flip V", toggle=True)
            sub_col = col.column(align=True)
            sub_col.prop(settings, "golden_spiral_length")
            row = sub_col.row(align=True)
            row.prop(settings, "golden_spiral_show_segments")
            row.prop(settings, "golden_spiral_fit")
        
        row = col.row(align=True)
        row.prop(settings, "show_golden_triangle", icon='OUTLINER_OB_FORCE_FIELD')
        row.prop(settings, "golden_triangle_color", text="")
        if settings.show_golden_triangle:
            row = col.row(align=True)
            row.prop(settings, "golden_triangle_rotation")
            row = col.row(align=True)
            row.prop(settings, "golden_triangle_scale")
            row.prop(settings, "golden_triangle_count")
        
        col.separator(factor=0.5)
        
        row = col.row(align=True)
        row.prop(settings, "show_circular_thirds", icon='MESH_CIRCLE')
        row.prop(settings, "circular_thirds_color", text="")
        if settings.show_circular_thirds:
            row = col.row(align=True)
            row.prop(settings, "circular_thirds_count", text="Circles")
            row.prop(settings, "circular_thirds_fit")
        row = col.row(align=True)
        row.prop(settings, "show_radial_symmetry", icon='FORCE_HARMONIC')
        row.prop(settings, "radial_symmetry_color", text="")
        if settings.show_radial_symmetry:
            col.prop(settings, "radial_line_count", text="Lines")
        
        col.separator(factor=0.5)
        
        row = col.row(align=True)
        row.prop(settings, "show_vanishing_point", icon='EMPTY_SINGLE_ARROW')
        row.prop(settings, "vanishing_point_color", text="")
        if settings.show_vanishing_point:
            row = col.row(align=True)
            row.prop(settings, "vanishing_point_x", text="VP X", slider=True)
            row.prop(settings, "vanishing_point_y", text="VP Y", slider=True)
            row = col.row(align=True)
            row.prop(settings, "vanishing_point_lines")
            row.prop(settings, "show_vanishing_point_grid")
            if settings.show_vanishing_point_grid:
                col.prop(settings, "vanishing_point_grid_count")
        
        col.separator(factor=0.5)
        
        row = col.row(align=True)
        row.prop(settings, "show_diagonal_reciprocals", icon='ORIENTATION_VIEW')
        row.prop(settings, "diagonal_reciprocals_color", text="")
        
        row = col.row(align=True)
        row.prop(settings, "show_harmony_triangles", icon='SNAP_EDGE')
        row.prop(settings, "harmony_triangles_color", text="")
        if settings.show_harmony_triangles:
            col.prop(settings, "harmony_triangles_flip", toggle=True)
        
        row = col.row(align=True)
        row.prop(settings, "show_diagonal_method", icon='DRIVER_DISTANCE')
        row.prop(settings, "diagonal_method_color", text="")
        if settings.show_diagonal_method:
            col.prop(settings, "diagonal_method_angle")
        
        col.separator()
        col.prop(settings, "line_width")
        col.separator()
        
        # Ruler & Display settings
        box = layout.box()
        row = box.row()
        row.label(text="Ruler", icon='ARROW_LEFTRIGHT')
        row.prop(settings, "show_rulers", text="")

        if settings.show_rulers:
            col = box.column(align=True)
            row = col.row()
            row.prop(settings, "ruler_units")
            row.prop(settings, "ruler_size")
            row = col.row()
            row.prop(settings, "ruler_color")
            row.prop(settings, "bg_color", text=" BG Color")
        
        # Presets section at bottom
        draw_preset_section(layout, settings)
    
    def any_guides_active(self, settings):
        return any([
            settings.show_thirds,
            settings.show_golden,
            settings.show_center,
            settings.show_diagonals,
            settings.show_rulers,
            settings.show_grid,
            settings.show_custom_guides,
            settings.show_golden_spiral,
            settings.show_golden_triangle,
            settings.show_circular_thirds,
            settings.show_radial_symmetry,
            settings.show_vanishing_point,
            settings.show_diagonal_reciprocals,
            settings.show_harmony_triangles,
            settings.show_diagonal_method
        ])


class VSE_PT_composition_guides(Panel):
    """Creates a Panel in the VSE sidebar"""
    bl_label = "Composition Guides"
    bl_idname = "VSE_PT_composition_guides"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Guides"
    
    @classmethod
    def poll(cls, context):
        # Show panel in both Preview-only and Sequencer+Preview modes
        return context.space_data.view_type in {'PREVIEW', 'SEQUENCER_PREVIEW'}
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.vse_guides

        # Toggle all guides button at top
        any_active = self.any_guides_active(settings)
        row = layout.row()
        row.scale_y = 1.2
        row.operator(
            "vse.toggle_all_guides",
            text="All Guides ON" if not any_active else "All Guides OFF",
            icon='HIDE_OFF' if any_active else 'HIDE_ON',
            depress=any_active
        )
        layout.separator()
        
        # Grid
        box = layout.box()
        row = box.row()
        row.label(text="Grid", icon='GRID')
        row.prop(settings, "show_grid", text="")
        if settings.show_grid:
            col = box.column(align=True)
            col.prop(settings, "grid_divisions")
            row = col.row()
            row.prop(settings, "grid_square")
            row.prop(settings, "grid_color", text="")       
        # Guide Lines
        box = layout.box()
        row = box.row()
        row.label(text="Guide Lines", icon='DRIVER')
        row.prop(settings, "show_custom_guides", text="")
        
        if settings.show_custom_guides:
            col = box.column(align=True)
            
            # Single add button
            col.operator("vse.add_custom_guide", text="Add Line", icon='ADD')
            
            if len(context.scene.custom_guides) > 0:
                col.separator()
                
                # Header with count and clear button
                row = col.row()
                row.label(text=f"Lines ({len(context.scene.custom_guides)})", icon='LINENUMBERS_ON')
                row.operator("vse.clear_custom_guides", text="", icon='TRASH')
                
                # UIList for guides
                row = col.row()
                row.template_list(
                    "VSE_UL_custom_guides",
                    "",
                    context.scene,
                    "custom_guides",
                    settings,
                    "active_guide_index",
                    rows=min(len(context.scene.custom_guides), 5),
                    maxrows=8
                )
                
                # List operations
                col_ops = row.column(align=True)
                col_ops.operator("vse.remove_custom_guide", text="", icon='REMOVE').index = settings.active_guide_index
                
                # Active guide properties
                if 0 <= settings.active_guide_index < len(context.scene.custom_guides):
                    active_guide = context.scene.custom_guides[settings.active_guide_index]
                    
                    col.separator()
                    
                    # Location & Rotation in a unified block
                    box = col.box()
                    
                    # Header
                    row = box.row()
                    row.label(text="Transform", icon='OBJECT_ORIGIN')
                    
                    # X/Y Properties
                    col_props = box.column(align=True)
                    
                    row = col_props.row(align=True)
                    row.prop(active_guide, "position_x", text="X")
                    row.prop(active_guide, "position_y", text="Y")
                    
                    col_props.separator()
                    
                    # Rotation
                    row = col_props.row(align=True)
                    row.prop(active_guide, "rotation", text="Rotation")
        
        # Composition Guides
        box = layout.box()
        box.label(text="Guides", icon='PIVOT_CURSOR')
        col = box.column(align=True)
        
        # Classic guides
        row = col.row(align=True)
        row.prop(settings, "show_thirds", icon='SELECT_SUBTRACT')
        row.prop(settings, "thirds_color", text="")
        
        row = col.row(align=True)
        row.prop(settings, "show_golden", icon='SORTBYEXT')
        row.prop(settings, "golden_color", text="")
        
        col.separator(factor=0.5)
        
        # Center and alignment
        row = col.row(align=True)
        row.prop(settings, "show_center", icon='PIVOT_MEDIAN')
        row.prop(settings, "center_color", text="")
        row = col.row(align=True)
        row.prop(settings, "show_diagonals", icon='CON_TRACKTO')
        row.prop(settings, "diagonals_color", text="")
        
        col.separator(factor=0.5)

        row = col.row(align=True)
        row.prop(settings, "show_golden_spiral", icon='FORCE_VORTEX')
        row.prop(settings, "golden_spiral_color", text="")
        if settings.show_golden_spiral:
            row = col.row(align=True)
            row.prop(settings, "golden_spiral_flip_h", text="Flip H", toggle=True)
            row.prop(settings, "golden_spiral_flip_v", text="Flip V", toggle=True)
            sub_col = col.column(align=True)
            sub_col.prop(settings, "golden_spiral_length")
            row = sub_col.row(align=True)
            row.prop(settings, "golden_spiral_show_segments")
            row.prop(settings, "golden_spiral_fit")
        
        row = col.row(align=True)
        row.prop(settings, "show_golden_triangle", icon='OUTLINER_OB_FORCE_FIELD')
        row.prop(settings, "golden_triangle_color", text="")
        if settings.show_golden_triangle:
            row = col.row(align=True)
            row.prop(settings, "golden_triangle_rotation")
            row = col.row(align=True)
            row.prop(settings, "golden_triangle_scale")
            row.prop(settings, "golden_triangle_count")
        
        col.separator(factor=0.5)
        
        row = col.row(align=True)
        row.prop(settings, "show_circular_thirds", icon='MESH_CIRCLE')
        row.prop(settings, "circular_thirds_color", text="")
        if settings.show_circular_thirds:
            row = col.row(align=True)
            row.prop(settings, "circular_thirds_count", text="Circles")
            row.prop(settings, "circular_thirds_fit")
        row = col.row(align=True)
        row.prop(settings, "show_radial_symmetry", icon='FORCE_HARMONIC')
        row.prop(settings, "radial_symmetry_color", text="")
        if settings.show_radial_symmetry:
            col.prop(settings, "radial_line_count", text="Lines")
        
        col.separator(factor=0.5)
        
        row = col.row(align=True)
        row.prop(settings, "show_vanishing_point", icon='EMPTY_SINGLE_ARROW')
        row.prop(settings, "vanishing_point_color", text="")
        if settings.show_vanishing_point:
            row = col.row(align=True)
            row.prop(settings, "vanishing_point_x", text="VP X", slider=True)
            row.prop(settings, "vanishing_point_y", text="VP Y", slider=True)
            row = col.row(align=True)
            row.prop(settings, "vanishing_point_lines")
            row.prop(settings, "show_vanishing_point_grid")
            if settings.show_vanishing_point_grid:
                col.prop(settings, "vanishing_point_grid_count")
        
        col.separator(factor=0.5)
        
        # Advanced diagonal guides
        row = col.row(align=True)
        row.prop(settings, "show_diagonal_reciprocals", icon='ORIENTATION_VIEW')
        row.prop(settings, "diagonal_reciprocals_color", text="")
        
        row = col.row(align=True)
        row.prop(settings, "show_harmony_triangles", icon='SNAP_EDGE')
        row.prop(settings, "harmony_triangles_color", text="")
        if settings.show_harmony_triangles:
            col.prop(settings, "harmony_triangles_flip", toggle=True)
        
        row = col.row(align=True)
        row.prop(settings, "show_diagonal_method", icon='DRIVER_DISTANCE')
        row.prop(settings, "diagonal_method_color", text="")
        if settings.show_diagonal_method:
            col.prop(settings, "diagonal_method_angle")
        
        col.separator(factor=0.5)


        col.prop(settings, "line_width")
        col.separator()        
        
        # Ruler & Display settings
        box = layout.box()
        row = box.row()
        row.label(text="Ruler", icon='ARROW_LEFTRIGHT')
        row.prop(settings, "show_rulers", text="")

        if settings.show_rulers:
            col = box.column(align=True)
            row = col.row()
            row.prop(settings, "ruler_units")
            row.prop(settings, "ruler_size")
            row = col.row()
            row.prop(settings, "ruler_color")
            row.prop(settings, "bg_color", text=" BG Color")
        
        # Presets section at bottom
        draw_preset_section(layout, settings)
    
    def any_guides_active(self, settings):
        return any([
            settings.show_thirds,
            settings.show_golden,
            settings.show_center,
            settings.show_diagonals,
            settings.show_rulers,
            settings.show_grid,
            settings.show_custom_guides,
            settings.show_golden_spiral,
            settings.show_golden_triangle,
            settings.show_circular_thirds,
            settings.show_radial_symmetry,
            settings.show_vanishing_point,
            settings.show_diagonal_reciprocals,
            settings.show_harmony_triangles,
            settings.show_diagonal_method
        ])


def draw_overlay_toggle(self, context):
    """Draw toggle button in VSE preview overlay popover"""
    # Only show in SEQUENCER_PREVIEW or PREVIEW mode
    if context.space_data.view_type not in {'PREVIEW', 'SEQUENCER_PREVIEW'}:
        return
        
    settings = context.scene.vse_guides
    
    # Check if any guides are active to determine icon
    any_active = any([
        settings.show_thirds,
        settings.show_golden,
        settings.show_center,
        settings.show_diagonals,
        settings.show_rulers,
        settings.show_grid,
        settings.show_custom_guides,
        settings.show_golden_spiral,
        settings.show_golden_triangle,
        settings.show_circular_thirds,
        settings.show_radial_symmetry,
        settings.show_vanishing_point,
        settings.show_diagonal_reciprocals,
        settings.show_harmony_triangles,
        settings.show_diagonal_method
    ])
    
    layout = self.layout
    layout.separator()
    layout.operator(
        "vse.toggle_all_guides",
        text="Composition Guides",
        icon='HIDE_OFF' if any_active else 'HIDE_ON'
    )


def register():
    bpy.utils.register_class(VSE_MT_preset_menu)
    bpy.utils.register_class(VSE_UL_custom_guides)
    bpy.utils.register_class(VIEW3D_PT_composition_guides)
    bpy.utils.register_class(VSE_PT_composition_guides)


def unregister():
    bpy.utils.unregister_class(VSE_PT_composition_guides)
    bpy.utils.unregister_class(VIEW3D_PT_composition_guides)
    bpy.utils.unregister_class(VSE_UL_custom_guides)
    bpy.utils.unregister_class(VSE_MT_preset_menu)
