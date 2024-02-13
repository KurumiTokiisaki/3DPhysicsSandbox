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

import config
from globalFunctions import *
import myGUI

while True:
    imports = input('Edit exportData? (y / n): ')
    if imports == 'y':
        imports = True
    elif imports == 'n':
        imports = False
    if type(imports) is bool:
        break
    else:
        print('Please enter y / n!')

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


# mode = 'vr'  # uncomment for testing VR settings on keyboard/mouse


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
        self.timer = 0  # stores how long the program is being run for so that it can save & exit before the 5-minute limit from the free Vizard license
        self.points = []
        self.joints = []
        self.collisionRect = []  # list of collision rectangles
        self.dragP = [None, None]  # last clicked point index
        self.lastP = [None, None]  # last clicked point that always retains its value for "recalling" objects to the controller
        self.lastR = [None, None]
        self.dragR = [None, None]  # last clicked controller index for the last clicked collision rect
        self.theForceJoint = False  # True if the force is being used
        self.pause = False  # pauses physics
        self.buttonHeld = {}
        for c in config.controls:
            self.buttonHeld.update({c: [False, False]})
        self.GUISelector = [False, False]  # stores if the button to summon the GUI selector is held
        self.buttonHeld['select'] = [False, False]  # stores if the select button is held on either controller
        self.collP = [None, None]  # stores the indexes of a point that is colliding with either controller
        self.anim = []  # stores all animations specific to the Main class
        self.animeScale = [1, 1]  # visual scale of animations
        self.animeScaleSpeed = 0  # rate at which animations scale
        self.animeColor = [[0, 0, 0], [0, 0, 0]]  # color of each animation
        self.GUIType = None  # holds the return value of GUISelector to create relevant GUI(s)
        self.clickTime = [0, 0]  # stores time since 'select' was pressed for both controllers in order for double-click detection
        self.jClickTime = [0, 0]  # stores time since 'j' was pressed for both controllers in order for double-click detection
        self.relPos = [[0, 0, 0], [0, 0, 0]]  # stores the relative position of selected points with either controller
        self.GUI = {
            'GUISelector': {'': {'main': None, 'pointRect': None}},
            'Tutorials': {'': {}}
        }
        self.newJoint = None
        self.tutorialTexts = {}
        self.importTutorials()
        self.voidBox = [VoidBox([-1, 0, 0], 'point'), VoidBox([-1, 0, 0], 'trash'), VoidBox([1, 0, 0], 'collisionRect'), VoidBox([1, 0, 0], 'trash'), VoidBox([0, -2, 0], 'trash', True)]  # make the summoner void boxes also trash cans
        if imports:
            self.importData()

    def importData(self):
        f = open('exportData', 'r')
        data = f.read().splitlines()
        formattedData = []  # formattedData = [points, joints, collisionRects]
        f.close()
        for pjc in data:
            if (pjc == 'POINTS') or (pjc == 'JOINTS') or (pjc == 'COLLISIONRECTS'):
                formattedData.append([])
            else:
                formattedData[-1].append(pjc)  # .replace(' |', ', ')
                formattedData[-1][-1] = formattedData[-1][-1].split(' | ')
        for i in range(len(formattedData)):
            for j in range(len(formattedData[i])):
                for k in range(len(formattedData[i][j])):
                    if (formattedData[i][j][k] != 's') and (formattedData[i][j][k] != 'l'):
                        try:
                            if i == 1:
                                formattedData[i][j][k] = int(formattedData[i][j][k])  # should be int for joints since list indexes cannot be floats
                            else:
                                formattedData[i][j][k] = float(formattedData[i][j][k])
                        except ValueError:
                            formattedData[i][j][k] = formattedData[i][j][k].replace('[', '')
                            formattedData[i][j][k] = formattedData[i][j][k].replace(']', '')
                            tempList = formattedData[i][j][k].split(', ')
                            for t in range(len(tempList)):
                                tempList[t] = float(tempList[t])
                            formattedData[i][j][k] = tempList
        points = formattedData[0]
        joints = formattedData[1]
        collisionRects = formattedData[2]
        print(collisionRects)
        for p in points:
            self.addPoint(p[0], p[1])
            self.points[-1].density = p[2]
        for j in joints:
            self.joints.append(Joint(j[0], j[1]))
        for c in collisionRects:
            self.addCollisionRect(CollisionRect(c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7]))

    def importTutorials(self):
        # global tutorialNames
        f = open('tutorialTexts', 'r')
        tutors = f.read().splitlines()
        tNames = []
        tTexts = []
        for l in tutors:
            if l.find('---') != -1:
                tTexts.append([])
                tempList = list(l)
                for _ in range(3):
                    tempList.pop(0)
                tempStr = ''
                for c in tempList:
                    tempStr = f'{tempStr}{c}'
                tNames.append(tempStr)
            else:
                tTexts[-1].append(l)
        for t in range(len(tNames)):
            tNames[t] = tNames[t].replace('newLine', '\n')  # solution from Python Discord, credit goes to lordtyrionlannister "Saul Goodman"
            self.tutorialTexts.update({tNames[t]: tTexts[t]})  # update local information about the tutorial
            tutorialNames.update({tNames[t]: None})  # update the global value of tutorialNames for use in myGUI.GUISelector
            self.GUI['Tutorials'][''].update({tNames[t]: None})  # update local value of tutorials in self.GUI
        f.close()
        self.GUI['Tutorials']['']['Introduction'] = myGUI.Tutorial([0, 2, 4], [10, 0.2], self.tutorialTexts['Introduction'], [], 0.3, [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])

    def getButtonReleased(self, cIdx):
        for b in self.buttonHeld:
            if not buttonPressed(b, controlsConf.controllers[cIdx], cIdx):
                self.buttonHeld[b][cIdx] = False

    def addPoint(self, cords, radius, *cIdx):
        self.points.append(Point(cords, radius))
        self.GUI.update({len(self.points) + 999: {'slider': {'radius': None, 'density': None}, 'manual': {'radius': None, 'density': None}}})
        if cIdx:
            self.lastP[cIdx[0]] = len(self.points) - 1

    def addCollisionRect(self, cRect):
        self.collisionRect.append(cRect)
        self.GUI.update({len(self.collisionRect) - 1: {'dial': {'XZ': None, 'XY': None, 'YZ': None, '3D': None, 'density': None, 'angle': None, 'viscosity': None}, 'slider': {0: None, 1: None, 2: None, 'density': None, 'angle': None, 'viscosity': None}, 'manual': {0: None, 1: None, 2: None, 'density': None, 'angle': None, 'viscosity': None}}})

    def main(self):
        self.timer += 1 / calcRate
        if self.timer > 290:  # exit after ~4.83 minutes
            print("Timer's up on the free license!")
            self.export()
        for c in range(controlsConf.controllerAmt):
            self.getButtonReleased(c)
            # summon the GUI selector if the 'GUISelector' button is pressed
            if (not self.buttonHeld['GUISelector'][c]) and buttonPressed('GUISelector', controlsConf.controllers[c], c):
                self.buttonHeld['GUISelector'][c] = True
                if self.GUI['GUISelector']['']['main'] is None:
                    self.GUI['GUISelector']['']['main'] = myGUI.GUISelector(spriteCreatorVars, controls.hand[c].cords, [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                else:
                    self.GUI['GUISelector']['']['main'].drawn = False
                    self.GUI['GUISelector']['']['main'].unDraw()

        for v in self.voidBox:
            v.drag()

        self.dragPoint()

    def dragPoint(self):
        # print(self.lastP)
        # if mode == 'vr':
        #     print(controlsConf.controllers[0].getButtonState() % touchpad, controlsConf.controllers[1].getButtonState() % touchpad)  # prints the current button being pressed for each controller
        # loop through all drag code for each controller
        colliding = False
        for c in range(controlsConf.controllerAmt):
            if self.clickTime[c] <= 0.25:
                self.clickTime[c] += 1 / calcRate
            if self.jClickTime[c] <= 0.25:
                self.jClickTime[c] += 1 / calcRate
            for g in self.GUI:
                for gu in self.GUI[g]:
                    for gui in self.GUI[g][gu]:
                        if self.GUI[g][gu][gui] is not None:
                            self.GUI[g][gu][gui].drag(c, selectP(c))
            for p in range(len(self.points)):
                if self.points[p].drawn:
                    if detectCollision(self.points[p].radius, controls.hand[c].radius, self.points[p].cords, controls.hand[c].cords) and (self.dragR[c] is None):
                        self.points[p].collidingController[c] = True
                        self.collP[c] = p  # set the collision point to the current point's index
                        if selectP(c):  # detect if the select button is being pressed, depending on the controller mode
                            if not self.buttonHeld['select'][c]:
                                self.buttonHeld['select'][c] = True
                                for axis in range(3):
                                    self.relPos[c][axis] = self.points[p].cords[axis] - controls.hand[c].cords[axis]
                                cords = controls.hand[c].cords  # set cords to the current controller's cords to shorten the below for increased readability
                                if self.clickTime[c] < 0.25:  # if there's a double click, summon sliders (if in VR) or manual inputs (if in keyboard/mouse) to change the density and radius of the double-clicked point
                                    if self.GUI[p + 1000]['slider']['radius'] is None:  # only summon if GUI is empty
                                        if mode == 'vr':
                                            self.GUI[p + 1000]['slider']['radius'] = myGUI.Slider(0, self.points[p].radius, self.points[p].origRadius, [cords[0], cords[1] + 0.5, cords[2]], 10, 0.1, maxRadius, minRadius, 'Radius', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                                        else:
                                            self.GUI[p + 1000]['slider']['radius'] = myGUI.Manual(0, self.points[p].radius, self.points[p].origRadius, [cords[0], cords[1] + 0.5, cords[2]], 'Radius', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                                    else:
                                        self.GUI[p + 1000]['slider']['radius'].unDraw()
                                        self.GUI[p + 1000]['slider']['radius'] = None
                                    if self.GUI[p + 1000]['slider']['density'] is None:  # only summon if GUI is empty
                                        if mode == 'vr':
                                            self.GUI[p + 1000]['slider']['density'] = myGUI.Slider(0, self.points[p].density, self.points[p].origDensity, [cords[0], cords[1] - 0.5, cords[2]], 10, 0.1, 10000, 1, 'Density', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                                            self.GUI[p + 1000]['slider']['density'].closeButton.unDraw()  # only one 'X' needs to be rendered, since there are two Xs within each other
                                            self.GUI[p + 1000]['slider']['density'].closeButton.cords[1] = cords[1] + 1  # offset this 'X' to be within the other 'X' so that they both act as one button to dismiss both radius and density GUIs simultaneously
                                        else:
                                            self.GUI[p + 1000]['slider']['density'] = myGUI.Manual(0, self.points[p].density, self.points[p].origDensity, [cords[0], cords[1] - 0.5, cords[2]], 'Density', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                                    else:
                                        self.GUI[p + 1000]['slider']['density'].unDraw()
                                        self.GUI[p + 1000]['slider']['density'] = None
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
                        self.points[p].collidingController[c] = False

                if buttonPressed('dragJoint', controlsConf.controllers[c], c):
                    collision = detectCollision(self.points[p].radius, controls.hand[c].radius, self.points[p].cords, controls.hand[c].cords)
                    colliding = colliding or collision
                    if (not self.buttonHeld['dragJoint'][c]) and collision:
                        self.buttonHeld['dragJoint'][c] = True
                        if self.jClickTime[c] < 0.25:
                            self.removeConnectedJoints(p)
                        else:
                            self.jClickTime[c] = 0
                            if self.newJoint is None:
                                self.newJoint = Joint(p, c, 'controls')
                            elif self.newJoint.pOne != p:  # if the point is not the current point, to prevent both points in a joint from being the exact same
                                self.newJoint.pTwo = p
                                self.newJoint.controller = False
                                self.joints.append(self.newJoint)
                                self.newJoint = None

                if buttonPressed('undoJoint', controlsConf.controllers[c], c):
                    if not self.buttonHeld['undoJoint'][c]:
                        self.buttonHeld['undoJoint'][c] = True
                        self.joints[-1].unDraw()
                        self.joints.pop(-1)  # popping allowed here since it's the end of the list

            for cr in range(len(self.collisionRect)):
                if self.collisionRect[cr].drawn:
                    yCollisionPlane = getYCollisionPlane(self.collisionRect[cr], controls.hand[c].cords)
                    if getCubeCollision(controls.hand[c].cords, controls.hand[c].radius, self.collisionRect[cr], yCollisionPlane) and (self.dragP[c] is None):
                        self.collisionRect[cr].collidingController[c] = True
                        if selectP(c):
                            self.lastR[c] = cr
                            if not self.buttonHeld['select'][c]:
                                self.buttonHeld['select'][c] = True
                                for axis in range(3):
                                    self.relPos[c][axis] = self.collisionRect[cr].cords[axis] - controls.hand[c].cords[axis]
                                if self.clickTime[c] < 0.25:  # if there's a double click, summon sliders (if in VR) or manual inputs (if in keyboard/mouse) to change the size and density of the double-clicked collision rect
                                    if self.GUI['GUISelector']['']['pointRect'] is None:
                                        self.GUI['GUISelector']['']['pointRect'] = myGUI.GUISelector({'Size': None, 'Solid/\nLiquid': None}, [controls.hand[c].cords[0], controls.hand[c].cords[1] - 1, controls.hand[c].cords[2]], [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]], cr)
                                    else:
                                        self.GUI['GUISelector']['']['pointRect'].drawn = False
                                        self.GUI['GUISelector']['']['pointRect'].unDraw()
                                else:
                                    self.clickTime[c] = 0  # reset the time since last click, since this click IS the last click!
                            if self.dragR[c] is None:  # used to set the drag variables if they are not already set
                                self.dragR[c] = cr
                        else:
                            self.buttonHeld['select'][c] = False
                    else:
                        self.collisionRect[cr].collidingController[c] = False
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
                if self.lastP[c] is not None:
                    self.points[self.lastP[c]].cords = copy.deepcopy(controls.hand[c].cords)
            # remove the force joint after recall is no longer active
            elif self.theForceJoint:
                if self.joints[-1].show:
                    self.joints[-1].cylinder.remove()
                self.joints.pop(-1)
                self.theForceJoint = False

            if buttonPressed('dragJoint', controlsConf.controllers[c], c) and (self.newJoint is not None) and (not colliding):
                self.newJoint.unDraw()
                self.newJoint = None

    def removeConnectedJoints(self, pIdx):
        for j in self.joints:
            if (j.pOne == pIdx) or (j.pTwo == pIdx):
                j.unDraw()

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
                                elif gta == 'viscosity':
                                    self.GUI[g][gt][gta].setVar(self.collisionRect[pcIdx].viscosity)
                                    self.collisionRect[pcIdx].viscosity = self.GUI[g][gt][gta].main()
                                elif (gta == 'XZ') or (gta == 'XY') or (gta == 'YZ') or (gta == '3D'):
                                    self.GUI[g][gt][gta].setVar(self.collisionRect[pcIdx].size)
                                    size = self.GUI[g][gt][gta].main()  # must be done AFTER setVar (for complex reasons)
                                    for axis in self.GUI[g][gt][gta].axes:
                                        self.collisionRect[pcIdx].setVars(self.collisionRect[pcIdx].cords, size[axis], axis)
                                elif g == 'Tutorials':
                                    self.GUI[g][gt][gta].main()
                                else:
                                    self.GUI[g][gt][gta].setVar(self.collisionRect[pcIdx].size[self.GUI[g][gt][gta].xyz])
                                    size = self.GUI[g][gt][gta].main()  # must be done AFTER setVar (for complex reasons)
                                    self.collisionRect[pcIdx].setVars(self.collisionRect[pcIdx].cords, size, self.GUI[g][gt][gta].xyz)
                        else:
                            self.GUI[g][gt][gta] = None

        if self.GUIType is not None:
            print(self.GUIType)
            if self.GUIType[0] == 'Tutorials':
                if self.GUI[self.GUIType[0]][''][self.GUIType[1][0]] is not None:
                    self.GUI[self.GUIType[0]][''][self.GUIType[1][0]].unDraw()
                    self.GUI[self.GUIType[0]][''][self.GUIType[1][0]] = None
                self.GUI[self.GUIType[0]][''][self.GUIType[1][0]] = myGUI.Tutorial(controls.hand[0].cords, [10, 0.2], self.tutorialTexts[self.GUIType[1][0]], [], 0.3, [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
            elif self.GUIType[0] == 'Save & Exit':
                self.export()
            elif self.GUIType[0] == 'Solid/\nLiquid':
                if self.GUIType[1][0] == 'Solid':
                    self.collisionRect[self.GUIType[3][0]].rectType = 's'
                elif self.GUIType[1][0] == 'Liquid':
                    self.collisionRect[self.GUIType[3][0]].rectType = 'l'
            elif self.GUIType[0] == 'Size':
                resetDicts = ['density', 'angle', 'viscosity']  # dictionary values to reset, no matter the GUI summoned
                for r in resetDicts:
                    if self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][r] is not None:
                        self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][r].unDraw()
                        self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][r] = None
                if self.GUIType[1][0] == 'Slider':
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['density'] = myGUI.Slider(0, self.collisionRect[self.GUIType[3][0]].density, 1000, [controls.hand[0].cords[0] + 2.5, controls.hand[0].cords[1] - 1, controls.hand[0].cords[2]], 5, 0.15, 50000, 10, 'Density', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['angle'] = myGUI.Slider(0, self.collisionRect[self.GUIType[3][0]].angle[2], 0.00001, [controls.hand[0].cords[0] + 2.5, controls.hand[0].cords[1] - 2, controls.hand[0].cords[2]], 5, 0.15, 89.99999, 0.00001, 'Angle', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['viscosity'] = myGUI.Slider(0, self.collisionRect[self.GUIType[3][0]].viscosity, 1, [controls.hand[0].cords[0] + 2.5, controls.hand[0].cords[1] - 3, controls.hand[0].cords[2]], 5, 0.15, 20, 0, 'Viscosity', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                    closeButtonCords = self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['density'].closeButton.cords
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['angle'].closeButton.setPos(closeButtonCords, True)
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['viscosity'].closeButton.setPos(closeButtonCords, True)
                    for axis in range(3):
                        self.collisionRect[self.GUIType[3][0]].size[axis] += self.collisionRect[self.GUIType[3][0]].sizeOffset[axis]
                    self.collisionRect[self.GUIType[3][0]].sizeOffset = [0, 0, 0]
                    size = 25
                    for axis in range(3):
                        if self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis] is not None:
                            self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis].unDraw()
                            self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis] = None
                        cords = copy.deepcopy(controls.hand[0].cords)
                        cords[axis] += 0.5 + size / 2
                        self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis] = myGUI.Slider(axis, self.collisionRect[self.GUIType[3][0]].size[axis], 1, cords, size, 0.15, 100, 0.1, f'Size {axis}', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                        self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis].closeButton.setPos(closeButtonCords, True)
                elif self.GUIType[1][0] == 'Manual':
                    for axis in range(3):
                        self.collisionRect[self.GUIType[3][0]].size[axis] += self.collisionRect[self.GUIType[3][0]].sizeOffset[axis]
                    self.collisionRect[self.GUIType[3][0]].sizeOffset = [0, 0, 0]
                    for axis in range(3):
                        if self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis] is not None:
                            self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis].unDraw()
                            self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis] = None
                        cords = copy.deepcopy(controls.hand[0].cords)
                        if mode == 'vr':
                            cords[0] += axis * 3.5
                            yDisp = -6.5
                            xDisp = 3.5
                        else:  # keyboard/mouse manual inputs are much tinier compared to VR manual inputs!
                            cords[0] += axis * 0.5
                            yDisp = -0.5
                            xDisp = 0.5
                        self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis] = myGUI.Manual(axis, self.collisionRect[self.GUIType[3][0]].size[axis], 1, cords, f'Size {axis}', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]], False)
                        if mode == 'vr':
                            closeButtonCords = self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][0].closeButton.cords
                            if axis != 0:  # don't prevent the only closeButton remaining from being removed!
                                self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][axis].closeButton.setPos(closeButtonCords, True)
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['density'] = myGUI.Manual(0, self.collisionRect[self.GUIType[3][0]].density, 1000, [controls.hand[0].cords[0], controls.hand[0].cords[1] + yDisp, controls.hand[0].cords[2]], 'Density', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]], False)
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['angle'] = myGUI.Manual(0, self.collisionRect[self.GUIType[3][0]].angle[2], 0.00001, [controls.hand[0].cords[0] + xDisp, controls.hand[0].cords[1] + yDisp, controls.hand[0].cords[2]], 'Angle', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]], False)
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['viscosity'] = myGUI.Manual(0, self.collisionRect[self.GUIType[3][0]].viscosity, 1, [controls.hand[0].cords[0] + xDisp * 2, controls.hand[0].cords[1] + yDisp, controls.hand[0].cords[2]], 'Viscosity', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]], False)

                    if mode == 'vr':
                        for g in resetDicts:
                            self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][g].closeButton.setPos(closeButtonCords, True)

                elif self.GUIType[1][0] == 'Dial':
                    if self.collisionRect[self.GUIType[3][0]].sizeOffset == [0, 0, 0]:
                        self.collisionRect[self.GUIType[3][0]].sizeOffset = [11, 11, 11]
                        for axis in range(3):
                            self.collisionRect[self.GUIType[3][0]].size[axis] -= self.collisionRect[self.GUIType[3][0]].sizeOffset[axis]
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
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['density'] = myGUI.Slider(0, self.collisionRect[self.GUIType[3][0]].density, 1000, [controls.hand[0].cords[0], controls.hand[0].cords[1] + 1, controls.hand[0].cords[2] - cRad - 0.2], 5, 0.15, 50000, 10, 'Density', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['angle'] = myGUI.Slider(0, self.collisionRect[self.GUIType[3][0]].angle[2], 0.00001, [controls.hand[0].cords[0], controls.hand[0].cords[1], controls.hand[0].cords[2] - cRad - 0.2], 5, 0.15, 89.99999, 0.00001, 'Angle', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                    self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()]['viscosity'] = myGUI.Slider(0, self.collisionRect[self.GUIType[3][0]].viscosity, 1, [controls.hand[0].cords[0], controls.hand[0].cords[1] - 1, controls.hand[0].cords[2] - cRad - 0.2], 5, 0.15, 20, 0, 'Viscosity', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                    for g in resetDicts:
                        self.GUI[self.GUIType[3][0]][self.GUIType[1][0].lower()][g].closeButton.setPos(closeButtonCords, True)

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
        if self.newJoint is not None:
            self.newJoint.draw()
        for g in self.GUI:
            for gu in self.GUI[g]:
                for gui in self.GUI[g][gu]:
                    if self.GUI[g][gu][gui] is not None:
                        self.GUI[g][gu][gui].draw(controls.camCords)
        for c in self.collisionRect:
            c.draw()

    def export(self):
        # format:
        # POINTS
        # cords, radius, density
        # JOINTS
        # pOneIdx, pTwoIdx
        # COLLISIONRECTS
        # size, cords, angle, density, viscosity, dragConst, transparency, rectType
        f = open('exportData', 'w')
        f.write('POINTS\n')
        for p in self.points:
            if p.drawn:
                f.write(f'{p.cords} | {p.radius} | {p.density}\n')
        f.write('JOINTS\n')
        for j in self.joints:
            if j.drawn:
                f.write(f'{j.pOne} | {j.pTwo}\n')
        f.write('COLLISIONRECTS\n')
        for c in self.collisionRect:
            if c.drawn:
                f.write(f'{[c.size[0] + c.sizeOffset[0], c.size[1] + c.sizeOffset[1], c.size[2] + c.sizeOffset[2]]} | {c.cords} | {c.angle} | {c.density} | {c.viscosity} | {c.dragConst} | {c.transparency} | {c.rectType}\n')
        f.close()
        viz.quit()
        print('Your progress has been saved in exportData!')


class Point:
    def __init__(self, cords, radius):
        self.drawn = True
        self.cords = copy.deepcopy(cords)
        self.radius = radius
        self.origRadius = radius
        self.density = 1000
        self.origDensity = 1000
        self.point = vizshape.addSphere()
        self.setRadiusDensity(self.radius, self.density)
        self.cloth = ''
        self.collidingController = [False, False]

    def setRadiusDensity(self, radius, density):
        self.radius = radius
        self.density = density
        self.point.setScale([self.radius, self.radius, self.radius])

    def main(self):
        pass

    def draw(self):
        if self.drawn:
            self.point.setPosition(self.cords)

    def unDraw(self):
        self.point.remove()
        self.drawn = False


class CollisionRect:
    def __init__(self, size, cords, angle, density, viscosity, dragConst, transparency, rectType, *hide):
        self.drawn = True
        self.rectType = rectType  # solid or liquid
        self.angle = angle
        self.vertexAngle = [0, 0, 0]
        self.size = size
        self.origSize = size
        self.show = False
        if not hide:
            self.show = True
            self.rect = vizshape.addBox([1, 1, 1])
            self.rect.setScale(self.size)
        self.cords = copy.deepcopy(cords)
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
        self.sizeOffset = [0, 0, 0]
        self.collidingController = [False, False]
        self.update()

    def update(self):
        if self.drawn:
            tempSize = [self.size[0] + self.sizeOffset[0], self.size[1] + self.sizeOffset[1], self.size[2] + self.sizeOffset[2]]
            for t in range(3):
                if tempSize[t] <= 0:
                    tempSize[t] = 0.1
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
        if self.show and self.drawn:
            if self.rectType == 's':
                self.transparency = 0.8
            elif self.rectType == 'l':
                self.transparency = 0.5
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

    def unDraw(self):
        self.rect.remove()
        self.drawn = False


class Joint:
    def __init__(self, pOneIdx, pTwoIdx, *controller):
        self.drawn = True
        self.pOne = pOneIdx
        self.pTwo = pTwoIdx
        if controller:
            self.controller = True
        else:
            self.controller = False
        self.height = 1
        self.radius = jointRadius
        self.cords = [0, 0, 0]
        self.cylinder = vizshape.addCylinder(1, 1, slices=jointResolution)

    def draw(self):
        if self.drawn:
            if not self.controller:
                self.height = distance(game.points[self.pOne].cords, game.points[self.pTwo].cords)
                self.cylinder.setScale([self.radius, self.height, self.radius])  # change visual of cylinder
                self.cords = midpoint(game.points[self.pOne], game.points[self.pTwo])
                self.cylinder.setEuler(getEulerAngle(game.points[self.pOne].cords, game.points[self.pTwo].cords))
            else:
                self.height = distance(game.points[self.pOne].cords, controls.hand[self.pTwo].cords)
                self.cylinder.setScale([self.radius, self.height, self.radius])  # change visual of cylinder
                self.cords = midpoint(game.points[self.pOne], controls.hand[self.pTwo])
                self.cylinder.setEuler(getEulerAngle(game.points[self.pOne].cords, controls.hand[self.pTwo].cords))

            self.cylinder.setPosition(self.cords)

    def unDraw(self):
        self.cylinder.remove()
        self.drawn = False


class VoidBox:
    def __init__(self, cords, spriteType, *display):
        self.cords = cords
        self.box = vizshape.addBox()
        self.box.setPosition(self.cords)
        self.box.alpha(0.25)
        self.innerShape = None
        self.spriteType = spriteType
        self.collisionRad = 0.25
        self.text = viz.addText3D('', fontSize=0.1)
        self.text.setPosition([self.cords[0] - 0.2, self.cords[1] + 0.55, self.cords[2]])
        if self.spriteType == 'collisionRect':
            self.innerShape = vizshape.addBox()
            self.innerShape.setScale([0.5, 0.5, 0.5])
            self.text.message('Collision Box')
        elif self.spriteType == 'point':
            self.innerShape = vizshape.addSphere()
            self.innerShape.setScale([0.25, 0.25, 0.25])
            self.text.message('Point')
        elif self.spriteType == 'trash' and display:
            self.text.message('Trash Can')
            self.collisionRad = 0.5
        if self.spriteType != 'trash':
            self.innerShape.setPosition(self.cords)
        self.pHeld = [False, False]

    def drag(self):
        for c in range(controlsConf.controllerAmt):
            collision = detectCollision(controls.hand[c].radius, self.collisionRad, controls.hand[c].cords, self.cords)
            if selectP(c):
                if not self.pHeld[c]:
                    self.pHeld[c] = True
                    if collision:
                        if self.spriteType == 'point':
                            game.addPoint(self.cords, 0.1, c)
                        elif self.spriteType == 'collisionRect':
                            game.addCollisionRect(CollisionRect([0.25, 0.25, 0.25], self.cords, [0, 0, math.radians(0.0001)], 1000, 1, 1, 1, 's'))
            elif self.spriteType == 'trash':
                if collision:
                    if game.lastP[c] is not None:
                        if game.points[game.lastP[c]].collidingController[c]:
                            game.removeConnectedJoints(game.lastP[c])
                            game.points[game.lastP[c]].unDraw()
                            game.points.pop(game.lastP[c])
                            game.lastP[c] = None
                            game.dragP[c] = None
                            game.collP[c] = None
                            for j in range(len(game.joints)):
                                if game.joints[j].pOne >= game.lastP[c]:
                                    game.joints[j].pOne -= 1
                                if game.joints[j].pTwo >= game.lastP[c]:
                                    game.joints[j].pTwo -= 1
                    if (game.lastR[c] is not None) and game.collisionRect[game.lastR[c]].collidingController[c]:
                        game.collisionRect[game.lastR[c]].unDraw()
            else:
                self.pHeld[c] = False


game = Main()

vizact.ontimer(1 / calcRate, game.main)
vizact.ontimer(1 / renderRate, game.render)
