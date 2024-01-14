import copy
import math
import random

import viz
import vizshape
from config import *
from globalFunctions import *


class Slider:
    def __init__(self, xyz, referenceVar, cords, length, pointRadius, maxi, mini, text):
        self.xyz = xyz
        self.var = referenceVar
        self.cords = copy.deepcopy(cords)
        self.length = length
        self.limits = [self.cords[self.xyz] - (self.length / 2), cords[self.xyz] + (self.length / 2)]  # x cords of both ends of the slider
        self.pRad = pointRadius
        self.max = maxi  # maximum variable value
        self.min = mini  # minimum variable value
        self.range = maxi - mini
        self.pointer = vizshape.addSphere(pointRadius, slices=pointResolution)
        self.sliders = [vizshape.addCylinder(length, 0.05), vizshape.addCylinder(pointRadius * 2, 0.02), vizshape.addCylinder(pointRadius * 2, 0.02)]
        self.pCords = copy.deepcopy(self.cords)
        self.pCords[xyz] += (self.var / self.range) * self.length
        self.oldPCords = copy.deepcopy(self.pCords)
        self.pVelocity = [0, 0, 0]
        self.textFront = viz.addText3D('', fontSize=0.1)
        self.textOffset = 0.2
        self.collision = False
        self.dragging = False
        self.text = viz.addText3D(f'{text}', fontSize=0.2)
        self.textPos = [0, 0, 0]

        if xyz == 0:
            self.textPos = [self.cords[0] - (len(text) / 20), self.cords[1] + 0.3, self.cords[2]]
            self.sliders[0].setEuler(90, 90, 0)
        elif xyz == 1:
            self.textPos = [self.cords[0] - (len(text) / 20), self.cords[1] + (self.length / 2) + 0.3, self.cords[2]]
            self.sliders[1].setEuler(90, 90, 0)
            self.sliders[2].setEuler(90, 90, 0)
        elif xyz == 2:
            self.textPos = [self.cords[0], self.cords[1] + 0.3, self.cords[2] + (len(text) / 20)]
            self.text.setEuler(90, 0, 0)
            self.sliders[0].setEuler(0, 90, 0)
        self.text.setPosition(self.textPos)
        self.sliders[0].setPosition(self.cords)
        setPos = copy.deepcopy(self.cords)
        setPos[self.xyz] = self.limits[0]
        self.sliders[1].setPosition(setPos)
        setPos = copy.deepcopy(self.cords)
        setPos[self.xyz] = self.limits[1]
        self.sliders[2].setPosition(setPos)

    def interpolate(self):
        relDist = self.pCords[self.xyz] - self.limits[0]
        ratio = relDist / self.length
        self.var = self.min + (self.range * ratio)

    def drag(self, c, dragging):
        self.dragging = dragging
        if dragging:
            self.collision = detectCollision(c.radius, self.pRad, c.cords, self.pCords)
            if self.collision:
                self.pCords[self.xyz] = copy.deepcopy(c.cords[self.xyz])

    def main(self):
        if self.pCords[self.xyz] < self.limits[0]:
            self.pCords[self.xyz] = copy.deepcopy(self.limits[0])
            self.oldPCords[self.xyz] = copy.deepcopy(self.pCords[self.xyz])
        elif self.pCords[self.xyz] > self.limits[1]:
            self.pCords[self.xyz] = copy.deepcopy(self.limits[1])
            self.oldPCords[self.xyz] = copy.deepcopy(self.pCords[self.xyz])

        self.oldPCords[self.xyz] += 1.5 * getSign(self.pVelocity[self.xyz]) / (calcRate ** 2)  # adds some drag on the slider

        if (abs(self.pVelocity[self.xyz]) < (10 ** -4)) and (not self.collision or not self.dragging):  # if there is to be frictional force on the slider's point and velocity is very small, make velocity 0 to prevent vibration
            self.oldPCords[self.xyz] = copy.deepcopy(self.pCords[self.xyz])

        # Verlet integration
        self.pVelocity[self.xyz] = self.pCords[self.xyz] - self.oldPCords[self.xyz]
        self.oldPCords = copy.deepcopy(self.pCords)
        self.pCords[self.xyz] += self.pVelocity[self.xyz]

        self.interpolate()
        return self.var

    def draw(self, camCords):
        self.pointer.setPosition(self.pCords)
        angle, pos = camAnglePos(camCords, self.pCords, self.pRad ** (1 / 3))
        self.textFront.setEuler(angle)
        self.textFront.setPosition(pos)
        self.textFront.message(f'{round(self.var, 4)}')

        angle, pos = camAnglePos(camCords, self.textPos, 0)
        self.text.setEuler(angle)

    def unDraw(self):
        self.pointer.remove()
        for s in range(len(self.sliders)):
            self.sliders[s].remove()
        self.textFront.remove()
        self.text.remove()


class Point:
    def __init__(self, rad):
        self.cords = [0, 0, 0]
        self.oldCords = [0, 0, 0]
        self.velocity = [0, 0, 0]
        self.radius = rad
        self.point = vizshape.addSphere(self.radius, slices=pointResolution)


class Dial:
    def __init__(self, xyz, referenceVar, cords, cRad, pointRadius, mini, maxi, text):
        self.xyz = xyz
        self.var = referenceVar
        self.cRad = cRad
        self.cords = copy.deepcopy(cords)
        self.min = []
        self.max = []
        self.range = []
        self.circle = []
        self.cAngle = []
        self.cMultiplier = []
        self.tDim = True if len(referenceVar) == 3 else False
        if not self.tDim:
            self.circle.append(vizshape.addTorus(cRad, 0.04))
            self.cAngle.append([0, 90, 0])
            self.circle[0].setPosition(self.cords)
            self.circle[0].setEuler(self.cAngle[0])
        self.p = Point(pointRadius)
        self.p.cords = copy.deepcopy(cords)
        self.p.oldCords = copy.deepcopy(self.p.cords)
        for axis in range(len(referenceVar)):  # used to allow for inheritance in DialThreeD
            self.min.append(mini[axis])
            self.max.append(maxi[axis])
            self.range.append(maxi[axis] - mini[axis])
            if self.tDim:
                self.p.cords[axis] += (self.var[axis] / self.range[axis]) * self.cRad * 2
        if not self.tDim:
            if self.xyz == 0:  # lying down
                self.axes = [0, 2]
            elif self.xyz == 1:  # upright (facing z)
                self.axes = [0, 1]
            else:  # upright (facing x)
                self.axes = [1, 2]
            self.p.cords[self.axes[0]] += (self.var[self.axes[0]] / self.range[self.axes[0]]) * self.cRad * 2
            self.p.cords[self.axes[1]] += (self.var[self.axes[1]] / self.range[self.axes[1]]) * self.cRad * 2
        self.text = text
        self.textFront = viz.addText3D('', fontSize=0.15)
        self.collision = False
        self.dragging = False
        if self.tDim:
            self.anim = CircleAnim(self.p, round(self.cRad) + 2, self.cRad, 0.04, [1, 0, 1], False, -1, 1, 0)

    def drag(self, c, dragging):
        self.dragging = dragging
        if dragging:
            self.collision = detectCollision(c.radius, self.p.radius, c.cords, self.p.cords)
            if self.collision:
                if not self.tDim:
                    self.p.cords[0] = copy.deepcopy(c.cords[0])
                    self.p.cords[1] = copy.deepcopy(c.cords[1])
                else:
                    self.p.cords = copy.deepcopy(c.cords)

    def interpolate(self):
        relDist = []
        ratio = []
        for dim in range(len(self.var)):
            if not self.tDim:
                relDist.append(self.p.cords[self.axes[dim]] - (self.cords[self.axes[dim]] - self.cRad))
            else:
                relDist.append(self.p.cords[dim] - (self.cords[dim] - self.cRad))
            ratio.append(relDist[dim] / (self.cRad * 2))
            self.var[dim] = self.min[dim] + (self.range[dim] * ratio[dim])

    def main(self):
        # self.circularMotion()  # MASSIVE work-in-progress
        self.boundDial()

        if not self.tDim:
            movingAngle = getAbsTwoDAngle([0, 0], [self.p.velocity[self.axes[0]], self.p.velocity[self.axes[1]]])
            self.p.oldCords[self.axes[0]] += 1.25 * getSign(self.p.velocity[self.axes[0]]) * sin(movingAngle) / (calcRate ** 2)  # adds some drag on the dial
            self.p.oldCords[self.axes[1]] += 1.25 * getSign(self.p.velocity[self.axes[1]]) * cos(movingAngle) / (calcRate ** 2)
        else:
            movingAngle = getAbsThreeDAngle([0, 0, 0], self.p.velocity, 'y')
            self.p.oldCords[0] += 1.25 * getSign(self.p.velocity[0]) * cos(movingAngle[1]) * sin(movingAngle[0]) / (calcRate ** 2)  # adds some drag on the dial
            self.p.oldCords[1] += 1.25 * getSign(self.p.velocity[1]) * sin(movingAngle[1]) / (calcRate ** 2)
            self.p.oldCords[2] += 1.25 * getSign(self.p.velocity[2]) * cos(movingAngle[1]) * cos(movingAngle[0]) / (calcRate ** 2)

        for axis in range(len(self.var)):
            if (abs(self.p.velocity[axis]) < (10 ** -4)) and (not self.dragging):  # if there is to be frictional force on the slider's point and velocity is very small, make velocity 0 to prevent vibration
                self.p.oldCords[axis] = copy.deepcopy(self.p.cords[axis])

        # Verlet integration
        for axis in range(3):
            self.p.velocity[axis] = self.p.cords[axis] - self.p.oldCords[axis]
        self.p.oldCords = copy.deepcopy(self.p.cords)
        for axis in range(3):
            self.p.cords[axis] += self.p.velocity[axis]

        self.interpolate()

        return self.var

    def circularMotion(self):
        resultAcc = (distance([0, 0, 0], self.p.velocity) ** 2) / self.cRad
        angle = getAbsTwoDAngle([self.cords[0], self.cords[1]], [self.p.cords[0], self.p.cords[1]])
        quartiles = [self.p.cords[0] <= self.cords[0], self.p.cords[1] <= self.cords[1]]
        acc = [resultAcc * sin(angle) * TFNum(quartiles[0]), resultAcc * cos(angle) * TFNum(quartiles[1])]
        self.p.oldCords[0] -= acc[0]  # / calcRate ** 2
        self.p.oldCords[1] -= acc[1]  # / calcRate ** 2

    # prevent "dialer" (point) from exiting the dial
    def boundDial(self):
        if distance(self.cords, self.p.cords) > self.cRad:
            self.p.cords = copy.deepcopy(self.p.oldCords)

    def draw(self, camCords):
        self.p.point.setPosition(self.p.cords)

        if not self.tDim:
            self.textFront.message(f'{self.text[0]}: {round(self.var[0], 4)}\n{self.text[1]}: {round(self.var[1], 4)}')
            self.textFront.setPosition(self.p.cords[0] - 0.3, self.p.cords[1] - 0.2, self.p.cords[2] - 0.2)
        else:
            self.textFront.message(f'{self.text[0]}: {round(self.var[0], 4)}\n{self.text[1]}: {round(self.var[1], 4)}\n{self.text[2]}: {round(self.var[2], 4)}')
        angle, pos = camAnglePos(camCords, self.p.cords, self.p.radius ** (1 / 3))
        self.textFront.setEuler(angle)
        self.textFront.setPosition(pos)

        if self.tDim:
            self.anim.draw(distance([0, 0, 0], self.p.velocity) * physicsTime * 0.2 + 0.1)

    def unDraw(self):
        self.p.point.remove()
        self.anim.unDraw()
        self.textFront.remove()


class Manual:
    def __init__(self, referenceVar):
        pass


class CircleAnim:
    def __init__(self, obj, circleAmount, radius, internalRadius, color, follow, *args):  # args = [minSpeed, maxSpeed, weight]
        self.point = obj
        self.sphereRad = radius
        self.circles = []
        self.rotations = []
        self.rotationSpeeds = []
        self.circleColor = color
        for c in range(circleAmount):
            self.circles.append(vizshape.addTorus(self.sphereRad, internalRadius))
            self.rotations.append([0, (180 / circleAmount) * c, 0])
            if args:
                self.rotationSpeeds.append([random.triangular(args[0], args[1], random.choice([-args[2], args[2]])), random.triangular(args[0], args[1], random.choice([-args[2], args[2]])), random.triangular(args[0], args[1], random.choice([-args[2], args[2]]))])  # make weighing random as well
            else:
                if (c % 2) == 0:
                    self.rotationSpeeds.append([1, 1, 1])
                else:
                    self.rotationSpeeds.append([-1, -1, -1])
            self.circles[c].setPosition(self.point.cords)
        self.follow = follow
        self.pause = False

    def draw(self, *speedScaler):
        for c in range(len(self.circles)):
            if self.follow:
                self.circles[c].setPosition(self.point.cords)
            if not self.pause:
                coefficient = 1
                if speedScaler:
                    coefficient = speedScaler[0]  # cache this value as it does not change throughout the loops below
                for axis in range(3):
                    self.rotations[c][axis] += animSpeed * 8 * self.rotationSpeeds[c][axis] * coefficient * 1440 / physicsTime
                self.circles[c].setEuler(self.rotations[c])
            self.circles[c].color(self.circleColor)

    def setScale(self, scale):
        for c in self.circles:
            c.setScale([scale, scale, scale])

    def setColor(self, color):
        for c in self.circles:
            c.color(color)

    def unDraw(self):
        for c in self.circles:
            c.remove()
