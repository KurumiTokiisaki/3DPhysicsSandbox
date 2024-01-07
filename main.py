import copy
import math

import panda3d.core
from panda3d.core import *
from panda3d.core import AmbientLight, DirectionalLight
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from panda3d.core import MeshDrawer2D
from direct.showbase.ShowBaseGlobal import globalClock
from globalFunctions import *


class Main(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # initial game window properties
        self.windowSize = (1500, 1000)
        self.windowProperties = WindowProperties()
        self.windowProperties.setSize(self.windowSize)
        self.win.requestProperties(self.windowProperties)

        # time since last frame
        self.dt = 1 / 144

        # add the main function to the task manager
        self.taskMgr.add(self.main, 'update')

        self.pause = False

        # border size (x, y, z)
        self.worldBorder = Vec3(100, 100, 100)

        # sprite lists
        self.points = []
        self.colliders = []
        self.collisionRects = []

    # create a point and add it to the points list
    def createPoint(self, radius, cords, oldCords):
        self.points.append(Point(radius, cords, oldCords, 1000))

    # load the points into the game window
    def loadActors(self):
        # render points
        for p in self.points:
            p.reparentTo(self.render)
        for c in self.colliders:
            c.reparentTo(self.render)
        for r in self.collisionRects:
            r.reparentTo(self.render)

    def main(self, task):
        if not self.pause:
            for p in range(len(self.points)):
                self.points[p].physics()

        return task.cont


class Point(Actor):
    def __init__(self, radius, cords, oldCords, density):
        Actor.__init__(self, "sphere.glb")
        self.radius = radius
        self.updateSize()
        self.collisionRadius = radius
        self.cords = cords  # (x, z, y)
        self.density = density
        self.mass = (4 / 3) * math.pi * (self.radius ** 3) * self.density
        self.oldCords = oldCords
        self.velocity = Vec3(0, 0, 0)
        self.acceleration = Vec3(0, 0, 0)
        self.force = Vec3(0, 0, 0)
        self.circularForce = Vec3(0, 0, 0)
        self.magneticForce = Vec3(0, 0, 0)

    def physics(self):
        self.circularMotion(hadronCollider)

        self.acceleration = self.force / self.mass
        for axis in range(3):
            self.oldCords[axis] -= self.acceleration[axis] * (game.dt ** 2)  # s = ½at²

        # Verlet integration
        self.velocity = (self.cords - self.oldCords) / game.dt

        # make previous frame's cords a copy of current frame's cords
        self.oldCords = copy.deepcopy(self.cords)

        # move the point
        self.cords += self.velocity * game.dt
        self.setPos(self.cords)

    def circularMotion(self, c):
        radius = distance(c.cords, self.cords)
        resultV = math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2 + self.velocity[2] ** 2)
        resultF = self.mass * (resultV ** 2) / radius
        angle = getThreeDAngle(c.cords, self.cords, 'y')
        self.circularForce[0] = resultF * sin(angle[0]) * cos(angle[1])

    def updateSize(self):
        self.set_scale(self.radius)


class Collider:
    def __init__(self, outerRadius, innerRadius, thickness):
        self.cords = Vec3(0, 0, 0)
        self.outerRad = outerRadius
        self.innerRad = innerRadius
        self.thickness = thickness


game = Main()

game.createPoint(1, Vec3(0, 100, 0), Vec3(0, 100, 0))
hadronCollider = Collider(69, 10, 1)
# game.createPoint(2, Vec3(-33, 100, 0), Vec3(-33, 100, 0))

game.loadActors()
game.run()
