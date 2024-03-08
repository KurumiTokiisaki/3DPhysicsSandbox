import viz
import math

# border properties
borderSize = [500, 500, 500]  # XYZ
borderHeight = -250  # center point of the border about the Y-axis

mode = 'k'  # controller mode (keyboard/mouse or VR)
fullscreen = True  # ignored in VR
handRadius = 0.1  # radius of each hand
gFieldDirection = {'pitch': math.radians(90), 'yaw': math.radians(0)}  # direction of gravitational field
gConst = -9.81  # gravitational field constant
renderRate = 165  # render rate (lower for performance, should be equal to the display's refresh rate)
collisionCalcTolerance = 0.01  # change these 2 tolerance values depending on calcRate (should be larger than collisionTolerance)
collisionTolerance = collisionCalcTolerance * 0.001  # global collision tolerance
jointResolution = 3  # lower to increase performance
pointResolution = 10  # lower to increase performance
theForce = False  # when True, recalling points causes them to float slowly to you. currently not implemented or used.
jointRadius = 0.015  # radius of all joints
animSpeed = 1 / renderRate  # speed of animations
minRadius = 0.05  # minimum radius of points
maxRadius = 2  # maximum radius of points
minDensity = 1  # minimum density of points/collisionRects
maxDensity = 10000  # maximum density of points/collisionRects

# general GUI types available for only vector quantities
GUItypes = {
    'Slider': {'X': None, 'Y': None, 'Z': None},
    'Dial': {'2D': {'XY': None, 'YZ': None, 'XZ': None}, '3D': None},
    'Manual': {'X': None, 'Y': None, 'Z': None}
}

# general GUI types available for scalar quantities
GUItypesScalar = {
    'Slider': {'X': None, 'Y': None, 'Z': None},
    'Manual': {'X': None, 'Y': None, 'Z': None}
}

# special vector-only GUI types allowing only dial summons
GUItypesVector = {
    'Slider': None,
    'Dial': {'2D': None, '3D': None},
    'Manual': None
}

tutorialNames = {}  # global dict containing all the names of tutorials from tutorialTexts.txt
clothNames = {}  # global dict containing all the names of cloths, which are defined as all points connected via common joints

# global dict containing all the global variables that are available as options for the user to change in the GUI selector
globalVars = {
    'gameSpeed': 1,  # factor for all objects' velocities
    'gField': [gConst * math.cos(gFieldDirection['pitch']) * math.cos(gFieldDirection['yaw']), gConst * math.sin(gFieldDirection['pitch']) * math.cos(gFieldDirection['yaw']), gConst * math.sin(gFieldDirection['yaw'])],  # gravitational field strength about x, y, and z using spherical coordinate geometry
    'gasDensity': 1.293,  # density of the air
    'springConst': 1000,  # global stiffness constant of all joints (make negative to break the sandbox)
    'damping': 3,  # global damping constant of all joints
    'friction': 0.05,  # global surface frictional force coefficient
    'strain': 2,  # global maximum strain before breaking point. currently unimplemented.
    'Tutorials': None,  # only here for summoning tutorials
    'cloths': None  # only here for summoning cloths
}

# global dict containing all the default values for each global variable, so they can undergo a hard reset by the user
defaultGlobalVars = {
    'gameSpeed': 1,
    'gField': [gConst * math.cos(gFieldDirection['pitch']) * math.cos(gFieldDirection['yaw']), gConst * math.sin(gFieldDirection['pitch']) * math.cos(gFieldDirection['yaw']), gConst * math.sin(gFieldDirection['yaw'])],
    'gasDensity': 1.293,
    'springConst': 1000,
    'damping': 3,
    'friction': 0.05,
    'strain': 10,
}

calcRate = 200  # physics calculations/second (higher number means more accurate physics but lower performance). sadly, this value cannot exceed the framerate of HMDs due to their non-overridable vsync setting! a limitation of Vizard is that processes can’t be run faster than the framerate of the Vizard game scene.
physicsTime = calcRate / globalVars['gameSpeed']  # value for time used in all force, acceleration, velocity, and displacement calculations
touchpad = 16  # ID of the VR controller's touchpad according to Vizard

# [max, min] values of all global variables for use in sliders/dials
globalRanges = {
    'gameSpeed': [2 * calcRate / 100, 0.1],  # limit the max. value of 'gameSpeed' linearly scaling with 'calcRate'
    'gField': [15, -15],
    'gasDensity': [10000, 0],
    'springConst': [10000 * (calcRate ** 1.5) / 2000, 0],  # limit the max. value of spring stiffness constant depending on 'calcRate' on a curve
    'damping': [2, 0],
    'strain': [50, 5],
    'friction': [1, 0]
}

# display these in the GUI selector when it’s summoned in 'spriteCreator.py'
spriteCreatorVars = {
    'Tutorials': None,
    'Save & Exit': None
}

# display these in the GUI selector when a collisionRect's type is to be changed by the user in 'spriteCreator.py'
collisionRectTypes = {
    'Solid': None,
    'Liquid': None
}

# controls for keyboard/VR
if mode == 'k':
    # controls that Vizard understands for keyboard/mouse
    controls = {
        'select': 1,
        'recall': 'r',
        'reset': viz.KEY_DELETE,
        'pause': 'p',
        'GUISelector': 'l',
        'dragJoint': 'j',
        'undoJoint': 'u'
    }
    # controls to display to the user in tutorial GUIs so that they know what to press for specific actions
    controlsMap = {
        'movement': 'W/A/S/D',
        'select': 'left-click',
        'recall': 'r',
        'reset': 'delete',
        'pause': 'p',
        'GUISelector': 'l',
        'dragJoint': 'j',
        'undoJoint': 'u'
    }

elif mode == 'vr':
    # controls that Vizard understands for an HMD's [leftController, rightController]
    controls = {
        'select': [4, 4],
        'recall': [8, 8],
        'reset': [1, None],
        'pause': [2, None],
        'GUISelector': [None, 1],
        'dragJoint': [None, 2],
        'undoJoint': [2, None]
    }
    # controls to display to the user in tutorial GUIs so that they know what to press for specific actions
    controlsMap = {
        'movement': 'joysticks',
        'select': 'left/right trigger',
        'recall': 'left/right touchpad',
        'reset': 'left menu',
        'pause': 'left middle-finger trigger',
        'GUISelector': 'right menu',
        'dragJoint': 'right middle-finger trigger',
        'undoJoint': 'left middle-finger trigger'
    }
