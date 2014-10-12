import sys
import pyglet
from engine.service import (
    ServiceManager, ResourceService
)

def image(filename):
    """
    Convenience function to load an image from the ResourceService,
    if configured.
    """
    try:
        return ServiceManager.instance[ResourceService].image(filename)
    except KeyError:
        sys.stderr.write("ResourceService is not configured, "+
                         "using fallback")
        return pyglet.image.load(filename)
        
def animation(filename, tiling, duration):
    try:
        return ServiceManager.instance[ResourceService].animation(filename, tiling, duration)
    except KeyError:
        sys.stderr.write("ResourceService is not configured, "+
                         "using fallback")
        seq = pyglet.image.ImageGrid(engine.resource.image(obj.animation_path), 
                                         *obj.animation_tiling)
            
        # TODO overall/frame duration not working
        frame_duration = obj.animation_duration / (obj.animation_tiling[0] *
                                                   obj.animation_tiling[1])
        animation = pyglet.image.Animation.from_image_sequence(seq,
                                                               frame_duration)
        return animation