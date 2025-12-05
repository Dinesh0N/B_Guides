"""
VSE Composition Guides & Rulers
A Blender addon for adding composition guides and rulers to the VSE Preview and 3D Viewport Camera
"""

bl_info = {
    "name": "B Guides",
    "author": "Dinesh007",
    "version": (1, 0, 0),
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

# Store draw handlers per window
draw_handlers = {}


@persistent
def load_handler(dummy):
    """Handler to ensure draw handlers are set up after file load"""
    ensure_draw_handlers()


def ensure_draw_handlers():
    """Ensure draw handlers are registered for all VSE preview windows"""
    global draw_handlers
    
    # Remove all existing handlers first
    for handler in list(draw_handlers.values()):
        if handler:
            try:
                bpy.types.SpaceSequenceEditor.draw_handler_remove(handler, 'PREVIEW')
            except:
                pass
    draw_handlers.clear()
    
    # Add handlers if not already present
    if not draw_handlers:
        try:
            # VSE Handlers
            # Handler for guides and grid (POST_VIEW - behind gizmos)
            handler_view = bpy.types.SpaceSequenceEditor.draw_handler_add(
                drawing.draw_guides_view, (), 'PREVIEW', 'POST_VIEW'
            )
            draw_handlers['vse_view'] = handler_view
            
            # 3D Viewport Handler
            handler_3d = bpy.types.SpaceView3D.draw_handler_add(
                camera_drawing.draw_camera_guides, (), 'WINDOW', 'POST_VIEW'
            )
            draw_handlers['view3d'] = handler_3d
            
            print("Composition Guides: Draw handlers registered successfully")
        except Exception as e:
            print(f"Composition Guides: Failed to add draw handlers: {e}")


def register():
    """Register all addon classes and handlers"""
    # Register submodules
    properties.register()
    operators.register()
    presets.register()
    ui.register()
    
    # Add load handler
    bpy.app.handlers.load_post.append(load_handler)
    
    # Set up initial handlers
    ensure_draw_handlers()
    
    print("Composition Guides & Rulers addon registered")


def unregister():
    """Unregister all addon classes and handlers"""
    global draw_handlers
    
    # Remove load handler
    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)
    
    # Remove all draw handlers
    for space_type, handler in list(draw_handlers.items()):
        if handler:
            try:
                if 'vse' in space_type:
                    bpy.types.SpaceSequenceEditor.draw_handler_remove(handler, 'PREVIEW')
                elif 'view3d' in space_type:
                    bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
            except:
                pass
    draw_handlers.clear()
    
    # Unregister submodules (in reverse order)
    ui.unregister()
    presets.unregister()
    operators.unregister()
    properties.unregister()
    
    print("Composition Guides & Rulers addon unregistered")


if __name__ == "__main__":
    register()
