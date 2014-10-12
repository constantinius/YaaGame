from engine.service import (
    AbstractService, GraphicsService,
    ServiceManager
)
import pyglet
import kytten

class GuiService(AbstractService):
    """ Service to manage GUI screens """

    def __init__(self, window, group_index = 1):
        self.guis = {}
        self.window = window
        self.batch = ServiceManager.instance[GraphicsService].batch
        self.group = pyglet.graphics.OrderedGroup(group_index)
    
    def add_gui(self, gui):
        """Add a gui to the manager."""
        assert(isinstance(gui, AbstractGui))
        self.guis[gui.name] = gui
        
    def show_gui(self, name):
        self.guis[name].show(self.window, self.batch,
                             self.group)
    
    def hide_gui(self, name):
        self.guis[name].hide()
        
    def on_draw(self):
        self.batch.draw()

class AbstractGui(object):
    def __init__(self, name):
        self.name = name
        self.root = None
        import os.path
        pth = os.path.abspath(os.path.join('graphics', 'theme'))
        self.theme = kytten.Theme(pth,
            override={
            "gui_color": [64, 128, 255, 255],
            "font_size": 14
        })
        self.visible = False
        
    def _build_gui(self, window, batch, group):
        return kytten.Dialog(
            kytten.TitleFrame("AbstractGui",
                width=200, height=150
            ),
            window=window, batch=batch,
            group=group, theme=self.theme
        )
    
    def show(self, window, batch, group):
        if not self.visible:
            self.root = self._build_gui(window, batch, group)
            self.visible = True
        
    def hide(self):
        if self.visible:
            self.root.teardown()
            self.visible = False
            self.root = None