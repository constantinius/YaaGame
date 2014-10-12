import pyglet
from engine.service import ServiceManager

class Application(object):
    """
    A wrapper class for arbitrary application set-up
    and tear-down mechanics. Incorporates a window 
    and a ServiceManager.
    """
    
    window_size = 640, 480
    
    def __init__(self):
        # create a service manager
        self.mgr = ServiceManager()
        
        # create a new window
        self.window = pyglet.window.Window(width = self.window_size[0],
                                           height = self.window_size[1])
        
        # set up window draw events
        @self.window.event
        def on_draw():
            self.window.clear()
            self.mgr.send_broadcast('on_draw')

        # set up tick events
        self.window.register_event_type('on_update')
        def tick(dt):
            self.mgr.send_broadcast('on_tick', dt)
            self.window.dispatch_event('on_update', dt)
        pyglet.clock.schedule(tick)
        
    def setup(self):
        """
        Interface to set up the Application.
        This is a good spot to set up all the services
        or the initial objects for the game.
        """
        pass
    
    def teardown(self):
        """
        Interface to tear down the Application.
        """
        pass
    
    def run(self):
        """
        Call this method to start the game. First 
        the Application.setup() method is called
        before the mainloop is started.
        """
        self.setup()
        self.mgr.send_broadcast('on_init', self.mgr)
        pyglet.app.run()
        self.teardown()