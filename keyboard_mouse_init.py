# base Vizard libraries
import viz
import vizfx
import vizconnect
import vizshape
import vizact
# used for trig functions
import math
import myGUI
from config import *
from globalFunctions import buttonPressed

# disable built-in mouse commands
viz.mouse.setOverride()

# mouse sensitivity
sensitivity = 25 / renderRate  # use maximum dpi and lowest sensitivity for most accurate results

# camera speed
minCamSpeed = 10 / renderRate
maxCamSpeed = minCamSpeed * 2

# scroll speed (for hand)
scrollSpeed = 0.015 / renderRate
# hide the cursor
viz.mouse.setCursor(0)
controllers = [None, None]
controllerAmt = 1


# main class for keyboard & mouse
class Main:
    def __init__(self):
        # add test object for reference
        # self.testAvatar = viz.addAvatar('vcc_male2.cfg').setPosition([0, 0, 5])
        self.camCords = viz.MainView.getPosition()
        self.camAngle = viz.MainView.getEuler()
        self.camVelocity = [0, 0, 0]

        # add the hand object
        self.radius = handRadius
        self.hand = [Point()]
        self.hand.append(self.hand[0])
        # how far hand is from camera initially
        self.handDepth = 1
        self.handAngle = [[0, 0, 0]]

        # camera speed (local)
        self.camSpeed = minCamSpeed

        self.anim = [myGUI.CircleAnim(self.hand[0], 4, self.hand[0].radius, 0.01, [100, 10, 1], True, 10)]

    def main(self):
        # call updateView when mouse is moved
        viz.callback(viz.MOUSE_MOVE_EVENT, self.updateView)

        # update hand position with new facing angle
        self.updateHandPos()

        # call moveCam when keyboard is pressed
        if viz.key.anyDown(['w', 'a', 's', 'd', ' ', viz.KEY_SHIFT_L, 'q']):
            self.camCords = viz.MainView.getPosition()
            # move camera based on button pressed
            self.moveCam()

        viz.MainView.setPosition(self.camCords)
        viz.MainView.setEuler(self.camAngle)
        self.hand[0].sphere.setPosition(self.hand[0].cords)
        self.hand[0].sphere.setEuler(self.handAngle[0])
        self.anim[0].draw()

    def updateView(self, cords):
        # camAngle = [pitch, yaw, tilt]
        self.camAngle = viz.MainView.getEuler()
        # update facing angle based on CHANGE in mouse position
        self.camAngle = [self.camAngle[0] + (cords.dx * sensitivity), self.camAngle[1] - (cords.dy * sensitivity), 0]  # self.camAngle[2]]

    # tilt is always 0 to prevent camera from going upside down

    def updateHandPos(self):
        vizact.onwheelup(self.addHand)
        vizact.onwheeldown(self.subHand)
        self.hand[0].cords[0] = self.camCords[0] + self.handDepth * math.sin(math.radians(self.camAngle[0])) * math.cos(math.radians(self.camAngle[1]))
        self.hand[0].cords[1] = self.camCords[1] - self.handDepth * math.sin(math.radians(self.camAngle[1]))
        self.hand[0].cords[2] = self.camCords[2] + self.handDepth * math.cos(math.radians(self.camAngle[0])) * math.cos(math.radians(self.camAngle[1]))

    def subHand(self):
        self.handDepth -= scrollSpeed

    def addHand(self):
        self.handDepth += scrollSpeed

    def getCamVelocity(self, forwardBackward, leftRight, sinCos):
        # y velocity is independent of x and z velocity
        if sinCos == 'sin':
            return [self.camSpeed * forwardBackward * math.sin(math.radians(self.camAngle[0]) + 45 * leftRight * forwardBackward), self.camVelocity[1],
                    self.camSpeed * forwardBackward * math.cos(math.radians(self.camAngle[0]) + 45 * leftRight * forwardBackward)]
        elif sinCos == 'cos':
            return [self.camSpeed * forwardBackward * math.cos(-math.radians(self.camAngle[0])), self.camVelocity[1], self.camSpeed * leftRight * math.sin(-math.radians(self.camAngle[0]))]

    def moveCam(self):
        # forward & backward
        if viz.key.isDown('w'):
            f = 1
        else:
            f = 0
        if viz.key.isDown('s'):
            b = -1
        else:
            b = 0

        # left & right
        if viz.key.isDown('a'):
            l = -1
        else:
            l = 0
        if viz.key.isDown('d'):
            r = 1
        else:
            r = 0

        # up & down
        if viz.key.isDown(' '):
            u = 1
        else:
            u = 0
        if viz.key.isDown(viz.KEY_SHIFT_L):
            d = -1
        else:
            d = 0

        # speed up
        if viz.key.isDown('q'):
            self.camSpeed = maxCamSpeed
        else:
            self.camSpeed = minCamSpeed

        # change movement based on facing angle
        if viz.key.isDown('w'):
            self.camVelocity = self.getCamVelocity(f + b, l + r, 'sin')
            if viz.key.isDown('s'):
                self.camVelocity = self.getCamVelocity(l + r, f + b, 'cos')
        elif viz.key.isDown('s'):
            self.camVelocity = self.getCamVelocity(f + b, l + r,
                                                   'sin')
        elif viz.key.isDown('a') or viz.key.isDown('d'):
            self.camVelocity = self.getCamVelocity(l + r, l + r, 'cos')
        else:
            self.camVelocity = [0, self.camVelocity[1], 0]
        # x and z velocities must be 0 when there is no lateral camera movement or else verical movement will be affected
        self.camVelocity[1] = self.camSpeed * (u + d)

        # add camera speed to camera cords
        self.camCords = [self.camCords[0] + self.camVelocity[0], self.camCords[1] + self.camVelocity[1], self.camCords[2] + self.camVelocity[2]]


class Point:
    def __init__(self):
        self.radius = 0.1
        self.sphere = vizshape.addSphere(self.radius)
        self.cords = [0, 0, 0]
