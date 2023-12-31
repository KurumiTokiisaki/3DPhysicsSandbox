"""
This module was generated by Vizconnect.
Version: 1.05
Generated on: 2023-11-13 13:23:53.659362
"""

import viz
import vizconnect

#################################
# Parent configuration, if any
#################################

def getParentConfiguration():
	#VC: set the parent configuration
	_parent = ''

	#VC: return the parent configuration
	return _parent


#################################
# Pre viz.go() Code
#################################

def preVizGo():
	return True


#################################
# Pre-initialization Code
#################################

def preInit():
	"""Add any code here which should be called after viz.go but before any initializations happen.
	Returned values can be obtained by calling getPreInitResult for this file's vizconnect.Configuration instance."""
	return None


#################################
# Group Code
#################################

def initGroups(initFlag=vizconnect.INIT_INDEPENDENT, initList=None):
	#VC: place any general initialization code here
	rawGroup = vizconnect.getRawGroupDict()

	#VC: initialize a new group
	_name = 'powerwall'
	if vizconnect.isPendingInit('group', _name, initFlag, initList):
		#VC: init the raw object
		if initFlag&vizconnect.INIT_RAW:
			#VC: create the raw object
			rawGroup[_name] = viz.addGroup()
	
		#VC: init the wrapper (DO NOT EDIT)
		if initFlag&vizconnect.INIT_WRAPPERS:
			vizconnect.addGroup(rawGroup[_name], _name, make='Virtual', model='Origin')

	#VC: return values can be modified here
	return None


#################################
# Display Code
#################################

def initDisplays(initFlag=vizconnect.INIT_INDEPENDENT, initList=None):
	#VC: place any general initialization code here
	rawDisplay = vizconnect.getRawDisplayDict()

	#VC: initialize a new display
	_name = 'powerwall'
	if vizconnect.isPendingInit('display', _name, initFlag, initList):
		#VC: init which needs to happen before viz.go
		if initFlag&vizconnect.INIT_PREVIZGO:
			viz.setOption('viz.stereo', viz.QUAD_BUFFER)
			viz.setOption('viz.fullscreen', 1)
	
		#VC: init the raw object
		if initFlag&vizconnect.INIT_RAW:
			#VC: set the window for the display
			_window = viz.MainWindow
			
			#VC: set some parameters
			imageWidth = 2
			imageHeight = 2
			imageRise = 0.1
			originLeft = 1.4142
			originRight = 1.4142
			shiftRight = 0
			shiftUp = 0
			shiftForward = 0
			stereo = viz.QUAD_BUFFER
			swapStereo = False
			
			#VC: create the raw object
			# Create a cave object
			import vizcave
			cave = vizcave.Cave(stereo=stereo)
			
			# get an origin node
			originName = _name
			initGroups(vizconnect.INIT_INDEPENDENT, [originName])# ensure it's been created
			originNode = vizconnect.getGroup(originName).getNode3d()
			
			# get the originLeft angle from the origin measurements
			import math
			aOR = math.pi/4.0
			aAOR = (originRight**2 - originLeft**2 - imageWidth**2)/(-2*originLeft*imageWidth)
			if abs(aAOR) <= 1:
				aOR = math.acos(aAOR)
			
			# convert the angle to front and right shifts
			Sr =-(math.cos(aOR)*originLeft-imageWidth/2.0)
			distanceToFront = math.sin(aOR)*originLeft
			
			# find left/right, up/down, front/back (x,y,z) extent of caves
			R = imageWidth/2.0+Sr+shiftRight# right
			L =-imageWidth/2.0+Sr+shiftRight# left
			U = imageRise+imageHeight+shiftUp# up/top
			D = imageRise+shiftUp# bottom/down
			F = distanceToFront+shiftForward# front
			
			C0 = L, U, F
			C1 = R, U, F
			C2 = L, D, F
			C3 = R, D, F
			
			#Create front wall
			wall = vizcave.Wall(	upperLeft=C0,
									upperRight=C1,
									lowerLeft=C2,
									lowerRight=C3,
									name='Front Wall' )
			
			cave.addWall(wall, window=_window)
			
			_window.setStereoSwap(swapStereo)
			
			#_window.setSize([1, 1])
			
			# We need to pass an object which will be used to update the projection
			# or the display to the view's position, typically this would be the
			# node attached to an avatar's head tracker.
			viewpoint = viz.addGroup()
			cave.setTracker(viewpoint)
			
			# Create a CaveView object for manipulating the entire cave environment.
			# The caveView is a node that can be adjusted to move the entire
			# cave around the virtual environment.
			caveView = vizcave.CaveView(viewpoint, view=_window.getView())
			_window.originLink = viz.link(originNode, caveView, dstFlag=viz.ABS_GLOBAL, srcFlag=viz.ABS_GLOBAL)
			_window.caveView = caveView
			_window.originNode = originNode
			_window.displayNode = cave
			_window.viewpointNode = viewpoint
			
			rawDisplay[_name] = _window
	
		#VC: init the wrapper (DO NOT EDIT)
		if initFlag&vizconnect.INIT_WRAPPERS:
			vizconnect.addDisplay(rawDisplay[_name], _name, make='Generic', model='Powerwall')

	#VC: return values can be modified here
	return None


#################################
# Tracker Code
#################################

def initTrackers(initFlag=vizconnect.INIT_INDEPENDENT, initList=None):
	#VC: place any general initialization code here
	rawTracker = vizconnect.getRawTrackerDict()

	#VC: initialize a new tracker
	_name = 'observer_client_tracker'
	if vizconnect.isPendingInit('tracker', _name, initFlag, initList):
		#VC: init the raw object
		if initFlag&vizconnect.INIT_RAW:
			#VC: set some parameters
			userTracker = viz.USER_HEAD
			observerIndex = 0
			
			#VC: create the raw object
			clientList =  viz.cluster.getObserverClientList()
			if observerIndex < len(clientList):
				client = clientList[observerIndex]
				raw = client.getTracker(userTracker)
				raw.userTracker = userTracker
				raw.client = client
			else:
				viz.logError('Error: observer index {} out of range.'.format(observerIndex))
				raw = viz.addGroup()
				raw.invalidTracker = True
			rawTracker[_name] = raw
	
		#VC: init the wrapper (DO NOT EDIT)
		if initFlag&vizconnect.INIT_WRAPPERS:
			vizconnect.addTracker(rawTracker[_name], _name, make='Virtual', model='Observer Client Tracker')

	#VC: initialize a new tracker
	_name = 'left_hand'
	if vizconnect.isPendingInit('tracker', _name, initFlag, initList):
		#VC: init the raw object
		if initFlag&vizconnect.INIT_RAW:
			#VC: set some parameters
			userTracker = viz.USER_HAND_LEFT
			observerIndex = 1
			
			#VC: create the raw object
			clientList =  viz.cluster.getObserverClientList()
			if observerIndex < len(clientList):
				client = clientList[observerIndex]
				raw = client.getTracker(userTracker)
				raw.userTracker = userTracker
				raw.client = client
			else:
				viz.logError('Error: observer index {} out of range.'.format(observerIndex))
				raw = viz.addGroup()
				raw.invalidTracker = True
			rawTracker[_name] = raw
	
		#VC: init the wrapper (DO NOT EDIT)
		if initFlag&vizconnect.INIT_WRAPPERS:
			vizconnect.addTracker(rawTracker[_name], _name, make='Virtual', model='Observer Client Tracker')

	#VC: initialize a new tracker
	_name = 'right_hand'
	if vizconnect.isPendingInit('tracker', _name, initFlag, initList):
		#VC: init the raw object
		if initFlag&vizconnect.INIT_RAW:
			#VC: set some parameters
			userTracker = viz.USER_HAND_RIGHT
			observerIndex = 2
			
			#VC: create the raw object
			clientList =  viz.cluster.getObserverClientList()
			if observerIndex < len(clientList):
				client = clientList[observerIndex]
				raw = client.getTracker(userTracker)
				raw.userTracker = userTracker
				raw.client = client
			else:
				viz.logError('Error: observer index {} out of range.'.format(observerIndex))
				raw = viz.addGroup()
				raw.invalidTracker = True
			rawTracker[_name] = raw
	
		#VC: init the wrapper (DO NOT EDIT)
		if initFlag&vizconnect.INIT_WRAPPERS:
			vizconnect.addTracker(rawTracker[_name], _name, make='Virtual', model='Observer Client Tracker')

	#VC: initialize a new tracker
	_name = 'keyboard'
	if vizconnect.isPendingInit('tracker', _name, initFlag, initList):
		#VC: init the raw object
		if initFlag&vizconnect.INIT_RAW:
			#VC: set some parameters
			trackerIndex = 4
			speed = 0.5
			debug = False
			
			#VC: create the raw object
			from vizconnect.util.virtual_trackers import Keyboard
			rawTracker[_name] = Keyboard(trackerIndex=trackerIndex, speed=speed, debug=debug)
	
		#VC: init the wrapper (DO NOT EDIT)
		if initFlag&vizconnect.INIT_WRAPPERS:
			vizconnect.addTracker(rawTracker[_name], _name, make='Virtual', model='Keyboard')

	#VC: set the name of the default
	vizconnect.setDefault('tracker', 'observer_client_tracker')

	#VC: return values can be modified here
	return None


#################################
# Input Code
#################################

def initInputs(initFlag=vizconnect.INIT_INDEPENDENT, initList=None):
	#VC: place any general initialization code here
	rawInput = vizconnect.getRawInputDict()

	#VC: return values can be modified here
	return None


#################################
# Event Code
#################################

def initEvents(initFlag=vizconnect.INIT_INDEPENDENT, initList=None):
	#VC: place any general initialization code here
	rawEvent = vizconnect.getRawEventDict()

	#VC: return values can be modified here
	return None


#################################
# Transport Code
#################################

def initTransports(initFlag=vizconnect.INIT_INDEPENDENT, initList=None):
	#VC: place any general initialization code here
	rawTransport = vizconnect.getRawTransportDict()

	#VC: return values can be modified here
	return None


#################################
# Tool Code
#################################

def initTools(initFlag=vizconnect.INIT_INDEPENDENT, initList=None):
	#VC: place any general initialization code here
	rawTool = vizconnect.getRawToolDict()

	#VC: return values can be modified here
	return None


#################################
# Avatar Code
#################################

def initAvatars(initFlag=vizconnect.INIT_INDEPENDENT, initList=None):
	#VC: place any general initialization code here
	rawAvatar = vizconnect.getRawAvatarDict()

	#VC: return values can be modified here
	return None


#################################
# Application Settings
#################################

def initSettings():
	#VC: apply general application settings
	viz.mouse.setTrap(False)
	viz.mouse.setVisible(viz.MOUSE_AUTO_HIDE)
	vizconnect.setMouseTrapToggleKey('')

	#VC: return values can be modified here
	return None


#################################
# Post-initialization Code
#################################

def postInit():
	"""Add any code here which should be called after all of the initialization of this configuration is complete.
	Returned values can be obtained by calling getPostInitResult for this file's vizconnect.Configuration instance."""
	return None


#################################
# Stand alone configuration
#################################

def initInterface():
	#VC: start the interface
	vizconnect.interface.go(__file__,
							live=True,
							openBrowserWindow=True,
							startingInterface=vizconnect.interface.INTERFACE_STARTUP)

	#VC: return values can be modified here
	return None


###############################################

if __name__ == "__main__":
	initInterface()
	viz.add('piazza.osgb')
	viz.add('piazza_animations.osgb')


