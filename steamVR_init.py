﻿# base Vizard libraries
import viz
import vizfx
import vizshape
import vizconnect
import steamvr
import vizact
from config import calcRate
# for trig functions
import math


# link HMD to program
hmdConfig = steamvr.HMD()

# camera speed
minCamSpeed = 0.03
maxCamSpeed = minCamSpeed * 2

# degrees of freedom to prevent joystick drift
freedomDegrees = 0.3
yFreedomDegrees = 0.3
# gets the HMD's controllers
controllers = [steamvr.getControllerList()[0], steamvr.getControllerList()[1]]
hmd = hmdConfig.getSensor()


# main class for HMD
class Main:
	def __init__(self):
		# test object for reference
		# self.testAvatar = viz.addAvatar('vcc_male2.cfg').setPosition([0, 0, 5])
		# max speed of camera
		self.camSpeed = minCamSpeed
		# camera variables
		self.apparentCamCords = [0, 0, 0]
		self.camCords = [0, 0, 0]
		self.camAngle = [0, 0, 0]
		self.camVelocity = [0, 0, 0]
		self.handAngle = [[0, 0, 0], [0, 0, 0]]
		
		self.hmdPos = hmd.getPosition()
		# controller sprites to render
		self.hand = [Point('l'), Point('r')]
		

	def main(self):
		# gets position of HMD IRL
		self.hmdPos = hmd.getPosition()
		self.moveCam()
		self.updateHMD()
		
		
		viz.MainView.setEuler(self.camAngle)
		viz.MainView.setPosition(self.camCords)
		for c in range(2):
			self.hand[c].sphere.setPosition(self.hand[c].cords)
			self.hand[c].sphere.setEuler(self.handAngle[c])
		

	# set controller position relative to camera position
	def updateHMD(self):
		self.camAngle = hmd.getEuler()
		
		for c in range(2):
			self.hand[c].cords = [controllers[c].getPosition()[0] + self.apparentCamCords[0], controllers[c].getPosition()[1] + self.apparentCamCords[1], controllers[c].getPosition()[2] + self.apparentCamCords[2]]
			self.handAngle[c] = controllers[c].getEuler()
	
	
	# move camera depending on joystick position
	def moveCam(self):
		# if right controller's rear finger trigger is pressed, increase the camera's max speed
		if controllers[1].getButtonState() == 2:
			self.camSpeed = maxCamSpeed
		else:
			self.camSpeed = minCamSpeed
		
		# if the left controller's joystick moves outside of its degrees of freedom, move the camera based on current facing angle
		if (abs(controllers[0].getThumbstick()[0]) > freedomDegrees) or (abs(controllers[0].getThumbstick()[1]) > freedomDegrees):
			self.camVelocity[0] = (controllers[0].getThumbstick()[1] * math.sin(math.radians(self.camAngle[0])) * self.camSpeed) + (controllers[0].getThumbstick()[0] * math.cos(-math.radians(self.camAngle[0])) * self.camSpeed)
			self.camVelocity[2] = (controllers[0].getThumbstick()[1] * math.cos(math.radians(self.camAngle[0])) * self.camSpeed) + (controllers[0].getThumbstick()[0] * math.sin(-math.radians(self.camAngle[0])) * self.camSpeed)
		else:
			self.camVelocity[0] = 0
			self.camVelocity[2] = 0

		# right controller's degrees of freedom are different to the left controller's, hence yFreedomDegrees
		if abs(controllers[1].getThumbstick()[1]) > yFreedomDegrees:
			self.camVelocity[1] = controllers[1].getThumbstick()[1] * self.camSpeed
		else:
			self.camVelocity[1] = 0
		
		# change camera coordinates depending on velocity and current position
		for c in range(3):
			# adds velocity to static position of camera
			self.apparentCamCords[c] += self.camVelocity[c]
			# adds static position of camera with HMD position IRL
			self.camCords[c] = self.apparentCamCords[c] + hmd.getPosition()[c]


#game = Main()

#vizact.ontimer(1 / 165, game.main)

class Point:
	def __init__(self, lr):
		self.radius = 0.1
		if lr == 'l':
			self.sphere = controllers[0].addModel()
		elif lr == 'r':
			self.sphere = controllers[1].addModel()
		self.cords = [0, 0, 0]
