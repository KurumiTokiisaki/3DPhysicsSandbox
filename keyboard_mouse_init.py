# base Vizard libraries
import viz
import vizshape
import vizact
# used for trig functions
import myGUI
from config import *

# disable built-in mouse commands
viz.mouse.setOverride()

# mouse sensitivity
sensitivity = 25 / renderRate  # use maximum dpi and lowest sensitivity for most accurate results

# camera speed
minCamSpeed = 10 / renderRate
maxCamSpeed = minCamSpeed * 2

# scroll speed (for hand)
scrollSpeed = 0.01 / renderRate
# hide the cursor
viz.mouse.setCursor(0)
controllers = [None, None]  # all values here for keyboard/mouse will always be None
controllerAmt = 1  # set this to 1 since there's only 1 controller, which is the mouse!


# main class for keyboard & mouse
class Main:
    def __init__(self) -> None:
        self.camCords = viz.MainView.getPosition()
        self.camAngle = viz.MainView.getEuler()  # [pitch, yaw, tilt]
        self.camVelocity = [0, 0, 0]

        # add the hand object
        self.hand = [Point()]  # draw the hand object
        self.hand.append(self.hand[0])  # make an identical copy of the first hand to compensate for the fact that VR has 2 controllers
        # how far hand is from camera initially
        self.handDepth = 1
        self.handAngle = [[0, 0, 0]]

        self.camSpeed = minCamSpeed  # current camera speed; can change to speed up or slow down

        self.anim = [myGUI.CircleAnim(self.hand[0], 5, self.hand[0].radius, 0.01, [100, 10, 1], True, 10)]  # add an animation around the hand

    def main(self) -> None:
        # call updateView when mouse is moved, so that the facing camera angle can be updated
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

    def updateView(self, cords: list) -> None:
        """
        :param cords: an object with attributes 'dy' (change in y mouse pos) and 'dx' (change in x mouse pos).
        """
        self.camAngle = viz.MainView.getEuler()
        self.camAngle = [self.camAngle[0] + (cords.dx * sensitivity), self.camAngle[1] - (cords.dy * sensitivity), 0]  # update the facing angle based on CHANGE in mouse position

    def updateHandPos(self) -> None:
        vizact.onwheelup(self.addHand)  # make the hand go further away if scrolling up
        vizact.onwheeldown(self.subHand)  # make the hand come closer if scrolling down
        # check fig. 1 see the spherical coordinate geometry maths for updating the hand's position in the code below
        self.hand[0].cords[0] = self.camCords[0] + self.handDepth * math.sin(math.radians(self.camAngle[0])) * math.cos(math.radians(self.camAngle[1]))
        self.hand[0].cords[1] = self.camCords[1] - self.handDepth * math.sin(math.radians(self.camAngle[1]))
        self.hand[0].cords[2] = self.camCords[2] + self.handDepth * math.cos(math.radians(self.camAngle[0])) * math.cos(math.radians(self.camAngle[1]))

    def subHand(self) -> None:
        self.handDepth -= scrollSpeed

    def addHand(self) -> None:
        self.handDepth += scrollSpeed

    def getCamVelocity(self, forwardBackward: int, leftRight: int, sinCos: str) -> list:
        """
        :param forwardBackward/leftRight: forwardBackward and leftRight can be positive/negative. when positive, move forwards and right, respectively. when negative, move backwards and left, respectively.
        :param sinCos: used to handle exceptions in which there is left/right movement AND forward/back movement (sin), or left/right movement and NO forward/back movement (cos).

        left/right movement is taken into account by reversing the trig functions and making their angle coefficients negative, since left/right is perpendicular to forward/back.
        velocity about the X/Z-axis is multiplied by sqrt(2) when moving diagonally to maintain a constant speed about the X and Z axes.
        45 is used in 'sin' since 45 degrees is diagonal to 0 degrees, allowing for accurate diagonal movements while maintaining a constant speed about X and Z.
            diagonal movement happens when W/S AND A/D are pressed.
        Y-velocity is independent of x and z velocity, so Y-velocity always returns itself.
        check out this link for the mathematical proof: https://drive.google.com/file/d/1y_UX1Otwlxe1toA1COCcLJ8Q-jlt4qe9/view?usp=sharing
        """
        if sinCos == 'sin':
            return [self.camSpeed * forwardBackward * math.sin(math.radians(self.camAngle[0]) + 45 * leftRight * forwardBackward), self.camVelocity[1],
                    self.camSpeed * forwardBackward * math.cos(math.radians(self.camAngle[0]) + 45 * leftRight * forwardBackward)]
        elif sinCos == 'cos':
            return [self.camSpeed * forwardBackward * math.cos(-math.radians(self.camAngle[0])), self.camVelocity[1], self.camSpeed * leftRight * math.sin(-math.radians(self.camAngle[0]))]

    def moveCam(self) -> None:
        """
        forward & backward, left & right, and up & down movements are summed, cancelling each other out when both are pressed at the same time to result in no movement
        """
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
        if viz.key.isDown('w') or viz.key.isDown('s'):
            self.camVelocity = self.getCamVelocity(f + b, l + r, 'sin')
        elif viz.key.isDown('a') or viz.key.isDown('d'):
            self.camVelocity = self.getCamVelocity(l + r, l + r, 'cos')
        else:  # if the space bar or left-shift is being pressed
            self.camVelocity = [0, self.camVelocity[1], 0]  # x and z velocities must be 0 when there is no lateral camera speed or else vertical camera velocity will be affected
        self.camVelocity[1] = self.camSpeed * (u + d)

        # add camera speed to camera cords
        self.camCords = [self.camCords[0] + self.camVelocity[0], self.camCords[1] + self.camVelocity[1], self.camCords[2] + self.camVelocity[2]]


class Point:
    def __init__(self) -> None:
        self.radius = handRadius
        self.sphere = vizshape.addSphere(self.radius)
        self.cords = [0, 0, 0]
