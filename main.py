from engine.application import Application
from engine.service import (
    ServiceManager, GameObjectService,
    PhysicsService, GraphicsService,
    InputService, ResourceService,
    MessageService,
    AbstractService
)
from engine.gui import (
    GuiService, AbstractGui
)
from engine.object import (
    GameObject, GraphicalObject,
    PhysicalObject, CombinedObject
)
import engine.graphics
import pyglet
import kytten
import pymunk
from pymunk import Vec2d
import random
import math
import os.path
import sys
import cPickle as pickle

DEBUG_DRAW = True


class SpaceShip(CombinedObject):
    image_path = "SpaceShip2.png"
    points = [(32, 0),
              (-32, 32),
              (-32, -32)]
    mass = 1
    maximum_speed = 350
    group = 1
    scale = 0.75

    def __init__(self, *args, **kwargs):
        """
        Create a new spaceship object.
        """
        super(SpaceShip, self).__init__(*args, **kwargs)

        self.is_turning_left = False
        self.is_turning_right = False
        self.is_accellerating = False
        self.is_shooting = False
        self.is_special = False

        self.next_shot = 0.
        self.next_special = 0.

        self.accelleration = 50
        self.turning_speed = 6
        self.body.angular_velocity = 0

    def update(self, dt):
        if self.is_turning_left and not self.is_turning_right:
            self.body.angular_velocity = self.turning_speed
        elif self.is_turning_right and not self.is_turning_left:
            self.body.angular_velocity = -self.turning_speed

        if self.is_accellerating:
            self.body.apply_force(self.body.rotation_vector *
                                  self.accelleration)
        else:
            self.body.reset_forces()

        if self.next_shot > 0.:
            self.next_shot -= dt
        if self.next_special > 0.:
            self.next_special -= dt

        if self.is_shooting and self.next_shot <= 0.:
            # reset time to next shot
            self.next_shot = 0.5

            # spawn a new Shot object
            position = self.body.position + self.body.rotation_vector * 40
            velocity = self.body.rotation_vector * Shot.initial_speed \
                       + self.body.velocity
            self.object_service.add_object(Shot(position=position,
                                                velocity=velocity,
                                                angle=self.body.angle))

        if self.is_special and self.next_special <= 0.:
            start = self.body.position
            end = self.body.position + self.body.rotation_vector * 10000

            ps = ServiceManager.instance[PhysicsService]
            info = ps.segment_query(start, end, True, group=1)

            if (info is not None
                and isinstance(info.shape.body.object, Asteroid)):
                self.next_special = 0.5
                position = self.body.position + self.body.rotation_vector * 40
                velocity = self.body.rotation_vector * 100 + self.body.velocity
                missile = Missile(target=info.shape.body.object,
                                  position=position,
                                  velocity=velocity,
                                  angle=self.body.angle)
                self.object_service.add_object(missile)

    def turn_left(self, value=True):
        self.is_turning_left = value
        if not value and not self.is_turning_right:
            self.body.angular_velocity = 0

    def turn_right(self, value=True):
        self.is_turning_right = value
        if not value and not self.is_turning_left:
            self.body.angular_velocity = 0

    def on_collision(self, other, arbiter):
        if isinstance(other, Asteroid):
            #spawn an explosion
            self.object_service.add_object(Explosion(position=arbiter.contacts[0].position))
            self.object_service.add_object(Explosion(position=self.body.position,
                                                     scale=2))

            # spawn some more explosions after time
            ms = ServiceManager.instance[MessageService]
            for _ in range(3):
                ms.send_message(self.object_service,
                                'add_object',
                                random.random(),
                                Explosion(position=self.body.position + Vec2d((random.random() - 0.5) * 100,
                                                                              (random.random() - 0.5) * 100),
                                          scale=random.random() + 1))

            self.object_service.remove_object(self)
            return True
        else:
            return False


class Asteroid(CombinedObject):
    image_path = "Asteroid1.png"
    radius = 32
    mass = 1

    def on_collision(self, other, arbiter):
        if isinstance(other, Shot) or isinstance(other, SpaceShip):
            if self.scale > 0.75:
                direction = other.body.velocity
                direction.rotate(math.pi / 2)

                velocity = direction.normalized() * 300 + self.body.velocity
                position = self.body.position
                self.object_service.add_object(Asteroid(position=position,
                                                        velocity=velocity,
                                                        scale=self.scale / 2))
                self.object_service.add_object(Asteroid(position=position,
                                                        velocity= -velocity,
                                                        scale=self.scale / 2))

            # chance to spawn a coin
            if random.random() <= Pickup.spawn_chance:
                self.object_service.add_object(Pickup(position=self.body.position,
                                                      velocity=self.body.velocity))

            self.object_service.remove_object(self)
        # return true anyways
        return True


class Shot(CombinedObject):
    image_path = "shot.png"
    points = [(8, 0),
              (-8, 4),
              (-8, -4)]
    mass = 1
    initial_speed = 700
    maximum_speed = SpaceShip.maximum_speed + initial_speed
    lifetime = 0.75
    scale = 0.3

    def __init__(self, *args, **kwargs):
        super(Shot, self).__init__(*args, **kwargs)
        self.lifetime = kwargs.get('lifetime', self.lifetime)

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0.:
            self.object_service.remove_object(self)

    def on_collision(self, other, arbiter):
        if isinstance(other, Asteroid):
            #spawn an explosion
            explosion = Explosion(position=arbiter.contacts[0].position)
            self.object_service.add_object(explosion)
            self.object_service.remove_object(self)
            return True
        else:
            return False


class Missile(Shot):
    image_path = "missile.png"
    maximum_speed = SpaceShip.maximum_speed
    scale = 1

    def __init__(self, target, *args, **kwargs):
        super(Missile, self).__init__(*args, **kwargs)
        self.target = target
        self.lifetime = 10.
        self.last_cloud = 0.

    def update(self, dt):
        #TODO: FIXME
        Shot.update(self, dt)

        mis_pos = self.body.position
        #mis_vel = self.body.velocity
        tar_pos = self.target.body.position
        tar_vel = self.target.body.velocity

        self.target_point = tar_pos - mis_pos + tar_vel# - mis_vel

        desired_vector = (self.target_point) / self.maximum_speed
        missile_dir = self.body.rotation_vector

        angle_diff = desired_vector.get_angle_between(missile_dir)
        self.body.angular_velocity = -angle_diff * 10


        #TODO remove this
        #desired_vector = tar_pos - mis_pos


        term = math.radians(45) - min(abs(angle_diff), math.radians(45))
        self.body.apply_force(missile_dir * 1000 * term)
        #self.body.velocity = desired_vector.normalized() * self.maximum_speed

        # check if a cloud needs to be created
        if self.last_cloud > 0.:
            self.last_cloud -= dt
        else:
            # spawn a new cloud object to show the moved path
            self.last_cloud = 0.05
            cloud = Cloud(position=self.sprite.position)
            self.object_service.add_object(cloud)

        self.desired_vector = desired_vector

    def debug_draw(self):
        #return
        #print self.body.position, self.target_point
        engine.graphics.draw_line(self.body.position,
                                  #self.target.body.position,
                                  self.body.position + self.target_point,
                                  #self.body.position + self.desired_vector * 1000,
                                  (1.0, 0, 0, 1.0))

        engine.graphics.draw_line(self.body.position,
                                  self.target.body.position,
                                  (0, 1.0, 0, 1.0))


class Cloud(GraphicalObject):
    animation_path = "simple_explosion_2.png"
    animation_tiling = (1, 8)
    animation_duration = 0.8
    group_index = 0

    def on_animation_end(self):
        self.object_service.remove_object(self)


class Explosion(GraphicalObject):
    animation_tiling = (4, 4)
    animation_duration = 0.5
    group_index = 2

    def __init__(self, *args, **kwargs):
        if 'animation_path' not in kwargs:
            kwargs['animation_path'] = "explosion%d.png" % random.randint(0, 6)
        super(Explosion, self).__init__(*args, **kwargs)

    def on_animation_end(self):
        self.object_service.remove_object(self)


class Pickup(CombinedObject):
    image_path = "coin.png"
    radius = 16
    mass = 0.000001
    group = 2

    spawn_chance = 0.5

    def on_collision(self, other, arbiter):
        if isinstance(other, SpaceShip):
            ServiceManager.instance[YaaGameService].points += 500
            self.object_service.remove_object(self)
            return False
        return True


class Marker(GraphicalObject):
    image_path = "spaceship.png"
    display_group = 11
    angle = -math.pi / 2
    scale = 0.5


class YaaGameService(AbstractService):
    def __init__(self, window, window_size):
        self.window_size = window_size
        window.set_handler('on_escape', self.on_escape)
        self.asteroid_count = 0
        self.font = pyglet.font.load('', 36, bold=True)
        self.point_label = pyglet.font.Text(self.font,
                                            '',
                                            color=(.5, .5, .5, .5),
                                            x=window_size[0] - 10,
                                            y=window_size[1] - 10)
        self.point_label.halign = 'right'
        self.point_label.valign = 'top'
        self.points = 0
        self.game_started = False
        self.lifes = []

        self.labels = []
        self.labels.append(self.point_label)

    def on_init(self, mgr):
        mgr[InputService].register_input_handler(pyglet.window.key.ESCAPE, self, 'on_escape')

    def on_escape(self, value):
        if value:
            self.mgr[GuiService].show_gui("main")

    def on_object_added(self, obj):
        if isinstance(obj, SpaceShip):
            self.is_ship_dead = False

            # set up SpaceShip input event handlers
            self.mgr[InputService].register_input_handler(pyglet.window.key.A, obj, 'turn_left')
            self.mgr[InputService].register_input_handler(pyglet.window.key.D, obj, 'turn_right')
            self.mgr[InputService].register_input_handler(pyglet.window.key.W, obj, 'is_accellerating')
            self.mgr[InputService].register_input_handler(pyglet.window.key.SPACE, obj, 'is_shooting')
            self.mgr[InputService].register_input_handler(pyglet.window.key.LCTRL, obj, 'is_special')

        elif isinstance(obj, Asteroid):
            self.asteroid_count += 1

    def on_object_removed(self, obj):
        if isinstance(obj, SpaceShip):
            # recreate the ship again, if lifes are left
            marker = self.lifes.pop()
            self.mgr[GameObjectService].remove_object(marker)
            if len(self.lifes) != 0:
                self.mgr[MessageService].send_message(self,
                                                      'on_recreate_spaceship',
                                                      delay=2.)
            else:
                """label = pyglet.font.Text(self.font,
                                         'You achieved %i points!' % self.points,
                                         color=(.5, .5, .5, .5),
                                         x=self.window_size[0]/2,
                                         y=self.window_size[1]/2,
                                         halign='center',
                                         valign='baseline')
                self.labels.append(label)"""
                self.mgr[GuiService].show_gui("submithighscore")

        elif isinstance(obj, Asteroid):
            self.asteroid_count -= 1
            if self.asteroid_count == 0 and self.game_started:
                # spawn new asteroids after some time
                self.mgr[MessageService].send_message(self,
                                                      'on_spawn_asteroids',
                                                      delay=3.)
            if self.game_started:
                # calculate points
                self.points += (2. - obj.scale) * 100

    def is_space_empty(self, position, size, layers= -1, group=0):
        size /= 2.
        bbox = (position[0] - size, position[1] - size,
                position[0] + size, position[1] + size)
        objects = self.mgr[PhysicsService].bbox_query(bbox, layers, group)
        if len(objects) == 0:
            return True
        else:
            return False

    def find_empty_space(self, size, tries=100):
        for _ in range(tries):
            position = (random.random() * self.window_size[0],
                        random.random() * self.window_size[1])
            if self.is_space_empty(position, size):
                return position
        raise Exception("Could not find empty space")

    def on_recreate_spaceship(self):
        self.game_started = True
        if self.is_space_empty(Vec2d(self.window_size) / 2, 80):
            ship = SpaceShip(position=(self.window_size[0] / 2, self.window_size[1] / 2))
            self.mgr[GameObjectService].add_object(ship)
        else:
            self.mgr[MessageService].send_message(self, 'on_recreate_spaceship',
                                                  delay=0.1)

    def on_spawn_asteroids(self):
        for _ in range(5):
            velocity = (random.random() - 0.5) * 100, (random.random() - 0.5) * 100
            scale = random.random() + 0.5
            size = Asteroid.radius * scale
            position = self.find_empty_space(size)
            asteroid = Asteroid(position=position, velocity=velocity, scale=scale)
            self.mgr[GameObjectService].add_object(asteroid)

    def on_start(self):
        self.mgr[GameObjectService].clear()
        self.mgr[GuiService].hide_gui("main")

        self.mgr[MessageService].send_message(self, 'on_recreate_spaceship', 0.5)
        self.on_spawn_asteroids()
        self.points = 0
        for i in range(3):
            marker = Marker(position=(i * 50 + 50,
                                        self.window_size[1] - 50))
            self.lifes.append(marker)
            self.mgr[GameObjectService].add_object(marker)

    def on_draw(self):
        #draw points
        self.point_label.text = str(int(self.points))

        for label in self.labels:
            label.draw()

    def save_highscore(self, name):
        highscores = self.get_highscores()
        highscores.append((self.points, name))
        highscores.sort()
        highscores.reverse()
        pickle.dump(highscores, open('highscores.dat', 'w+'))

    def get_highscores(self):
        try:
            return pickle.load(open('highscores.dat'))
        except IOError:
            return []


class MainMenu(AbstractGui):
    def __init__(self, name="main"):
        AbstractGui.__init__(self, name)

    def _build_gui(self, window, batch, group):
        def exit_game():
            sys.exit(0)

        def show_highscores():
            ServiceManager.instance[GuiService].show_gui("showhighscores")

        def show_options():
            ServiceManager.instance[GuiService].show_gui("options")

        return kytten.Dialog(
            kytten.TitleFrame("Main Menu",
                kytten.VerticalLayout([
                    kytten.Button("Start", on_click=ServiceManager.instance[YaaGameService].on_start),
                    kytten.Button("Highscores", on_click=show_highscores),
                    kytten.Button("Options", on_click=show_options),
                    kytten.Button("Quit", on_click=exit_game),
                ], align=kytten.HALIGN_LEFT),
            ),
            window=window, theme=self.theme, batch=batch, group=group,
            anchor=kytten.ANCHOR_CENTER,
        )


class OptionsGui(AbstractGui):
    def __init__(self, name="options"):
        AbstractGui.__init__(self, name)

    def _build_gui(self, window, batch, group):
        dialog = None

        def on_enter(dialog):
            self.hide()
            pass
            # TODO: save all options

        def on_save():
            on_enter(dialog)

        def on_cancel(_=None):
            self.hide()

        dialog = kytten.Dialog(
            kytten.TitleFrame("Options",
                kytten.VerticalLayout([
                    kytten.GridLayout([
                        #TODO fill in options
                    ]),
                    kytten.HorizontalLayout([
                        kytten.Button("Save", on_click=on_save),
                        kytten.Button("Cancel", on_click=on_cancel)
                    ])
                ], align=kytten.HALIGN_LEFT),
            ),
            window=window, theme=self.theme, batch=batch, group=group,
            anchor=kytten.ANCHOR_CENTER, on_enter=on_enter, on_escape=on_cancel
        )
        return dialog


class ShowHighscoresGui(AbstractGui):
    def __init__(self, name="showhighscores"):
        AbstractGui.__init__(self, name)

    def _build_gui(self, window, batch, group):
        highscores = ServiceManager.instance[YaaGameService].get_highscores()

        frmt = ''
        for score, name in highscores[:10]:
            frmt += '{align "left"} %s \n {align "right"} %s {align "left"}{}\n\n' % (name, score)

        return kytten.Dialog(
            kytten.TitleFrame("Highscores",
                kytten.VerticalLayout([
                    kytten.GridLayout([
                        [kytten.Label(name), kytten.Label("%i" % int(score))] \
                        for score, name in highscores
                    ]),
                    kytten.Button("Close", on_click=self.hide)
                ], align=kytten.HALIGN_LEFT),
            ),
            window=window, theme=self.theme, batch=batch, group=group,
            anchor=kytten.ANCHOR_CENTER,
        )


class SubmitHighscoreGui(AbstractGui):
    def __init__(self, name="submithighscore"):
        AbstractGui.__init__(self, name)

    def _build_gui(self, window, batch, group):
        #points = ServiceManager.instance[YaaGameService].points
        dialog = None

        def on_enter(dialog):
            name = dialog.get_values()['name']
            ServiceManager.instance[YaaGameService].save_highscore(name)
            self.hide()

        def on_escape(dialog):
            self.hide()

        def on_submit():
            on_enter(dialog)

        def on_cancel():
            on_escape(dialog)

        dialog = kytten.Dialog(
            kytten.TitleFrame("Submit Highscore",
                kytten.VerticalLayout([
                    kytten.GridLayout([
                        [kytten.Label("Name"), kytten.Input("name", "",
                                                            max_length=20)]
                    ]),
                    kytten.HorizontalLayout([
                        kytten.Button("Submit", on_click=on_submit),
                        kytten.Button("Cancel", on_click=on_cancel)
                    ])
                ], align=kytten.HALIGN_LEFT),
            ),
            window=window, theme=self.theme, batch=batch, group=group,
            anchor=kytten.ANCHOR_CENTER, on_enter=on_enter
        )

        return dialog


class YaaGame(Application):
    window_size = 700, 700

    def setup(self):
        # set up game services
        mgr = self.mgr
        bounds = (-10, -10, self.window_size[0] + 10, self.window_size[1] + 10)
        mgr += PhysicsService(bounds=bounds)
        mgr += GraphicsService()
        mgr += GameObjectService()
        mgr += InputService(window=self.window)
        mgr += ResourceService()
        mgr += YaaGameService(self.window, self.window_size)
        mgr += MessageService()
        mgr += GuiService(window=self.window, group_index=5)

        # setup resource locations
        mgr[ResourceService].add_resource_location("graphics", "sounds")

        mgr[InputService].register_input_handler(pyglet.window.key.R,
                                                 self.mgr[PhysicsService],
                                                 'switch_debug_draw')

        # create some Asteroids and add them to the object manager
        for _ in range(5):
            position = (random.random() * self.window_size[0],
                        random.random() * self.window_size[1])
            velocity = ((random.random() - 0.5) * 100,
                        (random.random() - 0.5) * 100)
            scale = random.random() + 0.5
            asteroid = Asteroid(position=position,
                                velocity=velocity,
                                scale=scale)

            self.mgr[GameObjectService].add_object(asteroid)

        mgr[GuiService].add_gui(OptionsGui())
        mgr[GuiService].add_gui(ShowHighscoresGui())
        mgr[GuiService].add_gui(SubmitHighscoreGui())
        mgr[GuiService].add_gui(MainMenu())
        mgr[GuiService].show_gui("main")


if __name__ == "__main__":
    app = YaaGame()
    app.run()
