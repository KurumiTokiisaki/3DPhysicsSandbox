import copy
import math
import random

import viz
import vizshape
from globalFunctions import *

controllerCount = 1
if mode == 'vr':
    controllerCount = 2

jetBrainsFontSize = 1.69  # font size of 1.69 equates to 1 unit of distance per character in Vizard


# mode = 'vr'  # uncomment for testing VR settings on keyboard/mouse


class Slider:
    def __init__(self, xyz, referenceVar, globalDefaultVar, cords, length, pointRadius, maxi, mini, text, lController, rController):
        self.type = 'slider'
        self.drawn = True
        self.xyz = xyz
        self.var = float(referenceVar)
        self.origVar = copy.deepcopy(float(referenceVar))
        self.globalOrigVar = float(globalDefaultVar)
        self.cords = copy.deepcopy(cords)
        self.length = length
        self.limits = [self.cords[self.xyz] - (self.length / 2), cords[self.xyz] + (self.length / 2)]  # x/y/z (depending on the value of self.xyz) cords of both ends of the slider
        self.pRad = pointRadius
        self.max = maxi  # maximum variable value
        self.min = mini  # minimum variable value
        self.range = maxi - mini
        self.pointer = vizshape.addSphere(pointRadius, slices=pointResolution)
        self.sliders = [vizshape.addCylinder(length, 0.05), vizshape.addCylinder(pointRadius * 2, 0.02), vizshape.addCylinder(pointRadius * 2, 0.02)]
        self.pCords = copy.deepcopy(self.cords)
        self.oldPCords = copy.deepcopy(self.pCords)
        self.pVelocity = [0, 0, 0]
        self.textFront = viz.addText3D('', fontSize=0.1)
        self.textOffset = 0.1
        self.collision = False
        self.dragging = False
        self.text = viz.addText3D(f'{text}', fontSize=0.2)
        self.textPos = [0, 0, 0]
        self.closeButton = XSymbol(0.5, self.cords)
        if self.xyz == 0:
            self.closeButton.cords = [self.limits[1] + 0.2, self.cords[1] + 0.5, self.cords[2]]
        elif self.xyz == 1:
            self.closeButton.cords = [self.cords[0] + 0.5, self.limits[1] + 0.2, self.cords[2]]
        elif self.xyz == 2:
            self.closeButton.cords = [self.cords[0], self.cords[1] + 0.5, self.limits[1] + 0.2]
        for s in self.closeButton.X:
            if (self.xyz == 0) or (self.xyz == 1):
                s.setEuler(s.getEuler()[0] + 90, s.getEuler()[1], s.getEuler()[2])
            s.setPosition(self.closeButton.cords)

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
        self.resetVar()
        self.cObj = [lController[0], rController[0]]  # controller objects
        self.cDat = [lController[1], rController[1]]  # controller point data
        self.timePressed = [0, 0]
        self.resetHeld = [0, 0]

    def resetVar(self, *args):  # reset the value of the reference variable to its initial value from when this class was initialized
        if args:
            self.pCords[self.xyz] = self.limits[0] + ((self.globalOrigVar + abs(self.min) * -getSign(self.min)) / self.range) * self.length
        else:
            self.pCords[self.xyz] = self.limits[0] + ((self.origVar + abs(self.min) * -getSign(self.min)) / self.range) * self.length
        self.oldPCords = copy.deepcopy(self.pCords)

    def setVar(self, var):  # set the reference variable to a specific value
        var = float(var)
        if (not self.dragging) or (not self.collision):
            self.pCords[self.xyz] = self.limits[0] + ((var + abs(self.min) * -getSign(self.min)) / self.range) * self.length

    def interpolate(self):
        relDist = self.pCords[self.xyz] - self.limits[0]
        ratio = relDist / self.length
        self.var = self.min + (self.range * ratio)

    def drag(self, cIdx, dragging):
        self.dragging = dragging
        if dragging:
            self.collision = detectCollision(self.cDat[cIdx].radius, self.pRad, self.cDat[cIdx].cords, self.pCords)
            if self.collision:
                self.pCords[self.xyz] = copy.deepcopy(self.cDat[cIdx].cords[self.xyz])

    def main(self):
        for c in range(controllerCount):
            if self.timePressed[c] <= 0.25:
                self.timePressed[c] += 1 / calcRate
            if buttonPressed('reset', self.cObj[c], c):
                if not self.resetHeld[c]:
                    self.resetHeld[c] = True
                    if self.timePressed[c] > 0.25:
                        self.resetVar()
                    else:
                        self.resetVar('hard')
                    self.timePressed[c] = 0
            else:
                self.resetHeld[c] = False
            if buttonPressed('select', self.cObj[c], c) and detectCollision(self.cDat[c].radius, self.closeButton.radius, self.cDat[c].cords, self.closeButton.cords):
                self.unDraw()
                self.drawn = False

        if self.pCords[self.xyz] < self.limits[0]:
            self.pCords[self.xyz] = copy.deepcopy(self.limits[0])
            self.oldPCords[self.xyz] = copy.deepcopy(self.pCords[self.xyz])
        elif self.pCords[self.xyz] > self.limits[1]:
            self.pCords[self.xyz] = copy.deepcopy(self.limits[1])
            self.oldPCords[self.xyz] = copy.deepcopy(self.pCords[self.xyz])

        self.oldPCords[self.xyz] += 0.015 * getSign(self.pVelocity[self.xyz]) / calcRate  # adds some drag on the slider

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
        angle, pos = camAnglePos(camCords, self.pCords, self.pRad)
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
        self.closeButton.unDraw()


class Point:
    def __init__(self, rad, show):
        self.cords = [0, 0, 0]
        self.oldCords = [0, 0, 0]
        self.velocity = [0, 0, 0]
        self.radius = rad
        self.show = show
        if self.show:  # can be false for use in buttons
            self.point = vizshape.addSphere(self.radius, slices=pointResolution)


class XSymbol:
    def __init__(self, size, cords):
        self.radius = size / 2
        self.cBox = Point(self.radius, False)  # True for testing
        # self.cBox.point.setPosition(cords)  # uncomment for testing
        self.cords = cords
        self.X = [vizshape.addCylinder(size / math.sqrt(2), 0.03), vizshape.addCylinder(size / math.sqrt(2), 0.03)]
        self.X[0].setEuler(0, 45, 0)
        self.X[1].setEuler(0, 135, 0)
        for c in range(len(self.X)):
            self.X[c].setPosition(self.cords)

    def setAngle(self, angle):
        self.X[0].setEuler(angle[0] + 90, angle[1] + 45, angle[2])
        self.X[1].setEuler(angle[0] + 90, angle[1] + 135, angle[2])

    def setPos(self, pos, *unDraw):
        self.cords = copy.deepcopy(pos)
        if unDraw:
            self.unDraw()
        else:
            for c in range(len(self.X)):
                self.X[c].setPosition(pos)

    def unDraw(self):
        self.X[0].remove()
        self.X[1].remove()
        if self.cBox.show:
            self.cBox.point.remove()


class Dial:
    def __init__(self, xyz, referenceVar, globalDefaultVar, cords, cRad, pointRadius, maxi, mini, text, lController, rController, *varOffset):
        self.type = 'dial'
        self.drawn = True
        self.xyz = xyz
        self.var = []
        self.globalOrigVar = []
        self.cRad = cRad
        self.cords = copy.deepcopy(cords)
        self.min = []
        self.max = []
        self.range = []
        self.circle = []
        self.cAngle = []
        self.cMultiplier = []
        self.tDim = True if len(mini) == 3 else False
        if not self.tDim:
            if self.xyz == 1:
                self.cAngle.append([0, 90, 0])
            elif self.xyz == 2:
                self.cAngle.append([90, 90, 0])
            else:
                self.cAngle.append([0, 0, 0])
            self.circle.append(vizshape.addTorus(cRad, 0.04))
            self.circle[0].setPosition(self.cords)
            self.circle[0].setEuler(self.cAngle[0])
        self.p = Point(pointRadius, True)
        self.p.cords = copy.deepcopy(cords)
        self.p.oldCords = copy.deepcopy(self.p.cords)
        if varOffset:
            self.varOffset = varOffset
        else:
            self.varOffset = [0, 0, 0]
        for axis in range(len(mini)):
            self.min.append(-(abs(mini[axis]) + abs(maxi[axis])) / 2)
            self.max.append((abs(mini[axis]) + abs(maxi[axis])) / 2)
            # self.varOffset.append((maxi[axis] + mini[axis]) / 2)
            self.range.append(maxi[axis] - mini[axis])
        for v in range(len(referenceVar)):
            self.var.append(float(referenceVar[v]))
        self.origVar = copy.deepcopy(self.var)
        for v in range(len(globalDefaultVar)):
            self.globalOrigVar.append(float(globalDefaultVar[v]))
        if not self.tDim:
            if self.xyz == 0:  # lying down
                self.axes = [0, 2]  # XZ
            elif self.xyz == 1:  # upright (facing z)
                self.axes = [0, 1]  # XY
            else:  # upright (facing x)
                self.axes = [1, 2]  # YZ
        else:
            self.axes = [0, 1, 2]
        self.text = text
        self.textFront = viz.addText3D('', fontSize=0.15)
        self.collision = False
        self.dragging = False
        self.anim = None
        if self.tDim:
            self.anim = CircleAnim(self.p, round(self.cRad) + 2, self.cRad, 0.04, [1, 0, 1], False, -3, 3, 5)
        self.resetVar()
        self.closeButton = XSymbol(0.5, [self.cords[0], self.cords[1] + self.cRad + 0.5, self.cords[2]])
        if not self.tDim:
            self.closeButton.setAngle(self.cAngle[0])
            if self.xyz == 0:
                self.closeButton.setPos([self.cords[0] + self.cRad + 0.5, self.cords[1], self.cords[2]])
                self.closeButton.setAngle((0, 0, 0))
        self.cObj = [lController[0], rController[0]]
        self.cDat = [lController[1], rController[1]]
        self.timePressed = [0, 0]
        self.resetHeld = [False, False]

    def resetVar(self, *args):
        if args:
            if self.tDim:
                for axis in range(3):
                    self.p.cords[axis] = self.cords[axis] + (self.globalOrigVar[axis] / self.range[axis]) * self.cRad * 2
            else:
                self.p.cords[self.axes[0]] = self.cords[self.axes[0]] + (self.globalOrigVar[self.axes[0]] / self.range[0]) * self.cRad * 2
                self.p.cords[self.axes[1]] = self.cords[self.axes[1]] + (self.globalOrigVar[self.axes[1]] / self.range[1]) * self.cRad * 2
        else:
            if self.tDim:
                for axis in range(3):
                    self.p.cords[axis] = self.cords[axis] + (self.origVar[axis] / self.range[axis]) * self.cRad * 2
            else:
                self.p.cords[self.axes[0]] = self.cords[self.axes[0]] + (self.origVar[self.axes[0]] / self.range[0]) * self.cRad * 2
                self.p.cords[self.axes[1]] = self.cords[self.axes[1]] + (self.origVar[self.axes[1]] / self.range[1]) * self.cRad * 2
        self.p.oldCords = copy.deepcopy(self.p.cords)

    def setVar(self, var):
        for v in range(len(var)):
            var[v] = float(var[v])
        for c in range(controllerCount):
            if (not self.dragging) or (not self.collision):
                if self.tDim:
                    for axis in range(3):
                        self.p.cords[axis] = self.cords[axis] + (var[axis] / self.range[axis]) * self.cRad * 2
                else:
                    self.p.cords[self.axes[0]] = self.cords[self.axes[0]] + (var[self.axes[0]] / self.range[0]) * self.cRad * 2
                    self.p.cords[self.axes[1]] = self.cords[self.axes[1]] + (var[self.axes[1]] / self.range[1]) * self.cRad * 2

    def drag(self, cIdx, dragging):
        self.dragging = dragging
        if dragging:
            self.collision = detectCollision(self.cDat[cIdx].radius, self.p.radius, self.cDat[cIdx].cords, self.p.cords)
            if self.collision:
                if not self.tDim:
                    self.p.cords[self.axes[0]] = copy.deepcopy(self.cDat[cIdx].cords[self.axes[0]])
                    self.p.cords[self.axes[1]] = copy.deepcopy(self.cDat[cIdx].cords[self.axes[1]])
                else:
                    self.p.cords = copy.deepcopy(self.cDat[cIdx].cords)

    def interpolate(self):
        relDist = []
        ratio = []
        # cords = [0, 0, 0]
        for dim in range(len(self.min)):
            # cords[self.axes[dim]] = self.cords[self.axes[dim]] - (self.max[dim] + self.min[dim]) / 2
            relDist.append(self.p.cords[self.axes[dim]] - self.cords[self.axes[dim]] + self.cRad)
            ratio.append(relDist[dim] / (self.cRad * 2))
            self.var[self.axes[dim]] = self.min[dim] + (self.range[dim] * ratio[dim])

    def main(self):
        for c in range(controllerCount):
            if self.timePressed[c] <= 0.25:
                self.timePressed[c] += 1 / calcRate
            if buttonPressed('reset', self.cObj[c], c):
                if not self.resetHeld[c]:
                    self.resetHeld[c] = True
                    if self.timePressed[c] > 0.25:
                        self.resetVar()
                    else:
                        self.resetVar('hard')
                    self.timePressed[c] = 0
            else:
                self.resetHeld[c] = False
            if buttonPressed('select', self.cObj[c], c) and detectCollision(self.cDat[c].radius, self.closeButton.radius, self.cDat[c].cords, self.closeButton.cords):
                self.unDraw()
                self.drawn = False

        # self.circularMotion()  # MASSIVE WIP
        self.boundDial()

        if not self.tDim:
            movingAngle = getAbsTwoDAngle([0, 0], [self.p.velocity[self.axes[0]], self.p.velocity[self.axes[1]]])
            self.p.oldCords[self.axes[0]] += 0.015 * getSign(self.p.velocity[self.axes[0]]) * sin(movingAngle) / calcRate  # adds some drag on the dial
            self.p.oldCords[self.axes[1]] += 0.015 * getSign(self.p.velocity[self.axes[1]]) * cos(movingAngle) / calcRate
        else:
            movingAngle = getAbsThreeDAngle([0, 0, 0], self.p.velocity, 'y')
            self.p.oldCords[0] += 0.015 * getSign(self.p.velocity[0]) * cos(movingAngle[1]) * sin(movingAngle[0]) / calcRate  # adds some drag on the dial
            self.p.oldCords[1] += 0.015 * getSign(self.p.velocity[1]) * sin(movingAngle[1]) / calcRate
            self.p.oldCords[2] += 0.015 * getSign(self.p.velocity[2]) * cos(movingAngle[1]) * cos(movingAngle[0]) / calcRate

        for axis in range(len(self.var)):
            for c in range(controllerCount):
                if (abs(self.p.velocity[axis]) < (10 ** -4)) and (not self.dragging or not self.collision):  # if there is to be frictional force on the slider's point and velocity is very small, make velocity 0 to prevent vibration
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
            self.textFront.message(f'{self.text[0]}: {round(self.var[self.axes[0]] + self.varOffset[self.axes[0]], 4)}\n{self.text[1]}: {round(self.var[self.axes[1]] + self.varOffset[self.axes[1]], 4)}')
            self.textFront.setPosition(self.p.cords[0] - 0.3, self.p.cords[1] - 0.2, self.p.cords[2] - 0.2)
        else:
            self.textFront.message(f'{self.text[0]}: {round(self.var[0] + self.varOffset[0], 4)}\n{self.text[1]}: {round(self.var[1] + self.varOffset[1], 4)}\n{self.text[2]}: {round(self.var[2] + self.varOffset[2], 4)}')
        angle, pos = camAnglePos(camCords, self.p.cords, self.p.radius ** (1 / 3))
        self.textFront.setEuler(angle)
        self.textFront.setPosition(pos)

        if self.tDim:
            self.anim.draw(distance([0, 0, 0], self.p.velocity) * 0.2 + 1)

    def unDraw(self):
        self.p.point.remove()
        if self.anim is not None:
            self.anim.unDraw()
        else:
            self.circle[0].remove()
        self.textFront.remove()
        self.closeButton.unDraw()


class Manual:
    def __init__(self, xyz, referenceVar, globalDefaultVar, cords, text, lController, rController, *follow):
        self.xyz = xyz
        if follow and (mode == 'vr'):
            self.follow = False
            self.fontSize = 0.3
        else:
            self.follow = True
            self.fontSize = 0.1
        self.cObj = [lController[0], rController[0]]
        self.cDat = [lController[1], rController[1]]
        self.drawn = True
        self.var = float(referenceVar)
        self.origVar = copy.deepcopy(float(referenceVar))
        self.globalOrigVar = float(globalDefaultVar)
        self.text = text
        self.cords = copy.deepcopy(cords)
        self.textVar = viz.addText3D('', fontSize=self.fontSize)
        self.boxes = []
        self.boxPos = []
        self.collP = []
        self.keypadTexts = []
        if mode == 'vr':
            # add & display variable information
            self.textVarPos = [self.cords[0] + 1, self.cords[1] + 2, self.cords[2]]

            # add & display the '0' number key
            self.boxes.append(vizshape.addBox())
            self.boxPos.append([self.cords[0] + 1, self.cords[1] - 3, self.cords[2]])
            self.keypadTexts.append(viz.addText3D('0', fontSize=0.2))

            # add & display the number keys
            for y in range(3):
                for x in range(3):
                    self.boxes.append(vizshape.addBox())
                    self.boxPos.append([self.cords[0] + x, self.cords[1] - y, self.cords[2]])
                    self.keypadTexts.append(viz.addText3D(f'{(y * 3) + (x + 1)}', fontSize=0.2))

            # add & display the forward/back keys
            for b in range(2):
                self.boxes.append(vizshape.addBox())
                self.boxPos.append([self.cords[0] + (b * 2), self.cords[1] + 1, self.cords[2]])
                if b == 0:
                    self.keypadTexts.append(viz.addText3D('<-', fontSize=0.2))
                elif b == 1:
                    self.keypadTexts.append(viz.addText3D('->', fontSize=0.2))

            # add & display the delete key
            self.boxes.append(vizshape.addBox())
            self.boxPos.append([self.cords[0] + 2, self.cords[1] - 3, self.cords[2]])
            self.keypadTexts.append(viz.addText3D('DEL', fontSize=0.2))

            # add & display the negative key
            self.boxes.append(vizshape.addBox())
            self.boxPos.append([self.cords[0], self.cords[1] - 3, self.cords[2]])
            self.keypadTexts.append(viz.addText3D('-', fontSize=0.2))

            # add & display the reset key
            self.boxes.append(vizshape.addBox())
            self.boxPos.append([self.cords[0], self.cords[1] - 4, self.cords[2]])
            self.keypadTexts.append(viz.addText3D('Reset', fontSize=0.2))

            # add and display the hard reset key
            self.boxes.append(vizshape.addBox())
            self.boxPos.append([self.cords[0] + 2, self.cords[1] - 4, self.cords[2]])
            self.keypadTexts.append(viz.addText3D('Hard\nReset', fontSize=0.2))

            for b in range(len(self.boxes)):
                self.boxes[b].alpha(0.3)
                self.boxes[b].setPosition(self.boxPos[b])
                self.keypadTexts[b].setPosition(self.boxPos[b])
                self.collP.append(Point(0.5 - self.cDat[1].radius, False))
                self.collP[b].cords = self.boxPos[b]

            self.closeButton = XSymbol(0.5, [self.textVarPos[0], self.textVarPos[1] - 1, self.textVarPos[2]])
        else:
            self.textVarPos = self.cords
        self.indicator = viz.addText3D('', fontSize=self.fontSize)
        self.spacing = '|'
        self.spaces = 0
        self.indicator.setPosition(self.textVarPos[0], self.textVarPos[1] - self.fontSize, self.textVarPos[2])  # offset the indicator to be on the same line as self.var
        self.keys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', viz.KEY_BACKSPACE, '-', viz.KEY_RETURN, viz.KEY_RIGHT, viz.KEY_LEFT]
        self.keyHeld = []
        self.textVar.setPosition(self.textVarPos)
        for k in range(len(self.keys)):
            self.keyHeld.append(False)
        self.timePressed = [0, 0]
        self.offset = [0, 0]
        self.decIdx = 0
        self.resetHeld = [False, False]
        self.selecting = [False, False]
        self.sHeld = [True, True]
        self.collision = [False, False]
        self.selectionIdx = [None, None]
        self.selections = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 'left', 'right', 'delete', '-', 'reset', 'hardReset']
        self.activePoint = None

    def addToVar(self, number):
        self.var = str(self.var)
        tempStr = ''
        for c in range(len(self.var) + 1):
            if c == (self.spaces + self.offset[1]):
                tempStr = f'{tempStr}{number}'
            if c < len(self.var):
                tempStr = f'{tempStr}{self.var[c]}'
        self.var = float(tempStr)
        self.spaces += 1

    def removeFromVar(self):
        self.var = str(self.var)
        tempStr = ''
        if (self.var[self.spaces - 1] != '.') and (self.var[self.spaces - 1] != '-'):
            for c in range(len(self.var)):
                if c != (self.spaces - 1):
                    tempStr = f'{tempStr}{self.var[c]}'
        else:
            tempStr = self.var
        if len(self.spacing) > 1:
            self.spaces -= 1
        self.var = float(tempStr)

    def main(self):
        if mode == 'vr':
            for c in range(controllerCount):
                if self.selecting[c]:
                    if detectCollision(self.cDat[c].radius, self.closeButton.radius, self.cDat[c].cords, self.closeButton.cords):
                        self.unDraw()
                        self.drawn = False
        else:
            if self.selecting[0]:
                if not self.sHeld[0]:
                    self.sHeld[0] = True
                    if detectCollision(self.cDat[0].radius, 0.2, self.cDat[0].cords, self.cords):
                        if self.activePoint is None:
                            self.activePoint = vizshape.addSphere(0.1)
                            self.activePoint.setPosition(self.cords[0], self.cords[1] + 0.2, self.cords[2])
                            self.activePoint.color([1, 0.1, 0.1])
                        else:
                            self.activePoint.remove()
                            self.activePoint = None
            else:
                self.sHeld[0] = False

        for c in range(controllerCount):
            if self.timePressed[c] <= 0.25:
                self.timePressed[c] += 1 / calcRate
            if buttonPressed('reset', self.cObj[c], c):
                if not self.resetHeld[c]:
                    self.resetHeld[c] = True
                    if self.timePressed[c] > 0.25:
                        self.resetVar()
                    else:
                        self.resetVar('hard')
                    self.timePressed[c] = 0
            else:
                self.resetHeld[c] = False

        if mode == 'vr':
            for c in range(controllerCount):
                if self.selectionIdx[c] is not None:
                    selection = self.selections[self.selectionIdx[c]]
                    if selection == 'right':
                        self.spaces += 1
                    elif selection == 'left':
                        if self.spaces > 1:
                            self.spaces -= 1
                    elif selection == 'delete':
                        self.removeFromVar()
                    elif selection == '-':
                        self.var = -self.var
                    elif selection == 'reset':
                        self.resetVar()
                    elif selection == 'hardReset':
                        self.resetVar('hard')
                    else:
                        self.addToVar(selection)
        elif mode == 'k':
            if self.activePoint is not None:
                for k in range(len(self.keys)):
                    if not viz.key.isDown(self.keys[k]):
                        self.keyHeld[k] = False
                if viz.key.anyDown(self.keys):
                    for n in range(10):
                        if viz.key.isDown(f'{n}'):
                            if not self.keyHeld[n]:
                                self.keyHeld[n] = True
                                self.addToVar(n)
                                break
                    if viz.key.isDown(self.keys[10]):
                        if not self.keyHeld[10]:
                            self.keyHeld[10] = True
                            self.removeFromVar()

                    if viz.key.isDown(self.keys[11]):
                        if not self.keyHeld[11]:
                            self.keyHeld[11] = True
                            self.var = -self.var

                    if viz.key.isDown(self.keys[12]):
                        self.drawn = False
                    if viz.key.isDown(self.keys[13]):
                        if not self.keyHeld[13]:
                            self.keyHeld[13] = True
                            self.spaces += 1
                    if viz.key.isDown(self.keys[14]):
                        if not self.keyHeld[14]:
                            self.keyHeld[14] = True
                            if self.spaces > 1:
                                self.spaces -= 1

        for c in range(len(str(self.var))):
            if str(self.var)[c] == '.':
                self.decIdx = c
        if self.spaces >= self.decIdx:
            self.offset[0] = -1
        else:
            self.offset[0] = 0
        if str(self.var)[0] == '-':
            self.offset[1] = 1
        else:
            self.offset[1] = 0

        tempStr = ''
        for s in range(self.spaces * 2 + self.offset[0] + self.offset[1]):  # multiply by 2 since 2 spaces = 1 character
            tempStr = f' {tempStr}'
        tempStr = f'{tempStr}|'
        self.spacing = tempStr

        if not self.drawn:
            self.unDraw()

        return self.var

    def drag(self, cIdx, selecting):
        self.selecting[cIdx] = selecting
        if mode == 'vr':
            if self.selecting[cIdx]:
                if not self.sHeld[cIdx]:
                    self.sHeld[cIdx] = True
                    for p in range(len(self.collP)):
                        self.collision[cIdx] = detectCollision(self.cDat[cIdx].radius, self.collP[p].radius, self.cDat[cIdx].cords, self.collP[p].cords)
                        if self.collision[cIdx]:
                            self.selectionIdx[cIdx] = p
                else:
                    self.selectionIdx[cIdx] = None
            else:
                self.sHeld[cIdx] = False

    def draw(self, camCords):
        self.textVar.message(f'{self.text}\n{self.var}')
        self.indicator.message(f'{self.spacing}')
        if mode == 'vr':
            if self.follow:
                self.textVarPos = [camCords[0], camCords[1], camCords[2] + 1]
                self.textVar.setPosition(self.textVarPos)
                self.indicator.setPosition(self.textVarPos[0], self.textVarPos[1] - 0.1, self.textVarPos[2])
            angle, pos = camAnglePos(camCords, self.closeButton.cords, 0)
            self.closeButton.setAngle(angle)
        else:
            angle, pos = camAnglePos(camCords, self.textVarPos, 0)
            self.textVar.setEuler(angle)
            self.indicator.setEuler(angle)  # fix this later
        for b in range(len(self.boxPos)):
            angle, pos = camAnglePos(camCords, self.boxPos[b], 0)
            self.keypadTexts[b].setEuler(angle)

    def setVar(self, var):
        var = float(var)
        self.var = var

    def resetVar(self, *args):
        if args:
            self.var = self.globalOrigVar
        else:
            self.var = self.origVar

    def unDraw(self):
        if mode == 'vr':
            self.closeButton.unDraw()
        self.indicator.remove()
        self.textVar.remove()
        for t in self.keypadTexts:
            t.remove()
        for b in self.boxes:
            b.remove()
        if self.activePoint is not None:
            self.activePoint.remove()


class CircleAnim:
    def __init__(self, obj, circleAmount, radius, internalRadius, color, follow, *args):  # args = [fixedSpeed] OR [minSpeed, maxSpeed, probabilityWeighting]
        self.point = obj
        self.sphereRad = radius
        self.circles = []
        self.rotations = []
        self.rotationSpeeds = []
        self.circleColor = color
        self.origColor = color
        for c in range(circleAmount):
            self.circles.append(vizshape.addTorus(self.sphereRad, internalRadius))
            self.rotations.append([0, (180 / circleAmount) * c, 0])
            if len(args) == 3:
                self.rotationSpeeds.append([random.triangular(args[0], args[1], random.choice([-args[2], args[2]])), random.triangular(args[0], args[1], random.choice([-args[2], args[2]])), random.triangular(args[0], args[1], random.choice([-args[2], args[2]]))])  # make weighing random as well
            elif len(args) == 1:
                if (c % 2) == 0:
                    self.rotationSpeeds.append([args[0], args[0], args[0]])
                else:
                    self.rotationSpeeds.append([-args[0], -args[0], -args[0]])
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
                    self.rotations[c][axis] += animSpeed * self.rotationSpeeds[c][axis] * coefficient * 500 / renderRate
                self.circles[c].setEuler(self.rotations[c])
            self.circles[c].color(self.circleColor)

    def setScale(self, scale):
        for c in self.circles:
            c.setScale([scale, scale, scale])

    def setColor(self, color):
        self.circleColor = color

    def resetColor(self):
        self.circleColor = copy.deepcopy(self.origColor)

    def resetScale(self):
        for c in self.circles:
            c.setScale([1, 1, 1])

    def unDraw(self):
        for c in self.circles:
            c.remove()


class GUISelector:
    def __init__(self, varDict, cords, lController, rController, *pIdx):
        self.cIdx = int
        if pIdx:
            self.pIdx = pIdx
        else:
            self.pIdx = 0
        self.cords = [cords[0] - (len(varDict) - 1) / 2, cords[1], cords[2]]
        self.drawn = True
        self.cObj = [lController[0], rController[0]]
        self.cDat = [lController[1], rController[1]]
        self.selecting = [False, False]
        self.sHeld = [False, False]
        self.collision = [False, False]
        self.var = None
        self.GUI = []
        self.stage = 'varSelection'

        self.GUIs = copy.deepcopy(varDict)
        for g in self.GUIs:
            self.GUIs[g] = None

        self.boxes = []
        self.collP = []
        self.text = []
        self.textObj = []
        self.drawSelection()

    def drawSelection(self):
        for g in self.GUIs:
            self.text.append(g)
            self.textObj.append(viz.addText3D(g, fontSize=0.1))
        for b in range(len(self.GUIs)):
            self.boxes.append(vizshape.addBox([0.9, 0.9, 0.9]))
            self.boxes[b].alpha(0.3)
            self.collP.append(Point(0.5 - self.cDat[1].radius, False))  # True for testing only
            self.collP[b].cords = [self.cords[0] + b, self.cords[1], self.cords[2]]
            # self.collP[b].point.setPosition(self.collP[b].cords)  # line here for testing only
            self.boxes[b].setPosition(self.collP[b].cords)
            self.textObj[b].setPosition([self.collP[b].cords[0] - len(self.text[b]) / 35, self.collP[b].cords[1], self.collP[b].cords[2]])

    def drag(self, cIdx, selecting):
        self.selecting[cIdx] = selecting
        if selecting:
            self.cIdx = cIdx
            for p in range(len(self.collP)):
                self.collision[cIdx] = detectCollision(self.cDat[cIdx].radius, self.collP[p].radius, self.cDat[cIdx].cords, self.collP[p].cords)
                if self.collision[cIdx] and (not self.sHeld[cIdx]):
                    self.sHeld[cIdx] = True
                    if self.stage == 'varSelection':
                        self.var = list(self.GUIs.keys())[p]
                        self.unDraw()
                        if self.var == 'Tutorials':
                            self.selectGUI(tutorialNames)
                        elif self.var == 'Save & Exit':
                            self.stage = 'complete'
                        elif self.var == 'cloths':
                            self.selectGUI(clothNames)
                        elif self.var == 'gField':
                            self.selectGUI(GUItypes)
                        elif self.var == 'Size':
                            self.selectGUI(GUItypesVector)
                        elif self.var == 'Solid/\nLiquid':
                            self.selectGUI(collisionRectTypes)
                        else:
                            self.selectGUI(GUItypesScalar)
                    elif self.stage == 'GUISelection':
                        if (self.var != 'Size') and (self.var != 'Solid/\nLiquid') and (type(globalVars[self.var]) is not list) and (list(self.GUIs.keys())[p] == 'Manual'):
                            self.GUI.append(list(self.GUIs.keys())[p])
                            self.GUI.append('def')
                            self.stage = 'complete'
                            break
                        else:
                            self.GUI.append(list(self.GUIs.keys())[p])
                            self.unDraw()
                            self.selectGUI(self.GUIs[list(self.GUIs.keys())[p]])
                    break
        else:
            self.sHeld[cIdx] = False

    def selectGUI(self, dictionary):
        if dictionary is not None:
            self.GUIs = copy.deepcopy(dictionary)
            self.drawSelection()
            self.stage = 'GUISelection'
        else:
            self.stage = 'complete'

    def main(self):
        if self.stage == 'complete':
            self.drawn = False
        if not self.drawn:
            self.unDraw()
            return self.var, self.GUI, self.cIdx, self.pIdx

    def draw(self, camCords):
        for t in range(len(self.textObj)):
            angle, pos = camAnglePos(camCords, self.collP[t].cords, 0.1)
            self.textObj[t].setEuler(angle)
            self.textObj[t].setPosition(pos)

    def unDraw(self):
        for b in self.boxes:
            b.remove()
        for t in self.textObj:
            t.remove()
        for p in self.collP:
            if p.show:
                p.point.remove()
        self.boxes = []
        self.text = []
        self.textObj = []
        self.collP = []


class Tutorial:
    def __init__(self, cords, sizeXZ, text, boldTextList, textSize, lController, rController):
        offset = 0.15
        self.drawn = True
        self.cords = copy.deepcopy(cords)
        self.text = copy.deepcopy(text)
        maxLen = math.floor((sizeXZ[0] - offset * 2) * jetBrainsFontSize / textSize)
        textList = []
        for t in range(len(self.text)):
            self.text[t] = self.text[t].split()
            textList.append(['\n'])
            for w in range(len(self.text[t])):
                if self.text[t][w].find('###') != -1:  # allows text following '###'s to be replaced with its respective control
                    for _ in range(3):
                        self.text[t][w] = removeFromStr(self.text[t][w], 0)
                    self.text[t][w] = controlsMap[self.text[t][w]]
                if (len(textList[-1][-1]) + len(self.text[t][w])) > maxLen:
                    textList[-1].append('\n')
                if textList[-1][-1] != '\n':
                    textList[-1][-1] = f'{textList[-1][-1]} {self.text[t][w]}'
                else:
                    textList[-1][-1] = f'{textList[-1][-1]}{self.text[t][w]}'  # no spaces on new lines!
        self.text = []
        for t in range(len(textList)):
            self.text.append('')
            for c in range(len(textList[t])):
                self.text[-1] = f'{self.text[-1]}{listToStr(textList[t][c])}'
        self.size = [sizeXZ[0], offset * 3 + getMaxLen(textList) * textSize, sizeXZ[1]]
        self.stage = 0
        self.stageDisplay = viz.addText3D('', fontSize=textSize)
        self.stageDisplay.setPosition(self.cords[0] - textSize / jetBrainsFontSize, self.cords[1] + self.size[1] / 1.9, self.cords[2])
        self.textObj = viz.addText3D('', fontSize=textSize)
        self.boltText = boldTextList
        self.closeButton = XSymbol(0.5, [self.cords[0] + self.size[0] / 1.9, self.cords[1] + self.size[1] / 1.9, self.cords[2]])
        self.closeButton.setAngle((0, 90, 0))
        self.box = vizshape.addBox(self.size)
        self.box.setPosition(cords)
        self.box.alpha(0.1)
        self.arrows = [vizshape.addArrow(0.1), vizshape.addArrow(0.1)]  # left arrow, right arrow
        self.arrows[0].setPosition(self.cords[0] - 0.5 - self.size[0] / 2, self.cords[1], self.cords[2])
        self.arrows[0].setEuler(-90, 0, 0)
        self.arrows[0].setScale((5, 5, 5))
        self.arrows[1].setPosition(self.cords[0] + 0.5 + self.size[0] / 2, self.cords[1], self.cords[2])
        self.arrows[1].setEuler(90, 0, 0)
        self.arrows[1].setScale((5, 5, 5))
        self.textObj.setPosition(self.cords[0] + offset - self.size[0] / 2, self.cords[1] - offset + self.size[1] / 2, self.cords[2])
        self.textObj.font("JetBrainsMono-2.304\\fonts\\ttf\\JetBrainsMono-Medium.ttf")  # JetBrains Mono is NOT my own work! The authors and OFL are in JetBrainsMono-2.304
        self.cObj = [lController[0], rController[0]]
        self.cDat = [lController[1], rController[1]]
        self.sHeld = [False, False]
        self.lClickHeld = [False, False]

    def drag(self, cIdx, selecting):
        if selecting:
            if not self.sHeld[cIdx]:
                self.sHeld[cIdx] = True
                for a in range(2):
                    if detectCollision(self.cDat[cIdx].radius, 0.3, self.cDat[cIdx].cords, self.arrows[a].getPosition()):
                        if a == 0:
                            self.stage -= 1
                        elif a == 1:
                            self.stage += 1
        else:
            self.sHeld[cIdx] = False
        if mode == 'k':
            if viz.key.isDown(viz.KEY_LEFT):
                if not self.lClickHeld[0]:
                    self.lClickHeld[0] = True
                    self.stage -= 1
            else:
                self.lClickHeld[0] = False
            if viz.key.isDown(viz.KEY_RIGHT):
                if not self.lClickHeld[1]:
                    self.lClickHeld[1] = True
                    self.stage += 1
            else:
                self.lClickHeld[1] = False
        if self.stage < 0:
            self.stage = len(self.text) - 1
        elif self.stage > (len(self.text) - 1):
            self.stage = 0

    def main(self):
        for c in range(controllerCount):
            if buttonPressed('select', self.cObj[c], c) and detectCollision(self.cDat[c].radius, self.closeButton.radius, self.cDat[c].cords, self.closeButton.cords):
                self.drawn = False

        if not self.drawn:
            self.unDraw()

    def draw(self, camCords):
        self.textObj.message(f'{self.text[self.stage]}')
        self.stageDisplay.message(f'{self.stage + 1} / {len(self.text)}')

    def unDraw(self):
        self.textObj.remove()
        self.closeButton.unDraw()
        self.box.remove()
        self.stageDisplay.remove()
        for a in self.arrows:
            a.remove()
