"""GPU drawing functions for VSE Guides addon"""

import bpy
import gpu
import blf
import math
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Matrix


def get_frame_coordinates(context: bpy.types.Context, region: bpy.types.Region) -> tuple[float, float, float, float]:
    """
    Get frame coordinates in screen space with center at (0,0).
    """
    render = context.scene.render
    render_width = render.resolution_x
    render_height = render.resolution_y
    
    # Account for pixel aspect ratio
    pixel_aspect = render.pixel_aspect_x / render.pixel_aspect_y if render.pixel_aspect_y != 0 else 1.0
    
    # Apply pixel aspect ratio to width
    adjusted_width = render_width * pixel_aspect
    adjusted_height = render_height
    
    if adjusted_width == 0 or adjusted_height == 0:
        return 0.0, 0.0, float(region.width), float(region.height)
    
    # Use view2d to convert preview coordinates to region coordinates
    view2d = region.view2d
    
    # Frame boundaries in preview space with center at (0,0)
    # Bottom-left corner
    x1, y1 = view2d.view_to_region(-adjusted_width / 2, -adjusted_height / 2, clip=False)
    # Top-right corner
    x2, y2 = view2d.view_to_region(adjusted_width / 2, adjusted_height / 2, clip=False)
    
    frame_x = float(x1)
    frame_y = float(y1)
    frame_width = float(x2 - x1)
    frame_height = float(y2 - y1)
    
    return frame_x, frame_y, frame_width, frame_height


def clip_line_to_rect(p1: Vector, p2: Vector, rect_x: float, rect_y: float, 
                        rect_width: float, rect_height: float) -> tuple[Vector, Vector] | None:
    """
    Clip a line segment to a rectangle using Cohen-Sutherland algorithm.
    """
    # Define region codes
    INSIDE = 0  # 0000
    LEFT = 1    # 0001
    RIGHT = 2   # 0010
    BOTTOM = 4  # 0100
    TOP = 8     # 1000
    
    def compute_code(x, y):
        code = INSIDE
        if x < rect_x:
            code |= LEFT
        elif x > rect_x + rect_width:
            code |= RIGHT
        if y < rect_y:
            code |= BOTTOM
        elif y > rect_y + rect_height:
            code |= TOP
        return code
    
    # Make copies to avoid modifying originals
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y
    
    code1 = compute_code(x1, y1)
    code2 = compute_code(x2, y2)
    
    accept = False
    
    while True:
        if code1 == 0 and code2 == 0:
            # Both points inside
            accept = True
            break
        elif (code1 & code2) != 0:
            # Both points share an outside region, line is completely outside
            break
        else:
            # Line needs clipping
            # Pick a point outside the rectangle
            code_out = code1 if code1 != 0 else code2
            
            # Find intersection point
            if code_out & TOP:
                x = x1 + (x2 - x1) * (rect_y + rect_height - y1) / (y2 - y1)
                y = rect_y + rect_height
            elif code_out & BOTTOM:
                x = x1 + (x2 - x1) * (rect_y - y1) / (y2 - y1)
                y = rect_y
            elif code_out & RIGHT:
                y = y1 + (y2 - y1) * (rect_x + rect_width - x1) / (x2 - x1)
                x = rect_x + rect_width
            elif code_out & LEFT:
                y = y1 + (y2 - y1) * (rect_x - x1) / (x2 - x1)
                x = rect_x
            
            # Replace point outside rectangle with intersection point
            if code_out == code1:
                x1, y1 = x, y
                code1 = compute_code(x1, y1)
            else:
                x2, y2 = x, y
                code2 = compute_code(x2, y2)
    
    if accept:
        return (Vector((x1, y1, 0)), Vector((x2, y2, 0)))
    else:
        return None



def draw_guides_view():
    """
    Draw guides and grid in POST_VIEW context.
    This ensures they are drawn in the scene space and appear behind gizmos.
    """
    try:
        context = bpy.context
        
        # Check if we have vse_guides settings
        if not hasattr(context.scene, 'vse_guides'):
            return
        
        settings = context.scene.vse_guides
        
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
        if not area or area.type != 'SEQUENCE_EDITOR':
            return
        
        space = context.space_data
        if not space or space.type != 'SEQUENCE_EDITOR':
            return
        
        # Only draw in preview region
        if space.view_type == 'SEQUENCER':
            return
            
        region = context.region
        if not region or region.type != 'PREVIEW':
             if region.type != 'WINDOW':
                 return
        
        # Set up orthographic projection for Screen Space drawing
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
            # Get frame coordinates in Screen Space
            frame_x, frame_y, frame_width, frame_height = get_frame_coordinates(context, region)
            
            # Draw rulers
            if settings.show_rulers:
                draw_rulers_base(context, settings, frame_x, frame_y, frame_width, frame_height)
            
            # Draw grid
            if settings.show_grid:
                draw_grid(settings, frame_x, frame_y, frame_width, frame_height)
            
            # Draw guides
            if any([settings.show_thirds, settings.show_golden, settings.show_center, 
                    settings.show_diagonals, settings.show_golden_spiral, 
                    settings.show_golden_triangle, settings.show_circular_thirds,
                    settings.show_radial_symmetry, settings.show_vanishing_point,
                    settings.show_diagonal_reciprocals, settings.show_harmony_triangles,
                    settings.show_diagonal_method]):
                draw_composition_guides(settings, frame_x, frame_y, frame_width, frame_height)
            
            # Draw custom guides
            if settings.show_custom_guides:
                draw_custom_guides(context, settings, frame_x, frame_y, frame_width, frame_height)
                
        finally:
            gpu.matrix.pop_projection()
            gpu.matrix.pop()
            
    except Exception as e:
        print(f"VSE Guides (View) draw error: {e}")
        import traceback
        traceback.print_exc()


def draw_rulers_pixel():
    """
    Draw rulers in POST_PIXEL context.
    This ensures they are drawn in screen space and stay on top as UI elements.
    """
    try:
        context = bpy.context
        
        if not hasattr(context.scene, 'vse_guides'):
            return
            
        settings = context.scene.vse_guides
        
        if not settings.show_rulers:
            return
            
        area = context.area
        if not area or area.type != 'SEQUENCE_EDITOR':
            return
            
        space = context.space_data
        if not space or space.type != 'SEQUENCE_EDITOR':
            return
            
        region = context.region
        if not region:
            return
            
        if space.view_type == 'SEQUENCER':
            return
            
        if not hasattr(region, 'view2d'):
            return
            
        if region.type not in {'WINDOW', 'PREVIEW'}:
            return
            
        width = region.width
        height = region.height
        
        if width <= 0 or height <= 0:
            return
            
        # Get frame coordinates in screen space for rulers
        frame_x, frame_y, frame_width, frame_height = get_frame_coordinates(context, region)
        
        draw_rulers_base(context, settings, frame_x, frame_y, frame_width, frame_height)
        
    except Exception as e:
        print(f"VSE Guides (Pixel) draw error: {e}")
        import traceback
        traceback.print_exc()


def draw_grid(settings: bpy.types.PropertyGroup, frame_x: float, frame_y: float, 
              frame_width: float, frame_height: float) -> None:
    """Draw grid overlay"""
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(0.5)
    
    lines = []
    divisions = settings.grid_divisions
    
    if settings.grid_square:
        # Square grid - calculate cell size based on smaller dimension
        min_dimension = min(frame_width, frame_height)
        cell_size = min_dimension / divisions
        
        # Calculate how many complete cells fit in each dimension
        h_cells = int(frame_width / cell_size)
        v_cells = int(frame_height / cell_size)
        
        # Center the grid
        h_offset = (frame_width - (h_cells * cell_size)) / 2
        v_offset = (frame_height - (v_cells * cell_size)) / 2
        
        # Calculate grid boundaries
        grid_left = frame_x + h_offset
        grid_right = frame_x + h_offset + (h_cells * cell_size)
        grid_bottom = frame_y + v_offset
        grid_top = frame_y + v_offset + (v_cells * cell_size)
        
        # Draw outer boundary of square grid area
        lines.extend([
            Vector((grid_left, grid_bottom, 0)),
            Vector((grid_right, grid_bottom, 0)),
            Vector((grid_right, grid_bottom, 0)),
            Vector((grid_right, grid_top, 0)),
            Vector((grid_right, grid_top, 0)),
            Vector((grid_left, grid_top, 0)),
            Vector((grid_left, grid_top, 0)),
            Vector((grid_left, grid_bottom, 0))
        ])
        
        # Vertical lines (only within square grid area)
        for i in range(1, h_cells):
            x = grid_left + (cell_size * i)
            lines.append(Vector((x, grid_bottom, 0)))
            lines.append(Vector((x, grid_top, 0)))
        
        # Horizontal lines (only within square grid area)
        for i in range(1, v_cells):
            y = grid_bottom + (cell_size * i)
            lines.append(Vector((grid_left, y, 0)))
            lines.append(Vector((grid_right, y, 0)))
    else:
        # Regular grid - divide frame evenly
        # Vertical lines
        for i in range(1, divisions):
            x = frame_x + (frame_width / divisions) * i
            lines.append(Vector((x, frame_y, 0)))
            lines.append(Vector((x, frame_y + frame_height, 0)))
        
        # Horizontal lines
        for i in range(1, divisions):
            y = frame_y + (frame_height / divisions) * i
            lines.append(Vector((frame_x, y, 0)))
            lines.append(Vector((frame_x + frame_width, y, 0)))
    
    if lines:
        batch = batch_for_shader(shader, 'LINES', {"pos": lines})
        shader.bind()
        grid_color = (settings.grid_color[0], settings.grid_color[1], 
                     settings.grid_color[2], settings.grid_color[3])
        shader.uniform_float("color", grid_color)
        batch.draw(shader)
    
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')


def draw_custom_guides(context: bpy.types.Context, settings: bpy.types.PropertyGroup, 
                      frame_x: float, frame_y: float, frame_width: float, frame_height: float,
                      custom_guides_list=None) -> None:
    """
    Draw custom draggable guides.
    Optimized to batch lines by color to reduce draw calls.
    """
    if custom_guides_list is None:
        if not hasattr(context.scene, 'custom_guides'):
            return
        custom_guides_list = context.scene.custom_guides
    
    lines_by_color = {}

    center_x = frame_x + frame_width / 2
    center_y = frame_y + frame_height / 2
    
    # Calculate scale factors (Screen Pixels per Image Pixel)
    render = context.scene.render
    scale_x = frame_width / render.resolution_x if render.resolution_x > 0 else 1.0
    scale_y = frame_height / render.resolution_y if render.resolution_y > 0 else 1.0
    
    # Pre-calculate max length needed
    max_length = max(frame_width, frame_height) * 3
    
    for guide in custom_guides_list:
        # Calculate pivot point in screen space
        pivot_x = center_x + (guide.position_x * frame_width / 2)
        pivot_y = center_y + (guide.position_y * frame_height / 2)
        
        # Base rotation from orientation
        base_angle = 0
        if guide.orientation == 'VERTICAL':
            base_angle = math.radians(90)
            
        # Total rotation
        total_angle = base_angle + guide.rotation
        
        # Calculate endpoints based on angle
        dx = max_length * math.cos(total_angle)
        dy = max_length * math.sin(total_angle)
        
        p1 = Vector((pivot_x - dx, pivot_y - dy, 0))
        p2 = Vector((pivot_x + dx, pivot_y + dy, 0))
        
        # Clip to frame boundaries if enabled
        final_line = None
        if settings.hide_guides_outside_frame:
            clipped = clip_line_to_rect(
                p1, p2,
                frame_x, frame_y, frame_width, frame_height
            )
            if clipped:
                final_line = clipped
        else:
            final_line = (p1, p2)
            
        if final_line:
            # Convert color to tuple for dictionary key
            color_key = tuple(guide.color)
            if color_key not in lines_by_color:
                lines_by_color[color_key] = []
            lines_by_color[color_key].append(final_line)
    
    # Draw batches
    if lines_by_color:
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(1.5)
        shader.bind()
        
        for color, lines in lines_by_color.items():
            vertices = []
            for p1, p2 in lines:
                vertices.append(p1)
                vertices.append(p2)
            
            if vertices:
                batch = batch_for_shader(shader, 'LINES', {"pos": vertices})
                shader.uniform_float("color", color)
                batch.draw(shader)
    
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')


def draw_composition_guides(settings: bpy.types.PropertyGroup, frame_x: float, frame_y: float, 
                            frame_width: float, frame_height: float) -> None:
    """Draw the composition guide lines inside frame coordinates"""
    
    # Prepare shader
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(settings.line_width)
    
    # Helper to draw a batch of lines with a specific color
    def draw_lines(lines, color):
        if not lines:
            return
        vertices = []
        for line_start, line_end in lines:
            # Clip lines to frame boundaries if enabled
            if settings.hide_guides_outside_frame:
                # Clip line to frame boundaries
                clipped = clip_line_to_rect(
                    line_start, line_end,
                    frame_x, frame_y, frame_width, frame_height
                )
                if clipped:
                    vertices.append(clipped[0])
                    vertices.append(clipped[1])
            else:
                vertices.append(line_start)
                vertices.append(line_end)
        
        if not vertices:
            return
            
        batch = batch_for_shader(shader, 'LINES', {"pos": vertices})
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)

    # Rule of thirds
    if settings.show_thirds:
        lines = []
        third_w = frame_width / 3
        third_h = frame_height / 3
        
        # Vertical lines
        lines.append((Vector((frame_x + third_w, frame_y, 0)), 
                     Vector((frame_x + third_w, frame_y + frame_height, 0))))
        lines.append((Vector((frame_x + 2 * third_w, frame_y, 0)), 
                     Vector((frame_x + 2 * third_w, frame_y + frame_height, 0))))
        
        # Horizontal lines
        lines.append((Vector((frame_x, frame_y + third_h, 0)), 
                     Vector((frame_x + frame_width, frame_y + third_h, 0))))
        lines.append((Vector((frame_x, frame_y + 2 * third_h, 0)), 
                     Vector((frame_x + frame_width, frame_y + 2 * third_h, 0))))
        
        draw_lines(lines, settings.thirds_color)
    
    # Golden ratio
    if settings.show_golden:
        lines = []
        golden = 1.618
        golden_w = frame_width / golden
        golden_h = frame_height / golden
        
        # Vertical lines
        lines.append((Vector((frame_x + golden_w, frame_y, 0)), 
                     Vector((frame_x + golden_w, frame_y + frame_height, 0))))
        lines.append((Vector((frame_x + frame_width - golden_w, frame_y, 0)), 
                     Vector((frame_x + frame_width - golden_w, frame_y + frame_height, 0))))
        
        # Horizontal lines
        lines.append((Vector((frame_x, frame_y + golden_h, 0)), 
                     Vector((frame_x + frame_width, frame_y + golden_h, 0))))
        lines.append((Vector((frame_x, frame_y + frame_height - golden_h, 0)), 
                     Vector((frame_x + frame_width, frame_y + frame_height - golden_h, 0))))
        
        draw_lines(lines, settings.golden_color)
    
    # Center guides (cross)
    if settings.show_center:
        lines = []
        center_x = frame_x + frame_width / 2
        center_y = frame_y + frame_height / 2
        
        # Small cross at center
        cross_size = min(frame_width, frame_height) * 0.05
        lines.append((Vector((center_x - cross_size, center_y, 0)), 
                     Vector((center_x + cross_size, center_y, 0))))
        lines.append((Vector((center_x, center_y - cross_size, 0)), 
                     Vector((center_x, center_y + cross_size, 0))))
        
        draw_lines(lines, settings.center_color)
    
    # Diagonals
    if settings.show_diagonals:
        lines = []
        lines.append((Vector((frame_x, frame_y, 0)), 
                     Vector((frame_x + frame_width, frame_y + frame_height, 0))))
        lines.append((Vector((frame_x + frame_width, frame_y, 0)), 
                     Vector((frame_x, frame_y + frame_height, 0))))
        
        draw_lines(lines, settings.diagonals_color)
    
    # Golden Spiral
    if settings.show_golden_spiral:
        lines = []
        # Calculate the ideal bounding box for the spiral to maintain Golden Ratio
        phi = 1.61803398875
        
        if settings.golden_spiral_fit:
            # Fit to frame: use frame dimensions as target
            target_w = frame_width
            target_h = frame_height
            offset_x = 0
            offset_y = 0
        elif frame_width / frame_height > phi:
            # Frame is wider than needed, fit to height
            target_h = frame_height
            target_w = frame_height * phi
            offset_x = (frame_width - target_w) / 2
            offset_y = 0
        else:
            # Frame is taller than needed (or close enough), fit to width
            if frame_width / frame_height < 1/phi:
                 # Very tall frame
                 target_w = frame_width
                 target_h = frame_width * phi
                 offset_x = 0
                 offset_y = (frame_height - target_h) / 2
            else:
                 # Standard fit
                 target_w = frame_width
                 target_h = frame_width / phi
                 offset_x = 0
                 offset_y = (frame_height - target_h) / 2
                 
                 # If that makes it too tall, fit to height instead
                 if target_h > frame_height:
                     target_h = frame_height
                     target_w = frame_height * phi
                     offset_x = (frame_width - target_w) / 2
                     offset_y = 0

        gen_h = 1000.0
        gen_w = gen_h * phi
        
        points = []
        rect_lines = []
        
        # Working coordinates
        lx, ly = 0.0, 0.0
        lw, lh = gen_w, gen_h
        
        # Limit iterations
        max_iter = settings.golden_spiral_length
        
        for idx in range(max_iter):
            if lw < 1.0 or lh < 1.0:
                break
                
            mindim = min(lw, lh)
            cycle = idx % 4
            segs = 32
            
            if cycle == 0:  # Left
                radius = mindim
                center_x = lx + radius
                center_y = ly
                start_angle = math.pi
                end_angle = math.pi / 2
                
                if settings.golden_spiral_show_segments:
                    rect_lines.append((Vector((lx + radius, ly, 0)), Vector((lx + radius, ly + lh, 0))))
                
                lx += radius
                lw -= radius
                
            elif cycle == 1:  # Top
                radius = mindim
                center_x = lx
                center_y = ly + lh - radius
                start_angle = math.pi / 2
                end_angle = 0
                
                if settings.golden_spiral_show_segments:
                    rect_lines.append((Vector((lx, ly + lh - radius, 0)), Vector((lx + lw, ly + lh - radius, 0))))
                
                lh -= radius
                
            elif cycle == 2:  # Right
                radius = mindim
                center_x = lx + lw - radius
                center_y = ly + lh
                start_angle = 0
                end_angle = -math.pi / 2
                
                if settings.golden_spiral_show_segments:
                    rect_lines.append((Vector((lx + lw - radius, ly, 0)), Vector((lx + lw - radius, ly + lh, 0))))
                
                lw -= radius
                
            elif cycle == 3:  # Bottom
                radius = mindim
                center_x = lx + lw
                center_y = ly + radius
                start_angle = -math.pi / 2
                end_angle = -math.pi
                
                if settings.golden_spiral_show_segments:
                    rect_lines.append((Vector((lx, ly + radius, 0)), Vector((lx + lw, ly + radius, 0))))
                
                ly += radius
                lh -= radius
            
            for i in range(segs + 1):
                t = i / segs
                angle = start_angle + (end_angle - start_angle) * t
                px = center_x + radius * math.cos(angle)
                py = center_y + radius * math.sin(angle)
                points.append(Vector((px, py, 0)))
        
        # Transform and add all lines
        all_lines_to_transform = []
        
        if len(points) > 1:
            for i in range(len(points) - 1):
                all_lines_to_transform.append((points[i], points[i+1]))
        
        if settings.golden_spiral_show_segments:
            all_lines_to_transform.extend(rect_lines)
        
        # Calculate scale factors
        scale_x = target_w / gen_w
        scale_y = target_h / gen_h
        
        for p1_orig, p2_orig in all_lines_to_transform:
            p1 = p1_orig.copy()
            p2 = p2_orig.copy()
            
            # Apply flips (in local space of the spiral rect)
            if settings.golden_spiral_flip_h:
                p1.x = gen_w - p1.x
                p2.x = gen_w - p2.x
            
            if settings.golden_spiral_flip_v:
                p1.y = gen_h - p1.y
                p2.y = gen_h - p2.y
            
            # Apply scaling to target dimensions
            p1.x *= scale_x
            p1.y *= scale_y
            p2.x *= scale_x
            p2.y *= scale_y
            
            # Apply global offset (frame position + centering offset)
            p1.x += frame_x + offset_x
            p1.y += frame_y + offset_y
            p2.x += frame_x + offset_x
            p2.y += frame_y + offset_y
            
            lines.append((p1, p2))
            
        draw_lines(lines, settings.golden_spiral_color)

    
    # Golden Triangle
    if settings.show_golden_triangle:
        lines = []
        
        center_x = frame_x + frame_width / 2
        center_y = frame_y + frame_height / 2
        
        # Base triangle size (covers frame when scale=1)
        scale = settings.golden_triangle_scale
        triangle_count = settings.golden_triangle_count
        
        # Base size is half the smaller dimension
        base_size = min(frame_width, frame_height) / 2 * scale
        
        # Triangle height (equilateral style)
        tri_h = base_size * math.sqrt(3) / 2
        
        # Generate nested triangles
        for t in range(triangle_count):
            # Scale factor for this triangle (outer to inner)
            t_scale = 1 - (t / triangle_count) if triangle_count > 1 else 1
            
            # Triangle vertices (pointing up, centered)
            top_x = center_x
            top_y = center_y + tri_h * 2/3 * t_scale
            bl_x = center_x - base_size * t_scale
            bl_y = center_y - tri_h * 1/3 * t_scale
            br_x = center_x + base_size * t_scale
            br_y = center_y - tri_h * 1/3 * t_scale
            
            # Apply rotation
            if settings.golden_triangle_rotation != 0:
                pivot = Vector((center_x, center_y, 0))
                rot_mat = Matrix.Rotation(settings.golden_triangle_rotation, 4, 'Z')
                
                p1 = Vector((top_x, top_y, 0))
                p2 = Vector((bl_x, bl_y, 0))
                p3 = Vector((br_x, br_y, 0))
                
                p1 = pivot + (rot_mat @ (p1 - pivot))
                p2 = pivot + (rot_mat @ (p2 - pivot))
                p3 = pivot + (rot_mat @ (p3 - pivot))
                
                lines.extend([
                    (p1, p2),
                    (p2, p3),
                    (p3, p1)
                ])
            else:
                lines.extend([
                    (Vector((top_x, top_y, 0)), Vector((bl_x, bl_y, 0))),
                    (Vector((bl_x, bl_y, 0)), Vector((br_x, br_y, 0))),
                    (Vector((br_x, br_y, 0)), Vector((top_x, top_y, 0)))
                ])
        
        draw_lines(lines, settings.golden_triangle_color)
    
    # Radial Symmetry
    if settings.show_radial_symmetry:
        lines = []
        center_x = frame_x + frame_width / 2
        center_y = frame_y + frame_height / 2
        max_radius = math.sqrt((frame_width / 2) ** 2 + (frame_height / 2) ** 2)
        
        for i in range(settings.radial_line_count):
            angle = (2 * math.pi * i) / settings.radial_line_count
            end_x = center_x + max_radius * math.cos(angle)
            end_y = center_y + max_radius * math.sin(angle)
            lines.append((Vector((center_x, center_y, 0)), Vector((end_x, end_y, 0))))
            
        draw_lines(lines, settings.radial_symmetry_color)
    
    # Vanishing Point Grid
    if settings.show_vanishing_point:
        lines = []
        vp_x = frame_x + frame_width * settings.vanishing_point_x
        vp_y = frame_y + frame_height * settings.vanishing_point_y
        
        # 1. Radial Lines (from VP to frame edges)
        line_count = settings.vanishing_point_lines
        if line_count > 0:
            # line_count is subdivisions per edge (1=corners only, 2=+midpoints, etc.)
            subdivisions = line_count
            
            # Define corners
            tl = Vector((frame_x, frame_y + frame_height, 0))
            tr = Vector((frame_x + frame_width, frame_y + frame_height, 0))
            br = Vector((frame_x + frame_width, frame_y, 0))
            bl = Vector((frame_x, frame_y, 0))
            
            # Define edges as (start, end) pairs
            edges = [
                (tl, tr), # Top
                (tr, br), # Right
                (br, bl), # Bottom
                (bl, tl)  # Left
            ]
            
            vp = Vector((vp_x, vp_y, 0))
            
            for start_p, end_p in edges:
                for i in range(subdivisions):
                    t = i / subdivisions
                    # Interpolate point on edge
                    p = start_p.lerp(end_p, t)
                    lines.append((vp, p))
        
        # 2. Perspective Grid (Concentric rectangles scaling to VP)
        if settings.show_vanishing_point_grid:
            grid_count = settings.vanishing_point_grid_count
            if grid_count > 0:
                
                # Frame corners
                c1 = Vector((frame_x, frame_y, 0))
                c2 = Vector((frame_x + frame_width, frame_y, 0))
                c3 = Vector((frame_x + frame_width, frame_y + frame_height, 0))
                c4 = Vector((frame_x, frame_y + frame_height, 0))
                
                vp = Vector((vp_x, vp_y, 0))
                
                for i in range(1, grid_count + 1):
                    # Non-linear spacing looks better for perspective (1/z)
                    t = i / (grid_count + 1)
                    
                    # Interpolate corners towards VP
                    p1 = c1.lerp(vp, t)
                    p2 = c2.lerp(vp, t)
                    p3 = c3.lerp(vp, t)
                    p4 = c4.lerp(vp, t)
                    
                    # Draw rectangle
                    lines.append((p1, p2))
                    lines.append((p2, p3))
                    lines.append((p3, p4))
                    lines.append((p4, p1))
            
        draw_lines(lines, settings.vanishing_point_color)
    
    # Circular Rule of Thirds
    if settings.show_circular_thirds:
        lines = []
        center_x = frame_x + frame_width / 2
        center_y = frame_y + frame_height / 2
        
        if settings.circular_thirds_fit:
            # Fit to frame (ellipses)
            radius_x = frame_width / 2
            radius_y = frame_height / 2
        else:
            # Standard circles
            max_radius = min(frame_width, frame_height) / 2
            radius_x = max_radius
            radius_y = max_radius
        
        # Draw concentric circles/ellipses based on count
        num_circles = settings.circular_thirds_count
        for i in range(1, num_circles + 1):
            ratio = i / num_circles
            r_x = radius_x * ratio
            r_y = radius_y * ratio
            segments = 64
            for j in range(segments):
                angle1 = (2 * math.pi * j) / segments
                angle2 = (2 * math.pi * (j + 1)) / segments
                x1 = center_x + r_x * math.cos(angle1)
                y1 = center_y + r_y * math.sin(angle1)
                x2 = center_x + r_x * math.cos(angle2)
                y2 = center_y + r_y * math.sin(angle2)
                lines.append((Vector((x1, y1, 0)), Vector((x2, y2, 0))))
                
        draw_lines(lines, settings.circular_thirds_color)
    
    # Diagonal Reciprocals
    if settings.show_diagonal_reciprocals:
        lines = []
        
        # Main diagonals (corner to corner)
        lines.append((Vector((frame_x, frame_y, 0)), 
                     Vector((frame_x + frame_width, frame_y + frame_height, 0))))
        lines.append((Vector((frame_x + frame_width, frame_y, 0)), 
                     Vector((frame_x, frame_y + frame_height, 0))))
        
        # Reciprocal diagonals from midpoints
        # From top-left to bottom-center
        lines.append((Vector((frame_x, frame_y + frame_height, 0)),
                     Vector((frame_x + frame_width / 2, frame_y, 0))))
        # From top-center to bottom-right
        lines.append((Vector((frame_x + frame_width / 2, frame_y + frame_height, 0)),
                     Vector((frame_x + frame_width, frame_y, 0))))
        # From top-right to bottom-center
        lines.append((Vector((frame_x + frame_width, frame_y + frame_height, 0)),
                     Vector((frame_x + frame_width / 2, frame_y, 0))))
        # From top-center to bottom-left
        lines.append((Vector((frame_x + frame_width / 2, frame_y + frame_height, 0)),
                     Vector((frame_x, frame_y, 0))))
        
        # From left-center to right-top
        lines.append((Vector((frame_x, frame_y + frame_height / 2, 0)),
                     Vector((frame_x + frame_width, frame_y + frame_height, 0))))
        # From left-center to right-bottom
        lines.append((Vector((frame_x, frame_y + frame_height / 2, 0)),
                     Vector((frame_x + frame_width, frame_y, 0))))
        # From right-center to left-top
        lines.append((Vector((frame_x + frame_width, frame_y + frame_height / 2, 0)),
                     Vector((frame_x, frame_y + frame_height, 0))))
        # From right-center to left-bottom
        lines.append((Vector((frame_x + frame_width, frame_y + frame_height / 2, 0)),
                     Vector((frame_x, frame_y, 0))))
        
        draw_lines(lines, settings.diagonal_reciprocals_color)
    
    # Harmony Triangles (Golden Triangle)
    if settings.show_harmony_triangles:
        lines = []
        
        # Helper to generate lines for a specific orientation
        def add_harmony_lines(flip_h, flip_v):
            # Base coordinates
            x1, y1 = frame_x, frame_y
            x2, y2 = frame_x + frame_width, frame_y + frame_height
            
            # Apply flips to corners
            if flip_h:
                x1, x2 = x2, x1
            if flip_v:
                y1, y2 = y2, y1
                
            # Main diagonal
            start = Vector((x1, y1, 0))
            end = Vector((x2, y2, 0))
            lines.append((start, end))
            
            # Perpendicular from other corners
            c1_x, c1_y = x1, y2
            c1 = Vector((c1_x, c1_y, 0))
            
            # Corner 2 (Bottom-Right relative to diagonal start)
            c2_x, c2_y = x2, y1
            c2 = Vector((c2_x, c2_y, 0))
            
            # Calculate foot of perpendicular

            line_vec = end - start
            line_len_sq = line_vec.length_squared
            
            if line_len_sq > 0:
                # Project c1 onto line
                t1 = (c1 - start).dot(line_vec) / line_len_sq
                foot1 = start + line_vec * t1
                lines.append((c1, foot1))
                
                # Project c2 onto line
                t2 = (c2 - start).dot(line_vec) / line_len_sq
                foot2 = start + line_vec * t2
                lines.append((c2, foot2))

        # Always draw the base version (Bottom-Left to Top-Right)
        add_harmony_lines(False, False)
        
        # Add flipped version if enabled
        if settings.harmony_triangles_flip:
            add_harmony_lines(True, False)
        
        draw_lines(lines, settings.harmony_triangles_color)
    
    # Diagonal Method (45-degree diagonals from corners)
    if settings.show_diagonal_method:
        lines = []
        
        # Use user-defined angle
        angle_rad = math.radians(settings.diagonal_method_angle)
        
        # Calculate length needed to cross the frame
        # Max dimension * sqrt(2) is safe enough, or just a large number
        max_len = max(frame_width, frame_height) * 2.0
        
        # Calculate offsets based on angle
        dx = max_len * math.cos(angle_rad)
        dy = max_len * math.sin(angle_rad)
        
        lines.append((Vector((frame_x, frame_y, 0)),
                     Vector((frame_x + dx, frame_y + dy, 0))))
        
        # Mirror angle horizontally
        lines.append((Vector((frame_x + frame_width, frame_y, 0)),
                     Vector((frame_x + frame_width - dx, frame_y + dy, 0))))
        
        # Mirror angle vertically
        lines.append((Vector((frame_x, frame_y + frame_height, 0)),
                     Vector((frame_x + dx, frame_y + frame_height - dy, 0))))
        
        # Mirror angle both ways
        lines.append((Vector((frame_x + frame_width, frame_y + frame_height, 0)),
                     Vector((frame_x + frame_width - dx, frame_y + frame_height - dy, 0))))
        
        draw_lines(lines, settings.diagonal_method_color)
    
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')


def format_unit_value(value, unit_type):
    """Professional number formatting with adaptive precision"""
    if unit_type == 'RESOLUTION':
        # Integer precision for resolution
        return f"{int(round(value))}"
    elif unit_type == 'PIXELS':
        return f"{int(round(value))}"
    elif unit_type == 'PERCENT':
        # Smart percentage formatting
        if abs(value) < 1:
            return f"{value:.1f}"
        else:
            return f"{int(round(value))}"
    return str(int(round(value)))


def draw_rulers_base(context, settings, frame_x, frame_y, frame_width, frame_height):
    """
    Base function for drawing rulers, shared between VSE and 3D Viewport.
    """
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    
    ruler_size = settings.ruler_size
    gap = 2
    
    # Draw background boxes for rulers
    # Top ruler
    top_ruler_verts = [
        Vector((frame_x - gap, frame_y + frame_height + gap, 0)),
        Vector((frame_x + frame_width + gap, frame_y + frame_height + gap, 0)),
        Vector((frame_x + frame_width + gap, frame_y + frame_height + gap + ruler_size, 0)),
        Vector((frame_x - gap, frame_y + frame_height + gap + ruler_size, 0))
    ]
    indices = ((0, 1, 2), (2, 3, 0))
    batch = batch_for_shader(shader, 'TRIS', {"pos": top_ruler_verts}, indices=indices)
    
    # Use user-configured background color
    bg_color = tuple(settings.bg_color)
    gpu.state.blend_set('ALPHA')
    shader.bind()
    shader.uniform_float("color", bg_color)
    batch.draw(shader)
    
    # Left ruler
    left_ruler_verts = [
        Vector((frame_x - ruler_size - gap, frame_y - gap, 0)),
        Vector((frame_x - gap, frame_y - gap, 0)),
        Vector((frame_x - gap, frame_y + frame_height + gap, 0)),
        Vector((frame_x - ruler_size - gap, frame_y + frame_height + gap, 0))
    ]
    batch = batch_for_shader(shader, 'TRIS', {"pos": left_ruler_verts}, indices=indices)
    batch.draw(shader)
    
    # Corner box (slightly darker than ruler background)
    corner_bg_color = (
        settings.bg_color[0] * 0.7,
        settings.bg_color[1] * 0.7,
        settings.bg_color[2] * 0.7,
        min(1.0, settings.bg_color[3] * 1.1)
    )
    corner_verts = [
        Vector((frame_x - ruler_size - gap, frame_y + frame_height + gap, 0)),
        Vector((frame_x - gap, frame_y + frame_height + gap, 0)),
        Vector((frame_x - gap, frame_y + frame_height + gap + ruler_size, 0)),
        Vector((frame_x - ruler_size - gap, frame_y + frame_height + gap + ruler_size, 0))
    ]
    batch = batch_for_shader(shader, 'TRIS', {"pos": corner_verts}, indices=indices)
    shader.bind()
    shader.uniform_float("color", corner_bg_color)
    batch.draw(shader)
    
    # Draw unit label in corner
    font_id = 0
    blf.size(font_id, 8)
    blf.color(font_id, 0.7, 0.7, 0.7, 1.0)
    blf.enable(font_id, blf.SHADOW)
    blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 0.8)
    
    # Get unit abbreviation
    unit_labels = {
        'RESOLUTION': 'px',
        'PIXELS': 'px',
        'MM': 'mm',
        'CM': 'cm',
        'PERCENT': '%'
    }
    unit_text = unit_labels.get(settings.ruler_units, 'px')
    
    # Center text in corner box
    text_width, text_height = blf.dimensions(font_id, unit_text)
    corner_center_x = frame_x - gap - ruler_size / 2
    corner_center_y = frame_y + frame_height + gap + ruler_size / 2
    blf.position(font_id, corner_center_x - text_width / 2, corner_center_y - text_height / 2, 0)
    blf.draw(font_id, unit_text)
    
    blf.disable(font_id, blf.SHADOW)
    
    # Setup text with better readability and anti-aliasing
    font_id = 0
    blf.size(font_id, 10)
    blf.color(font_id, *settings.ruler_color)
    
    # Enable shadow for depth
    blf.enable(font_id, blf.SHADOW)
    blf.shadow(font_id, 5, 0.0, 0.0, 0.0, 1.0)
    blf.shadow_offset(font_id, 1, -1)
    
    # Enable rotation for better rendering (keeps text upright)
    blf.rotation(font_id, 0)
    
    # Get render resolution
    render = context.scene.render
    render_width = render.resolution_x * render.resolution_percentage / 100
    render_height = render.resolution_y * render.resolution_percentage / 100
    
    # Calculate zoom-adaptive tick spacing like a real ruler
    pixels_per_unit = frame_width / render_width if render_width > 0 else 1
    
    # Find appropriate major tick interval (in resolution units)
    possible_intervals = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
    target_spacing_px = 80  # Target spacing in screen pixels
    
    major_interval_units = 100
    for interval in possible_intervals:
        spacing_px = interval * pixels_per_unit
        if spacing_px >= target_spacing_px:
            major_interval_units = interval
            break
    
    # Calculate actual spacing in screen pixels
    major_spacing_px = major_interval_units * pixels_per_unit
    
    # Number of subdivisions between major ticks (always 10 for real ruler feel)
    num_subdivisions = 10
    minor_spacing_px = major_spacing_px / num_subdivisions
    
    # Pre-calculate common values
    ruler_text_y = frame_y + frame_height + gap + ruler_size * 0.65
    min_label_gap = 3
    
    # Collect all tick marks for batch drawing
    major_ticks = []
    medium_ticks = []
    minor_ticks = []
    labels_to_draw = []
    
    # Performance optimization: limit tick count for extreme zoom
    max_ticks = 500
    estimated_ticks = int(frame_width / minor_spacing_px) if minor_spacing_px > 0 else 0
    
    # If too many ticks, increase spacing dynamically
    if estimated_ticks > max_ticks:
        # Skip some subdivisions to reduce tick count
        skip_factor = max(1, int(estimated_ticks / max_ticks))
        actual_spacing = minor_spacing_px * skip_factor
    else:
        skip_factor = 1
        actual_spacing = minor_spacing_px
    
    # Horizontal ruler with subdivisions and overlap prevention
    tick_index = 0
    x_px = 0
    last_label_end_x = frame_x - 100  # Track last label position to prevent overlap
    
    while x_px <= frame_width:
        x_pos = frame_x + x_px
        
        # Calculate position in render resolution
        res_pos = x_px / frame_width * render_width if frame_width > 0 else 0
        
        # Calculate value based on units
        if settings.ruler_units == 'RESOLUTION':
            raw_value = res_pos
        elif settings.ruler_units == 'PIXELS':
            raw_value = x_px
        else:  # PERCENT
            raw_value = (res_pos / render_width) * 100 if render_width > 0 else 0
        
        # Determine tick type based on subdivision
        is_major = (tick_index % num_subdivisions == 0)
        is_medium = (tick_index % (num_subdivisions // 2) == 0) and not is_major
        
        # Collect tick vertices for batch drawing
        tick_height = ruler_size * (0.6 if is_major else 0.4 if is_medium else 0.25)
        y_top = frame_y + frame_height + gap + tick_height
        
        if is_major:
            major_ticks.extend([
                Vector((x_pos, frame_y + frame_height + gap, 0)),
                Vector((x_pos, y_top, 0))
            ])
            # Prepare label for drawing
            value_str = format_unit_value(raw_value, settings.ruler_units)
            text_width, text_height = blf.dimensions(font_id, value_str)
            text_x = x_pos - text_width / 2
            text_end_x = text_x + text_width
            
            # Check for overlap with previous label and ensure within bounds
            if text_x > last_label_end_x + min_label_gap and text_end_x < frame_x + frame_width:
                labels_to_draw.append((value_str, text_x, ruler_text_y))
                last_label_end_x = text_end_x
        elif is_medium:
            medium_ticks.extend([
                Vector((x_pos, frame_y + frame_height + gap, 0)),
                Vector((x_pos, y_top, 0))
            ])
        else:
            minor_ticks.extend([
                Vector((x_pos, frame_y + frame_height + gap, 0)),
                Vector((x_pos, y_top, 0))
            ])
        
        x_px += actual_spacing
        tick_index += skip_factor
    
    # Batch draw all horizontal ticks for better performance
    if major_ticks:
        gpu.state.line_width_set(2.0)
        batch = batch_for_shader(shader, 'LINES', {"pos": major_ticks})
        shader.bind()
        shader.uniform_float("color", settings.ruler_color)
        batch.draw(shader)
    
    if medium_ticks:
        gpu.state.line_width_set(1.5)
        medium_color = (settings.ruler_color[0] * 0.7, settings.ruler_color[1] * 0.7, 
                       settings.ruler_color[2] * 0.7, settings.ruler_color[3] * 0.75)
        batch = batch_for_shader(shader, 'LINES', {"pos": medium_ticks})
        shader.bind()
        shader.uniform_float("color", medium_color)
        batch.draw(shader)
    
    if minor_ticks:
        gpu.state.line_width_set(1.0)
        minor_color = (settings.ruler_color[0] * 0.5, settings.ruler_color[1] * 0.5, 
                      settings.ruler_color[2] * 0.5, settings.ruler_color[3] * 0.6)
        batch = batch_for_shader(shader, 'LINES', {"pos": minor_ticks})
        shader.bind()
        shader.uniform_float("color", minor_color)
        batch.draw(shader)
    
    # Draw all labels
    for label_text, label_x, label_y in labels_to_draw:
        blf.position(font_id, label_x, label_y, 0)
        blf.draw(font_id, label_text)
    
    # Draw end tick mark and label
    x_pos_end = frame_x + frame_width
    if settings.ruler_units == 'RESOLUTION':
        end_value = render_width
    elif settings.ruler_units == 'PIXELS':
        end_value = frame_width
    else:  # PERCENT
        end_value = 100
    
    value_str_end = format_unit_value(end_value, settings.ruler_units)
    text_width_end, text_height_end = blf.dimensions(font_id, value_str_end)
    text_x_end = x_pos_end - text_width_end / 2
    
    # Draw end tick
    gpu.state.line_width_set(2.0)
    tick_height_end = ruler_size * 0.6
    tick_verts_end = [
        Vector((x_pos_end, frame_y + frame_height + gap, 0)),
        Vector((x_pos_end, frame_y + frame_height + gap + tick_height_end, 0))
    ]
    batch = batch_for_shader(shader, 'LINES', {"pos": tick_verts_end})
    shader.bind()
    shader.uniform_float("color", settings.ruler_color)
    batch.draw(shader)
    
    # Draw end label
    text_y_end = frame_y + frame_height + gap + ruler_size * 0.65
    blf.position(font_id, text_x_end, text_y_end, 0)
    blf.draw(font_id, value_str_end)
    
    # Vertical ruler (similar logic)
    v_major_ticks = []
    v_medium_ticks = []
    v_minor_ticks = []
    v_labels_to_draw = []
    
    estimated_v_ticks = int(frame_height / minor_spacing_px) if minor_spacing_px > 0 else 0
    
    if estimated_v_ticks > max_ticks:
        v_skip_factor = max(1, int(estimated_v_ticks / max_ticks))
        v_actual_spacing = minor_spacing_px * v_skip_factor
    else:
        v_skip_factor = 1
        v_actual_spacing = minor_spacing_px
    
    tick_index = 0
    y_px = 0
    last_label_end_y = frame_y - 100
    
    while y_px <= frame_height:
        y_pos = frame_y + y_px
        
        # Calculate position in render resolution (from top to bottom, 0 at top)
        res_pos = (frame_height - y_px) / frame_height * render_height if frame_height > 0 else 0
        
        # Calculate value based on units
        if settings.ruler_units == 'RESOLUTION':
            raw_value = res_pos
        elif settings.ruler_units == 'PIXELS':
            raw_value = frame_height - y_px
        else:  # PERCENT
            raw_value = (res_pos / render_height) * 100 if render_height > 0 else 0
        
        # Determine tick type based on subdivision
        is_major = (tick_index % num_subdivisions == 0)
        is_medium = (tick_index % (num_subdivisions // 2) == 0) and not is_major
        
        # Collect tick vertices for batch drawing
        tick_width = ruler_size * (0.6 if is_major else 0.4 if is_medium else 0.25)
        x_left = frame_x - gap - tick_width
        
        if is_major:
            v_major_ticks.extend([
                Vector((x_left, y_pos, 0)),
                Vector((frame_x - gap, y_pos, 0))
            ])
            # Prepare label for drawing
            value_str = format_unit_value(raw_value, settings.ruler_units)
            text_width, text_height = blf.dimensions(font_id, value_str)
            text_start_y = y_pos - text_width / 2
            text_end_y = y_pos + text_width / 2
            
            # Check for overlap with previous label and ensure within bounds
            if text_start_y > last_label_end_y + min_label_gap and text_end_y < frame_y + frame_height:
                text_x = frame_x - gap - ruler_size * 0.7
                text_y = y_pos - text_width / 2
                v_labels_to_draw.append((value_str, text_x, text_y))
                last_label_end_y = text_end_y
        elif is_medium:
            v_medium_ticks.extend([
                Vector((x_left, y_pos, 0)),
                Vector((frame_x - gap, y_pos, 0))
            ])
        else:
            v_minor_ticks.extend([
                Vector((x_left, y_pos, 0)),
                Vector((frame_x - gap, y_pos, 0))
            ])
        
        y_px += v_actual_spacing
        tick_index += v_skip_factor
    
    # Batch draw all vertical ticks
    if v_major_ticks:
        gpu.state.line_width_set(2.0)
        batch = batch_for_shader(shader, 'LINES', {"pos": v_major_ticks})
        shader.bind()
        shader.uniform_float("color", settings.ruler_color)
        batch.draw(shader)
    
    if v_medium_ticks:
        gpu.state.line_width_set(1.5)
        medium_color = (settings.ruler_color[0] * 0.7, settings.ruler_color[1] * 0.7, 
                       settings.ruler_color[2] * 0.7, settings.ruler_color[3] * 0.75)
        batch = batch_for_shader(shader, 'LINES', {"pos": v_medium_ticks})
        shader.bind()
        shader.uniform_float("color", medium_color)
        batch.draw(shader)
    
    if v_minor_ticks:
        gpu.state.line_width_set(1.0)
        minor_color = (settings.ruler_color[0] * 0.5, settings.ruler_color[1] * 0.5, 
                      settings.ruler_color[2] * 0.5, settings.ruler_color[3] * 0.6)
        batch = batch_for_shader(shader, 'LINES', {"pos": v_minor_ticks})
        shader.bind()
        shader.uniform_float("color", minor_color)
        batch.draw(shader)
    
    # Draw all vertical labels with rotation
    if v_labels_to_draw:
        blf.enable(font_id, blf.ROTATION)
        blf.rotation(font_id, math.pi / 2)
        for label_text, label_x, label_y in v_labels_to_draw:
            blf.position(font_id, label_x, label_y, 0)
            blf.draw(font_id, label_text)
        blf.rotation(font_id, 0)
        blf.disable(font_id, blf.ROTATION)
    
    # Draw end tick mark and label for vertical ruler (top = 0)
    y_pos_end = frame_y + frame_height
    # Top of frame is 0 in our coordinate system
    end_value = 0
    
    value_str_end = format_unit_value(end_value, settings.ruler_units)
    text_width_end, text_height_end = blf.dimensions(font_id, value_str_end)
    text_x_end = frame_x - gap - ruler_size * 0.7
    text_y_end = y_pos_end - text_width_end / 2
    
    # Draw end tick
    gpu.state.line_width_set(2.0)
    tick_width_end = ruler_size * 0.6
    tick_verts_end = [
        Vector((frame_x - gap, y_pos_end, 0)),
        Vector((frame_x - gap - tick_width_end, y_pos_end, 0))
    ]
    batch = batch_for_shader(shader, 'LINES', {"pos": tick_verts_end})
    shader.bind()
    shader.uniform_float("color", settings.ruler_color)
    batch.draw(shader)
    
    # Draw end label
    blf.enable(font_id, blf.ROTATION)
    blf.rotation(font_id, math.pi / 2)
    blf.position(font_id, text_x_end, text_y_end, 0)
    blf.draw(font_id, value_str_end)
    blf.rotation(font_id, 0)
    blf.disable(font_id, blf.ROTATION)
    
    blf.disable(font_id, blf.SHADOW)
    
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')
