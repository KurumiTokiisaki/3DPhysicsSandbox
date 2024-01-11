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
        if self.tDim:
            loops = 8
            for c in range(loops):
                self.circle.append(vizshape.addTorus(cRad, 0.04))
                self.circle[c].setPosition(self.cords)
                self.cAngle.append([0, (180 / loops) * c, 0])
                self.cMultiplier.append(0)
                if (c % 2) == 0:
                    self.cMultiplier[c] = random.triangular(-1, 1, 1)  # weight more heavily to +1
                else:
                    self.cMultiplier[c] = random.triangular(-1, 1, -1)  # weight more heavily to -1
        else:
            self.circle.append(vizshape.addTorus(cRad, 0.04))
            self.cAngle.append([0, 90, 0])
            self.circle[0].setPosition(self.cords)
            self.circle[0].setEuler(self.cAngle[0])
        self.pRad = pointRadius
        self.pointer = vizshape.addSphere(self.pRad, slices=pointResolution)
        self.pCords = copy.deepcopy(cords)
        self.oldPCords = copy.deepcopy(self.pCords)
        for axis in range(len(referenceVar)):  # used to allow for inheritance in DialThreeD
            self.min.append(mini[axis])
            self.max.append(maxi[axis])
            self.range.append(maxi[axis] - mini[axis])
            if self.tDim:
                self.pCords[axis] += (self.var[axis] / self.range[axis]) * self.cRad * 2
        if not self.tDim:
            if self.xyz == 0:  # lying down
                self.axes = [0, 2]
            elif self.xyz == 1:  # upright (facing z)
                self.axes = [0, 1]
            else:  # upright (facing x)
                self.axes = [1, 2]
            self.pCords[self.axes[0]] += (self.var[self.axes[0]] / self.range[self.axes[0]]) * self.cRad * 2
            self.pCords[self.axes[1]] += (self.var[self.axes[1]] / self.range[self.axes[1]]) * self.cRad * 2
        self.pVelocity = [0, 0, 0]
        self.text = text
        self.textFront = viz.addText3D('', fontSize=0.15)
        self.collision = False
        self.dragging = False

    def drag(self, c, dragging):
        self.dragging = dragging
        if dragging:
            self.collision = detectCollision(c.radius, self.pRad, c.cords, self.pCords)
            if self.collision:
                if not self.tDim:
                    self.pCords[0] = copy.deepcopy(c.cords[0])
                    self.pCords[1] = copy.deepcopy(c.cords[1])
                else:
                    self.pCords = copy.deepcopy(c.cords)

    def interpolate(self):
        relDist = []
        ratio = []
        for dim in range(len(self.var)):
            if not self.tDim:
                relDist.append(self.pCords[self.axes[dim]] - (self.cords[self.axes[dim]] - self.cRad))
            else:
                relDist.append(self.pCords[dim] - (self.cords[dim] - self.cRad))
            ratio.append(relDist[dim] / (self.cRad * 2))
            self.var[dim] = self.min[dim] + (self.range[dim] * ratio[dim])

    def main(self):
        # self.circularMotion()  # MASSIVE work-in-progress
        self.boundDial()

        if not self.tDim:
            movingAngle = getAbsTwoDAngle([0, 0], [self.pVelocity[self.axes[0]], self.pVelocity[self.axes[1]]])
            self.oldPCords[self.axes[0]] += 1.25 * getSign(self.pVelocity[self.axes[0]]) * sin(movingAngle) / (calcRate ** 2)  # adds some drag on the dial
            self.oldPCords[self.axes[1]] += 1.25 * getSign(self.pVelocity[self.axes[1]]) * cos(movingAngle) / (calcRate ** 2)
        else:
            movingAngle = getAbsThreeDAngle([0, 0, 0], self.pVelocity, 'y')
            self.oldPCords[0] += 1.25 * getSign(self.pVelocity[0]) * cos(movingAngle[1]) * sin(movingAngle[0]) / (calcRate ** 2)  # adds some drag on the dial
            self.oldPCords[1] += 1.25 * getSign(self.pVelocity[1]) * sin(movingAngle[1]) / (calcRate ** 2)
            self.oldPCords[2] += 1.25 * getSign(self.pVelocity[2]) * cos(movingAngle[1]) * cos(movingAngle[0]) / (calcRate ** 2)

        for axis in range(len(self.var)):
            if (abs(self.pVelocity[axis]) < (10 ** -4)) and (not self.dragging):  # if there is to be frictional force on the slider's point and velocity is very small, make velocity 0 to prevent vibration
                self.oldPCords[axis] = copy.deepcopy(self.pCords[axis])

        # Verlet integration
        for axis in range(3):
            self.pVelocity[axis] = self.pCords[axis] - self.oldPCords[axis]
        self.oldPCords = copy.deepcopy(self.pCords)
        for axis in range(3):
            self.pCords[axis] += self.pVelocity[axis]

        self.interpolate()

        return self.var

    def circularMotion(self):
        resultAcc = (distance([0, 0, 0], self.pVelocity) ** 2) / self.cRad
        angle = getAbsTwoDAngle([self.cords[0], self.cords[1]], [self.pCords[0], self.pCords[1]])
        quartiles = [self.pCords[0] <= self.cords[0], self.pCords[1] <= self.cords[1]]
        acc = [resultAcc * sin(angle) * TFNum(quartiles[0]), resultAcc * cos(angle) * TFNum(quartiles[1])]
        self.oldPCords[0] -= acc[0]  # / calcRate ** 2
        self.oldPCords[1] -= acc[1]  # / calcRate ** 2

    # prevent "dialer" (point) from exiting the dial
    def boundDial(self):
        if distance(self.cords, self.pCords) > self.cRad:
            self.pCords = copy.deepcopy(self.oldPCords)

    def draw(self, camCords):
        self.pointer.setPosition(self.pCords)

        if not self.tDim:
            self.textFront.message(f'{self.text[0]}: {round(self.var[0], 4)}\n{self.text[1]}: {round(self.var[1], 4)}')
            self.textFront.setPosition(self.pCords[0] - 0.3, self.pCords[1] - 0.2, self.pCords[2] - 0.2)
        else:
            self.textFront.message(f'{self.text[0]}: {round(self.var[0], 4)}\n{self.text[1]}: {round(self.var[1], 4)}\n{self.text[2]}: {round(self.var[2], 4)}')
        angle, pos = camAnglePos(camCords, self.pCords, self.pRad ** (1 / 3))
        self.textFront.setEuler(angle)
        self.textFront.setPosition(pos)

        if self.tDim:
            for c in range(len(self.circle)):
                self.cAngle[c][0] += animSpeed * 8 * self.cMultiplier[c] * (distance([0, 0, 0], self.pVelocity) * physicsTime + 1)
                self.cAngle[c][1] += animSpeed * 8 * self.cMultiplier[c] * (distance([0, 0, 0], self.pVelocity) * physicsTime + 1)
                self.circle[c].setEuler(self.cAngle[c])

    def unDraw(self):
        self.pointer.remove()
        for c in range(len(self.circle)):
            self.circle[c].remove()
        self.textFront.remove()
