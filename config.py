import viz
import math

# border properties
borderSize = [500, 500, 250]  # XYZ
borderHeight = -50

fullscreen = True
handRadius = 0.1  # radius of each hand
gFieldDirection = {'pitch': math.radians(90), 'yaw': math.radians(0)}
gConst = -9.81  # gravitational field constant
renderRate = 144  # render rate (lower for performance)
collisionTolerance = 0  # global collision tolerance (since computer programs aren't perfect unlike in real life 😭) (must lower when increasing calcRate or decreasing physicsTime; refer to collisionToleranceTables for values obtained through testing)
collisionCalcTolerance = 0.001  # change these 2 tolerance values depending on calcRate (should be larger than collisionTolerance)
jointResolution = 3  # lower to increase performance
pointResolution = 10  # lower to increase performance
theForce = False  # when True, "recalling" points causes them to float slowly to you
jointRadius = 0.015  # radius of all joints
animSpeed = 1 / renderRate  # speed of animations
minRadius = 0.05  # minimum radius of points
maxRadius = 2  # maximum radius of points
GUItypes = {
    'Slider': {'X': None, 'Y': None, 'Z': None},
    'Dial': {'2D': {'XY': None, 'YZ': None, 'XZ': None}, '3D': None},
    'Manual': {'X': None, 'Y': None, 'Z': None}
}

GUItypesScalar = {
    'Slider': {'X': None, 'Y': None, 'Z': None},
    'Manual': {'X': None, 'Y': None, 'Z': None}
}

GUItypesVector = {
    'Slider': None,
    'Dial': {'2D': None, '3D': None},
    'Manual': None
}

tutorialNames = {}
clothNames = {}

globalVars = {
    'gameSpeed': 1,  # game speed factor
    'gField': [gConst * math.cos(gFieldDirection['pitch']) * math.cos(gFieldDirection['yaw']), gConst * math.sin(gFieldDirection['pitch']) * math.cos(gFieldDirection['yaw']), gConst * math.sin(gFieldDirection['yaw'])],  # gravitational field constant about x, y, and z
    'gasDensity': 1.293,  # density of all gases
    'springConst': 1000,  # global spring constant (make negative to break the sandbox)
    'damping': 3,  # global damping constant (reduce as more points are connected to the same object)
    'friction': 1,  # global frictional force coefficient. set to 'sticky' for infinite value.
    'strain': 2,  # global maximum strain before breaking point
    'Tutorials': None,  # only here for summoning tutorials
    'cloths': None  # only here for summoning cloths
}

defaultGlobalVars = {
    'gameSpeed': 1,  # game speed factor
    'gField': [gConst * math.cos(gFieldDirection['pitch']) * math.cos(gFieldDirection['yaw']), gConst * math.sin(gFieldDirection['pitch']) * math.cos(gFieldDirection['yaw']), gConst * math.sin(gFieldDirection['yaw'])],  # gravitational field constant about x, y, and z
    'gasDensity': 0,  # density of all gases
    'springConst': 1000,  # global spring constant (make negative to break the sandbox)
    'damping': 3,  # global damping constant (reduce as more points are connected to the same object)
    'friction': 0.1,  # global frictional force coefficient. set to 'sticky' for infinite value.
    'strain': 10,  # global maximum strain before breaking point
}

globalRanges = {
    'gameSpeed': [3, 0.1],  # [max, min]
    'gField': [15, -15],
    'gasDensity': [10000, 0],
    'springConst': [10000, 0],
    'damping': [2, 0],
    'strain': [50, 5],
    'friction': [2, 0]
}

spriteCreatorVars = {
    'Tutorials': None,
    'Save & Exit': None
}

collisionRectTypes = {
    'Solid': None,
    'Liquid': None
}

mode = 'k'  # controller mode (keyboard/mouse or VR)
calcRate = 300  # physics calculations/second (higher number means more accurate physics but lower performance). Sadly this value cannot exceed 90 for some VR headsets due to their un-overrideable vsync!
physicsTime = calcRate * (1 / globalVars['gameSpeed'])  # inverse of physics speed (cannot be larger than frame-rate or smaller than 60)
touchpad = 16

# controls for keyboard/VR
if mode == 'k':
    controls = {
        'select': 1,
        'recall': 'r',
        'reset': viz.KEY_DELETE,
        'pause': 'p',
        'GUISelector': 'l',
        'dragJoint': 'j',
        'undoJoint': 'u'
    }
    controlsMap = {
        'select': 'left-click',
        'recall': 'r',
        'reset': 'delete',
        'pause': 'p',
        'GUISelector': 'l'
    }
elif mode == 'vr':
    controls = {
        'select': [4, 4],
        'recall': [8, 8],
        'reset': [1, None],
        'pause': [2, None],
        'GUISelector': [None, 1],
        'dragJoint': [None, 2],
        'undoJoint': [2, None]
    }
    controlsMap = {
        'select': 'left/right trigger',
        'recall': 'left/right touchpad',
        'reset': 'left menu',
        'pause': 'left middle-finger trigger',
        'GUISelector': 'right menu'
    }
