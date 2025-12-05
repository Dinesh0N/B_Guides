"""Operators for VSE Guides addon"""

import os
import bpy
from bpy.types import Operator
from bpy.props import IntProperty, EnumProperty, FloatProperty

from .properties import update_all_areas, update_vse_areas, update_3d_areas


def get_settings_for_context(context):
    """Get the appropriate settings and custom guides based on context"""
    if context.area and context.area.type == 'VIEW_3D':
        camera = context.scene.camera
        if camera and hasattr(camera.data, 'camera_guides'):
            return camera.data.camera_guides, camera.data.custom_camera_guides, update_3d_areas
    
    # Default to VSE
    return context.scene.vse_guides, context.scene.custom_guides, update_vse_areas


class VSE_OT_move_custom_guide(Operator):
    """Move an existing guide line by clicking and dragging it"""
    bl_idname = "vse.move_custom_guide"
    bl_label = "Move Guide Line"
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}
    
    guide_index: IntProperty(default=-1)
    
    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.area.type == 'SEQUENCE_EDITOR' and hasattr(context.scene, 'custom_guides')
    
    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        if event.type == 'MOUSEMOVE':
            if self.guide:
                # Calculate scale factors
                render = context.scene.render
                scale_x = self.frame_width / render.resolution_x if render.resolution_x > 0 else 1.0
                scale_y = self.frame_height / render.resolution_y if render.resolution_y > 0 else 1.0
                
                if self.guide.orientation == 'HORIZONTAL':
                    # Calculate position relative to center in screen pixels
                    center_y = self.frame_y + self.frame_height / 2
                    screen_offset_y = event.mouse_region_y - center_y
                    # Convert to normalized (-1 to 1)
                    val = screen_offset_y / (self.frame_height / 2)
                    self.guide.position_y = max(-1.0, min(1.0, val))
                else:
                    # Calculate position relative to center in screen pixels
                    center_x = self.frame_x + self.frame_width / 2
                    screen_offset_x = event.mouse_region_x - center_x
                    # Convert to normalized (-1 to 1)
                    val = screen_offset_x / (self.frame_width / 2)
                    self.guide.position_x = max(-1.0, min(1.0, val))
                context.area.tag_redraw()
            return {'RUNNING_MODAL'}
        
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.guide.orientation == 'HORIZONTAL':
                self.report({'INFO'}, f"Guide moved to Y: {self.guide.position_y:.2f}")
            else:
                self.report({'INFO'}, f"Guide moved to X: {self.guide.position_x:.2f}")
            return {'FINISHED'}
        
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            if self.guide:
                self.guide.position_x = self.original_position_x
                self.guide.position_y = self.original_position_y
            context.area.tag_redraw()
            return {'CANCELLED'}
        
        elif event.type == 'DEL' and event.value == 'PRESS':
            if self.guide_index >= 0:
                context.scene.custom_guides.remove(self.guide_index)
                context.area.tag_redraw()
                self.report({'INFO'}, "Guide deleted")
            return {'FINISHED'}
        
        return {'RUNNING_MODAL'}
    
    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        region = context.region
        render = context.scene.render
        render_width = render.resolution_x
        render_height = render.resolution_y
        
        if render_width == 0 or render_height == 0:
            return {'CANCELLED'}
        
        view2d = region.view2d
        x1, y1 = view2d.view_to_region(-render_width / 2, -render_height / 2, clip=False)
        x2, y2 = view2d.view_to_region(render_width / 2, render_height / 2, clip=False)
        
        self.frame_x = float(x1)
        self.frame_y = float(y1)
        self.frame_width = float(x2 - x1)
        self.frame_height = float(y2 - y1)
        
        mouse_x = event.mouse_region_x
        mouse_y = event.mouse_region_y
        
        threshold = 5
        closest_guide = None
        closest_distance = threshold
        closest_index = -1
        
        center_x = self.frame_x + self.frame_width / 2
        center_y = self.frame_y + self.frame_height / 2
        
        # Calculate scale factors
        scale_x = self.frame_width / render_width if render_width > 0 else 1.0
        scale_y = self.frame_height / render_height if render_height > 0 else 1.0
        
        for i, guide in enumerate(context.scene.custom_guides):
            if guide.orientation == 'HORIZONTAL':
                # Convert guide position (normalized) to screen pixels
                guide_screen_y = center_y + (guide.position_y * self.frame_height / 2)
                distance = abs(mouse_y - guide_screen_y)
                if distance < closest_distance and self.frame_x <= mouse_x <= self.frame_x + self.frame_width:
                    closest_distance = distance
                    closest_guide = guide
                    closest_index = i
            else:
                # Convert guide position (normalized) to screen pixels
                guide_screen_x = center_x + (guide.position_x * self.frame_width / 2)
                distance = abs(mouse_x - guide_screen_x)
                if distance < closest_distance and self.frame_y <= mouse_y <= self.frame_y + self.frame_height:
                    closest_distance = distance
                    closest_guide = guide
                    closest_index = i
        
        if closest_guide is None:
            # Pass through if no guide clicked so user can select strips
            return {'PASS_THROUGH'}
        
        self.guide = closest_guide
        self.guide_index = closest_index
        self.original_position_x = closest_guide.position_x
        self.original_position_y = closest_guide.position_y
        
        # Set as active guide
        context.scene.vse_guides.active_guide_index = closest_index
        
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class VSE_OT_drag_guide_from_ruler(Operator):
    """Drag to create a guide line from ruler area"""
    bl_idname = "vse.drag_guide_from_ruler"
    bl_label = "Drag Guide Line from Ruler"
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}
    
    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.area.type == 'SEQUENCE_EDITOR' and hasattr(context.scene, 'custom_guides')
    
    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        if event.type == 'MOUSEMOVE':
            if self.guide:
                # Calculate scale factors
                render = context.scene.render
                scale_x = self.frame_width / render.resolution_x if render.resolution_x > 0 else 1.0
                scale_y = self.frame_height / render.resolution_y if render.resolution_y > 0 else 1.0
                
                if self.guide.orientation == 'HORIZONTAL':
                    center_y = self.frame_y + self.frame_height / 2
                    screen_offset_y = event.mouse_region_y - center_y
                    val = screen_offset_y / (self.frame_height / 2)
                    self.guide.position_y = max(-1.0, min(1.0, val))
                else:
                    center_x = self.frame_x + self.frame_width / 2
                    screen_offset_x = event.mouse_region_x - center_x
                    val = screen_offset_x / (self.frame_width / 2)
                    self.guide.position_x = max(-1.0, min(1.0, val))
                context.area.tag_redraw()
            return {'RUNNING_MODAL'}
        
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.guide:
                if self.guide.orientation == 'HORIZONTAL':
                    self.report({'INFO'}, f"Horizontal guide added at Y: {self.guide.position_y:.2f}")
                else:
                    self.report({'INFO'}, f"Vertical guide added at X: {self.guide.position_x:.2f}")
                return {'FINISHED'}
            return {'CANCELLED'}
        
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            if self.guide:
                context.scene.custom_guides.remove(len(context.scene.custom_guides) - 1)
            context.area.tag_redraw()
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}
    
    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        region = context.region
        render = context.scene.render
        render_width = render.resolution_x
        render_height = render.resolution_y
        
        if render_width == 0 or render_height == 0:
            return {'CANCELLED'}
        
        view2d = region.view2d
        x1, y1 = view2d.view_to_region(-render_width / 2, -render_height / 2, clip=False)
        x2, y2 = view2d.view_to_region(render_width / 2, render_height / 2, clip=False)
        
        self.frame_x = float(x1)
        self.frame_y = float(y1)
        self.frame_width = float(x2 - x1)
        self.frame_height = float(y2 - y1)
        
        settings = context.scene.vse_guides
        ruler_size = settings.ruler_size
        
        mouse_x = event.mouse_region_x
        mouse_y = event.mouse_region_y
        
        in_top_ruler = (self.frame_x <= mouse_x <= self.frame_x + self.frame_width and 
                       self.frame_y + self.frame_height <= mouse_y <= self.frame_y + self.frame_height + ruler_size)
        
        in_left_ruler = (self.frame_x - ruler_size <= mouse_x <= self.frame_x and 
                        self.frame_y <= mouse_y <= self.frame_y + self.frame_height)
        
        if not (in_top_ruler or in_left_ruler):
            self.report({'WARNING'}, "Click in ruler area to create guide")
            return {'CANCELLED'}
        
        guide = context.scene.custom_guides.add()
        
        if in_top_ruler:
            guide.orientation = 'HORIZONTAL'
            center_y = self.frame_y + self.frame_height / 2
            val = (mouse_y - center_y) / (self.frame_height / 2)
            guide.position_y = max(-1.0, min(1.0, val))
        else:
            guide.orientation = 'VERTICAL'
            center_x = self.frame_x + self.frame_width / 2
            val = (mouse_x - center_x) / (self.frame_width / 2)
            guide.position_x = max(-1.0, min(1.0, val))
        
        self.guide = guide
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


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


class VSE_OT_export_guides_image(Operator):
    """Export current guides as a PNG image with transparent background"""
    bl_idname = "vse.export_guides_image"
    bl_label = "Export Guides Image"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Path to save the image",
        subtype='FILE_PATH',
        default=""
    )
    
    insert_strip: bpy.props.BoolProperty(
        name="Insert as Strip",
        description="Insert the exported image as a strip in the VSE",
        default=False
    )
    
    def invoke(self, context, event):
        import os
        # Set default filename
        blend_path = bpy.data.filepath
        if blend_path:
            base = os.path.splitext(os.path.basename(blend_path))[0]
        else:
            base = "untitled"
        self.filepath = os.path.join(os.path.dirname(blend_path) if blend_path else "/tmp", f"{base}_guides.png")
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        import numpy as np
        import math
        
        settings, custom_guides, update_func = get_settings_for_context(context)
        
        # Get render resolution
        render = context.scene.render
        width = render.resolution_x
        height = render.resolution_y
        
        if width == 0 or height == 0:
            self.report({'ERROR'}, "Invalid render resolution")
            return {'CANCELLED'}
        
        # Create RGBA image array (transparent background)
        image_data = np.zeros((height, width, 4), dtype=np.float32)
        
        # Get line width from settings
        line_width = settings.line_width
        
        # Helper function to draw anti-aliased thick line into an alpha mask
        def draw_line_to_mask(mask, x0, y0, x1, y1, thickness=None):
            """Draw anti-aliased line into alpha mask using MAX blending"""
            if thickness is None:
                thickness = line_width
            
            # Calculate line vector and length
            dx = x1 - x0
            dy = y1 - y0
            length = math.sqrt(dx * dx + dy * dy)
            
            if length < 0.001:
                return
            
            # Normalize direction
            nx = dx / length
            ny = dy / length
            
            # Calculate bounding box with padding
            half_thick = thickness / 2 + 1
            min_x = max(0, int(min(x0, x1) - half_thick - 1))
            max_x = min(width, int(max(x0, x1) + half_thick + 2))
            min_y = max(0, int(min(y0, y1) - half_thick - 1))
            max_y = min(height, int(max(y0, y1) + half_thick + 2))
            
            if min_x >= max_x or min_y >= max_y:
                return
            
            # Create coordinate grids for the bounding box region
            y_coords, x_coords = np.mgrid[min_y:max_y, min_x:max_x]
            
            # Calculate distance from each pixel to the line segment
            vx = x_coords - x0
            vy = y_coords - y0
            
            # Project onto line direction to get parameter t
            t = (vx * nx + vy * ny)
            t = np.clip(t, 0, length)
            
            # Closest point on line segment
            closest_x = x0 + t * nx
            closest_y = y0 + t * ny
            
            # Distance from pixel to closest point on line
            dist_x = x_coords - closest_x
            dist_y = y_coords - closest_y
            distance = np.sqrt(dist_x * dist_x + dist_y * dist_y)
            
            # Calculate alpha based on distance (anti-aliased edge)
            half_width = thickness / 2
            alpha_mult = np.clip(half_width + 0.5 - distance, 0, 1)
            
            # Only process pixels that have some contribution
            valid_mask = alpha_mult > 0.001
            
            if not np.any(valid_mask):
                return
            
            # Get indices relative to the bounding box
            rel_y, rel_x = np.where(valid_mask)
            
            # Get absolute indices
            abs_y = rel_y + min_y
            abs_x = rel_x + min_x
            
            # Get new alpha values
            new_alphas = alpha_mult[valid_mask]
            
            # Update mask with maximum alpha
            current_alphas = mask[abs_y, abs_x]
            mask[abs_y, abs_x] = np.maximum(current_alphas, new_alphas)

        # Helper to composite accumulated mask onto image
        def composite_mask(mask, color):
            """Composite alpha mask onto main image with given color"""
            if not np.any(mask > 0.001):
                return
                
            r, g, b, a = color
            
            # Get indices where mask has content
            valid_indices = mask > 0.001
            
            # Get alpha values for these pixels (mask * color alpha)
            pixel_alpha = mask[valid_indices] * a
            
            # Get coordinates
            y_indices, x_indices = np.where(valid_indices)
            
            # Current background alpha
            old_a = image_data[y_indices, x_indices, 3]
            
            # Standard over operator
            new_a = pixel_alpha + old_a * (1 - pixel_alpha)
            
            # Avoid division by zero
            nz = new_a > 0.0001
            
            if np.any(nz):
                # Filter indices to only those with non-zero new alpha
                y_nz = y_indices[nz]
                x_nz = x_indices[nz]
                alpha_nz = pixel_alpha[nz]
                old_a_nz = old_a[nz]
                new_a_nz = new_a[nz]
                
                # Composite RGB
                for c, col_val in enumerate([r, g, b]):
                    old_c = image_data[y_nz, x_nz, c]
                    image_data[y_nz, x_nz, c] = (
                        col_val * alpha_nz + old_c * old_a_nz * (1 - alpha_nz)
                    ) / new_a_nz
                
                image_data[y_nz, x_nz, 3] = new_a_nz
            
            # Clear mask for next use
            mask.fill(0)

        # Shared mask buffer
        mask_buffer = np.zeros((height, width), dtype=np.float32)
        
        # Wrapper for draw_line to maintain compatibility with existing logic structure
        # but redirect to mask buffer
        def draw_line(x0, y0, x1, y1, color=None, thickness=None):
            # Note: color argument is ignored here as we draw to mask
            draw_line_to_mask(mask_buffer, x0, y0, x1, y1, thickness)

        # Draw thirds
        if settings.show_thirds:
            color = tuple(settings.thirds_color)
            third_x = width / 3
            third_y = height / 3
            draw_line(third_x, 0, third_x, height)
            draw_line(2 * third_x, 0, 2 * third_x, height)
            draw_line(0, third_y, width, third_y)
            draw_line(0, 2 * third_y, width, 2 * third_y)
            composite_mask(mask_buffer, color)
        
        # Draw golden ratio
        if settings.show_golden:
            color = tuple(settings.golden_color)
            golden = 1.618
            golden_w = width / golden
            golden_h = height / golden
            draw_line(golden_w, 0, golden_w, height)
            draw_line(width - golden_w, 0, width - golden_w, height)
            draw_line(0, golden_h, width, golden_h)
            draw_line(0, height - golden_h, width, height - golden_h)
            composite_mask(mask_buffer, color)
        
        # Draw center
        if settings.show_center:
            color = tuple(settings.center_color)
            cx, cy = width / 2, height / 2
            cross_size = min(width, height) * 0.05
            draw_line(cx - cross_size, cy, cx + cross_size, cy)
            draw_line(cx, cy - cross_size, cx, cy + cross_size)
            composite_mask(mask_buffer, color)
        
        # Draw diagonals
        if settings.show_diagonals:
            color = tuple(settings.diagonals_color)
            draw_line(0, 0, width, height)
            draw_line(width, 0, 0, height)
            composite_mask(mask_buffer, color)
        
        # Draw grid
        if settings.show_grid:
            color = tuple(settings.grid_color)
            divisions = settings.grid_divisions
            
            if settings.grid_square:
                # Square grid - calculate cell size based on smaller dimension
                min_dimension = min(width, height)
                cell_size = min_dimension / divisions
                
                # Calculate how many complete cells fit in each dimension
                h_cells = int(width / cell_size)
                v_cells = int(height / cell_size)
                
                # Center the grid
                h_offset = (width - (h_cells * cell_size)) / 2
                v_offset = (height - (v_cells * cell_size)) / 2
                
                # Grid boundaries
                grid_left = h_offset
                grid_right = h_offset + (h_cells * cell_size)
                grid_bottom = v_offset
                grid_top = v_offset + (v_cells * cell_size)
                
                # Draw outer boundary
                draw_line(grid_left, grid_bottom, grid_right, grid_bottom, thickness=0.5)
                draw_line(grid_right, grid_bottom, grid_right, grid_top, thickness=0.5)
                draw_line(grid_right, grid_top, grid_left, grid_top, thickness=0.5)
                draw_line(grid_left, grid_top, grid_left, grid_bottom, thickness=0.5)
                
                # Vertical lines
                for i in range(1, h_cells):
                    x = grid_left + (cell_size * i)
                    draw_line(x, grid_bottom, x, grid_top, thickness=0.5)
                
                # Horizontal lines
                for i in range(1, v_cells):
                    y = grid_bottom + (cell_size * i)
                    draw_line(grid_left, y, grid_right, y, thickness=0.5)
            else:
                # Regular grid
                for i in range(1, divisions):
                    x = width * i / divisions
                    y = height * i / divisions
                    draw_line(x, 0, x, height, thickness=0.5)
                    draw_line(0, y, width, y, thickness=0.5)
            composite_mask(mask_buffer, color)
        
        # Draw custom guides
        if settings.show_custom_guides:
            cx, cy = width / 2, height / 2
            max_len = max(width, height) * 2
            
            guides_by_color = {}
            for guide in custom_guides:
                col_key = tuple(guide.color)
                if col_key not in guides_by_color:
                    guides_by_color[col_key] = []
                guides_by_color[col_key].append(guide)
            
            for col_key, guides in guides_by_color.items():
                for guide in guides:
                    pivot_x = cx + guide.position_x * width / 2
                    pivot_y = cy + guide.position_y * height / 2
                    
                    if guide.orientation == 'HORIZONTAL':
                        base_angle = 0
                    else:
                        base_angle = math.pi / 2
                    
                    angle = base_angle + guide.rotation
                    dx = math.cos(angle) * max_len
                    dy = math.sin(angle) * max_len
                    
                    draw_line(pivot_x - dx, pivot_y - dy, pivot_x + dx, pivot_y + dy, thickness=1.5)
                
                composite_mask(mask_buffer, col_key)
        
        # Draw golden spiral
        if settings.show_golden_spiral:
            color = tuple(settings.golden_spiral_color)
            phi = 1.61803398875
            
            # Determine dimensions that fit within the frame
            if settings.golden_spiral_fit:
                target_w = width
                target_h = height
                offset_x = 0
                offset_y = 0
            elif width / height > phi:
                target_h = height
                target_w = height * phi
                offset_x = (width - target_w) / 2
                offset_y = 0
            else:
                if width / height < 1/phi:
                    target_w = width
                    target_h = width * phi
                    offset_x = 0
                    offset_y = (height - target_h) / 2
                else:
                    target_w = width
                    target_h = width / phi
                    offset_x = 0
                    offset_y = (height - target_h) / 2
                    if target_h > height:
                        target_h = height
                        target_w = height * phi
                        offset_x = (width - target_w) / 2
                        offset_y = 0
            
            # Generate spiral
            gen_h = 1000.0
            gen_w = gen_h * phi
            
            points = []
            segment_lines = []  # For show_segments feature
            lx, ly = 0.0, 0.0
            lw, lh = gen_w, gen_h
            
            max_iter = settings.golden_spiral_length
            
            for idx in range(max_iter):
                if lw < 1.0 or lh < 1.0:
                    break
                
                mindim = min(lw, lh)
                cycle = idx % 4
                segs = 32
                
                if cycle == 0:
                    radius = mindim
                    center_x = lx + radius
                    center_y = ly
                    start_angle = math.pi
                    end_angle = math.pi / 2
                    # Segment line
                    if settings.golden_spiral_show_segments:
                        segment_lines.append(((lx + radius, ly), (lx + radius, ly + lh)))
                    lx += radius
                    lw -= radius
                elif cycle == 1:
                    radius = mindim
                    center_x = lx
                    center_y = ly + lh - radius
                    start_angle = math.pi / 2
                    end_angle = 0
                    # Segment line
                    if settings.golden_spiral_show_segments:
                        segment_lines.append(((lx, ly + lh - radius), (lx + lw, ly + lh - radius)))
                    lh -= radius
                elif cycle == 2:
                    radius = mindim
                    center_x = lx + lw - radius
                    center_y = ly + lh
                    start_angle = 0
                    end_angle = -math.pi / 2
                    # Segment line
                    if settings.golden_spiral_show_segments:
                        segment_lines.append(((lx + lw - radius, ly), (lx + lw - radius, ly + lh)))
                    lw -= radius
                elif cycle == 3:
                    radius = mindim
                    center_x = lx + lw
                    center_y = ly + radius
                    start_angle = -math.pi / 2
                    end_angle = -math.pi
                    # Segment line
                    if settings.golden_spiral_show_segments:
                        segment_lines.append(((lx, ly + radius), (lx + lw, ly + radius)))
                    ly += radius
                    lh -= radius
                
                for i in range(segs + 1):
                    t = i / segs
                    angle = start_angle + (end_angle - start_angle) * t
                    px = center_x + radius * math.cos(angle)
                    py = center_y + radius * math.sin(angle)
                    points.append((px, py))
            
            # Scale and offset points, then draw
            scale_x = target_w / gen_w
            scale_y = target_h / gen_h
            
            # Helper to transform a point
            def transform_point(px, py):
                if settings.golden_spiral_flip_h:
                    px = gen_w - px
                if settings.golden_spiral_flip_v:
                    py = gen_h - py
                return px * scale_x + offset_x, py * scale_y + offset_y
            
            # Draw spiral curve
            for i in range(len(points) - 1):
                p1x, p1y = transform_point(*points[i])
                p2x, p2y = transform_point(*points[i + 1])
                draw_line(p1x, p1y, p2x, p2y)
            
            # Draw segment lines if enabled
            if settings.golden_spiral_show_segments:
                for (sx1, sy1), (sx2, sy2) in segment_lines:
                    p1x, p1y = transform_point(sx1, sy1)
                    p2x, p2y = transform_point(sx2, sy2)
                    draw_line(p1x, p1y, p2x, p2y)
            
            composite_mask(mask_buffer, color)
        
        # Draw circular thirds
        if settings.show_circular_thirds:
            color = tuple(settings.circular_thirds_color)
            cx, cy = width / 2, height / 2
            
            if settings.circular_thirds_fit:
                radius_x = width / 2
                radius_y = height / 2
            else:
                max_radius = min(width, height) / 2
                radius_x = max_radius
                radius_y = max_radius
            
            num_circles = settings.circular_thirds_count
            for i in range(1, num_circles + 1):
                ratio = i / num_circles
                r_x = radius_x * ratio
                r_y = radius_y * ratio
                segments = 64
                for j in range(segments):
                    angle1 = (2 * math.pi * j) / segments
                    angle2 = (2 * math.pi * (j + 1)) / segments
                    x1 = cx + r_x * math.cos(angle1)
                    y1 = cy + r_y * math.sin(angle1)
                    x2 = cx + r_x * math.cos(angle2)
                    y2 = cy + r_y * math.sin(angle2)
                    draw_line(x1, y1, x2, y2)
            composite_mask(mask_buffer, color)
        
        # Draw vanishing point
        if settings.show_vanishing_point:
            color = tuple(settings.vanishing_point_color)
            vp_x = width * settings.vanishing_point_x
            vp_y = height * settings.vanishing_point_y
            
            # 1. Radial Lines (from VP to frame edges)
            line_count = settings.vanishing_point_lines
            if line_count > 0:
                # line_count is subdivisions per edge (1=corners only, 2=+midpoints, etc.)
                subdivisions = line_count
                
                # Define corners (x, y)
                tl = (0, height)
                tr = (width, height)
                br = (width, 0)
                bl = (0, 0)
                
                # Define edges as (start, end) pairs
                edges = [
                    (tl, tr), # Top
                    (tr, br), # Right
                    (br, bl), # Bottom
                    (bl, tl)  # Left
                ]
                
                for (sx, sy), (ex, ey) in edges:
                    for i in range(subdivisions):
                        t = i / subdivisions
                        # Interpolate point on edge
                        px = sx * (1 - t) + ex * t
                        py = sy * (1 - t) + ey * t
                        draw_line(vp_x, vp_y, px, py)
            
            # 2. Perspective Grid (Concentric rectangles scaling to VP)
            if settings.show_vanishing_point_grid:
                grid_count = settings.vanishing_point_grid_count
                if grid_count > 0:
                    # Frame corners
                    c1x, c1y = 0, 0
                    c2x, c2y = width, 0
                    c3x, c3y = width, height
                    c4x, c4y = 0, height
                    
                    for i in range(1, grid_count + 1):
                        t = i / (grid_count + 1)
                        
                        # Interpolate corners towards VP
                        # p = c + (vp - c) * t = c * (1-t) + vp * t
                        p1x = c1x * (1-t) + vp_x * t
                        p1y = c1y * (1-t) + vp_y * t
                        
                        p2x = c2x * (1-t) + vp_x * t
                        p2y = c2y * (1-t) + vp_y * t
                        
                        p3x = c3x * (1-t) + vp_x * t
                        p3y = c3y * (1-t) + vp_y * t
                        
                        p4x = c4x * (1-t) + vp_x * t
                        p4y = c4y * (1-t) + vp_y * t
                        
                        # Draw rectangle
                        draw_line(p1x, p1y, p2x, p2y)
                        draw_line(p2x, p2y, p3x, p3y)
                        draw_line(p3x, p3y, p4x, p4y)
                        draw_line(p4x, p4y, p1x, p1y)
            
            composite_mask(mask_buffer, color)
        
        # Draw diagonal reciprocals
        if settings.show_diagonal_reciprocals:
            color = tuple(settings.diagonal_reciprocals_color)
            # Main diagonals
            draw_line(0, 0, width, height)
            draw_line(width, 0, 0, height)
            # Reciprocal lines from midpoints (matching drawing.py)
            draw_line(0, height, width/2, 0)
            draw_line(width/2, height, width, 0)
            draw_line(width, height, width/2, 0)
            draw_line(width/2, height, 0, 0)
            draw_line(0, height/2, width, height)
            draw_line(0, height/2, width, 0)
            draw_line(width, height/2, 0, height)
            draw_line(width, height/2, 0, 0)
            composite_mask(mask_buffer, color)
        
        # Draw harmony triangles
        if settings.show_harmony_triangles:
            color = tuple(settings.harmony_triangles_color)
            draw_line(0, 0, width, height)
            w_sq = width * width
            h_sq = height * height
            denom = w_sq + h_sq
            if denom > 0:
                foot_x = (width * h_sq) / denom
                foot_y = (height * h_sq) / denom
                draw_line(0, height, foot_x, foot_y)
                foot_x2 = (width * w_sq) / denom
                foot_y2 = (height * w_sq) / denom
                draw_line(width, 0, foot_x2, foot_y2)
            composite_mask(mask_buffer, color)
        
        # Draw diagonal method (45-degree lines)
        if settings.show_diagonal_method:
            color = tuple(settings.diagonal_method_color)
            min_dim = min(width, height)
            draw_line(0, 0, min_dim, min_dim)
            draw_line(width, 0, width - min_dim, min_dim)
            draw_line(0, height, min_dim, height - min_dim)
            draw_line(width, height, width - min_dim, height - min_dim)
            composite_mask(mask_buffer, color)
        
        # Draw radial symmetry (lines from center through to edges)
        if settings.show_radial_symmetry:
            color = tuple(settings.radial_symmetry_color)
            cx, cy = width / 2, height / 2
            line_count = settings.radial_line_count
            max_radius = math.sqrt((width/2)**2 + (height/2)**2)
            
            for i in range(line_count):
                angle = (2 * math.pi * i) / line_count
                end_x = cx + max_radius * math.cos(angle)
                end_y = cy + max_radius * math.sin(angle)
                draw_line(cx, cy, end_x, end_y)
            composite_mask(mask_buffer, color)
        
        # Draw golden triangle
        if settings.show_golden_triangle:
            color = tuple(settings.golden_triangle_color)
            
            cx, cy = width / 2, height / 2
            
            # Base triangle size (covers frame when scale=1)
            scale = settings.golden_triangle_scale
            triangle_count = settings.golden_triangle_count
            
            # Base size is half the smaller dimension
            base_size = min(width, height) / 2 * scale
            
            # Triangle height (equilateral style)
            tri_h = base_size * math.sqrt(3) / 2
            
            # Rotation helper
            def rotate_point(x, y):
                if settings.golden_triangle_rotation != 0:
                    cos_r = math.cos(settings.golden_triangle_rotation)
                    sin_r = math.sin(settings.golden_triangle_rotation)
                    dx, dy = x - cx, y - cy
                    return cx + dx * cos_r - dy * sin_r, cy + dx * sin_r + dy * cos_r
                return x, y
            
            # Generate nested triangles
            for t in range(triangle_count):
                # Scale factor for this triangle (outer to inner)
                t_scale = 1 - (t / triangle_count) if triangle_count > 1 else 1
                
                # Triangle vertices (pointing up, centered)
                top_x = cx
                top_y = cy + tri_h * 2/3 * t_scale
                bl_x = cx - base_size * t_scale
                bl_y = cy - tri_h * 1/3 * t_scale
                br_x = cx + base_size * t_scale
                br_y = cy - tri_h * 1/3 * t_scale
                
                # Apply rotation
                top_x, top_y = rotate_point(top_x, top_y)
                bl_x, bl_y = rotate_point(bl_x, bl_y)
                br_x, br_y = rotate_point(br_x, br_y)
                
                draw_line(top_x, top_y, bl_x, bl_y)
                draw_line(bl_x, bl_y, br_x, br_y)
                draw_line(br_x, br_y, top_x, top_y)
            
            composite_mask(mask_buffer, color)
        
        # Save image using Blender's API
        img_name = "guides_export_temp"
        if img_name in bpy.data.images:
            bpy.data.images.remove(bpy.data.images[img_name])
        
        img = bpy.data.images.new(img_name, width=width, height=height, alpha=True, float_buffer=True)
        img.pixels = image_data.flatten().tolist()
        img.filepath_raw = self.filepath
        img.file_format = 'PNG'
        img.save()
        
        self.report({'INFO'}, f"Exported guides to: {self.filepath}")
        
        # Insert as strip if requested
        if self.insert_strip:
            # Find sequencer
            if context.scene.sequence_editor is None:
                context.scene.sequence_editor_create()
            
            sed = context.scene.sequence_editor
            
            # Find empty channel - use strips_all for Blender 5.0
            max_channel = 1
            if hasattr(sed, 'strips_all'):
                for seq in sed.strips_all:
                    if seq.channel >= max_channel:
                        max_channel = seq.channel + 1
            elif hasattr(sed, 'sequences_all'):
                for seq in sed.sequences_all:
                    if seq.channel >= max_channel:
                        max_channel = seq.channel + 1
            
            # Use operator to add image strip (most reliable across versions)
            try:
                # Ensure we're in the right context
                bpy.ops.sequencer.image_strip_add(
                    directory=os.path.dirname(self.filepath) + os.sep,
                    files=[{"name": os.path.basename(self.filepath)}],
                    frame_start=context.scene.frame_current,
                    channel=max_channel
                )
                
                # Find the newly added strip and configure it
                if hasattr(sed, 'strips_all'):
                    strips = sed.strips_all
                elif hasattr(sed, 'sequences_all'):
                    strips = sed.sequences_all
                else:
                    strips = []
                
                for strip in strips:
                    if hasattr(strip, 'filepath') and strip.filepath and self.filepath in strip.filepath:
                        strip.frame_final_duration = context.scene.frame_end - context.scene.frame_start + 1
                        strip.blend_type = 'ALPHA_OVER'
                        strip.name = "Guides"
                        break
                
                self.report({'INFO'}, f"Added guides as image strip in channel {max_channel}")
            except Exception as e:
                self.report({'WARNING'}, f"Exported image but couldn't add strip: {e}")
        
        # Clean up temp image
        bpy.data.images.remove(img)
        
        return {'FINISHED'}


# Registration
classes = (
    VSE_OT_move_custom_guide,
    VSE_OT_drag_guide_from_ruler,
    VSE_OT_add_custom_guide,
    VSE_OT_remove_custom_guide,
    VSE_OT_clear_custom_guides,
    VSE_OT_move_guide_up,
    VSE_OT_move_guide_down,
    VSE_OT_reset_guides,
    VSE_OT_toggle_all_guides,
    VSE_OT_export_guides_image,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)



def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
