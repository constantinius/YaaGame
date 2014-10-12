import math
import pyglet.gl
import pyglet.graphics
from engine.entity import AbstractModel

class GraphicalModel(AbstractModel):
    image_path = None           # path to the static image.
    animation_path = None       # path to the animation image
    animation_tiling = (1, 1)   # the tiling of the animation image
    animation_duration = 1.     # the overall duration of the animation
    scale = 1.                  # the size-scale of the object
    group_index = 1             # the display group index

    def __init__(self, *args, **kwargs):
        super(GraphicalModel, self).__init__(*args, **kwargs)
        
        self.image_path = kwargs.get('image_path', self.image_path)
        self.animation_path = kwargs.get('animation_path', self.animation_path)
        self.scale = kwargs.get('scale', self.scale)
        self.group_index = kwargs.get('group_index', self.group_index)
        self.position = kwargs.get('position', (0, 0))
        self.angle = math.degrees(kwargs.get('angle', 0))
        
        self._create_sprite()
    
    def _create_sprite(self):
        pass
    
    def _set_scale(self, value): self.sprite.scale = value
    
    def _get_position(self): return self.sprite.position
    def _set_position(self, value): self.sprite.position = value
    
    properties = {
        'scale': (None, _set_scale),
        'position': (_get_position, _set_position),
    }

#def create_sprite(model, 

def draw_line_loop(points, color = None):
    """
    helper function to draw a specific line loop, specified by a list 
    of points (iterable of Vec2ds) in a specified color (not implemented).
    """
    if color is not None:
        if len(color) == 3: pyglet.gl.glColor3f(*color)
        if len(color) == 4: pyglet.gl.glColor4f(*color)
    
    verts = []
    for point in points:
        verts.extend(point)
    
    pyglet.graphics.draw(len(verts)/2, pyglet.gl.GL_LINE_LOOP,
        ('v2f', verts)
    )

def draw_line(start, end, color = None):
    if color is not None:
        if len(color) == 3: pyglet.gl.glColor3f(*color)
        if len(color) == 4: pyglet.gl.glColor4f(*color)
    
    verts = [start[0], start[1], end[0], end[1]]
    pyglet.graphics.draw(2, pyglet.gl.GL_LINE_LOOP,
        ('v2f', verts)
    )

_circlepoints = []
for i in range(100):
    angle = i * 2 * math.pi / 100
    _circlepoints.append(math.cos(angle))
    _circlepoints.append(math.sin(angle))
circle_list = pyglet.graphics.vertex_list(len(_circlepoints)/2,
                                          ('v2f', _circlepoints))

def draw_circle(position, radius, color = None):
    """
    helper function to draw a circle at a given position (Vec2d) with a 
    given radius in a specified color.
    """
    if color is not None:
        if len(color) == 3: pyglet.gl.glColor3f(*color)
        if len(color) == 4: pyglet.gl.glColor4f(*color)
    
    pyglet.gl.glPushMatrix()
    pyglet.gl.glTranslatef(position[0], position[1], 0.)
    pyglet.gl.glScalef(radius, radius, 0)
    circle_list.draw(pyglet.gl.GL_LINE_LOOP)
    pyglet.gl.glPopMatrix()