import math
import pymunk
import pyglet
import engine
from engine.graphics import draw_line_loop, draw_circle


class ServiceManager():
    """
    This class is responsible for managing game services.
    """
    instance = None

    def __init__(self):
        """
        Initialization method for a service manager.
        """
        self.__services = {}
        ServiceManager.instance = self
        self.broadcasts = {}

    def register_service(self, service_class, *args, **kwargs):
        """
        Factory method to create and register a new game service in the manager
        """
        service = service_class(*args, **kwargs)
        service.mgr = self
        self.__services[service_class] = service

    def add_service(self, service):
        self +=service

    def __iadd__(self, service):
        cls = service.__class__
        if cls in self.__services:
            raise Exception("Service class %s is already registered" %
                            cls.__name__)

        service.mgr = self
        self.__services[cls] = service
        return self

    def __getitem__(self, service_class):
        """
        Return the service by its class.
        """
        return self.__services[service_class]

    def get_timestamp(self):
        """
        Convenience method to get the actual timestamp of the 
        current frame.
        """
        pass

    def send_broadcast(self, event, *args, **kwargs):
        """
        Sends a broadcast message to all services, meaning, to call a
        function on the service if it hast it.
        The method caches what services implement the event handler for
        faster processing.
        """

        # cache all handlers if not present
        if event not in self.broadcasts:
            handlers = []
            for service in sorted(self.__services.values(),
                                  key=lambda service: service.priority):
                if hasattr(service, event):
                    handlers.append(getattr(service, event))
            self.broadcasts[event] = tuple(handlers)

        # actually 'send' the message
        for handler in self.broadcasts[event]:
            handler(*args, **kwargs)

class AbstractService(object):
    """
    An abstract base class for all game services.
    """

    # The priority in what order the service receives messages.
    # lower priorities mean earlier receit.
    priority = 0

    def on_init(self, mgr):
        pass

class GameObjectService(AbstractService):
    """
    GameObjectServices manage the insertion and extraction of object
    from and to the game.
    """

    def __init__(self):
        """
        Initializes the GameObjectService.
        """
        self.objects = []
        self.objects_to_remove = set()
        self.debug_draw = True

    def add_object_class(self, cls, *args, **kwargs):
        """
        Factory method, to add a new GameObject to the game. The object
        is created by a given class and an argument list.
        """
        obj = cls(*args, **kwargs)
        return self.add_object(obj)

    def add_object(self, obj):
        """
        Adds a GameObject to the active GameObjects. Sends a broadcast
        message 'on_object_added' of the addition of the object to all
        other services.
        """
        obj.object_service = self
        obj.on_added()
        self.objects.append(obj)
        self.mgr.send_broadcast('on_object_added', obj)
        return obj

    def remove_object(self, obj):
        """
        Removes a game object from the game. Sends a broadcast message
        'on_object_removed' to all other services.
        
        UPDATE: objects are removed in the next update
        """
        if obj not in self.objects_to_remove:
            obj.on_removed()
            self.mgr.send_broadcast('on_object_removed', obj)
            self.objects_to_remove.add(obj)

    def clear(self):
        """
        Removes all objects currently registered.
        """
        for obj in self.objects:
            self.remove_object(obj)


    def on_tick(self, dt):
        """
        This version of on_tick sends the 'update' message to all
        active objects in the game.
        """
        for obj in self.objects_to_remove:
            self.objects.remove(obj)

        self.objects_to_remove.clear()

        for obj in self.objects:
            obj.update(dt)

    def on_draw(self):
        if not self.debug_draw:
            return

        for obj in self.objects:
            obj.debug_draw()


class PhysicsService(AbstractService):
    """
    The PhysicsService is responsible to hold and update the physical
    state of all objects with a physical component registered.
    It also updates the graphical position and rotation of the objects.
    """
    priority = 10

    def __init__(self, *args, **kwargs):
        """
        Initializes the physics engine and the PhysicsService.
        """
        pymunk.init_pymunk()
        self.space = pymunk.Space()
        self.physical_objects = []
        self.bounds = kwargs.get('bounds', None)

        self.space.set_default_collision_handler(self.on_collision, None, None, None)

        # prepare the debug drawing of a sphere
        self.debug_draw = False


    def on_tick(self, dt):
        """
        Updates the physical state of the objects in the game.
        """
        self.space.step(dt)
        for obj in self.physical_objects:
            self._check_wrap_around(obj)
            obj.sprite.position = obj.body.position
            obj.sprite.rotation = -math.degrees(obj.body.angle)

            #TODO: find out meaning
            #obj.body.reset_forces()

    def on_draw(self):
        """
        Draws all the shapes within the space.
        """
        if not self.debug_draw:
            return

        pyglet.gl.glColor4f(1.0, 0, 0, 1.0)
        for shape in self.space.shapes:
            if isinstance(shape, pymunk.Poly):
                draw_line_loop(shape.get_points())
            elif isinstance(shape, pymunk.Circle):
                draw_circle(shape.body.position, shape.radius)

    def on_object_added(self, obj):
        """
        Message handler for 'on_object_added' messages. If the object
        contains a body and a shape, it is added to the list of physical
        objects.
        """
        if hasattr(obj, 'shape') and hasattr(obj, 'body'):
            self.physical_objects.append(obj)
            self.space.add(obj.shape, obj.body)

    def on_object_removed(self, obj):
        """
        Message handler for 'on_object_removed' messages. Removes objects 
        and shapes from the space.
        """
        if obj in self.physical_objects:
            self.physical_objects.remove(obj)
            self.space.remove(obj.shape, obj.body)

    def _check_wrap_around(self, obj):
        """
        Provides the 'wrap around' functionality.
        TODO: outsource this to an own service
        maybe create a WrapAroundPhysicsService
        """
        width = self.bounds[2] - self.bounds[0]
        height = self.bounds[3] - self.bounds[1]
        if self.bounds is not None:
            while obj.body.position[0] < self.bounds[0]:
                obj.body.position[0] += width
            while obj.body.position[0] > self.bounds[2]:
                obj.body.position[0] -= width
            while obj.body.position[1] < self.bounds[1]:
                obj.body.position[1] += height
            while obj.body.position[1] > self.bounds[3]:
                obj.body.position[1] -= height

    def on_collision(self, space, arbiter, *args, **kwargs):
        """
        TODO document
        """
        first = arbiter.shapes[0].body.object
        second = arbiter.shapes[1].body.object
        ret = (first.on_collision(second, arbiter),
               second.on_collision(first, arbiter))
        return (ret[0] and ret[1])

    def switch_debug_draw(self, value):
        if value:
            self.debug_draw = not self.debug_draw

    def bbox_query(self, bbox, layers= -1, group=0):
        query_hits = []
        def cf(_shape, data):
            shape = self.space._shapes[_shape.contents.hashid]
            query_hits.append(shape.body.object)

        f = pymunk._chipmunk.cpSpaceBBQueryFunc(cf)
        pymunk._chipmunk.cpSpaceBBQuery(self.space._space,
                                        pymunk._chipmunk.cpBB(*bbox),
                                        layers,
                                        group,
                                        f,
                                        None)

        return query_hits

    def segment_query(self, start, end, first=False, layers= -1, group=0):
        if first:
            return self.space.segment_query_first(start, end, layers, group)
        else:
            return self.space.segment_query(start, end, layers, group)

    def point_query(self, point, first=False, layers= -1, group=0):
        if first:
            return self.space.point_query_first(point, layers, group)
        else:
            return self.space.point_query(point, layers, group)


class GraphicsService(AbstractService):
    """
    The GraphicsService is responsible for drawing objects and managing 
    graphical representations of the game objects.
    """
    priority = 1

    def __init__(self):
        """
        Initializes the GraphicsService.
        """
        self.batch = pyglet.graphics.Batch()
        self.groups = {}
        self.debug_draw = False

        self.fps = pyglet.clock.ClockDisplay()

    def get_display_group(self, index):
        if index in self.groups:
            return self.groups[index]
        else:
            group = pyglet.graphics.OrderedGroup(index)
            self.groups[index] = group
            return group

    def on_draw(self):
        """
        Draws all objects registerd in the batch.
        """

        self.batch.draw()
        self.fps.draw()

    def on_object_added(self, obj):
        """
        Adds an object to the drawing batch.
        """
        group = self.get_display_group(obj.group_index)

        if obj.image_path is not None:
            image = engine.resource.image(obj.image_path)
            image.anchor_x = image.width / 2
            image.anchor_y = image.height / 2
            obj.sprite = pyglet.sprite.Sprite(image, group=group,
                                              batch=self.batch)
            obj.sprite.position = obj.position

        elif obj.animation_path is not None:
            animation = engine.resource.animation(obj.animation_path,
                                                  obj.animation_tiling,
                                                  obj.animation_duration)

            #TODO: not working...
            #animation.add_to_texture_bin(bin)

            obj.sprite = pyglet.sprite.Sprite(animation, group=group,
                                              batch=self.batch)
            obj.sprite.position = obj.position
            #obj.sprite.x -= animation.get_max_width() * obj.scale / 2
            #obj.sprite.y -= animation.get_max_height() * obj.scale / 2

            @obj.sprite.event
            def on_animation_end():
                obj.on_animation_end()
        else:
            raise Exception("No image path specified.")

        obj.sprite.rotation = obj.angle
        obj.sprite.scale = obj.scale

    def on_object_removed(self, obj):
        """
        Removes an object from the drawing batch.
        """
        obj.sprite.delete()
        pass # TODO, or maybe not :)

class InputService(AbstractService):
    """
    Service for gathering and redirecting input signals.
    """
    def __init__(self, window):
        """
        Initializes the service and sets up the window handlers.
        """
        self.input_handlers = {}
        window.set_handler('on_key_press', self.on_key_press)
        window.set_handler('on_key_release', self.on_key_release)

        """
        @window.event
        def on_key_press(key, modifiers):
            self.on_key_press(key, modifiers)
        @window.event
        def on_key_release(key, modifiers):
            self.on_key_release(key, modifiers)"""

    def on_key_press(self, key, modifiers):
        """
        TODO document
        """
        if key not in self.input_handlers:
            return

        obj, handler = self.input_handlers[key]
        if handler is not None:
            if callable(getattr(obj, handler)):
                getattr(obj, handler)(True)
            else:
                setattr(obj, handler, True)
        else:
            obj.on_key_press(key, modifiers)

        return pyglet.event.EVENT_HANDLED

    def on_key_release(self, key, modifiers):
        """
        TODO document
        """
        if key not in self.input_handlers:
            return

        obj, handler = self.input_handlers[key]
        if handler is not None:
            if callable(getattr(obj, handler)):
                getattr(obj, handler)(False)
            else:
                setattr(obj, handler, False)
        else:
            obj.on_key_release(key, modifiers)

        return pyglet.event.EVENT_HANDLED

    def register_input_handler(self, key, obj, handler=None):
        """
        TODO document
        """
        self.input_handlers[key] = (obj, handler)

class ResourceService(AbstractService):
    """
    Service for handling (loading/unloading) resources (images, sounds, 
    texts...) and managing their locations.
    """
    def __init__(self, *args, **kwargs):
        self.resources = {}

    def process_resource_file(self, path="resources.xml"):
        import xml.etree.cElementTree as xml
        tree = xml.parse(path)
        locations = [location.path for location in tree.findall("/Locations")]

    def add_resource_location(self, *locations):
        pyglet.resource.path.extend(locations)
        pyglet.resource.reindex()

    def remove_resource_location(self, *locations):
        for location in locations:
            pyglet.resource.path.remove(location)
        pyglet.resource.reindex()

    def image(self, filename):
        try:
            return self.resources[filename]
        except KeyError:
            image = pyglet.resource.image(filename)
            self.resources[filename] = image
            return image

    def animation(self, filename, tiling, duration):
        new_name = "animation_" + filename
        try:
            return self.resources[new_name]
        except KeyError:
            image = self.image(filename)
            seq = pyglet.image.ImageGrid(image, *tiling)

            for image in seq:
                image.anchor_x = image.width / 2
                image.anchor_y = image.height / 2

            frame_duration = duration / (tiling[0] * tiling[1])
            animation = pyglet.image.Animation.from_image_sequence(seq,
                                                                   frame_duration)

            self.resources[new_name] = animation
            return animation

    def sound(self, filename):
        pass

class MessageService(AbstractService):
    """
    Service for a (delayed) delivery of messages between services 
    and game objects.
    """

    priority = 6

    class Message(object):
        """
        Helper class for messages.
        """
        def __init__(self, receivers, message, timestamp, *args, **kwargs):
            self.receivers = receivers
            self.message = message
            self.timestamp = timestamp
            self.args = args
            self.kwargs = kwargs

        def send(self):
            """
            Sends the message. i.e calls the according function with
            the saved parameters from all saved recipients.
            """
            for receiver in self.receivers:
                getattr(receiver, self.message)(*self.args, **self.kwargs)

    def __init__(self, *args, **kwargs):
        """
        Initializes a MessageService instance.
        """
        self.queue = []     # the main message queue of the service
        self.timestamp = 0.

    def send_message(self, receivers, message, delay=0., *args, **kwargs):
        """
        Send a (delayed) message to a list of receivers.
        """
        #TODO get current timestamp
        timestamp = 0
        # check if receivers are iterable, else create a 
        # tuple with a single value
        try:
            iter(receivers)
        except TypeError:
            receivers = (receivers,)

        # store a new message object in the message queue 
        msg = MessageService.Message(receivers, message, self.timestamp + delay,
                                     *args, **kwargs)
        self.queue.append(msg)
        self.queue.sort(key=lambda msg: msg.timestamp)

    def on_tick(self, dt):
        """
        Walk through all messages and send all which are to be dispatched.
        This should be a sorted list, so we can stop after the first one that
        has a higher timestamp than the current.
        """
        #TODO get current timestamp
        self.timestamp += dt
        for msg in self.queue:
            if msg.timestamp < self.timestamp:
                msg.send()
                self.queue.remove(msg)
            else:
                break
