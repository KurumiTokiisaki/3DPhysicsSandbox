# base Vizard libraries
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

# controller mode
mode = 'k'
fullscreen = True

# Vizard window initialization
viz.setMultiSample(4)  # FSAA (Full Screen Anti-Alaiasing)
viz.fov(90)
viz.go()

# controls for keyboard/VR
if mode == 'k':
    select = 1
    recall = 'r'
elif mode == 'vr':
    select = 4
    recall = 24
touchPad = 16

if mode == 'vr':
    import steamVR_init
    controls = steamVR_init.Main()
elif mode == 'k':
    import keyboard_mouse_init
    controls = keyboard_mouse_init.Main()
    if fullscreen:
        viz.window.setFullscreen()

refreshRate = 165  # display refresh rate
gConst = 9.81  # gravitational field constant
gasDensity = 1.293  # density of all gas
jointRadius = 0.01  # radius of joints
jointMadness = 0  # yes
theForce = False  # when True, "recalling" points causes them to float slowly to you
jointResolution = 2  # lower to increase performance
pointResolution = 10  # lower to increase performance


# get the scalar distance between 2 points with coordinate attributes
def distance(cordOne, cordTwo):
    diff = [0, 0, 0]
    for d in range(3):
        diff[d] = cordOne[d] - cordTwo[d]
    return math.sqrt(diff[0] ** 2 + diff[1] ** 2 + diff[2] ** 2)


# get the distance between 2 points given differences in x, y, and z values
def diffDistance(diffX, diffY, diffZ):
    return math.sqrt(diffX ** 2 + diffY ** 2 + diffZ ** 2)


# detects collisions between 2 points with radius attributes (basically spheres)
def detectCollision(pOne, pTwo):
    sumR = pOne.radius + pTwo.radius
    if distance(pOne.cords, pTwo.cords) <= sumR:
        return True


# returns the midpoint of two points
def midpoint(pOne, pTwo):
    mid = [0, 0, 0]
    for m in range(3):
        mid[m] = (pOne.cords[m] + pTwo.cords[m]) / 2
    return [mid[0], mid[1], mid[2]]


# returns the angle [pitch, yaw, roll] between 2 points
def getAngle(cordOne, cordTwo, dr):
    diff = [0, 0, 0]
    for d in range(3):
        diff[d] = cordOne[d] - cordTwo[d]

    if diff[2] != 0:
        pitch = math.atan(diff[0] / diff[2])  # angle from x to z
        if diff[0] != 0:
            yaw = (math.pi / 4) - math.atan(diff[1] / math.sqrt(diff[0] ** 2 + diff[2] ** 2))  # angle from y to z
        else:
            yaw = 0
    else:
        pitch = math.pi / 4
        yaw = 0
    if diff[2] <= 0:
        yaw = -yaw  # angle from y to z (reversed since this negates after negative difference along z for some reason)
    roll = jointMadness
    if dr == 'd':
        pitch = math.degrees(pitch)
        yaw = math.degrees(yaw)
        roll = math.degrees(roll)

    return [pitch, yaw, roll]


def getThreeDAngle(cordOne, cordTwo, xyz):
    diff = [0, 0, 0]
    for d in range(3):
        diff[d] = cordOne[d] - cordTwo[d]
    
    if xyz == 'x':
        if diff[2] != 0:
            pitch = math.atan(diff[2] / diff[1])  # relative angle from x to z
            if diff[0] != 0:
                yaw = math.atan(diff[0] / math.sqrt(diff[1] ** 2 + diff[2] ** 2))  # relative angle from y to x/z
            else:
                yaw = 0
        else:
            pitch = math.pi / 4
            yaw = 0
    elif xyz == 'y':
        if diff[2] != 0:
            pitch = math.atan(diff[0] / diff[2])  # relative angle from x to z
            if diff[0] != 0:
                yaw = math.atan(diff[1] / math.sqrt(diff[0] ** 2 + diff[2] ** 2))  # relative angle from y to x/z
            else:
                yaw = 0
        else:
            pitch = math.pi / 4
            yaw = 0
    elif xyz == 'z':
        if diff[2] != 0:
            pitch = math.atan(diff[0] / diff[1])  # relative angle from x to z
            if diff[0] != 0:
                yaw = math.atan(diff[2] / math.sqrt(diff[0] ** 2 + diff[1] ** 2))  # relative angle from y to x/z
            else:
                yaw = 0
        else:
            pitch = math.pi / 4
            yaw = 0

    return [pitch, yaw, 0]



# get the angle between cordOne and cordTwo in a 2D plane
def getTwoDAngle(cordOne, cordTwo):
    diff = [0, 0]
    for d in range(2):
        diff[d] = cordOne[d] - cordTwo[d]
    return math.atan(diff[0] / diff[1])


# gets the sign of a value (+/-)
def getSign(value):
    if value >= 0:
        return 1
    elif value < 0:
        return -1


# resolves spheres (points) bouncing on the edges of collision cuboids (collision rects)
# the returned value to set the new cords to depends on the angle and colliding plane of the particle
def edgeBounce(resultV, angle, e, angleState):
    if angleState == 0:
        if (abs(math.degrees(angle)) % 90) < 45:
            return resultV * math.sin(angle * 2) * e, resultV * math.cos(angle * 2) * e
        else:
            return resultV * math.sin(angle * 2) * e, resultV * math.cos(angle * 2)
    else:
        if (abs(math.degrees(angle)) % 90) > 45:
            return resultV * math.sin(angle * 2) * e, resultV * math.cos(angle * 2) * e
        else:
            return resultV * math.sin(angle * 2) * e, resultV * math.cos(angle * 2)


def vertexBounce(resultV, angle, aIdx, e, trig):
    if trig == 'cos':
        #if (abs(math.degrees(angle[aIdx[1]])) % 90) > 45:
        return resultV * math.cos(angle[aIdx[1]]) * math.sin(angle[aIdx[0]]) * e, resultV * math.sin(angle[aIdx[1]]) * e, resultV * math.cos(angle[aIdx[1]]) * math.cos(angle[aIdx[0]]) * e
        #else:
        #    return resultV * math.cos(angle[aIdx[1]]) * math.sin(angle[aIdx[0]]) * e, resultV * math.sin(angle[aIdx[1]]), resultV * math.cos(angle[aIdx[1]]) * math.cos(angle[aIdx[0]]) * e
    elif trig == 'sin':
        if (abs(math.degrees(angle[aIdx[1]])) % 90) > 45:
            return resultV * math.sin(angle[aIdx[1]] * 2) * math.sin(angle[aIdx[0]]) * e, resultV * math.cos(angle[aIdx[1]] * 2) * e, resultV * math.sin(angle[aIdx[1]] * 2) * math.cos(angle[aIdx[0]]) * e
        else:
            return resultV * math.sin(angle[aIdx[1]] * 2) * math.sin(angle[aIdx[0]]) * e, resultV * math.cos(angle[aIdx[1]] * 2), resultV * math.sin(angle[aIdx[1]] * 2) * math.cos(angle[aIdx[0]]) * e


# Main class for main.py
class Main:
    def __init__(self):
        vizshape.addGrid()
        self.gridFloor = 0  # y-coordinate of test collision
        self.points = []  # list of points for the whole program
        self.joints = []  # list of joints for the whole program
        self.collisionRect = []  # list of collision rectangles
        self.dragP = 'none'  # last clicked point index
        self.dragC = 'none'  # last clicked controller index for the last clicked point
        self.lastP = -1  # last clicked point that always retains its value for "recalling" objects to the controller
        self.theForceJoint = False  # True if the force is being used
        self.pause = False  # pauses physics
        self.pHeld = False  # sees if 'p' is held down

    def main(self):
        # pause if 'p' is pressed
        if ((mode == 'k' and viz.key.isDown('p')) or (mode == 'vr')) and (not self.pHeld):
            self.pause = not self.pause
            self.pHeld = True
        elif not viz.key.isDown('p'):
            self.pHeld = False

        controls.main()  # runs the main function in the current control (keyboard/VR) setting
        self.dragPoints()  # runs the function that detects if controller is "dragging" a point
        

        # detect & resolve collisions with collision boxes
        for p in range(len(self.points)):
            if (self.points[p].cords[1] - self.points[p].radius) <= self.gridFloor:
                self.points[p].cords[1] = self.points[p].oldCords[1]
                # self.points[p].oldCords[1] = self.points[p].cords[1] + self.points[p].velocity[1]
            # detect collisions with other points
            for po in range(len(self.points)):
                if detectCollision(self.points[p], self.points[po]) and (p != po):
                    self.sphereCollision(p, po)
            
            self.points[p].boxCollision()
            self.points[p].move()
        
        # update the visuals of joints and constrain points
        for j in range(len(self.joints)):
            self.joints[j].update()
            if not self.pause:
                self.joints[j].constrain()

    # used to drag points around using pointer/controller
    def dragPoints(self):
        for p in range(len(self.points)):
            for c in range(len(controls.hand)):
                if ((mode == 'k') and (viz.mouse.getState() == select)) or ((mode == 'vr') and (steamVR_init.controllers[c].getButtonState() == select)):  # detect if the select button is being pressed, depending on the controller mode
                    if (self.dragP == 'none') and (self.dragC == 'none'):  # used to set the drag variables if they are not already set
                        if detectCollision(self.points[p], controls.hand[c]):
                            self.dragP = p
                            self.lastP = p
                            self.dragC = c
                    else:
                        self.points[self.dragP].cords = copy.deepcopy(controls.hand[self.dragC].cords)  # set the point position to the controller (that grabbed that point)'s position
                # reset drag variables if select button is not pressed
                elif (self.dragC != 'none') and (((mode == 'vr') and (steamVR_init.controllers[self.dragC].getButtonState() != select)) or ((mode == 'k') and (viz.mouse.getState() != select))):
                    self.dragP = 'none'
                    self.dragC = 'none'
                # recalls the last clicked point to the controller's position
                if ((mode == 'vr') and (steamVR_init.controllers[c].getButtonState() == recall)) or ((mode == 'k') and viz.key.isDown(recall)):
                    # allows the force to be used (if True)
                    if theForce and (self.theForceJoint == False):
                        self.joints.append(Joint(False, 0, 0.05, None, self.lastP, True, c))
                        self.theForceJoint = True
                    # set cords of point to user pointer/hand
                    elif not theForce:
                        self.points[self.lastP].cords = copy.deepcopy(controls.hand[c].cords)
                # remove the force joint after recall is no longer active
                elif self.theForceJoint:
                    if self.joints[-1].show:
                        self.joints[-1].cylinder.remove()
                    self.joints.pop(-1)
                    self.theForceJoint = False
    
    def sphereCollision(self, pOne, pTwo):
        pass


# class for spheres
class Point:
    def __init__(self, radius, density):
        self.radius = radius
        self.sphere = vizshape.addSphere(radius, slices=pointResolution)  # vizard object for sphere
        self.cords = [0, 0, 0]
        self.oldCords = [0, 0, 0]  # coordinates from last frame
        self.velocity = [0, 0, 0]
        self.reboundVelocity = [0, 0, 0]
        self.force = [0, 0, 0]
        self.normalForce = [0, 0, 0]
        self.acc = [0, 0, 0]
        self.density = density
        self.volume = 4 / 3 * math.pi * self.radius ** 3
        self.mass = self.density * self.volume
        self.weight = self.mass * gConst
        self.gasDrag = [0, 0, 0]
        self.liquidDrag = [0, 0, 0]
        self.gasUpthrust = [0, 0, 0]
        self.liquidUpthrust = [0, 0, 0]
        self.friction = [0, 0, 0]
        self.constrainForce = [0, 0, 0]
        self.collision = ''
        self.lastCollision = ''
        self.vertexState = ''
        self.e = 1  # elasticity
        self.sf = 0  # surface friction

    def setRadiusDensity(self, radius, density):
        self.radius = radius
        self.volume = 4 / 3 * math.pi * self.radius ** 3
        self.mass = density * self.volume
        self.weight = self.mass * gConst
        self.sphere.remove()
        self.sphere = vizshape.addSphere(radius, slices=pointResolution)

    def move(self):
        # Verlet integration
        for c in range(3):
            self.velocity[c] = self.cords[c] - self.oldCords[c]  # set velocity to change in position
        
        if not game.pause:
            self.physics()
        
        self.oldCords = copy.deepcopy(self.cords)

        if not game.pause:
            for v in range(3):
                self.cords[v] += self.velocity[v]  # change coordinates based on velocity

        self.sphere.setPosition(self.cords)

    def physics(self):
        for axis in range(3):
            # add physics here

            self.force[axis] = self.gasDrag[axis] + self.liquidDrag[axis] + self.gasUpthrust[axis] + self.liquidUpthrust[axis] + self.friction[axis] + self.constrainForce[axis] + self.normalForce[axis]
            if axis == 0:
                self.force[axis] += self.weight
            self.acc[axis] = self.force[axis] / self.mass
            self.velocity[axis] += self.acc[axis] / (refreshRate ** 2)

    # detects and resolves collisions between spheres (points) and static cuboids (collision rects)
    def boxCollision(self):
        for b in game.collisionRect:
            self.vertexState = ''

            # fix repitition below, possibly using a for loop
            # self.lastcollision represents the surface of a collision cuboid that the point is currently above, factoring in its radius
            if ((self.cords[1] + self.radius) > b.plane['bottom']) and ((self.cords[1] - self.radius) < b.plane['top']):
                if ((self.cords[2] - self.radius) < b.plane['front']) and ((self.cords[2] + self.radius) > b.plane['back']):
                    if (self.cords[0] - self.radius) > b.plane['right']:
                        self.lastCollision = 'right'
                    elif (self.cords[0] + self.radius) < b.plane['left']:
                        self.lastCollision = 'left'
                elif ((self.cords[0] + self.radius) > b.plane['left']) and ((self.cords[0] - self.radius) < b.plane['right']):
                    if (self.cords[2] + self.radius) > b.plane['front']:
                        self.lastCollision = 'front'
                    elif (self.cords[2] - self.radius) < b.plane['back']:
                        self.lastCollision = 'back'
            elif ((self.cords[0] + self.radius) > b.plane['left']) and ((self.cords[0] - self.radius) < b.plane['right']) and ((self.cords[2] - self.radius) < b.plane['front']) and ((self.cords[2] + self.radius) > b.plane['back']):
                if (self.cords[1] + self.radius) > b.plane['top']:
                    self.lastCollision = 'top'
                elif (self.cords[1] - self.radius) < b.plane['bottom']:
                    self.lastCollision = 'bottom'
            
            # self.collision represents the surface of a collision cuboid that the point is currently above, using only its center point as reference
            if (self.cords[1] > b.plane['bottom']) and (self.cords[1] < b.plane['top']):
                if (self.cords[2] < b.plane['front']) and (self.cords[2] > b.plane['back']):
                    if self.cords[0] > b.plane['right']:
                        self.collision = 'right'
                    elif self.cords[0] < b.plane['left']:
                        self.collision = 'left'
                    else:
                        self.collision = ''
                elif (self.cords[0] > b.plane['left']) and (self.cords[0] < b.plane['right']):
                    if self.cords[2] > b.plane['front']:
                        self.collision = 'front'
                    elif self.cords[2] < b.plane['back']:
                        self.collision = 'back'
                    else:
                        self.collision = ''
                else:
                    self.collision = ''
            elif (self.cords[0] > b.plane['left']) and (self.cords[0] < b.plane['right']) and (self.cords[2] < b.plane['front']) and (self.cords[2] > b.plane['back']):
                if self.cords[1] > b.plane['top']:
                    self.collision = 'top'
                elif self.cords[1] < b.plane['bottom']:
                    self.collision = 'bottom'
                else:
                    self.collision = ''
            else:
                self.collision = ''

            
            if ((self.cords[0] > b.plane['right']) or (self.cords[0] < b.plane['left'])) and ((self.cords[2] < b.plane['front']) and (self.cords[2] > b.plane['back'])) and (
                    (self.cords[1] > b.plane['top']) or (self.cords[1] < b.plane['bottom'])):
                self.vertexState = 'z'
            elif ((self.cords[2] > b.plane['front']) or (self.cords[2] < b.plane['back'])) and ((self.cords[1] > b.plane['bottom']) and (self.cords[1] < b.plane['top'])) and (
                    (self.cords[0] > b.plane['right']) or (self.cords[0] < b.plane['left'])):
                self.vertexState = 'y'
            elif ((self.cords[0] < b.plane['right']) and (self.cords[0] > b.plane['left'])) and ((self.cords[2] > b.plane['front']) or (self.cords[2] < b.plane['back'])) and (
                    (self.cords[1] > b.plane['top']) or (self.cords[1] < b.plane['bottom'])):
                self.vertexState = 'x'

            # get the distance to the 2 nearest vertices
            vertexDist = []
            vertexIdx = [0, 0]
            relativeDist = [0, 0, 0]
            for v in b.vertex:
                vertexDist.append(distance(self.cords, v))
            minDist = [float('inf'), float('inf')]
            tempDist = copy.deepcopy(vertexDist)
            for ve in range(len(vertexDist)):
                if vertexDist[ve] < minDist[0]:
                    minDist[1] = minDist[0]
                    minDist[0] = vertexDist[ve]
                    vertexIdx[1] = vertexIdx[0]
                    vertexIdx[0] = ve
                elif vertexDist[ve] < minDist[1]:
                    minDist[1] = vertexDist[ve]
                    vertexIdx[1] = ve
            if (self.radius < minDist[0]) and (self.radius < minDist[1]):
                minDist[0] = math.sqrt(minDist[0] ** 2 - self.radius ** 2)
                minDist[1] = math.sqrt(minDist[1] ** 2 - self.radius ** 2)

                for a in range(3):
                    relativeDist[a] = minDist[0]

            # if this statement is not the first, points will clip through collision rects at their boundaries
            if (self.collision != '') and ((self.cords[0] + self.radius) >= b.plane['left']) and ((self.cords[0] - self.radius) <= b.plane['right']) and ((self.cords[1] + self.radius) >= b.plane['bottom']) and (
                    (self.cords[1] - self.radius) <= b.plane['top']) and ((self.cords[2] - self.radius) <= b.plane['front']) and ((self.cords[2] + self.radius) >= b.plane['back']):
                if (self.collision == 'left') or (self.collision == 'right'):
                    self.cords[0] = self.oldCords[0]# - self.velocity[0] * self.e
                elif (self.collision == 'top') or (self.collision == 'bottom'):
                    self.cords[1] = self.oldCords[1]# - self.velocity[1] * self.e
                elif (self.collision == 'front') or (self.collision == 'back'):
                    self.cords[2] = self.oldCords[2]# - self.velocity[2] * self.e

            # 
            elif (minDist[0] + minDist[1]) <= distance(b.vertex[vertexIdx[0]], b.vertex[vertexIdx[1]]):
                if (self.lastCollision == 'right') or (self.lastCollision == 'top') or (self.lastCollision == 'front'):
                    multiplier = 1
                else:
                    multiplier = -1
                
                if self.vertexState == 'x':
                    i = [2, 1]
                    # special case scenario for top and bottom
                    if self.lastCollision == 'top':
                        cIdx = 0
                    elif self.lastCollision == 'bottom':
                        cIdx = 1

                elif self.vertexState == 'y':
                    i = [2, 0]

                elif self.vertexState == 'z':
                    i = [1, 0]
                    # special case scenario for top and bottom
                    if self.lastCollision == 'top':
                        cIdx = 2
                    elif self.lastCollision == 'bottom':
                        cIdx = 3
                
                # general case scenario for right, left, front, and back
                if self.lastCollision == 'right':
                    cIdx = 0
                elif self.lastCollision == 'left':
                    cIdx = 1
                elif self.lastCollision == 'front':
                    cIdx = 2
                elif self.lastCollision == 'back':
                    cIdx = 3

                angle = getTwoDAngle([self.cords[i[1]], self.cords[i[0]]], [b.vertex[vertexIdx[0]][i[1]], b.vertex[vertexIdx[0]][i[0]]])
                resultV = math.sqrt(self.velocity[i[0]] ** 2 + self.velocity[i[1]] ** 2)
                resultF = math.sqrt(self.force[i[0]] ** 2 + self.force[i[1]] ** 2)
                if cIdx == 0:
                    iIdx = -1
                    pMultiplier = -1
                elif cIdx == 1:
                    iIdx = -1
                    pMultiplier = 1
                elif cIdx == 2:
                    iIdx = 0
                    pMultiplier = 1
                elif cIdx == 3:
                    iIdx = 0
                    pMultiplier = -1
                self.reboundVelocity[i[0]], self.reboundVelocity[i[1]] = edgeBounce(resultV, angle, self.e, iIdx)
                self.cords[i[iIdx - 1]] = self.cords[i[iIdx - 1]] + multiplier * self.reboundVelocity[i[0]]
                self.cords[i[iIdx]] = self.oldCords[i[iIdx]] + pMultiplier * self.reboundVelocity[i[1]]
                self.normalForce[i[iIdx - 1]] = resultF * math.cos(angle) * multiplier * getSign(angle)

                # print(self.lastCollision, self.vertexState, self.velocity, angle)

            elif distance(b.vertex[vertexIdx[0]], self.cords) <= self.radius:
                resultF = math.sqrt(self.force[0] ** 2 + self.force[1] ** 2 + self.force[2] ** 2)
                resultV = math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2 + self.velocity[2] ** 2)

                if (self.lastCollision == 'top') or (self.lastCollision == 'bottom'):
                    angle = getThreeDAngle(b.vertex[vertexIdx[0]], self.cords, 'y')
                    if (vertexIdx[0] == 0) or (vertexIdx[0] == 1) or (vertexIdx[0] == 6) or (vertexIdx[0] == 3):
                        pMultiplier = [-1, -1]
                        nMultiplier = [-1, -1]
                    elif (vertexIdx[0] == 4) or (vertexIdx[0] == 5) or (vertexIdx[0] == 2) or (vertexIdx[0] == 7):
                        pMultiplier = [1, 1]
                        nMultiplier = [1, 1]
                    if self.lastCollision == 'top':
                        yMultiplier = -1
                    elif self.lastCollision == 'bottom':
                        yMultiplier = 1
                    
                    self.reboundVelocity[0], self.reboundVelocity[1], self.reboundVelocity[2] = vertexBounce(resultV, angle, [0, 1], self.e, 'sin')
                    self.cords[0] += pMultiplier[0] * self.reboundVelocity[0]
                    self.cords[1] = self.oldCords[1] + self.reboundVelocity[1] * yMultiplier
                    self.cords[2] += pMultiplier[1] * self.reboundVelocity[2]
                    self.normalForce[0] = nMultiplier[0] * resultF * math.sin(angle[1]) * math.sin(angle[0])
                    self.normalForce[2] = nMultiplier[1] * resultF * math.sin(angle[1]) * math.cos(angle[0])

                elif (self.lastCollision == 'left') or (self.lastCollision == 'right'):
                    angle = getThreeDAngle(b.vertex[vertexIdx[0]], self.cords, 'x')
                    if (vertexIdx[0] == 1) or (vertexIdx[0] == 4) or (vertexIdx[0] == 6) or (vertexIdx[0] == 7):
                        pMultiplier = [1, 1]
                        if (vertexIdx[0] == 6) or (vertexIdx[0] == 7):
                            nMultiplier = [-1, -1]
                        elif (vertexIdx[0] == 1) or (vertexIdx[0] == 4):
                            nMultiplier = [1, 1]
                    elif (vertexIdx[0] == 2) or (vertexIdx[0] == 3) or (vertexIdx[0] == 0) or (vertexIdx[0] == 5):
                        pMultiplier = [-1, -1]
                        if (vertexIdx[0] == 0) or (vertexIdx[0] == 5):
                            nMultiplier = [1, 1]
                        elif (vertexIdx[0] == 2) or (vertexIdx[0] == 3):
                            nMultiplier = [-1, -1]
                    if self.lastCollision == 'left':
                        yMultiplier = 1
                    elif self.lastCollision == 'right':
                        yMultiplier = -1
                    
                    self.reboundVelocity[2], self.reboundVelocity[0], self.reboundVelocity[1] = vertexBounce(resultV, angle, [0, 1], self.e, 'sin')
                    self.cords[1] += pMultiplier[0] * self.reboundVelocity[1]
                    self.cords[0] = self.oldCords[0] + self.reboundVelocity[0] * yMultiplier
                    self.cords[2] += pMultiplier[1] * self.reboundVelocity[2]
                    self.normalForce[1] = nMultiplier[0] * resultF * math.cos(angle[1]) * math.cos(angle[0])
                    self.normalForce[2] = nMultiplier[1] * resultF * math.cos(angle[1]) * math.sin(angle[0])

                elif (self.lastCollision == 'front') or (self.lastCollision == 'back'):
                    angle = getThreeDAngle(b.vertex[vertexIdx[0]], self.cords, 'z')
                    if (vertexIdx[0] == 0) or (vertexIdx[0] == 1) or (vertexIdx[0] == 3) or (vertexIdx[0] == 6):
                        pMultiplier = [-1, -1]
                        nMultiplier = [-1, -1]
                    elif (vertexIdx[0] == 7) or (vertexIdx[0] == 2) or (vertexIdx[0] == 4) or (vertexIdx[0] == 5):
                        pMultiplier = [1, 1]
                        nMultiplier = [1, 1]
                    if self.lastCollision == 'front':
                        yMultiplier = -1
                    elif self.lastCollision == 'back':
                        yMultiplier = 1
                    
                    self.reboundVelocity[0], self.reboundVelocity[2], self.reboundVelocity[1] = vertexBounce(resultV, angle, [0, 1], self.e, 'sin')
                    self.cords[0] += pMultiplier[0] * self.reboundVelocity[0]
                    self.cords[2] = self.oldCords[2] + self.reboundVelocity[2] * yMultiplier
                    self.cords[1] += pMultiplier[1] * self.reboundVelocity[1]
                    self.normalForce[0] = nMultiplier[0] * resultF * math.sin(angle[1]) * math.sin(angle[0])
                    self.normalForce[1] = nMultiplier[1] * resultF * math.sin(angle[1]) * math.cos(angle[0])
                
                # print(self.lastCollision, math.degrees(angle[0]), math.degrees(angle[1]), vertexIdx[0])

            else:
                self.normalForce = [0, 0, 0]
                self.reboundVelocity = [0, 0, 0]


# class for cylinders (joints) connecting spheres
class Joint:
    def __init__(self, show, maxLength, stiffness, pOne, pTwo, *theForceJoint):
        self.height = 1
        self.pOne = pOne
        self.pTwo = pTwo
        if stiffness == '':
            self.stiffness = 0.1
        else:
            self.stiffness = stiffness
        self.cords = [0, 0, 0]
        self.angle = [0, 0, 0]
        self.show = show
        if maxLength == '':
            self.maxLength = distance(game.points[self.pOne].cords, game.points[self.pTwo].cords)
        else:
            self.maxLength = maxLength
        self.diff = [0, 0, 0]  # prevents multiple sq(rt) calculations to increase performance
        self._update = [0, 0, 0]
        if self.show:
            self.cylinder = vizshape.addCylinder(self.height, jointRadius, slices=jointResolution)  # make the cyldinder object for the joint if shown
        self.theForceJoint = False
        self.cIdx = -1
        # additional arguments to set the joint to be "the chosen force joint"
        if len(theForceJoint) > 0:
            self.theForceJoint = theForceJoint[0]
            self.cIdx = theForceJoint[1]

    # update the position and appearance of the joint
    def update(self):
        if self.show:
            self.cylinder.remove()

        for d in range(3):
            if self.theForceJoint:
                self.diff[d] = controls.hand[self.cIdx].cords[d] - game.points[self.pTwo].cords[d]
            else:
                self.diff[d] = game.points[self.pOne].cords[d] - game.points[self.pTwo].cords[d]

        self.height = diffDistance(self.diff[0], self.diff[1], self.diff[2])

        if self.show:
            self.cylinder = vizshape.addCylinder(self.height, jointRadius, slices=jointResolution)
            if self.theForceJoint:
                self.cords = midpoint(controls.hand[self.cIdx], game.points[self.pTwo])
                self.cylinder.setEuler(getAngle(controls.hand[self.cIdx].cords, game.points[self.pTwo].cords), 'd')
            else:
                self.cords = midpoint(game.points[self.pOne], game.points[self.pTwo])
                self.cylinder.setEuler(getAngle(game.points[self.pOne].cords, game.points[self.pTwo].cords), 'd')

            self.cylinder.setPosition(self.cords)

    # constrain points connected to this joint
    def constrain(self):
        if (self.height < self.maxLength) or (self.height > self.maxLength):
            for u in range(3):
                self._update[u] = self.stiffness * self.diff[u] * ((self.maxLength / self.height) - 1)

        for i in range(3):
            if self.theForceJoint:
                game.points[self.pTwo].cords[i] -= self._update[i]  # pull last dragged point regardless of its mass
            else:
                game.points[self.pOne].cords[i] += self._update[i] / game.points[self.pOne].mass  # pull each point depending on its mass
                game.points[self.pTwo].cords[i] -= self._update[i] / game.points[self.pTwo].mass  # pull each point depending on its mass 


class CollisionRect:
    def __init__(self, size, cords, angle):
        self.size = size
        self.rect = vizshape.addBox(self.size)
        self.cords = cords
        self.angle = angle
        self.vertex = []  # [x, y, x] -> [['right', 'top', 'front'], ['left', 'top', 'front'], ['right', 'bottom', 'front'], ['left', 'bottom', 'front'], ['right', 'top', 'back'], ['left', 'top', 'back'], ['right', 'bottom', 'back'], ['left', 'bottom', 'back']]
        self.plane = {
            'front': [0, 0, 0],
            'back': [0, 0, 0],
            'left': [0, 0, 0],
            'right': [0, 0, 0],
            'top': [0, 0, 0],
            'bottom': [0, 0, 0]
        }
        self.update()

    def update(self):
        self.rect.remove()
        self.rect = vizshape.addBox(self.size)
        self.rect.setPosition(self.cords)
        self.rect.setEuler(self.angle)
        sizeMultiplier = [0.5, 0.5, 0.5]
        for v in range(8):
            if v == 1:
                sizeMultiplier[0] = -sizeMultiplier[0]
            elif v == 2:
                sizeMultiplier[1] = -sizeMultiplier[1]
            elif v == 3:
                sizeMultiplier[2] = -sizeMultiplier[2]
            elif v == 4:
                sizeMultiplier[1] = -sizeMultiplier[1]
            elif v == 5:
                sizeMultiplier[0] = -sizeMultiplier[0]
            elif v == 6:
                sizeMultiplier[1] = -sizeMultiplier[1]
            elif v == 7:
                sizeMultiplier[2] = -sizeMultiplier[2]
            tempVertex = [0, 0, 0]
            for i in range(3):
                tempVertex[i] = self.cords[i] + (self.size[i] * sizeMultiplier[i])
            self.vertex.append(tempVertex)
        print(self.vertex)
        # tempVertex = []
        # for x in range(len(self.vertex)):
        #    tempVertex.append([])
        #    for y in range(len(self.vertex[x])):
        #        if y == 0:
        #            if self.vertex[x][y] == 1:
        #                tempVertex[x].append('right')
        #            elif self.vertex[x][y] == -1:
        #                tempVertex[x].append('left')
        #        elif y == 1:
        #            if self.vertex[x][y] == 1:
        #                tempVertex[x].append('top')
        #            elif self.vertex[x][y] == -1:
        #                tempVertex[x].append('bottom')
        #        elif y == 2:
        #            if self.vertex[x][y] == 1:
        #                tempVertex[x].append('front')
        #            elif self.vertex[x][y] == -1:
        #                tempVertex[x].append('back')
        # print(tempVertex)
        self.plane['front'] = self.cords[2] + (self.size[2] / 2)
        self.plane['back'] = self.cords[2] - (self.size[2] / 2)
        self.plane['left'] = self.cords[0] - (self.size[0] / 2)
        self.plane['right'] = self.cords[0] + (self.size[0] / 2)
        self.plane['top'] = self.cords[1] + (self.size[1] / 2)
        self.plane['bottom'] = self.cords[1] - (self.size[1] / 2)


game = Main()

# makes a cube using points and joints
cube = False
if cube:
    cubeSize = 8
    for ve in range(cubeSize):
        if ve != 7:
            game.points.append(Point(0.1, 1000))
        else:
            game.points.append(Point(0.3, 1000))
    game.points[0].cords = [2, 4.5, 2]  # top-front-right
    game.points[0].oldCords = [2, 4.5, 2]
    game.points[1].cords = [2, 4.5, -2]  # top-back-right
    game.points[1].oldCords = [2, 4.5, -2]
    game.points[2].cords = [-2, 4.5, -2]  # top-back-left
    game.points[2].oldCords = [-2, 4, -2]
    game.points[3].cords = [-2, 4.5, 2]  # top-front-left
    game.points[3].oldCords = [-2, 4, 2]
    game.points[4].cords = [2, 0.5, 2]
    game.points[4].oldCords = [2, 0.5, 2]
    game.points[5].cords = [2, 0.5, -2]
    game.points[5].oldCords = [2, 0, -2]
    game.points[6].cords = [-2, 0.5, -2]
    game.points[6].oldCords = [-2, 0.5, -2]
    game.points[7].cords = [-2, 0.5, 2]
    game.points[7].oldCords = [-2, 0.5, 2]

    for j in range(cubeSize):
        for jo in range(cubeSize):
            if (j != jo) and (jo >= j):
                game.joints.append(Joint(True, '', 0.4, j, jo))

game.points.append(Point(0.2, 1))

game.collisionRect.append(CollisionRect((2, 2, 2), [0, 3, 3], [0, 0, 0]))

vizact.ontimer(1 / refreshRate, game.main)  # run game.main refreshRate times each second
# add framerate here
