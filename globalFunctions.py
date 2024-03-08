import math

from config import *
import viz

jointMadness = 0  # breaks the visuals of joints if not 0


# round off the value of sin(angle) for approximation, lowering the percentage uncertainty in floating point error
def sin(angle: float) -> float:
    return round(math.sin(angle), 13)


# round off the value of cos(angle) for approximation, lowering the percentage uncertainty in floating point error
def cos(angle: float) -> float:
    return round(math.cos(angle), 13)


# get the scalar distance between 2 coordinates
def distance(cordOne: list, cordTwo: list) -> float:
    diff = [0, 0, 0]
    for d in range(3):
        diff[d] = cordOne[d] - cordTwo[d]
    return math.sqrt(diff[0] ** 2 + diff[1] ** 2 + diff[2] ** 2)


# get the distance between 2 positions given the difference in their x, y, and z values
def diffDistance(diffX: float, diffY: float, diffZ: float) -> float:
    return math.sqrt(diffX ** 2 + diffY ** 2 + diffZ ** 2)


# get the relative displacement between 2 points about each axis
def displacement(cordOne: list, cordTwo: list) -> list:
    return [cordOne[0] - cordTwo[0], cordOne[1] - cordTwo[1], cordOne[2] - cordTwo[2]]


# detects collisions between 2 points (sphere<>sphere collision detection) given their radii and positions using spherical coordinate geometry
def detectPointCollision(radOne: float, radTwo: float, cordOne: list, cordTwo: list) -> bool:
    sumR = radOne + radTwo
    return distance(cordOne, cordTwo) <= sumR


# returns the midpoint of two points
def midpoint(pOne: object, pTwo: object) -> list:
    mid = [0, 0, 0]
    for m in range(3):
        mid[m] = (pOne.cords[m] + pTwo.cords[m]) / 2
    return [mid[0], mid[1], mid[2]]


# returns the direction and magnitude of pitch and yaw angles between 2 positions using spherical coordinate geometry
def getThreeDAngle(cordOne: list, cordTwo: list, xyz: str) -> list:
    diff = [0, 0, 0]
    for d in range(3):
        diff[d] = cordOne[d] - cordTwo[d]

    # change order of angular calcs when calculating angles relative to x, y, or z
    if xyz == 'x':
        diffIdx = [2, 1, 0]
    elif xyz == 'y':
        diffIdx = [0, 2, 1]
    elif xyz == 'z':
        diffIdx = [0, 1, 2]

    if diff[diffIdx[1]] != 0:  # prevents ZeroDivisionError
        pitch = math.atan(diff[diffIdx[0]] / diff[diffIdx[1]])  # relative angle from x to z
    else:
        pitch = math.pi / 2
    if (diff[diffIdx[0]] != 0) or (diff[diffIdx[1]] != 0):  # prevents ZeroDivisionError
        yaw = math.atan(diff[diffIdx[2]] / math.sqrt(diff[diffIdx[1]] ** 2 + diff[diffIdx[0]] ** 2))  # relative angle from y to x/z
    else:
        yaw = math.pi / 2

    return [pitch, yaw, 0]


# return only the magnitude of pitch and yaw angles (in radians) between 2 positions using spherical coordinate geometry
def getAbsThreeDAngle(cordOne: list, cordTwo: list, xyz: str) -> list:
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

    if diff[diffIdx[1]] != 0:  # prevents ZeroDivisionError
        pitch = math.atan(diff[diffIdx[0]] / diff[diffIdx[1]])  # relative angle from x to z
    else:
        pitch = math.pi / 2
    if (diff[diffIdx[0]] != 0) or (diff[diffIdx[1]] != 0):  # prevents ZeroDivisionError
        yaw = math.atan(diff[diffIdx[2]] / math.sqrt(diff[diffIdx[1]] ** 2 + diff[diffIdx[0]] ** 2))  # relative angle from y to x/z
    else:
        yaw = math.pi / 2

    return [pitch, yaw, 0]


# returns the angle [pitch, yaw, roll] (in radians) between 2 points. this is a special case for the Vizard setEuler function.
def getEulerAngle(cordOne: list, cordTwo: list) -> list:
    diff = [0, 0, 0]
    for d in range(3):
        diff[d] = cordOne[d] - cordTwo[d]

    if diff[2] != 0:  # prevents ZeroDivisionError
        pitch = math.degrees(math.atan(diff[0] / diff[2]))  # angle from x to z
    else:
        pitch = 90
    if diff[0] != 0:  # prevents ZeroDivisionError
        yaw = 90 - math.degrees(math.atan(diff[1] / math.sqrt(diff[0] ** 2 + diff[2] ** 2)))  # angle from y to x/z
    else:
        yaw = 90
    if diff[2] <= 0:
        yaw = -yaw  # reversed when there's negative difference along the z-axis
    roll = jointMadness

    return [pitch, yaw, roll]


# get the direction and magnitude of angle between the x and y positions of 2 positions
def getTwoDAngle(cordOne: list, cordTwo: list) -> float:
    diff = [0, 0]
    for d in range(2):
        diff[d] = cordOne[d] - cordTwo[d]
    return math.atan(diff[0] / diff[1])  # angle from x to y


# get only the magnitude of angle between the x and y positions of 2 positions
def getAbsTwoDAngle(cordOne: list, cordTwo: list) -> float:
    diff = [0, 0]
    for d in range(2):
        diff[d] = abs(cordOne[d] - cordTwo[d])
    if diff[1] == 0:  # prevents ZeroDivisionError
        return math.pi / 2
    return math.atan(diff[0] / diff[1])  # angle from x to y


# gets the sign of a value (+/-)
def getSign(value: (float or int)) -> int:
    return 1 if value >= 0 else -1


# resolves spheres (points) bouncing on the edges of collision cuboids (collision rects)
# the returned value to set the new cords to depends on the colliding angle and colliding plane of the point
# check out the maths here: https://drive.google.com/file/d/1ES6T8RilTcE5Pu7Zhdxfo6R6hvvsViAT/view?usp=drive_link
def edgeBounce(resultV: float, angle: list, e: float, angleState: int) -> tuple:
    if angleState == 0:
        if (abs(math.degrees(angle[0])) % 90) > 45:
            return resultV * sin(angle[1] * 2) * sin(angle[0]) * e, resultV * cos(angle[1] * 2) * e, resultV * sin(angle[1] * 2) * cos(angle[0]) * e  # here's why I multiply the angle by 2: https://drive.google.com/file/d/1BeUFv6UuvRvqFxwgApfSc328uGC2fKmZ/view?usp=drive_link
        else:
            return resultV * sin(angle[1] * 2) * sin(angle[0]) * e, resultV * cos(angle[1] * 2), resultV * sin(angle[1] * 2) * cos(angle[0]) * e
    else:
        if (abs(math.degrees(angle[0])) % 90) < 45:
            return resultV * sin(angle[1] * 2) * sin(angle[0]) * e, resultV * cos(angle[1] * 2) * e, resultV * sin(angle[1] * 2) * cos(angle[0]) * e  # here's why I multiply the angle by 2: https://drive.google.com/file/d/1BeUFv6UuvRvqFxwgApfSc328uGC2fKmZ/view?usp=drive_link
        else:
            return resultV * sin(angle[1] * 2) * sin(angle[0]) * e, resultV * cos(angle[1] * 2), resultV * sin(angle[1] * 2) * cos(angle[0]) * e


# resolves spheres (points) bouncing on the corners of collision cuboids (collision rects)
# the returned value to set the new cords to depends on the colliding angle of the point
# check out the maths here: https://drive.google.com/file/d/1ES6T8RilTcE5Pu7Zhdxfo6R6hvvsViAT/view?usp=drive_link
def vertexBounce(resultV: float, angle: list, e: float) -> tuple:
    if (abs(math.degrees(angle[1])) % 90) > 45:
        return resultV * sin(angle[1] * 2) * sin(angle[0]) * e, resultV * cos(angle[1] * 2) * e, resultV * sin(angle[1] * 2) * cos(angle[0]) * e
    else:
        return resultV * sin(angle[1] * 2) * sin(angle[0]) * e, resultV * cos(angle[1] * 2), resultV * sin(angle[1] * 2) * cos(angle[0]) * e


def capVolume(h: float, r: float) -> float:  # submerged height and sphere radius as parameters
    return (math.pi * (h ** 2) / 3) * ((3 * r) - h)  # https://drive.google.com/file/d/1mfi4ajJRJr676QW_TxjNS7zyM0jippvX/view?usp=drive_link


def capArea(h: float, r: float) -> float:  # submerged height and sphere radius as parameters
    return 2 * math.pi * r * h  # half the differential of cap volume with respect to r


# returns the dot product between 2 cords (operator can vary) (currently unused)
def dotP(pOne: list, pTwo: list, op: str) -> list:
    if op == '+':
        return [pOne[0] + pTwo[0], pOne[1] + pTwo[1], pOne[2] + pTwo[2]]
    elif op == '-':
        return [pOne[0] - pTwo[0], pOne[1] - pTwo[1], pOne[2] - pTwo[2]]
    elif op == '*':
        return [pOne[0] * pTwo[0], pOne[1] * pTwo[1], pOne[2] * pTwo[2]]
    elif op == '/':
        return [pOne[0] / pTwo[0], pOne[1] / pTwo[1], pOne[2] / pTwo[2]]


# returns the 3D cords between 2 cords given a singular cord missing the two other cords (e.g. solve for cord C on the line AB, given C's x-position) (currently unused)
def dotPLine(a: list, b: list, c: float, ty: int):
    ab = dotP(b, a, '-')
    m = (c - a[ty]) / ab[ty]
    r = dotP(a, dotP(ab, [m, m, m], '*'), '+')  # resultant cord value
    return r


# converts True/False to +/-
def TFNum(boolean: bool) -> int:
    return 1 if boolean else -1


# gets the angle (in degrees) and displacement of an object around a bounding sphere (give a radius as disp) from said object to another object (currently only used to make text face towards the camera in some GUIs)
def camAnglePos(camCords: list, pCords: list, disp: float) -> (list, list):
    angleDisp = getThreeDAngle(pCords, camCords, 'y')
    angle = getEulerAngle(camCords, pCords)
    multiplier = 1
    if camCords[2] > pCords[2]:
        angle[0] -= 180
        angle[1] -= 180
        multiplier = -1
    facingAngle = [angle[0], (angle[1] + 90) * multiplier, 0]
    if disp != 0:  # only calculate displacement around a sphere when its radius is given
        pos = pCords[0] - (multiplier * disp * cos(angleDisp[1]) * sin(angleDisp[0])), pCords[1] - (disp * sin(angleDisp[1])), pCords[2] - (multiplier * disp * cos(angleDisp[1]) * cos(angleDisp[0]))
    else:
        pos = pCords
    return facingAngle, pos


# gets the button currently being pressed
def buttonPressed(button: str, *args: list) -> bool:
    """
    :param button: name of the button in question.
    :param args: only used if in VR. is a list containing both controller objects.
    :return: boolean value for if the button is being pressed.
    """
    if mode == 'k':
        if button == 'select':
            return viz.mouse.getState() == controls[button]
        else:
            return viz.key.isDown(controls[button])
    elif mode == 'vr':
        return (args[0].getButtonState() % touchpad) == controls[button][args[1]]  # there is a modulo here in case the sensitive controllers detect that the touchpad is being tapped


def checkInList(arr: list, value: any) -> bool:
    return value in arr


# convert a list to a string
def listToStr(listIn: list) -> str:
    tempStr = ''
    for l in listIn:
        tempStr = f'{tempStr}{l}'
    return tempStr


# convert a string to a list
def strToList(strIn: str) -> list:
    tempList = []
    for c in strIn:
        tempList.append(c)
    return tempList


# get the maximum length of a list within a multidimensional list
def getMaxLen(listIn: list) -> int:
    maxLen = 0
    for l in listIn:
        if len(l) > maxLen:
            maxLen = len(l)
    return maxLen


# remove a character from a string at a specified index
def removeFromStr(string: str, popIdx: int) -> str:
    strList = strToList(string)
    strList.pop(popIdx)
    modifiedStr = ''
    for i in strList:
        modifiedStr = f'{modifiedStr}{i}'
    return modifiedStr


# runs the code, given a GUI object, to remove it from the Vizard game scene. this will ALWAYS run when a new copy of a GUI is created, so that it can be removed and then "re-summoned" at a new position.
def removeGUI(GUIObj: object) -> None:
    GUIObj.drawn = False
    GUIObj.unDraw()
