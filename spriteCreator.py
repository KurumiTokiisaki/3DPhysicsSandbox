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

# 'l/rControllerObj' are constants used for interacting with GUIs by passing these into classes in myGUI whenever GUIs are summoned
lControllerObj = [controlsConf.controllers[0], controls.hand[0]]
rControllerObj = [controlsConf.controllers[1], controls.hand[1]]


def selectP(cIdx):
    return buttonPressed('select', controlsConf.controllers[cIdx], cIdx)


def getYCollisionPlane(b, cords):
    return {
        'left': {'y': (b.grad['y'] * cords[0]) + (b.vertex[1][1] - (b.grad['y'] * b.vertex[1][0])), 'm': b.grad['y'], 'c': b.vertex[1][1] - (b.grad['y'] * b.vertex[1][0])},
        'right': {'y': (b.grad['y'] * cords[0]) + (b.vertex[0][1] - (b.grad['y'] * b.vertex[0][0])), 'm': b.grad['y'], 'c': b.vertex[0][1] - (b.grad['y'] * b.vertex[0][0])},
        'top': {'y': (b.grad['x'] * cords[0]) + (b.vertex[1][1] - (b.grad['x'] * b.vertex[1][0])), 'm': b.grad['x'], 'c': b.vertex[1][1] - (b.grad['x'] * b.vertex[1][0])},
        'bottom': {'y': (b.grad['x'] * cords[0]) + (b.vertex[7][1] - (b.grad['x'] * b.vertex[7][0])), 'm': b.grad['x'], 'c': b.vertex[7][1] - (b.grad['x'] * b.vertex[7][0])},
    }


def getXCollisionPlane(b, cords):
    return {
        'left': {'x': - (b.grad['x'] * cords[1]) + (b.vertex[1][0] + (b.grad['x'] * b.vertex[1][1])), 'm': -b.grad['x'], 'c': b.vertex[1][0] + (b.grad['x'] * b.vertex[1][1])},
        'right': {'x': - (b.grad['x'] * cords[1]) + (b.vertex[0][0] + (b.grad['x'] * b.vertex[0][1])), 'm': -b.grad['x'], 'c': b.vertex[0][0] + (b.grad['x'] * b.vertex[0][1])},
        'top': {'x': - (b.grad['y'] * cords[1]) + (b.vertex[1][0] + (b.grad['y'] * b.vertex[1][1])), 'm': -b.grad['y'], 'c': b.vertex[1][0] + (b.grad['y'] * b.vertex[1][1])},
        'bottom': {'x': - (b.grad['y'] * cords[1]) + (b.vertex[7][0] + (b.grad['y'] * b.vertex[7][1])), 'm': -b.grad['y'], 'c': b.vertex[7][0] + (b.grad['y'] * b.vertex[7][1])}
    }


def getCubeCollision(cords, radius, b, yCollisionPlane):
    return (cords[1] <= (collisionTolerance + yCollisionPlane['top']['y'] + radius / cos(b.angle[2]))) and (cords[1] >= (-collisionTolerance + yCollisionPlane['bottom']['y'] - radius / cos(b.angle[2]))) and (cords[1] <= (collisionTolerance + yCollisionPlane['right']['y'] + radius / sin(b.angle[2]))) and (
            cords[1] >= (-collisionTolerance + yCollisionPlane['left']['y'] - radius / sin(b.angle[2]))) and (cords[2] <= (collisionTolerance + b.plane['front'] + radius)) and (cords[2] >= (-collisionTolerance + b.plane['back'] - radius))


def getSliderManual(xyz, referenceVar, globalDefaultVar, cords, length, maxi, mini, text):
    if mode == 'vr':
        return myGUI.Slider(xyz, referenceVar, globalDefaultVar, cords, length, maxi, mini, text, lControllerObj, rControllerObj)
    elif mode == 'k':
        return myGUI.Manual(xyz, referenceVar, globalDefaultVar, cords, text, lControllerObj, rControllerObj)


class Main:
    def __init__(self) -> None:
        self.__timer = 0  # stores how long the program is being run for so that it can save & exit before the 5-minute limit from the free Vizard license
        self.points = []  # points list for the entire program
        self.joints = []  # joints list for the entire program
        self.collisionRect = []  # list of collisionRects
        self.dragP = [None, None]  # last clicked point index
        self.lastP = [None, None]  # last clicked point that always retains its value for "recalling" objects to the controller
        self.lastR = [None, None]
        self.dragR = [None, None]  # last clicked controller index for the last clicked collisionRect
        self.collP = [None, None]  # stores the indexes of a point that is colliding with either controller
        self.pause = False  # pauses physics
        self.__buttonHeld = {}
        for c in config.controls:
            self.__buttonHeld.update({c: [False, False]})  # stores if the button 'c' is being held on either controller
        self.__animeScale = [1, 1]  # visual scale of animations
        self.__animeScaleSpeed = 0  # rate at which animations scale
        self.__animeColor = [[0, 0, 0], [0, 0, 0]]  # color of each animation
        self.__GUIType = None  # holds the return value of GUISelector to create relevant GUI(s)
        self.__clickTime = [0, 0]  # stores time since 'select' was pressed for both controllers in order for double-click detection
        self.__jClickTime = [0, 0]  # stores time since 'j' was pressed for both controllers in order for double-click detection
        self.__relPos = [[0, 0, 0], [0, 0, 0]]  # stores the relative position of selected points with either controller
        self.__GUI = {
            'GUISelector': {'': {'main': None, 'pointRect': None}},
            'Tutorials': {'': {}}
        }
        self.__newJoint = None
        self.__tutorialTexts = {}
        self.__importTutorials()  # works the same way as '__importTutorials' from sandbox.py
        self.__voidBox = [VoidBox([-1, 0, 0], 'point'), VoidBox([-1, 0, 0], 'trash'), VoidBox([1, 0, 0], 'collisionRect'), VoidBox([1, 0, 0], 'trash'), VoidBox([0, -2, 0], 'trash', True)]  # make the void boxes used to summon points and joints also into trash cans
        # if the user typed 'y', import from exportData
        if imports:
            self.__importData()  # works the same way as '__importData()' from sandbox.py

    # used to read the contents of exportData to allow the user to import their own creations from spriteCreator.py
    def __importData(self) -> None:
        f = open('exportData', 'r')
        data = f.read().splitlines()
        formattedData = []  # formattedData = [points, joints, collisionRects]
        f.close()
        for pjc in data:
            if (pjc == 'POINTS') or (pjc == 'JOINTS') or (pjc == 'COLLISIONRECTS'):
                formattedData.append([])
            else:
                formattedData[-1].append(pjc)
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
        for p in points:
            self.addPoint(p[0], p[1])
            self.points[-1].density = p[2]
        for j in joints:
            self.joints.append(Joint(j[0], j[1]))
        for c in collisionRects:
            self.addCollisionRect(CollisionRect(c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7]))

    # used to import tutorials from 'tutorialTexts.txt'
    def __importTutorials(self):
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
            self.__tutorialTexts.update({tNames[t]: tTexts[t]})  # update local information about the tutorial
            tutorialNames.update({tNames[t]: None})  # update the global value of tutorialNames for use in myGUI.GUISelector
            self.__GUI['Tutorials'][''].update({tNames[t]: None})  # update local value of tutorials in self.GUI
        f.close()
        if not imports:
            self.__GUI['Tutorials']['']['Introduction'] = myGUI.Tutorial([0, 2, 4], [10, 0.2], self.__tutorialTexts['Introduction'], [], 0.3, lControllerObj, rControllerObj)

    def __getButtonReleased(self, cIdx):
        for b in self.__buttonHeld:
            if not buttonPressed(b, controlsConf.controllers[cIdx], cIdx):
                self.__buttonHeld[b][cIdx] = False

    def addCollisionRect(self, cRect: object) -> None:
        self.collisionRect.append(cRect)
        # set all collisionRect keys to their index positions, so they can easily be referenced
        self.__GUI.update({len(self.collisionRect) - 1: {'dial': {'XZ': None, 'XY': None, 'YZ': None, '3D': None, 'density': None, 'angle': None, 'viscosity': None}, 'slider': {0: None, 1: None, 2: None, 'density': None, 'angle': None, 'viscosity': None}, 'manual': {0: None, 1: None, 2: None, 'density': None, 'angle': None, 'viscosity': None}}})

    def addPoint(self, cords: list, radius: float, *cIdx: list) -> None:
        self.points.append(Point(cords, radius))
        # displace all points' keys by 1000 index spaces so that they don't map to collisionRect indexes
        self.__GUI.update({len(self.points) + 999: {'slider': {'radius': None, 'density': None}, 'manual': {'radius': None, 'density': None}}})
        if cIdx:
            self.lastP[cIdx[0]] = len(self.points) - 1

    def main(self) -> None:
        self.__timer += 1 / calcRate
        if self.__timer > 290:  # exit after ~4.83 minutes
            print("5-minute timer's up on the free license!")
            self.__export()
        for c in range(controlsConf.controllerAmt):
            self.__getButtonReleased(c)
            # summon the GUI selector if the 'GUISelector' button is pressed
            if (not self.__buttonHeld['GUISelector'][c]) and buttonPressed('GUISelector', controlsConf.controllers[c], c):
                self.__buttonHeld['GUISelector'][c] = True
                if self.__GUI['GUISelector']['']['main'] is None:
                    self.__GUI['GUISelector']['']['main'] = myGUI.GUISelector(spriteCreatorVars, controls.hand[c].cords, lControllerObj, rControllerObj)
                else:
                    self.__GUI['GUISelector']['']['main'].drawn = False
                    self.__GUI['GUISelector']['']['main'].unDraw()

        # detect for hand<>void box interactions
        for v in self.__voidBox:
            v.drag()

        self.__dragPoint()  # detect hand<>object interactions

    def __dragPoint(self) -> None:
        # if mode == 'vr':
        #     print(controlsConf.controllers[0].getButtonState() % touchpad, controlsConf.controllers[1].getButtonState() % touchpad)  # prints the current button being pressed for each controller
        colliding = False  # True if there is ANY hand<>point/collisionRect collision
        for c in range(controlsConf.controllerAmt):
            if self.__clickTime[c] <= 0.25:
                self.__clickTime[c] += 1 / calcRate
            if self.__jClickTime[c] <= 0.25:
                self.__jClickTime[c] += 1 / calcRate
            for g in self.__GUI:
                for gu in self.__GUI[g]:
                    for gui in self.__GUI[g][gu]:
                        if self.__GUI[g][gu][gui] is not None:
                            self.__GUI[g][gu][gui].drag(c, selectP(c))  # detect for hand<>GUI interactions

            # hand<>point dragging
            for p in range(len(self.points)):
                if self.points[p].drawn:
                    if detectPointCollision(self.points[p].radius, controls.hand[c].radius, self.points[p].cords, controls.hand[c].cords) and (self.dragR[c] is None):
                        self.points[p].collidingController[c] = True
                        self.collP[c] = p  # set the collision point to the current point's index
                        if selectP(c):  # detect if the select button is being pressed, depending on the controller mode
                            if not self.__buttonHeld['select'][c]:
                                self.__buttonHeld['select'][c] = True
                                for axis in range(3):
                                    self.__relPos[c][axis] = self.points[p].cords[axis] - controls.hand[c].cords[axis]
                                if self.__clickTime[c] < 0.25:  # if there's a double click, summon sliders (if in VR) or manual inputs (if in keyboard/mouse) to change the density and radius of the double-clicked point
                                    self.__setRadiusDensityGUI(controls.hand[c].cords, p)
                                else:
                                    self.__clickTime[c] = 0  # reset the time since last click, since this click IS the last click!
                            if self.dragP[c] is None:  # used to set the drag variables if they are not already set
                                self.dragP[c] = p
                                if self.lastP[c] != p:  # no need to run the below if the value of lastP won't change
                                    if mode == 'vr':
                                        if self.lastP[c - 1] != p:  # prevents both controllers from recalling the same point
                                            self.lastP[c] = p
                                    else:
                                        self.lastP[c] = p
                    else:
                        self.points[p].collidingController[c] = False

                # make joints when either hand is colliding with a joint
                if buttonPressed('dragJoint', controlsConf.controllers[c], c):
                    collision = detectPointCollision(self.points[p].radius, controls.hand[c].radius, self.points[p].cords, controls.hand[c].cords)
                    colliding = colliding or collision
                    if (not self.__buttonHeld['dragJoint'][c]) and collision:  # if either hand is colliding with a point, make a joint
                        self.__buttonHeld['dragJoint'][c] = True
                        if self.__jClickTime[c] < 0.25:
                            self.removeConnectedJoints(p)  # remove all joints connected to the colliding point if 'dragJoint' is double-clicked
                        else:
                            self.__jClickTime[c] = 0
                            if self.__newJoint is None:
                                self.__newJoint = Joint(p, c, True)  # attach the joint to the current point and controller's hand
                            elif self.__newJoint.pOne != p:  # if the point to attach the joint to is not the current point, prevent both points in a joint from being the exact same
                                self.__newJoint.pTwo = p
                                self.__newJoint.controller = False
                                self.joints.append(self.__newJoint)
                                self.__newJoint = None

                # remove latest created joint
                if buttonPressed('undoJoint', controlsConf.controllers[c], c):
                    if not self.__buttonHeld['undoJoint'][c]:
                        self.__buttonHeld['undoJoint'][c] = True
                        self.joints[-1].unDraw()
                        self.joints.pop(-1)

            # hand<>collisionRect dragging
            for cr in range(len(self.collisionRect)):
                if self.collisionRect[cr].drawn:
                    yCollisionPlane = getYCollisionPlane(self.collisionRect[cr], controls.hand[c].cords)
                    if getCubeCollision(controls.hand[c].cords, controls.hand[c].radius, self.collisionRect[cr], yCollisionPlane) and (self.dragP[c] is None):  # detect for hand<>collisionRect collisions using y = mx + c
                        self.collisionRect[cr].collidingController[c] = True
                        if selectP(c):
                            self.lastR[c] = cr
                            if not self.__buttonHeld['select'][c]:
                                self.__buttonHeld['select'][c] = True
                                for axis in range(3):
                                    self.__relPos[c][axis] = self.collisionRect[cr].cords[axis] - controls.hand[c].cords[axis]
                                if self.__clickTime[c] < 0.25:  # if there's a double click, summon sliders (if in VR) or manual inputs (if in keyboard/mouse) to change the size and density of the double-clicked collision rect
                                    if self.__GUI['GUISelector']['']['pointRect'] is None:
                                        self.__GUI['GUISelector']['']['pointRect'] = myGUI.GUISelector({'Size': None, 'Solid/\nLiquid': None}, [controls.hand[c].cords[0], controls.hand[c].cords[1] - 1, controls.hand[c].cords[2]], lControllerObj, rControllerObj, cr)
                                    else:
                                        self.__GUI['GUISelector']['']['pointRect'].drawn = False
                                        self.__GUI['GUISelector']['']['pointRect'].unDraw()
                                else:
                                    self.__clickTime[c] = 0  # reset the time since last click, since this click IS the last click!
                            if self.dragR[c] is None:  # used to set the drag variables if they are not already set
                                self.dragR[c] = cr
                        else:
                            self.__buttonHeld['select'][c] = False
                    else:
                        self.collisionRect[cr].collidingController[c] = False
            if self.dragP[c] is not None:
                for axis in range(3):
                    self.points[self.dragP[c]].cords[axis] = controls.hand[c].cords[axis] + self.__relPos[c][axis]  # set the point position to the position of the controller that grabbed said point
            if self.dragR[c] is not None:
                tempCords = [0, 0, 0]
                for axis in range(3):
                    tempCords[axis] = controls.hand[c].cords[axis] + self.__relPos[c][axis]
                self.collisionRect[self.dragR[c]].cords = copy.deepcopy(tempCords)  # set the collisionRect position to the controller's hand that grabbed said collisionRect's position
            self.__selectPointAnime(c)
            # reset drag variables if select button is not pressed
            if not selectP(c):
                self.dragP[c] = None
                self.dragR[c] = None
            # recalls the last clicked point to the controller's position
            if buttonPressed('recall', controlsConf.controllers[c], c):
                if self.lastP[c] is not None:
                    self.points[self.lastP[c]].cords = copy.deepcopy(controls.hand[c].cords)

            # remove the joint if 'dragJoint' is pressed again, and the hand isn't colliding with any point
            # basically just remove the joint if it's being attached to the air
            if buttonPressed('dragJoint', controlsConf.controllers[c], c) and (self.__newJoint is not None) and (not colliding):
                self.__newJoint.unDraw()
                self.__newJoint = None

    def __setRadiusDensityGUI(self, cords, p):
        if self.__GUI[p + 1000]['slider']['radius'] is None:  # only summon if GUI is empty
            self.__GUI[p + 1000]['slider']['radius'] = getSliderManual(0, self.points[p].radius, self.points[p].origRadius, [cords[0], cords[1] + 0.5, cords[2]], 10, maxRadius, minRadius, 'Radius')
        else:
            self.__GUI[p + 1000]['slider']['radius'].unDraw()
            self.__GUI[p + 1000]['slider']['radius'] = None
        if self.__GUI[p + 1000]['slider']['density'] is None:  # only summon if GUI is empty
            self.__GUI[p + 1000]['slider']['density'] = getSliderManual(0, self.points[p].density, self.points[p].origDensity, [cords[0], cords[1] - 0.5, cords[2]], 10, maxDensity, minDensity, 'Density')
            if mode == 'vr':
                self.__GUI[p + 1000]['slider']['density'].closeButton.unDraw()  # only one 'X' needs to be rendered, since there are two Xs within each other
                self.__GUI[p + 1000]['slider']['density'].closeButton.cords[1] = cords[1] + 1  # offset this 'X' to be within the other 'X' so that they both act as one button to dismiss both radius and density GUIs simultaneously
        else:
            self.__GUI[p + 1000]['slider']['density'].unDraw()
            self.__GUI[p + 1000]['slider']['density'] = None

    def __selectPointAnime(self, c):
        # unique animation for selecting points
        if self.collP[c] is not None:  # only run animations if a point is intersecting with a hand
            if self.dragP[c] is not None:  # only run the below if a point is being dragged
                controls.anim[c].point = self.points[self.collP[c]]  # make the selection animation encapsulate the point
                if self.__animeScale[c] > (self.points[self.collP[c]].radius / controls.anim[c].sphereRad):  # set the maximum size of the animation equal to the size of the selected point
                    self.__animeScaleSpeed -= 0.1 / physicsTime
                    self.__animeScale[c] += self.__animeScaleSpeed
                    # approximate function for changing color with time based on radius: f(x) = 6 / (time * sqrt(radius * 10))
                    f = 6 / (renderRate * math.sqrt(self.points[self.collP[c]].radius * 10))
                    # green-shift the animation
                    self.__animeColor[c][0] -= f
                    self.__animeColor[c][1] += f
                else:
                    self.__animeScale[c] = self.points[self.collP[c]].radius / controls.anim[c].sphereRad
                    controls.anim[c].pause = True
                controls.anim[c].setScale(self.__animeScale[c])
                controls.anim[c].setColor(self.__animeColor[c])
            elif not detectPointCollision(self.points[self.collP[c]].radius, controls.hand[c].radius, self.points[self.collP[c]].cords, controls.hand[c].cords):
                self.collP[c] = None  # the final else statement takes care of the rest
            else:
                controls.anim[c].point = self.points[self.collP[c]]
                self.__animeScale[c] = 1.2 * self.points[self.collP[c]].radius / controls.anim[c].sphereRad
                self.__animeScaleSpeed = 0
                self.__animeColor[c] = [1, 0, 0]
                controls.anim[c].setScale(self.__animeScale[c])
                controls.anim[c].setColor(self.__animeColor[c])
                controls.anim[c].pause = False
        else:  # return the animation to the hand. this is a must since points can be deleted.
            controls.anim[c].point = controls.hand[c]
            controls.anim[c].resetColor()
            controls.anim[c].resetScale()
            self.collP[c] = None
            controls.anim[c].pause = False

    def removeConnectedJoints(self, pIdx):
        for j in self.joints:
            if (j.pOne == pIdx) or (j.pTwo == pIdx):
                j.unDraw()

    def __updateGUI(self):
        for g in self.__GUI:
            for gt in self.__GUI[g]:
                for gta in self.__GUI[g][gt]:
                    if self.__GUI[g][gt][gta] is not None:
                        if self.__GUI[g][gt][gta].drawn:
                            if g == 'GUISelector':
                                self.__GUIType = self.__GUI[g][gt][gta].main()
                            else:
                                pcIdx = g  # for both points and collisionRects, depending on what was double-clicked
                                if gta == 'radius':
                                    self.__GUI[g][gt][gta].setVar(self.points[pcIdx - 1000].radius)
                                    self.points[pcIdx - 1000].setRadiusDensity(self.__GUI[g][gt][gta].main(), self.points[pcIdx - 1000].density)
                                elif gta == 'density':
                                    if pcIdx >= 1000:
                                        self.__GUI[g][gt][gta].setVar(self.points[pcIdx - 1000].density)
                                        self.points[pcIdx - 1000].setRadiusDensity(self.points[pcIdx - 1000].radius, self.__GUI[g][gt][gta].main())
                                    else:
                                        self.__GUI[g][gt][gta].setVar(self.collisionRect[pcIdx].density)
                                        self.collisionRect[pcIdx].density = self.__GUI[g][gt][gta].main()
                                elif gta == 'angle':
                                    self.__GUI[g][gt][gta].setVar(math.degrees(self.collisionRect[pcIdx].angle[2]))
                                    self.collisionRect[pcIdx].angle[2] = math.radians(self.__GUI[g][gt][gta].main())
                                elif gta == 'viscosity':
                                    self.__GUI[g][gt][gta].setVar(self.collisionRect[pcIdx].viscosity)
                                    self.collisionRect[pcIdx].viscosity = self.__GUI[g][gt][gta].main()
                                elif (gta == 'XZ') or (gta == 'XY') or (gta == 'YZ') or (gta == '3D'):
                                    self.__GUI[g][gt][gta].setVar(self.collisionRect[pcIdx].size)
                                    size = self.__GUI[g][gt][gta].main()
                                    for axis in self.__GUI[g][gt][gta].axes:
                                        self.collisionRect[pcIdx].size[axis] = size[axis]
                                elif g == 'Tutorials':
                                    self.__GUI[g][gt][gta].main()
                                else:  # must be referring to the size of a collisionRect
                                    self.__GUI[g][gt][gta].setVar(self.collisionRect[pcIdx].size)
                                    self.collisionRect[pcIdx].size = self.__GUI[g][gt][gta].main()
                        else:
                            self.__GUI[g][gt][gta] = None

        self.__selectGUIType()

    # summons a GUI if self.GUIType has a value, running through all the possible case scenarios and exceptions for different variables
    # since there are many exceptions, this method has a very large cognitive complexity
    def __selectGUIType(self):
        if self.__GUIType is not None:
            if self.__GUIType[0] == 'Tutorials':
                if self.__GUI[self.__GUIType[0]][''][self.__GUIType[1][0]] is not None:
                    self.__GUI[self.__GUIType[0]][''][self.__GUIType[1][0]].unDraw()
                    self.__GUI[self.__GUIType[0]][''][self.__GUIType[1][0]] = None
                self.__GUI[self.__GUIType[0]][''][self.__GUIType[1][0]] = myGUI.Tutorial(controls.hand[0].cords, [10, 0.2], self.__tutorialTexts[self.__GUIType[1][0]], [], 0.3, lControllerObj, rControllerObj)
            elif self.__GUIType[0] == 'Save & Exit':
                self.__export()
            elif self.__GUIType[0] == 'Solid/\nLiquid':
                if self.__GUIType[1][0] == 'Solid':
                    self.collisionRect[self.__GUIType[3][0]].rectType = 's'
                elif self.__GUIType[1][0] == 'Liquid':
                    self.collisionRect[self.__GUIType[3][0]].rectType = 'l'
            elif self.__GUIType[0] == 'Size':
                resetDicts = ['density', 'angle', 'viscosity']  # dictionary values to reset, no matter the GUI summoned
                for r in resetDicts:
                    if self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()][r] is not None:
                        self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()][r].unDraw()
                        self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()][r] = None
                if self.__GUIType[1][0] == 'Slider':
                    self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['density'] = myGUI.Slider(0, self.collisionRect[self.__GUIType[3][0]].density, 1000,
                                                                                                             [controls.hand[0].cords[0] + 2.5, controls.hand[0].cords[1] - 1,
                                                                                                              controls.hand[0].cords[2]], 5, 50000, 10, 'Density',
                                                                                                             lControllerObj,
                                                                                                             rControllerObj)
                    self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['angle'] = myGUI.Slider(0, self.collisionRect[self.__GUIType[3][0]].angle[2], 0.001,
                                                                                                           [controls.hand[0].cords[0] + 2.5, controls.hand[0].cords[1] - 2, controls.hand[0].cords[2]],
                                                                                                           5, 89.99999, 0.001, 'Angle', lControllerObj,
                                                                                                           rControllerObj)
                    self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['viscosity'] = myGUI.Slider(0, self.collisionRect[self.__GUIType[3][0]].viscosity, 1,
                                                                                                               [controls.hand[0].cords[0] + 2.5, controls.hand[0].cords[1] - 3,
                                                                                                                controls.hand[0].cords[2]], 5, 20, 0, 'Viscosity',
                                                                                                               lControllerObj,
                                                                                                               rControllerObj)
                    closeButtonCords = self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['density'].closeButton.cords
                    self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['angle'].closeButton.setPos(closeButtonCords, True)
                    self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['viscosity'].closeButton.setPos(closeButtonCords, True)
                    for axis in range(3):
                        self.collisionRect[self.__GUIType[3][0]].size[axis] += self.collisionRect[self.__GUIType[3][0]].sizeOffset[axis]
                    self.collisionRect[self.__GUIType[3][0]].sizeOffset = [0, 0, 0]
                    size = 25
                    for axis in range(3):
                        if self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()][axis] is not None:
                            self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()][axis].unDraw()
                            self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()][axis] = None
                        cords = copy.deepcopy(controls.hand[0].cords)
                        cords[axis] += 0.5 + size / 2
                        self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()][axis] = myGUI.Slider(axis, self.collisionRect[self.__GUIType[3][0]].size, [1, 1, 1], cords, size, 100, 0.1,
                                                                                                            f'Size {axis}', lControllerObj,
                                                                                                            rControllerObj)
                        self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()][axis].closeButton.setPos(closeButtonCords, True)
                elif self.__GUIType[1][0] == 'Manual':
                    for axis in range(3):
                        self.collisionRect[self.__GUIType[3][0]].size[axis] += self.collisionRect[self.__GUIType[3][0]].sizeOffset[axis]
                    self.collisionRect[self.__GUIType[3][0]].sizeOffset = [0, 0, 0]
                    for axis in range(3):
                        if self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()][axis] is not None:
                            self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()][axis].unDraw()
                            self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()][axis] = None
                        cords = copy.deepcopy(controls.hand[0].cords)
                        if mode == 'vr':
                            cords[0] += axis * 3.5
                            yDisp = -6.5
                            xDisp = 3.5
                        else:  # keyboard/mouse manual inputs are much tinier compared to VR manual inputs, so make the distance to each input much smaller.
                            cords[0] += axis * 0.5
                            yDisp = -0.5
                            xDisp = 0.5
                        self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()][axis] = myGUI.Manual(axis, self.collisionRect[self.__GUIType[3][0]].size, [1, 1, 1], cords, f'Size {axis}',
                                                                                                            lControllerObj,
                                                                                                            rControllerObj, False)
                        if mode == 'vr':
                            closeButtonCords = self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()][0].closeButton.cords
                            if axis != 0:  # don't prevent the only closeButton remaining from being removed!
                                self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()][axis].closeButton.setPos(closeButtonCords, True)
                    self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['density'] = myGUI.Manual(0, self.collisionRect[self.__GUIType[3][0]].density, 1000,
                                                                                                             [controls.hand[0].cords[0], controls.hand[0].cords[1] + yDisp, controls.hand[0].cords[2]],
                                                                                                             'Density', lControllerObj,
                                                                                                             rControllerObj, False)
                    self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['angle'] = myGUI.Manual(0, self.collisionRect[self.__GUIType[3][0]].angle[2], 0.001,
                                                                                                           [controls.hand[0].cords[0] + xDisp, controls.hand[0].cords[1] + yDisp,
                                                                                                            controls.hand[0].cords[2]], 'Angle', lControllerObj,
                                                                                                           rControllerObj, False)
                    self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['viscosity'] = myGUI.Manual(0, self.collisionRect[self.__GUIType[3][0]].viscosity, 1,
                                                                                                               [controls.hand[0].cords[0] + xDisp * 2, controls.hand[0].cords[1] + yDisp,
                                                                                                                controls.hand[0].cords[2]], 'Viscosity',
                                                                                                               lControllerObj,
                                                                                                               rControllerObj, False)

                    if mode == 'vr':
                        for g in resetDicts:
                            self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()][g].closeButton.setPos(closeButtonCords, True)

                elif self.__GUIType[1][0] == 'Dial':
                    if self.collisionRect[self.__GUIType[3][0]].sizeOffset == [0, 0, 0]:
                        self.collisionRect[self.__GUIType[3][0]].sizeOffset = [11, 11, 11]
                        for axis in range(3):
                            self.collisionRect[self.__GUIType[3][0]].size[axis] -= self.collisionRect[self.__GUIType[3][0]].sizeOffset[axis]
                    varOffset = self.collisionRect[self.__GUIType[3][0]].sizeOffset
                    cRad = 10
                    if self.__GUIType[1][1] == '3D':
                        self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['3D'] = myGUI.Dial(0, self.collisionRect[self.__GUIType[3][0]].size, [-11, -11, -11], controls.hand[0].cords,
                                                                                                          cRad, [20, 20, 20], [-20, -20, -20], 'XYZ', lControllerObj,
                                                                                                          rControllerObj, varOffset[0], varOffset[1], varOffset[2])
                        closeButtonCords = self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['3D'].closeButton.cords
                    else:
                        self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['XY'] = myGUI.Dial(1, self.collisionRect[self.__GUIType[3][0]].size, [-11, -11, -11], controls.hand[0].cords,
                                                                                                          cRad, [20, 20], [-20, -20], 'XY', lControllerObj,
                                                                                                          rControllerObj, varOffset[0], varOffset[1], varOffset[2])
                        closeButtonCords = self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['XY'].closeButton.cords
                        self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['XZ'] = myGUI.Dial(0, self.collisionRect[self.__GUIType[3][0]].size, [-11, -11, -11], controls.hand[0].cords,
                                                                                                          cRad, [20, 20], [-20, -20], 'XZ', lControllerObj,
                                                                                                          rControllerObj, varOffset[0], varOffset[1], varOffset[2])
                        self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['XZ'].closeButton.setPos(closeButtonCords, True)
                    self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['density'] = myGUI.Slider(0, self.collisionRect[self.__GUIType[3][0]].density, 1000,
                                                                                                             [controls.hand[0].cords[0], controls.hand[0].cords[1] + 1,
                                                                                                              controls.hand[0].cords[2] - cRad - 0.2], 5, 50000, 10, 'Density',
                                                                                                             lControllerObj,
                                                                                                             rControllerObj)
                    self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['angle'] = myGUI.Slider(0, self.collisionRect[self.__GUIType[3][0]].angle[2], 0.001,
                                                                                                           [controls.hand[0].cords[0], controls.hand[0].cords[1],
                                                                                                            controls.hand[0].cords[2] - cRad - 0.2], 5, 89.99999, 0.001, 'Angle',
                                                                                                           lControllerObj,
                                                                                                           rControllerObj)
                    self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()]['viscosity'] = myGUI.Slider(0, self.collisionRect[self.__GUIType[3][0]].viscosity, 1,
                                                                                                               [controls.hand[0].cords[0], controls.hand[0].cords[1] - 1,
                                                                                                                controls.hand[0].cords[2] - cRad - 0.2], 5, 20, 0, 'Viscosity',
                                                                                                               lControllerObj,
                                                                                                               rControllerObj)
                    for g in resetDicts:
                        self.__GUI[self.__GUIType[3][0]][self.__GUIType[1][0].lower()][g].closeButton.setPos(closeButtonCords, True)

            self.__GUIType = None

    def render(self):
        self.__updateGUI()
        controls.main()
        for p in self.points:
            p.draw()
        for j in self.joints:
            j.draw()
        if self.__newJoint is not None:
            self.__newJoint.draw()
        for g in self.__GUI:
            for gu in self.__GUI[g]:
                for gui in self.__GUI[g][gu]:
                    if self.__GUI[g][gu][gui] is not None:
                        self.__GUI[g][gu][gui].draw(controls.camCords)
        for c in self.collisionRect:
            c.draw()

    def __export(self):
        """
        export format:
            POINTS: cords, radius, density
            JOINTS: pOneIdx, pTwoIdx
            COLLISIONRECTS: size, cords, angle, density, viscosity, dragConst, transparency, rectType
        """
        f = open('exportData', 'w')
        f.write('POINTS\n')
        for p in self.points:
            if p.drawn:  # only add points if they haven't been dumped in a 'trash' void box
                f.write(f'{p.cords} | {p.radius} | {p.density}\n')
        f.write('JOINTS\n')
        for j in self.joints:
            if j.drawn:  # only add joints if they haven't been dumped in a 'trash' void box
                f.write(f'{j.pOne} | {j.pTwo}\n')
        f.write('COLLISIONRECTS\n')
        for c in self.collisionRect:
            if c.drawn:  # only add collisionRects if they haven't been dumped in a 'trash' void box
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
            if self.vertex[0][0] != self.vertex[7][0]:
                my = (self.vertex[0][1] - self.vertex[7][1]) / (self.vertex[0][0] - self.vertex[7][0])
            else:
                my = float('inf')
            self.grad = {
                'x': mx,
                'y': my
            }

    def draw(self):
        if self.show and self.drawn:
            self.update()
            if self.rectType == 's':
                self.transparency = 0.8
            elif self.rectType == 'l':
                self.transparency = 0.5
            tempSize = [self.size[0] + self.sizeOffset[0], self.size[1] + self.sizeOffset[1], self.size[2] + self.sizeOffset[2]]
            self.rect.setScale(tempSize)
            self.rect.setPosition(self.cords)
            self.rect.setEuler(math.degrees(self.angle[0]), math.degrees(self.angle[1]), math.degrees(self.angle[2]))
            self.rect.alpha(self.transparency)

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
    def __init__(self, cords, spriteType, *display) -> None:
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

    def drag(self) -> None:
        for c in range(controlsConf.controllerAmt):
            collision = detectPointCollision(controls.hand[c].radius, self.collisionRad, controls.hand[c].cords, self.cords)

            # if a hand is dragging a point/collisionRect from a void box that summons points/collisionRects
            if selectP(c):
                if not self.pHeld[c]:
                    self.pHeld[c] = True
                    if collision:
                        if self.spriteType == 'point':
                            game.addPoint(self.cords, 0.1, c)
                        elif self.spriteType == 'collisionRect':
                            game.addCollisionRect(CollisionRect([0.25, 0.25, 0.25], self.cords, [0, 0, math.radians(0.001)], 1000, 1, 1, 1, 's'))

            # if a point/collisionRect is being dropped off by a hand in a trash void box
            elif self.spriteType == 'trash':
                if collision:
                    if game.lastP[c] is not None:
                        if game.points[game.lastP[c]].collidingController[c]:
                            game.removeConnectedJoints(game.lastP[c])  # remove all joints connected to the dismissed point
                            game.points[game.lastP[c]].unDraw()
                            game.points.pop(game.lastP[c])
                            game.lastP[c] = None
                            game.dragP[c] = None
                            game.collP[c] = None
                            # if the index position of any joint's reference point(s) is >= the index position of the dismissed point, decrease said index position(s) by 1
                            # this is done since the point object at the index position 'lastP' is popped from the points list, decreasing all subsequent objects' index positions by 1
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
