"""Property groups for VSE Guides addon"""

import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty,
    FloatProperty,
    IntProperty,
    EnumProperty,
    FloatVectorProperty,
)

def update_vse_areas():
    """Force redraw of all sequencer areas"""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'SEQUENCE_EDITOR':
                area.tag_redraw()


def update_3d_areas():
    """Force redraw of all 3D viewport areas"""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def update_all_areas():
    """Force redraw of all relevant areas"""
    update_vse_areas()
    update_3d_areas()


class CustomGuide(PropertyGroup):
    """Custom draggable guide"""
    
    name: bpy.props.StringProperty(
        name="Name",
        description="Guide name",
        default="Guide"
    )
    
    position_x: FloatProperty(
        name="X",
        description="Guide X position (normalized: -1=Left, 0=Center, 1=Right)",
        default=0.0,
        min=-1.0,
        max=1.0,
        step=1.0,
        update=lambda self, context: update_all_areas()
    )
    
    position_y: FloatProperty(
        name="Y",
        description="Guide Y position (normalized: -1=Bottom, 0=Center, 1=Top)",
        default=0.0,
        min=-1.0,
        max=1.0,
        step=1.0,
        update=lambda self, context: update_all_areas()
    )
    
    rotation: FloatProperty(
        name="Rotation",
        description="Guide rotation in degrees",
        default=0.0,
        unit='ROTATION',
        update=lambda self, context: update_all_areas()
    )
    
    orientation: EnumProperty(
        name="Orientation",
        items=[
            ('HORIZONTAL', "Horizontal", "Horizontal guide"),
            ('VERTICAL', "Vertical", "Vertical guide"),
        ],
        default='HORIZONTAL'
    )
    
    color: FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.0, 0.4, 1.0, 0.5)
    )


class VSEGuidesSettings(PropertyGroup):
    """Main settings for VSE Guides"""
    
    # Guide toggles
    show_thirds: BoolProperty(
        name="Rule of Thirds",
        description="Show rule of thirds guide",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    thirds_color: FloatVectorProperty(
        name="Thirds Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_all_areas()
    )
    
    show_golden: BoolProperty(
        name="Golden Ratio",
        description="Show golden ratio guide",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    golden_color: FloatVectorProperty(
        name="Golden Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_all_areas()
    )
    
    show_center: BoolProperty(
        name="Center Guides",
        description="Show center cross or full crosshair",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    

    
    center_color: FloatVectorProperty(
        name="Center Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_all_areas()
    )
    
    show_diagonals: BoolProperty(
        name="Diagonals",
        description="Show diagonal guides",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    diagonals_color: FloatVectorProperty(
        name="Diagonals Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_all_areas()
    )
    
    show_golden_spiral: BoolProperty(
        name="Golden Spiral",
        description="Show Fibonacci/golden spiral",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    golden_spiral_flip_h: BoolProperty(
        name="Flip Horizontal",
        description="Flip golden spiral horizontally",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    golden_spiral_flip_v: BoolProperty(
        name="Flip Vertical",
        description="Flip golden spiral vertically",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    golden_spiral_length: IntProperty(
        name="Spiral Length",
        description="Number of spiral iterations",
        min=1,
        max=24,
        default=8,
        update=lambda self, context: update_all_areas()
    )
    
    golden_spiral_show_segments: BoolProperty(
        name="Show Segments",
        description="Show subdivision squares",
        default=True,
        update=lambda self, context: update_all_areas()
    )
    
    golden_spiral_fit: BoolProperty(
        name="Fit to Frame",
        description="Stretch spiral to fit frame boundary",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    golden_spiral_color: FloatVectorProperty(
        name="Spiral Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_all_areas()
    )
    
    show_golden_triangle: BoolProperty(
        name="Triangle",
        description="Show golden triangle composition",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    golden_triangle_rotation: FloatProperty(
        name="Rotation",
        description="Rotation in degrees",
        default=0.0,
        unit='ROTATION',
        update=lambda self, context: update_all_areas()
    )
    
    golden_triangle_scale: FloatProperty(
        name="Scale",
        description="Scale of the triangle (0.1 to 2.0)",
        min=0.1,
        max=2.0,
        default=1.0,
        update=lambda self, context: update_all_areas()
    )
    
    golden_triangle_count: IntProperty(
        name="Triangle Count",
        description="Number of nested triangles",
        min=1,
        max=10,
        default=1,
        update=lambda self, context: update_all_areas()
    )
    
    golden_triangle_color: FloatVectorProperty(
        name="Triangle Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_all_areas()
    )
    
    
    show_radial_symmetry: BoolProperty(
        name="Radial Symmetry",
        description="Show radial symmetry lines",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    radial_symmetry_color: FloatVectorProperty(
        name="Radial Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_all_areas()
    )
    
    radial_line_count: IntProperty(
        name="Line Count",
        description="Number of radial symmetry lines",
        min=2,
        max=32,
        default=8,
        update=lambda self, context: update_all_areas()
    )
    
    show_vanishing_point: BoolProperty(
        name="Vanishing Point Grid",
        description="Show perspective vanishing point grid",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    vanishing_point_color: FloatVectorProperty(
        name="VP Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_all_areas()
    )
    
    vanishing_point_x: FloatProperty(
        name="VP X Position",
        description="Vanishing point X position (0-1)",
        min=0.0,
        max=1.0,
        default=0.5,
        update=lambda self, context: update_all_areas()
    )
    
    vanishing_point_y: FloatProperty(
        name="VP Y Position",
        description="Vanishing point Y position (0-1)",
        min=0.0,
        max=1.0,
        default=0.5,
        update=lambda self, context: update_all_areas()
    )
    
    vanishing_point_lines: IntProperty(
        name="Line Count",
        description="Subdivisions per edge (1=corners only, 2=+midpoints, etc.)",
        min=1,
        max=16,
        default=1,
        update=lambda self, context: update_all_areas()
    )
    
    show_vanishing_point_grid: BoolProperty(
        name="Show Grid",
        description="Show perspective grid lines",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    vanishing_point_grid_count: IntProperty(
        name="Grid Count",
        description="Number of perspective grid lines",
        min=2,
        max=64,
        default=10,
        update=lambda self, context: update_all_areas()
    )
    
    show_circular_thirds: BoolProperty(
        name="Circular",
        description="Show circular/concentric rule of thirds",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    circular_thirds_count: IntProperty(
        name="Circle Count",
        description="Number of concentric circles",
        min=1,
        max=10,
        default=3,
        update=lambda self, context: update_all_areas()
    )
    
    circular_thirds_fit: BoolProperty(
        name="Fit to Frame",
        description="Stretch circles to fit frame boundary (creates ellipses)",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    circular_thirds_color: FloatVectorProperty(
        name="Circular Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_all_areas()
    )
    
    show_diagonal_reciprocals: BoolProperty(
        name="Diagonal Reciprocals",
        description="Show diagonal reciprocal composition guides",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    diagonal_reciprocals_color: FloatVectorProperty(
        name="Diagonal Reciprocals Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_all_areas()
    )
    
    show_harmony_triangles: BoolProperty(
        name="Golden Triangle",
        description="Show harmony triangle composition guides",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    harmony_triangles_color: FloatVectorProperty(
        name="Golden Triangle Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_all_areas()
    )
    
    harmony_triangles_flip: BoolProperty(
        name="Flip",
        description="Flip harmony triangles",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    show_diagonal_method: BoolProperty(
        name="Diagonal Method",
        description="Show 45-degree diagonal lines from corners",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    diagonal_method_color: FloatVectorProperty(
        name="Diagonal Method Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_all_areas()
    )
    
    diagonal_method_angle: FloatProperty(
        name="Angle",
        description="Angle of diagonal lines",
        default=45.0,
        min=0.0,
        max=90.0,
        update=lambda self, context: update_all_areas()
    )
    
    # Ruler settings
    show_rulers: BoolProperty(
        name="Show Rulers",
        description="Show rulers with measurements",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    ruler_units: EnumProperty(
        name="Units",
        description="Ruler measurement units",
        items=[
            ('RESOLUTION', "Resolution", "Show measurements in resolution pixels"),
            ('PIXELS', "Pixels", "Show measurements in display pixels"),
            ('PERCENT', "Percentage", "Show measurements as percentage"),
        ],
        default='RESOLUTION',
        update=lambda self, context: update_all_areas()
    )
    
    # Visual settings

    
    ruler_color: FloatVectorProperty(
        name="Ruler Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_all_areas()
    )
    
    line_width: FloatProperty(
        name="Line Width",
        description="Width of guide lines",
        min=0.5,
        max=5.0,
        default=1.0,
        update=lambda self, context: update_all_areas()
    )
    
    ruler_size: IntProperty(
        name="Ruler Size",
        description="Height/width of ruler bars",
        min=20,
        max=50,
        default=30,
        update=lambda self, context: update_all_areas()
    )
    
    bg_color: FloatVectorProperty(
        name="BG Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.16, 0.16, 0.16, 0.96),
        update=lambda self, context: update_all_areas()
    )
    
    # Grid settings
    show_grid: BoolProperty(
        name="Grid",
        description="Show grid overlay",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    grid_divisions: IntProperty(
        name="Grid Divisions",
        description="Number of grid divisions",
        min=2,
        max=32,
        default=8,
        update=lambda self, context: update_all_areas()
    )
    
    grid_square: BoolProperty(
        name="Square Grid",
        description="Force square grid cells (equal width and height)",
        default=False,
        update=lambda self, context: update_all_areas()
    )
    
    grid_color: FloatVectorProperty(
        name="Grid Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.3),
        update=lambda self, context: update_all_areas()
    )
    
    # Guide Lines
    show_custom_guides: BoolProperty(
        name="Guide Lines",
        description="Show guide lines",
        default=True,
        update=lambda self, context: update_all_areas()
    )
    
    active_guide_index: IntProperty(
        name="Active Guide",
        description="Active custom guide index",
        default=0
    )
    
    # Frame clipping
    hide_guides_outside_frame: BoolProperty(
        name="Hide Guides Outside Frame",
        description="Hide guide lines that extend outside the frame boundaries",
        default=True,
        update=lambda self, context: update_all_areas()
    )
    
    # Internal storage for toggle state
    stored_active_guides: bpy.props.StringProperty(
        default=""
    )
    
    # Preset management
    active_preset: bpy.props.StringProperty(
        name="Active Preset",
        description="Currently selected preset",
        default=""
    )
    
    new_preset_name: bpy.props.StringProperty(
        name="New Preset Name",
        description="Name for saving a new preset",
        default=""
    )


class CustomCameraGuide(PropertyGroup):
    """Custom guide for camera - stored per camera"""
    
    name: bpy.props.StringProperty(
        name="Name",
        description="Guide name",
        default="Guide"
    )
    
    position_x: FloatProperty(
        name="X",
        description="Guide X position (normalized: -1=Left, 0=Center, 1=Right)",
        default=0.0,
        min=-1.0,
        max=1.0,
        step=1.0,
        update=lambda self, context: update_3d_areas()
    )
    
    position_y: FloatProperty(
        name="Y",
        description="Guide Y position (normalized: -1=Bottom, 0=Center, 1=Top)",
        default=0.0,
        min=-1.0,
        max=1.0,
        step=1.0,
        update=lambda self, context: update_3d_areas()
    )
    
    rotation: FloatProperty(
        name="Rotation",
        description="Guide rotation in degrees",
        default=0.0,
        unit='ROTATION',
        update=lambda self, context: update_3d_areas()
    )
    
    orientation: EnumProperty(
        name="Orientation",
        items=[
            ('HORIZONTAL', "Horizontal", "Horizontal guide"),
            ('VERTICAL', "Vertical", "Vertical guide"),
        ],
        default='HORIZONTAL'
    )
    
    color: FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.0, 0.4, 1.0, 0.5)
    )


class CameraGuidesSettings(PropertyGroup):
    """Guide settings stored per camera"""
    
    # Guide toggles
    show_thirds: BoolProperty(
        name="Rule of Thirds",
        description="Show rule of thirds guide",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    thirds_color: FloatVectorProperty(
        name="Thirds Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_3d_areas()
    )
    
    show_golden: BoolProperty(
        name="Golden Ratio",
        description="Show golden ratio guide",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    golden_color: FloatVectorProperty(
        name="Golden Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_3d_areas()
    )
    
    show_center: BoolProperty(
        name="Center Guides",
        description="Show center cross or full crosshair",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    center_color: FloatVectorProperty(
        name="Center Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_3d_areas()
    )
    
    show_diagonals: BoolProperty(
        name="Diagonals",
        description="Show diagonal guides",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    diagonals_color: FloatVectorProperty(
        name="Diagonals Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_3d_areas()
    )
    
    show_golden_spiral: BoolProperty(
        name="Golden Spiral",
        description="Show Fibonacci/golden spiral",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    golden_spiral_flip_h: BoolProperty(
        name="Flip Horizontal",
        description="Flip golden spiral horizontally",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    golden_spiral_flip_v: BoolProperty(
        name="Flip Vertical",
        description="Flip golden spiral vertically",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    golden_spiral_length: IntProperty(
        name="Spiral Length",
        description="Number of spiral iterations",
        min=1,
        max=24,
        default=8,
        update=lambda self, context: update_3d_areas()
    )
    
    golden_spiral_show_segments: BoolProperty(
        name="Show Segments",
        description="Show subdivision squares",
        default=True,
        update=lambda self, context: update_3d_areas()
    )
    
    golden_spiral_fit: BoolProperty(
        name="Fit to Frame",
        description="Stretch spiral to fit frame boundary",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    golden_spiral_color: FloatVectorProperty(
        name="Spiral Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_3d_areas()
    )
    
    show_golden_triangle: BoolProperty(
        name="Triangle",
        description="Show golden triangle composition",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    golden_triangle_rotation: FloatProperty(
        name="Rotation",
        description="Rotation in degrees",
        default=0.0,
        unit='ROTATION',
        update=lambda self, context: update_3d_areas()
    )
    
    golden_triangle_scale: FloatProperty(
        name="Scale",
        description="Scale of the triangle (0.1 to 2.0)",
        min=0.1,
        max=2.0,
        default=1.0,
        update=lambda self, context: update_3d_areas()
    )
    
    golden_triangle_count: IntProperty(
        name="Triangle Count",
        description="Number of nested triangles",
        min=1,
        max=10,
        default=1,
        update=lambda self, context: update_3d_areas()
    )
    
    golden_triangle_color: FloatVectorProperty(
        name="Triangle Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_3d_areas()
    )
    
    show_radial_symmetry: BoolProperty(
        name="Radial Symmetry",
        description="Show radial symmetry lines",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    radial_symmetry_color: FloatVectorProperty(
        name="Radial Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_3d_areas()
    )
    
    radial_line_count: IntProperty(
        name="Line Count",
        description="Number of radial symmetry lines",
        min=2,
        max=32,
        default=8,
        update=lambda self, context: update_3d_areas()
    )
    
    show_vanishing_point: BoolProperty(
        name="Vanishing Point Grid",
        description="Show perspective vanishing point grid",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    vanishing_point_color: FloatVectorProperty(
        name="VP Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_3d_areas()
    )
    
    vanishing_point_x: FloatProperty(
        name="VP X Position",
        description="Vanishing point X position (0-1)",
        min=0.0,
        max=1.0,
        default=0.5,
        update=lambda self, context: update_3d_areas()
    )
    
    vanishing_point_y: FloatProperty(
        name="VP Y Position",
        description="Vanishing point Y position (0-1)",
        min=0.0,
        max=1.0,
        default=0.5,
        update=lambda self, context: update_3d_areas()
    )
    
    vanishing_point_lines: IntProperty(
        name="Line Count",
        description="Subdivisions per edge (1=corners only, 2=+midpoints, etc.)",
        min=1,
        max=16,
        default=1,
        update=lambda self, context: update_3d_areas()
    )
    
    show_vanishing_point_grid: BoolProperty(
        name="Show Grid",
        description="Show perspective grid lines",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    vanishing_point_grid_count: IntProperty(
        name="Grid Count",
        description="Number of perspective grid lines",
        min=2,
        max=64,
        default=10,
        update=lambda self, context: update_3d_areas()
    )
    
    show_circular_thirds: BoolProperty(
        name="Circular",
        description="Show circular/concentric rule of thirds",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    circular_thirds_count: IntProperty(
        name="Circle Count",
        description="Number of concentric circles",
        min=1,
        max=10,
        default=3,
        update=lambda self, context: update_3d_areas()
    )
    
    circular_thirds_fit: BoolProperty(
        name="Fit to Frame",
        description="Stretch circles to fit frame boundary (creates ellipses)",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    circular_thirds_color: FloatVectorProperty(
        name="Circular Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_3d_areas()
    )
    
    show_diagonal_reciprocals: BoolProperty(
        name="Diagonal Reciprocals",
        description="Show diagonal reciprocal composition guides",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    diagonal_reciprocals_color: FloatVectorProperty(
        name="Diagonal Reciprocals Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_3d_areas()
    )
    
    show_harmony_triangles: BoolProperty(
        name="Golden Triangle",
        description="Show harmony triangle composition guides",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    harmony_triangles_color: FloatVectorProperty(
        name="Golden Triangle Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_3d_areas()
    )
    
    harmony_triangles_flip: BoolProperty(
        name="Flip",
        description="Flip harmony triangles",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    show_diagonal_method: BoolProperty(
        name="Diagonal Method",
        description="Show 45-degree diagonal lines from corners",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    diagonal_method_color: FloatVectorProperty(
        name="Diagonal Method Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.5),
        update=lambda self, context: update_3d_areas()
    )
    
    diagonal_method_angle: FloatProperty(
        name="Angle",
        description="Angle of diagonal lines",
        default=45.0,
        min=0.0,
        max=90.0,
        update=lambda self, context: update_3d_areas()
    )
    
    # Ruler settings
    show_rulers: BoolProperty(
        name="Show Rulers",
        description="Show rulers with measurements",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    ruler_units: EnumProperty(
        name="Units",
        description="Ruler measurement units",
        items=[
            ('RESOLUTION', "Resolution", "Show measurements in resolution pixels"),
            ('PIXELS', "Pixels", "Show measurements in display pixels"),
            ('PERCENT', "Percentage", "Show measurements as percentage"),
        ],
        default='RESOLUTION',
        update=lambda self, context: update_3d_areas()
    )
    
    ruler_color: FloatVectorProperty(
        name="Ruler Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.8),
        update=lambda self, context: update_3d_areas()
    )
    
    line_width: FloatProperty(
        name="Line Width",
        description="Width of guide lines",
        min=0.5,
        max=5.0,
        default=1.0,
        update=lambda self, context: update_3d_areas()
    )
    
    ruler_size: IntProperty(
        name="Ruler Size",
        description="Height/width of ruler bars",
        min=20,
        max=50,
        default=30,
        update=lambda self, context: update_3d_areas()
    )
    
    bg_color: FloatVectorProperty(
        name="BG Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.16, 0.16, 0.16, 0.96),
        update=lambda self, context: update_3d_areas()
    )
    
    # Grid settings
    show_grid: BoolProperty(
        name="Grid",
        description="Show grid overlay",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    grid_divisions: IntProperty(
        name="Grid Divisions",
        description="Number of grid divisions",
        min=2,
        max=32,
        default=8,
        update=lambda self, context: update_3d_areas()
    )
    
    grid_square: BoolProperty(
        name="Square Grid",
        description="Force square grid cells (equal width and height)",
        default=False,
        update=lambda self, context: update_3d_areas()
    )
    
    grid_color: FloatVectorProperty(
        name="Grid Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 0.3),
        update=lambda self, context: update_3d_areas()
    )
    
    # Guide Lines
    show_custom_guides: BoolProperty(
        name="Guide Lines",
        description="Show guide lines",
        default=True,
        update=lambda self, context: update_3d_areas()
    )
    
    active_guide_index: IntProperty(
        name="Active Guide",
        description="Active custom guide index",
        default=0
    )
    
    # Frame clipping
    hide_guides_outside_frame: BoolProperty(
        name="Hide Guides Outside Frame",
        description="Hide guide lines that extend outside the frame boundaries",
        default=True,
        update=lambda self, context: update_3d_areas()
    )
    
    # Internal storage for toggle state
    stored_active_guides: bpy.props.StringProperty(
        default=""
    )
    
    # Preset management
    active_preset: bpy.props.StringProperty(
        name="Active Preset",
        description="Currently selected preset",
        default=""
    )
    
    new_preset_name: bpy.props.StringProperty(
        name="New Preset Name",
        description="Name for saving a new preset",
        default=""
    )


# Registration
classes = (
    CustomGuide,
    VSEGuidesSettings,
    CustomCameraGuide,
    CameraGuidesSettings,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # VSE settings (on Scene)
    bpy.types.Scene.vse_guides = bpy.props.PointerProperty(type=VSEGuidesSettings)
    bpy.types.Scene.custom_guides = bpy.props.CollectionProperty(type=CustomGuide)
    
    # Camera settings (on Camera data)
    bpy.types.Camera.camera_guides = bpy.props.PointerProperty(type=CameraGuidesSettings)
    bpy.types.Camera.custom_camera_guides = bpy.props.CollectionProperty(type=CustomCameraGuide)


def unregister():
    # Camera settings
    if hasattr(bpy.types.Camera, 'camera_guides'):
        del bpy.types.Camera.camera_guides
    if hasattr(bpy.types.Camera, 'custom_camera_guides'):
        del bpy.types.Camera.custom_camera_guides
    
    # VSE settings
    if hasattr(bpy.types.Scene, 'vse_guides'):
        del bpy.types.Scene.vse_guides
    if hasattr(bpy.types.Scene, 'custom_guides'):
        del bpy.types.Scene.custom_guides
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

