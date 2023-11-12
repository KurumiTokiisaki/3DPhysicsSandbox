import panda3d
from panda3d.core import WindowProperties
from panda3d.core import AmbientLight, DirectionalLight
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from panda3d.core import Vec3, Vec4
from panda3d.core import MeshDrawer2D
from direct.showbase.ShowBaseGlobal import globalClock


class Main(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # initial game window properties
        self.windowSize = (1500, 1000)
        self.windowProperties = WindowProperties()
        self.windowProperties.setSize(self.windowSize)
        self.win.requestProperties(self.windowProperties)

        # add the physics function to the task manager
        self.taskMgr.add(self.main, 'update')
        self.pause = False

        # border size (x, y, z)
        self.worldBorder = Vec3(100, 100, 100)
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
        for p in range(len(self.points)):
            self.points[p].move()

    def main(self, task):
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
        self.n = False

    def move(self):
        # cause the point to "vibrate" back and forth 1 unit each frame
        if self.n:
            self.cords += Vec3(1, 0, 0)
            self.n = False
        else:
            self.cords -= Vec3(1, 0, 0)
            self.n = True

        self.sphere.setPos(self.cords)

    def updateSize(self):
        self.sphere.set_scale(self.radius)


game = Main()

game.createPoint(1, Vec3(-30, 100, 0), Vec3(0, 100, 0))

game.loadActors()
game.run()
