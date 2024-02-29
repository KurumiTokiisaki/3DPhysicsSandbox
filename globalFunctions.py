import math
from config import *
import viz

jointMadness = 0  # yes


# sin and cos functions used here due to floating point error in math.pi
def sin(angle):
    returnAngle = math.sin(angle)
    return round(returnAngle, 13)


def cos(angle):
    returnAngle = math.cos(angle)
    return round(returnAngle, 13)


# get the scalar distance between 2 coordinates
def distance(cordOne, cordTwo):
    diff = [0, 0, 0]
    for d in range(3):
        diff[d] = cordOne[d] - cordTwo[d]
    return math.sqrt(diff[0] ** 2 + diff[1] ** 2 + diff[2] ** 2)


# get the distance between 2 points given differences in x, y, and z values
def diffDistance(diffX, diffY, diffZ):
    return math.sqrt(diffX ** 2 + diffY ** 2 + diffZ ** 2)


# get the relative displacement between 2 points
def displacement(cordOne, cordTwo):
    return [cordOne[0] - cordTwo[0], cordOne[1] - cordTwo[1], cordOne[2] - cordTwo[2]]


# detects collisions between 2 points with radius attributes (basically spheres)
def detectCollision(rOne, rTwo, cOne, cTwo):
    sumR = rOne + rTwo
    return distance(cOne, cTwo) <= sumR


# returns the midpoint of two points
def midpoint(pOne, pTwo):
    mid = [0, 0, 0]
    for m in range(3):
        mid[m] = (pOne.cords[m] + pTwo.cords[m]) / 2
    return [mid[0], mid[1], mid[2]]


# returns the angle [pitch, yaw, roll] between 2 points. this is a special case for the Vizard setEuler function some reason unbeknownst to me! (trust)
def getEulerAngle(cordOne, cordTwo):
    diff = [0, 0, 0]
    for d in range(3):
        diff[d] = cordOne[d] - cordTwo[d]

    if diff[2] != 0:
        pitch = math.degrees(math.atan(diff[0] / diff[2]))  # angle from x to z
        if diff[0] != 0:
            yaw = 90 - math.degrees(math.atan(diff[1] / math.sqrt(diff[0] ** 2 + diff[2] ** 2)))  # angle from y to z
        else:
            yaw = 0
    else:
        pitch = 90
        yaw = 0
    if diff[2] <= 0:
        yaw = -yaw  # angle from y to z (reversed since this negates after negative difference along z since trig is funny)
    roll = jointMadness

    return [pitch, yaw, roll]


def getThreeDAngle(cordOne, cordTwo, xyz):
    diff = [0, 0, 0]
    for d in range(3):
        diff[d] = cordOne[d] - cordTwo[d]

    # change order of angular calcs when calculating angles relative to x, y, or z
    # by default, it will be x
    if (not xyz) or (xyz == 'x'):
        diffIdx = [2, 1, 0]
    elif xyz == 'y':
        diffIdx = [0, 2, 1]
    elif xyz == 'z':
        diffIdx = [0, 1, 2]

    if diff[diffIdx[1]] != 0:
        pitch = math.atan(diff[diffIdx[0]] / diff[diffIdx[1]])  # relative angle from x to z
    else:
        pitch = math.pi / 2
    if (diff[diffIdx[0]] != 0) or (diff[diffIdx[1]] != 0):
        yaw = math.atan(diff[diffIdx[2]] / math.sqrt(diff[diffIdx[1]] ** 2 + diff[diffIdx[0]] ** 2))  # relative angle from y to x/z
    else:
        yaw = math.pi / 2

    return [pitch, yaw, 0]


def getAbsThreeDAngle(cordOne, cordTwo, xyz):
    diff = [0, 0, 0]
    for d in range(3):
        diff[d] = abs(cordOne[d] - cordTwo[d])

    # change order of angular calcs when calculating angles relative to x, y, or z
    # by default, it will be x
    if (not xyz) or (xyz == 'x'):
        diffIdx = [2, 1, 0]
    elif xyz == 'y':
        diffIdx = [0, 2, 1]
    elif xyz == 'z':
        diffIdx = [0, 1, 2]

    if diff[diffIdx[1]] != 0:
        pitch = math.atan(diff[diffIdx[0]] / diff[diffIdx[1]])  # relative angle from x to z
    else:
        pitch = math.pi / 2
    if (diff[diffIdx[0]] != 0) or (diff[diffIdx[1]] != 0):
        yaw = math.atan(diff[diffIdx[2]] / math.sqrt(diff[diffIdx[1]] ** 2 + diff[diffIdx[0]] ** 2))  # relative angle from y to x/z
    else:
        yaw = math.pi / 2

    return [pitch, yaw, 0]


# get the angle between cordOne and cordTwo in a 2D plane
def getTwoDAngle(cordOne, cordTwo):
    diff = [0, 0]
    for d in range(2):
        diff[d] = cordOne[d] - cordTwo[d]
    return math.atan(diff[0] / diff[1])


def getAbsTwoDAngle(cordOne, cordTwo):
    diff = [0, 0]
    for d in range(2):
        diff[d] = abs(cordOne[d] - cordTwo[d])
    if diff[1] == 0:
        return math.pi / 2
    return math.atan(diff[0] / diff[1])


# gets the sign of a value (+/-)
def getSign(value):
    return 1 if value >= 0 else -1


# resolves spheres (points) bouncing on the edges of collision cuboids (collision rects)
# the returned value to set the new cords to depends on the angle and colliding plane of the particle
# check out the maths here: https://drive.google.com/file/d/1ES6T8RilTcE5Pu7Zhdxfo6R6hvvsViAT/view?usp=drive_link
def edgeBounce(resultV, angle, e, angleState):
    if angleState == 0:
        if (abs(math.degrees(angle[0])) % 90) > 45:
            return resultV * sin(angle[1] * 2) * sin(angle[0]) * e, resultV * cos(angle[1] * 2) * e, resultV * sin(angle[1] * 2) * cos(
                angle[0]) * e  # here's why I multiply the angle by 2: https://drive.google.com/file/d/1BeUFv6UuvRvqFxwgApfSc328uGC2fKmZ/view?usp=drive_link
        else:
            return resultV * sin(angle[1] * 2) * sin(angle[0]) * e, resultV * cos(angle[1] * 2), resultV * sin(angle[1] * 2) * cos(angle[0]) * e
    else:
        if (abs(math.degrees(angle[0])) % 90) < 45:
            return resultV * sin(angle[1] * 2) * sin(angle[0]) * e, resultV * cos(angle[1] * 2) * e, resultV * sin(angle[1] * 2) * cos(
                angle[0]) * e  # here's why I multiply the angle by 2: https://drive.google.com/file/d/1BeUFv6UuvRvqFxwgApfSc328uGC2fKmZ/view?usp=drive_link
        else:
            return resultV * sin(angle[1] * 2) * sin(angle[0]) * e, resultV * cos(angle[1] * 2), resultV * sin(angle[1] * 2) * cos(angle[0]) * e


# resolves spheres (points) bouncing on the corners of collision cuboids (collision rects)
# the returned value to set the new cords to depends on the angle of the particle
# check out the maths here: https://drive.google.com/file/d/1ES6T8RilTcE5Pu7Zhdxfo6R6hvvsViAT/view?usp=drive_link
def vertexBounce(resultV, angle, e):
    if (abs(math.degrees(angle[1])) % 90) > 45:
        return resultV * sin(angle[1] * 2) * sin(angle[0]) * e, resultV * cos(angle[1] * 2) * e, resultV * sin(angle[1] * 2) * cos(angle[0]) * e
    else:
        return resultV * sin(angle[1] * 2) * sin(angle[0]) * e, resultV * cos(angle[1] * 2), resultV * sin(angle[1] * 2) * cos(angle[0]) * e


def capVolume(h, r):  # submerged height and sphere radius as parameters
    return (math.pi * (h ** 2) / 3) * ((3 * r) - h)  # https://drive.google.com/file/d/1mfi4ajJRJr676QW_TxjNS7zyM0jippvX/view?usp=drive_link


def capArea(h, r):  # submerged height and sphere radius as parameters
    return 2 * math.pi * r * h  # differential of cap volume


# returns the dot product between 2 cords (operator can vary)
def dotP(pOne, pTwo, op):
    if op == '+':
        return [pOne[0] + pTwo[0], pOne[1] + pTwo[1], pOne[2] + pTwo[2]]
    elif op == '-':
        return [pOne[0] - pTwo[0], pOne[1] - pTwo[1], pOne[2] - pTwo[2]]
    elif op == '*':
        return [pOne[0] * pTwo[0], pOne[1] * pTwo[1], pOne[2] * pTwo[2]]
    elif op == '/':
        return [pOne[0] / pTwo[0], pOne[1] / pTwo[1], pOne[2] / pTwo[2]]


# returns the 3D cords between 2 cords given a singular cord missing the two other cords (e.g. solve for cord C on the line AB, given C's x-value)
def dotPLine(a, b, c, ty):
    ab = dotP(b, a, '-')
    m = (c - a[ty]) / ab[ty]
    r = dotP(a, dotP(ab, [m, m, m], '*'), '+')  # resultant cord value
    return r


# converts True/False to +/-
def TFNum(boolean):
    return 1 if boolean else -1


# gets the angle (in degrees) and displacement of an object around a bounding sphere (give a radius as disp) from said object to another object (currently only used for text and the camera)
def camAnglePos(camCords, pCords, disp):
    angleDisp = getThreeDAngle(pCords, camCords, 'y')
    angle = getEulerAngle(camCords, pCords)
    multiplier = 1
    if camCords[2] > pCords[2]:
        angle[0] -= 180
        angle[1] -= 180
        multiplier = -1
    facingAngle = [angle[0], (angle[1] + 90) * multiplier, 0]
    if disp != 0:
        pos = pCords[0] - (multiplier * disp * cos(angleDisp[1]) * sin(angleDisp[0])), pCords[1] - (disp * sin(angleDisp[1])), pCords[2] - (multiplier * disp * cos(angleDisp[1]) * cos(angleDisp[0]))
    else:
        pos = pCords
    return facingAngle, pos


def buttonPressed(button, *args):  # gets the button currently being pressed
    if mode == 'k':
        if button == 'select':
            return viz.mouse.getState() == controls[button]
        else:
            return viz.key.isDown(controls[button])
    elif mode == 'vr':
        return (args[0].getButtonState() % touchpad) == controls[button][args[1]]  # this value is modulo in case the sensitive controllers detect that the touchpad is being tapped


def checkInList(arr, value):
    return value in arr


# convert a list to a string
def listToStr(listIn):
    tempStr = ''
    for l in listIn:
        tempStr = f'{tempStr}{l}'
    return tempStr


# convert a string to a list
def strToList(strIn):
    tempList = []
    for c in strIn:
        tempList.append(c)
    return tempList


# get the maximum length of a list in a multidimensional list
def getMaxLen(listIn):
    maxLen = 0
    for l in listIn:
        if len(l) > maxLen:
            maxLen = len(l)
    return maxLen


# remove a character from a string at a specified index
def removeFromStr(string, popIdx):
    strArray = []
    for c in string:
        strArray.append(c)
    strArray.pop(popIdx)
    modifiedStr = ''
    for i in strArray:
        modifiedStr = f'{modifiedStr}{i}'
    return modifiedStr


# runs the code, given a GUI object, to remove it from the Vizard game scene. this will ALWAYS run when a new copy of a GUI is created, so that it can be "re-summoned" at a new position.
def removeGUI(GUIObj):
    GUIObj.drawn = False
    GUIObj.unDraw()
