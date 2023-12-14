resultF = 0
                    if (self.force[0] * self.multiplier) < 0:
                        resultF += abs(self.force[0] * math.cos(-abs(self.bAngle[2])))
                    if (self.force[1] * self.multiplier) < 0:
                        resultF += abs(self.force[1] * math.sin(-abs(self.bAngle[2])))

                    if self.collisionState == 'y':
                        self.normalForce[0] = -resultF * cos(-abs(self.bAngle[2])) * self.multiplier
                        self.normalForceAfter[1] = -resultF * sin(-abs(self.bAngle[2])) * self.multiplier
                        self.friction[0] = -resultF * sin(-abs(self.bAngle[2])) * self.sf * getSign(self.velocity[0])  # make ff magnitude always constant
                    elif self.collisionState == 'x':
                        self.normalForce[1] = resultF * sin(-abs(self.bAngle[2])) * self.multiplier
                        self.normalForceAfter[0] = resultF * cos(-abs(self.bAngle[2])) * self.multiplier
                        self.friction[1] = -resultF * cos(-abs(self.bAngle[2])) * self.sf * getSign(self.velocity[1])
                    self.friction[2] = -resultF * self.sf * getSign(self.velocity[2])