# base Vizard libraries
import viz
import vizfx
import vizshape
import vizconnect
import steamvr
import vizact
from config import calcRate
# for trig functions
import myGUI
from config import *
from globalFunctions import buttonPressed

# link HMD to program
hmdConfig = steamvr.HMD()

# camera speed
minCamSpeed = 10 / renderRate
maxCamSpeed = minCamSpeed * 2

# degrees of freedom to prevent joystick drift
freedomDegrees = 0.5
yFreedomDegrees = 0.5
# gets the HMD's controllers
controllers = [steamvr.getControllerList()[0], steamvr.getControllerList()[1]]
hmd = hmdConfig.getSensor()
controllerAmt = 2


# main class for HMD
class Main:
    def __init__(self):
        # test object for reference
        # self.testAvatar = viz.addAvatar('vcc_male2.cfg').setPosition([0, 0, 5])
        # max speed of camera
        self.camSpeed = minCamSpeed
        # camera variables
        self.apparentCamCords = [0, 0, 0]
        self.camCords = [0, 0, 0]
        self.camAngle = [0, 0, 0]
        self.camVelocity = [0, 0, 0]
        self.handAngle = [[0, 0, 0], [0, 0, 0]]

        self.hmdPos = hmd.getPosition()
        # controller sprites to render
        self.hand = [Point('l'), Point('r')]

        self.anim = [myGUI.CircleAnim(self.hand[0], 4, 0.1, 0.01, [100, 5, 1], True), myGUI.CircleAnim(self.hand[1], 4, 0.1, 0.01, [100, 5, 1], True)]

    def main(self):
        # gets position of HMD IRL
        self.hmdPos = hmd.getPosition()
        self.moveCam()
        self.updateHMD()

        viz.MainView.setEuler(self.camAngle)
        viz.MainView.setPosition(self.camCords)
        for c in range(2):
            self.hand[c].sphere.setPosition(self.hand[c].cords)
            self.hand[c].sphere.setEuler(self.handAngle[c])
            self.anim[c].draw()

    # set controller position relative to camera position
    def updateHMD(self):
        self.camAngle = hmd.getEuler()

        for c in range(2):
            self.hand[c].cords = [controllers[c].getPosition()[0] + self.apparentCamCords[0], controllers[c].getPosition()[1] + self.apparentCamCords[1], controllers[c].getPosition()[2] + self.apparentCamCords[2]]
            self.handAngle[c] = controllers[c].getEuler()

    # move camera depending on joystick position
    def moveCam(self):
        # if right controller's rear finger trigger is pressed, increase the camera's max speed
        if controllers[1].getButtonState() == 2:
            self.camSpeed = maxCamSpeed
        else:
            self.camSpeed = minCamSpeed

        # if the left controller's joystick moves outside its degrees of freedom, move the camera based on current facing angle
        if (abs(controllers[0].getThumbstick()[0]) > freedomDegrees) or (abs(controllers[0].getThumbstick()[1]) > freedomDegrees):
            self.camVelocity[0] = (controllers[0].getThumbstick()[1] * math.sin(math.radians(self.camAngle[0])) * self.camSpeed) + (controllers[0].getThumbstick()[0] * math.cos(-math.radians(self.camAngle[0])) * self.camSpeed)
            self.camVelocity[2] = (controllers[0].getThumbstick()[1] * math.cos(math.radians(self.camAngle[0])) * self.camSpeed) + (controllers[0].getThumbstick()[0] * math.sin(-math.radians(self.camAngle[0])) * self.camSpeed)
        else:
            self.camVelocity[0] = 0
            self.camVelocity[2] = 0

        # right controller's degrees of freedom are different to the left controller's, hence yFreedomDegrees
        if abs(controllers[1].getThumbstick()[1]) > yFreedomDegrees:
            self.camVelocity[1] = controllers[1].getThumbstick()[1] * self.camSpeed
        else:
            self.camVelocity[1] = 0

        # change camera coordinates depending on velocity and current position
        for c in range(3):
            # adds velocity to static position of camera
            self.apparentCamCords[c] += self.camVelocity[c]
            # adds static position of camera with HMD position IRL
            self.camCords[c] = self.apparentCamCords[c] + hmd.getPosition()[c]


class Point:
    def __init__(self, lr):
        self.radius = handRadius
        if lr == 'l':
            self.sphere = controllers[0].addModel()
        elif lr == 'r':
            self.sphere = controllers[1].addModel()
        self.cords = [0, 0, 0]
