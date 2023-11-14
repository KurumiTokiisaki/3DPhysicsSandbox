import copy
from panda3d.core import WindowProperties
from panda3d.core import AmbientLight, DirectionalLight
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from panda3d.core import Vec3, Vec4
from panda3d.core import MeshDrawer2D
from direct.showbase.ShowBaseGlobal import globalClock
import math

class Main(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # initial game window properties
        self.windowSize = (1500, 1000)
        self.windowProperties = WindowProperties()
        self.windowProperties.setSize(self.windowSize)
        self.win.requestProperties(self.windowProperties)

        # time since last frame
        self.dt = globalClock.getDt()

        # add the main function to the task manager
        self.taskMgr.add(self.main, 'update')

        self.pause = False

        # border size (x, y, z)
        self.worldBorder = Vec3(100, 100, 100)

        # sprite lists
        self.points = []
        self.collisionRects = []

    # create a point and add it to the points list
    def createPoint(self, radius, cords, oldCords):
        self.points.append(Point(radius, cords, oldCords))

    # load the points into the game window
    def loadActors(self):
        # render points
        for p in self.points:
            p.sphere.reparentTo(self.render)

    # run physics on all points
    def physics(self):
        # print(self.points[0].cords)
        # input(self.points[0].oldCords)
        for p in range(len(self.points)):
            self.points[p].move()

    def detectDrag(self):
        

    def main(self, task):
        self.dt = globalClock.getDt()
        if not self.pause:
            self.physics()

        return task.cont


class Point:
    def __init__(self, radius, cords, oldCords):
        self.sphere = Actor("sphere.glb")
        self.physics = True
        self.radius = radius
        self.updateSize()
        self.collisionRadius = radius
        self.cords = cords
        self.oldCords = oldCords
        self.velocity = Vec3(0, 0, 0)

    def move(self):
        # Verlet integration
        self.velocity = self.cords - self.oldCords

        # make previous frame's cords a copy of current frame's cords
        self.oldCords = copy.deepcopy(self.cords)

        # move the point
        self.cords += self.velocity
        self.sphere.setPos(self.cords)

    def updateSize(self):
        self.sphere.set_scale(self.radius)


game = Main()

game.createPoint(1, Vec3(-30, 100, 0), Vec3(-30 - 1 / 144, 100, 0))
game.createPoint(2, Vec3(-33, 100, 0), Vec3(-33, 100, 0))

game.loadActors()
game.run()
