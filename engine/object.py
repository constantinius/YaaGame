import pyglet
import pymunk
import math
import engine.resource

class GameObject(object):
    """
    Common base class for all game objects in the game.
    """
    
    def __init__(self, *args, **kwargs):
        if not hasattr(self, 'properties'):
            self.properties = {}
    
    def _register_property_getter(self, name, handler):
        if name not in self.properties:
            self.properties[name] = ([handler], [])
        else:
            self.properties[name][0].append(handler)
    
    def _register_property_setter(self, name, handler):
        """
        Private method to register a property setter 
        method for a specific property.
        """
        if name not in self.properties:
            self.properties[name] = ([], [handler])
        else:
            self.properties[name][1].append(handler)
            
    def _register_property(self, name, getter = None, setter = None):
        if getter is not None:
            self._register_property_getter(name, getter)
        if setter is not None:
            self._register_property_setter(name, setter)
    
    def __settattr__(self, name, value):
        if name in self.__dict__:
            self.__dict__[name] = value
        else:
            for handler in self.properties[name][1]:
                handler(value)
    
    def __getattr__(self, name):
        try:
            return getattr(self.__class__, name)
        except AttributeError:
            return self.__dict__['properties'][name][0][0]()
    
    def on_added(self):
        """
        Stub message handler for 'on_added' messages.
        """
        pass
    
    def on_removed(self):
        """
        Stub message handler for 'on_removed' messages.
        """
        pass
        
    def update(self, dt):
        """
        This is a good spot to insert AI and Input gathering.
        """
        pass
        
    def debug_draw(self):
        pass
        
    def on_key_press(self, key, modifiers):
        """
        Default key event handling function.
        """
        pass
        
    def on_key_release(self, key, modifiers):
        """
        Default key event handling function.
        """
        pass
        
class GraphicalObject(GameObject):
    """
    Abstract class for all visual objects.
    """
    
    image_path = None           # path to the static image.
    animation_path = None       # path to the animation image
    animation_tiling = (1, 1)   # the tiling of the animation image
    animation_duration = 1.     # the overall duration of the animation
    scale = 1.                  # the size-scale of the object
    group_index = 1             # the display group index
    angle = 0                   # default angle
    
    def __init__(self, *args, **kwargs):
        """
        Initializes a GraphicalObject with either a static image or
        an animation.
        """
        GameObject.__init__(self, *args, **kwargs)
       
        self.image_path = kwargs.get('image_path', self.image_path)
        self.animation_path = kwargs.get('animation_path', self.animation_path)
        self.scale = kwargs.get('scale', self.scale)
        self.group_index = kwargs.get('group_index', self.group_index)
        self.position = kwargs.get('position', (0, 0))
        self.angle = math.degrees(kwargs.get('angle', self.angle))
        
        self._register_property('position', self._get_position, self._set_position)
    
    def _get_position(self): return self.sprite.position
    def _set_position(self, value): self.sprite.position = value
    
    def on_animation_end(self):
        """
        Default event handler for ending animations.
        """
        pass
        
    def on_predraw(self):
        pass
    
    def on_postdraw(self):
        pass
        
class PhysicalObject(GameObject):
    """
    Abstract subclass for all GameObjects with physical interaction.
    """
    maximum_speed = 200.        # default maximum speed
    scale = 1.                  # the size-scale of the object
    mass = 1.                   # default mass
    radius = None               # radius for circles
    points = None               # points for polygons
    
    group = 0                   # collision group
    layers = -1                 # collision layers
    sensor = False              # sensor flag
    elasticity = 1.             # bouncing property
    friction = 1.               # friction property
    
    def __init__(self, *args, **kwargs):
        """
        Initializes a PhysicalObject with either a Circle or a Polygon shape.
        """
        GameObject.__init__(self, *args, **kwargs)
        
        self.scale = kwargs.get('scale', self.scale)
        mass = kwargs.get('mass', self.mass) * self.scale
        radius = kwargs.get('radius', self.radius)
        points = kwargs.get('points', self.points)
        
        if radius is not None:
            radius *= self.scale
            moment = pymunk.moment_for_circle(mass, 0, radius)
            self.body = pymunk.Body(mass, moment)
            self.shape = pymunk.Circle(self.body, radius)
        
        elif points is not None:
            vertices = map(pymunk.Vec2d, self.points)
            for vertex in vertices:
                vertex *= self.scale
            moment = pymunk.moment_for_poly(mass, vertices)
            self.body = pymunk.Body(mass, moment)
            self.shape = pymunk.Poly(self.body, vertices)
        else:
            raise Exception("Neither radius nor points are specified")
        
        self.body._bodycontents.v_limit = self.maximum_speed
        
        # set up hook to get from the body to the game object
        self.body.object = self
        
        # set up initial parameters
        self.body.position = kwargs.get('position', (0, 0))
        self.body.velocity = kwargs.get('velocity', (0, 0))
        self.body.angle = kwargs.get('angle', 0)
        
        self.shape.group = kwargs.get('group', self.group)
        self.shape.layers = kwargs.get('layers', self.layers)
        self.shape.sensor = kwargs.get('sensor', self.sensor)
        self.shape.elasticity = kwargs.get('elasticity', self.elasticity)
        self.shape.friction = kwargs.get('friction', self.friction)
        
        self._register_property('position', self._get_position, self._set_position)
        self._register_property('velocity', self._get_velocity, self._set_velocity)
        self._register_property('angle', self._get_angle, self._set_angle)
    
    """ Property getters/setters """
    def _get_position(self): return self.body.position
    def _set_position(self, value): self.body.position = value
    
    def _set_velocity(self, value): self.body.velocity = value
    def _get_velocity(self): return self.body.velocity
    
    def _get_angle(self): return self.body.angle
    def _set_angle(self, value): self.body.angle = value
        
    def on_collision(self, other, arbiter):
        """
        Default collision handling function. Return True if
        collision shall be accepted, e.e processed further, or
        False if not.
        """
        return True
        
class CombinedObject(GraphicalObject, PhysicalObject):
    """
    Convenience class for combined graphical and physical objects.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Convenience CTOR to initialize both Graphical and Physical part
        of the object.
        """
        GameObject.__init__(self, *args, **kwargs)
        GraphicalObject.__init__(self, *args, **kwargs)
        PhysicalObject.__init__(self, *args, **kwargs)
