"""GPU drawing functions for 3D Viewport camera guides"""

import bpy
import gpu
import math
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Matrix
from bpy_extras import view3d_utils


def get_camera_frame_coordinates(context, region, region_data):
    """
    Get camera frame coordinates in screen space using proper camera projection.
    This accounts for camera parent transforms and all camera properties.
    """
    if region_data.view_perspective != 'CAMERA':
        return None
    
    scene = context.scene
    camera = scene.camera
    
    if not camera:
        return None
    
    render = scene.render
    render_width = render.resolution_x
    render_height = render.resolution_y
    
    if render_width == 0 or render_height == 0:
        return None
    
    # Get camera data
    camera_obj = camera
    
    corners_camera = camera.data.view_frame(scene=scene)
    
    corners_world = [camera_obj.matrix_world @ corner for corner in corners_camera]
    
    # Project world coordinates to region (screen) coordinates
    corners_region = []
    for world_co in corners_world:
        region_co = view3d_utils.location_3d_to_region_2d(region, region_data, world_co)
        if region_co is None:
            # Corner is behind camera or outside view
            return None
        corners_region.append(region_co)
    
    # Calculate bounding box of the projected corners
    min_x = min(co.x for co in corners_region)
    max_x = max(co.x for co in corners_region)
    min_y = min(co.y for co in corners_region)
    max_y = max(co.y for co in corners_region)
    
    frame_x = float(min_x)
    frame_y = float(min_y)
    frame_width = float(max_x - min_x)
    frame_height = float(max_y - min_y)
    
    return frame_x, frame_y, frame_width, frame_height


def draw_camera_guides():
    """Main drawing callback for 3D Viewport camera guides"""
    try:
        context = bpy.context
        
        # Get scene and active camera
        scene = context.scene
        camera = scene.camera
        
        if not camera or not camera.data:
            return
        
        # Check if camera has guide settings
        if not hasattr(camera.data, 'camera_guides'):
            return
        
        settings = camera.data.camera_guides
        
        # Check if any guides need to be drawn
        if not any([
            settings.show_thirds,
            settings.show_golden,
            settings.show_center,
            settings.show_diagonals,
            settings.show_grid,
            settings.show_custom_guides,
            settings.show_golden_spiral,
            settings.show_golden_triangle,
            settings.show_circular_thirds,
            settings.show_radial_symmetry,
            settings.show_vanishing_point,
            settings.show_diagonal_reciprocals,
            settings.show_harmony_triangles,
            settings.show_diagonal_method,
            settings.show_rulers
        ]):
            return
        
        # Get current area and space
        area = context.area
        if not area or area.type != 'VIEW_3D':
            return
        
        space = context.space_data
        if not space or space.type != 'VIEW_3D':
            return
        
        region = context.region
        if not region or region.type != 'WINDOW':
            return
        
        region_data = context.region_data
        if not region_data:
            return
        
        # Only draw in camera view
        if region_data.view_perspective != 'CAMERA':
            return
        
        # Get camera frame coordinates
        coords = get_camera_frame_coordinates(context, region, region_data)
        if not coords:
            return
        
        frame_x, frame_y, frame_width, frame_height = coords
        
        # Set up orthographic projection for 2D drawing in POST_VIEW
        width = region.width
        height = region.height
        
        gpu.matrix.push()
        gpu.matrix.push_projection()
        
        projection_matrix = Matrix([
            [2.0 / width, 0, 0, -1],
            [0, 2.0 / height, 0, -1],
            [0, 0, -1, 0],
            [0, 0, 0, 1]
        ])
        
        gpu.matrix.load_projection_matrix(projection_matrix)
        gpu.matrix.load_identity()
        
        try:
            # Import drawing functions from the main drawing module
            from . import drawing
            
            # Draw rulers
            if settings.show_rulers:
                drawing.draw_rulers_base(context, settings, frame_x, frame_y, frame_width, frame_height)
            
            # Draw grid
            if settings.show_grid:
                drawing.draw_grid(settings, frame_x, frame_y, frame_width, frame_height)
            
            # Draw guides
            if any([settings.show_thirds, settings.show_golden, settings.show_center, 
                    settings.show_diagonals, settings.show_golden_spiral, 
                    settings.show_golden_triangle, settings.show_circular_thirds,
                    settings.show_radial_symmetry, settings.show_vanishing_point,
                    settings.show_diagonal_reciprocals, settings.show_harmony_triangles,
                    settings.show_diagonal_method]):
                drawing.draw_composition_guides(settings, frame_x, frame_y, frame_width, frame_height)
            
            # Draw custom guides
            if settings.show_custom_guides:
                drawing.draw_custom_guides(context, settings, frame_x, frame_y, frame_width, frame_height, 
                                         custom_guides_list=camera.data.custom_camera_guides)
        finally:
            # Restore matrices
            gpu.matrix.pop_projection()
            gpu.matrix.pop()
    
    except Exception as e:
        print(f"3D Viewport Guides draw error: {e}")
        import traceback
        traceback.print_exc()
