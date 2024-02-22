# base Vizard libraries

import random
import time

import viz
import vizfx
import vizshape
import vizconnect
import steamvr
import vizact
import viztask
import math
# used for copying the value of a list/dictionary variable to another, without referencing the original variable
import copy

import config
from globalFunctions import *
import myGUI

# in the beginning, always ask the user if they want to load the data from exportData
while True:  # if the user doesn't input 'y' or 'n', loop forever until they do
    imports = input('Import from exportData? (y / n): ')
    if imports.lower() == 'y':
        imports = True
    elif imports.lower() == 'n':
        imports = False
    if type(imports) is bool:
        break
    else:
        print('Please enter y / n!')

# Vizard window initialization
viz.setMultiSample(4)  # FSAA (Full Screen Anti-Aliasing)
viz.fov(90)  # FoV (Field of View) increased from the default value of 60 to 90 to allow more things to be seen by the camera at once
viz.go()  # initialise the Vizard game window

"""
'controlsConf' will be used to query the Vizard hand objects for getting their button pressed
'controls' will be used to query the hands for their positions
the correct controls file for importing is indicated by the mode ('k/m' or 'VR' as 'k' or 'vr', respectively)
"""
if mode == 'vr':
    import steamVR_init as controlsConf
elif mode == 'k':
    if fullscreen:  # only allow full-screen if on k/m, since it breaks stuff in VR
        viz.window.setFullscreen()
    import keyboard_mouse_init as controlsConf
controls = controlsConf.Main()

# 'l/rControllerObj' are constants used for interacting with GUIs by passing these into classes in myGUI whenever GUIs are summoned
lControllerObj = [controlsConf.controllers[0], controls.hand[0]]
rControllerObj = [controlsConf.controllers[1], controls.hand[1]]

viz.vsync(0)  # disable vsync (cuz it caps off max calcs/second) to the display's refresh rate. unfortunately doesn't work for VR.


# generalized control function to get if the 'select' button is being pressed, given a controller's index (0==left, 1==right)
def selectP(cIdx):
    return buttonPressed('select', controlsConf.controllers[cIdx], cIdx)


# Main class for main.py
class Main:
    def __init__(self):
        self.pause = False  # stores if physics should be paused (all points have 0 velocity if True)

        self.points = []  # list of points for the whole program
        self.diff = []  # cache variable to store the scalar distance between each point

        self.joints = []  # list of joints for the whole program
        self.collisionRect = []  # list of collision rectangles for the whole program

        self.__GUI = {
            """
            this is a dictionary of all GUIs and their possible forms in the notation: variable: {type: {axes: None}}, where None is replaced with the GUI object when they are summoned.
            for all scalar quantities, manual has only one axis: default, or 'def' for short. this is for two reasons:
                1) having no axes (no direction, since it's a scalar) means that, well... there aren't any axes; only magnitude!
                2) while slider and dial GUI types have axes regardless if a value is a vector or scalar quantity, that's only because their visuals can be affected by summoning them about different axes. manual inputs' visuals aren't affected by its axis!
            tutorials have an empty dictionary to allow tutorials to be updated to it from the importTutorials method, allowing for the selection of all tutorials from tutorialTexts
            """
            'gameSpeed': {'dial': {'XZ': None, 'XY': None, 'YZ': None, '3D': None}, 'slider': {'X': None, 'Y': None, 'Z': None}, 'manual': {'def': None}},
            'gField': {'dial': {'XZ': None, 'XY': None, 'YZ': None, '3D': None}, 'slider': {'X': None, 'Y': None, 'Z': None}, 'manual': {'X': None, 'Y': None, 'Z': None}},
            'gasDensity': {'dial': {'XZ': None, 'XY': None, 'YZ': None, '3D': None}, 'slider': {'X': None, 'Y': None, 'Z': None}, 'manual': {'def': None}},
            'springConst': {'dial': {'XZ': None, 'XY': None, 'YZ': None, '3D': None}, 'slider': {'X': None, 'Y': None, 'Z': None}, 'manual': {'def': None}},
            'damping': {'dial': {'XZ': None, 'XY': None, 'YZ': None, '3D': None}, 'slider': {'X': None, 'Y': None, 'Z': None}, 'manual': {'def': None}},
            'friction': {'dial': {'XZ': None, 'XY': None, 'YZ': None, '3D': None}, 'slider': {'X': None, 'Y': None, 'Z': None}, 'manual': {'def': None}},
            'strain': {'dial': {'XZ': None, 'XY': None, 'YZ': None, '3D': None}, 'slider': {'X': None, 'Y': None, 'Z': None}, 'manual': {'def': None}},
            'GUISelector': {'': {'': None}},  # this has empty strings since the GUI selector has no type or axes
            'Tutorials': {'': {}}  # this has empty strings since all tutorials have no type nor axes
        }

        self.__buttonHeld = {}  # stores if a button is being held
        # update buttonHeld to have all the controls from config.controls
        for cMap in config.controls:
            self.__buttonHeld.update({cMap: [False, False]})
        self.__dragP = [None, None]  # last clicked point index, which loses its value after deselecting a point
        self.__lastP = [None, None]  # last clicked point index, which retains its value even after deselecting a point
        self.__collP = [None, None]  # stores the indexes of points that are colliding with either controller
        self.__animeScale = [1, 1]  # visual scale of controller animations
        self.__animeScaleSpeed = 0  # rate at which animations scale
        self.__animeColor = [[0, 0, 0], [0, 0, 0]]  # stores the color of each controller's animation
        self.__GUIType = None  # holds the return value of GUISelector to create relevant GUI(s)
        self.__clickTime = [0, 0]  # stores time since 'select' was pressed for both controllers in order for double-click detection
        self.__relPos = [[0, 0, 0], [0, 0, 0]]  # stores the relative position of selected points with either controller

        self.__clothData = {}  # stores the indexes of all points in a cloth, with the cloth's name as the key
        self.__tutorialTexts = {}  # stores all titles and contents of tutorials
        self.__importTutorials()
        # if the user typed 'y', import from exportData
        if imports:
            self.__importData()

    def __importData(self):
        f = open('exportData', 'r')
        data = f.read().splitlines()
        formattedData = []  # the code below makes this into the form: [[points], [joints], [collisionRects]]
        f.close()
        """
        step-by-step process of reading exportData:
            1. if the upcoming lines represent a different type (points/joints/collisionRects) to the previous line, append a new list to formattedData.
                the initial type is None, so the first line in exportData will always be 'POINTS'.
            2. until the next line represents a different type, append the current line to the latest list in formattedData.
            see below for point 3 onwards.
        """
        for pjc in data:  # loop through all lines in exportData
            if (pjc == 'POINTS') or (pjc == 'JOINTS') or (pjc == 'COLLISIONRECTS'):
                formattedData.append([])
            else:
                formattedData[-1].append(pjc)
                formattedData[-1][-1] = formattedData[-1][-1].split(' | ')
        """
            3. at this point, formattedData contains data in the form: [['points'], ['joints'], ['collisionRects']]. however, all this data is the literal string text from exportData.
                as such, the next steps will work on converting relevant values to lists, floats, and strings so that the program can recognize them as points/joints/collisionRects.
            4. go through each list in formattedData:
                a) 'i' represents the index of the type (0 == point, 1 == joint, 2 == collisionRect)
                b) 'j' represents the index of the object (point/joint/collisionRect)
                c) 'k' represents the index of the current element in the object (e.g. cords, radius, density, size)
            5. handle an exception case for the only string in exportData, which is the type of collisionRect (solid/liquid as 's'/'l', respectively).
            6. if the current type is a joint (when i == 1), make all values integers since they represent the points list indexes, since list indexes must be integers!
            7. if the current value isn't a number, it must be a list. as such, remove the brackets and convert the current value into a list.
                then convert all values in this list to a float. after that, assign the current value as a list to formattedData.
                here's what this would look like: '[0.1, 0.2, 0.3]' -> '0.1, 0.2, 0.3' -> [0.1, 0.2, 0.3]
            8. formattedData is now truly formatted data! simply add the points, joints, and collisionRects to their respective lists from the data in formattedData.
        """
        for i in range(len(formattedData)):
            for j in range(len(formattedData[i])):
                for k in range(len(formattedData[i][j])):
                    if (formattedData[i][j][k] != 's') and (formattedData[i][j][k] != 'l'):
                        try:
                            if i == 1:  # if current type is a joint
                                formattedData[i][j][k] = int(formattedData[i][j][k])  # make data int since list indexes (of the points list) cannot be floats
                            else:
                                formattedData[i][j][k] = float(formattedData[i][j][k])
                        except ValueError:  # if current value is a list and not a number
                            formattedData[i][j][k] = formattedData[i][j][k].replace('[', '')
                            formattedData[i][j][k] = formattedData[i][j][k].replace(']', '')
                            tempList = formattedData[i][j][k].split(', ')  # convert value into a list
                            for t in range(len(tempList)):
                                tempList[t] = float(tempList[t])
                            formattedData[i][j][k] = tempList
        points = formattedData[0]  # format: [[cords (float)], radius (float), density (float)]
        joints = formattedData[1]  # format: [point 1 index (float), point 2 index (float)]
        collisionRects = formattedData[2]  # format: [[size (float)], [cords (float)], [angle (float)], density (float), viscosity (float), dragConst (float), transparency (float), rectType (string)]
        # although dragConst is always 1, I plan to do something with this in the future
        for p in points:
            self.addPoint(Point(p[1], p[2], True))
            self.points[-1].teleport(p[0])  # move the point to its coordinates while maintaining 0 speed
        for j in joints:
            # pass 'self' into Joint to allow it to get its initial length ('height')
            # this is a must since importData is run in the Main class' initialization, so the game() instance doesn't exist at this moment in time!
            self.joints.append(Joint(True, '', globalVars['springConst'], j[0], j[1], globalVars['damping'], 69, self))
            self.__initCloths(j)
        for cr in collisionRects:
            self.collisionRect.append(CollisionRect(cr[0], cr[1], cr[2], cr[3], cr[4], cr[5], cr[6], cr[7]))

    # identify cloths based on joints connected to a points
    def __initCloths(self, jDat):
        """
        by looping through all points, if the index of both points match the point indexes of the joint (jDat), make both points have the same cloth.
        'p' and 'po' are indexes in the point list.
        the point at index 'p' will always be the one to have a cloth before any point at index 'po', so that its cloth value can spread to all other points in the same sprite. this logic is made possible by point 2 below.
        if statement analysis:
            1. 'p != po': the current point isn't referring to itself.
            2. 'po > p': don't compare points that have already been looped through (e.g. [1, 5] and [5, 0] are unique, but [1, 5] and [5, 1] are not).
                this reduces the time complexity of the nested for loop from O(n²) to O(n² / 2), since 'p' can never be larger than 'po'.
            3. '((jDat[0] == p) and (jDat[1] == po)) or ((jDat[1] == p) and (jDat[0] == po))': both point's indexes are equal to the point indexes of the joint, regardless of their order.
        """
        for p in range(len(self.points)):
            for po in range(len(self.points)):
                if (p != po) and (po > p) and (((jDat[0] == p) and (jDat[1] == po)) or ((jDat[1] == p) and (jDat[0] == po))):
                    # if the point hasn't been assigned a cloth, make a new cloth with a unique key len(joints)
                    # len(joints) will always be unique since a new joint is appended to the joints list each time this method runs
                    if self.points[p].cloth == '':
                        self.points[p].cloth = f'{len(self.joints)}'
                    self.points[po].cloth = self.points[p].cloth  # make both point's cloths identical (since they are connected to the same joint)

    # initialize all the lists that depend on the size of self.points and self.collisionRect
    def initLists(self):
        for p in range(len(self.points)):
            self.__GUI.update({p: {'slider': {'radius': None, 'density': None}, 'manual': {'radius': None, 'density': None}}})  # add a radius/density GUI to the GUI dictionary for each point, with the key as the integer value of the point's index
            for _ in range(len(self.collisionRect)):  # append the below to each point for every collisionRect in the game
                self.points[p].collision.append('')
                self.points[p].lastCollision.append('')
                self.points[p].colliding.append(False)
                self.points[p].cubeCollision.append(False)
                self.points[p].cubeCollisionCalc.append(False)
                self.points[p].cubeSubmersion.append(False)
                self.points[p].addMultiplier()

            self.diff.append([])
            for _ in range(len(self.points)):
                # this allows 'diff' to store the relative distance between every point to every other point where 'p' is the index of the reference point in question
                self.diff[p].append(0)
        self.__lastP = [len(self.points) - 1, len(self.points) - 2]  # by default, set the last selected points to the latest added points
        self.__updateCloths()
        # below is the code I used to get the relative size of the JetBrains font to the game scene
        # myT = viz.addText3D('abcd', fontSize=1.69 / 4)  # OBSERVATION: font size of 1.69 has the width of 1 unit
        # myT = viz.addText3D('a\nb\nc', fontSize=1)  # OBSERVATION: font size of 1 has the height of 1 unit
        # myT.font("JetBrainsMono-2.304\\fonts\\ttf\\JetBrainsMono-Medium.ttf")

    # update all the lists whenever a new point or collisionRect is added for the same reasons as the 'initLists' method
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
        self.__updateCloths()

    # put the indexes of all points into the clothData dictionary identify all points in a cloth
    def __updateCloths(self):
        global clothNames  # globalized to allow the clothNames dict in config to be updated for cloth/point selection in the GUISelector
        for p in range(len(self.points)):
            # if the point isn't a part of a cloth, make its key as its position index 'p' in the points list
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
                for tutorial in tempList:
                    tempStr = f'{tempStr}{tutorial}'
                tNames.append(tempStr)
            else:
                tTexts[-1].append(l)  # if the current line isn't a tutorial's title, add it to the latest tutorial's contents
        for t in range(len(tNames)):
            tNames[t] = tNames[t].replace('newLine', '\n')  # solution from Python Discord, credit goes to lordtyrionlannister "Saul Goodman". replaces all newLine values with an actual new line in string format.
            self.__tutorialTexts.update({tNames[t]: tTexts[t]})  # update local information about the tutorial
            tutorialNames.update({tNames[t]: None})  # update the global value of tutorialNames for use in GUISelector
            self.__GUI['Tutorials'][''].update({tNames[t]: None})  # update local values of tutorials in self.GUI
        f.close()
        if not imports:
            # always summon the introduction tutorial when the program starts
            # this won't be summoned if the user is importing from exportData since they would have already seen the introduction tutorial in spriteCreator.py
            self.__GUI['Tutorials']['']['Introduction'] = myGUI.Tutorial([0, 2, 4], [10, 0.2], self.__tutorialTexts['Introduction'], [], 0.3, lControllerObj, rControllerObj)

    # teleport a cloth to a controller's position; it can be specified if the parameter 'cloth' is a point index or a cloth name
    def __tpCloth(self, cloth, cords, cIdx):
        """
        :param cloth: the name of a cloth/a point's index, depending on 'cloth' being a string/integer, respectively.
        :param cords: location to teleport the cloth/point to.
        :param cIdx: index of the controller to teleport the point/cloth to.

        when teleporting a point that's part of a cloth, the entire cloth (all points in the cloth) should be teleported at once.
        this prevents its joints from being stretched too far which would cause the user to lose control of the cloth.
        this is done by getting the change in position of the reference point during its teleport, and then adding this change in position to all position values of the other points in the cloth.
            the logic is as follows: 'cords' - 'oldCords', where 'cords' is the destination and 'oldCords' is the initial position.
        although this only applies if the reference point is a part of a cloth, this method works even if the reference point isn't a part of a cloth.
        check out this link for an illustration: https://drive.google.com/file/d/1d5MI1ox6PDqQiyb2x0-5k5LS-S4PIIEs/view?usp=drive_link
        """
        cordDiff = []  # stores the change in pos of the reference point
        if type(cloth) is int:  # if 'cloth' is a point index
            pIdx = cloth
            cloth = self.points[pIdx].cloth
        else:  # if 'cloth' is the name of a cloth
            pIdx = self.__clothData[cloth][-1]  # set the reference point's index to the latest point in the cloth

        # get change in pos as a result of the reference point's teleportation
        self.points[pIdx].cords = copy.deepcopy(controls.hand[cIdx].cords)
        for co in range(3):
            cordDiff.append(self.points[pIdx].cords[co] - self.points[pIdx].oldCords[co])

        if cloth != '':  # only teleport other points if the reference point is a part of a cloth
            for p in self.__clothData[f'{cloth}']:
                if p != pIdx:  # exclude the reference point from teleportation since the reference point is teleported even if the value of 'cloth' is empty
                    for cor in range(3):
                        self.points[p].cords[cor] += cordDiff[cor]
                        self.points[p].oldCords[cor] += cordDiff[cor]
        self.points[pIdx].oldCords = copy.deepcopy(cords)

    # the method in this class that allows the program to run and manages all other methods
    def main(self):
        global physicsTime  # must be globalised since gameSpeed can be changed by the user from the GUI selector
        physicsTime = calcRate * (1 / globalVars['gameSpeed'])  # update the value of physicsTime based on gameSpeed, since gameSpeed can be changed in a GUI
        for c in range(controlsConf.controllerAmt):
            self.__getButtonReleased(c)
            self.__pauseGame(c)
            self.__summonGUISelector(c)

        self.__dragPoint()

        for p in range(len(self.points)):
            self.points[p].sf = globalVars['friction']  # update each point's local value of friction based on globalVars['friction'], since friction can be changed in a GUI
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
        """
        :param p: index of the reference point to check for collisions with.

        this method is used to detect and resolve the collisions between two points.
        currently, it only works with 100% elasticity since I can't figure out what this means: https://en.wikipedia.org/wiki/Collision_response#Impulse-based_reaction_model

        process:
            1. loop through all points.
                'po > p': don't compare points that have already been looped through (e.g. [1, 5] and [5, 0] are unique, but [1, 5] and [5, 1] are not).
                this reduces the time complexity of the nested for loop from O(n²) to O(n² / 2), since 'p' can never be larger than 'po'.
            2. if the distance between both points <= the sum of their radii, there's a collision between them.
                check out this link for logical proof: https://drive.google.com/file/d/1WH5wvc5lVaKQhG9lBSByJf3SIlzh-unJ/view?usp=drive_link
            3. calculate the size of the collision normal's angles.
                imagine a line connecting the centres of both points. that's the collision normal!
            4. calculate the size of relative components of velocity for each point.
                then, using spherical coordinate geometry, calculate the resultant speed of these velocities relative to the normal.
                imagine yourself standing on the point of collision on either point. how fast you see the other point moving towards you (as you get crushed between them) is what this value represents!
            5. use the formula "ΔP = ((m1 * m2 * (v1 - v2) * normal) / (m1 + m2)) * 2" to get the change in momentum of both points.
                I derived this by testing collisions in a PhET simulation: https://phet.colorado.edu/sims/html/collision-lab/latest/collision-lab_all.html
            6. get the resultant direction of each point depending on which quartile they're colliding in.
                check out this link for the logic behind this: https://drive.google.com/file/d/1GDe4hnh2pb6aZ9L_Rz93G3oayglutxei/view?usp=sharing
            7. resolve the collision using spherical coordinate geometry, reversing the direction of impulse for both points due to Newton's 3rd Law.
        """
        # detect & resolve collisions with all points
        for po in range(len(self.points)):
            if (po > p) and (p != po) and (self.points[p].disabledPointCollisions[0] != po) and (self.points[po].disabledPointCollisions[0] != p):
                sumR = self.points[p].radius + self.points[po].radius
                # detect collisions utilizing the cached values of dist
                if self.diff[p][po] <= sumR:
                    mOne = copy.deepcopy(self.points[p].mass)
                    mTwo = copy.deepcopy(self.points[po].mass)
                    vOne = copy.deepcopy(self.points[p].velocity)
                    vTwo = copy.deepcopy(self.points[po].velocity)
                    normal = getAbsThreeDAngle(self.points[p].cords, self.points[po].cords, 'y')  # get the size of the collision normal's angle
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
                    # changing cords will change velocity due to Verlet integration
                    self.points[p].cords[0] -= deltaP * multiplier[0] * cos(normal[1]) * sin(normal[0]) / (self.points[p].mass * calcRate)
                    self.points[po].cords[0] += deltaP * multiplier[0] * cos(normal[1]) * sin(normal[0]) / (self.points[po].mass * calcRate)
                    self.points[p].cords[1] -= deltaP * multiplier[1] * sin(normal[1]) / (self.points[p].mass * calcRate)
                    self.points[po].cords[1] += deltaP * multiplier[1] * sin(normal[1]) / (self.points[po].mass * calcRate)
                    self.points[p].cords[2] -= deltaP * multiplier[2] * cos(normal[1]) * cos(normal[0]) / (self.points[p].mass * calcRate)
                    self.points[po].cords[2] += deltaP * multiplier[2] * cos(normal[1]) * cos(normal[0]) / (self.points[po].mass * calcRate)

    # get if a button isn't being pressed to allow for single-click detection
    def __getButtonReleased(self, cIdx):
        """
        :param cIdx: controller index value

        this method is used to allow for single-click detection by setting buttonHeld to false if the button specified by 'config.controls' isn't being held.
        when the button held is set to True, its code will not be able to run until it becomes False again, which only happens when it's released.
        """
        for b in self.__buttonHeld:
            if not buttonPressed(b, controlsConf.controllers[cIdx], cIdx):
                self.__buttonHeld[b][cIdx] = False

    # summon the GUI selector if the 'GUISelector' button is pressed
    def __summonGUISelector(self, cIdx):
        # only summon if the GUISelector button isn't being held down
        if (not self.__buttonHeld['GUISelector'][cIdx]) and buttonPressed('GUISelector', controlsConf.controllers[cIdx], cIdx):
            self.__buttonHeld['GUISelector'][cIdx] = True
            if self.__GUI['GUISelector'][''][''] is None:
                self.__GUI['GUISelector'][''][''] = myGUI.GUISelector(globalVars, controls.hand[cIdx].cords, lControllerObj, rControllerObj)
            else:
                removeGUI(self.__GUI['GUISelector'][''][''])

    # pause the physics if the 'pause' button is pressed
    def __pauseGame(self, cIdx):
        if (not self.__buttonHeld['pause'][cIdx]) and buttonPressed('pause', controlsConf.controllers[cIdx], cIdx):
            self.__buttonHeld['pause'][cIdx] = True
            self.pause = not self.pause  # reciprocate between True and False

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
        """
        this method is used to drag points around using a hand, as well as running the animations for doing so.
        process:
            1. loop through all controllers.
            2. detect for GUI interactions with the current hand.
            3. loop through all points; detect for collisions between points and the current hand. if there's a collision:
                a) start the collision animation (collP)
                b) detect for selection
            4. if a point is being selected by a hand, get its relative position to the hand to freeze its position relative to the hand. (see step 8)
            5. detect for double clicks. if the current hand's select button is pressed twice within 0.25s, allow the selected point's radius & density to be modified.
            6. set the selecting point to be dragged until "select" is released.
                this allows the controller to drag the point along with it even if they are no longer colliding (which can happen in-between frames).
            7. set the last selected point (lastP) to the currently selected point for the current hand to allow for the hand to recall said point. (see step 11)
            see below for point 8 onwards.
        """
        # if mode == 'vr':
        #     print(controlsConf.controllers[0].getButtonState() % touchpad, controlsConf.controllers[1].getButtonState() % touchpad)  # prints the current button being pressed for each controller

        # loop through all drag code for each controller
        for c in range(controlsConf.controllerAmt):
            if self.__clickTime[c] <= 0.25:
                self.__clickTime[c] += 1 / calcRate  # increase since the last click
            for gVar in self.__GUI:
                for gType in self.__GUI[gVar]:
                    for gAxis in self.__GUI[gVar][gType]:
                        if self.__GUI[gVar][gType][gAxis] is not None:
                            self.__GUI[gVar][gType][gAxis].drag(c, selectP(c))  # detect GUI interactions
            for p in range(len(self.points)):
                if detectCollision(self.points[p].radius, controls.hand[c].radius, self.points[p].cords, controls.hand[c].cords):  # any point<>hand collision
                    self.__collP[c] = p
                    if selectP(c):
                        if not self.__buttonHeld['select'][c]:  # prevents other points from being picked up while a current point is being selected
                            self.__buttonHeld['select'][c] = True
                            for axis in range(3):
                                self.__relPos[c][axis] = self.points[p].cords[axis] - controls.hand[c].cords[axis]
                            if self.__clickTime[c] < 0.25:  # if there's a double click, summon sliders (if in VR) or manual inputs (if in keyboard/mouse) to change the density and radius of the double-clicked point
                                self.__setRadiusDensityGUI(controls.hand[c].cords, p)
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

            """
            8. if the controller is selecting a point, set its cords to the hand's cords, factoring in the relative position of selection to the hand.
            9. run point selection animations.
            10. if a point is no longer being selected, reset dragP for the current hand to indicate its deselection.
            11. if the "recall" button is pressed/held, bring the last selected point (for that hand) (along with all other points in the same cloth) to the current hand's position.
                teleport happens 1 frame after selection. classical movement happens from frame 2 onwards to allow Verlet integration to work.
            """
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
                    self.__tpCloth(self.__lastP[c], self.points[self.__lastP[c]].cords, c)
                    self.__buttonHeld['recall'][c] = True

    def __setRadiusDensityGUI(self, cords, p):
        if self.__GUI[p]['slider']['radius'] is None:  # only summon if GUI is empty
            if mode == 'vr':
                self.__GUI[p]['slider']['radius'] = myGUI.Slider(0, self.points[p].radius, self.points[p].origRadius, [cords[0], cords[1] + 0.5, cords[2]], 10, 0.1, maxRadius, minRadius, 'Radius', lControllerObj, rControllerObj)
            elif mode == 'k':
                self.__GUI[p]['slider']['radius'] = myGUI.Manual(0, self.points[p].radius, self.points[p].origRadius, [cords[0], cords[1] + 0.5, cords[2]], 'Radius', lControllerObj, rControllerObj)
        else:
            self.__GUI[p]['slider']['radius'].unDraw()
            self.__GUI[p]['slider']['radius'] = None
        if self.__GUI[p]['slider']['density'] is None:  # only summon if GUI is empty
            if mode == 'vr':
                self.__GUI[p]['slider']['density'] = myGUI.Slider(0, self.points[p].density, self.points[p].origDensity, [cords[0], cords[1] - 0.5, cords[2]], 10, 0.1, 10000, 1, 'Density', lControllerObj, rControllerObj)
                self.__GUI[p]['slider']['density'].closeButton.unDraw()  # only one 'X' needs to be rendered, since there are two Xs within each other
                self.__GUI[p]['slider']['density'].closeButton.cords[1] = cords[1] + 1  # offset this 'X' to be within the other 'X' so that they both act as one button to dismiss both radius and density GUIs simultaneously
            elif mode == 'k':
                self.__GUI[p]['slider']['density'] = myGUI.Manual(0, self.points[p].density, self.points[p].origDensity, [cords[0], cords[1] - 0.5, cords[2]], 'Density', lControllerObj, rControllerObj)
        else:
            self.__GUI[p]['slider']['density'].unDraw()
            self.__GUI[p]['slider']['density'] = None

    # animates selecting points depending on if it's being hovered over or selected
    def __selectPointAnime(self, c):
        # unique animation for selecting points: https://drive.google.com/file/d/1KWI48WwJub0FmlYfQJStTQ83OMEIPDVs/view?usp=drive_link
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
                self.__animeScale[c] = 1.2 * self.points[self.__collP[c]].radius / controls.anim[c].sphereRad  # makes the size of the animation 20% larger than the size of the point, taking into accrIdx that it's been scaled down to match the size of the controller
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
                # don't detect for collisions if any diff value is greater than the sum of both points' radii. also don't get distance between 2 points if you already have it! this is a performance optimization that essentially halves the time complexity of this function, which is O(n²).
                if (((disp[0] <= sumR) or (disp[1] <= sumR) or (disp[2] <= sumR)) or (self.points[p].cloth != '') and (self.points[po].cloth != '')) and (p != po) and (po > p):
                    self.diff[p][po] = diffDistance(disp[0], disp[1], disp[2])

    # add a point to the points list
    def addPoint(self, point):
        self.points.append(point)
        for p in range(len(self.points)):
            self.points[p].pIdx = p

    # draw and update all the summoned GUIs
    def __updateGUI(self):
        """
        this method is used to update all the summoned GUIs.
        gVar: GUI's reference variable
        gType: type of GUI (slider, dial, manual)
        gAxis: which axis the GUI is about
        self.__GUI[gVar][gType][gAxis]: the current GUI object

        process:
            1. loop through each GUI. if the GUI exists, continue.
            2. if the GUI is drawn, continue. otherwise, remove the GUI object from the 'GUI' dictionary.
            3. handle an exception in which the GUI selector is summoned, since it'll return the selected GUI by the user to the 'GUIType' variable.
            4. if the 'gVar' isn't an integer (meaning it's not a point index), then its GUI's reference variable must map to a variable in the 'globalVars' dictionary. if so:
                a) if long as the GUI isn't a tutorial, its set its reference variable to the variable it maps to and update the variable it maps to its reference variable.
                b) otherwise, if the GUI is a tutorial, just run its main function to check if it's being dismissed by the user.
            5. otherwise, that must mean that the current GUI's reference variable maps to either the radius or density of a point.
                the index position of this point in the points list is represented by 'gVar' if 'gVar' is an integer.

        'setVar' is used to update the variable of this GUI if multiple GUIs are summoned that have a common variable.
            this allows for multiple GUIs to affect each other, which looks very cool!
        one line after every 'setVar', the variable that the GUI changes is updated. the reason this is after 'setVar' is to prevent a recursive state in which the variable never changes.
        """
        for gVar in self.__GUI:
            for gType in self.__GUI[gVar]:
                for gAxis in self.__GUI[gVar][gType]:
                    currentGUI = self.__GUI[gVar][gType][gAxis]  # alias for the current GUI object
                    if currentGUI is not None:  # if the GUI currently exists
                        if currentGUI.drawn:  # if the GUI is currently summoned
                            if gVar == 'GUISelector':  # if the GUISelector is to be summoned, get its result in self.GUIType
                                self.__GUIType = currentGUI.main()
                            else:
                                if type(gVar) is not int:  # if gVar isn't a point index
                                    if gVar != 'Tutorials':
                                        currentGUI.setVar(globalVars[gVar])
                                        globalVars[gVar] = currentGUI.main()
                                    else:  # if the GUI is a tutorial, don't do any fancy stuff. just run its main method!
                                        currentGUI.main()
                                else:  # if the GUI was summoned as a result of double-clicking on a point, update the radius and density of that point
                                    if gAxis == 'radius':
                                        currentGUI.setVar(self.points[gVar].radius)
                                        self.points[gVar].setRadiusDensity(currentGUI.main(), self.points[gVar].density)
                                    elif gAxis == 'density':
                                        currentGUI.setVar(self.points[gVar].density)
                                        self.points[gVar].setRadiusDensity(self.points[gVar].radius, currentGUI.main())
                        else:  # if the GUI is to be removed (since it's no longer drawn)
                            self.__GUI[gVar][gType][gAxis] = None

        self.__selectGUIType()

    # summons a GUI if self.GUIType has a value, running through all the possible case scenarios and exceptions for different variables
    def __selectGUIType(self):
        """
        this method is used to summon a GUI if 'GUIType' isn't None, running through all the possible case scenarios and exceptions for different variables and GUI types.
        different case scenarios cause the data returned from 'GUIType' to vary. this method also runs through all these scenarios.
        all GUIs summoned first check to see if they have been summoned previously. if so, they are removed and re-summoned at the hand's position.
        all GUI objects are provided with the objects of both controllers so that they can detect interactions between them ('lController' & 'rController').

        process:
            1. if a cloth was selected from the GUI selector, summon it to the controller's position.
            2. if a tutorial was selected from the GUI selector, summon the selected tutorial to the hand's position.
            3. if a variable was selected, check for its type:
                a) if the selected GUI type is a slider:
                    1) pass in the necessary variables to initialize the slider.
                b) if the selected GUI type is a dial (this option is only present if the reference variable is a vector):
                    1) make a copy the dimension of the dial (2D/3D) and append it to the end of the 'GUIType' list.
                        this is used generalize the dial's reference in the 'GUI' dictionary to indicate if the dial is 3D.
                    2) if the dial is 2D, get the two axes on which the reference variable is to be changed mapping the axes selected to two indexes.
                        indicate this by making the length of the 'maxi' and 'mini' values passed into the Dial class to 2.
                    3) if the dial is 3D, all three axes will always being changed.
                        indicate this by making the length of the 'maxi' and 'mini' values passed into the Dial class to 3.
                c) if the selected GUI type is a manual input:
                    1) pass in the necessary variables to initialize the manual input.
            4. after this, always reset the value of 'GUIType' to None so that only 1 GUI is summoned at a time.
        """
        if self.__GUIType is not None:
            if self.__GUIType[0] == 'cloths':
                self.__tpCloth(self.__GUIType[1][0], controls.hand[self.__GUIType[2]].cords, self.__GUIType[2])
            elif self.__GUIType[0] == 'Tutorials':
                if self.__GUI[self.__GUIType[0]][''][self.__GUIType[1][0]] is not None:
                    self.__GUI[self.__GUIType[0]][''][self.__GUIType[1][0]].unDraw()
                    self.__GUI[self.__GUIType[0]][''][self.__GUIType[1][0]] = None
                self.__GUI[self.__GUIType[0]][''][self.__GUIType[1][0]] = myGUI.Tutorial(controls.hand[0].cords, [10, 0.2], self.__tutorialTexts[self.__GUIType[1][0]], [], 0.3, lControllerObj, rControllerObj)
            else:
                maxValue = globalRanges[self.__GUIType[0]][0]
                minValue = globalRanges[self.__GUIType[0]][1]
                refVar = globalVars[self.__GUIType[0]]
                defRefVar = defaultGlobalVars[self.__GUIType[0]]

                if self.__GUIType[1][0] == 'Slider':
                    xyz = self.__setupSliderManual()
                    self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][1]] = myGUI.Slider(xyz, refVar, defRefVar, controls.hand[0].cords, 5, maxValue, minValue, self.__GUIType[0], lControllerObj, rControllerObj)

                elif self.__GUIType[1][0] == 'Dial':
                    self.__GUIType[1].append(self.__GUIType[1][1])  # make 'GUIType[1][2]' equal to 'GUIType[1][1]', which is whether the dial is 2D or 3D
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
                        self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][2]] = myGUI.Dial(xyz, refVar, defRefVar, controls.hand[0].cords, 5, [maxValue, maxValue], [minValue, minValue], self.__GUIType[1][2], lControllerObj, rControllerObj)
                    elif self.__GUIType[1][1] == '3D':  # if the dial is 3D, no axis needs to be provided since it will change all three of the variable's values in its list (basically means axis is XYZ)
                        self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][2]] = myGUI.Dial(0, refVar, defRefVar, controls.hand[0].cords, 5, [maxValue, maxValue, maxValue], [minValue, minValue, minValue], 'XYZ', lControllerObj, rControllerObj)

                elif self.__GUIType[1][0] == 'Manual':
                    xyz = self.__setupSliderManual()
                    self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][1]] = myGUI.Manual(xyz, refVar, defRefVar, controls.hand[0].cords, self.__GUIType[0], lControllerObj, rControllerObj)

            self.__GUIType = None

    # set up the GUI and axes of a slider or manual GUI
    def __setupSliderManual(self):
        if self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][1]] is not None:
            self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][1]].unDraw()
            self.__GUI[self.__GUIType[0]][self.__GUIType[1][0].lower()][self.__GUIType[1][1]] = None
        # get the axis' index on which the GUI is situated
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
        self.collision = []  # self.collision[crIdx] represents the surface of a collision cuboid that the point is CURRENTLY (hence making self.collision[crIdx] = '' in else cases) in front of, using only its center point as reference
        self.lastCollision = []
        self.__vertexState = ''  # closest vertex plane
        self.e = 1  # elasticity constant
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
        self.__weight = [self.mass * globalVars['gField'][0], self.mass * globalVars['gField'][1], self.mass * globalVars['gField'][2]]  # update weight of the point since gField can be changed in a GUI

        if not game.pause:
            self.__physics()
        self.__boxCollision()  # runs collision code

        # Verlet integration
        for axis in range(3):
            self.velocity[axis] = (self.cords[axis] - self.oldCords[axis]) * physicsTime  # set velocity to change in position
        self.oldCords = copy.deepcopy(self.cords)  # cords for this frame is set to oldCords for next frame

        if not game.pause:
            # move the point based on its velocity
            for v in range(3):
                self.cords[v] += self.velocity[v] / physicsTime

    def draw(self):
        if self.show:
            self.sphere.setPosition(self.cords)

    def __physics(self):
        """
        this method is used to calculate and manage all the physics for a point.

        process:
            1. loop through all three axes XYZ.
            2. calculate drag caused by the air using the formula: "1/2 * density * area * velocity²"
                gas drag acts in the opposite direction to motion, hence getting the opposite sign of velocity.
            3. calculate upthrust caused by the air using the formula: "-volume * weight"
                negative coefficient used here since upthrust always acts in the opposite direction to gField.
            4. sum all the forces together in a resultant force value.
                different forces are stored in different variables since it makes them a lot easier to identify and manage, and also to reassign in each frame.
            5. check for any collisions with collisionRects.
            6. add normal reaction force, friction, and impulse caused by a collision with a collisionRect to resultant force.
                these values are all 0 if there's no collision with a collisionRect.
            7. calculate acceleration using "a = F / m", and update oldCords to cause a change in velocity from verlet integration.
                v = d / t and a = v / t, thus d = a * t². t² is actually divided instead of multiplied since physicsTime is a frequency.
            8. calculate the direction of motion for use in friction calculations.
        """
        for axis in range(3):
            self.__gasDrag[axis] = 0.5 * globalVars['gasDensity'] * -getSign(self.velocity[axis]) * math.pi * (self.radius ** 2) * ((self.velocity[axis] / physicsTime) ** 2)  # divide velocity by 'physicsTime' so that gasDrag can always remain constant
            self.__gasUpthrust[axis] = -(4 / 3) * math.pi * (self.radius ** 3) * globalVars['gasDensity'] * globalVars['gField'][axis]

            self.__force[axis] = self.__gasDrag[axis] + self.__liquidDrag[axis] + self.__gasUpthrust[axis] + self.__liquidUpthrust[axis] + self.__weight[axis] + self.constrainForce[axis]  # get resultant force

        self.__resolveRectCollisions()

        # add all forces together and calculate acceleration from this resultant force
        for axis in range(3):
            self.__force[axis] += self.__normalForce[axis] + self.__friction[axis] + self.__impulse[axis]
            self.__acc[axis] = self.__force[axis] / self.mass  # F = ma, thus a = F / m
            self.oldCords[axis] -= self.__acc[axis] / (physicsTime ** 2)  # divide by time since d(s) = a / d(f)²
        self.constrainForce = [0, 0, 0]

        # direction of motion relative to each axis in the form [x:y, x:z, y:z]
        if self.velocity[1] != 0:  # prevents dividing by 0
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
        """
        this method calculates normal reaction force and friction. the reason it's here and not in 'boxCollision' is because resultant force from all other forces must be calculated first.

        process:
            1. loop through all collisionRects and detect for collisions with solids.
            2) get components of forces acting in the direction of the collision plane and add them to 'resultF', since that's what normal reaction force is.
                imagine this: you put a ball next to a perfectly straight-up wall. the wall won't push on it, since it's not pushing on the wall!
            3) if colliding with the right/left faces of a collisionRect, subtract 90 degrees from all angle calculations, since left/right is perpendicular to top/bottom.
            4) calculate the X and Y components of 'resultF' as the normal reaction force about X and Y.
                normal force about Z has an exception case since the collisionRect can't rotate about the Z-axis.

            the logic behind normal force calculations can be seen here: https://drive.google.com/file/d/1bkBZ3yYHVgOEAl8abxuTd2Ed1gnEsUrB/view?usp=sharing

        note that all normalForce values will be multiplied by 0.999999 to compensate for floating point error, since it'll return a normalForce value that's too low/high otherwise.
            higher normalForce than its actual value is a problem since it'll cause a point to accelerate off the surface (which violates Newton's 3rd law). thus, its value is lowered by 0.001%.
        """
        for crIdx in range(len(game.collisionRect)):
            cr = game.collisionRect[crIdx]  # alias for current collisionRect
            if self.cubeCollisionCalc[crIdx] and (cr.type == 's'):
                self.__bAngle = copy.deepcopy(cr.angle)  # assign collisionRect angle to a private variable, so it can be changed (for the sake of calculation) without actually changing the collisionRect's angle

                resultF = 0
                if (self.collision[crIdx] == 'top') or (self.collision[crIdx] == 'bottom'):
                    if (self.__force[0] * self.__multiplier[crIdx]) > 0:  # multiplier is used here to differentiate between top/bottom for the correct direction
                        resultF += abs(self.__force[0] * math.sin(self.__bAngle[2]))
                    if (self.__force[1] * self.__multiplier[crIdx]) < 0:
                        resultF += abs(self.__force[1] * math.cos(self.__bAngle[2]))

                elif (self.collision[crIdx] == 'right') or (self.collision[crIdx] == 'left'):
                    self.__bAngle[2] -= math.pi / 2
                    if (self.__force[0] * self.__multiplier[crIdx]) < 0:  # multiplier is used here to differentiate between right/left for the correct direction
                        resultF += abs(self.__force[0] * math.sin(self.__bAngle[2]))
                    if (self.__force[1] * self.__multiplier[crIdx]) < 0:
                        resultF += abs(self.__force[1] * math.cos(self.__bAngle[2]))

                elif (self.collision[crIdx] == 'front') or (self.collision[crIdx] == 'back'):
                    if (self.__force[2] * self.__multiplier[crIdx]) < 0:
                        resultF += abs(self.__force[2])
                    # different code for front/back normal force and friction calcs since the Z angle of a collisionRect is always 0
                    self.__normalForce[2] = resultF * self.__multiplier[crIdx] * 0.999999
                    for plane in range(2):
                        self.__friction[plane] = -getSign(self.velocity[plane]) * resultF * self.sf * cr.sf * sin(abs(self.__movingAngle[0]))

                if (self.collision[crIdx] != 'front') and (self.collision[crIdx] != 'back'):
                    self.__normalForce[0] = -resultF * sin(self.__collAngle[2]) * self.__multiplier[crIdx] * 0.999999
                    self.__normalForce[1] = resultF * cos(self.__collAngle[2]) * self.__multiplier[crIdx] * 0.999999
                    # negative coefficients used for friction here since it always acts in the opposite direction to motion
                    if self.__collisionState == 'y':
                        # negative coefficients used for normalForce here since it always acts in the opposite direction to resultant force
                        self.__friction[0] = -getSign(self.velocity[0]) * resultF * cos(self.__collAngle[2]) * self.sf * cr.sf * sin(abs(self.__movingAngle[1]))
                        self.__friction[2] = -getSign(self.velocity[2]) * resultF * cos(self.__collAngle[2]) * self.sf * cr.sf * cos(abs(self.__movingAngle[1]))
                    elif self.__collisionState == 'x':
                        # no need for negative coefficients here since collAngle is negative
                        self.__friction[1] = getSign(self.velocity[1]) * resultF * sin(self.__collAngle[2]) * self.sf * cr.sf * cos(abs(self.__movingAngle[2]))
                        self.__friction[2] = getSign(self.velocity[2]) * resultF * sin(self.__collAngle[2]) * self.sf * cr.sf * sin(abs(self.__movingAngle[2]))

    # check this out to see how I use lines, domains, and ranges for collision detection: https://drive.google.com/file/d/1a0McNZn3RdBdNACSEkrpEFIMrSON3MYZ/view?usp=sharing
    # check this out to see how I get the formulae of the lines: https://drive.google.com/file/d/1xwD0r6H49mgiumBW7Ax1TiJFgu5GsMbu/view?usp=sharing
    def __yCollisionPlane(self, b):  # find "y" from the mathematical form: "y = mx + c" for each collision plane
        """
        :param b: collisionRect object
        :return: dictionary of all values for each equation.

        all 'b.vertex' values represent reference points on the collisionRect's vertices, so that y-intercept can be calculated.
        some reference points are repeated since multiple lines can share the same reference points.
            'left' at 'top' both intersect at the top-left vertex, so their x-coordinates are used for both lines.

        """
        return {
            'left': {'y': (b.grad['y'] * self.cords[0]) + (b.vertex[1][1] - (b.grad['y'] * b.vertex[1][0])), 'm': b.grad['y'], 'c': b.vertex[1][1] - (b.grad['y'] * b.vertex[1][0])},
            'right': {'y': (b.grad['y'] * self.cords[0]) + (b.vertex[0][1] - (b.grad['y'] * b.vertex[0][0])), 'm': b.grad['y'], 'c': b.vertex[0][1] - (b.grad['y'] * b.vertex[0][0])},
            'top': {'y': (b.grad['x'] * self.cords[0]) + (b.vertex[1][1] - (b.grad['x'] * b.vertex[1][0])), 'm': b.grad['x'], 'c': b.vertex[1][1] - (b.grad['x'] * b.vertex[1][0])},
            'bottom': {'y': (b.grad['x'] * self.cords[0]) + (b.vertex[7][1] - (b.grad['x'] * b.vertex[7][0])), 'm': b.grad['x'], 'c': b.vertex[7][1] - (b.grad['x'] * b.vertex[7][0])},
        }

    def __xCollisionPlane(self, b):  # find "x" from the mathematical form: "x = my + c" for each collision plane
        """
        :param b: collisionRect object
        :return: dictionary of all values for each equation.

        all 'b.vertex' values represent reference points on the collisionRect's vertices, so that x-intercept can be calculated.
        some reference points are repeated since multiple lines can share the same reference points.
            'left' at 'top' both intersect at the top-left vertex, so their y-coordinates are used for both lines.
        all values for 'b.grad' are swapped and negated since "x = my + c" is essentially the normal to "y = mx + c".
            thus, "m" must be negated and reciprocated, meaning m(X) = -(1 / m(Y)) and m(Y) = -(1 / m(X)).
        """
        return {
            'left': {'x': - (b.grad['x'] * self.cords[1]) + (b.vertex[1][0] + (b.grad['x'] * b.vertex[1][1])), 'm': -b.grad['x'], 'c': b.vertex[1][0] + (b.grad['x'] * b.vertex[1][1])},
            'right': {'x': - (b.grad['x'] * self.cords[1]) + (b.vertex[0][0] + (b.grad['x'] * b.vertex[0][1])), 'm': -b.grad['x'], 'c': b.vertex[0][0] + (b.grad['x'] * b.vertex[0][1])},
            'top': {'x': - (b.grad['y'] * self.cords[1]) + (b.vertex[1][0] + (b.grad['y'] * b.vertex[1][1])), 'm': -b.grad['y'], 'c': b.vertex[1][0] + (b.grad['y'] * b.vertex[1][1])},
            'bottom': {'x': - (b.grad['y'] * self.cords[1]) + (b.vertex[7][0] + (b.grad['y'] * b.vertex[7][1])), 'm': -b.grad['y'], 'c': b.vertex[7][0] + (b.grad['y'] * b.vertex[7][1])}
        }

    # detects and resolves collisions between spheres (points) and static cuboids (collision rects)
    def __boxCollision(self):
        """
        this method detects and resolves collisions between spheres (points) and static cuboids (collision rects).
        my method uses AABB collision detection.

        process:
            1. loop through all collisionRects.
            2. get the line equations for X and Y to enable plane collision detection.
                y = mx + c is used for smaller values of bAngle (<=45°) since gradient m will always be <=1 (since tan(45) = 1).
                x = my + c is used for larger values of bAngle (>45°) since tan(bAngle) will get extremely large, causing large floating point error uncertainty.
                    if this is not used, large value of bAngle (on the colliding plane) will cause colliding points to skyrocket instantly due to extremely large values of gradient m.
            3. if a point is:
                a) intersecting a collisionRect with a large tolerance 'collisionCalcTolerance', apply normal reaction force and friction.
                b) intersecting a collisionRect with a small tolerance 'collisionTolerance', teleport the point to the collisionRect surface and apply an impulse.
                c) fully within a collisionRect with a small tolerance 'collisionTolerance', apply liquid physics if the collisionRect is a liquid.
                detection is done using domains/ranges of lines: https://drive.google.com/file/d/1a0McNZn3RdBdNACSEkrpEFIMrSON3MYZ/view?usp=sharing
                these tolerances are used to compensate for floating point error.
                if not used, collisions will be detected every other frame rather than every frame even if a point visually slides down a surface.
                this is a problem since the point will experience an impulse nearly every frame rather than just once when colliding with a collisionRect.
                    if elasticity >= 1, the point would accelerate every other frame (speed up infinitely).
                    if elasticity < 1, the point would decelerate every other frame (slow down infinitely).
                    both of these outcomes would occur due floating point error in trig functions and position values.
                check out this link to see some examples: https://drive.google.com/file/d/1i6ZdYdIu9J1fGjqJSI3Ou5GV-YMcyKag/view?usp=sharing
            4. if the point is in front of a collisionRect's edge, store that edge's axis (ignoring the collisionRect's orientation) in 'vertexState'.
                vertexState will be used to fetch the indexes of the grouped vertices depending on its axis.
                    here's why this must be done: https://drive.google.com/file/d/1llq6UTfJHZ2GJic5s8510RJoKKEBbg1Y/view?usp=sharing
                ultimately, this will allow a point to determine the 2 closest vertices of each collisionRect to the point to allow for edge collision detection.
                here's how 'vertexState' is determined: https://drive.google.com/file/d/1PQrnfejqzLJlD6GdVNaNNZzTivElZJHb/view?usp=sharing
                    here's a 2D-ish visualization of this: https://drive.google.com/file/d/1Ne9uYwj5Y1x832fyxHiSnWMDw0zEPRHm/view?usp=sharing, https://drive.google.com/file/d/1dtp28rJAdf8S78__yX-8-ykr1pub44e5/view?usp=sharing
            5. if the point is in front of a plane, set 'lastCollision' to the plane it's in front of. also factors in the point's radius.
                this value should never reset to allow for accurate liquid physics calculations.
                radius is added when the plane is 'right'/'top'/'front', since those planes face the positive x/y/z axes (respectively).
                radius is subtracted when the plane is 'left'/'bottom'/'back', since those planes face the negative x/y/z axes (respectively).
            6. if the point's CENTER is in front of a plane, set 'collision' to the plane it's in front of.
                this value resets if the point isn't in front of a plane anymore.
                'collision' is used to get what plane a point is currently in front of, so that the appropriate calculations for collision resolution can be applied, e.g.:
                    whether to use y = mx + c OR x = my + c, direction of resultant and normal reaction forces, direction & magnitude of impulse.
            see below for point 7 onwards.
        """
        cubeCollision = False
        cubeSubmersion = False
        for crIdx in range(len(game.collisionRect)):
            cr = game.collisionRect[crIdx]  # alias for current collisionRect

            self.__bAngle = copy.deepcopy(cr.angle)  # assign collisionRect angle to a private variable, so it can be changed (for the sake of calculation) without actually changing the collisionRect's angle
            self.__yCollisionLine = self.__yCollisionPlane(cr)
            self.__xCollisionLine = self.__xCollisionPlane(cr)

            # aliasing variables for increased readability
            topY = self.__yCollisionLine['top']['y']
            bottomY = self.__yCollisionLine['bottom']['y']
            rightY = self.__yCollisionLine['right']['y']
            leftY = self.__yCollisionLine['left']['y']
            radOffsetCos = self.radius / cos(self.__bAngle[2])
            radOffsetSin = self.radius / sin(self.__bAngle[2])

            # it's appropriate to use y = mx + c for collision detection here (even for large angles) since floating point error has negligible effect on detection
            self.cubeCollisionCalc[crIdx] = (self.cords[1] <= (collisionCalcTolerance + topY + radOffsetCos)) and (self.cords[1] >= (-collisionCalcTolerance + bottomY - radOffsetCos)) and (
                    self.cords[1] <= (collisionCalcTolerance + rightY + radOffsetSin)) and (self.cords[1] >= (-collisionCalcTolerance + leftY - radOffsetSin)) and (self.cords[2] <= (collisionCalcTolerance + cr.plane['front'] + self.radius)) and (
                                                    self.cords[2] >= (-collisionCalcTolerance + cr.plane['back'] - self.radius))  # True if any part of the point is inside a collisionRect, given a collisionCalcTolerance
            self.cubeCollision[crIdx] = (self.cords[1] <= (collisionTolerance + topY + radOffsetCos)) and (self.cords[1] >= (-collisionTolerance + bottomY - radOffsetCos)) and (
                    self.cords[1] <= (collisionTolerance + rightY + radOffsetSin)) and (self.cords[1] >= (-collisionTolerance + leftY - radOffsetSin)) and (self.cords[2] <= (collisionTolerance + cr.plane['front'] + self.radius)) and (
                                                self.cords[2] >= (-collisionTolerance + cr.plane['back'] - self.radius))  # True if any part of the point is inside a collisionRect, given a collisionTolerance
            self.cubeSubmersion[crIdx] = (self.cords[1] <= (collisionTolerance + topY - radOffsetCos)) and (self.cords[1] >= (-collisionTolerance + bottomY + radOffsetCos)) and (
                    self.cords[1] <= (collisionTolerance + rightY - radOffsetSin)) and (self.cords[1] >= (-collisionTolerance + leftY + radOffsetSin)) and (self.cords[2] <= (collisionTolerance + cr.plane['front'] - self.radius)) and (
                                                 self.cords[2] >= (-collisionTolerance + cr.plane['back'] + self.radius))  # cubeCollision but with reversed radii calcs, since this is cubeSUBMERSION after all!

            # check out the logic here: https://drive.google.com/file/d/1B-GqxPcpGkWAE_ogzMvYntTNmt8R99gT/view?usp=drive_link
            self.__vertexState = ''  # stores the facing axis of the nearest vertex
            if ((self.cords[1] > rightY) or (self.cords[1] < leftY)) and ((self.cords[1] > topY) or (self.cords[1] < bottomY)) and ((self.cords[2] <= cr.plane['front']) and (self.cords[2] >= cr.plane['back'])):  # x > right, x < left, y > top, y < bottom, back < z < front
                self.__vertexState = 'z'
            elif ((self.cords[1] > rightY) or (self.cords[1] < leftY)) and ((self.cords[1] <= topY) and (self.cords[1] >= bottomY)) and ((self.cords[2] > cr.plane['front']) or (self.cords[2] < cr.plane['back'])):  # x > right, x < left, bottom < y < top, z > front, z < back
                self.__vertexState = 'y'
            elif ((self.cords[1] <= rightY) and (self.cords[1] >= leftY)) and ((self.cords[1] > topY) or (self.cords[1] < bottomY)) and ((self.cords[2] > cr.plane['front']) or (self.cords[2] < cr.plane['back'])):  # left < x < right, y > top, y < bottom, z > front, z < back
                self.__vertexState = 'x'

            # self.lastCollision represents the surface of a collision cuboid that the point was LAST in front of, factoring in its radius as well. this value never resets.
            if (self.cords[1] <= (rightY + self.radius)) and (self.cords[1] >= (leftY - self.radius)) and (self.cords[2] <= (cr.plane['front'] + self.radius)) and (self.cords[2] >= (cr.plane['back'] - self.radius)):
                if self.cords[1] >= (topY + self.radius):
                    self.lastCollision[crIdx] = 'top'
                elif self.cords[1] <= (bottomY - self.radius):
                    self.lastCollision[crIdx] = 'bottom'
            elif (self.cords[1] <= topY) and (self.cords[1] >= bottomY) and (self.cords[2] <= cr.plane['front']) and (self.cords[2] >= cr.plane['back']):
                if self.cords[1] >= (rightY + self.radius):
                    self.lastCollision[crIdx] = 'right'
                elif self.cords[1] <= (leftY - self.radius):
                    self.lastCollision[crIdx] = 'left'
            elif (self.cords[1] <= (topY + self.radius)) and (self.cords[1] >= (bottomY - self.radius)) and (self.cords[1] <= (rightY + self.radius)) and (self.cords[1] >= (leftY - self.radius)):
                if self.cords[2] >= (cr.plane['front'] - self.radius):
                    self.lastCollision[crIdx] = 'front'
                elif self.cords[2] <= (cr.plane['back'] + self.radius):
                    self.lastCollision[crIdx] = 'back'

            if not self.cubeCollision[crIdx]:  # causes self.collision[crIdx] to reset when not in front of a plane
                self.collision[crIdx] = ''
            if (self.cords[1] <= rightY) and (self.cords[1] >= leftY) and (self.cords[2] <= (cr.plane['front'])) and (self.cords[2] >= (cr.plane['back'])):
                if self.cords[1] >= topY:
                    self.collision[crIdx] = 'top'
                elif self.cords[1] <= bottomY:
                    self.collision[crIdx] = 'bottom'
            elif (self.cords[1] <= topY) and (self.cords[1] >= bottomY) and (self.cords[2] <= cr.plane['front']) and (self.cords[2] >= cr.plane['back']):
                if self.cords[1] >= rightY:
                    self.collision[crIdx] = 'right'
                elif self.cords[1] <= leftY:
                    self.collision[crIdx] = 'left'
            elif (self.cords[1] <= topY) and (self.cords[1] >= bottomY) and (self.cords[1] <= rightY) and (self.cords[1] >= leftY):
                if self.cords[2] >= (cr.plane['front']):
                    self.collision[crIdx] = 'front'
                elif self.cords[2] <= (cr.plane['back']):
                    self.collision[crIdx] = 'back'

            # get the distance until edge/vertex collision
            if (self.collision[crIdx] == '') or (self.__vertexState != ''):  # "why should we resolve vertex/edge collisions if the point is in front of a face on the collision rect?" hence, this if statement is used to optimize performance.
                minDist, vertexIdx = self.__getVertexDist(cr)  # get the distance to a vertex/edge collision as well as the index of the vertex/vertices, respectively

            # here's why I use 'multiplier': https://drive.google.com/file/d/1Gpy3J38fYBKXRfSFU2cz9M1vn91dDYWK/view?usp=drive_link
            if (self.lastCollision[crIdx] == 'right') or (self.lastCollision[crIdx] == 'top') or (self.lastCollision[crIdx] == 'front'):
                self.__multiplier[crIdx] = 1
            else:
                self.__multiplier[crIdx] = -1  # radius displacement is reversed for left, bottom, and back since they face the negative x/y/z axes, respectively

            """
            7. detect collisions between points and planes:
                if the point is in front of a plane (vertexState == '' and collision != '') AND a collisionRect is being collided with (cubeCollisionCalc).
            8. detect collisions between points and edges:
                if the point is in front of an edge (vertexState != '') AND https://drive.google.com/file/d/14ooXx_oDUzhqFVb1EDGZTB3ShXxDIFNU/view?usp=sharing AND the collisionRect is a solid (cr.type == 's').
            9. detect collisions between points and vertices:
                if the point's distance to the nearest vertex is ever less than its radius.
            10. if steps 7, 8, 9 are all False, reset 'colliding' to False so that an impulse can be applied on the next collision.
            11. if the point isn't colliding with any collisionRect, reset all values that depend on undergoing a collision to 0.
            """

            # detect collisions between points and planes (flat surfaces) on a collision rect (cuboid)
            if (self.__vertexState == '') and (self.collision[crIdx] != '') and self.cubeCollisionCalc[crIdx]:
                self.__planeCollision(crIdx, cr)

            # detect collisions between points and edges on a SOLID collision rect (cuboid)
            # see the 'getVertexDist' method for the logic behind 'minDist'
            elif (self.__vertexState != '') and (minDist <= (distance(cr.vertex[vertexIdx[0]], cr.vertex[vertexIdx[1]]))) and (cr.type == 's'):
                self.cords = copy.deepcopy(self.oldCords)  # freeze the point (unfinished/failed implementation)

            # detect collisions between points and vertices (corners) on a SOLID collision rect (cuboid)
            # see the 'getVertexDist' method for the logic behind 'cr.vertex[vertexIdx]' (closest vertex to the point at index 'vertexIdx')
            elif (self.collision[crIdx] == '') and (self.__vertexState == '') and (distance(cr.vertex[vertexIdx], self.cords) <= self.radius) and (cr.type == 's'):
                self.cords = copy.deepcopy(self.oldCords)  # freeze the point (unfinished/failed implementation)

            # if none of the cases above are True, then the point isn't colliding with any collisionRect
            else:
                self.colliding[crIdx] = False

            cubeCollision = cubeCollision or self.cubeCollisionCalc[crIdx]  # True if cubeCollisionCalc is ever True
            cubeSubmersion = cubeSubmersion or self.cubeSubmersion[crIdx]  # True if cubeSubmersion is ever True

        if not cubeCollision:  # reset values that depend on a solid cube collision when not colliding with ANY collisionRect
            self.__normalForce = [0, 0, 0]
            self.__friction = [0, 0, 0]
            self.__impulse = [0, 0, 0]
        if not cubeSubmersion:  # reset values that depend on being submerged in a liquid when not submerged in ANY collisionRect
            self.__liquidUpthrust = [0, 0, 0]
            self.__liquidDrag = [0, 0, 0]
            self.__submergedVolume = 0
            self.__submergedArea = 0
            self.__submergedRadius = 0

    def __getVertexDist(self, cr):
        """
        :param cr: collisionRect object.

        this method is used to get the distance and index(es) to the nearest vertex(es), which will be used for vertex/edge collision detection.
        due to this method's highly mathematical and logical approach, all comments will be in-line for increased readability.
        """
        vertexDist = []  # distance to each edge/vertex, depending on the type of collision
        vIdx = []  # stores (specific) index values in a specific order from the collisionRect.vertex list
        vertexIdx = []  # stores index of closest vertex indexes
        minDist = float('inf')  # context of value changes depending on type of collision (see the bookmark below)

        # group vertices based on 'vertexState' because of this: https://drive.google.com/file/d/1llq6UTfJHZ2GJic5s8510RJoKKEBbg1Y/view?usp=drive_link
        if self.__vertexState == 'x':
            vIdx = [[0, 1], [2, 7], [3, 6], [4, 5]]
        elif self.__vertexState == 'y':
            vIdx = [[0, 7], [1, 2], [3, 4], [5, 6]]
        elif self.__vertexState == 'z':
            vIdx = [[0, 5], [1, 4], [2, 3], [6, 7]]
        else:  # when undergoing a corner collision, don't group vertices (since only the nearest vertex is relevant)
            for inc in range(8):
                vIdx.append(inc)

        if self.__vertexState != '':  # edge collision detection
            dist = []  # distance to each vertex as indicated by vIdx
            for d in range(len(vIdx)):
                dist.append([])
                vertexDist.append(0)
                for h in range(len(vIdx[d])):
                    tempDist = distance(cr.vertex[vIdx[d][h]], self.cords)  # value of d1 when h == 0, and d2 when h == 1
                    if tempDist >= self.radius:  # used to prevent sqrt(-number)
                        # check out the maths & logic for this here: https://drive.google.com/file/d/14ooXx_oDUzhqFVb1EDGZTB3ShXxDIFNU/view?usp=sharing (edge-collision-detection.JPG)
                        dist[d].append(math.sqrt(tempDist ** 2 - self.radius ** 2))  # gets the distance from each vertex to the current sphere's position (value of v1/v2 from edge-collision-detection.JPG)
                        vertexDist[d] += dist[d][h]  # sum of v1 and v2 as seen in edge-collision-detection.JPG, where dist[d][0] = v1 and dist[d][1] = v2
                    else:  # if tempDist < radius, then a collision is happening
                        dist[d].append(0)
        else:  # vertex (corner) collision detection
            for d in cr.vertex:
                vertexDist.append(distance(d, self.cords))

        # get the closest vertex to the point
        for ve in range(len(vertexDist)):
            if vertexDist[ve] < minDist:
                minDist = vertexDist[ve]  # get the new smallest value of calculated v1 + v2 (if edge) OR distance to the new closest vertex (if vertex)
                vertexIdx = vIdx[ve]  # get the index(ex) of the new closest vertex(es)

        return minDist, vertexIdx

    def __planeCollision(self, crIdx, cr):
        if (self.collision[crIdx] == 'right') or (self.collision[crIdx] == 'left'):
            # shift angle by 90° since perpendicular surfaces to the collision rect (left & right) are, well... perpendicular (to top & bottom)
            # angle is subtracted since all movement is reversed since it's, well... perpendicular
            # this also makes dealing with gradients easier (I only have to get magnitude of gradient, not whether its positive or negative)
            self.__bAngle[2] -= math.pi / 2
        self.__collAngle = copy.deepcopy(self.__bAngle)

        # determine whether to use y = mx + c or x = my + c based on the size of bAngle (which directly affects gradient m)
        # if m is too large for y = mx + c, use x = my + c for a much smaller gradient m (to increase floating point precision)
        # check out this link to see the logic behind this: https://drive.google.com/file/d/1s67QaMXnC3LGD11jn75S9DDp1HxjND_O/view?usp=sharing
        if abs(math.degrees(self.__bAngle[2])) <= 45:
            self.__collisionState = 'y'
        else:
            self.__collisionState = 'x'

        # determine which collision calculations to use if the collisionRect is a solid or liquid
        if self.cubeCollision[crIdx]:
            if cr.type == 's':
                self.__planeCollisionSolid(crIdx)
            elif cr.type == 'l':
                self.__planeCollisionLiquid(crIdx, cr)

    def __planeCollisionLiquid(self, crIdx, cr):
        # get cap volume with submerged radius, etc.
        # also disable gas upthrust for submerged parts
        submergedAmt = 0
        if (self.collision[crIdx] == 'front') or (self.collision[crIdx] == 'back'):
            submergedAmt = abs((cr.plane[self.collision[crIdx]] + (self.__multiplier[crIdx] * self.radius) - self.cords[2]))  # TODO: check out the maths for this here:
        elif self.__collisionState == 'y':
            submergedAmt = abs((self.__yCollisionLine[self.collision[crIdx]]['y'] + (self.__multiplier[crIdx] * self.radius / cos(self.__bAngle[2])) - self.cords[1]) * cos(self.__bAngle[2]))  # TODO: check out the maths for this here:
        elif self.__collisionState == 'x':
            submergedAmt = abs((self.__xCollisionLine[self.collision[crIdx]]['x'] - (self.__multiplier[crIdx] * self.radius / sin(self.__bAngle[2])) - self.cords[0]) * sin(self.__bAngle[2]))
        self.__submergedVolume = capVolume(submergedAmt, self.radius)
        self.__submergedArea = capArea(submergedAmt, self.radius)
        self.__submergedRadius = submergedAmt
        if self.cubeSubmersion[crIdx]:  # if fully submerged
            self.__submergedVolume = copy.deepcopy(self.__volume)
        if self.__submergedRadius > self.radius:  # if half of sphere is submerged
            self.__submergedArea = self.__halfArea
            self.__submergedRadius = self.radius
        for axis in range(3):
            self.__liquidUpthrust[axis] = cr.density * -globalVars['gField'][axis] * self.__submergedVolume  # Upthrust = fluid density * gravitational field strength * submerged volume
            self.__liquidDrag[axis] = (0.5 * cr.viscosity * (self.velocity[axis] ** 2) * -getSign(self.velocity[axis]) * self.__submergedArea)  # Drag = 1/2 cpAv²

    def __planeCollisionSolid(self, crIdx):
        """
        :param crIdx: index of the colliding collisionRect in the collisionRect list.
        :param cr: colliding collisionRect object

        this method is used to resolve collisions between point and collisionRect planes (surfaces).

        process:
            1. get the collisionRect object from the collisionRect list.
            2. check collisionState.
                if it's 'y': use y = mx + c.
                if it's 'x': use x = my + c.
                this is done so that gradient 'm' is always <= 1 so that there's lots of decimal places available for more accurate floating point precision.
            3. teleport the point to the surface of the plane by getting the x/y coordinate of its line equation, displacing the teleportation by the point's radius.
                a) if the point hasn't collided with a collisionRect yet, reset the apply an impulse based on the momentum of the point relative to the collisionRect plane.
                    imagine dropping a ball onto a slope. it won't fully stop as it hits the slope; it'll be shot down the slope! that's why an impulse is applied at the point of collision here.
                b) if the point has already collided, only teleport the point.
                radius is accounted for here otherwise half the point will get stuck inside the collisionRect.
            4. if the point is colliding with the 'front'/'back' of a collisionRect, no need for any fancy line equations.
                just teleport the point to the surface of the plane, factoring in radius.

        for all radius displacements, 'multiplier' is used to get which direction to displace the point by, since displacement should be reversed for 'left'/'bottom'/'front' collisions.

        """

        cr = game.collisionRect[crIdx]  # get the colliding collisionRect object
        if (self.collision[crIdx] == 'top') or (self.collision[crIdx] == 'right') or (self.collision[crIdx] == 'bottom') or (self.collision[crIdx] == 'left'):  # colliding with top/right/bottom/left plane
            if self.__collisionState == 'y':
                if not self.colliding[crIdx]:
                    self.colliding[crIdx] = True
                    self.cords[1] = self.__yCollisionLine[self.collision[crIdx]]['y'] + (self.__multiplier[crIdx] * self.radius / cos(self.__bAngle[2]))  # use y = mx + c where m <= 1 and y = cords[1]
                    self.oldCords[0] = copy.deepcopy(self.cords[0])
                    self.oldCords[1] = copy.deepcopy(self.cords[1])
                    resultP = (self.mass * self.velocity[0] * cos(self.__bAngle[2])) + (self.mass * self.velocity[1] * sin(self.__bAngle[2]))
                    self.__impulse[0] = resultP * physicsTime * cos(self.__bAngle[2]) * self.e
                    self.__impulse[1] = resultP * physicsTime * sin(self.__bAngle[2]) * self.e
                else:
                    self.__impulse = [0, 0, 0]
                    self.cords[1] = self.__yCollisionLine[self.collision[crIdx]]['y'] + (self.__multiplier[crIdx] * self.radius / cos(self.__bAngle[2]))
            elif self.__collisionState == 'x':
                if not self.colliding[crIdx]:
                    self.colliding[crIdx] = True
                    self.cords[0] = self.__xCollisionLine[self.collision[crIdx]]['x'] - (self.__multiplier[crIdx] * self.radius / sin(self.__bAngle[2]))  # use x = my + c where m <= 1 and x = cords[0]
                    self.oldCords[0] = copy.deepcopy(self.cords[0])
                    self.oldCords[1] = copy.deepcopy(self.cords[1])
                    resultP = (self.mass * self.velocity[0] * cos(self.__bAngle[2])) + (self.mass * self.velocity[1] * sin(self.__bAngle[2]))
                    self.__impulse[0] = resultP * physicsTime * cos(self.__bAngle[2]) * self.e
                    self.__impulse[1] = resultP * physicsTime * sin(self.__bAngle[2]) * self.e
                else:
                    self.__impulse = [0, 0, 0]
                    self.cords[0] = self.__xCollisionLine[self.collision[crIdx]]['x'] - (self.__multiplier[crIdx] * self.radius / sin(self.__bAngle[2]))
        elif (self.collision[crIdx] == 'front') or (self.collision[crIdx] == 'back'):
            if not self.colliding[crIdx]:
                self.colliding[crIdx] = True
                self.cords[2] = cr.plane[self.collision[crIdx]] + (self.radius * self.__multiplier[crIdx])
                self.oldCords[2] = copy.deepcopy(self.cords[2])
            else:
                self.cords[2] = cr.plane[self.collision[crIdx]] + (self.radius * self.__multiplier[crIdx])


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
        # if self.__height >= (self.origLength * self.maxStrain):
        #     self.snap()  # MASSIVE WIP

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
                self.constrainForce[u] = self.stiffness * (self.diff[u] / self.__height) * (self.origLength - self.__height)  # (F = kx) check out the maths for this using this link:
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
        game.updateLists()  # more points and joints means that relevant info needs to be updated for each point

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
        game.updateLists()  # more points and joints means that relevant info needs to be updated for each point


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
        self.vertex = []  # vertices ordered in: [['right', 'top', 'front'], ['left', 'top', 'front'], ['left', 'bottom', 'front'], ['left', 'bottom', 'back'], ['left', 'top', 'back'], ['right', 'top', 'back'], ['right', 'bottom', 'back'], ['right', 'bottom', 'front']]
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
        if self.vertex[0][0] != self.vertex[7][0]:
            my = (self.vertex[0][1] - self.vertex[7][1]) / (self.vertex[0][0] - self.vertex[7][0])
        else:
            my = float('inf')
        self.grad = {
            'x': mx,
            'y': my
        }


game = Main()

# makes a cube using points and joints
if not imports:
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

    game.collisionRect.append(CollisionRect((100, 50, 50), [-60, 0, 0], [math.radians(0), math.radians(0), math.radians(0.001)], 1000, 10, 1, 0.8, 's'))  # CANNOT be negative angle or above 90 (make near-zero for an angle of 0)
    game.collisionRect.append(CollisionRect((100, 50, 50), [60, 0, 0], [math.radians(0), math.radians(0), math.radians(30)], 1000, 10, 1, 0.8, 's'))
    game.collisionRect.append(CollisionRect((50, 50, 50), [170, 0, 0], [math.radians(0), 0, math.radians(0.001)], 2000, 1, 1, 0.5, 'l'))

# make the borders (which are hidden collisionRects)
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
