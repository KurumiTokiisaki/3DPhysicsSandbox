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
from config import *

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

viz.vsync(0)  # disable vsync (cuz it decreases max calcs/second)


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
        self.pHeld = False  # stores if 'p' is held down
        self.rHeld = False  # stores if 'r' is held down
        self.physicsTime = physicsTime
        self.n = 0

    def main(self):
        # if (1 / viz.getFrameElapsed()) > 0:
        #     self.physicsTime = 1000
        # self.physicsTime += (1 / viz.getFrameElapsed()) / self.n
        # print(self.physicsTime)
        # pause if 'p' is pressed
        if (not self.pHeld) and (mode == 'k') and viz.key.isDown('p'):
            self.pause = not self.pause
            self.pHeld = True
        elif not viz.key.isDown('p'):
            self.pHeld = False

        controls.main()
        self.dragPoints()  # runs the function that detects if controller is "dragging" a point

        if not self.pause:
            for j in range(len(game.joints)):
                game.joints[j].constrain('f')
                game.joints[j].updateOldHeight()

        # detect & resolve collisions with collision boxes
        for p in range(len(self.points)):
            if (self.points[p].cords[1] - self.points[p].radius) <= self.gridFloor:
                self.points[p].cords[1] = self.points[p].oldCords[1]
            # detect collisions with other points
            for po in range(len(self.points)):
                if detectCollision(self.points[p], self.points[po]) and (p != po):
                    pass  # self.sphereCollision(p, po)
            self.points[p].move()

        for p in range(len(self.points)):
            self.points[p].tempCords = [0, 0, 0]

    def render(self):
        for p in self.points:
            p.draw()
        for j in self.joints:
            j.draw()

    # used to drag points around using pointer/controller
    def dragPoints(self):
        for c in range(len(controls.hand)):
            for p in range(len(self.points)):
                if ((mode == 'k') and (viz.mouse.getState() == select)) or ((mode == 'vr') and (steamVR_init.controllers[c].getButtonState() == select)):  # detect if the select button is being pressed, depending on the controller mode
                    if (self.dragP == 'none') and (self.dragC == 'none'):  # used to set the drag variables if they are not already set
                        if detectCollision(self.points[p], controls.hand[c]):
                            self.dragP = p
                            self.lastP = p
                            self.dragC = c
                    else:
                        self.points[self.dragP].cords = copy.deepcopy(controls.hand[self.dragC].cords)  # set the point position to the controller (that grabbed that point)'s position
            # reset drag variables if select button is not pressed
            if (self.dragC != 'none') and (((mode == 'vr') and (steamVR_init.controllers[self.dragC].getButtonState() != select)) or ((mode == 'k') and (viz.mouse.getState() != select))):
                self.dragP = 'none'
                self.dragC = 'none'
            # recalls the last clicked point to the controller's position
            if ((mode == 'vr') and (steamVR_init.controllers[c].getButtonState() == recall)) or ((mode == 'k') and viz.key.isDown(recall)):
                # allows the force to be used (if True)
                if theForce and (not self.theForceJoint):
                    self.joints.append(Joint(False, 0, 0.01, None, self.lastP, True, c))
                    self.theForceJoint = True
                # set cords of point to user pointer/hand
                elif not theForce:
                    self.points[self.lastP].cords = copy.deepcopy(controls.hand[c].cords)
                    if not self.rHeld:
                        cordDiff = []
                        for co in range(3):
                            cordDiff.append(self.points[self.lastP].cords[co] - self.points[self.lastP].oldCords[co])
                        for po in range(len(self.points)):
                            if (po != self.lastP) and (self.points[po].cloth == self.points[self.lastP].cloth) and (self.points[self.lastP].cloth != ''):
                                for cor in range(3):
                                    self.points[po].cords[cor] += cordDiff[cor]
                                    self.points[po].oldCords[cor] += cordDiff[cor]
                        self.points[self.lastP].oldCords = self.points[self.lastP].cords
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

    def addPoint(self, point):
        self.points.append(point)
        for p in range(len(self.points)):
            self.points[p].pIdx = p


# class for spheres
class Point:
    def __init__(self, radius, density):
        self.radius = radius
        self.sphere = vizshape.addSphere(radius, slices=pointResolution)  # vizard object for sphere
        self.cords = [0, 0, 0]
        self.oldCords = [0, 0, 0]  # coordinate position from last frame
        self.velocity = [0, 0, 0]
        self.momentum = [0, 0, 0]
        self.oldVelocity = [0, 0, 0]  # velocity value from the previous frame
        self.reboundVelocity = [0, 0, 0]  # resultant velocity caused by collisions
        self.force = [0, 0, 0]
        self.normalForce = [0, 0, 0]  # here's how I'll calculate this: https://drive.google.com/file/d/1ES6T8RilTcE5Pu7Zhdxfo6R6hvvsViAT/view?usp=drive_link
        self.normalForceAfter = [0, 0, 0]
        self.acc = [0, 0, 0]
        self.density = density
        self.volume = 4 / 3 * math.pi * self.radius ** 3
        self.mass = self.density * self.volume
        self.weight = [self.mass * gField[0], self.mass * gField[1], self.mass * gField[2]]
        self.gasDrag = [0, 0, 0]
        self.liquidDrag = [0, 0, 0]
        self.gasUpthrust = [0, 0, 0]
        self.liquidUpthrust = [0, 0, 0]
        self.friction = [0, 0, 0]
        self.constrainForce = [0, 0, 0]
        self.solidCubeCollision = False
        self.liquidCubeCollision = False
        self.collision = ''
        self.lastCollision = ''
        self.vertexState = ''  # closest vertex plane
        self.e = 0  # elasticity (should be 0 when part of a cloth)
        self.sf = 0  # surface friction coefficient. set to 'sticky' for infinite value.
        self.multiplier = 1  # variable for movement calcs
        self.constrainVelocity = [0, 0, 0]
        self.connectedJoint = False
        self.cloth = ''
        self.b = None  # current colliding solid
        self.movingAngle = [0, 0, 0]  # direction of movement
        self.collisionState = ''
        self.bAngle = [0, 0, 0]  # stores angle of b.angle
        self.angleState = True  # used for special cases of b.angle
        self.pIdx = ''  # index in game.points
        self.tempCords = [0, 0, 0]

    def setRadiusDensity(self, radius, density):
        self.radius = radius
        self.volume = 4 / 3 * math.pi * self.radius ** 3
        self.mass = density * self.volume
        self.weight = self.mass * gField
        self.sphere.remove()
        self.sphere = vizshape.addSphere(radius, slices=pointResolution)

    def move(self):
        self.oldVelocity = copy.deepcopy(self.velocity)

        # Verlet integration
        for c in range(3):
            self.velocity[c] = (self.cords[c] - self.oldCords[c])  # * game.physicsTime  # set velocity to change in position

        if not game.pause:
            self.physics()
        self.b = self.boxCollision()  # stores list of currently colliding solid collision box, also running collision code

        self.oldCords = copy.deepcopy(self.cords)

        if not game.pause:
            for v in range(3):
                self.cords[v] += self.velocity[v]  # / game.physicsTime  # change coordinates based on velocity

        # update the visuals of joints and constrain points
        for j in range(len(game.joints)):
            # if game.joints[j].pOne == self.pIdx:
            if not game.pause:
                game.joints[j].update()
                game.joints[j].constrain('n')

    def draw(self):
        self.sphere.setPosition(self.cords)

    def physics(self):
        for axis in range(3):
            # add physics here
            # self.gasDrag[axis] = 0.5 * gasDensity * -getSign(self.velocity[axis]) * ((self.velocity[axis] / time) ** 2) * 2 * math.pi * (self.radius ** 2)
            # self.gasUpthrust[axis] = -(4 / 3) * math.pi * (self.radius ** 3) * gasDensity * gField[axis]

            self.force[axis] = self.gasDrag[axis] + self.liquidDrag[axis] + self.gasUpthrust[axis] + self.liquidUpthrust[axis] + self.weight[axis]
            self.force[axis] += self.constrainForce[axis]  # constraining force added here to prevent points from floating

        # calculate normal reaction force. the reason it's here and not in boxCollision is because resultant force must first be calculated above.
        if self.b:  # if collision box list is not empty
            for b in self.b:
                self.bAngle = copy.deepcopy(b.angle)  # assigns collisionRect angle to local variable, so it can be changed (for the sake of calculation) without changing the collisionRect's angle itself

                if (self.collision == 'top') or (self.collision == 'bottom'):
                    resultF = 0
                    # check out this link to see why these if statements are used here, as well as the math:
                    if (self.force[0] * self.multiplier) > 0:
                        resultF += abs(self.force[0] * math.sin(self.bAngle[2]))
                    if (self.force[1] * self.multiplier) < 0:
                        resultF += abs(self.force[1] * math.cos(self.bAngle[2]))

                elif (self.collision == 'right') or (self.collision == 'left'):
                    self.bAngle[2] -= math.pi / 2
                    resultF = 0
                    if (self.force[0] * self.multiplier) < 0:
                        resultF += abs(self.force[0] * math.sin(self.bAngle[2]))
                    if (self.force[1] * self.multiplier) < 0:
                        resultF += abs(self.force[1] * math.cos(self.bAngle[2]))

                elif (self.collision == 'front') or (self.collision == 'back'):
                    resultF = 0
                    if (self.force[2] * self.multiplier) < 0:
                        resultF += abs(self.force[2])
                    self.normalForceAfter[2] = resultF * self.multiplier
                    for plane in range(2):
                        self.friction[plane] = -resultF * self.sf * getSign(self.velocity[plane]) * sin(abs(self.movingAngle[0]))

                # negative coefficients used for friction here since it always acts in the opposite direction to motion
                if self.collisionState == 'y':
                    # negative coefficients used for normalForce here since it always acts in the opposite direction to resultant force
                    # *0.999999 used here to compensate for floating point error
                    self.normalForce[0] = -resultF * sin(self.bAngle[2]) * self.multiplier * 0.999999
                    self.normalForce[1] = resultF * cos(self.bAngle[2]) * self.multiplier * 0.999999
                    # self.normalForce[2] = -resultF * sin(self.bAngle[0]) * self.multiplier * 0.999999
                    self.friction[0] = -getSign(self.velocity[0]) * resultF * cos(self.bAngle[2]) * self.sf * sin(abs(self.movingAngle[1]))
                    self.friction[2] = -getSign(self.velocity[2]) * resultF * cos(self.bAngle[2]) * self.sf * cos(abs(self.movingAngle[1]))
                elif self.collisionState == 'x':
                    self.normalForce[0] = -resultF * sin(self.bAngle[2]) * self.multiplier * 0.999999
                    self.normalForce[1] = resultF * cos(self.bAngle[2]) * self.multiplier * 0.999999
                    # self.normalForce[2] = -resultF * sin(self.bAngle[0]) * self.multiplier * 0.999999
                    self.friction[1] = -getSign(self.velocity[1]) * resultF * cos(self.bAngle[2]) * self.sf * cos(abs(self.movingAngle[2]))
                    self.friction[2] = -getSign(self.velocity[2]) * resultF * cos(self.bAngle[2]) * self.sf * sin(abs(self.movingAngle[2]))

        for axis in range(3):
            self.force[axis] += self.normalForce[axis] + self.friction[axis]  # - self.constrainForce[axis]
            self.acc[axis] = self.force[axis] / self.mass
            self.force[axis] += self.normalForceAfter[axis]  # parallel normal force done after acceleration calculation as all point collisions are assumed to have infinite magnitude
            self.velocity[axis] += self.acc[axis] / (game.physicsTime ** 2)  # divide by time since d(v) = a * d(t)
        # print(self.force, self.collision, self.collisionState)
        # print(self.velocity[1])
        self.constrainForce = [0, 0, 0]  # reset constrainForce

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
        bArray = []
        for b in game.collisionRect:
            self.bAngle = copy.deepcopy(b.angle)
            # self.collision represents the surface of a collision cuboid that the point is CURRENTLY (hence making self.collision = '' in else cases) in front of, using only its center point as reference
            yCollisionPlane = self.yCollisionPlane(b)
            xCollisionPlane = self.xCollisionPlane(b)

            # check out the logic here: https://drive.google.com/file/d/1B-GqxPcpGkWAE_ogzMvYntTNmt8R99gT/view?usp=drive_link
            self.vertexState = ''  # stores the facing axis of the nearest vertex
            if ((self.cords[1] > yCollisionPlane['right']['y']) or (self.cords[1] < yCollisionPlane['left']['y'])) and ((self.cords[1] > yCollisionPlane['top']['y']) or (self.cords[1] < yCollisionPlane['bottom']['y'])) and (
                    (self.cords[2] <= b.plane['front']) and (self.cords[2] >= b.plane['back'])):  # x > right, x < left, y > top, y < bottom, back < z < front
                self.vertexState = 'z'
            elif ((self.cords[1] > yCollisionPlane['right']['y']) or (self.cords[1] < yCollisionPlane['left']['y'])) and ((self.cords[1] <= yCollisionPlane['top']['y']) and (self.cords[1] >= yCollisionPlane['bottom']['y'])) and (
                    (self.cords[2] > b.plane['front']) or (self.cords[2] < b.plane['back'])):  # x > right, x < left, bottom < y < top, z > front, z < back
                self.vertexState = 'y'
            elif ((self.cords[1] <= yCollisionPlane['right']['y']) and (self.cords[1] >= yCollisionPlane['left']['y'])) and ((self.cords[1] > yCollisionPlane['top']['y']) or (self.cords[1] < yCollisionPlane['bottom']['y'])) and (
                    (self.cords[2] > b.plane['front']) or (self.cords[2] < b.plane['back'])):  # left < x < right, y > top, y < bottom, z > front, z < back
                self.vertexState = 'x'

            # self.lastCollision represents the surface of a collision cuboid that the point was LAST in front of, factoring in its radius as well. this value never resets.
            if (self.cords[1] <= (yCollisionPlane['right']['y'] + self.radius)) and (self.cords[1] >= (yCollisionPlane['left']['y'] - self.radius)) and (self.cords[2] <= (b.plane['front'] + self.radius)) and (self.cords[2] >= (b.plane['back'] - self.radius)):
                if self.cords[1] >= (yCollisionPlane['top']['y'] + self.radius):
                    self.lastCollision = 'top'
                elif self.cords[1] <= (yCollisionPlane['bottom']['y'] - self.radius):
                    self.lastCollision = 'bottom'
            elif (self.cords[1] <= yCollisionPlane['top']['y']) and (self.cords[1] >= yCollisionPlane['bottom']['y']) and (self.cords[2] <= b.plane['front']) and (self.cords[2] >= b.plane['back']):
                if self.cords[1] >= (yCollisionPlane['right']['y'] + self.radius):
                    self.lastCollision = 'right'
                elif self.cords[1] <= (yCollisionPlane['left']['y'] - self.radius):
                    self.lastCollision = 'left'
            elif (self.cords[1] <= (yCollisionPlane['top']['y'] + self.radius)) and (self.cords[1] >= (yCollisionPlane['bottom']['y'] - self.radius)) and (self.cords[1] <= (yCollisionPlane['right']['y'] + self.radius)) and (self.cords[1] >= (yCollisionPlane['left']['y'] - self.radius)):
                if self.cords[2] >= (b.plane['front'] - self.radius):
                    self.lastCollision = 'front'
                elif self.cords[2] <= (b.plane['back'] + self.radius):
                    self.lastCollision = 'back'

            self.solidCubeCollision = (self.cords[1] <= (yCollisionPlane['top']['y'] + self.radius / cos(b.angle[2]))) and (self.cords[1] >= (yCollisionPlane['bottom']['y'] - self.radius / cos(b.angle[2]))) and (self.cords[1] <= (yCollisionPlane['right']['y'] + self.radius / sin(b.angle[2]))) and (self.cords[1] >= (yCollisionPlane['left']['y'] - self.radius / sin(b.angle[2]))) and (
                    self.cords[2] <= (b.plane['front'] + self.radius)) and (self.cords[2] >= (b.plane['back'] - self.radius))

            if not self.solidCubeCollision:  # reset self.collision when not in a collision
                self.collision = ''
            if (self.cords[1] <= yCollisionPlane['right']['y']) and (self.cords[1] >= yCollisionPlane['left']['y']) and (self.cords[2] <= b.plane['front']) and (self.cords[2] >= b.plane['back']):
                if self.cords[1] >= (yCollisionPlane['top']['y']):
                    self.collision = 'top'
                elif self.cords[1] <= (yCollisionPlane['bottom']['y']):
                    self.collision = 'bottom'
            elif (self.cords[1] <= yCollisionPlane['top']['y']) and (self.cords[1] >= yCollisionPlane['bottom']['y']) and (self.cords[2] <= b.plane['front']) and (self.cords[2] >= b.plane['back']):
                if self.cords[1] >= (yCollisionPlane['right']['y']):
                    self.collision = 'right'
                elif self.cords[1] <= (yCollisionPlane['left']['y']):
                    self.collision = 'left'
            elif (self.cords[1] < yCollisionPlane['top']['y']) and (self.cords[1] > yCollisionPlane['bottom']['y']) and (self.cords[1] < yCollisionPlane['right']['y']) and (self.cords[1] > yCollisionPlane['left']['y']):
                if self.cords[2] >= (b.plane['front']):
                    self.collision = 'front'
                elif self.cords[2] <= (b.plane['back']):
                    self.collision = 'back'
            # print(self.vertexState, self.collision)

            # get the distance until edge/vertex collision
            if (self.collision == '') or (self.vertexState != ''):  # "why should we resolve vertex/edge collisions if the point is in front of a face on the collision rect?" hence, this if statement is used to optimize performance.
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
            if (self.lastCollision == 'right') or (self.lastCollision == 'top') or (self.lastCollision == 'front'):
                self.multiplier = 1
            else:
                self.multiplier = -1

            # detect collisions between points and planes (flat surfaces) on a collision rect (cuboid)
            if (self.vertexState == '') and (self.collision != '') and self.solidCubeCollision:
                if str(self.sf) == 'sticky':
                    self.cords = self.oldCords  # "stick" cords to oldCords
                else:
                    if (self.collision == 'right') or (self.collision == 'left'):
                        xyz = 0  # colliding about x
                        xyzFriction = [1, 2]  # movement about y and z
                    elif (self.collision == 'top') or (self.collision == 'bottom'):
                        xyz = 1  # colliding about y
                        xyzFriction = [0, 2]  # movement about x and z
                    elif (self.collision == 'front') or (self.collision == 'back'):
                        xyz = 2  # colliding about z
                        xyzFriction = [0, 1]  # movement about x and y

                    resultV = 0  # resultant velocity used for elastic points (when e > 0)

                    if (self.collision == 'top') or (self.collision == 'right') or (self.collision == 'bottom') or (self.collision == 'left'):  # colliding with top/right/bottom/left plane
                        if (self.collision == 'right') or (self.collision == 'left'):
                            self.angleState = False  # used to reverse direction of resultV when needed
                            self.bAngle[2] -= math.pi / 2
                        else:
                            self.angleState = True
                        # if self.angleState or (abs(math.degrees(self.bAngle[2])) < 45):
                        resultV -= self.oldVelocity[0] * cos(self.bAngle[2])  # / game.physicsTime
                        resultV -= self.oldVelocity[1] * sin(self.bAngle[2])  # / game.physicsTime
                        # else:  # for some reason there is a special case scenario here. I will fix this later.
                        #     resultV += self.oldVelocity[0] * cos(self.bAngle[2])  # / game.physicsTime
                        #     resultV += self.oldVelocity[1] * sin(self.bAngle[2])  # / game.physicsTime

                        # check out this link to see why I need the logic below:
                        if abs(math.degrees(self.bAngle[2])) < 45:
                            self.collisionState = 'y'
                            if self.normalForce == [0, 0, 0]:
                                # if self.velocity[1] >= 0:  # moving upwards
                                #     self.oldCords[0] = self.cords[0] + resultV
                                # else:  # moving downwards
                                #     self.cords[0] = self.oldCords[0] - resultV
                                self.velocity[0] = -resultV
                                yCollisionPlane = self.yCollisionPlane(b)  # explicitly reassign yCollisionPlane after changing cords value to allow sphere to stay on the ramp's surface
                            self.cords[1] = yCollisionPlane[self.collision]['y'] + (self.multiplier * self.radius / cos(self.bAngle[2])) + (cos(self.bAngle[2]) * resultV * self.e)
                            self.cords[0] -= resultV * cos(self.bAngle[2]) * self.e
                        else:
                            self.collisionState = 'x'
                            if self.normalForce == [0, 0, 0]:
                                # if self.velocity[0] <= 0:  # moving left
                                #     self.oldCords[1] = self.cords[1] + resultV
                                # else:  # moving right
                                #     self.cords[1] = self.oldCords[1] - resultV
                                self.velocity[1] = -resultV
                                xCollisionPlane = self.xCollisionPlane(b)
                            self.cords[0] = xCollisionPlane[self.collision]['x'] - (self.multiplier * self.radius / sin(self.bAngle[2])) + (sin(self.bAngle[2]) * resultV * self.e)
                            self.cords[1] -= resultV * cos(self.bAngle[2]) * self.e
                    elif (self.collision == 'front') or (self.collision == 'back'):
                        self.cords[2] = b.plane[self.collision] + (self.radius * self.multiplier)
                        self.oldCords[2] = self.cords[2]

                bArray.append(b)

            # detect collisions between points and edges on a collision rect (cuboid)
            elif (self.vertexState != '') and (minDist <= (distance(b.vertex[vertexIdx[0]], b.vertex[vertexIdx[1]]))):
                if str(self.sf) == 'sticky':
                    self.cords = self.oldCords
                else:
                    sinCos = 'sin'
                    if (self.lastCollision == 'top') or (self.lastCollision == 'bottom'):
                        i = [2, 1, 0]

                    elif (self.lastCollision == 'left') or (self.lastCollision == 'right'):
                        i = [2, 0, 1]

                    elif (self.lastCollision == 'front') or (self.lastCollision == 'back'):
                        i = [1, 0, 2]

                    collisionPoint = self.cords[0] + (self.radius / cos(self.bAngle[2])), yCollisionPlane[self.lastCollision]['y'], b.vertex[vertexIdx[0]][i[0]]
                    self.angle = getThreeDAngle(collisionPoint, self.cords, self.vertexState)
                    # angle = getTwoDAngle([self.cords[i[1]], self.cords[i[0]]], [b.vertex[vertexIdx[0]][i[1]], b.vertex[vertexIdx[0]][i[0]]])
                    resultV = math.sqrt(self.oldVelocity[i[0]] ** 2 + self.oldVelocity[i[1]] ** 2)
                    resultF = math.sqrt(self.force[i[0]] ** 2 + self.force[i[1]] ** 2)
                    self.reboundVelocity[i[0]], self.reboundVelocity[i[1]], self.reboundVelocity[i[2]] = edgeBounce(resultV, self.angle, self.e, -1)
                    self.cords[i[0]] += self.multiplier * self.reboundVelocity[i[0]]
                    self.oldCords[i[1]] = yCollisionPlane[self.lastCollision]['y'] + (self.radius * cos(self.angle[0]))
                    self.cords[i[1]] = yCollisionPlane[self.lastCollision]['y'] + ((self.radius * cos(self.angle[0])) + self.reboundVelocity[i[1]])
                    self.cords[i[2]] += self.multiplier * self.reboundVelocity[i[2]]
                    if sinCos == 'sin':
                        self.normalForce[i[0]] = resultF * sin(self.angle[0]) * self.multiplier  # getSign used here as a result of testing
                        self.normalForce[i[2]] = -resultF * sin(self.bAngle[2]) * self.multiplier
                    elif sinCos == 'cos':
                        self.normalForce[i[0]] = resultF * cos(self.angle[0]) * self.multiplier
                        self.normalForce[i[2]] = -resultF * cos(self.bAngle[2]) * self.multiplier
                    # print(self.reboundVelocity, self.normalForce, angle)
                bArray.append(b)

            # detect collisions between points and vertices (corners) on a collision rect (cuboid)
            elif (self.collision == '') and (self.vertexState == '') and (distance(b.vertex[vertexIdx], self.cords) <= self.radius):
                if str(self.sf) == 'sticky':
                    self.cords = self.oldCords
                else:
                    resultF = math.sqrt(self.force[0] ** 2 + self.force[1] ** 2 + self.force[2] ** 2)
                    resultV = math.sqrt(self.oldVelocity[0] ** 2 + self.oldVelocity[1] ** 2 + self.oldVelocity[2] ** 2)

                    # nMultiplier was obtained through testing
                    if (self.lastCollision == 'top') or (self.lastCollision == 'bottom'):
                        self.angle = getThreeDAngle(b.vertex[vertexIdx], self.cords, 'y')
                        if (vertexIdx == 0) or (vertexIdx == 1) or (vertexIdx == 6) or (vertexIdx == 3):
                            pMultiplier = [-1, -1]
                            nMultiplier = [1, 1]
                        elif (vertexIdx == 4) or (vertexIdx == 5) or (vertexIdx == 2) or (vertexIdx == 7):
                            pMultiplier = [1, 1]
                            nMultiplier = [-1, -1]
                        if self.lastCollision == 'top':
                            yMultiplier = -1
                        elif self.lastCollision == 'bottom':
                            yMultiplier = 1

                        self.reboundVelocity[0], self.reboundVelocity[1], self.reboundVelocity[2] = vertexBounce(resultV, self.angle, self.e)
                        self.cords[0] += pMultiplier[0] * self.reboundVelocity[0]
                        self.cords[1] = self.oldCords[1] + self.reboundVelocity[1] * yMultiplier
                        self.cords[2] += pMultiplier[1] * self.reboundVelocity[2]
                        self.normalForce[0] = nMultiplier[0] * resultF * cos(self.angle[1]) * sin(self.angle[0]) * -yMultiplier
                        self.normalForce[2] = nMultiplier[1] * resultF * cos(self.angle[1]) * cos(self.angle[0]) * -yMultiplier

                    elif (self.lastCollision == 'left') or (self.lastCollision == 'right'):
                        self.angle = getThreeDAngle(b.vertex[vertexIdx], self.cords, 'x')
                        if (vertexIdx == 1) or (vertexIdx == 4) or (vertexIdx == 6) or (vertexIdx == 7):
                            pMultiplier = [1, 1]
                            if (vertexIdx == 6) or (vertexIdx == 7):
                                nMultiplier = [-1, -1]
                            elif (vertexIdx == 1) or (vertexIdx == 4):
                                nMultiplier = [1, 1]
                        elif (vertexIdx == 2) or (vertexIdx == 3) or (vertexIdx == 0) or (vertexIdx == 5):
                            pMultiplier = [-1, -1]
                            if (vertexIdx == 0) or (vertexIdx == 5):
                                nMultiplier = [1, 1]
                            elif (vertexIdx == 2) or (vertexIdx == 3):
                                nMultiplier = [-1, -1]
                        if self.lastCollision == 'left':
                            yMultiplier = 1
                        elif self.lastCollision == 'right':
                            yMultiplier = -1

                        self.reboundVelocity[2], self.reboundVelocity[0], self.reboundVelocity[1] = vertexBounce(resultV, self.angle, self.e)
                        self.cords[1] += pMultiplier[0] * self.reboundVelocity[1]
                        self.cords[0] = self.oldCords[0] + self.reboundVelocity[0] * yMultiplier
                        self.cords[2] += pMultiplier[1] * self.reboundVelocity[2]
                        self.normalForce[1] = nMultiplier[0] * resultF * cos(self.angle[1]) * cos(self.angle[0])
                        self.normalForce[2] = nMultiplier[1] * resultF * cos(self.angle[1]) * sin(self.angle[0])

                    elif (self.lastCollision == 'front') or (self.lastCollision == 'back'):
                        self.angle = getThreeDAngle(b.vertex[vertexIdx], self.cords, 'z')
                        if (vertexIdx == 0) or (vertexIdx == 1) or (vertexIdx == 3) or (vertexIdx == 6):
                            pMultiplier = [-1, -1]
                            nMultiplier = [-1, -1]
                        elif (vertexIdx == 7) or (vertexIdx == 2) or (vertexIdx == 4) or (vertexIdx == 5):
                            pMultiplier = [1, 1]
                            nMultiplier = [1, 1]
                        if self.lastCollision == 'front':
                            yMultiplier = -1
                        elif self.lastCollision == 'back':
                            yMultiplier = 1

                        self.reboundVelocity[0], self.reboundVelocity[2], self.reboundVelocity[1] = vertexBounce(resultV, self.angle, self.e)
                        self.cords[0] += pMultiplier[0] * self.reboundVelocity[0]
                        self.cords[2] = self.oldCords[2] + self.reboundVelocity[2] * yMultiplier
                        self.cords[1] += pMultiplier[1] * self.reboundVelocity[1]
                        self.normalForce[0] = nMultiplier[0] * resultF * cos(self.angle[1]) * sin(self.angle[0]) * yMultiplier
                        self.normalForce[1] = nMultiplier[1] * resultF * cos(self.angle[1]) * cos(self.angle[0]) * yMultiplier

                    # print(self.lastCollision, math.degrees(angle[0]), math.degrees(angle[1]), vertexIdx[0])
                bArray.append(b)

            else:
                # reset values that depend on a collision when not colliding
                self.normalForce = [0, 0, 0]
                self.normalForceAfter = [0, 0, 0]
                self.reboundVelocity = [0, 0, 0]
                self.friction = [0, 0, 0]
        return bArray


# class for cylinders (joints) connecting spheres
class Joint:
    def __init__(self, show, origLength, stiffness, pOne, pTwo, bounciness, maxLength, *theForceJoint):
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
        self.maxLength = maxLength  # maximum length of joint before breaking
        self.diff = [0, 0, 0]  # by having this local variable,  multiple redundant sq(rt) calcs are prevented increase performance
        self.constrainForce = [0, 0, 0]
        self._update = [0, 0, 0]
        self.damping = [0, 0, 0]
        if self.show:
            self.cylinder = vizshape.addCylinder(1, self.radius, slices=jointResolution)  # make the joint visible if shown
            # self.cylinder = viz.add('sphere.glb')
        self.volume = math.pi * (self.radius ** 2) * self.height
        self.theForceJoint = False
        self.cIdx = -1
        # additional arguments to set the joint to be "the chosen force joint"
        if len(theForceJoint) > 0:
            self.theForceJoint = theForceJoint[0]
            self.cIdx = theForceJoint[1]

    # update the position and appearance of the joint
    def update(self):
        for d in range(3):
            if self.theForceJoint:
                self.diff[d] = controls.hand[self.cIdx].cords[d] - game.points[self.pTwo].cords[d]
            else:
                self.diff[d] = (game.points[self.pOne].cords[d] + game.points[self.pOne].tempCords[d]) - (game.points[self.pTwo].cords[d] + game.points[self.pTwo].tempCords[d])

        self.height = diffDistance(self.diff[0], self.diff[1], self.diff[2])
        self.radius = math.sqrt(self.volume / (math.pi * self.height))  # r = sqrt(v / πh)
        # no need to reassign volume here since it always stays constant

    def updateOldHeight(self):
        self.oldHeight = copy.deepcopy(self.height)

    def draw(self):
        if self.show:
            self.cylinder.setScale([1, self.height, 1])  # change visual of cylinder
            if self.theForceJoint:
                self.cords = midpoint(controls.hand[self.cIdx], game.points[self.pTwo])  # set the midpoint of the joint to the middle of each connected cord
                self.cylinder.setEuler(getEulerAngle(controls.hand[self.cIdx].cords, game.points[self.pTwo].cords))  # set the facing angle of the joint to "connect" to both points
            else:
                self.cords = midpoint(game.points[self.pOne], game.points[self.pTwo])
                self.cylinder.setEuler(getEulerAngle(game.points[self.pOne].cords, game.points[self.pTwo].cords))

            self.cylinder.setPosition(self.cords)

    # constrain points connected to this joint
    def constrain(self, f):
        if (self.height < self.origLength) or (self.height > self.origLength):
            for u in range(3):
                if self.theForceJoint:
                    self._update[u] = 0.01 * (self.diff[u] * ((self.origLength / self.height) - 1))  # pull points by changing their cords directly rather than force (since it doesn't matter when you use The Force!)
                self.constrainForce[u] = self.stiffness * (self.diff[u] / self.height) * (self.origLength - self.height)  # check out the maths for this using this link:
                self.damping[u] = self.dampingConst * abs((self.diff[u] / self.height) * (self.oldHeight - self.height)) * getSign(game.points[self.pOne].velocity[u] - game.points[self.pTwo].velocity[u])  # damping force = c constant * change in joint length (relative to both points) * relative direction
        # self.stiffness = self.origStiffness * (math.pi * (self.radius ** 2)) / self.origArea  # increase stiffness as length decreases and vice versa as length increases
        for i in range(3):
            if self.theForceJoint:
                game.points[self.pTwo].cords[i] -= self._update[i]  # pull last dragged point regardless of its mass (because it's THE FORCE)
            else:
                game.points[self.pOne].tempCords[i] += self.constrainForce[i] / (game.physicsTime ** 2)
                game.points[self.pTwo].tempCords[i] -= self.constrainForce[i] / (game.physicsTime ** 2)
                if f == 'f':
                    game.points[self.pOne].constrainForce[i] += self.constrainForce[i] - self.damping[i]
                    game.points[self.pTwo].constrainForce[i] -= self.constrainForce[i] - self.damping[i]  # negative due to Newton's 3rd law
                    print(f'{game.points[self.pOne].tempCords[i]}, {game.points[self.pTwo].tempCords[i]}')

    # break the joint after extending a specified distance
    def snap(self):
        pass


class CollisionRect:
    def __init__(self, size, cords, angle, density, transparency, rectType):
        self.type = rectType
        self.angle = angle
        self.vertexAngle = [0, 0, 0]
        self.size = size
        self.rect = vizshape.addBox(self.size)
        self.cords = cords
        self.density = density
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
                else:  # z
                    tempVertex[i] = self.cords[i] + (self.size[i] * sizeMultiplier[i])

            self.vertex.append(tempVertex)
        print(self.vertex)

        self.plane['front'] = self.cords[2] + (self.size[2] / 2)
        self.plane['back'] = self.cords[2] - (self.size[2] / 2)
        self.plane['left'] = self.cords[0] - (self.size[0] / 2)
        self.plane['right'] = self.cords[0] + (self.size[0] / 2)
        self.plane['top'] = self.cords[1] + (self.size[1] / 2)
        self.plane['bottom'] = self.cords[1] - (self.size[1] / 2)

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
        print(self.plane)
        print(self.grad)


game = Main()

# makes a cube using points and joints
cube = True
if cube:
    cubeSize = 8
    for ve in range(cubeSize):
        if ve != 7:
            game.addPoint(Point(0.1, 1000))
        else:
            game.addPoint(Point(0.1, 1000))
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
            if (j != jo) and (jo >= j):
                game.joints.append(Joint(True, '', k, j, jo, damping, 69))

    for p in range(len(game.points)):
        game.points[p].e = 0
        game.points[p].cords[1] += 2
        game.points[p].oldCords[1] += 2
    # game.points.append(Point(0.1, 1000))

sphere = False
if sphere:
    game.addPoint(Point(0.01, 1000))
elif not cube:
    game.addPoint(Point(0.1, 1000))

game.collisionRect.append(CollisionRect((50, 50, 50), [0, 30, 0], [math.radians(0), 0, math.radians(30)], 1000, 0.9, 's'))  # CANNOT be negative angle or above 90 (make near-zero for an angle of 0)

vizact.ontimer(1 / calcRate, game.main)  # run game.main time times each second
vizact.ontimer(1 / renderRate, game.render)
# add framerate here
