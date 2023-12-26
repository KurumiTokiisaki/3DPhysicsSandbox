import math
from globalFunctions import sin
from globalFunctions import cos

mode = 'k'  # controller mode
fullscreen = True
gameSpeed = 1  # game speed factor
calcRate = 1000  # physics calculations/second (higher number means more accurate physics)
physicsTime = calcRate * (1 / gameSpeed)  # inverse of physics speed (cannot be larger than framerate or smaller than 60)
renderRate = 144  # render rate (lower for performance)
gConst = -9.81  # gravitational field constant
gFieldDirection = {'pitch': math.radians(90), 'yaw': math.radians(0)}
gField = [gConst * cos(gFieldDirection['pitch']) * cos(gFieldDirection['yaw']), gConst * sin(gFieldDirection['pitch']) * cos(gFieldDirection['yaw']), gConst * sin(gFieldDirection['yaw'])]  # gravitational field constant about x, y, and z
gasDensity = 1.293  # density of all gas
jointRadius = 0.015  # radius of joints
theForce = False  # when True, "recalling" points causes them to float slowly to you
jointResolution = 2  # lower to increase performance
pointResolution = 10  # lower to increase performance
k = 2500  # global spring constant (make negative to break the sandbox)
damping = 7  # global damping constant
collisionTolerance = 0.0001  # global collision tolerance (since computer programs aren't perfect unlike in real life 😭) (must lower when increasing calcRate or decreasing physicsTime; refer to collisionToleranceTables for values obtained through testing)
