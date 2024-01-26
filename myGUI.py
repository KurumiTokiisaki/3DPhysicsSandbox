import copy
import math
import random

import viz
import vizshape
from globalFunctions import *


class Slider:
    def __init__(self, xyz, referenceVar, globalDefaultVar, cords, length, pointRadius, maxi, mini, text, lController, rController):
        self.type = 'slider'
        self.drawn = True
        self.xyz = xyz
        self.var = referenceVar
        self.origVar = referenceVar
        self.globalOrigVar = globalDefaultVar
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
        self.textOffset = 0.2
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
            self.closeButton.cords = [self.cords[0], self.cords[1] + 0.5, self.limits[0] - 0.2]
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
        self.timePressed = 0
        self.resetHeld = 0

    def resetVar(self, *args):  # reset the value of the reference variable to its initial value from when this class was initialized
        if args:
            self.pCords[self.xyz] = self.limits[0] + ((self.globalOrigVar + abs(self.min) * -getSign(self.min)) / self.range) * self.length
        else:
            self.pCords[self.xyz] = self.limits[0] + ((self.origVar + abs(self.min) * -getSign(self.min)) / self.range) * self.length
        self.oldPCords = copy.deepcopy(self.pCords)

    def setVar(self, var):  # set the reference variable to a specific value
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
        if self.timePressed <= 0.25:
            self.timePressed += 1 / calcRate
        if buttonPressed('reset', self.cObj, 0):
            if not self.resetHeld:
                self.resetHeld = True
                if self.timePressed > 0.25:
                    self.resetVar()
                else:
                    self.resetVar('hard')
                self.timePressed = 0
        else:
            self.resetHeld = False

        for c in range(2):
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
        # self.cBox.point.setPosition(cords)
        self.cords = cords
        self.X = [vizshape.addCylinder(size / math.sqrt(2), 0.03), vizshape.addCylinder(size / math.sqrt(2), 0.03)]
        self.X[0].setEuler(0, 45, 0)
        self.X[1].setEuler(0, 135, 0)
        for c in range(len(self.X)):
            self.X[c].setPosition(self.cords)

    def unDraw(self):
        self.X[0].remove()
        self.X[1].remove()
        if self.cBox.show:
            self.cBox.point.remove()


class Dial:
    def __init__(self, xyz, referenceVar, globalDefaultVar, cords, cRad, pointRadius, mini, maxi, text, lController, rController):
        self.type = 'dial'
        self.drawn = True
        self.xyz = xyz
        self.var = referenceVar
        self.origVar = copy.deepcopy(referenceVar)
        self.globalOrigVar = globalDefaultVar
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
            else:
                self.cAngle.append([0, 0, 0])
            self.circle.append(vizshape.addTorus(cRad, 0.04))
            self.circle[0].setPosition(self.cords)
            self.circle[0].setEuler(self.cAngle[0])
        self.p = Point(pointRadius, True)
        self.p.cords = copy.deepcopy(cords)
        self.p.oldCords = copy.deepcopy(self.p.cords)
        for axis in range(len(mini)):  # used to allow for inheritance in DialThreeD
            self.min.append(mini[axis])
            self.max.append(maxi[axis])
            self.range.append(maxi[axis] - mini[axis])
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
        self.cObj = [lController[0], rController[0]]
        self.cDat = [lController[1], rController[1]]
        self.timePressed = 0
        self.resetHeld = False

    def resetVar(self, *args):
        if args:
            if self.tDim:
                for axis in range(3):
                    self.p.cords[axis] = self.cords[axis] - (self.globalOrigVar[axis] / self.range[axis]) * self.cRad * 2
            else:
                self.p.cords[self.axes[0]] = self.cords[self.axes[0]] - (self.globalOrigVar[self.axes[0]] / self.range[0]) * self.cRad * 2
                self.p.cords[self.axes[1]] = self.cords[self.axes[1]] - (self.globalOrigVar[self.axes[1]] / self.range[1]) * self.cRad * 2
        else:
            if self.tDim:
                for axis in range(3):
                    self.p.cords[axis] = self.cords[axis] - (self.origVar[axis] / self.range[axis]) * self.cRad * 2
            else:
                self.p.cords[self.axes[0]] = self.cords[self.axes[0]] - (self.origVar[self.axes[0]] / self.range[0]) * self.cRad * 2
                self.p.cords[self.axes[1]] = self.cords[self.axes[1]] - (self.origVar[self.axes[1]] / self.range[1]) * self.cRad * 2
        self.p.oldCords = copy.deepcopy(self.p.cords)

    def setVar(self, var):
        if (not self.dragging) or (not self.collision):
            if self.tDim:
                for axis in range(3):
                    self.p.cords[axis] = self.cords[axis] - (var[axis] / self.range[axis]) * self.cRad * 2
            else:
                self.p.cords[self.axes[0]] = self.cords[self.axes[0]] - (var[self.axes[0]] / self.range[0]) * self.cRad * 2
                self.p.cords[self.axes[1]] = self.cords[self.axes[1]] - (var[self.axes[1]] / self.range[1]) * self.cRad * 2

    def drag(self, cIdx, dragging):
        self.dragging = dragging
        if dragging:
            self.collision = detectCollision(self.cDat[cIdx].radius, self.p.radius, self.cDat[cIdx].cords, self.p.cords)
            if self.collision:
                if not self.tDim:
                    self.p.cords[self.axes[0]] = copy.deepcopy(self.cDat[cIdx].cords[0])
                    self.p.cords[self.axes[1]] = copy.deepcopy(self.cDat[cIdx].cords[1])
                else:
                    self.p.cords = copy.deepcopy(self.cDat[cIdx].cords)

    def interpolate(self):
        relDist = []
        ratio = []
        for dim in range(len(self.min)):
            relDist.append(self.p.cords[self.axes[dim]] - (self.cords[self.axes[dim]] - self.cRad))
            ratio.append(relDist[dim] / (self.cRad * 2))
            self.var[self.axes[dim]] = -self.min[dim] - (self.range[dim] * ratio[dim])

    def main(self):
        if self.timePressed <= 0.25:
            self.timePressed += 1 / calcRate
        if buttonPressed('reset', self.cObj, 0):
            if not self.resetHeld:
                self.resetHeld = True
                if self.timePressed > 0.25:
                    self.resetVar()
                else:
                    self.resetVar('hard')
                self.timePressed = 0
        else:
            self.resetHeld = False

        for c in range(2):
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
            self.textFront.message(f'{self.text[0]}: {round(self.var[0], 4)}\n{self.text[1]}: {round(self.var[1], 4)}')
            self.textFront.setPosition(self.p.cords[0] - 0.3, self.p.cords[1] - 0.2, self.p.cords[2] - 0.2)
        else:
            self.textFront.message(f'{self.text[0]}: {round(self.var[0], 4)}\n{self.text[1]}: {round(self.var[1], 4)}\n{self.text[2]}: {round(self.var[2], 4)}')
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
    def __init__(self, xyz, referenceVar, globalDefaultVar, cords, text, lController, rController):
        self.xyz = xyz
        self.drawn = True
        self.var = referenceVar
        self.origVar = copy.deepcopy(referenceVar)
        self.globalOrigVar = globalDefaultVar
        self.text = text
        self.cords = cords
        self.textVar = viz.addText3D('', fontSize=0.1)
        self.textVar.setPosition(self.cords)
        self.cObj = [lController[0], rController[0]]
        self.cDat = [lController[1], rController[1]]
        self.keys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', viz.KEY_BACKSPACE, '-', viz.KEY_RETURN]
        self.keyHeld = []
        for k in range(len(self.keys)):
            self.keyHeld.append(False)
        self.timePressed = 0
        self.resetHeld = False

    def main(self):
        if self.timePressed <= 0.25:
            self.timePressed += 1 / calcRate
        if buttonPressed('reset', self.cObj, 0):
            if not self.resetHeld:
                self.resetHeld = True
                if self.timePressed > 0.25:
                    self.resetVar()
                else:
                    self.resetVar('hard')
                self.timePressed = 0
        else:
            self.resetHeld = False

        if viz.key.anyDown(self.keys):
            for n in range(10):
                if viz.key.isDown(f'{n}'):
                    if not self.keyHeld[n]:
                        self.var = float(f'{self.var}{n}')
                        self.keyHeld[n] = True
                        break
                else:
                    self.keyHeld[n] = False
            if viz.key.isDown(viz.KEY_BACKSPACE):
                if not self.keyHeld[10]:
                    self.keyHeld[10] = True
                    tempVar = ''
                    self.var = str(self.var)
                    if len(self.var) == 1:
                        tempVar = 0
                    else:
                        for i in range(len(self.var) - 1):
                            tempVar = f'{tempVar}{self.var[i]}'
                    self.var = float(tempVar)
                else:
                    self.keyHeld[10] = False
            if viz.key.isDown('-'):
                if not self.keyHeld[11]:
                    self.keyHeld[11] = True
                    self.var = -self.var
                else:
                    self.keyHeld[11] = False

            if viz.key.isDown(viz.KEY_RETURN):
                self.drawn = False

        if not self.drawn:
            self.unDraw()
        return self.var

    def drag(self, cIdx, selecting):
        pass

    def draw(self, camCords):
        self.textVar.message(f'{self.text}\n{round(self.var, 4)}')
        angle, pos = camAnglePos(camCords, self.cords, 0)
        self.textVar.setEuler(angle)

    def setVar(self, var):
        self.var = var

    def resetVar(self, *args):
        if args:
            self.var = self.globalOrigVar
        else:
            self.var = self.origVar

    def unDraw(self):
        self.textVar.remove()


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
    def __init__(self, varDict, cords, lController, rController):
        self.cords = [cords[0] - (len(varDict) - 1) / 2, cords[1], cords[2]]
        self.drawn = True
        self.cObj = [lController[0], rController[0]]
        self.cDat = [lController[1], rController[1]]
        self.selecting = False
        self.sHeld = False
        self.collision = False
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
        self.selecting = selecting
        if selecting:
            for p in range(len(self.collP)):
                self.collision = detectCollision(self.cDat[cIdx].radius, self.collP[p].radius, self.cDat[cIdx].cords, self.collP[p].cords)
                if self.collision and (not self.sHeld):
                    self.sHeld = True
                    if self.stage == 'varSelection':
                        self.var = list(self.GUIs.keys())[p]
                        self.unDraw()
                        self.selectGUI(GUItypes)
                    elif self.stage == 'GUISelection':
                        if (type(globalVars[self.var]) is not list) and (list(self.GUIs.keys())[p] == 'Manual'):
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
            self.sHeld = False

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
            return self.var, self.GUI

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
