import math

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
def detectCollision(pOne, pTwo):
    sumR = pOne.radius + pTwo.radius
    return distance(pOne.cords, pTwo.cords) <= sumR


# returns the midpoint of two points
def midpoint(pOne, pTwo):
    mid = [0, 0, 0]
    for m in range(3):
        mid[m] = (pOne.cords[m] + pTwo.cords[m]) / 2
    return [mid[0], mid[1], mid[2]]


# returns the angle [pitch, yaw, roll] between 2 points. this is a special case for the Vizard setEuler function some reason unbeknownst to me!
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
        yaw = -yaw  # angle from y to z (reversed since this negates after negative difference along z for some reason)
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
    if (diff[diffIdx[0]] != 0) and (diff[diffIdx[1]] != 0):
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
    return (math.pi * (h ** 2) / 3) * ((3 * r) - h)


def capArea(h, r):  # submerged height and sphere radius as parameters
    return 2 * math.pi * r * h
