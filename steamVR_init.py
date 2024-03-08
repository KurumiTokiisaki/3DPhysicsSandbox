# base Vizard libraries
import viz
import steamvr
# for trig functions
import myGUI
from config import *

# link HMD (Head-Mounted Display) to program
hmdConfig = steamvr.HMD()

# camera speed
minCamSpeed = 5 / renderRate
maxCamSpeed = minCamSpeed * 4

# degrees of freedom to prevent joystick drift. this value can lower the higher-quality a controller is.
freedomDegrees = 0.3
yFreedomDegrees = 0.3
# gets the HMD's controllers
controllers = [steamvr.getControllerList()[0], steamvr.getControllerList()[1]]
hmd = hmdConfig.getSensor()  # get the gyroscope and position details of the HMD
controllerAmt = 2  # set this to 2 since there's 2 controllers


# main class for HMD
class Main:
    def __init__(self) -> None:
        # max speed of camera
        self.camSpeed = minCamSpeed
        # camera variables
        self.apparentCamCords = [0, 0, 0]  # camera cords when the HMD's relative position isn't taken into account
        self.camCords = [0, 0, 0]  # actual camera cords after adding the HMD's relative position to apparentCamCords
        self.camAngle = [0, 0, 0]  # HMD's facing angle
        self.camVelocity = [0, 0, 0]
        self.handAngle = [[0, 0, 0], [0, 0, 0]]

        self.hmdPos = hmd.getPosition()  # position of the HMD relative to the computer IRL
        # controller sprites to render
        self.hand = [Point('l'), Point('r')]

        self.anim = [myGUI.CircleAnim(self.hand[0], 4, 0.1, 0.01, [100, 5, 1], True), myGUI.CircleAnim(self.hand[1], 4, 0.1, 0.01, [100, 5, 1], True)]

    def main(self) -> None:
        self.hmdPos = hmd.getPosition()  # update the position of the camera by querying the HMD's new position every frame
        self.moveCam()
        self.updateHMD()

        # update the position and facing angle of the camera in the Vizard game scene
        viz.MainView.setPosition(self.camCords)
        viz.MainView.setEuler(self.camAngle)
        # update visuals about both hands and their animations
        for c in range(2):
            self.hand[c].sphere.setPosition(self.hand[c].cords)
            self.hand[c].sphere.setEuler(self.handAngle[c])
            self.anim[c].draw()

    # set controller position relative to camera position
    def updateHMD(self) -> None:
        self.camAngle = hmd.getEuler()  # update the angle of the camera by querying teh HMD's new orientation every frame

        # update info about both hands (position & orientation)
        for c in range(2):
            self.hand[c].cords = [controllers[c].getPosition()[0] + self.apparentCamCords[0], controllers[c].getPosition()[1] + self.apparentCamCords[1], controllers[c].getPosition()[2] + self.apparentCamCords[2]]
            self.handAngle[c] = controllers[c].getEuler()

    # move camera depending on joystick position
    def moveCam(self) -> None:
        """
        the left joystick is used to control lateral position (X & Z axes), and the right joystick is used to control vertical position only (Y axis).
        when setting camVelocity[0] and camVelocity[2], the tilt of the left joystick about both its axes (since it can be tilted up/down AND left/right) are taken into account to allow full 360 degree motion.
        left/right movement is taken into account by reversing the trig functions and making their angle coefficients negative, since left/right is perpendicular to forward/back.
        camAngle is used here to allow the camera to move relative to the current facing position rather than to the world axes.
        check out this link for the mathematical proof: https://drive.google.com/file/d/1y_UX1Otwlxe1toA1COCcLJ8Q-jlt4qe9/view?usp=sharing
        """
        if controllers[1].getButtonState() == 2:
            self.camSpeed = maxCamSpeed
        else:
            self.camSpeed = minCamSpeed

        # if the left controller's joystick moves outside its degrees of freedom, move the camera based on current facing angle
        if (abs(controllers[0].getThumbstick()[0]) > freedomDegrees) or (abs(controllers[0].getThumbstick()[1]) > freedomDegrees) or (abs(controllers[0].getTrackpad()[0] > freedomDegrees)):
            self.camVelocity[0] = (controllers[0].getThumbstick()[1] * math.sin(math.radians(self.camAngle[0])) * self.camSpeed) + (controllers[0].getThumbstick()[0] * math.cos(-math.radians(self.camAngle[0])) * self.camSpeed)
            self.camVelocity[2] = (controllers[0].getThumbstick()[1] * math.cos(math.radians(self.camAngle[0])) * self.camSpeed) + (controllers[0].getThumbstick()[0] * math.sin(-math.radians(self.camAngle[0])) * self.camSpeed)
        else:  # if the left joystick isn't being tilted (within the degrees if freedom), don't move!
            self.camVelocity[0] = 0
            self.camVelocity[2] = 0

        # right controller's degrees of freedom are different to the left controller's, hence yFreedomDegrees
        if abs(controllers[1].getThumbstick()[1]) > yFreedomDegrees:
            self.camVelocity[1] = controllers[1].getThumbstick()[1] * self.camSpeed
        else:  # if the right joystick isn't being tilted (within the degrees if freedom), don't move!
            self.camVelocity[1] = 0

        # change camera coordinates depending on velocity and current position
        for c in range(3):
            # adds velocity to static position of camera
            self.apparentCamCords[c] += self.camVelocity[c]
            # adds static position of camera with HMD position IRL
            self.camCords[c] = self.apparentCamCords[c] + hmd.getPosition()[c]


class Point:
    def __init__(self, lr: str) -> None:
        self.radius = handRadius
        if lr == 'l':
            self.sphere = controllers[0].addModel()  # add left controller model to the Vizard game scene
        elif lr == 'r':
            self.sphere = controllers[1].addModel()  # add right controller model to the Vizard game scene
        self.cords = [0, 0, 0]
