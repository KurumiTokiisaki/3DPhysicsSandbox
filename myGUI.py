import copy
import math
import viz
import vizshape
from config import *
from globalFunctions import *


class Slider:
    def __init__(self, xyz, referenceVar, cords, length, pointRadius, maxi, mini, text):
        self.xyz = xyz
        self.initVar = referenceVar
        self.var = referenceVar
        self.cords = cords
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
        self.textFront = viz.addText3D(f'{round(self.var, 4)}')
        self.textBack = viz.addText3D(f'{round(self.var, 4)}')  # reverse setEuler for this
        self.textFront.fontSize(0.1)
        self.textBack.fontSize(0.1)
        self.textOffset = 0.2
        self.collision = False
        self.dragging = False
        self.text = viz.addText3D(f'{text}', fontSize=0.2)
        self.textPos = [0, 0, 0]

        if xyz == 0:
            self.textPos = [self.cords[0] - (len(text) / 20), self.cords[1] + 0.3, self.cords[2]]
            self.sliders[0].setEuler(90, 90, 0)
            self.textFront.setEuler(180, 0, 0)
        elif xyz == 1:
            self.textPos = [self.cords[0] - (len(text) / 20), self.cords[1] + (self.length / 2) + 0.3, self.cords[2]]
            self.sliders[1].setEuler(90, 90, 0)
            self.sliders[2].setEuler(90, 90, 0)
            self.textFront.setEuler(180, 0, 0)
        elif xyz == 2:
            self.textPos = [self.cords[0], self.cords[1] + 0.3, self.cords[2] + (len(text) / 20)]
            self.text.setEuler(90, 0, 0)
            self.sliders[0].setEuler(0, 90, 0)
            self.textFront.setEuler(-90, 0, 0)
            self.textBack.setEuler(90, 0, 0)
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

        self.oldPCords[self.xyz] += 1.5 * getSign(self.pVelocity[self.xyz]) / (calcRate ** 2)  # some drag on the slider

        if (abs(self.pVelocity[self.xyz]) < (10 ** -4)) and (not self.collision or not self.dragging):
            self.oldPCords[self.xyz] = copy.deepcopy(self.pCords[self.xyz])  # frictional force on the slider's point

        # Verlet integration
        self.pVelocity[self.xyz] = self.pCords[self.xyz] - self.oldPCords[self.xyz]
        self.oldPCords = copy.deepcopy(self.pCords)
        self.pCords[self.xyz] += self.pVelocity[self.xyz]

        self.interpolate()
        return self.var

    def draw(self, cam):
        self.pointer.setPosition(self.pCords)
        setPos = [copy.deepcopy(self.pCords), copy.deepcopy(self.pCords)]
        if (self.xyz == 0) or (self.xyz == 1):
            radMod = 2
            offsetMod = 0
        else:
            radMod = 0
            offsetMod = 2
        setPos[0][radMod] += self.pRad
        setPos[1][radMod] -= self.pRad
        if (self.xyz == 0) or (self.xyz == 1):
            setPos[0][offsetMod] += self.textOffset
            setPos[1][offsetMod] -= self.textOffset
        else:
            setPos[0][offsetMod] -= self.textOffset
            setPos[1][offsetMod] += self.textOffset
        self.textFront.setPosition(setPos[0])
        self.textBack.setPosition(setPos[1])
        self.textFront.message(f'{round(self.var, 4)}')
        self.textBack.message(f'{round(self.var, 4)}')

    def unDraw(self):
        self.pointer.remove()
        for s in range(len(self.sliders)):
            self.sliders[s].remove()
        self.textFront.remove()
        self.textBack.remove()
        self.text.remove()
