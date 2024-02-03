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


# Main class for main.py
class Main:
    def __init__(self):
        # commented code below used for testinglsd
        # vizshape.addGrid()
        # vizshape.addGrid(axis=vizshape.AXIS_X)
        # vizshape.addBox((1, 0.01, 1)).setPosition(0, 0, 0)
        # vizshape.addBox((1, 0.01, 1)).setPosition(0, -1, 0)
        # vizshape.addBox((1, 0.01, 1)).setPosition(0, -2, 0)
        self.gridFloor = 0  # y-coordinate of test collision
        self.points = []  # list of points for the whole program
        self.joints = []  # list of joints for the whole program
        self.texts = []
        self.GUI = {  # dictionary of all GUIs and their possible forms (dimensions, axes, etc.)
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
        self.dragP = [None, None]  # last clicked point index
        self.dragC = [None, None]  # last clicked controller index for the last clicked point
        self.lastP = [None, None]  # last clicked point that always retains its value for "recalling" objects to the controller
        self.theForceJoint = False  # True if the force is being used
        self.pause = False  # pauses physics
        self.pHeld = False  # stores if 'p' is held down
        self.rHeld = False  # stores if 'r' is held down
        self.lHeld = False  # stores if 'l' is held down
        self.GUISelector = False  # stores if the button to summon the GUI selector is held
        self.returnHeld = False  # stores if 'return' is held down
        self.selectHeld = [False, False]  # stores if the select button is held on either controller
        self.collP = [None, None]  # stores the indexes of a point that is colliding with either controller
        self.anim = []  # stores all animations specific to the Main class
        self.animeScale = [1, 1]  # visual scale of animations
        self.animeScaleSpeed = 0  # rate at which animations scale
        self.animeColor = [[0, 0, 0], [0, 0, 0]]  # color of each animation
        self.GUIType = None  # holds the return value of GUISelector to create relevant GUI(s)
        self.clickTime = [0, 0]  # stores time since 'select' was pressed for both controllers in order for double-click detection
        self.relPos = [[0, 0, 0], [0, 0, 0]]  # stores the relative position of selected points with either controller
        self.clothData = {}
        # self.cloths = {}
        self.tutorialTexts = {}
        # self.tutorialNames = {}
        self.importTutorials()

    # initialize all the lists that depend on self.points and self.collisionRect
    def initLists(self):
        for p in range(len(self.points)):
            self.GUI.update({p: {'slider': {'radius': None, 'density': None}, 'manual': {'radius': None, 'density': None}}})
            for _ in range(len(self.collisionRect)):
                self.points[p].collision.append('')
                self.points[p].lastCollision.append('')
                self.points[p].colliding.append(False)
                self.points[p].cubeCollision.append(False)
                self.points[p].cubeCollisionCalc.append(False)
                self.points[p].cubeSubmersion.append(False)
                self.points[p].multiplier.append(1)

            self.diff.append([])
            for _ in range(len(self.points)):
                self.diff[p].append(0)
        self.lastP = [len(self.points) - 1, len(self.points) - 2]
        self.updateJointConnections()
        self.updateCloths()
        # below is the code I used to get the relative size of the JetBrains font to the game scene
        # myT = viz.addText3D('abcd', fontSize=1.69 / 4)  # OBSERVATION: font size of 1.69 has the width of 1 unit
        # myT = viz.addText3D('a\nb\nc', fontSize=1)  # OBSERVATION: font size of 1 has the height of 1 unit
        # myT.font("JetBrainsMono-2.304\\fonts\\ttf\\JetBrainsMono-Medium.ttf")

    def updateLists(self):
        self.GUI.update({len(self.points) - 1: {'slider': {'radius': None, 'density': None}, 'manual': {'radius': None, 'density': None}}})
        for _ in range(len(self.collisionRect)):
            self.points[-1].collision.append('')
            self.points[-1].lastCollision.append('')
            self.points[-1].colliding.append(False)
            self.points[-1].cubeCollision.append(False)
            self.points[-1].cubeCollisionCalc.append(False)
            self.points[-1].cubeSubmersion.append(False)
            self.points[-1].multiplier.append(1)
        self.diff.append([])
        for p in range(len(self.points) - 1):
            self.diff[p].append(0)
        for p in range(len(self.points)):
            self.diff[-1].append(0)
        self.updateJointConnections()
        self.updateCloths()

    # put the indexes of all points into a list
    def updateCloths(self):
        global clothNames
        for p in range(len(self.points)):
            if self.points[p].cloth == '':
                clothNames.update({f'{p}': None})
                self.clothData.update({f'{p}': [p]})
            elif self.clothData.get(self.points[p].cloth) is None:
                clothNames.update({self.points[p].cloth: None})
                self.clothData.update({self.points[p].cloth: []})
            if (self.points[p].cloth != '') and (not checkInList(self.clothData[self.points[p].cloth], p)):
                self.clothData[self.points[p].cloth].append(p)
        # cloths = self.cloths

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
        print(self.GUI['Tutorials'])
        f.close()

    def tpCloth(self, cloth, cords, c, tpType):
        cordDiff = []
        if tpType == 'cloth':
            pIdx = self.clothData[cloth][0]
            self.points[pIdx].cords = copy.deepcopy(controls.hand[c].cords)
            for co in range(3):
                cordDiff.append(self.points[pIdx].cords[co] - self.points[pIdx].oldCords[co])
            if cloth != '':
                for p in self.clothData[f'{cloth}']:
                    if p != pIdx:
                        for cor in range(3):
                            self.points[p].cords[cor] += cordDiff[cor]
                            self.points[p].oldCords[cor] += cordDiff[cor]
            self.points[pIdx].oldCords = copy.deepcopy(cords)
        elif tpType == 'point':
            for co in range(3):
                cordDiff.append(self.points[cloth].cords[co] - self.points[cloth].oldCords[co])
            if self.points[cloth].cloth != '':
                for p in self.clothData[f'{self.points[cloth].cloth}']:
                    if p != self.lastP[c]:
                        for cor in range(3):
                            self.points[p].cords[cor] += cordDiff[cor]
                            self.points[p].oldCords[cor] += cordDiff[cor]
            self.points[cloth].oldCords = copy.deepcopy(cords)

    def updateJointConnections(self):
        for p in range(len(self.points)):
            tempInt = 0
            for j in self.joints:
                if (j.pOne == p) or (j.pTwo == p):
                    tempInt += 1
            self.points[p].jointConnections = tempInt

    def main(self):
        global physicsTime  # must be globalised since gameSpeed can be changed by the user from the GUI selector
        physicsTime = calcRate * (1 / globalVars['gameSpeed'])  # update the value of physicsTime based on gameSpeed
        for c in range(controlsConf.controllerAmt):
            # pause if the 'pause' button is pressed
            if (not self.pHeld) and buttonPressed('pause', controlsConf.controllers[c], c):
                self.pause = not self.pause  # reverse the boolean value of self.pause
                if buttonPressed('pause', controlsConf.controllers[c], c):
                    self.pHeld = True
            elif not buttonPressed('pause', controlsConf.controllers[c], c):
                self.pHeld = False

            # summon the GUI selector if the 'GUISelector' button is pressed
            if (not self.lHeld) and buttonPressed('GUISelector', controlsConf.controllers[c], c):
                if self.GUI['GUISelector'][''][''] is None:
                    self.GUI['GUISelector'][''][''] = myGUI.GUISelector(globalVars, controls.hand[c].cords, [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                else:
                    self.GUI['GUISelector'][''][''].drawn = False
                    self.GUI['GUISelector'][''][''].unDraw()
                if buttonPressed('GUISelector', controlsConf.controllers[c], c):
                    self.lHeld = True
            elif not buttonPressed('GUISelector', controlsConf.controllers[c], c):
                self.lHeld = False

        self.dragPoint()  # runs the function that detects if controller is selecting a point so that it can be "dragged" along with the controller

        for p in range(len(self.points)):
            self.points[p].sf = globalVars['friction']  # update each point's local value of friction based on globalVars['friction'], for the same reason physicsTime is updated
            # if (self.points[p].cords[1] - self.points[p].radius) <= self.gridFloor:
            #     self.points[p].cords[1] = self.gridFloor + self.points[p].radius
            #     self.points[p].oldCords[1] = self.points[p].cords[1]
            # detect collisions with other points
            for po in range(len(self.points)):
                if (po > p) and (p != po) and (self.points[p].pointCollisions[0] != po) and (self.points[po].pointCollisions[0] != p):  # performance optimisation: only go through unique combinations of p and po (e.g. [1, 5] and [5, 0] are unique, but [1, 5] and [5, 1] are not)
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

            self.points[p].move()

        self.getDist()  # cache the distance between each point

        # update each joint
        for j in range(len(self.joints)):
            self.joints[j].stiffness = globalVars['springConst']  # set stiffness for the same reason as physicsTime
            self.joints[j].dampingConst = globalVars['damping']  # set dampingConst for the same reason as physicsTime
            # self.joints[j].maxStrain = globalVars['strain']  # set strain for the same reason as physicsTime
            self.joints[j].update()
            if not self.pause:
                self.joints[j].constrain()  # apply a force to each point from each joint

    def render(self):
        self.updateGUI()  # update all GUIs
        controls.main()  # runs the main function in the current control (keyboard/VR) setting
        for p in self.points:
            p.draw()
        for j in self.joints:
            j.draw()
        for g in self.GUI:
            for gu in self.GUI[g]:
                for gui in self.GUI[g][gu]:
                    if self.GUI[g][gu][gui] is not None:
                        self.GUI[g][gu][gui].draw(controls.camCords)

    # used to drag points around using pointer/controller
    def dragPoint(self):
        if mode == 'vr':
            print(controlsConf.controllers[0].getButtonState() % touchpad, controlsConf.controllers[1].getButtonState() % touchpad)  # prints the current button being pressed for each controller

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
                if detectCollision(self.points[p].radius, controls.hand[c].radius, self.points[p].cords, controls.hand[c].cords):
                    self.collP[c] = p  # set the collision point to the current point's index
                    if selectP(c):  # detect if the select button is being pressed, depending on the controller mode
                        if not self.selectHeld[c]:
                            self.selectHeld[c] = True
                            for axis in range(3):
                                self.relPos[c][axis] = self.points[p].cords[axis] - controls.hand[c].cords[axis]
                            cords = controls.hand[c].cords  # set cords to the current controller's cords to shorten the below for increased readability
                            if self.clickTime[c] < 0.25:  # if there's a double click, summon sliders (if in VR) or manual inputs (if in keyboard/mouse) to change the density and radius of the double-clicked point
                                if self.GUI[p]['slider']['radius'] is None:  # only summon if GUI is empty
                                    if mode == 'vr':
                                        self.GUI[p]['slider']['radius'] = myGUI.Slider(0, self.points[p].radius, self.points[p].origRadius, [cords[0], cords[1] + 0.5, cords[2]], 10, 0.1, maxRadius, minRadius, 'Radius', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                                    else:
                                        self.GUI[p]['slider']['radius'] = myGUI.Manual(0, self.points[p].radius, self.points[p].origRadius, [cords[0], cords[1] + 0.5, cords[2]], 'Radius', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                                if self.GUI[p]['slider']['density'] is None:  # only summon if GUI is empty
                                    if mode == 'vr':
                                        self.GUI[p]['slider']['density'] = myGUI.Slider(0, self.points[p].density, self.points[p].origDensity, [cords[0], cords[1] - 0.5, cords[2]], 10, 0.1, 10000, 1, 'Density', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                                        self.GUI[p]['slider']['density'].closeButton.unDraw()  # only one 'X' needs to be rendered, since there are two Xs within each other
                                        self.GUI[p]['slider']['density'].closeButton.cords[1] = cords[1] + 1  # offset this 'X' to be within the other 'X' so that they both act as one button to dismiss both radius and density GUIs simultaneously
                                    else:
                                        self.GUI[p]['slider']['density'] = myGUI.Manual(0, self.points[p].density, self.points[p].origDensity, [cords[0], cords[1] - 0.5, cords[2]], 'Density', [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
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
            if self.dragP[c] is not None:
                for axis in range(3):
                    self.points[self.dragP[c]].cords[axis] = controls.hand[c].cords[axis] + self.relPos[c][axis]  # set the point position to the controller that grabbed said point's position
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
            # recalls the last clicked point to the controller's position
            if buttonPressed('recall', controlsConf.controllers[c], c):
                if theForce and (not self.theForceJoint):
                    self.joints.append(Joint(False, 0, 0.01, None, self.lastP[c], True, c))
                    self.theForceJoint = True
                # set cords of point to user pointer/hand
                elif not theForce:
                    self.points[self.lastP[c]].cords = copy.deepcopy(controls.hand[c].cords)
                    if not self.rHeld:
                        # cordDiff = []
                        # for co in range(3):
                        #     cordDiff.append(self.points[self.lastP[c]].cords[co] - self.points[self.lastP[c]].oldCords[co])
                        # for po in range(len(self.points)):
                        #     if (po != self.lastP[c]) and (self.points[po].cloth == self.points[self.lastP[c]].cloth) and (self.points[self.lastP[c]].cloth != ''):
                        #         for cor in range(3):
                        #             self.points[po].cords[cor] += cordDiff[cor]
                        #             self.points[po].oldCords[cor] += cordDiff[cor]
                        # self.points[self.lastP[c]].oldCords = copy.deepcopy(controls.hand[c].cords)
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

    def sphereCollision(self, pOne, pTwo):
        angle = getThreeDAngle(self.points[pOne].cords, self.points[pTwo].cords, 'y')
        for v in range(3):
            self.points[pOne].cords[v] = self.points[pOne].oldCords[v] - self.points[pOne].oldVelocity[v] * self.points[pOne].e
            self.points[pTwo].cords[v] = self.points[pTwo].oldCords[v] - self.points[pTwo].oldVelocity[v] * self.points[pTwo].e

    # get the distance between each point
    def getDist(self):
        for p in range(len(self.points)):
            for po in range(len(self.points)):
                sumR = self.points[p].radius + self.points[po].radius
                disp = displacement(self.points[p].cords, self.points[po].cords)
                if (((disp[0] < sumR) or (disp[1] < sumR) or (disp[2] < sumR)) or (self.points[p].cloth != '') and (self.points[po].cloth != '')) and (p != po) and (po > p):  # don't detect for collisions if any diff value is greater than the sum of both points' radii. also don't get distance between 2 points if you already have it!
                    self.diff[p][po] = diffDistance(disp[0], disp[1], disp[2])

    def addPoint(self, point):
        self.points.append(point)
        for p in range(len(self.points)):
            self.points[p].pIdx = p

    def updateGUI(self):
        for g in self.GUI:
            for gt in self.GUI[g]:
                for gta in self.GUI[g][gt]:
                    if self.GUI[g][gt][gta] is not None:
                        if self.GUI[g][gt][gta].drawn:
                            if g == 'GUISelector':
                                self.GUIType = self.GUI[g][gt][gta].main()
                            else:
                                if type(g) is not int:
                                    if (type(globalVars[g]) is list) and ((gt == 'slider') or (gt == 'manual')):
                                        self.GUI[g][gt][gta].setVar(globalVars[g][self.GUI[g][gt][gta].xyz])
                                        globalVars[g][self.GUI[g][gt][gta].xyz] = self.GUI[g][gt][gta].main()
                                    elif g != 'Tutorials':
                                        self.GUI[g][gt][gta].setVar(globalVars[g])
                                        globalVars[g] = self.GUI[g][gt][gta].main()
                                    else:
                                        self.GUI[g][gt][gta].main()
                                else:
                                    if gta == 'radius':
                                        self.GUI[g][gt][gta].setVar(self.points[g].radius)
                                        self.points[g].setRadiusDensity(self.GUI[g][gt][gta].main(), self.points[g].density)
                                    elif gta == 'density':
                                        self.GUI[g][gt][gta].setVar(self.points[g].density)
                                        self.points[g].setRadiusDensity(self.points[g].radius, self.GUI[g][gt][gta].main())
                        else:
                            self.GUI[g][gt][gta] = None

        if self.GUIType is not None:
            # print(self.GUIType)
            if self.GUIType[0] == 'cloths':
                self.tpCloth(self.GUIType[1][0], controls.hand[0].cords, 0, 'cloth')
            elif self.GUIType[0] == 'Tutorials':
                if self.GUI[self.GUIType[0]][''][self.GUIType[1][0]] is None:
                    self.GUI[self.GUIType[0]][''][self.GUIType[1][0]] = myGUI.Tutorial(controls.hand[0].cords, [10, 0.2], self.tutorialTexts[self.GUIType[1][0]], [], 0.3, [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
            elif self.GUIType[1][0] == 'Slider':
                if self.GUI[self.GUIType[0]][self.GUIType[1][0].lower()][self.GUIType[1][1]] is not None:
                    self.GUI[self.GUIType[0]][self.GUIType[1][0].lower()][self.GUIType[1][1]].unDraw()
                    self.GUI[self.GUIType[0]][self.GUIType[1][0].lower()][self.GUIType[1][1]] = None
                if self.GUIType[1][1] == 'X':
                    xyz = 0
                elif self.GUIType[1][1] == 'Y':
                    xyz = 1
                else:
                    xyz = 2
                if type(globalVars[self.GUIType[0]]) is list:  # if the quantity is a vector, xyz effects visuals and direction
                    self.GUI[self.GUIType[0]][self.GUIType[1][0].lower()][self.GUIType[1][1]] = myGUI.Slider(xyz, globalVars[self.GUIType[0]][xyz], defaultGlobalVars[self.GUIType[0]][xyz], controls.hand[0].cords, 5, 0.15, globalRanges[self.GUIType[0]][0], globalRanges[self.GUIType[0]][1], self.GUIType[0], [controlsConf.controllers[0], controls.hand[0]],
                                                                                                             [controlsConf.controllers[1], controls.hand[1]])
                else:  # if the quantity is a scalar, xyz only effects visuals
                    self.GUI[self.GUIType[0]][self.GUIType[1][0].lower()][self.GUIType[1][1]] = myGUI.Slider(xyz, globalVars[self.GUIType[0]], defaultGlobalVars[self.GUIType[0]], controls.hand[0].cords, 5, 0.15, globalRanges[self.GUIType[0]][0], globalRanges[self.GUIType[0]][1], self.GUIType[0], [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
            elif self.GUIType[1][0] == 'Dial':
                self.GUIType[1].append(self.GUIType[1][1])
                if self.GUI[self.GUIType[0]][self.GUIType[1][0].lower()][self.GUIType[1][2]] is not None:
                    self.GUI[self.GUIType[0]][self.GUIType[1][0].lower()][self.GUIType[1][2]].unDraw()
                    self.GUI[self.GUIType[0]][self.GUIType[1][0].lower()][self.GUIType[1][2]] = None
                if self.GUIType[1][1] == '2D':
                    if self.GUIType[1][2] == 'XZ':
                        xyz = 0
                    elif self.GUIType[1][2] == 'XY':
                        xyz = 1
                    else:
                        xyz = 2
                    self.GUI[self.GUIType[0]][self.GUIType[1][0].lower()][self.GUIType[1][2]] = myGUI.Dial(xyz, globalVars[self.GUIType[0]], defaultGlobalVars[self.GUIType[0]], controls.hand[0].cords, 5, 0.15, [globalRanges[self.GUIType[0]][0], globalRanges[self.GUIType[0]][0]], [globalRanges[self.GUIType[0]][1], globalRanges[self.GUIType[0]][1]], self.GUIType[0],
                                                                                                           [controlsConf.controllers[0], controls.hand[0]],
                                                                                                           [controlsConf.controllers[1], controls.hand[1]])
                elif self.GUIType[1][1] == '3D':
                    self.GUI[self.GUIType[0]][self.GUIType[1][0].lower()][self.GUIType[1][2]] = myGUI.Dial(0, globalVars[self.GUIType[0]], defaultGlobalVars[self.GUIType[0]], controls.hand[0].cords, 5, 0.15, [globalRanges[self.GUIType[0]][0], globalRanges[self.GUIType[0]][0], globalRanges[self.GUIType[0]][0]],
                                                                                                           [globalRanges[self.GUIType[0]][1], globalRanges[self.GUIType[0]][1], globalRanges[self.GUIType[0]][1]], self.GUIType[0],
                                                                                                           [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
            elif self.GUIType[1][0] == 'Manual':
                if self.GUIType[1][1] == 'X':
                    xyz = 0
                elif self.GUIType[1][1] == 'Y':
                    xyz = 1
                else:
                    xyz = 2
                # print(self.GUIType)
                if type(globalVars[self.GUIType[0]]) is list:
                    self.GUI[self.GUIType[0]][self.GUIType[1][0].lower()][self.GUIType[1][1]] = myGUI.Manual(xyz, globalVars[self.GUIType[0]][xyz], defaultGlobalVars[self.GUIType[0]][xyz], controls.hand[0].cords, self.GUIType[0], [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])
                else:
                    self.GUI[self.GUIType[0]][self.GUIType[1][0].lower()][self.GUIType[1][1]] = myGUI.Manual(xyz, globalVars[self.GUIType[0]], defaultGlobalVars[self.GUIType[0]], controls.hand[0].cords, self.GUIType[0], [controlsConf.controllers[0], controls.hand[0]], [controlsConf.controllers[1], controls.hand[1]])

            self.GUIType = None


# class for spheres
class Point:
    def __init__(self, radius, density, show, *pointCollisions):
        self.jointConnections = 0  # number of connected joints
        self.show = show
        self.radius = radius
        self.origRadius = radius
        self.diameter = self.radius * 2
        if self.show:
            self.sphere = vizshape.addSphere(1, slices=pointResolution)  # vizard object for sphere
            self.sphere.setScale([self.radius, self.radius, self.radius])
        self.cords = [0, 0, 0]
        self.oldCords = [0, 0, 0]  # coordinate position from last frame
        self.velocity = [0, 0, 0]
        self.momentum = [0, 0, 0]
        self.oldVelocity = [0, 0, 0]  # velocity value from the previous frame
        self.reboundVelocity = [0, 0, 0]  # resultant velocity caused by collisions
        self.force = [0, 0, 0]
        self.normalForce = [0, 0, 0]  # here's how I'll calculate this: https://drive.google.com/file/d/1ES6T8RilTcE5Pu7Zhdxfo6R6hvvsViAT/view?usp=drive_link
        self.acc = [0, 0, 0]
        self.density = density
        self.origDensity = density
        self.volume = (4 / 3) * math.pi * self.radius ** 3
        self.halfArea = 2 * math.pi * self.radius ** 2
        self.mass = self.density * self.volume
        self.weight = [self.mass * globalVars['gField'][0], self.mass * globalVars['gField'][1], self.mass * globalVars['gField'][2]]
        self.gasDrag = [0, 0, 0]
        self.liquidDrag = [0, 0, 0]
        self.gasUpthrust = [0, 0, 0]
        self.liquidUpthrust = [0, 0, 0]
        self.friction = [0, 0, 0]
        self.constrainForce = [0, 0, 0]
        self.impulse = [0, 0, 0]
        self.cubeCollision = []
        self.cubeCollisionCalc = []
        self.cubeSubmersion = []
        self.collision = []  # self.collision[count] represents the surface of a collision cuboid that the point is CURRENTLY (hence making self.collision[count] = '' in else cases) in front of, using only its center point as reference
        self.lastCollision = []
        self.vertexState = ''  # closest vertex plane
        self.e = 0.95  # elasticity (WARNING: must be less than 1 (can be closer to 1 as calcRate increases) due to floating point error)
        self.sf = globalVars['friction']  # surface friction coefficient
        self.multiplier = []  # variable for movement calcs
        self.constrainVelocity = [0, 0, 0]
        self.connectedJoint = False
        self.cloth = ''
        self.movingAngle = [0, 0, 0]  # direction of movement
        self.collisionState = ''
        self.bAngle = [0, 0, 0]  # stores angle of b.angle
        self.collAngle = [0, 0, 0]  # angle of collision point
        self.colliding = []
        self.pIdx = ''
        self.submergedVolume = 0
        self.submergedArea = 0
        self.submergedRadius = 0
        self.pointCollisions = ['']
        if len(pointCollisions) > 0:
            self.pointCollisions = pointCollisions

    def setRadiusDensity(self, radius, density):
        self.radius = radius
        self.density = density
        self.diameter = self.radius * 2
        self.volume = 4 / 3 * math.pi * self.radius ** 3
        self.halfArea = 2 * math.pi * self.radius ** 2
        self.mass = self.density * self.volume
        self.weight = [self.mass * globalVars['gField'][0], self.mass * globalVars['gField'][1], self.mass * globalVars['gField'][2]]
        if self.show:
            self.sphere.setScale([self.radius, self.radius, self.radius])

    def move(self):
        self.weight = [self.mass * globalVars['gField'][0], self.mass * globalVars['gField'][1], self.mass * globalVars['gField'][2]]

        if not game.pause:
            self.physics()
        self.boxCollision()  # runs collision code

        self.oldVelocity = copy.deepcopy(self.velocity)

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

    def physics(self):
        for axis in range(3):
            # add physics here
            self.gasDrag[axis] = 0.5 * globalVars['gasDensity'] * -getSign(self.velocity[axis]) * ((self.velocity[axis] / physicsTime) ** 2) * math.pi * (self.radius ** 2)
            self.gasUpthrust[axis] = -(4 / 3) * math.pi * (self.radius ** 3) * globalVars['gasDensity'] * globalVars['gField'][axis]

            self.force[axis] = self.gasDrag[axis] + self.liquidDrag[axis] + self.gasUpthrust[axis] + self.liquidUpthrust[axis] + self.weight[axis]
            self.force[axis] += self.constrainForce[axis]  # constraining force added here to prevent points from floating

        # calculate normal reaction force. the reason it's here and not in boxCollision is because resultant force must first be calculated above.
        count = 0
        for b in game.collisionRect:
            if self.cubeCollisionCalc[count] and (b.type == 's'):
                self.bAngle = copy.deepcopy(b.angle)  # assigns collisionRect angle to local variable, so it can be changed (for the sake of calculation) without changing the collisionRect's angle itself

                resultF = 0
                if (self.lastCollision[count] == 'top') or (self.lastCollision[count] == 'bottom'):
                    # check out this link to see why these if statements are used here, as well as the math:
                    if (self.force[0] * self.multiplier[count]) > 0:
                        resultF += abs(self.force[0] * math.sin(self.bAngle[2]))
                    if (self.force[1] * self.multiplier[count]) < 0:
                        resultF += abs(self.force[1] * math.cos(self.bAngle[2]))

                elif (self.lastCollision[count] == 'right') or (self.lastCollision[count] == 'left'):
                    self.bAngle[2] -= math.pi / 2
                    if (self.force[0] * self.multiplier[count]) < 0:
                        resultF += abs(self.force[0] * math.sin(self.bAngle[2]))
                    if (self.force[1] * self.multiplier[count]) < 0:
                        resultF += abs(self.force[1] * math.cos(self.bAngle[2]))

                elif (self.lastCollision[count] == 'front') or (self.lastCollision[count] == 'back'):
                    if (self.force[2] * self.multiplier[count]) < 0:
                        resultF += abs(self.force[2])
                    self.normalForce[2] = resultF * self.multiplier[count] * 0.999999
                    for plane in range(2):
                        self.friction[plane] = -resultF * self.sf * getSign(self.velocity[plane]) * sin(abs(self.movingAngle[0]))

                # negative coefficients used for friction here since it always acts in the opposite direction to motion
                if self.collisionState == 'y':
                    # negative coefficients used for normalForce here since it always acts in the opposite direction to resultant force
                    # *0.999999 used here to compensate for floating point error (I hate floating point error)
                    self.normalForce[0] = -resultF * sin(self.collAngle[2]) * self.multiplier[count] * 0.999999
                    self.normalForce[1] = resultF * cos(self.collAngle[2]) * self.multiplier[count] * 0.999999
                    self.normalForce[2] = -resultF * sin(self.collAngle[0]) * self.multiplier[count] * 0.999999
                    self.friction[0] = -getSign(self.velocity[0]) * resultF * cos(self.collAngle[2]) * self.sf * sin(abs(self.movingAngle[1]))
                    self.friction[2] = -getSign(self.velocity[2]) * resultF * cos(self.collAngle[2]) * self.sf * cos(abs(self.movingAngle[1]))
                elif self.collisionState == 'x':
                    self.normalForce[0] = -resultF * sin(self.collAngle[2]) * self.multiplier[count] * 0.999999
                    self.normalForce[1] = resultF * cos(self.collAngle[2]) * self.multiplier[count] * 0.999999
                    self.normalForce[2] = -resultF * sin(self.collAngle[0]) * self.multiplier[count] * 0.999999
                    self.friction[1] = getSign(self.velocity[1]) * resultF * sin(self.collAngle[2]) * self.sf * cos(abs(self.movingAngle[2]))
                    self.friction[2] = getSign(self.velocity[2]) * resultF * sin(self.collAngle[2]) * self.sf * sin(abs(self.movingAngle[2]))
            count += 1

        for axis in range(3):
            self.force[axis] += self.normalForce[axis] + self.friction[axis] + self.impulse[axis]
            self.acc[axis] = self.force[axis] / self.mass  # F = ma, a = F/m
            self.oldCords[axis] -= self.acc[axis] / (physicsTime ** 2)  # divide by time since d(v) = a * d(t)
        self.constrainForce = [0, 0, 0]  # reset constrainForce
        # print(self.force)

        # moving angle about relative to each axis in the form of [x:y, x:z, y:z]
        if self.velocity[1] != 0:
            self.movingAngle[0] = math.atan(self.velocity[0] / self.velocity[1])
        else:
            self.movingAngle[0] = math.pi / 2
        if self.velocity[2] != 0:
            self.movingAngle[1] = math.atan(self.velocity[0] / self.velocity[2])
        else:
            self.movingAngle[1] = math.pi / 2
        if self.velocity[1] != 0:
            self.movingAngle[2] = math.atan(self.velocity[2] / self.velocity[1])
        else:
            self.movingAngle[2] = math.pi / 2

    # check this out here to see how I use lines, domains, and ranges for collision detection:
    def yCollisionPlane(self, b):
        return {
            'left': {'y': (b.grad['y'] * self.cords[0]) + (b.vertex[1][1] - (b.grad['y'] * b.vertex[1][0])), 'm': b.grad['y'], 'c': b.vertex[1][1] - (b.grad['y'] * b.vertex[1][0])},
            'right': {'y': (b.grad['y'] * self.cords[0]) + (b.vertex[0][1] - (b.grad['y'] * b.vertex[0][0])), 'm': b.grad['y'], 'c': b.vertex[0][1] - (b.grad['y'] * b.vertex[0][0])},
            'top': {'y': (b.grad['x'] * self.cords[0]) + (b.vertex[1][1] - (b.grad['x'] * b.vertex[1][0])), 'm': b.grad['x'], 'c': b.vertex[1][1] - (b.grad['x'] * b.vertex[1][0])},
            'bottom': {'y': (b.grad['x'] * self.cords[0]) + (b.vertex[2][1] - (b.grad['x'] * b.vertex[2][0])), 'm': b.grad['x'], 'c': b.vertex[2][1] - (b.grad['x'] * b.vertex[2][0])},
        }

    def xCollisionPlane(self, b):
        return {
            'left': {'x': - (b.grad['x'] * self.cords[1]) + (b.vertex[1][0] + (b.grad['x'] * b.vertex[1][1])), 'm': -b.grad['x'], 'c': b.vertex[1][0] + (b.grad['x'] * b.vertex[1][1])},
            'right': {'x': - (b.grad['x'] * self.cords[1]) + (b.vertex[0][0] + (b.grad['x'] * b.vertex[0][1])), 'm': -b.grad['x'], 'c': b.vertex[0][0] + (b.grad['x'] * b.vertex[0][1])},
            'top': {'x': - (b.grad['y'] * self.cords[1]) + (b.vertex[1][0] + (b.grad['y'] * b.vertex[1][1])), 'm': -b.grad['y'], 'c': b.vertex[1][0] + (b.grad['y'] * b.vertex[1][1])},
            'bottom': {'x': - (b.grad['y'] * self.cords[1]) + (b.vertex[2][0] + (b.grad['y'] * b.vertex[2][1])), 'm': -b.grad['y'], 'c': b.vertex[2][0] + (b.grad['y'] * b.vertex[2][1])}
        }

    # detects and resolves collisions between spheres (points) and static cuboids (collision rects)
    def boxCollision(self):
        cubeCollision = False
        cubeSubmersion = False
        count = 0  # using count here instead of len(game.collisionRect) since it's just so much easier to read and type 'b' instead of 'game.collisionRect[b]'
        for b in game.collisionRect:
            self.bAngle = copy.deepcopy(b.angle)
            yCollisionPlane = self.yCollisionPlane(b)
            xCollisionPlane = self.xCollisionPlane(b)

            # check out the logic here: https://drive.google.com/file/d/1B-GqxPcpGkWAE_ogzMvYntTNmt8R99gT/view?usp=drive_link
            self.vertexState = ''  # stores the facing axis of the nearest vertex
            if ((self.cords[1] > yCollisionPlane['right']['y']) or (self.cords[1] < yCollisionPlane['left']['y'])) and ((self.cords[1] > yCollisionPlane['top']['y']) or (self.cords[1] < yCollisionPlane['bottom']['y'])) and (
                    (self.cords[2] <= b.plane['front']) and (self.cords[2] >= b.plane['back'])):  # x > right, x < left, y > top, y < bottom, back < z < front
                self.vertexState = 'z'
            elif ((self.cords[1] > yCollisionPlane['right']['y']) or (self.cords[1] < yCollisionPlane['left']['y'])) and ((self.cords[1] <= yCollisionPlane['top']['y']) and (self.cords[1] >= yCollisionPlane['bottom']['y'])) and (
                    (self.cords[2] > b.plane['front']) or (self.cords[2] < b.plane['back'])):  # x > right, x < lfet, bottom < y < top, z > front, z < back
                self.vertexState = 'y'
            elif ((self.cords[1] <= yCollisionPlane['right']['y']) and (self.cords[1] >= yCollisionPlane['left']['y'])) and ((self.cords[1] > yCollisionPlane['top']['y']) or (self.cords[1] < yCollisionPlane['bottom']['y'])) and (
                    (self.cords[2] > b.plane['front']) or (self.cords[2] < b.plane['back'])):  # left < x < right, y > top, y < bottom, z > front, z < back
                self.vertexState = 'x'

            # self.lastCollision represents the surface of a collision cuboid that the point was LAST in front of, factoring in its radius as well. this value never resets.
            if (self.cords[1] <= (yCollisionPlane['right']['y'] + self.radius)) and (self.cords[1] >= (yCollisionPlane['left']['y'] - self.radius)) and (self.cords[2] <= (b.plane['front'] + self.radius)) and (self.cords[2] >= (b.plane['back'] - self.radius)):
                if self.cords[1] >= (yCollisionPlane['top']['y'] + self.radius):
                    self.lastCollision[count] = 'top'
                elif self.cords[1] <= (yCollisionPlane['bottom']['y'] - self.radius):
                    self.lastCollision[count] = 'bottom'
            elif (self.cords[1] <= yCollisionPlane['top']['y']) and (self.cords[1] >= yCollisionPlane['bottom']['y']) and (self.cords[2] <= b.plane['front']) and (self.cords[2] >= b.plane['back']):
                if self.cords[1] >= (yCollisionPlane['right']['y'] + self.radius):
                    self.lastCollision[count] = 'right'
                elif self.cords[1] <= (yCollisionPlane['left']['y'] - self.radius):
                    self.lastCollision[count] = 'left'
            elif (self.cords[1] <= (yCollisionPlane['top']['y'] + self.radius)) and (self.cords[1] >= (yCollisionPlane['bottom']['y'] - self.radius)) and (self.cords[1] <= (yCollisionPlane['right']['y'] + self.radius)) and (self.cords[1] >= (yCollisionPlane['left']['y'] - self.radius)):
                if self.cords[2] >= (b.plane['front'] - self.radius):
                    self.lastCollision[count] = 'front'
                elif self.cords[2] <= (b.plane['back'] + self.radius):
                    self.lastCollision[count] = 'back'

            self.cubeCollisionCalc[count] = (self.cords[1] <= (collisionCalcTolerance + yCollisionPlane['top']['y'] + self.radius / cos(self.bAngle[2]))) and (self.cords[1] >= (-collisionCalcTolerance + yCollisionPlane['bottom']['y'] - self.radius / cos(self.bAngle[2]))) and (self.cords[1] <= (collisionCalcTolerance + yCollisionPlane['right']['y'] + self.radius / sin(self.bAngle[2]))) and (
                    self.cords[1] >= (-collisionCalcTolerance + yCollisionPlane['left']['y'] - self.radius / sin(self.bAngle[2]))) and (self.cords[2] <= (collisionCalcTolerance + b.plane['front'] + self.radius)) and (self.cords[2] >= (-collisionCalcTolerance + b.plane['back'] - self.radius))

            self.cubeCollision[count] = (self.cords[1] <= (collisionTolerance + yCollisionPlane['top']['y'] + self.radius / cos(self.bAngle[2]))) and (self.cords[1] >= (-collisionTolerance + yCollisionPlane['bottom']['y'] - self.radius / cos(self.bAngle[2]))) and (self.cords[1] <= (collisionTolerance + yCollisionPlane['right']['y'] + self.radius / sin(self.bAngle[2]))) and (
                    self.cords[1] >= (-collisionTolerance + yCollisionPlane['left']['y'] - self.radius / sin(self.bAngle[2]))) and (self.cords[2] <= (collisionTolerance + b.plane['front'] + self.radius)) and (self.cords[2] >= (-collisionTolerance + b.plane['back'] - self.radius))
            self.cubeSubmersion[count] = (self.cords[1] <= (collisionTolerance + yCollisionPlane['top']['y'] - self.radius / cos(self.bAngle[2]))) and (self.cords[1] >= (-collisionTolerance + yCollisionPlane['bottom']['y'] + self.radius / cos(self.bAngle[2]))) and (self.cords[1] <= (collisionTolerance + yCollisionPlane['right']['y'] - self.radius / sin(self.bAngle[2]))) and (
                    self.cords[1] >= (-collisionTolerance + yCollisionPlane['left']['y'] + self.radius / sin(self.bAngle[2]))) and (self.cords[2] <= (collisionTolerance + b.plane['front'] - self.radius)) and (self.cords[2] >= (-collisionTolerance + b.plane['back'] + self.radius))  # cubeCollision[count] but with reversed radii calcs

            if not self.cubeCollision[count]:  # reset self.collision[count] when not in front of a plane
                self.collision[count] = ''
            if (self.cords[1] <= (yCollisionPlane['right']['y'])) and (self.cords[1] >= (yCollisionPlane['left']['y'])) and (self.cords[2] <= (b.plane['front'])) and (self.cords[2] >= (b.plane['back'])):
                if self.cords[1] >= (yCollisionPlane['top']['y']):
                    self.collision[count] = 'top'
                elif self.cords[1] <= (yCollisionPlane['bottom']['y']):
                    self.collision[count] = 'bottom'
            elif (self.cords[1] <= yCollisionPlane['top']['y']) and (self.cords[1] >= yCollisionPlane['bottom']['y']) and (self.cords[2] <= b.plane['front']) and (self.cords[2] >= b.plane['back']):
                if self.cords[1] >= (yCollisionPlane['right']['y']):
                    self.collision[count] = 'right'
                elif self.cords[1] <= (yCollisionPlane['left']['y']):
                    self.collision[count] = 'left'
            elif (self.cords[1] <= (yCollisionPlane['top']['y'])) and (self.cords[1] >= (yCollisionPlane['bottom']['y'])) and (self.cords[1] <= (yCollisionPlane['right']['y'])) and (self.cords[1] >= (yCollisionPlane['left']['y'])):
                if self.cords[2] >= (b.plane['front']):
                    self.collision[count] = 'front'
                elif self.cords[2] <= (b.plane['back']):
                    self.collision[count] = 'back'
            # print(self.collision)

            # get the distance until edge/vertex collision
            if (self.collision[count] == '') or (self.vertexState != ''):  # "why should we resolve vertex/edge collisions if the point is in front of a face on the collision rect?" hence, this if statement is used to optimize performance.
                vertexDist = []  # distance to each edge/vertex, depending on the type of collision
                vIdx = []  # stores (specific) index values in a specific order from the collisionRect.vertex list because of this: https://drive.google.com/file/d/1llq6UTfJHZ2GJic5s8510RJoKKEBbg1Y/view?usp=drive_link
                vertexIdx = []  # final index of closest vertex index
                minDist = float('inf')  # final distance to the closest vertex
                if self.vertexState == 'x':
                    vIdx = [[0, 1], [2, 7], [3, 6], [4, 5]]
                elif self.vertexState == 'y':
                    vIdx = [[0, 7], [1, 2], [3, 4], [5, 6]]
                elif self.vertexState == 'z':
                    vIdx = [[0, 5], [1, 4], [2, 3], [6, 7]]
                else:  # when undergoing a corner collision
                    vIdx = []
                    for inc in range(8):
                        vIdx.append(inc)

                if self.vertexState != '':  # edge collision detection:
                    dist = []  # distance to each vertex as indicated by vIdx
                    for d in range(len(vIdx)):
                        dist.append([])
                        vertexDist.append(0)
                        for h in range(len(vIdx[d])):
                            tempDist = distance(b.vertex[vIdx[d][h]], self.cords)
                            if tempDist >= self.radius:  # used to prevent sqrt(-number)
                                dist[d].append(math.sqrt(tempDist ** 2 - self.radius ** 2))  # gets the distance from each vertex to the current sphere's position
                                vertexDist[d] += dist[d][h]
                            else:
                                dist[d].append(0)
                else:  # corner collision detection:
                    for d in range(len(b.vertex)):
                        vertexDist.append(distance(b.vertex[d], self.cords))

                # get the smallest value in the list
                for ve in range(len(vertexDist)):
                    if vertexDist[ve] < minDist:  # if current value is less than lowest value:
                        minDist = vertexDist[ve]  # set lowest value to current value
                        vertexIdx = vIdx[ve]  # set index of lowest value to current index

            # multiplier obtained through testing
            if (self.lastCollision[count] == 'right') or (self.lastCollision[count] == 'top') or (self.lastCollision[count] == 'front'):
                self.multiplier[count] = 1
            else:
                self.multiplier[count] = -1

            # detect collisions between points and planes (flat surfaces) on a collision rect (cuboid)
            if (self.vertexState == '') and (self.collision[count] != '') and self.cubeCollisionCalc[count]:
                if (self.collision[count] == 'right') or (self.collision[count] == 'left'):
                    self.bAngle[2] -= math.pi / 2  # shift angle by 90° since perpendicular surfaces to the collision rect (left & right) are, well... perpendicular (to top & bottom). reason this is subtraction is because all movement is reversed since it's, well... perpendicular.
                self.collAngle = copy.deepcopy(self.bAngle)
                if abs(math.degrees(self.bAngle[2])) < 45:
                    self.collisionState = 'y'
                else:
                    self.collisionState = 'x'

                if self.cubeCollision[count]:
                    if b.type == 's':
                        if str(self.sf) == 'sticky':
                            self.cords = copy.deepcopy(self.oldCords)  # "stick" cords to oldCords
                        else:
                            if (self.collision[count] == 'top') or (self.collision[count] == 'right') or (self.collision[count] == 'bottom') or (self.collision[count] == 'left'):  # colliding with top/right/bottom/left plane
                                # check out this link to see why I need the logic below:
                                if self.collisionState == 'y':
                                    if not self.colliding[count]:
                                        self.colliding[count] = True
                                        # self.cords[0] = copy.deepcopy(self.oldCords[0])
                                        # yCollisionPlane = self.yCollisionPlane(b)
                                        self.cords[1] = yCollisionPlane[self.collision[count]]['y'] + (self.multiplier[count] * self.radius / cos(self.bAngle[2]))
                                        self.oldCords[0] = copy.deepcopy(self.cords[0])
                                        self.oldCords[1] = copy.deepcopy(self.cords[1])
                                        resultP = ((self.mass * self.velocity[0] * cos(self.bAngle[2])) + (self.mass * self.velocity[1] * sin(self.bAngle[2])))
                                        self.impulse[0] = resultP * physicsTime * cos(self.bAngle[2]) * self.e
                                        self.impulse[1] = resultP * physicsTime * sin(self.bAngle[2]) * self.e
                                    else:
                                        self.impulse = [0, 0, 0]
                                        self.cords[1] = yCollisionPlane[self.collision[count]]['y'] + (self.multiplier[count] * self.radius / cos(self.bAngle[2]))
                                else:
                                    if not self.colliding[count]:
                                        self.colliding[count] = True
                                        self.cords[0] = xCollisionPlane[self.collision[count]]['x'] - (self.multiplier[count] * self.radius / sin(self.bAngle[2]))
                                        self.oldCords[0] = copy.deepcopy(self.cords[0])
                                        self.oldCords[1] = copy.deepcopy(self.cords[1])
                                        resultP = (self.mass * self.velocity[0] * cos(self.bAngle[2])) + (self.mass * self.velocity[1] * sin(self.bAngle[2]))
                                        self.impulse[0] = resultP * physicsTime * cos(self.bAngle[2]) * self.e
                                        self.impulse[1] = resultP * physicsTime * sin(self.bAngle[2]) * self.e
                                    else:
                                        self.impulse = [0, 0, 0]
                                        self.cords[0] = xCollisionPlane[self.collision[count]]['x'] - (self.multiplier[count] * self.radius / sin(self.bAngle[2]))  # + (sin(self.bAngle[2]) * resultV * self.e)
                            elif (self.collision[count] == 'front') or (self.collision[count] == 'back'):
                                if not self.colliding[count]:
                                    self.colliding[count] = True
                                    self.cords[2] = b.plane[self.collision[count]] + (self.radius * self.multiplier[count])
                                    self.oldCords[2] = copy.deepcopy(self.cords[2])
                                else:
                                    self.cords[2] = b.plane[self.collision[count]] + (self.radius * self.multiplier[count])

                    elif b.type == 'l':
                        # get cap volume with submerged radius, etc.
                        # also disable gas upthrust for submerged parts
                        if self.collisionState == 'y':
                            submergedAmt = abs((yCollisionPlane[self.collision[count]]['y'] + (self.multiplier[count] * self.radius / cos(self.bAngle[2])) - self.cords[1]) * cos(self.bAngle[2]))  # check out the maths for this here:
                        elif self.collisionState == 'x':
                            submergedAmt = abs((xCollisionPlane[self.collision[count]]['x'] - (self.multiplier[count] * self.radius / sin(self.bAngle[2])) - self.cords[0]) * sin(self.bAngle[2]))
                        self.submergedVolume = capVolume(submergedAmt, self.radius)
                        self.submergedArea = capArea(submergedAmt, self.radius)
                        self.submergedRadius = submergedAmt

                        if self.cubeSubmersion[count]:  # if fully submerged
                            self.submergedVolume = copy.deepcopy(self.volume)

                        if self.submergedRadius > self.radius:  # if half of sphere is submerged
                            self.submergedArea = copy.deepcopy(self.halfArea)
                            self.submergedRadius = copy.deepcopy(self.radius)

                        for axis in range(3):
                            self.liquidUpthrust[axis] = b.density * -globalVars['gField'][axis] * self.submergedVolume  # U = pgV
                            self.liquidDrag[axis] = (0.5 * b.dragConst * (self.velocity[axis] ** 2) * -getSign(self.velocity[axis]) * self.submergedArea) + (6 * math.pi * b.viscosity * self.submergedRadius * -self.velocity[axis])  # D = 6πμrv + 1/2 cpAv² (Drag = Stokes' law + drag force)

                # collidingB.append(b)

            # detect collisions between points and edges on a collision rect (cuboid)
            elif (self.vertexState != '') and (minDist <= (distance(b.vertex[vertexIdx[0]], b.vertex[vertexIdx[1]]))):
                if b.type == 's':
                    # i = [0, 0, 0]
                    if str(self.sf) == 'sticky':
                        self.cords = copy.deepcopy(self.oldCords)
                    else:
                        self.cords = copy.deepcopy(self.oldCords)
                        # if (self.lastCollision[count] == 'top') or (self.lastCollision[count] == 'bottom'):
                        #     i = [2, 1, 0]
                        #
                        # elif (self.lastCollision[count] == 'left') or (self.lastCollision[count] == 'right'):
                        #     i = [2, 0, 1]
                        #
                        # elif (self.lastCollision[count] == 'front') or (self.lastCollision[count] == 'back'):
                        #     i = [1, 0, 2]

                        # if abs(math.degrees(self.bAngle[2])) < 45:
                        #     self.collisionState = 'y'
                        #     collisionPoint = self.cords[0] + (self.radius / cos(self.bAngle[2])), yCollisionPlane[self.lastCollision[count]][self.collisionState], b.vertex[vertexIdx[0]][i[0]]
                        # else:
                        #     self.collisionState = 'x'
                        #     collisionPoint = self.cords[1] + (self.radius / cos(self.bAngle[2])), yCollisionPlane[self.lastCollision[count]][self.collisionState], b.vertex[vertexIdx[0]][i[0]]

                        # self.angle = getThreeDAngle(collisionPoint, self.cords, self.vertexState)
                        # angle = getTwoDAngle([self.cords[i[1]], self.cords[i[0]]], [b.vertex[vertexIdx[0]][i[1]], b.vertex[vertexIdx[0]][i[0]]])
                        # resultV = math.sqrt(self.oldVelocity[i[0]] ** 2 + self.oldVelocity[i[1]] ** 2)
                        # self.reboundVelocity[i[0]], self.reboundVelocity[i[1]], self.reboundVelocity[i[2]] = edgeBounce(resultV, self.angle, self.e, -1)
                        # self.cords[i[0]] += self.multiplier[count] * self.reboundVelocity[i[0]]
                        # self.oldCords[i[1]] = yCollisionPlane[self.lastCollision[count]]['y'] + (self.radius * cos(self.angle[0]))
                        # self.collAngle = getThreeDAngle(collisionPoint, self.cords, 'y')
                        # self.cords[i[1]] = yCollisionPlane[self.lastCollision[count]][self.collisionState] + (self.radius * sin(self.collAngle[0]))
                        # self.oldCords[i[1]] = copy.deepcopy(self.cords[i[1]])
                        # self.cords[i[2]] += self.multiplier[count] * self.reboundVelocity[i[2]]
                        # print(self.normalForce, self.collAngle)

                elif b.type == 'l':
                    pass

                # collidingB.append(b)

            # detect collisions between points and vertices (corners) on a collision rect (cuboid)
            elif (self.collision[count] == '') and (self.vertexState == '') and (distance(b.vertex[vertexIdx], self.cords) <= self.radius):
                if str(self.sf) == 'sticky':
                    self.cords = copy.deepcopy(self.oldCords)
                else:
                    self.cords = copy.deepcopy(self.oldCords)
                    # resultF = math.sqrt(self.force[0] ** 2 + self.force[1] ** 2 + self.force[2] ** 2)
                    # resultV = math.sqrt(self.oldVelocity[0] ** 2 + self.oldVelocity[1] ** 2 + self.oldVelocity[2] ** 2)
                    #
                    # # nMultiplier was obtained through testing
                    # if (self.lastCollision[count] == 'top') or (self.lastCollision[count] == 'bottom'):
                    #     self.angle = getThreeDAngle(b.vertex[vertexIdx], self.cords, 'y')
                    #     if (vertexIdx == 0) or (vertexIdx == 1) or (vertexIdx == 6) or (vertexIdx == 3):
                    #         pMultiplier = [-1, -1]
                    #         nMultiplier = [1, 1]
                    #     elif (vertexIdx == 4) or (vertexIdx == 5) or (vertexIdx == 2) or (vertexIdx == 7):
                    #         pMultiplier = [1, 1]
                    #         nMultiplier = [-1, -1]
                    #     if self.lastCollision[count] == 'top':
                    #         yMultiplier = -1
                    #     elif self.lastCollision[count] == 'bottom':
                    #         yMultiplier = 1
                    #
                    #     self.reboundVelocity[0], self.reboundVelocity[1], self.reboundVelocity[2] = vertexBounce(resultV, self.angle, self.e)
                    #     self.cords[0] += pMultiplier[0] * self.reboundVelocity[0]
                    #     self.cords[1] = self.oldCords[1] + self.reboundVelocity[1] * yMultiplier
                    #     self.cords[2] += pMultiplier[1] * self.reboundVelocity[2]
                    #     self.normalForce[0] = nMultiplier[0] * resultF * cos(self.angle[1]) * sin(self.angle[0]) * -yMultiplier
                    #     self.normalForce[2] = nMultiplier[1] * resultF * cos(self.angle[1]) * cos(self.angle[0]) * -yMultiplier
                    #
                    # elif (self.lastCollision[count] == 'left') or (self.lastCollision[count] == 'right'):
                    #     self.angle = getThreeDAngle(b.vertex[vertexIdx], self.cords, 'x')
                    #     if (vertexIdx == 1) or (vertexIdx == 4) or (vertexIdx == 6) or (vertexIdx == 7):
                    #         pMultiplier = [1, 1]
                    #         if (vertexIdx == 6) or (vertexIdx == 7):
                    #             nMultiplier = [-1, -1]
                    #         elif (vertexIdx == 1) or (vertexIdx == 4):
                    #             nMultiplier = [1, 1]
                    #     elif (vertexIdx == 2) or (vertexIdx == 3) or (vertexIdx == 0) or (vertexIdx == 5):
                    #         pMultiplier = [-1, -1]
                    #         if (vertexIdx == 0) or (vertexIdx == 5):
                    #             nMultiplier = [1, 1]
                    #         elif (vertexIdx == 2) or (vertexIdx == 3):
                    #             nMultiplier = [-1, -1]
                    #     if self.lastCollision[count] == 'left':
                    #         yMultiplier = 1
                    #     elif self.lastCollision[count] == 'right':
                    #         yMultiplier = -1
                    #
                    #     self.reboundVelocity[2], self.reboundVelocity[0], self.reboundVelocity[1] = vertexBounce(resultV, self.angle, self.e)
                    #     self.cords[1] += pMultiplier[0] * self.reboundVelocity[1]
                    #     self.cords[0] = self.oldCords[0] + self.reboundVelocity[0] * yMultiplier
                    #     self.cords[2] += pMultiplier[1] * self.reboundVelocity[2]
                    #     self.normalForce[1] = nMultiplier[0] * resultF * cos(self.angle[1]) * cos(self.angle[0])
                    #     self.normalForce[2] = nMultiplier[1] * resultF * cos(self.angle[1]) * sin(self.angle[0])
                    #
                    # elif (self.lastCollision[count] == 'front') or (self.lastCollision[count] == 'back'):
                    #     self.angle = getThreeDAngle(b.vertex[vertexIdx], self.cords, 'z')
                    #     if (vertexIdx == 0) or (vertexIdx == 1) or (vertexIdx == 3) or (vertexIdx == 6):
                    #         pMultiplier = [-1, -1]
                    #         nMultiplier = [-1, -1]
                    #     elif (vertexIdx == 7) or (vertexIdx == 2) or (vertexIdx == 4) or (vertexIdx == 5):
                    #         pMultiplier = [1, 1]
                    #         nMultiplier = [1, 1]
                    #     if self.lastCollision[count] == 'front':
                    #         yMultiplier = -1
                    #     elif self.lastCollision[count] == 'back':
                    #         yMultiplier = 1
                    #
                    #     self.reboundVelocity[0], self.reboundVelocity[2], self.reboundVelocity[1] = vertexBounce(resultV, self.angle, self.e)
                    #     self.cords[0] += pMultiplier[0] * self.reboundVelocity[0]
                    #     self.cords[2] = self.oldCords[2] + self.reboundVelocity[2] * yMultiplier
                    #     self.cords[1] += pMultiplier[1] * self.reboundVelocity[1]
                    #     self.normalForce[0] = nMultiplier[0] * resultF * cos(self.angle[1]) * sin(self.angle[0]) * yMultiplier
                    #     self.normalForce[1] = nMultiplier[1] * resultF * cos(self.angle[1]) * cos(self.angle[0]) * yMultiplier

                    # print(self.lastCollision[count], math.degrees(angle[0]), math.degrees(angle[1]), vertexIdx[0])
                # collidingB.append(b)
            else:
                self.colliding[count] = False

            cubeCollision = cubeCollision or self.cubeCollisionCalc[count]
            cubeSubmersion = cubeSubmersion or self.cubeSubmersion[count]
            count += 1

        if not cubeCollision:
            # reset values that depend on a collision when not colliding
            self.normalForce = [0, 0, 0]
            self.reboundVelocity = [0, 0, 0]
            self.friction = [0, 0, 0]
            self.impulse = [0, 0, 0]
        if not cubeSubmersion:
            self.liquidUpthrust = [0, 0, 0]
            self.liquidDrag = [0, 0, 0]
            self.submergedVolume = 0
            self.submergedArea = 0
            self.submergedRadius = 0


# class for cylinders (joints) connecting spheres
class Joint:
    def __init__(self, show, origLength, stiffness, pOne, pTwo, bounciness, maxStrain, *theForceJoint):
        self.pOne = pOne  # index of first connected point
        self.pTwo = pTwo  # index of second connected point
        game.points[pOne].connectedJoint = True
        game.points[pTwo].connectedJoint = True
        self.height = distance(game.points[self.pOne].cords, game.points[self.pTwo].cords)  # current size of joint
        self.oldHeight = copy.deepcopy(self.height)  # size of joint from previous frame
        self.radius = jointRadius
        self.stiffness = stiffness
        self.origStiffness = stiffness
        self.origArea = math.pi * (self.radius ** 2)
        self.dampingConst = bounciness
        self.cords = [0, 0, 0]
        self.angle = [0, 0, 0]
        self.show = show
        if origLength == '':
            self.origLength = copy.deepcopy(self.height)
        else:
            self.origLength = origLength
        self.maxStrain = maxStrain  # maximum length of joint before breaking
        self.diff = [0, 0, 0]  # caching variable, avoiding repeat calcs to increase performance
        self.constrainForce = [0, 0, 0]
        self._update = [0, 0, 0]
        self.damping = [0, 0, 0]
        self.dampingCoef = 1
        if self.show:
            self.cylinder = vizshape.addCylinder(1, self.radius, slices=jointResolution)  # make the joint visible if shown
        self.volume = math.pi * (self.radius ** 2) * self.height
        self.theForceJoint = False
        self.cIdx = -1
        # additional arguments to set the joint to be "the chosen force joint"
        if len(theForceJoint) > 0:
            self.theForceJoint = theForceJoint[0]
            self.cIdx = theForceJoint[1]

    # update the position and appearance of the joint
    def update(self):
        if self.height >= (self.origLength * self.maxStrain):
            pass
            # self.snap()  # MASSIVE WIP

        if self.theForceJoint:
            self.diff = displacement(controls.hand[self.cIdx].cords, game.points[self.pTwo].cords)
        else:
            self.diff = displacement(game.points[self.pOne].cords, game.points[self.pTwo].cords)
        self.oldHeight = copy.deepcopy(self.height)
        if (self.pOne > self.pTwo) and (game.diff[self.pTwo][self.pOne] != 0):  # must be used to compensate for "also don't get distance between 2 points if you already have it!"
            self.height = game.diff[self.pTwo][self.pOne]
        elif game.diff[self.pOne][self.pTwo] != 0:
            self.height = game.diff[self.pOne][self.pTwo]
        # self.radius = math.sqrt(self.volume / (math.pi * self.height))  # r = sqrt(v / πh)
        # no need to reassign volume here since it always stays constant

    def draw(self):
        if self.show:
            self.cylinder.setScale([self.radius, self.height, 1])  # change visual of cylinder
            if self.theForceJoint:
                self.cords = midpoint(controls.hand[self.cIdx], game.points[self.pTwo])  # set the midpoint of the joint to the middle of each connected cord
                self.cylinder.setEuler(getEulerAngle(controls.hand[self.cIdx].cords, game.points[self.pTwo].cords))  # set the facing angle of the joint to "connect" to both points
            else:
                self.cords = midpoint(game.points[self.pOne], game.points[self.pTwo])
                self.cylinder.setEuler(getEulerAngle(game.points[self.pOne].cords, game.points[self.pTwo].cords))

            self.cylinder.setPosition(self.cords)

    # constrain points connected to this joint
    def constrain(self):
        if (self.height != self.origLength) and (self.height != 0):
            # self.dampingCoef = 1 + (self.height / self.origLength)
            for u in range(3):
                if self.theForceJoint:
                    self._update[u] = 0.01 * (self.diff[u] * ((self.origLength / self.height) - 1))  # pull points by changing their cords directly rather than force (since it doesn't matter when you use The Force!)
                self.constrainForce[u] = self.stiffness * (self.diff[u] / self.height) * (self.origLength - self.height)  # check out the maths for this using this link:
                self.damping[u] = self.dampingCoef * self.dampingConst * abs((self.diff[u] / self.height) * (self.oldHeight - self.height)) * getSign(game.points[self.pOne].velocity[u] - game.points[self.pTwo].velocity[u]) * physicsTime  # damping force = damping constant * change in joint length (relative to both points) * relative direction
        # self.stiffness = self.origStiffness * (math.pi * (self.radius ** 2)) / self.origArea  # increase stiffness as length decreases and vice versa as length increases
        for i in range(3):
            if self.theForceJoint:
                game.points[self.pTwo].cords[i] -= self._update[i]  # pull last dragged point regardless of its mass (because it's THE FORCE)
            else:
                game.points[self.pOne].constrainForce[i] += self.constrainForce[i] - self.damping[i]
                game.points[self.pTwo].constrainForce[i] -= self.constrainForce[i] - self.damping[i]  # negative due to Newton's 3rd law

    # break the joint after extending a specified distance
    def snap(self):
        # radius cannot be less than 0.05 due to floating point error
        if (game.points[self.pOne].jointConnections <= 2) and (game.points[self.pTwo].jointConnections <= 2):
            pass
        else:
            if (game.points[self.pOne].radius / 2) < minRadius:
                pointRad = minRadius
            else:
                pointRad = game.points[self.pOne].radius / 2
            game.points.append(Point(pointRad, game.points[self.pOne].density, True, self.pOne))
            game.points[self.pOne].setRadiusDensity(pointRad, game.points[self.pOne].density)
            game.points[self.pOne].pointCollisions = [len(game.points) - 1]
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
            game.points.append(Point(pointRad, game.points[self.pTwo].density, True, self.pTwo))
            game.points[self.pTwo].setRadiusDensity(pointRad, game.points[self.pTwo].density)
            self.pOne = len(game.points) - 1
            game.points[-1].cords = copy.deepcopy(self.cords)
            game.points[-1].oldCords = copy.deepcopy(game.points[-1].cords)
            game.points[self.pTwo].pointCollisions = [len(game.points) - 1]
            # self.origLength *= self.maxStrain
            self.origLength *= 2
            self.diff = [0, 0, 0]
            self.height = copy.deepcopy(self.origLength)
            self.oldHeight = copy.deepcopy(self.height)
            self.maxStrain *= 2
            game.points[self.pTwo].cloth = self.pTwo * len(game.points)  # unique cloth key
            game.points[-1].cloth = self.pTwo * len(game.points)
            game.updateLists()


class CollisionRect:
    def __init__(self, size, cords, angle, density, viscosity, dragConst, transparency, rectType):
        self.type = rectType  # solid or liquid
        self.angle = angle
        self.vertexAngle = [0, 0, 0]
        self.size = size
        self.rect = vizshape.addBox(self.size)
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
        self.update()

    def update(self):
        self.rect.remove()
        self.rect = vizshape.addBox(self.size)
        self.rect.setPosition(self.cords)
        self.rect.setEuler(math.degrees(self.angle[0]), math.degrees(self.angle[1]), math.degrees(self.angle[2]))
        self.rect.alpha(self.transparency)
        sizeMultiplier = [0.5, 0.5, 0.5]
        multiplier = 1
        self.vertexAngle = math.atan(self.size[1] / self.size[0])
        # print(math.degrees(self.vertexAngle))
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
                    tempVertex[i] = self.cords[i] + (xySize * sizeMultiplier[i] * cos(self.vertexAngle + (multiplier * self.angle[2])))
                elif i == 1:  # y
                    tempVertex[i] = self.cords[i] + (xySize * sizeMultiplier[i] * sin(self.vertexAngle + (multiplier * self.angle[2])))
                elif i == 2:  # z
                    tempVertex[i] = self.cords[i] + (self.size[i] * sizeMultiplier[i])

            self.vertex.append(tempVertex)

        # multiplier = [1, 1]
        # self.vertexAngle = getThreeDAngle([0, 0, 0], self.size, 'y')
        # self.vertexAngle = [abs(self.vertexAngle[0]), abs(self.vertexAngle[1]), abs(self.vertexAngle[2])]
        # size = math.sqrt((self.size[0]) ** 2 + (self.size[1]) ** 2 + (self.size[2]) ** 2)
        # size = [0, 0, 0]
        # size[0] = math.sqrt((self.size[0]) ** 2 + (self.size[1]) ** 2)  # front/back
        # size[1] = math.sqrt((self.size[0]) ** 2 + (self.size[2]) ** 2)  # top/bottom
        # size[2] = math.sqrt((self.size[1]) ** 2 + (self.size[2]) ** 2)  # left/right
        # self.vertexAngle[0] = math.atan(self.size[1] / self.size[0])
        # self.vertexAngle[1] = math.atan(self.size[2] / self.size[0])
        # self.vertexAngle[2] = math.atan(self.size[2] / self.size[1])
        # print(math.degrees(self.vertexAngle[0]), math.degrees(self.vertexAngle[1]), math.degrees(self.vertexAngle[2]))
        # bAngle = copy.deepcopy(self.angle)
        # bAngle[0] += self.vertexAngle[0]
        # bAngle[1] += self.vertexAngle[1]
        # bAngle[2] += self.vertexAngle[2]
        # matrix = [0, 0, 0]
        # matrix[0] = [cos(bAngle[0]) * cos(bAngle[1]), cos(bAngle[0]) * sin(bAngle[1]) * sin(bAngle[2]) - sin(bAngle[0]) * cos(bAngle[2]), cos(bAngle[0]) * sin(bAngle[1]) * cos(bAngle[2]) + sin(bAngle[0]) * sin(bAngle[2])]
        # matrix[1] = [sin(bAngle[0]) * cos(bAngle[1]), sin(bAngle[0]) * sin(bAngle[1]) * sin(bAngle[2]) + cos(bAngle[0]) * cos(bAngle[2]), sin(bAngle[0]) * sin(bAngle[1]) * cos(bAngle[2]) - cos(bAngle[0]) * sin(bAngle[2])]
        # matrix[2] = [-sin(bAngle[1]), cos(bAngle[1]) * sin(bAngle[2]), cos(bAngle[1]) * cos(bAngle[2])]
        # for i in range(3):
        #     for j in range(3):
        #         matrix[i][j] *= size
        # print(matrix)
        # for v in range(8):
        #     if (v == 1) or (v == 5):
        #         sizeMultiplier[0] = -sizeMultiplier[0]
        #     elif (v == 4) or (v == 6) or (v == 2):
        #         sizeMultiplier[1] = -sizeMultiplier[1]
        #     elif (v == 3) or (v == 7):
        #         sizeMultiplier[2] = -sizeMultiplier[2]
        #     if (v == 1) or (v == 4) or (v == 6) or (v == 7):
        #         multiplier[0] = -1
        #     elif (v == 0) or (v == 5) or (v == 2) or (v == 3):
        #         multiplier[0] = 1
        #     if (v == 0) or (v == 2) or (v == 3) or (v == 5):
        #         multiplier[1] = -1
        #     else:
        #         multiplier[1] = 1
        #     tempVertex = [0, 0, 0]
        #     for i in range(3):
        #         if i == 0:  # x
        #             tempVertex[i] = self.cords[i] + (size * sizeMultiplier[i] * cos(self.vertexAngle[1] + (multiplier[0] * self.angle[0])) * sin(self.vertexAngle[0] + (multiplier[1] * self.angle[2])))
        #             # tempVertex[i] = self.cords[i] + (sizeMultiplier[i] * size[0] * cos(self.vertexAngle[0] + (multiplier[0] * (self.angle[2] - self.angle[0]))))
        #         elif i == 1:  # y
        #             # tempVertex[i] = self.cords[i] + (size * sizeMultiplier[i] * sin(self.vertexAngle[1] + (multiplier[0] * self.angle[2])))
        #             tempVertex[i] = self.cords[i] + (size * sizeMultiplier[i] * cos(self.vertexAngle[1] + (multiplier[0] * self.angle[0])) * cos(self.vertexAngle[0] + (multiplier[1] * self.angle[2])))
        #             # tempVertex[i] = self.cords[i] + (sizeMultiplier[i] * size[0] * sin(self.vertexAngle[0] + (multiplier[0] * self.angle[2])))
        #         elif i == 2:  # z
        #             tempVertex[i] = self.cords[i] + (size * sizeMultiplier[i] * cos(self.vertexAngle[1]) * cos(self.vertexAngle[0] + (multiplier[1] * self.angle[0])))
        #             # tempVertex[i] = self.cords[i] + (sizeMultiplier[i] * self.size[2])
        #     self.vertex.append(tempVertex)

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

        # print(self.vertex)
        # print(self.vertexAngle)


game = Main()

# makes a cube using points and joints
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
    # if cubeSize > 8:
    #     game.points[8].cords = [0, 1.5, 0]
    #     game.points[8].oldCords = [0, 1.5, 0]
    #     game.points[9].cords = [0, 2.5, 0]
    #     game.points[9].oldCords = [0, 2.5, 0]
    #     game.points[10].cords = [0, 0.5, 0]
    #     game.points[10].oldCords = [0, 0.5, 0]
    #     game.points[11].cords = [1, 1.5, 0]
    #     game.points[11].oldCords = [1, 1.5, 0]
    #     game.points[12].cords = [-1, 1.5, 0]
    #     game.points[12].oldCords = [-1, 1.5, 0]
    #     game.points[13].cords = [0, 1.5, 1]
    #     game.points[13].oldCords = [0, 1.5, 1]
    #     game.points[14].cords = [0, 1.5, -1]
    #     game.points[14].oldCords = [0, 1.5, -1]

    # for z in range(cubeRes):
    #     for y in range(cubeRes):
    #         for x in range(cubeRes):
    #             if (x == 0) or (y == 0) or (z == 0) or (x == (cubeRes - 1)) or (y == (cubeRes - 1)) or (z == (cubeRes - 1)):
    #                 game.addPoint(Point(pointRadius, 1000, True))
    #                 game.points[-1].cords = [x * cubeSize / cubeRes, y * cubeSize / cubeRes, z * cubeSize / cubeRes]
    #                 game.points[-1].oldCords = copy.deepcopy(game.points[-1].cords)
    #                 game.points[-1].cloth = 'cube'

    for j in range(len(game.points)):
        for jo in range(len(game.points)):
            if (j != jo) and (jo > j):  # performance optimisation: only go through unique combinations of j and jo (e.g. [1, 5] and [5, 0] are unique, but [1, 5] and [5, 1] are not)
                if jo <= 7:
                    game.joints.append(Joint(True, '', globalVars['springConst'], j, jo, globalVars['damping'], globalVars['strain']))
                else:
                    game.joints.append(Joint(True, '', globalVars['springConst'], j, jo, globalVars['damping'], globalVars['strain']))
    # game.addPoint(Point(0.1, 1000))

sphere = False
if sphere:
    game.addPoint(Point(0.01, 1000, True))
elif not cube:
    pass
    # game.addPoint(Point(0.6, 1000, True))
    # game.addPoint(Point(0.4, 1000, True))
    # game.points[0].cords = [-(25 + game.points[0].radius) * sin(math.radians(30)), 30 + (25 + game.points[0].radius) * cos(math.radians(30)), 0]
    # game.points[0].oldCords = copy.deepcopy(game.points[0].cords)
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
            game.collisionRect.append(CollisionRect((10, 10, 10), [x, y + 10, 0], [0, 0, math.radians((80 * s / surfaceRes) + 5)], 1000, 1, 0.9, 1, 's'))
        except ValueError:
            continue
game.collisionRect.append(CollisionRect((100, 50, 50), [-50, 0, 0], [math.radians(0), math.radians(0), math.radians(0.001)], 1000, 10, 1, 0.9, 's'))  # CANNOT be negative angle or above 90 (make near-zero for an angle of 0)
game.collisionRect.append(CollisionRect((100, 50, 50), [60, 0, 0], [math.radians(0), math.radians(0), math.radians(30)], 1000, 10, 1, 0.9, 's'))
game.collisionRect.append(CollisionRect((50, 50, 50), [170, 0, 0], [math.radians(0), 0, math.radians(0.0001)], 2000, 1, 1, 0.5, 'l'))
game.collisionRect.append(CollisionRect((5000, 5, 10), [0, 125, 0], [math.radians(0), 0, math.radians(44)], 1000, 10, 1, 0.9, 's'))
game.collisionRect.append(CollisionRect((5000, 20, 10), [0, 128, 10], [math.radians(0), 0, math.radians(44)], 1000, 10, 1, 0.9, 's'))
game.collisionRect.append(CollisionRect((5000, 20, 10), [0, 128, -10], [math.radians(0), 0, math.radians(44)], 1000, 10, 1, 0.9, 's'))

game.initLists()  # WARNING: MUST ALWAYS RUN THIS RIGHT BEFORE vizact.ontimer
vizact.ontimer(1 / calcRate, game.main)  # calculate physics game.time times each second
vizact.ontimer(1 / renderRate, game.render)  # render objects game.render times each second
