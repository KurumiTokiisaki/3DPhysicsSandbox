import viz
import math

mode = 'vr'  # controller mode
fullscreen = True
gameSpeed = 1  # game speed factor
calcRate = 144  # physics calculations/second (higher number means more accurate physics but lower framerate)
physicsTime = calcRate * (1 / gameSpeed)  # inverse of physics speed (cannot be larger than framerate or smaller than 60)
renderRate = 90  # render rate (lower for performance)
animSpeed = 1 / renderRate  # speed of animations
gConst = -9.81  # gravitational field constant
gFieldDirection = {'pitch': math.radians(90), 'yaw': math.radians(0)}
gField = [gConst * math.cos(gFieldDirection['pitch']) * math.cos(gFieldDirection['yaw']), gConst * math.sin(gFieldDirection['pitch']) * math.cos(gFieldDirection['yaw']), gConst * math.sin(gFieldDirection['yaw'])]  # gravitational field constant about x, y, and z
gasDensity = 0  # density of all gas
jointRadius = 0.015  # radius of joints
theForce = False  # when True, "recalling" points causes them to float slowly to you
jointResolution = 3  # lower to increase performance
pointResolution = 10  # lower to increase performance
k = 2500  # global spring constant (make negative to break the sandbox)
damping = 3  # global damping constant (reduce as more points are connected to the same object)
collisionTolerance = 0  # global collision tolerance (since computer programs aren't perfect unlike in real life 😭) (must lower when increasing calcRate or decreasing physicsTime; refer to collisionToleranceTables for values obtained through testing)
collisionCalcTolerance = 0.1  # change these 2 tolerance values depending on calcRate (should be larger than collisionTolerance)

# controls for keyboard/VR
if mode == 'k':
    controls = {
        'select': 1,
        'recall': 'r',
        'reset': viz.KEY_DELETE,
        'pause': viz.key.charToCode('p'),
        'gFieldY': viz.key.charToCode('g'),
        'gField': viz.key.charToCode('h'),
        'GUISelector': None
    }
elif mode == 'vr':
    controls = {
        'select': [20, 4],
        'recall': [24, 24],
        'reset': [18, 2],
        'pause': [10, 10],
        'gFieldY': [23, 7],
        'gField': [18, 2],
        'GUISelector': None
    }
touchPad = 16
