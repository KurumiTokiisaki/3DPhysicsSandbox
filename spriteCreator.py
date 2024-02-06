# base Vizard libraries

import random
import time

import viz
import vizfx
import vizshape
import vizconnect
import steamvr
import vizact
# for trig functions
import viztask
import math
# used for setting one variable to another
import copy

from globalFunctions import *
import myGUI

# Vizard window initialization
viz.setMultiSample(4)  # FSAA (Full Screen Anti-Alaiasing)
viz.fov(90)
viz.go()

if mode == 'vr':
    import steamVR_init as controlsConf
elif mode == 'k':
    import keyboard_mouse_init as controlsConf

    if fullscreen:
        viz.window.setFullscreen()

controls = controlsConf.Main()

viz.vsync(0)  # disable vsync (cuz it decreases max calcs/second)


def selectP(cIdx):
    return buttonPressed('select', controlsConf.controllers[cIdx], cIdx)


def getYCollisionPlane(b, cords):
    return {
        'left': {'y': (b.grad['y'] * cords[0]) + (b.vertex[1][1] - (b.grad['y'] * b.vertex[1][0])), 'm': b.grad['y'], 'c': b.vertex[1][1] - (b.grad['y'] * b.vertex[1][0])},
        'right': {'y': (b.grad['y'] * cords[0]) + (b.vertex[0][1] - (b.grad['y'] * b.vertex[0][0])), 'm': b.grad['y'], 'c': b.vertex[0][1] - (b.grad['y'] * b.vertex[0][0])},
        'top': {'y': (b.grad['x'] * cords[0]) + (b.vertex[1][1] - (b.grad['x'] * b.vertex[1][0])), 'm': b.grad['x'], 'c': b.vertex[1][1] - (b.grad['x'] * b.vertex[1][0])},
        'bottom': {'y': (b.grad['x'] * cords[0]) + (b.vertex[2][1] - (b.grad['x'] * b.vertex[2][0])), 'm': b.grad['x'], 'c': b.vertex[2][1] - (b.grad['x'] * b.vertex[2][0])},
    }


def getXCollisionPlane(b, cords):
    return {
        'left': {'x': - (b.grad['x'] * cords[1]) + (b.vertex[1][0] + (b.grad['x'] * b.vertex[1][1])), 'm': -b.grad['x'], 'c': b.vertex[1][0] + (b.grad['x'] * b.vertex[1][1])},
        'right': {'x': - (b.grad['x'] * cords[1]) + (b.vertex[0][0] + (b.grad['x'] * b.vertex[0][1])), 'm': -b.grad['x'], 'c': b.vertex[0][0] + (b.grad['x'] * b.vertex[0][1])},
        'top': {'x': - (b.grad['y'] * cords[1]) + (b.vertex[1][0] + (b.grad['y'] * b.vertex[1][1])), 'm': -b.grad['y'], 'c': b.vertex[1][0] + (b.grad['y'] * b.vertex[1][1])},
        'bottom': {'x': - (b.grad['y'] * cords[1]) + (b.vertex[2][0] + (b.grad['y'] * b.vertex[2][1])), 'm': -b.grad['y'], 'c': b.vertex[2][0] + (b.grad['y'] * b.vertex[2][1])}
    }


def getCubeCollision(cords, radius, b, yCollisionPlane):
    return (cords[1] <= (collisionTolerance + yCollisionPlane['top']['y'] + radius / cos(b.angle[2]))) and (cords[1] >= (-collisionTolerance + yCollisionPlane['bottom']['y'] - radius / cos(b.angle[2]))) and (cords[1] <= (collisionTolerance + yCollisionPlane['right']['y'] + radius / sin(b.angle[2]))) and (
            cords[1] >= (-collisionTolerance + yCollisionPlane['left']['y'] - radius / sin(b.angle[2]))) and (cords[2] <= (collisionTolerance + b.plane['front'] + radius)) and (cords[2] >= (-collisionTolerance + b.plane['back'] - radius))


class Main:
    def __init__(self):
        self.points = []
        self.joints = []
        self.collisionRect = []  # list of collision rectangles
        self.dragP = [None, None]  # last clicked point index
        self.dragC = [None, None]  # last clicked controller index for the last clicked point
        self.lastP = [None, None]  # last clicked point that always retains its value for "recalling" objects to the controller
        self.dragR = [None, None]  # last clicked controller index for the last clicked collision rect
        self.theForceJoint = False  # True if the force is being used
        self.pause = False  # pauses physics
        self.pHeld = [False, False]  # stores if 'p' is held down
        self.rHeld = [False, False]  # stores if 'r' is held down
        self.lHeld = [False, False]  # stores if 'l' is held down
        self.GUISelector = [False, False]  # stores if the button to summon the GUI selector is held
        self.selectHeld = [False, False]  # stores if the select button is held on either controller
        self.collP = [None, None]  # stores the indexes of a point that is colliding with either controller
        self.anim = []  # stores all animations specific to the Main class
        self.animeScale = [1, 1]  # visual scale of animations
        self.animeScaleSpeed = 0  # rate at which animations scale
        self.animeColor = [[0, 0, 0], [0, 0, 0]]  # color of each animation
        self.GUIType = None  # holds the return value of GUISelector to create relevant GUI(s)
        self.clickTime = [0, 0]  # stores time since 'select' was pressed for both controllers in order for double-click detection
        self.relPos = [[0, 0, 0], [0, 0, 0]]  # stores the relative position of selected points with either controller
        self.GUI = {
            'GUISelector': {'': {'': None}},
            'Tutorials': {'': {}}
        }
        self.addPoint([0, 0, 0], 0.1)

    def addPoint(self, cords, radius):
        self.points.append(Point(cords, radius))
        self.GUI.update({len(self.points) + 999: {'slider': {'radius': None, 'density': None}, 'manual': {'radius': None, 'density': None}}})
        self.lastP = [len(self.points) - 1, len(self.points) - 2]

    def addCollisionRect(self, cRect):
        self.collisionRect.append(cRect)
        self.GUI.update({len(self.collisionRect) - 1: {'dial': {'XZ': None, 'XY': None, 'YZ': None, '3D': None, 'density': None, 'angle': None}, 'slider': {0: None, 1: None, 2: None, 'density': None, 'angle': None}, 'manual': {0: None, 1: None, 2: None, 'density': None, 'angle': None}}})

    def main(self):
        self.dragPoint()

    def dragPoint(self):
        # if mode == 'vr':
        #     print(controlsConf.controllers[0].getButtonState() % touchpad, controlsConf.controllers[1].getButtonState() % touchpad)  # prints the current button being pressed for each controller

        # loop through all drag code for each controller
        for c in range(controlsConf.controllerAmt):
            if self.clickTime[c] <= 0.25:
                self.clickTime[c] += 1 / calcRate
            for g in self.GUI:
                for gu in self.GUI[g]:
                    for gui in self.GUI[g][gu]:
                        if self.GUI[g][gu][gui] is not None:
                            self.GUI[g][gu][gui].drag(c, selectP(c))
            for p in range(len(self.points)):
                if detectCollision(self.points[p].radius, controls.hand[c].radius, self.points[p].cords, controls.hand[c].cords) and (self.dragR[c] is None):
                    self.collP[c] = p  # set the collision point to the current point's index
                    if selectP(c):  # detect if the select button is being pressed, depending on the controller mode
                        if not self.selectHeld[c]:
                            self.selectHeld[c] = True
                            for axis in range(3):
                                self.relPos[c][axis] = self.points[p].cords[axis] - controls.hand[c].cords[axis]
                            cords = controls.hand[c].cords  # set cords to the current controller's cords to shorten the below for increased readability
                            if self.clickTime[c] < 0.25:  # if there's a double click, summon sliders (if in VR) or manual inputs (if in keyboard/mouse) to change the density and radius of the double-clicked point
                                if self.GUI[p + 1000]['slider']['radius'] is None:  # only summon if GUI is empty
                                    if mode == 'vr':
                                        self.GUI[p + 1000]['slider']['radius'] = myGUI.Slider(0, self.points[p].radius, self.points[p].origRadius, [cords[0], cords[1] + 0.5, cords[2]], 10, 0.1, maxRadius, minRadius, 'Radius', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                                    else:
                                        self.GUI[p + 1000]['slider']['radius'] = myGUI.Manual(0, self.points[p].radius, self.points[p].origRadius, [cords[0], cords[1] + 0.5, cords[2]], 'Radius', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                                if self.GUI[p + 1000]['slider']['density'] is None:  # only summon if GUI is empty
                                    if mode == 'vr':
                                        self.GUI[p + 1000]['slider']['density'] = myGUI.Slider(0, self.points[p].density, self.points[p].origDensity, [cords[0], cords[1] - 0.5, cords[2]], 10, 0.1, 10000, 1, 'Density', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                                        self.GUI[p + 1000]['slider']['density'].closeButton.unDraw()  # only one 'X' needs to be rendered, since there are two Xs within each other
                                        self.GUI[p + 1000]['slider']['density'].closeButton.cords[1] = cords[1] + 1  # offset this 'X' to be within the other 'X' so that they both act as one button to dismiss both radius and density GUIs simultaneously
                                    else:
                                        self.GUI[p + 1000]['slider']['density'] = myGUI.Manual(0, self.points[p].density, self.points[p].origDensity, [cords[0], cords[1] - 0.5, cords[2]], 'Density', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                            else:
                                self.clickTime[c] = 0  # reset the time since last click, since this click IS the last click!
                        if self.dragP[c] is None:  # used to set the drag variables if they are not already set
                            self.dragP[c] = p
                            if self.lastP[c] != p:  # no need to run the below if the value of lastP won't change
                                if mode == 'vr':
                                    if self.lastP[c - 1] != p:  # only allow unique points to be recalled by each controller
                                        self.lastP[c] = p
                                else:
                                    self.lastP[c] = p
                    else:
                        self.selectHeld[c] = False

            for cr in range(len(self.collisionRect)):
                yCollisionPlane = getYCollisionPlane(self.collisionRect[cr], controls.hand[c].cords)
                if getCubeCollision(controls.hand[c].cords, controls.hand[c].radius, self.collisionRect[cr], yCollisionPlane) and (self.dragC[c] is None):
                    if selectP(c):
                        if not self.selectHeld[c]:
                            self.selectHeld[c] = True
                            for axis in range(3):
                                self.relPos[c][axis] = self.collisionRect[cr].cords[axis] - controls.hand[c].cords[axis]
                            cords = controls.hand[c].cords
                            if self.clickTime[c] < 0.25:  # if there's a double click, summon sliders (if in VR) or manual inputs (if in keyboard/mouse) to change the size and density of the double-clicked collision rect
                                if mode == 'k':
                                    if self.GUI['GUISelector'][''][''] is None:
                                        self.GUI['GUISelector'][''][''] = myGUI.GUISelector({'Size': None, 'Angle': None}, [controls.hand[c].cords[0], controls.hand[c].cords[1] - 1, controls.hand[c].cords[2]], [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]], cr)
                                    else:
                                        self.GUI['GUISelector'][''][''].drawn = False
                                        self.GUI['GUISelector'][''][''].unDraw()
                                else:
                                    for axis in range(3):
                                        if self.GUI[cr]['slider'][axis] is None:  # only summon if GUI is empty
                                            if mode == 'vr':
                                                self.GUI[cr]['slider'][axis] = myGUI.Slider(axis, self.collisionRect[cr].size[axis], self.collisionRect[cr].origSize[axis], [cords[0], cords[1] + (axis - 2) * 0.5, cords[2]], 10, 0.1, maxRadius, minRadius, f'Size {axis}', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                                            else:
                                                self.GUI[cr]['slider'][axis] = myGUI.Manual(axis, self.collisionRect[cr].size[axis], self.collisionRect[cr].origSize[axis], [cords[0], cords[1] + (axis - 2) * 0.5, cords[2]], f'Size {axis}', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                                    if self.GUI[cr]['slider']['density'] is None:  # only summon if GUI is empty
                                        if mode == 'vr':
                                            self.GUI[cr]['slider']['density'] = myGUI.Slider(0, self.collisionRect[cr].density, self.collisionRect[cr].origDensity, [cords[0], cords[1] - 0.5, cords[2]], 10, 0.1, 10000, 1, 'Density', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                                            self.GUI[cr]['slider']['density'].closeButton.unDraw()  # only one 'X' needs to be rendered, since there are two Xs within each other
                                            self.GUI[cr]['slider']['density'].closeButton.cords[1] = cords[1] + 1  # offset this 'X' to be within the other 'X' so that they both act as one button to dismiss both radius and density GUIs simultaneously
                                        else:
                                            self.GUI[cr]['slider']['density'] = myGUI.Manual(0, self.collisionRect[cr].density, self.collisionRect[cr].origDensity, [cords[0], cords[1] + 1, cords[2]], 'Density', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                            else:
                                self.clickTime[c] = 0  # reset the time since last click, since this click IS the last click!
                        if self.dragR[c] is None:  # used to set the drag variables if they are not already set
                            self.dragR[c] = cr
                    else:
                        self.selectHeld[c] = False

            if self.dragP[c] is not None:
                for axis in range(3):
                    self.points[self.dragP[c]].cords[axis] = controls.hand[c].cords[axis] + self.relPos[c][axis]  # set the point position to the controller that grabbed said point's position
            if self.dragR[c] is not None:
                tempCords = [0, 0, 0]
                for axis in range(3):
                    tempCords[axis] = controls.hand[c].cords[axis] + self.relPos[c][axis]
                self.collisionRect[self.dragR[c]].setVars(tempCords)  # set the collision rect position to the controller that grabbed said collision rect's position
            # unique animation for selecting points
            if self.collP[c] is not None:  # only run animations if a point is intersecting with a controller
                if self.dragP[c] is not None:  # only run the below if a point is being dragged
                    controls.anim[c].point = self.points[self.collP[c]]  # make the selection animation encapsulate the point
                    if self.animeScale[c] > (self.points[self.collP[c]].radius / controls.anim[c].sphereRad):  # set the maximum size of the animation equal to the size of the selected point
                        self.animeScaleSpeed -= 0.1 / physicsTime
                        self.animeScale[c] += self.animeScaleSpeed
                        # approximate function for changing color with time based on radius: f(x) = 6 / (time * sqrt(radius * 10))
                        f = 6 / (renderRate * math.sqrt(self.points[self.collP[c]].radius * 10))
                        # green-shift the animation
                        self.animeColor[c][0] -= f
                        self.animeColor[c][1] += f
                    else:
                        self.animeScale[c] = self.points[self.collP[c]].radius / controls.anim[c].sphereRad
                        controls.anim[c].pause = True
                    controls.anim[c].setScale(self.animeScale[c])
                    controls.anim[c].setColor(self.animeColor[c])
                elif not detectCollision(self.points[self.collP[c]].radius, controls.hand[c].radius, self.points[self.collP[c]].cords, controls.hand[c].cords):
                    controls.anim[c].point = controls.hand[c]
                    controls.anim[c].setScale(1)
                    self.collP[c] = None
                    controls.anim[c].pause = False
                else:
                    controls.anim[c].point = self.points[self.collP[c]]
                    self.animeScale[c] = 1.2 * self.points[self.collP[c]].radius / controls.anim[c].sphereRad
                    self.animeScaleSpeed = 0
                    controls.anim[c].setScale(self.animeScale[c])
                    self.animeColor[c] = [1, 0, 0]
                    controls.anim[c].setColor([1, 0, 0])
                    controls.anim[c].pause = False
            else:  # return the animation to the controller
                controls.anim[c].resetColor()
                controls.anim[c].resetScale()
                controls.anim[c].point = controls.hand[c]
            # reset drag variables if select button is not pressed
            if not selectP(c):
                self.dragP[c] = None
                self.dragR[c] = None
            # recalls the last clicked point to the controller's position
            if buttonPressed('recall', controlsConf.controllers[c], c):
                self.points[self.lastP[c]].cords = copy.deepcopy(controls.hand[c].cords)
                if not self.rHeld:
                    self.tpCloth(self.lastP[c], self.points[self.lastP[c]].cords, c, 'point')
                    self.rHeld = True
            # remove the force joint after recall is no longer active
            elif self.theForceJoint:
                if self.joints[-1].show:
                    self.joints[-1].cylinder.remove()
                self.joints.pop(-1)
                self.theForceJoint = False
            else:
                self.rHeld = False

    def tpCloth(self, cloth, cords, c, tpType):
        cordDiff = []
        if tpType == 'cloth':
            pIdx = self.clothData[cloth][0]
            for co in range(3):
                cordDiff.append(controls.hand[co].cords - self.points[pIdx].cords[co])
            if cloth != '':
                for p in self.clothData[f'{cloth}']:
                    if p != pIdx:
                        for cor in range(3):
                            self.points[p].cords[cor] += cordDiff[cor]
            self.points[pIdx].cords = copy.deepcopy(cords)
        elif tpType == 'point':
            for co in range(3):
                cordDiff.append(controls.hand[co].cords - self.points[cloth].cords[co])
            if self.points[cloth].cloth != '':
                for p in self.clothData[f'{self.points[cloth].cloth}']:
                    if p != self.lastP[c]:
                        for cor in range(3):
                            self.points[p].cords[cor] += cordDiff[cor]
            self.points[cloth].cords = copy.deepcopy(cords)

    def updateGUI(self):
        for g in self.GUI:
            for gt in self.GUI[g]:
                for gta in self.GUI[g][gt]:
                    if self.GUI[g][gt][gta] is not None:
                        if self.GUI[g][gt][gta].drawn:
                            if g == 'GUISelector':
                                self.GUIType = self.GUI[g][gt][gta].main()
                            else:
                                pcIdx = g  # for both points and collision rects, depending on what was double-clicked
                                if gta == 'radius':
                                    self.GUI[g][gt][gta].setVar(self.points[pcIdx - 1000].radius)
                                    self.points[pcIdx - 1000].setRadiusDensity(self.GUI[g][gt][gta].main(), self.points[pcIdx - 1000].density)
                                elif gta == 'density':
                                    if g >= 1000:
                                        self.GUI[g][gt][gta].setVar(self.points[pcIdx - 1000].density)
                                        self.points[pcIdx - 1000].setRadiusDensity(self.points[pcIdx - 1000].radius, self.GUI[g][gt][gta].main())
                                    else:
                                        self.GUI[g][gt][gta].setVar(self.collisionRect[pcIdx].density)
                                        self.collisionRect[pcIdx].density = self.GUI[g][gt][gta].main()
                                elif gta == 'angle':
                                    self.GUI[g][gt][gta].setVar(math.degrees(self.collisionRect[pcIdx].angle[2]))
                                    self.collisionRect[pcIdx].setVars(self.collisionRect[pcIdx].cords, self.collisionRect[pcIdx].size[0], 0, math.radians(self.GUI[g][gt][gta].main()), 2)
                                else:
                                    size = self.GUI[g][gt][gta].main()
                                    if type(size) is list:
                                        self.GUI[g][gt][gta].setVar(self.collisionRect[pcIdx].size)
                                        for axis in self.GUI[g][gt][gta].axes:
                                            self.collisionRect[pcIdx].setVars(self.collisionRect[pcIdx].cords, size[axis], axis)
                                    else:
                                        self.GUI[g][gt][gta].setVar(self.collisionRect[pcIdx].size[self.GUI[g][gt][gta].xyz])
                                        self.collisionRect[pcIdx].setVars(self.collisionRect[pcIdx].cords, size, self.GUI[g][gt][gta].xyz)

                        else:
                            self.GUI[g][gt][gta] = None

        if self.GUIType is not None:
            if self.GUIType[0] == 'Size':
                if self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['density'] is not None:
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['density'].unDraw()
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['density'] = None
                if self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['angle'] is not None:
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['angle'].unDraw()
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['angle'] = None
                if self.GUIType[1][0] == 'Slider':
                    size = 10
                    for axis in range(3):
                        if self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis] is not None:
                            self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis].unDraw()
                            self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis] = None
                        cords = copy.deepcopy(controls.hand[0].cords)
                        cords[axis] += 0.2 + size / 2
                        self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis] = myGUI.Slider(axis, self.collisionRect[self.GUIType[3][0]].size[axis], 1, cords, size, 0.15, 100, 0.1, f'Size {axis}', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['density'] = myGUI.Slider(0, self.collisionRect[self.GUIType[3][0]].density, 1000, [controls.hand[0].cords[0] + 2.5, controls.hand[0].cords[1] - 1, controls.hand[0].cords[2]], 5, 0.15, 50000, 10, 'Density', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['angle'] = myGUI.Slider(0, self.collisionRect[self.GUIType[3][0]].angle[2], 0.00001, [controls.hand[0].cords[0] + 2.5, controls.hand[0].cords[1] - 2, controls.hand[0].cords[2]], 5, 0.15, 89.99999, 0.00001, 'Angle', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                elif self.GUIType[1][0] == 'Manual':
                    for axis in range(3):
                        if self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis] is not None:
                            self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis].unDraw()
                            self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis] = None
                        cords = copy.deepcopy(controls.hand[0].cords)
                        if mode == 'vr':
                            cords[0] += axis * 3.5
                            yDisp = -6.5
                            xDisp = 3.5
                        else:
                            cords[0] += axis * 0.5
                            yDisp = -0.5
                            xDisp = 0.5
                        self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis] = myGUI.Manual(axis, self.collisionRect[self.GUIType[3][0]].size[axis], 1, cords, f'Size {axis}', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]], False)
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['density'] = myGUI.Manual(0, self.collisionRect[self.GUIType[3][0]].density, 1000, [controls.hand[0].cords[0], controls.hand[0].cords[1] + yDisp, controls.hand[0].cords[2]], 'Density', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]], False)
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['angle'] = myGUI.Manual(0, self.collisionRect[self.GUIType[3][0]].angle[2], 0.00001, [controls.hand[0].cords[0] + xDisp, controls.hand[0].cords[1] + yDisp, controls.hand[0].cords[2]], 'Angle', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]], False)
                elif self.GUIType[1][0] == 'Dial':
                    varOffset = self.collisionRect[self.GUIType[3][0]].sizeOffset
                    cRad = 10
                    if self.GUIType[1][1] == '3D':
                        self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['3D'] = myGUI.Dial(0, self.collisionRect[self.GUIType[3][0]].size, [-11, -11, -11], controls.hand[0].cords, cRad, 0.15, [20, 20, 20], [-20, -20, -20], 'XYZ', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]], varOffset[0], varOffset[1], varOffset[2])
                        closeButtonCords = self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['3D'].closeButton.cords
                    else:
                        self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['XY'] = myGUI.Dial(1, self.collisionRect[self.GUIType[3][0]].size, [-11, -11, -11], controls.hand[0].cords, cRad, 0.15, [20, 20], [-20, -20], 'XY', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]], varOffset[0], varOffset[1], varOffset[2])
                        closeButtonCords = self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['XY'].closeButton.cords
                        self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['XZ'] = myGUI.Dial(0, self.collisionRect[self.GUIType[3][0]].size, [-11, -11, -11], controls.hand[0].cords, cRad, 0.15, [20, 20], [-20, -20], 'XZ', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]], varOffset[0], varOffset[1], varOffset[2])
                        self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['XZ'].closeButton.setPos(closeButtonCords, True)
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['density'] = myGUI.Slider(0, self.collisionRect[self.GUIType[3][0]].density, 1000, [controls.hand[0].cords[0], controls.hand[0].cords[1] - 0.5, controls.hand[0].cords[2] - cRad - 0.2], 5, 0.15, 50000, 10, 'Density', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['density'].closeButton.setPos(closeButtonCords, True)
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['angle'] = myGUI.Slider(0, self.collisionRect[self.GUIType[3][0]].angle[2], 0.00001, [controls.hand[0].cords[0], controls.hand[0].cords[1] + 0.5, controls.hand[0].cords[2] - cRad - 0.2], 5, 0.15, 89.99999, 0.00001, 'Angle', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['angle'].closeButton.setPos(closeButtonCords, True)
            elif self.GUIType[0] == 'Angle':
                print(self.GUIType)
            elif self.GUIType[0] == 'Tutorials':
                if self.GUI[self.GUIType[0]][''][self.GUIType[1][0]] is not None:
                    self.GUI[self.GUIType[0]][''][self.GUIType[1][0]].unDraw()
                    self.GUI[self.GUIType[0]][''][self.GUIType[1][0]] = None
                self.GUI[self.GUIType[0]][''][self.GUIType[1][0]] = myGUI.Tutorial(controls.hand[0].cords, [10, 0.2], self.tutorialTexts[self.GUIType[1][0]], [], 0.3, [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
            self.GUIType = None

    def render(self):
        self.updateGUI()
        controls.main()
        for p in self.points:
            p.draw()
        for j in self.joints:
            j.draw()
        for g in self.GUI:
            for gu in self.GUI[g]:
                for gui in self.GUI[g][gu]:
                    if self.GUI[g][gu][gui] is not None:
                        self.GUI[g][gu][gui].draw(controls.camCords)
        for c in self.collisionRect:
            c.draw()


class Point:
    def __init__(self, cords, radius):
        self.cords = copy.deepcopy(cords)
        self.radius = radius
        self.origRadius = radius
        self.density = 1000
        self.origDensity = 1000
        self.point = vizshape.addSphere()
        self.setRadiusDensity(self.radius, self.density)
        self.cloth = ''
        self.dragging = False

    def setRadiusDensity(self, radius, density):
        self.radius = radius
        self.density = density
        self.point.setScale([self.radius, self.radius, self.radius])

    def main(self):
        pass

    def draw(self):
        self.point.setPosition(self.cords)


class CollisionRect:
    def __init__(self, size, sizeOffset, cords, angle, density, viscosity, dragConst, transparency, rectType, *hide):
        self.type = rectType  # solid or liquid
        self.angle = angle
        self.vertexAngle = [0, 0, 0]
        self.size = size
        self.origSize = size
        self.show = False
        if not hide:
            self.show = True
            self.rect = vizshape.addBox([1, 1, 1])
            self.rect.setScale(self.size)
        self.cords = cords
        self.density = density
        self.origDensity = density
        self.dragConst = dragConst
        self.viscosity = viscosity
        self.transparency = transparency
        self.vertex = [None, None, None, None, None, None, None, None]  # [x, y, z] -> [['right', 'top', 'front'], ['left', 'top', 'front'], ['left', 'bottom', 'front'], ['left', 'bottom', 'back'], ['left', 'top', 'back'], ['right', 'top', 'back'], ['right', 'bottom', 'back'], ['right', 'bottom', 'front']]
        self.plane = {
            'front': 0,
            'back': 0,
            'left': 0,
            'right': 0,
            'top': 0,
            'bottom': 0
        }
        self.grad = dict
        self.sf = 1
        self.sizeOffset = sizeOffset
        self.update()

    def update(self):
        tempSize = [self.size[0] + self.sizeOffset[0], self.size[1] + self.sizeOffset[1], self.size[2] + self.sizeOffset[2]]
        sizeMultiplier = [0.5, 0.5, 0.5]
        multiplier = 1
        self.vertexAngle = math.atan(tempSize[1] / tempSize[0])
        for v in range(8):
            if (v == 1) or (v == 5):
                sizeMultiplier[0] = -sizeMultiplier[0]
            elif (v == 4) or (v == 6) or (v == 2):
                sizeMultiplier[1] = -sizeMultiplier[1]
            elif (v == 3) or (v == 7):
                sizeMultiplier[2] = -sizeMultiplier[2]
            if (v == 1) or (v == 4) or (v == 6) or (v == 7):
                multiplier = -1
            elif (v == 0) or (v == 5) or (v == 2) or (v == 3):
                multiplier = 1
            tempVertex = [0, 0, 0]
            xySize = math.sqrt((tempSize[0]) ** 2 + (tempSize[1]) ** 2)
            for i in range(3):
                if i == 0:  # x
                    tempVertex[i] = self.cords[i] + (xySize * sizeMultiplier[i] * cos(self.vertexAngle + (multiplier * self.angle[2])))
                elif i == 1:  # y
                    tempVertex[i] = self.cords[i] + (xySize * sizeMultiplier[i] * sin(self.vertexAngle + (multiplier * self.angle[2])))
                elif i == 2:  # z
                    tempVertex[i] = self.cords[i] + (tempSize[i] * sizeMultiplier[i])

            self.vertex[v] = tempVertex

        self.plane['right'] = self.cords[0] + (tempSize[0] / 2)
        self.plane['left'] = self.cords[0] - (tempSize[0] / 2)
        self.plane['top'] = self.cords[1] + (tempSize[1] / 2)
        self.plane['bottom'] = self.cords[1] - (tempSize[1] / 2)
        self.plane['front'] = self.cords[2] + (tempSize[2] / 2)
        self.plane['back'] = self.cords[2] - (tempSize[2] / 2)

        if self.vertex[0][0] != self.vertex[1][0]:
            mx = (self.vertex[0][1] - self.vertex[1][1]) / (self.vertex[0][0] - self.vertex[1][0])
        else:
            mx = float('inf')
        if self.vertex[5][0] != self.vertex[6][0]:
            my = (self.vertex[5][1] - self.vertex[6][1]) / (self.vertex[5][0] - self.vertex[6][0])
        else:
            my = float('inf')
        self.grad = {
            'x': mx,
            'y': my
        }

    def draw(self):
        if self.show:
            tempSize = [self.size[0] + self.sizeOffset[0], self.size[1] + self.sizeOffset[1], self.size[2] + self.sizeOffset[2]]
            self.rect.setScale(tempSize)
            self.rect.setPosition(self.cords)
            self.rect.setEuler(math.degrees(self.angle[0]), math.degrees(self.angle[1]), math.degrees(self.angle[2]))
            self.rect.alpha(self.transparency)

    def setVars(self, cords, *sizeAngle):
        self.cords = copy.deepcopy(cords)
        if len(sizeAngle) >= 1:
            self.size[sizeAngle[1]] = copy.deepcopy(sizeAngle[0])
        if len(sizeAngle) >= 3:
            self.angle[sizeAngle[3]] = copy.deepcopy(sizeAngle[2])
        self.update()


class Joint:
    def __init__(self, pOne, pTwo):
        self.pOne = pOne
        self.pTwo = pTwo
        self.cylinder = vizshape.addCylinder()
        self.length = 0

    def draw(self):
        self.cylinder.setScale([1, self.length, 1])

    def unDraw(self):
        self.cylinder.remove()


game = Main()
game.addCollisionRect(CollisionRect([-11, -11, -11], [12, 12, 12], [2, 1, 0], [0, 0, math.radians(69)], 1000, 10, 1, 0.5, 's'))

vizact.ontimer(1 / physicsTime, game.main)
vizact.ontimer(1 / renderRate, game.render)
