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
    imports = input('Import from exportData? (y / n): ')
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

# initialize controls
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


# Main class for main.py
class Main:
    def __init__(self):
        self.points = []  # list of points for the whole program
        self.joints = []  # list of joints for the whole program
        self.__GUI = {  # dictionary of all GUIs and their possible forms (dimensions, axes, etc.)
            'gameSpeed': {'dial': {'XZ': None, 'XY': None, 'YZ': None, '3D': None}, 'slider': {'X': None, 'Y': None, 'Z': None}, 'manual': {'def': None}},
            'gField': {'dial': {'XZ': None, 'XY': None, 'YZ': None, '3D': None}, 'slider': {'X': None, 'Y': None, 'Z': None}, 'manual': {'X': None, 'Y': None, 'Z': None}},
            'gasDensity': {'dial': {'XZ': None, 'XY': None, 'YZ': None, '3D': None}, 'slider': {'X': None, 'Y': None, 'Z': None}, 'manual': {'def': None}},
            'springConst': {'dial': {'XZ': None, 'XY': None, 'YZ': None, '3D': None}, 'slider': {'X': None, 'Y': None, 'Z': None}, 'manual': {'def': None}},
            'damping': {'dial': {'XZ': None, 'XY': None, 'YZ': None, '3D': None}, 'slider': {'X': None, 'Y': None, 'Z': None}, 'manual': {'def': None}},
            'friction': {'dial': {'XZ': None, 'XY': None, 'YZ': None, '3D': None}, 'slider': {'X': None, 'Y': None, 'Z': None}, 'manual': {'def': None}},
            'strain': {'dial': {'XZ': None, 'XY': None, 'YZ': None, '3D': None}, 'slider': {'X': None, 'Y': None, 'Z': None}, 'manual': {'def': None}},
            'GUISelector': {'': {'': None}},  # this has empty strings since the GUI selector has only one possible form
            'Tutorials': {'': {}}
        }
        self.diff = []  # cache variable to store the scalar distance between each point
        self.collisionRect = []  # list of collision rectangles
        self.__dragP = [None, None]  # last clicked point index
        self.__lastP = [None, None]  # last clicked point that always retains its value for "recalling" objects to the controller
        self.pause = False  # pauses physics
        self.__buttonHeld = {}  # stores if a button is being held from config.controls
        for c in config.controls:
            self.__buttonHeld.update({c: [False, False]})
        self.__collP = [None, None]  # stores the indexes of a point that is colliding with either controller
        self.__animeScale = [1, 1]  # visual scale of controller animations
        self.__animeScaleSpeed = 0  # rate at which animations scale
        self.__animeColor = [[0, 0, 0], [0, 0, 0]]  # color of each animation
        self.__GUIType = None  # holds the return value of GUISelector to create relevant GUI(s)
        self.__clickTime = [0, 0]  # stores time since 'select' was pressed for both controllers in order for double-click detection
        self.__relPos = [[0, 0, 0], [0, 0, 0]]  # stores the relative position of selected points with either controller
        self.__clothData = {}
        self.__tutorialTexts = {}
        self.__importTutorials()
        if imports:
            self.__importData()

    def __importData(self):
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
            self.addPoint(Point(p[1], p[2], True))
            self.points[-1].teleport(p[0])
        for j in joints:
            self.joints.append(Joint(True, '', globalVars['springConst'], j[0], j[1], globalVars['damping'], 69, self))
            for p in range(len(self.points)):
                for po in range(len(self.points)):
                    if (p != po) and (po > p) and (((j[0] == p) and (j[1] == po)) or ((j[1] == p) and (j[0] == po))):
                        if self.points[p].cloth == '':
                            self.points[p].cloth = f'{len(self.joints)}'
                        self.points[po].cloth = self.points[p].cloth
        for c in collisionRects:
            self.collisionRect.append(CollisionRect(c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7]))

    # initialize all the lists that depend on self.points and self.collisionRect
    def initLists(self):
        for p in range(len(self.points)):
            self.__GUI.update({p: {'slider': {'radius': None, 'density': None}, 'manual': {'radius': None, 'density': None}}})
            for _ in range(len(self.collisionRect)):
                self.points[p].collision.append('')
                self.points[p].lastCollision.append('')
                self.points[p].colliding.append(False)
                self.points[p].cubeCollision.append(False)
                self.points[p].cubeCollisionCalc.append(False)
                self.points[p].cubeSubmersion.append(False)
                self.points[p].addMultiplier()

            self.diff.append([])
            for _ in range(len(self.points)):
                self.diff[p].append(0)
        self.__lastP = [len(self.points) - 1, len(self.points) - 2]
        self.__updateJointConnections()
        self.__updateCloths()
        # below is the code I used to get the relative size of the JetBrains font to the game scene
        # myT = viz.addText3D('abcd', fontSize=1.69 / 4)  # OBSERVATION: font size of 1.69 has the width of 1 unit
        # myT = viz.addText3D('a\nb\nc', fontSize=1)  # OBSERVATION: font size of 1 has the height of 1 unit
        # myT.font("JetBrainsMono-2.304\\fonts\\ttf\\JetBrainsMono-Medium.ttf")

    # update all the lists that depend on self.points and self.collisionRect after adding a collisionRect or point
    def updateLists(self):
        self.__GUI.update({len(self.points) - 1: {'slider': {'radius': None, 'density': None}, 'manual': {'radius': None, 'density': None}}})
        for _ in range(len(self.collisionRect)):
            self.points[-1].collision.append('')
            self.points[-1].lastCollision.append('')
            self.points[-1].colliding.append(False)
            self.points[-1].cubeCollision.append(False)
            self.points[-1].cubeCollisionCalc.append(False)
            self.points[-1].cubeSubmersion.append(False)
            self.points[-1].addMultiplier()
        self.diff.append([])
        for p in range(len(self.points) - 1):
            self.diff[p].append(0)
        for p in range(len(self.points)):
            self.diff[-1].append(0)
        self.__updateJointConnections()
        self.__updateCloths()

    # put the indexes of all points into the clothData dictionary identify all points in a cloth
    def __updateCloths(self):
        global clothNames  # globalized to allow the clothNames dict in config to be updated for cloth/point selection in the GUISelector
        for p in range(len(self.points)):
            # if the point isn't a part of a cloth, make its key as its position index p in the points list
            if self.points[p].cloth == '':
                clothNames.update({f'{p}': None})
                self.__clothData.update({f'{p}': [p]})
            # if the current point's cloth does not currently exist in clothData AND the current point is a part of a cloth, then add the cloth's name as a key to clothData and clothNames
            elif self.__clothData.get(self.points[p].cloth) is None:
                clothNames.update({self.points[p].cloth: None})
                self.__clothData.update({self.points[p].cloth: []})
            # if the current point is a part of a cloth AND the current point's index doesn't currently exist in clothData, add it to clothData
            if (self.points[p].cloth != '') and (not checkInList(self.__clothData[self.points[p].cloth], p)):
                self.__clothData[self.points[p].cloth].append(p)

    def __importTutorials(self):
        f = open('tutorialTexts', 'r')
        tutors = f.read().splitlines()
        tNames = []
        tTexts = []
        for l in tutors:
            if l.find('---') != -1:  # if the current line is a tutorial's title, as indicated by a triple-dash, add a new list to tTexts to allow subsequent lines to be added to the new list until another tutorial's title is reached
                tTexts.append([])
                tempList = list(l)
                for _ in range(3):
                    tempList.pop(0)  # gets rid of the triple-dash to add the title to tNames
                tempStr = ''
                for c in tempList:
                    tempStr = f'{tempStr}{c}'
                tNames.append(tempStr)
            else:
                tTexts[-1].append(l)  # if the current line isn't a tutorial's title, 
        for t in range(len(tNames)):
            tNames[t] = tNames[t].replace('newLine', '\n')  # solution from Python Discord, credit goes to lordtyrionlannister "Saul Goodman". replaces all newLine values with an actual new line in string format.
            self.__tutorialTexts.update({tNames[t]: tTexts[t]})  # update local information about the tutorial
            tutorialNames.update({tNames[t]: None})  # update the global value of tutorialNames for use in the GUISelector
            self.__GUI['Tutorials'][''].update({tNames[t]: None})  # update local values of tutorials in self.GUI
        f.close()
        self.__GUI['Tutorials']['']['Introduction'] = myGUI.Tutorial([0, 2, 4], [10, 0.2], self.__tutorialTexts['Introduction'], [], 0.3, [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])  # always summon the introduction tutorial when the program starts

    # teleport a cloth to a controller's position; it can be specified if the parameter 'cloth' is a point index or a cloth name
    def __tpCloth(self, cloth, cords, c, tpType):
        cordDiff = []
        if tpType == 'cloth':  # tpType is cloth when a cloth is being summoned using the GUISelector
            pIdx = self.__clothData[cloth][0]
            self.points[pIdx].cords = copy.deepcopy(controls.hand[c].cords)
            for co in range(3):
                cordDiff.append(self.points[pIdx].cords[co] - self.points[pIdx].oldCords[co])
            if cloth != '':
                for p in self.__clothData[f'{cloth}']:
                    if p != pIdx:
                        for cor in range(3):
                            self.points[p].cords[cor] += cordDiff[cor]
                            self.points[p].oldCords[cor] += cordDiff[cor]
            self.points[pIdx].oldCords = copy.deepcopy(cords)
        elif tpType == 'point':  # tpType is point when a cloth is being summoned using the 'recall' button
            for co in range(3):
                cordDiff.append(self.points[cloth].cords[co] - self.points[cloth].oldCords[co])
            if self.points[cloth].cloth != '':
                for p in self.__clothData[f'{self.points[cloth].cloth}']:
                    if p != self.__lastP[c]:
                        for cor in range(3):
                            self.points[p].cords[cor] += cordDiff[cor]
                            self.points[p].oldCords[cor] += cordDiff[cor]
            self.points[cloth].oldCords = copy.deepcopy(cords)

    # update the number of connected joints to a point whenever a new joint is added
    def __updateJointConnections(self):
        for p in range(len(self.points)):
            tempInt = 0
            for j in self.joints:
                if (j.pOne == p) or (j.pTwo == p):
                    tempInt += 1
            self.points[p].jointConnections = tempInt

    # the function in this class that allows the program to run
    def main(self):
        global physicsTime  # must be globalised since gameSpeed can be changed by the user from the GUI selector
        physicsTime = calcRate * (1 / globalVars['gameSpeed'])  # update the value of physicsTime based on gameSpeed, since gameSpeed can be changed in a GUI
        for c in range(controlsConf.controllerAmt):
            self.__getButtonReleased(c)
            self.__pauseGame(c)
            self.__summonGUISelector(c)

        self.__dragPoint()

        for p in range(len(self.points)):
            self.points[p].sf = globalVars['friction']  # update each point's local value of friction based on globalVars['friction'], for the same reason physicsTime is updated
            self.__pointCollision(p)

            self.points[p].move()

        self.__getDist()  # cache the distance between each point

        # update each joint
        for j in range(len(self.joints)):
            self.joints[j].stiffness = globalVars['springConst']  # set stiffness for the same reason as physicsTime
            self.joints[j].dampingConst = globalVars['damping']  # set dampingConst for the same reason as physicsTime
            self.joints[j].maxStrain = globalVars['strain']  # set strain for the same reason as physicsTime
            self.joints[j].update()
            if not self.pause:
                self.joints[j].constrain()  # apply a force to each point from each joint

    def __pointCollision(self, p):
        # detect & resolve collisions with all points
        for po in range(len(self.points)):
            if (po > p) and (p != po) and (self.points[p].disabledPointCollisions[0] != po) and (self.points[po].disabledPointCollisions[0] != p):  # performance optimisation: only go through unique combinations of p and po (e.g. [1, 5] and [5, 0] are unique, but [1, 5] and [5, 1] are not)
                sumR = self.points[p].radius + self.points[po].radius
                # detect collisions utilizing the cached values of dist
                if self.diff[p][po] <= sumR:
                    # NOTE: the numbering of each point are unimportant
                    # store the mass and velocity of both points in much shorter variables in order to make them more readable
                    mOne = copy.deepcopy(self.points[p].mass)
                    mTwo = copy.deepcopy(self.points[po].mass)
                    vOne = copy.deepcopy(self.points[p].velocity)
                    vTwo = copy.deepcopy(self.points[po].velocity)
                    normal = getThreeDAngle(self.points[p].cords, self.points[po].cords, 'y')  # get the angle of the collision normal
                    for n in range(3):
                        normal[n] = abs(normal[n])  # make pitch, yaw, and roll of the normal angle positive
                    vRel = [abs(vOne[0] - vTwo[0]), abs(vOne[1] - vTwo[1]), abs(vOne[2] - vTwo[2])]
                    resultV = (vRel[0] * cos(normal[1]) * sin(normal[0])) + (vRel[1] * sin(normal[1])) + (vRel[2]) * cos(normal[1]) * cos(normal[0])  # calculate resultant velocity of each point relative to the normal
                    deltaP = ((mOne * mTwo) / (mOne + mTwo)) * resultV * 2  # calculate change in momentum
                    # determine the direction at which each point should be deflected
                    multiplier = [1, 1, 1]
                    if self.points[p].cords[0] > self.points[po].cords[0]:
                        multiplier[0] = -1
                    if self.points[p].cords[1] > self.points[po].cords[1]:
                        multiplier[1] = -1
                    if self.points[p].cords[2] > self.points[po].cords[2]:
                        multiplier[2] = -1
                    # calculate resultant velocity of each point and resolve the collision
                    self.points[p].cords[0] -= deltaP * cos(normal[1]) * sin(normal[0]) / (self.points[p].mass * calcRate) * multiplier[0]
                    self.points[po].cords[0] += deltaP * cos(normal[1]) * sin(normal[0]) / (self.points[po].mass * calcRate) * multiplier[0]
                    self.points[p].cords[1] -= deltaP * sin(normal[1]) / (self.points[p].mass * calcRate) * multiplier[1]
                    self.points[po].cords[1] += deltaP * sin(normal[1]) / (self.points[po].mass * calcRate) * multiplier[1]
                    self.points[p].cords[2] -= deltaP * cos(normal[1]) * cos(normal[0]) / (self.points[p].mass * calcRate) * multiplier[2]
                    self.points[po].cords[2] += deltaP * cos(normal[1]) * cos(normal[0]) / (self.points[po].mass * calcRate) * multiplier[2]

    # get if a button isn't being pressed to allow for single-click detection
    def __getButtonReleased(self, cIdx):
        for b in self.__buttonHeld:
            if not buttonPressed(b, controlsConf.controllers[cIdx], cIdx):
                self.__buttonHeld[b][cIdx] = False

    # summon the GUI selector if the 'GUISelector' button is pressed
    def __summonGUISelector(self, cIdx):
        if (not self.__buttonHeld['GUISelector'][cIdx]) and buttonPressed('GUISelector', controlsConf.controllers[cIdx], cIdx):
            self.__buttonHeld['GUISelector'][cIdx] = True
            if self.__GUI['GUISelector'][''][''] is None:
                self.__GUI['GUISelector'][''][''] = myGUI.GUISelector(globalVars, controls.hand[cIdx].cords, [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
            else:
                self.__GUI['GUISelector'][''][''].drawn = False
                self.__GUI['GUISelector'][''][''].unDraw()

    # pause if the 'pause' button is pressed
    def __pauseGame(self, cIdx):
        if (not self.__buttonHeld['pause'][cIdx]) and buttonPressed('pause', controlsConf.controllers[cIdx], cIdx):
            self.__buttonHeld['pause'][cIdx] = True
            self.pause = not self.pause  # reverse the boolean value of self.pause

    def render(self):
        self.__updateGUI()  # update all GUIs
        controls.main()  # runs the main function in the current control (keyboard/VR) setting
        for p in self.points:
            p.draw()
        for j in self.joints:
            j.draw()
        for g in self.__GUI:
            for gu in self.__GUI[g]:
                for gui in self.__GUI[g][gu]:
                    if self.__GUI[g][gu][gui] is not None:
                        self.__GUI[g][gu][gui].draw(controls.camCords)

    # used to drag points around using pointer/controller
    def __dragPoint(self):
        # if mode == 'vr':
        #     print(controlsConf.controllers[0].getButtonState() % touchpad, controlsConf.controllers[1].getButtonState() % touchpad)  # prints the current button being pressed for each controller

        # loop through all drag code for each controller
        for c in range(controlsConf.controllerAmt):
            if self.__clickTime[c] <= 0.25:
                self.__clickTime[c] += 1 / calcRate
            for g in self.__GUI:
                for gu in self.__GUI[g]:
                    for gui in self.__GUI[g][gu]:
                        if self.__GUI[g][gu][gui] is not None:
                            self.__GUI[g][gu][gui].drag(c, selectP(c))
            for p in range(len(self.points)):
                if detectCollision(self.points[p].radius, controls.hand[c].radius, self.points[p].cords, controls.hand[c].cords):
                    self.__collP[c] = p  # set the collision point to the current point's index
                    if selectP(c):  # detect if the select button is being pressed, depending on the controller mode
                        if not self.__buttonHeld['select'][c]:
                            self.__buttonHeld['select'][c] = True
                            for axis in range(3):
                                self.__relPos[c][axis] = self.points[p].cords[axis] - controls.hand[c].cords[axis]
                            cords = controls.hand[c].cords  # set cords to the current controller's cords to shorten the below for increased readability
                            if self.__clickTime[c] < 0.25:  # if there's a double click, summon sliders (if in VR) or manual inputs (if in keyboard/mouse) to change the density and radius of the double-clicked point
                                if self.__GUI[p]['slider']['radius'] is None:  # only summon if GUI is empty
                                    if mode == 'vr':
                                        self.__GUI[p]['slider']['radius'] = myGUI.Slider(0, self.points[p].radius, self.points[p].origRadius, [cords[0], cords[1] + 0.5, cords[2]], 10, 0.1, maxRadius, minRadius, 'Radius', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                                    elif mode == 'k':
                                        self.__GUI[p]['slider']['radius'] = myGUI.Manual(0, self.points[p].radius, self.points[p].origRadius, [cords[0], cords[1] + 0.5, cords[2]], 'Radius', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                                else:
                                    self.__GUI[p]['slider']['radius'].unDraw()
                                    self.__GUI[p]['slider']['radius'] = None
                                if self.__GUI[p]['slider']['density'] is None:  # only summon if GUI is empty
                                    if mode == 'vr':
                                        self.__GUI[p]['slider']['density'] = myGUI.Slider(0, self.points[p].density, self.points[p].origDensity, [cords[0], cords[1] - 0.5, cords[2]], 10, 0.1, 10000, 1, 'Density', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                                        self.__GUI[p]['slider']['density'].closeButton.unDraw()  # only one 'X' needs to be rendered, since there are two Xs within each other
                                        self.__GUI[p]['slider']['density'].closeButton.cords[1] = cords[1] + 1  # offset this 'X' to be within the other 'X' so that they both act as one button to dismiss both radius and density GUIs simultaneously
                                    elif mode == 'k':
                                        self.__GUI[p]['slider']['density'] = myGUI.Manual(0, self.points[p].density, self.points[p].origDensity, [cords[0], cords[1] - 0.5, cords[2]], 'Density', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                                else:
                                    self.__GUI[p]['slider']['density'].unDraw()
                                    self.__GUI[p]['slider']['density'] = None
                            else:
                                self.__clickTime[c] = 0  # reset the time since last click, since this click IS the last click!
                        if self.__dragP[c] is None:  # used to set the drag variables if they are not already set
                            self.__dragP[c] = p
                            if self.__lastP[c] != p:  # no need to run the below if the value of lastP won't change
                                if mode == 'vr':
                                    if self.__lastP[c - 1] != p:  # only allow unique points to be recalled by each controller
                                        self.__lastP[c] = p
                                else:
                                    self.__lastP[c] = p
            if self.__dragP[c] is not None:
                # set the dragging point's position to the controller that's dragging said point
                for axis in range(3):
                    self.points[self.__dragP[c]].cords[axis] = controls.hand[c].cords[axis] + self.__relPos[c][axis]
            self.__selectPointAnime(c)
            # reset drag variables if select button is not pressed
            if not selectP(c):
                self.__dragP[c] = None
            # recalls the last clicked point to the controller's position
            if buttonPressed('recall', controlsConf.controllers[c], c) and (self.__lastP[c] >= 0):
                # set cords of point to user pointer/hand
                self.points[self.__lastP[c]].cords = copy.deepcopy(controls.hand[c].cords)
                if not self.__buttonHeld['recall'][c]:
                    self.__tpCloth(self.__lastP[c], self.points[self.__lastP[c]].cords, c, 'point')
                    self.__buttonHeld['recall'][c] = True

    # animates selecting points depending on if it's being hovered over or selected
    def __selectPointAnime(self, c):
        # unique animation for selecting points
        if self.__collP[c] is not None:  # only run animations if a point is intersecting with a controller
            if self.__dragP[c] is not None:  # if the point is being selected, run the selection animation
                controls.anim[c].point = self.points[self.__collP[c]]  # make the selection animation encapsulate the point
                if self.__animeScale[c] > (self.points[self.__collP[c]].radius / controls.anim[c].sphereRad):
                    self.__animeScaleSpeed -= 0.1 / physicsTime
                    self.__animeScale[c] += self.__animeScaleSpeed  # accelerate the animation as it wraps around the point
                    f = 6 / (renderRate * math.sqrt(self.points[self.__collP[c]].radius * 10))  # approximate function for changing color with time based on radius: f(x) = 6 / (frequency * sqrt(radius * 10))
                    # green-shift the animation to make it feel like the point is being selected
                    self.__animeColor[c][0] -= f
                    self.__animeColor[c][1] += f
                else:
                    self.__animeScale[c] = self.points[self.__collP[c]].radius / controls.anim[c].sphereRad  # makes the minimum size of the animation equal to the size of the selected point
                    controls.anim[c].pause = True
                controls.anim[c].setScale(self.__animeScale[c])
                controls.anim[c].setColor(self.__animeColor[c])
            elif not detectCollision(self.points[self.__collP[c]].radius, controls.hand[c].radius, self.points[self.__collP[c]].cords, controls.hand[c].cords):  # if the controller is not hovering over a point, return the animation to the controller
                controls.anim[c].point = controls.hand[c]
                controls.anim[c].setScale(1)
                self.__collP[c] = None
                controls.anim[c].pause = False
            else:  # if the controller is hovering over a point, run the hovering animation
                controls.anim[c].point = self.points[self.__collP[c]]
                self.__animeScale[c] = 1.2 * self.points[self.__collP[c]].radius / controls.anim[c].sphereRad  # makes the size of the animation 20% larger than the size of the point, taking into account that it's been scaled down to match the size of the controller
                self.__animeScaleSpeed = 0
                controls.anim[c].setScale(self.__animeScale[c])
                self.__animeColor[c] = [1, 0, 0]  # make the animation red
                controls.anim[c].setColor([1, 0, 0])
                controls.anim[c].pause = False
        else:  # return the animation to the controller
            controls.anim[c].resetColor()
            controls.anim[c].resetScale()
            controls.anim[c].point = controls.hand[c]

    # get the distance between each point
    def __getDist(self):
        for p in range(len(self.points)):
            for po in range(len(self.points)):
                sumR = self.points[p].radius + self.points[po].radius
                disp = displacement(self.points[p].cords, self.points[po].cords)
                # don't detect for collisions if any diff value is greater than the sum of both points' radii. also don't get distance between 2 points if you already have it! this is a performance optimization that essentially halves the time complexity of this function, which is O(n!).
                if (((disp[0] <= sumR) or (disp[1] <= sumR) or (disp[2] <= sumR)) or (self.points[p].cloth != '') and (self.points[po].cloth != '')) and (p != po) and (po > p):
                    self.diff[p][po] = diffDistance(disp[0], disp[1], disp[2])

    # add a point to the points list
    def addPoint(self, point):
        self.points.append(point)
        for p in range(len(self.points)):
            self.points[p].pIdx = p

    # draw and update all the summoned GUIs
    def __updateGUI(self):
        for gVar in self.__GUI:
            for gType in self.__GUI[gVar]:
                for gAxis in self.__GUI[gVar][gType]:
                    if self.__GUI[gVar][gType][gAxis] is not None:  # if the GUI currently exists
                        if self.__GUI[gVar][gType][gAxis].drawn:  # if the GUI is currently summoned
                            if gVar == 'GUISelector':  # if the GUISelector is to be summoned, get its result as self.GUIType
                                self.__GUIType = self.__GUI[gVar][gType][gAxis].main()
                            else:
                                if type(gVar) is not int:
                                    if (type(globalVars[gVar]) is list) and ((gType == 'slider') or (gType == 'manual')):  # if the variable of the GUI is a list, an index xyz must be provided to change its value
                                        self.__GUI[gVar][gType][gAxis].setVar(globalVars[gVar][self.__GUI[gVar][gType][gAxis].xyz])  # updates the variable of this GUI if another GUI shares the same variable as this one
                                        globalVars[gVar][self.__GUI[gVar][gType][gAxis].xyz] = self.__GUI[gVar][gType][gAxis].main()  # update the variable that the GUI changes
                                    elif gVar != 'Tutorials':  # if the variable of the GUI isn't a list OR if it's type is a dial (since all return values of dials are lists), and index won't need to be provided
                                        self.__GUI[gVar][gType][gAxis].setVar(globalVars[gVar])  # updates the variable of this GUI if another GUI shares the same variable as this one
                                        globalVars[gVar] = self.__GUI[gVar][gType][gAxis].main()  # update the variable that the GUI changes
                                    else:  # if the GUI is a tutorial, don't do any fancy stuff. just run its main method!
                                        self.__GUI[gVar][gType][gAxis].main()
                                else:  # if the GUI was summoned as a result of double-clicking on a point, update the radius and density of that point
                                    if gAxis == 'radius':
                                        self.__GUI[gVar][gType][gAxis].setVar(self.points[gVar].radius)
                                        self.points[gVar].setRadiusDensity(self.__GUI[gVar][gType][gAxis].main(), self.points[gVar].density)
                                    elif gAxis == 'density':
                                        self.__GUI[gVar][gType][gAxis].setVar(self.points[gVar].density)
                                        self.points[gVar].setRadiusDensity(self.points[gVar].radius, self.__GUI[gVar][gType][gAxis].main())
                        else:  # if the GUI is to be removed
                            self.__GUI[gVar][gType][gAxis] = None

        self.__selectGUIType()

    # summon a GUI if self.GUIType is not None, running through all the possible case scenarios and exceptions for different variables
    def __selectGUIType(self):
        if self.__GUIType is not None:
            if self.__GUIType[0] == 'cloths':
                self.__tpCloth(self.__GUIType[1][0], controls.hand[self.__GUIType[2]].cords, self.__GUIType[2], 'cloth')
            elif self.__GUIType[0] == 'Tutorials':
                if self.__GUI[self.__GUIType[0]][''][self.__GUIType[1][0]] is not None:
                    self.__GUI[self.__GUIType[0]][''][self.__GUIType[1][0]].unDraw()
                    self.__GUI[self.__GUIType[0]][''][self.__GUIType[1][0]] = None
                self.__GUI[self.__GUIType[0]][''][self.__GUIType[1][0]] = myGUI.Tutorial(controls.hand[0].cords, [10, 0.2], self.__tutorialTexts[self.__GUIType[1][0]], [], 0.3, [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
            elif self.__GUIType[1][0] == 'Slider':
                xyz = self.__setupSliderManual()
                if type(globalVars[self.__GUIType[0]]) is list:  # if the quantity is a vector, xyz effects visuals and direction
                    self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][1]] = myGUI.Slider(xyz, globalVars[self.__GUIType[0]][xyz], defaultGlobalVars[self.__GUIType[0]][xyz], controls.hand[0].cords, 5, 0.15, globalRanges[self.__GUIType[0]][0], globalRanges[self.__GUIType[0]][1], self.__GUIType[0], [controlsConf.controllers[0], controls.hand[0]],
                                                                                                                     [controlsConf.controllers[1], controls.hand[1]])
                else:  # if the quantity is a scalar, xyz only effects visuals
                    self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][1]] = myGUI.Slider(xyz, globalVars[self.__GUIType[0]], defaultGlobalVars[self.__GUIType[0]], controls.hand[0].cords, 5, 0.15, globalRanges[self.__GUIType[0]][0], globalRanges[self.__GUIType[0]][1], self.__GUIType[0], [controlsConf.controllers[0], controls.hand[0]],
                                                                                                                     [controlsConf.controllers[1], controls.hand[1]])
            elif self.__GUIType[1][0] == 'Dial':
                self.__GUIType[1].append(self.__GUIType[1][1])
                if self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][2]] is not None:
                    self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][2]].unDraw()
                    self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][2]] = None
                if self.__GUIType[1][1] == '2D':  # if the dial is 2D, it will need to be provided with an axis representing the two values of the variable's list that should be changed
                    if self.__GUIType[1][2] == 'XZ':
                        xyz = 0
                    elif self.__GUIType[1][2] == 'XY':
                        xyz = 1
                    else:
                        xyz = 2
                    self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][2]] = myGUI.Dial(xyz, globalVars[self.__GUIType[0]], defaultGlobalVars[self.__GUIType[0]], controls.hand[0].cords, 5, 0.15, [globalRanges[self.__GUIType[0]][0], globalRanges[self.__GUIType[0]][0]], [globalRanges[self.__GUIType[0]][1], globalRanges[self.__GUIType[0]][1]], self.__GUIType[1][2],
                                                                                                                   [controlsConf.controllers[0], controls.hand[0]],
                                                                                                                   [controlsConf.controllers[1], controls.hand[1]])
                elif self.__GUIType[1][1] == '3D':  # if the dial is 3D, no axis needs to be provided since it will change all three of the variable's values in its list (basically means axis is XYZ)
                    self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][2]] = myGUI.Dial(0, globalVars[self.__GUIType[0]], defaultGlobalVars[self.__GUIType[0]], controls.hand[0].cords, 5, 0.15, [globalRanges[self.__GUIType[0]][0], globalRanges[self.__GUIType[0]][0], globalRanges[self.__GUIType[0]][0]],
                                                                                                                   [globalRanges[self.__GUIType[0]][1], globalRanges[self.__GUIType[0]][1], globalRanges[self.__GUIType[0]][1]], 'XYZ',
                                                                                                                   [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
            elif self.__GUIType[1][0] == 'Manual':
                xyz = self.__setupSliderManual()
                if type(globalVars[self.__GUIType[0]]) is list:  # if the quantity is a vector, xyz effects direction
                    self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][1]] = myGUI.Manual(xyz, globalVars[self.__GUIType[0]][xyz], defaultGlobalVars[self.__GUIType[0]][xyz], controls.hand[0].cords, self.__GUIType[0], [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                else:  # if the quantity is a scalar, xyz doesn't matter (which is an exception to the manual input GUI that's handled in myGUI)
                    self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][1]] = myGUI.Manual(xyz, globalVars[self.__GUIType[0]], defaultGlobalVars[self.__GUIType[0]], controls.hand[0].cords, self.__GUIType[0], [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])

            self.__GUIType = None

    # set up the GUI and axes of a slider or manual GUI
    def __setupSliderManual(self):
        if self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][1]] is not None:  # if the GUI is already summoned, remove it and summon a new one
            self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][1]].unDraw()
            self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][1]] = None
        if self.__GUIType[1][1] == 'X':
            xyz = 0
        elif self.__GUIType[1][1] == 'Y':
            xyz = 1
        else:
            xyz = 2
        return xyz


# class for spheres
class Point:
    def __init__(self, radius, density, show, *disabledPointCollisions):
        self.jointConnections = 0  # number of connected joints; usage will be determined with future implementations
        self.show = show
        self.radius = radius
        self.origRadius = radius
        if self.show:
            self.sphere = vizshape.addSphere(1, slices=pointResolution)  # vizard object for sphere
            self.sphere.setScale([self.radius, self.radius, self.radius])
        self.cords = [0, 0, 0]
        self.oldCords = [0, 0, 0]  # coordinate position from last frame
        self.velocity = [0, 0, 0]
        self.__force = [0, 0, 0]
        self.__normalForce = [0, 0, 0]  # here's how I'll calculate this when on a vertex: https://drive.google.com/file/d/1ES6T8RilTcE5Pu7Zhdxfo6R6hvvsViAT/view?usp=drive_link
        self.__acc = [0, 0, 0]
        self.density = density
        self.origDensity = density
        self.__volume = (4 / 3) * math.pi * self.radius ** 3
        self.__halfArea = 2 * math.pi * self.radius ** 2
        self.mass = self.density * self.__volume
        self.__weight = [self.mass * globalVars['gField'][0], self.mass * globalVars['gField'][1], self.mass * globalVars['gField'][2]]
        self.__gasDrag = [0, 0, 0]
        self.__liquidDrag = [0, 0, 0]
        self.__gasUpthrust = [0, 0, 0]
        self.__liquidUpthrust = [0, 0, 0]
        self.__friction = [0, 0, 0]
        self.constrainForce = [0, 0, 0]
        self.__impulse = [0, 0, 0]
        self.cubeCollision = []
        self.cubeCollisionCalc = []
        self.cubeSubmersion = []
        self.collision = []  # self.collision[count] represents the surface of a collision cuboid that the point is CURRENTLY (hence making self.collision[count] = '' in else cases) in front of, using only its center point as reference
        self.lastCollision = []
        self.__vertexState = ''  # closest vertex plane
        self.e = 1  # elasticity (MUST BE 1 AT ALL TIMES BC FLOATING POINT ERROR SUCKS :sob:)
        self.sf = globalVars['friction']  # surface friction coefficient
        self.__multiplier = []  # variable for movement calcs
        self.cloth = ''
        self.__movingAngle = [0, 0, 0]  # direction of movement
        self.__collisionState = ''
        self.__bAngle = [0, 0, 0]  # stores angle of b.angle
        self.__collAngle = [0, 0, 0]  # angle of collision point
        self.colliding = []
        self.pIdx = ''
        self.__submergedVolume = 0
        self.__submergedArea = 0
        self.__submergedRadius = 0
        self.disabledPointCollisions = ['']
        self.__xCollisionLine = None
        self.__yCollisionLine = None
        if len(disabledPointCollisions) > 0:
            self.disabledPointCollisions = disabledPointCollisions

    # setter method
    def addMultiplier(self):
        self.__multiplier.append(1)

    def teleport(self, cords):
        self.cords = copy.deepcopy(cords)
        self.oldCords = copy.deepcopy(cords)

    def setRadiusDensity(self, radius, density):
        self.radius = radius
        self.density = density
        self.__volume = 4 / 3 * math.pi * self.radius ** 3
        self.__halfArea = 2 * math.pi * self.radius ** 2
        self.mass = self.density * self.__volume
        if self.show:
            self.sphere.setScale([self.radius, self.radius, self.radius])

    def move(self):
        self.__weight = [self.mass * globalVars['gField'][0], self.mass * globalVars['gField'][1], self.mass * globalVars['gField'][2]]

        if not game.pause:
            self.__physics()
        self.__boxCollision()  # runs collision code

        # Verlet integration
        for c in range(3):
            self.velocity[c] = (self.cords[c] - self.oldCords[c]) * physicsTime  # set velocity to change in position
        self.oldCords = copy.deepcopy(self.cords)

        if not game.pause:
            for v in range(3):
                self.cords[v] += self.velocity[v] / physicsTime  # change coordinates based on velocity

    def draw(self):
        if self.show:
            self.sphere.setPosition(self.cords)

    def __physics(self):
        for axis in range(3):
            self.__gasDrag[axis] = 0.5 * globalVars['gasDensity'] * -getSign(self.velocity[axis]) * ((self.velocity[axis] / physicsTime) ** 2) * math.pi * (self.radius ** 2)
            self.__gasUpthrust[axis] = -(4 / 3) * math.pi * (self.radius ** 3) * globalVars['gasDensity'] * globalVars['gField'][axis]

            self.__force[axis] = self.__gasDrag[axis] + self.__liquidDrag[axis] + self.__gasUpthrust[axis] + self.__liquidUpthrust[axis] + self.__weight[axis] + self.constrainForce[axis]

        self.__resolveRectCollisions()

        # add all forces together and calculate acceleration from this resultant force
        for axis in range(3):
            self.__force[axis] += self.__normalForce[axis] + self.__friction[axis] + self.__impulse[axis]
            self.__acc[axis] = self.__force[axis] / self.mass  # F = ma, a = F/m
            self.oldCords[axis] -= self.__acc[axis] / (physicsTime ** 2)  # divide by time since d(v) = a * d(t)
        self.constrainForce = [0, 0, 0]  # reset constrainForce

        # moving angle about relative to each axis in the form of [x:y, x:z, y:z]
        if self.velocity[1] != 0:
            self.__movingAngle[0] = math.atan(self.velocity[0] / self.velocity[1])
        else:
            self.__movingAngle[0] = math.pi / 2
        if self.velocity[2] != 0:
            self.__movingAngle[1] = math.atan(self.velocity[0] / self.velocity[2])
        else:
            self.__movingAngle[1] = math.pi / 2
        if self.velocity[1] != 0:
            self.__movingAngle[2] = math.atan(self.velocity[2] / self.velocity[1])
        else:
            self.__movingAngle[2] = math.pi / 2

    def __resolveRectCollisions(self):
        # calculate normal reaction force. the reason it's here and not in boxCollision is because resultant force must first be calculated above.
        count = 0
        for b in game.collisionRect:
            if self.cubeCollisionCalc[count] and (b.type == 's'):
                self.__bAngle = copy.deepcopy(b.angle)  # assigns collisionRect angle to local variable, so it can be changed (for the sake of calculation) without changing the collisionRect's angle itself

                resultF = 0
                if (self.lastCollision[count] == 'top') or (self.lastCollision[count] == 'bottom'):
                    # check out this link to see why these if statements are used here, as well as the math:
                    if (self.__force[0] * self.__multiplier[count]) > 0:
                        resultF += abs(self.__force[0] * math.sin(self.__bAngle[2]))
                    if (self.__force[1] * self.__multiplier[count]) < 0:
                        resultF += abs(self.__force[1] * math.cos(self.__bAngle[2]))

                elif (self.lastCollision[count] == 'right') or (self.lastCollision[count] == 'left'):
                    self.__bAngle[2] -= math.pi / 2
                    if (self.__force[0] * self.__multiplier[count]) < 0:
                        resultF += abs(self.__force[0] * math.sin(self.__bAngle[2]))
                    if (self.__force[1] * self.__multiplier[count]) < 0:
                        resultF += abs(self.__force[1] * math.cos(self.__bAngle[2]))

                elif (self.lastCollision[count] == 'front') or (self.lastCollision[count] == 'back'):
                    if (self.__force[2] * self.__multiplier[count]) < 0:
                        resultF += abs(self.__force[2])
                    self.__normalForce[2] = resultF * self.__multiplier[count] * 0.999999  # floating point error is annoying
                    for plane in range(2):
                        self.__friction[plane] = -resultF * self.sf * b.sf * getSign(self.velocity[plane]) * sin(abs(self.__movingAngle[0]))

                # negative coefficients used for friction here since it always acts in the opposite direction to motion
                self.__normalForce[0] = -resultF * sin(self.__collAngle[2]) * self.__multiplier[count] * 0.999999
                self.__normalForce[1] = resultF * cos(self.__collAngle[2]) * self.__multiplier[count] * 0.999999
                self.__normalForce[2] = -resultF * sin(self.__collAngle[0]) * self.__multiplier[count] * 0.999999
                if self.__collisionState == 'y':
                    # negative coefficients used for normalForce here since it always acts in the opposite direction to resultant force
                    # *0.999999 used here to compensate for floating point error (I hate floating point error)
                    self.__friction[0] = -getSign(self.velocity[0]) * resultF * cos(self.__collAngle[2]) * self.sf * b.sf * sin(abs(self.__movingAngle[1]))
                    self.__friction[2] = -getSign(self.velocity[2]) * resultF * cos(self.__collAngle[2]) * self.sf * b.sf * cos(abs(self.__movingAngle[1]))
                elif self.__collisionState == 'x':
                    self.__friction[1] = getSign(self.velocity[1]) * resultF * sin(self.__collAngle[2]) * self.sf * b.sf * cos(abs(self.__movingAngle[2]))
                    self.__friction[2] = getSign(self.velocity[2]) * resultF * sin(self.__collAngle[2]) * self.sf * b.sf * sin(abs(self.__movingAngle[2]))
            count += 1

    # check this out here to see how I use lines, domains, and ranges for collision detection:
    def __yCollisionPlane(self, b):  # y = mx + c
        return {
            'left': {'y': (b.grad['y'] * self.cords[0]) + (b.vertex[1][1] - (b.grad['y'] * b.vertex[1][0])), 'm': b.grad['y'], 'c': b.vertex[1][1] - (b.grad['y'] * b.vertex[1][0])},
            'right': {'y': (b.grad['y'] * self.cords[0]) + (b.vertex[0][1] - (b.grad['y'] * b.vertex[0][0])), 'm': b.grad['y'], 'c': b.vertex[0][1] - (b.grad['y'] * b.vertex[0][0])},
            'top': {'y': (b.grad['x'] * self.cords[0]) + (b.vertex[1][1] - (b.grad['x'] * b.vertex[1][0])), 'm': b.grad['x'], 'c': b.vertex[1][1] - (b.grad['x'] * b.vertex[1][0])},
            'bottom': {'y': (b.grad['x'] * self.cords[0]) + (b.vertex[2][1] - (b.grad['x'] * b.vertex[2][0])), 'm': b.grad['x'], 'c': b.vertex[2][1] - (b.grad['x'] * b.vertex[2][0])},
        }

    def __xCollisionPlane(self, b):  # x = ym + c
        return {
            'left': {'x': - (b.grad['x'] * self.cords[1]) + (b.vertex[1][0] + (b.grad['x'] * b.vertex[1][1])), 'm': -b.grad['x'], 'c': b.vertex[1][0] + (b.grad['x'] * b.vertex[1][1])},
            'right': {'x': - (b.grad['x'] * self.cords[1]) + (b.vertex[0][0] + (b.grad['x'] * b.vertex[0][1])), 'm': -b.grad['x'], 'c': b.vertex[0][0] + (b.grad['x'] * b.vertex[0][1])},
            'top': {'x': - (b.grad['y'] * self.cords[1]) + (b.vertex[1][0] + (b.grad['y'] * b.vertex[1][1])), 'm': -b.grad['y'], 'c': b.vertex[1][0] + (b.grad['y'] * b.vertex[1][1])},
            'bottom': {'x': - (b.grad['y'] * self.cords[1]) + (b.vertex[2][0] + (b.grad['y'] * b.vertex[2][1])), 'm': -b.grad['y'], 'c': b.vertex[2][0] + (b.grad['y'] * b.vertex[2][1])}
        }

    # detects and resolves collisions between spheres (points) and static cuboids (collision rects)
    def __boxCollision(self):
        cubeCollision = False
        cubeSubmersion = False
        count = 0  # using count here instead of len(game.collisionRect) since it's just so much easier to read and type 'b' instead of 'game.collisionRect[b]'
        for cr in game.collisionRect:
            self.__bAngle = copy.deepcopy(cr.angle)
            self.__yCollisionLine = self.__yCollisionPlane(cr)
            self.__xCollisionLine = self.__xCollisionPlane(cr)

            # check out the logic here: https://drive.google.com/file/d/1B-GqxPcpGkWAE_ogzMvYntTNmt8R99gT/view?usp=drive_link
            self.__vertexState = ''  # stores the facing axis of the nearest vertex
            if ((self.cords[1] > self.__yCollisionLine['right']['y']) or (self.cords[1] < self.__yCollisionLine['left']['y'])) and ((self.cords[1] > self.__yCollisionLine['top']['y']) or (self.cords[1] < self.__yCollisionLine['bottom']['y'])) and ((self.cords[2] <= cr.plane['front']) and (self.cords[2] >= cr.plane['back'])):  # x > right, x < left, y > top, y < bottom, back < z < front
                self.__vertexState = 'z'
            elif ((self.cords[1] > self.__yCollisionLine['right']['y']) or (self.cords[1] < self.__yCollisionLine['left']['y'])) and ((self.cords[1] <= self.__yCollisionLine['top']['y']) and (self.cords[1] >= self.__yCollisionLine['bottom']['y'])) and ((self.cords[2] > cr.plane['front']) or (self.cords[2] < cr.plane['back'])):  # x > right, x < left, bottom < y < top, z > front, z < back
                self.__vertexState = 'y'
            elif ((self.cords[1] <= self.__yCollisionLine['right']['y']) and (self.cords[1] >= self.__yCollisionLine['left']['y'])) and ((self.cords[1] > self.__yCollisionLine['top']['y']) or (self.cords[1] < self.__yCollisionLine['bottom']['y'])) and ((self.cords[2] > cr.plane['front']) or (self.cords[2] < cr.plane['back'])):  # left < x < right, y > top, y < bottom, z > front, z < back
                self.__vertexState = 'x'

            # self.lastCollision represents the surface of a collision cuboid that the point was LAST in front of, factoring in its radius as well. this value never resets.
            if (self.cords[1] <= (self.__yCollisionLine['right']['y'] + self.radius)) and (self.cords[1] >= (self.__yCollisionLine['left']['y'] - self.radius)) and (self.cords[2] <= (cr.plane['front'] + self.radius)) and (self.cords[2] >= (cr.plane['back'] - self.radius)):
                if self.cords[1] >= (self.__yCollisionLine['top']['y'] + self.radius):
                    self.lastCollision[count] = 'top'
                elif self.cords[1] <= (self.__yCollisionLine['bottom']['y'] - self.radius):
                    self.lastCollision[count] = 'bottom'
            elif (self.cords[1] <= self.__yCollisionLine['top']['y']) and (self.cords[1] >= self.__yCollisionLine['bottom']['y']) and (self.cords[2] <= cr.plane['front']) and (self.cords[2] >= cr.plane['back']):
                if self.cords[1] >= (self.__yCollisionLine['right']['y'] + self.radius):
                    self.lastCollision[count] = 'right'
                elif self.cords[1] <= (self.__yCollisionLine['left']['y'] - self.radius):
                    self.lastCollision[count] = 'left'
            elif (self.cords[1] <= (self.__yCollisionLine['top']['y'] + self.radius)) and (self.cords[1] >= (self.__yCollisionLine['bottom']['y'] - self.radius)) and (self.cords[1] <= (self.__yCollisionLine['right']['y'] + self.radius)) and (self.cords[1] >= (self.__yCollisionLine['left']['y'] - self.radius)):
                if self.cords[2] >= (cr.plane['front'] - self.radius):
                    self.lastCollision[count] = 'front'
                elif self.cords[2] <= (cr.plane['back'] + self.radius):
                    self.lastCollision[count] = 'back'

            self.cubeCollisionCalc[count] = (self.cords[1] <= (collisionCalcTolerance + self.__yCollisionLine['top']['y'] + self.radius / cos(self.__bAngle[2]))) and (self.cords[1] >= (-collisionCalcTolerance + self.__yCollisionLine['bottom']['y'] - self.radius / cos(self.__bAngle[2]))) and (
                    self.cords[1] <= (collisionCalcTolerance + self.__yCollisionLine['right']['y'] + self.radius / sin(self.__bAngle[2]))) and (self.cords[1] >= (-collisionCalcTolerance + self.__yCollisionLine['left']['y'] - self.radius / sin(self.__bAngle[2]))) and (self.cords[2] <= (collisionCalcTolerance + cr.plane['front'] + self.radius)) and (
                                                    self.cords[2] >= (-collisionCalcTolerance + cr.plane['back'] - self.radius))  # True if any part of the point is in a collisionRect, given a collisionCalcTolerance
            self.cubeCollision[count] = (self.cords[1] <= (collisionTolerance + self.__yCollisionLine['top']['y'] + self.radius / cos(self.__bAngle[2]))) and (self.cords[1] >= (-collisionTolerance + self.__yCollisionLine['bottom']['y'] - self.radius / cos(self.__bAngle[2]))) and (
                    self.cords[1] <= (collisionTolerance + self.__yCollisionLine['right']['y'] + self.radius / sin(self.__bAngle[2]))) and (
                                                self.cords[1] >= (-collisionTolerance + self.__yCollisionLine['left']['y'] - self.radius / sin(self.__bAngle[2]))) and (self.cords[2] <= (collisionTolerance + cr.plane['front'] + self.radius)) and (
                                                self.cords[2] >= (-collisionTolerance + cr.plane['back'] - self.radius))  # True if any part of the point is in a collisionRect, given a collisionTolerance
            self.cubeSubmersion[count] = (self.cords[1] <= (collisionTolerance + self.__yCollisionLine['top']['y'] - self.radius / cos(self.__bAngle[2]))) and (self.cords[1] >= (-collisionTolerance + self.__yCollisionLine['bottom']['y'] + self.radius / cos(self.__bAngle[2]))) and (
                    self.cords[1] <= (collisionTolerance + self.__yCollisionLine['right']['y'] - self.radius / sin(self.__bAngle[2]))) and (
                                                 self.cords[1] >= (-collisionTolerance + self.__yCollisionLine['left']['y'] + self.radius / sin(self.__bAngle[2]))) and (self.cords[2] <= (collisionTolerance + cr.plane['front'] - self.radius)) and (self.cords[2] >= (-collisionTolerance + cr.plane['back'] + self.radius))  # cubeCollision[count] but with reversed radii calcs

            if not self.cubeCollision[count]:  # reset self.collision[count] when not in front of a plane
                self.collision[count] = ''
            if (self.cords[1] <= (self.__yCollisionLine['right']['y'])) and (self.cords[1] >= (self.__yCollisionLine['left']['y'])) and (self.cords[2] <= (cr.plane['front'])) and (self.cords[2] >= (cr.plane['back'])):
                if self.cords[1] >= (self.__yCollisionLine['top']['y']):
                    self.collision[count] = 'top'
                elif self.cords[1] <= (self.__yCollisionLine['bottom']['y']):
                    self.collision[count] = 'bottom'
            elif (self.cords[1] <= self.__yCollisionLine['top']['y']) and (self.cords[1] >= self.__yCollisionLine['bottom']['y']) and (self.cords[2] <= cr.plane['front']) and (self.cords[2] >= cr.plane['back']):
                if self.cords[1] >= (self.__yCollisionLine['right']['y']):
                    self.collision[count] = 'right'
                elif self.cords[1] <= (self.__yCollisionLine['left']['y']):
                    self.collision[count] = 'left'
            elif (self.cords[1] <= (self.__yCollisionLine['top']['y'])) and (self.cords[1] >= (self.__yCollisionLine['bottom']['y'])) and (self.cords[1] <= (self.__yCollisionLine['right']['y'])) and (self.cords[1] >= (self.__yCollisionLine['left']['y'])):
                if self.cords[2] >= (cr.plane['front']):
                    self.collision[count] = 'front'
                elif self.cords[2] <= (cr.plane['back']):
                    self.collision[count] = 'back'

            # get the distance until edge/vertex collision
            if (self.collision[count] == '') or (self.__vertexState != ''):  # "why should we resolve vertex/edge collisions if the point is in front of a face on the collision rect?" hence, this if statement is used to optimize performance.
                minDist, vertexIdx = self.__getVertexDist(cr)  # get the distance to the closest vertices as well as their indexes

            # multiplier obtained through testing
            if (self.lastCollision[count] == 'right') or (self.lastCollision[count] == 'top') or (self.lastCollision[count] == 'front'):
                self.__multiplier[count] = 1
            else:
                self.__multiplier[count] = -1  # EVERYTHING is reversed for left, bottom, and back

            # detect collisions between points and planes (flat surfaces) on a collision rect (cuboid)
            if (self.__vertexState == '') and (self.collision[count] != '') and self.cubeCollisionCalc[count]:
                self.__planeCollision(count, cr)

            # detect collisions between points and edges on a SOLID collision rect (cuboid)
            elif (self.__vertexState != '') and (minDist <= (distance(cr.vertex[vertexIdx[0]], cr.vertex[vertexIdx[1]]))) and (cr.type == 's'):
                self.cords = copy.deepcopy(self.oldCords)

            # detect collisions between points and vertices (corners) on a SOLID collision rect (cuboid)
            elif (self.collision[count] == '') and (self.__vertexState == '') and (distance(cr.vertex[vertexIdx], self.cords) <= self.radius) and (cr.type == 's'):
                self.cords = copy.deepcopy(self.oldCords)
            else:
                self.colliding[count] = False

            cubeCollision = cubeCollision or self.cubeCollisionCalc[count]
            cubeSubmersion = cubeSubmersion or self.cubeSubmersion[count]
            count += 1

        if not cubeCollision:  # reset values that depend on a solid cube collision when not colliding
            self.__normalForce = [0, 0, 0]
            self.__friction = [0, 0, 0]
            self.__impulse = [0, 0, 0]
        if not cubeSubmersion:  # reset values that depend on being submerged in a liquid when not colliding
            self.__liquidUpthrust = [0, 0, 0]
            self.__liquidDrag = [0, 0, 0]
            self.__submergedVolume = 0
            self.__submergedArea = 0
            self.__submergedRadius = 0

    def __getVertexDist(self, cr):
        vertexDist = []  # distance to each edge/vertex, depending on the type of collision
        vIdx = []  # stores (specific) index values in a specific order from the collisionRect.vertex list because of this: https://drive.google.com/file/d/1llq6UTfJHZ2GJic5s8510RJoKKEBbg1Y/view?usp=drive_link
        vertexIdx = []  # final index of closest vertex index
        minDist = float('inf')  # final distance to the closest vertex
        if self.__vertexState == 'x':
            vIdx = [[0, 1], [2, 7], [3, 6], [4, 5]]
        elif self.__vertexState == 'y':
            vIdx = [[0, 7], [1, 2], [3, 4], [5, 6]]
        elif self.__vertexState == 'z':
            vIdx = [[0, 5], [1, 4], [2, 3], [6, 7]]
        else:  # when undergoing a corner collision
            for inc in range(8):
                vIdx.append(inc)  # [0, 1, 2, 3, 4, 5, 6, 7]
        if self.__vertexState != '':  # edge collision detection:
            dist = []  # distance to each vertex as indicated by vIdx
            for d in range(len(vIdx)):  # 4
                dist.append([])  # [[0, 1], [2, 7], [3, 6], [4, 5]]
                vertexDist.append(0)
                for h in range(len(vIdx[d])):  # 2
                    tempDist = distance(cr.vertex[vIdx[d][h]], self.cords)
                    if tempDist >= self.radius:  # used to prevent sqrt(-number)
                        dist[d].append(math.sqrt(tempDist ** 2 - self.radius ** 2))  # gets the distance from each vertex to the current sphere's position
                        vertexDist[d] += dist[d][h]
                    else:
                        dist[d].append(0)
        else:  # corner collision detection:
            for d in range(len(cr.vertex)):
                vertexDist.append(distance(cr.vertex[d], self.cords))
        # get the smallest value in the list
        for ve in range(len(vertexDist)):
            if vertexDist[ve] < minDist:  # if current value is less than lowest value:
                minDist = vertexDist[ve]  # set lowest value to current value
                vertexIdx = vIdx[ve]  # set index of lowest value to current index
        return minDist, vertexIdx

    def __planeCollision(self, count, cr):
        if (self.collision[count] == 'right') or (self.collision[count] == 'left'):
            self.__bAngle[2] -= math.pi / 2  # shift angle by 90° since perpendicular surfaces to the collision rect (left & right) are, well... perpendicular (to top & bottom). reason this is subtraction is because all movement is reversed since it's, well... perpendicular.
        self.__collAngle = copy.deepcopy(self.__bAngle)
        if abs(math.degrees(self.__bAngle[2])) < 45:
            self.__collisionState = 'y'
        else:
            self.__collisionState = 'x'
        if self.cubeCollision[count]:
            if cr.type == 's':
                self.__planeCollisionSolid(count, cr)
            elif cr.type == 'l':
                self.__planeCollisionLiquid(count, cr)

    def __planeCollisionLiquid(self, count, cr):
        # get cap volume with submerged radius, etc.
        # also disable gas upthrust for submerged parts
        submergedAmt = 0
        if (self.collision[count] == 'front') or (self.collision[count] == 'back'):
            submergedAmt = abs((cr.plane[self.collision[count]] + (self.__multiplier[count] * self.radius) - self.cords[2]))  # TODO: check out the maths for this here:
        elif self.__collisionState == 'y':
            submergedAmt = abs((self.__yCollisionLine[self.collision[count]]['y'] + (self.__multiplier[count] * self.radius / cos(self.__bAngle[2])) - self.cords[1]) * cos(self.__bAngle[2]))  # TODO: check out the maths for this here:
        elif self.__collisionState == 'x':
            submergedAmt = abs((self.__xCollisionLine[self.collision[count]]['x'] - (self.__multiplier[count] * self.radius / sin(self.__bAngle[2])) - self.cords[0]) * sin(self.__bAngle[2]))
        self.__submergedVolume = capVolume(submergedAmt, self.radius)
        self.__submergedArea = capArea(submergedAmt, self.radius)
        self.__submergedRadius = submergedAmt
        if self.cubeSubmersion[count]:  # if fully submerged
            self.__submergedVolume = copy.deepcopy(self.__volume)
        if self.__submergedRadius > self.radius:  # if half of sphere is submerged
            self.__submergedArea = self.__halfArea
            self.__submergedRadius = self.radius
        for axis in range(3):
            self.__liquidUpthrust[axis] = cr.density * -globalVars['gField'][axis] * self.__submergedVolume  # U = pgV
            self.__liquidDrag[axis] = (0.5 * cr.viscosity * (self.velocity[axis] ** 2) * -getSign(self.velocity[axis]) * self.__submergedArea)  # Drag = 1/2 cpAv²

    def __planeCollisionSolid(self, count, cr):
        if str(self.sf) == 'sticky':
            self.cords = copy.deepcopy(self.oldCords)  # "stick" cords to oldCords
        else:
            if (self.collision[count] == 'top') or (self.collision[count] == 'right') or (self.collision[count] == 'bottom') or (self.collision[count] == 'left'):  # colliding with top/right/bottom/left plane
                # TODO: check out this link to see why I need the logic below:
                if self.__collisionState == 'y':
                    if not self.colliding[count]:
                        self.colliding[count] = True
                        self.cords[1] = self.__yCollisionLine[self.collision[count]]['y'] + (self.__multiplier[count] * self.radius / cos(self.__bAngle[2]))
                        self.oldCords[0] = copy.deepcopy(self.cords[0])
                        self.oldCords[1] = copy.deepcopy(self.cords[1])
                        resultP = (self.mass * self.velocity[0] * cos(self.__bAngle[2])) + (self.mass * self.velocity[1] * sin(self.__bAngle[2]))
                        self.__impulse[0] = resultP * physicsTime * cos(self.__bAngle[2]) * self.e
                        self.__impulse[1] = resultP * physicsTime * sin(self.__bAngle[2]) * self.e
                    else:
                        self.__impulse = [0, 0, 0]
                        self.cords[1] = self.__yCollisionLine[self.collision[count]]['y'] + (self.__multiplier[count] * self.radius / cos(self.__bAngle[2]))
                elif self.__collisionState == 'x':
                    if not self.colliding[count]:
                        self.colliding[count] = True
                        self.cords[0] = self.__xCollisionLine[self.collision[count]]['x'] - (self.__multiplier[count] * self.radius / sin(self.__bAngle[2]))
                        self.oldCords[0] = copy.deepcopy(self.cords[0])
                        self.oldCords[1] = copy.deepcopy(self.cords[1])
                        resultP = (self.mass * self.velocity[0] * cos(self.__bAngle[2])) + (self.mass * self.velocity[1] * sin(self.__bAngle[2]))
                        self.__impulse[0] = resultP * physicsTime * cos(self.__bAngle[2]) * self.e
                        self.__impulse[1] = resultP * physicsTime * sin(self.__bAngle[2]) * self.e
                    else:
                        self.__impulse = [0, 0, 0]
                        self.cords[0] = self.__xCollisionLine[self.collision[count]]['x'] - (self.__multiplier[count] * self.radius / sin(self.__bAngle[2]))
            elif (self.collision[count] == 'front') or (self.collision[count] == 'back'):
                if not self.colliding[count]:
                    self.colliding[count] = True
                    self.cords[2] = cr.plane[self.collision[count]] + (self.radius * self.__multiplier[count])
                    self.oldCords[2] = copy.deepcopy(self.cords[2])
                else:
                    self.cords[2] = cr.plane[self.collision[count]] + (self.radius * self.__multiplier[count])


# class for cylinders (joints) connecting spheres
class Joint:
    def __init__(self, show, origLength, stiffness, pOne, pTwo, bounciness, maxStrain, gameObj):
        self.pOne = pOne  # index of first connected point
        self.pTwo = pTwo  # index of second connected point
        self.__height = distance(gameObj.points[self.pOne].cords, gameObj.points[self.pTwo].cords)  # current size of joint
        self.__oldHeight = self.__height  # size of joint from previous frame
        self.radius = jointRadius
        self.stiffness = stiffness
        self.dampingConst = bounciness
        self.cords = [0, 0, 0]
        self.angle = [0, 0, 0]
        self.show = show
        if origLength == '':
            self.origLength = copy.deepcopy(self.__height)
        else:
            self.origLength = origLength
        self.maxStrain = maxStrain  # maximum length of joint before breaking
        self.diff = [0, 0, 0]  # caching variable, avoiding repeat calcs to increase performance
        self.constrainForce = [0, 0, 0]
        self.__damping = [0, 0, 0]
        self.__dampingCoef = 1  # coefficient of damping independent of globalVars['damping']
        if self.show:
            self.cylinder = vizshape.addCylinder(1, 1, slices=jointResolution)  # make the joint visible if shown
        self.__volume = math.pi * (self.radius ** 2) * self.__height

    # update the position and appearance of the joint
    def update(self):
        if self.__height >= (self.origLength * self.maxStrain):
            pass
            # self.snap()  # MASSIVE WIP

        self.diff = displacement(game.points[self.pOne].cords, game.points[self.pTwo].cords)
        self.__oldHeight = copy.deepcopy(self.__height)
        if (self.pOne > self.pTwo) and (game.diff[self.pTwo][self.pOne] != 0):  # must be used to compensate for "also don't get distance between 2 points if you already have it!" as seen in getDist() from the Main class
            self.__height = game.diff[self.pTwo][self.pOne]
        elif game.diff[self.pOne][self.pTwo] != 0:
            self.__height = game.diff[self.pOne][self.pTwo]
        self.radius = math.sqrt(self.__volume / (math.pi * self.__height))  # r = sqrt(v / πh)
        # no need to reassign volume here since it always stays constant

    def draw(self):
        if self.show:
            self.cylinder.setScale([self.radius, self.__height, self.radius])  # change visual of cylinder
            self.cords = midpoint(game.points[self.pOne], game.points[self.pTwo])
            self.cylinder.setEuler(getEulerAngle(game.points[self.pOne].cords, game.points[self.pTwo].cords))

            self.cylinder.setPosition(self.cords)

    # constrain points connected to this joint
    def constrain(self):
        if (self.__height != self.origLength) and (self.__height != 0):
            for u in range(3):
                self.constrainForce[u] = self.stiffness * (self.diff[u] / self.__height) * (self.origLength - self.__height)  # check out the maths for this using this link:
                self.__damping[u] = self.__dampingCoef * self.dampingConst * abs((self.diff[u] / self.__height) * (self.__oldHeight - self.__height)) * getSign(game.points[self.pOne].velocity[u] - game.points[self.pTwo].velocity[u]) * physicsTime  # damping force = damping constant * change in joint length (relative to both points) * relative direction
        for i in range(3):
            game.points[self.pOne].constrainForce[i] += self.constrainForce[i] - self.__damping[i]
            game.points[self.pTwo].constrainForce[i] -= self.constrainForce[i] - self.__damping[i]  # negative due to Newton's 3rd law

    # break the joint after extending a specified distance (MASSIVE WIP)
    def __snap(self):
        # radius cannot be less than 0.05 due to floating point error
        if (game.points[self.pOne].radius / 2) < minRadius:
            pointRad = minRadius
        else:
            pointRad = game.points[self.pOne].radius / 2
        game.addPoint(Point(pointRad, game.points[self.pOne].density, True, self.pOne))
        game.points[self.pOne].setRadiusDensity(pointRad, game.points[self.pOne].density)
        game.points[self.pOne].disabledPointCollisions = [len(game.points) - 1]
        game.points[-1].cords = copy.deepcopy(self.cords)
        game.points[-1].oldCords = copy.deepcopy(self.cords)
        game.joints.append(Joint(True, self.origLength * 2, self.stiffness / 8, self.pOne, len(game.points) - 1, self.dampingConst, self.maxStrain * 2))  # maxStrain is increased since whenever materials break, since they pass their elastic limit in reality
        game.points[self.pOne].cloth = self.pOne * len(game.points)  # unique cloth key
        game.points[-1].cloth = self.pOne * len(game.points)
        game.updateLists()

        if (game.points[self.pTwo].radius / 2) < minRadius:
            pointRad = minRadius
        else:
            pointRad = game.points[self.pTwo].radius / 2
        self.stiffness /= 8
        game.addPoint(Point(pointRad, game.points[self.pTwo].density, True, self.pTwo))
        game.points[self.pTwo].setRadiusDensity(pointRad, game.points[self.pTwo].density)
        self.pOne = len(game.points) - 1
        game.points[-1].cords = copy.deepcopy(self.cords)
        game.points[-1].oldCords = copy.deepcopy(game.points[-1].cords)
        game.points[self.pTwo].disabledPointCollisions = [len(game.points) - 1]
        self.origLength *= self.maxStrain
        self.origLength *= 2
        self.diff = [0, 0, 0]
        self.__height = copy.deepcopy(self.origLength)
        self.__oldHeight = copy.deepcopy(self.__height)
        self.maxStrain *= 2
        game.points[self.pTwo].cloth = self.pTwo * len(game.points)  # unique cloth key
        game.points[-1].cloth = self.pTwo * len(game.points)
        game.updateLists()


class CollisionRect:
    def __init__(self, size, cords, angle, density, viscosity, dragConst, transparency, rectType, *hide):
        self.type = rectType  # solid or liquid
        self.angle = angle
        self.__vertexAngle = [0, 0, 0]
        self.size = size
        self.show = False
        if not hide:
            self.show = True
            self.__rect = vizshape.addBox([1, 1, 1])
            self.__rect.setScale(self.size)
        self.cords = cords
        self.density = density
        self.dragConst = dragConst
        self.viscosity = viscosity
        self.transparency = transparency
        self.vertex = []  # [x, y, z] -> [['right', 'top', 'front'], ['left', 'top', 'front'], ['left', 'bottom', 'front'], ['left', 'bottom', 'back'], ['left', 'top', 'back'], ['right', 'top', 'back'], ['right', 'bottom', 'back'], ['right', 'bottom', 'front']]
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
        self.update()

    def update(self):
        if self.show:
            self.__rect.setScale(self.size)
            self.__rect.setPosition(self.cords)
            self.__rect.setEuler(math.degrees(self.angle[0]), math.degrees(self.angle[1]), math.degrees(self.angle[2]))
            self.__rect.alpha(self.transparency)
        sizeMultiplier = [0.5, 0.5, 0.5]
        multiplier = 1
        self.__vertexAngle = math.atan(self.size[1] / self.size[0])
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
            xySize = math.sqrt((self.size[0]) ** 2 + (self.size[1]) ** 2)
            for i in range(3):
                if i == 0:  # x
                    tempVertex[i] = self.cords[i] + (xySize * sizeMultiplier[i] * cos(self.__vertexAngle + (multiplier * self.angle[2])))
                elif i == 1:  # y
                    tempVertex[i] = self.cords[i] + (xySize * sizeMultiplier[i] * sin(self.__vertexAngle + (multiplier * self.angle[2])))
                elif i == 2:  # z
                    tempVertex[i] = self.cords[i] + (self.size[i] * sizeMultiplier[i])

            self.vertex.append(tempVertex)

        self.plane['right'] = self.cords[0] + (self.size[0] / 2)
        self.plane['left'] = self.cords[0] - (self.size[0] / 2)
        self.plane['top'] = self.cords[1] + (self.size[1] / 2)
        self.plane['bottom'] = self.cords[1] - (self.size[1] / 2)
        self.plane['front'] = self.cords[2] + (self.size[2] / 2)
        self.plane['back'] = self.cords[2] - (self.size[2] / 2)

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


game = Main()

# makes a cube using points and joints
if not imports:
    cube = True
    if cube:
        cubeSize = 8
        cubeRes = 3
        pointRadius = 0.1
        for ve in range(cubeSize):
            if ve > 7:
                if ve == 8:
                    game.addPoint(Point(0.1, 1000, False))  # central point
                else:
                    game.addPoint(Point(0.1, 1000, False))
            else:
                game.addPoint(Point(0.1, 1000, True))
            game.points[ve].cloth = 'cube'
        game.points[0].cords = [1, 2.5, 1]  # top-front-right
        game.points[0].oldCords = [1, 2.5, 1]
        game.points[1].cords = [1, 2.5, -1]  # top-back-right
        game.points[1].oldCords = [1, 2.5, -1]
        game.points[2].cords = [-1, 2.5, -1]  # top-back-left
        game.points[2].oldCords = [-1, 2.5, -1]
        game.points[3].cords = [-1, 2.5, 1]  # top-front-left
        game.points[3].oldCords = [-1, 2.5, 1]
        game.points[4].cords = [1, 0.5, 1]
        game.points[4].oldCords = [1, 0.5, 1]
        game.points[5].cords = [1, 0.5, -1]
        game.points[5].oldCords = [1, 0.5, -1]
        game.points[6].cords = [-1, 0.5, -1]
        game.points[6].oldCords = [-1, 0.5, -1]
        game.points[7].cords = [-1, 0.5, 1]
        game.points[7].oldCords = [-1, 0.5, 1]

        for j in range(len(game.points)):
            for jo in range(len(game.points)):
                if (j != jo) and (jo > j):  # performance optimisation: only go through unique combinations of j and jo (e.g. [1, 5] and [5, 0] are unique, but [1, 5] and [5, 1] are not)
                    if jo <= 7:
                        game.joints.append(Joint(True, '', globalVars['springConst'], j, jo, globalVars['damping'], globalVars['strain'], game))
                    else:
                        game.joints.append(Joint(True, '', globalVars['springConst'], j, jo, globalVars['damping'], globalVars['strain'], game))
        # game.addPoint(Point(0.1, 1000))

    game.addPoint(Point(0.6, 1000, True))
    game.addPoint(Point(0.4, 1000, True))

    for p in range(len(game.points)):
        game.points[p].cords[1] += 50
        game.points[p].oldCords[1] += 50
        game.points[p].cords[0] -= 20
        game.points[p].oldCords[0] -= 20
    game.points[-1].cords[1] += 10
    game.points[-1].oldCords[1] += 10
    game.points[-2].cords[1] += 10
    game.points[-2].oldCords[1] += 10
    game.points[-1].cords[0] -= 10
    game.points[-1].oldCords[0] -= 10
    game.points[-2].cords[0] -= 20
    game.points[-2].oldCords[0] -= 20

    slantedSurface = False
    if slantedSurface:
        surfaceRes = 400
        radius = 5
        for s in range(surfaceRes):
            x = radius * s / surfaceRes
            try:
                y = math.sqrt(radius - (x ** 2))
                game.collisionRect.append(CollisionRect((10, 10, 10), [x, y + 10, 0], [0, 0, math.radians((80 * s / surfaceRes) + 5)], 1000, 1, 0.8, 1, 's'))
            except ValueError:
                continue
    game.collisionRect.append(CollisionRect((100, 50, 50), [-60, 0, 0], [math.radians(0), math.radians(0), math.radians(0.001)], 1000, 10, 1, 0.8, 's'))  # CANNOT be negative angle or above 90 (make near-zero for an angle of 0)
    game.collisionRect.append(CollisionRect((100, 50, 50), [60, 0, 0], [math.radians(0), math.radians(0), math.radians(30)], 1000, 10, 1, 0.8, 's'))
    game.collisionRect.append(CollisionRect((50, 50, 50), [170, 0, 0], [math.radians(0), 0, math.radians(0.001)], 2000, 1, 1, 0.5, 'l'))

# draw the borders (which are hidden collisionRects)
game.collisionRect.append(CollisionRect((borderSize[0], 1, borderSize[2]), [0, borderHeight, 0], [0, 0, math.radians(0.001)], 1000, 10, 1, 1, 's', False))
game.collisionRect.append(CollisionRect((borderSize[0], borderSize[1], 1), [0, borderHeight + borderSize[1] / 2, borderSize[2] / 2], [0, 0, math.radians(0.001)], 1000, 10, 1, 1, 's', False))
game.collisionRect.append(CollisionRect((borderSize[0], borderSize[1], 1), [0, borderHeight + borderSize[1] / 2, -borderSize[2] / 2], [0, 0, math.radians(0.001)], 1000, 10, 1, 1, 's', False))
game.collisionRect.append(CollisionRect((1, borderSize[1], borderSize[2]), [borderSize[0] / 2, borderHeight + borderSize[1] / 2, 0], [0, 0, math.radians(0.001)], 1000, 10, 1, 1, 's', False))
game.collisionRect.append(CollisionRect((1, borderSize[1], borderSize[2]), [-borderSize[0] / 2, borderHeight + borderSize[1] / 2, 0], [0, 0, math.radians(0.001)], 1000, 10, 1, 1, 's', False))
for cr in range(5):
    game.collisionRect[-cr - 1].sf = 4  # make points on the collisionRect stop quicker (depends on the point's surface friction as well)

game.initLists()  # WARNING: must ALWAYS run this ONCE before vizact.ontimer
vizact.ontimer(1 / calcRate, game.main)  # calculate physics game.time times each second
vizact.ontimer(1 / renderRate, game.render)  # render objects game.render times each second
