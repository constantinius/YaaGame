import math


class Property(object):
    def __init__(self):
        self.getter = None
        self.setters = []

    def attach(self, getter, setter, override=False):
        if override or self.getter is None:
            self.getter = getter
        self.setters.append(setter)

    def __get__(self, instance, owner):
        if self.getter:
            return self.getter()
        raise AttributeError

    def __set__(self, instance, value):
        for setter in self.setters:
            setter(value)


class Entity(object):
    models = []

    def __init__(self, *args, **kwargs):
        # set up initial arguments (defined in the Entity subclass)
        initargs = {}
        for argname in dir(self.__class__):
            if not argname.startswith("__"):
                initargs[argname] = getattr(self.__class__, argname)
        initargs.update(kwargs)

        models = {}
        self.properties = {}
        for cls in self.models:
            model = cls(self, *args, **initargs)
            for prop in model.properties():
                self.register_property(*prop)
            models[cls] = model
        self.models = models

    #####################
    #   MODELS          #
    #####################

    def __contains__(self, modelclass):
        """
        Helper function to check if an entity contains a
        specific model by class.
        """
        return modelclass in self.__class__.models

    def get_model(self, modelclass):
        """
        Return the model instance from this entity by
        its model class.
        """
        return self.models[modelclass]

    #####################
    #   PROPERTIES      #
    #####################

    def __getitem__(self, name):
        """
        Get the propery by name. Dispatches the 'get'
        handler of the registered property.
        """
        return self.properties[name][0]()

    def __setitem__(self, name, value):
        """
        """
        for handler in self.properties[name][1]:
            handler(value)

    def _register_property_getter(self, name, handler, override=False):
        """
        Private method to register a property getter
        function for a specific property.
        """
        if name not in self.properties:
            self.properties[name] = [handler, []]
        elif override:
            self.properties[name][0] = handler

    def _register_property_setter(self, name, handler):
        """
        Private method to register a property setter
        function for a specific property.
        """
        if name not in self.properties:
            self.properties[name] = [None, [handler]]
        else:
            self.properties[name][1].append(handler)

    def register_property(self, name, getter=None, setter=None,
                          override=False):
        """
        Register a property by name with its getter
        and setter function.
        """
        if getter is not None:
            self._register_property_getter(name, getter, override)
        if setter is not None:
            self._register_property_setter(name, setter)

    '''def __settattr__(self, name, value):
        """
        Set a property value with the registered setter
        handlers. All handler functions are called.
        """
        if name in self.__dict__:
            self.__dict__[name] = value
        else:
            for handler in self.properties[name][1]:
                handler(value)

    def __getattr__(self, name):
        """
        Get a property value with the registered getter
        handler. This is the first one of list.
        """
        try:
            return getattr(self.__class__, name)
        except AttributeError:
            return self.__dict__['properties'][name][0]()
    '''

    '''
    def register_behavior(self, name, handler):
        """
        Register a behavior by name within the entity.
        """
        self.behaviors[name] = handler

    def __call__(self, name, *args, **kwargs):
        """
        Call a specific registered behavior of one of the
        included models.
        """
        self.behaviors[name](*args, **kwargs)
    '''


class AbstractModel(object):
    behaviors = []

    def __init__(self, entity, *args, **kwargs):
        self.entity = entity

    def properties(self):
        """
        Method to return a list of tuples containing the
        property name, getter, setter and, optionally a
        boolean value indicating if the getter shall override
        an existing one.
        """
        return []


class ImageModel(AbstractModel):

    image_path = None           # path to the static image.
    animation_path = None       # path to the animation image
    animation_tiling = (1, 1)   # the tiling of the animation image
    animation_duration = 1.     # the overall duration of the animation
    scale = 1.                  # the size-scale of the object
    group_index = 1             # the display group index

    def __init__(self, image_path=None, animation_path=None, scale=1.,
                 *args, **kwargs):
        super(ImageModel, self).__init__(*args, **kwargs)

        self.image_path = kwargs.get('image_path', self.image_path)
        self.animation_path = kwargs.get('animation_path', self.animation_path)
        self.scale = kwargs.get('scale', self.scale)
        self.group_index = kwargs.get('group_index', self.group_index)
        self.position = kwargs.get('position', (0, 0))
        self.angle = math.degrees(kwargs.get('angle', 0))

    def _set_scale(self, value): self.sprite.scale = value

    def properties(self):
        return super(ImageModel, self).properties + [
            ('scale', self._get_scale, self._set_scale),
            ('position', self._get_position, self._set_position),
            ('angle', self._get_angle, self._set_angle),
            #('image_path', , )
        ]



