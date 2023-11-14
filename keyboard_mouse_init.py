import viz
import vizfx
import vizconnect
import vizshape
import math
import time

# viz init functions
viz.setMultiSample(4)
viz.fov(90)
viz.go()
viz.window.setFullscreen()

# disable built-in mouse commands
viz.mouse.setOverride()

# mouse sensitivity
sensitivity = 0.1

# camera speed
minCamSpeed = 0.03
maxCamSpeed = minCamSpeed * 2

# scroll speed (for hand)
scrollSpeed = 0.0001

# hide the cursor
viz.mouse.setCursor(0)


class Main():
	def __init__(self):
		self.frameTime = 0
		self.testAvatar = viz.addAvatar('vcc_male2.cfg').setPosition([0, 0, 5])
		self.camCords = viz.MainView.getPosition()
		self.camAngle = viz.MainView.getEuler()
		self.camVelocity = [0, 0, 0]
		self.hand = vizshape.addSphere(0.1)
		self.handCords = [0, 0, 0]
		# how far hand is from camera initially
		self.handDepth = 1
		# camera speed (local)
		self.minCamSpeed = minCamSpeed
		self.maxCamSpeed = maxCamSpeed
		self.camSpeed = self.minCamSpeed


	def main(self):
		print(viz.window.getFrameRate())
		# call updateView when mouse is moved
		viz.callback(viz.MOUSE_MOVE_EVENT, self.updateView)
		
		self.updateHandPos()
		
		# call keypressed when keyboard is pressed
		if viz.key.anyDown(['w', 'a', 's', 'd', ' ', viz.KEY_SHIFT_L, 'q']):
			self.camCords = viz.MainView.getPosition()
			self.moveCam()


		viz.MainView.setPosition(self.camCords)
		viz.MainView.setEuler(self.camAngle)
		self.hand.setPosition(self.handCords)


	def updateView(self, cords):
		self.camAngle = viz.MainView.getEuler()
		# update facing angle based on change in mouse position
		self.camAngle = [self.camAngle[0] + (cords.dx * sensitivity), self.camAngle[1] - (cords.dy * sensitivity), 0]  # self.camAngle[2]]
	
	def updateHandPos(self):
		vizact.onwheelup(self.addHand)
		vizact.onwheeldown(self.subHand)
		self.handCords[0] = self.camCords[0] + self.handDepth * math.sin(math.radians(self.camAngle[0])) * math.cos(math.radians(self.camAngle[1]))
		self.handCords[1] = self.camCords[1] - self.handDepth * math.sin(math.radians(self.camAngle[1]))
		self.handCords[2] = self.camCords[2] + self.handDepth * math.cos(math.radians(self.camAngle[0])) * math.cos(math.radians(self.camAngle[1]))
	
	def subHand(self):
		self.handDepth -= scrollSpeed
	def addHand(self):
		self.handDepth += scrollSpeed

	def getCamVelocity(self, forwardBackward, leftRight, sinCos):
		# y velocity is independent of x and z velocity
		if sinCos == 'sin':
			return [self.camSpeed * forwardBackward * math.sin(math.radians(self.camAngle[0]) + 45 * leftRight * forwardBackward), self.camVelocity[1], self.camSpeed * forwardBackward * math.cos(math.radians(self.camAngle[0]) + 45 * leftRight * forwardBackward)]
		elif sinCos == 'cos':
			return [self.camSpeed * forwardBackward * math.cos(-math.radians(self.camAngle[0])), self.camVelocity[1], self.camSpeed * leftRight * math.sin(-math.radians(self.camAngle[0]))]

	def moveCam(self):
		if viz.key.isDown('w'):
			f = 1
		else:
			f = 0
		if viz.key.isDown('a'):
			l = -1
		else:
			l = 0
		if viz.key.isDown('s'):
			b = -1
		else:
			b = 0
		if viz.key.isDown('d'):
			r = 1
		else:
			r = 0
		if viz.key.isDown(' '):
			u = 1
		else:
			u = 0
		if viz.key.isDown(viz.KEY_SHIFT_L):
			d = -1
		else:
			d = 0

		if viz.key.isDown('q'):
			self.camSpeed = self.maxCamSpeed
		else:
			self.camSpeed = self.minCamSpeed

		# change movement based on facing angle
		if viz.key.isDown('w'):
				self.camVelocity = self.getCamVelocity(f + b, l + r, 'sin')  # camSpeed * (f + b) * math.sin(math.radians(self.camAngle[0]) + 45 * (l + r)), camSpeed * (u + d), camSpeed * (f + b) * math.cos(math.radians(self.camAngle[0]) + 45 * (l + r))]
				if viz.key.isDown('s'):
					self.camVelocity = self.getCamVelocity(l + r, f + b, 'cos')  # [camSpeed * (l + r) * math.cos(-math.radians(self.camAngle[0])), camSpeed * (u + d), camSpeed * (l + r) * math.sin(-math.radians(self.camAngle[0]))]
		elif viz.key.isDown('s'):
			self.camVelocity = self.getCamVelocity(f + b, l + r, 'sin')  # [camSpeed * (f + b) * math.sin(math.radians(self.camAngle[0]) - 45 * (l + r)), camSpeed * (u + d), camSpeed * (f + b) * math.cos(math.radians(self.camAngle[0]) -  45 * (l + r))]
		elif viz.key.isDown('a') or viz.key.isDown('d'):
			self.camVelocity = self.getCamVelocity(l + r, l + r, 'cos')  # [camSpeed * (l + r) * math.cos(-math.radians(self.camAngle[0])), camSpeed * (u + d), camSpeed * (l + r) * math.sin(-math.radians(self.camAngle[0]))]
		else:
			self.camVelocity = [0, self.camVelocity[1], 0]
		# x and z velocities must be 0 when there is no lateral camera movement or else other values will be affected
		self.camVelocity[1] = self.camSpeed * (u + d)
		
		# add camera speed to camera cords
		self.camCords = [self.camCords[0] + self.camVelocity[0], self.camCords[1] + self.camVelocity[1], self.camCords[2] + self.camVelocity[2]]

game = Main()
# call main 165 times each second
vizact.ontimer(1 / 165, game.main)
