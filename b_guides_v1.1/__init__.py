"""
VSE Composition Guides & Rulers
A Blender addon for adding composition guides and rulers to the VSE Preview and 3D Viewport Camera
"""

bl_info = {
    "name": "B Guides",
    "author": "Dinesh007",
    "version": (1, 0, 1),
    "blender": (5, 0, 0),
    "location": "3D Viewport/Sequence Editor > Sidebar > Guides",
    "description": "Adds composition guides and rulers to VSE Preview and 3D Viewport Camera",
    "category": "3D View, Camera, Sequencer",
}

import bpy
from bpy.app.handlers import persistent

# Import submodules
from . import properties
from . import operators
from . import presets
from . import ui
from . import drawing
from . import camera_drawing

# Store draw handlers
_draw_handlers = {
    'vse_view': None,
    'view3d': None,
}


def _any_vse_guide_active(settings):
    """Check if any VSE guide is enabled."""
    if settings is None:
        return False
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
        settings.show_diagonal_method,
    ])


def _any_camera_guide_active(camera):
    """Check if any camera guide is enabled for the given camera."""
    if camera is None or not hasattr(camera.data, 'camera_guides'):
        return False
    settings = camera.data.camera_guides
    return _any_vse_guide_active(settings)


def register_vse_handler():
    """Register VSE draw handler if not already registered."""
    global _draw_handlers
    if _draw_handlers['vse_view'] is None:
        try:
            _draw_handlers['vse_view'] = bpy.types.SpaceSequenceEditor.draw_handler_add(
                drawing.draw_guides_view, (), 'PREVIEW', 'POST_VIEW'
            )
        except Exception as e:
            print(f"B Guides: Failed to register VSE handler: {e}")


def unregister_vse_handler():
    """Unregister VSE draw handler if registered."""
    global _draw_handlers
    if _draw_handlers['vse_view'] is not None:
        try:
            bpy.types.SpaceSequenceEditor.draw_handler_remove(_draw_handlers['vse_view'], 'PREVIEW')
        except Exception:
            pass
        _draw_handlers['vse_view'] = None


def register_3d_handler():
    """Register 3D Viewport draw handler if not already registered."""
    global _draw_handlers
    if _draw_handlers['view3d'] is None:
        try:
            _draw_handlers['view3d'] = bpy.types.SpaceView3D.draw_handler_add(
                camera_drawing.draw_camera_guides, (), 'WINDOW', 'POST_VIEW'
            )
        except Exception as e:
            print(f"B Guides: Failed to register 3D handler: {e}")


def unregister_3d_handler():
    """Unregister 3D Viewport draw handler if registered."""
    global _draw_handlers
    if _draw_handlers['view3d'] is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_draw_handlers['view3d'], 'WINDOW')
        except Exception:
            pass
        _draw_handlers['view3d'] = None


def update_vse_handler_state():
    """Register or unregister VSE handler based on current settings."""
    try:
        scene = bpy.context.scene
        if scene and hasattr(scene, 'vse_guides'):
            if _any_vse_guide_active(scene.vse_guides):
                register_vse_handler()
            else:
                unregister_vse_handler()
    except Exception:
        pass


def update_3d_handler_state():
    """Register or unregister 3D handler based on current camera settings."""
    try:
        scene = bpy.context.scene
        if scene and scene.camera:
            if _any_camera_guide_active(scene.camera):
                register_3d_handler()
            else:
                unregister_3d_handler()
    except Exception:
        pass


@persistent
def load_handler(dummy):
    """Handler to set up draw handlers after file load if guides were enabled."""
    # Check VSE guides
    try:
        for scene in bpy.data.scenes:
            if hasattr(scene, 'vse_guides') and _any_vse_guide_active(scene.vse_guides):
                register_vse_handler()
                break
    except Exception:
        pass
    
    # Check camera guides
    try:
        for camera in bpy.data.cameras:
            if hasattr(camera, 'camera_guides') and _any_vse_guide_active(camera.camera_guides):
                register_3d_handler()
                break
    except Exception:
        pass


def register():
    """Register all addon classes and handlers"""
    # Register submodules
    properties.register()
    operators.register()
    presets.register()
    ui.register()
    
    # Add load handler
    bpy.app.handlers.load_post.append(load_handler)
    
    # Don't register draw handlers here - they'll be registered on demand
    # when user enables guides or when a file with enabled guides is loaded
    
    print("B Guides addon registered")


def unregister():
    """Unregister all addon classes and handlers"""
    # Remove load handler
    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)
    
    # Remove all draw handlers
    unregister_vse_handler()
    unregister_3d_handler()
    
    # Unregister submodules (in reverse order)
    ui.unregister()
    presets.unregister()
    operators.unregister()
    properties.unregister()
    
    print("B Guides addon unregistered")


if __name__ == "__main__":
    register()
