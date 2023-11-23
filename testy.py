import math


def edgeBounce(cIdx, oldCords, velocity, angle, trig):
    if trig == 'cos':
        if angle < 0:
            return oldCords[cIdx[0]] + (velocity[cIdx[1]] * math.cos(angle)) - (velocity[cIdx[0]] * math.sin(angle)), oldCords[cIdx[1]] - (velocity[cIdx[0]] * math.cos(angle)) + (velocity[cIdx[1]] * math.cos(angle))
        elif angle > 0:
            return oldCords[cIdx[0]] - (velocity[cIdx[1]] * math.cos(angle)) + (velocity[cIdx[0]] * math.sin(angle)), oldCords[cIdx[1]] + (velocity[cIdx[0]] * math.cos(-angle)) + (velocity[cIdx[1]] * math.cos(-angle))
    elif trig == 'sin':
        if angle < 0:
            return oldCords[cIdx[0]] + (velocity[cIdx[1]] * math.sin(angle)) - (velocity[cIdx[0]] * math.sin(angle)), oldCords[cIdx[1]] - (velocity[cIdx[0]] * math.sin(angle)) + (velocity[cIdx[1]] * math.cos(angle))
        elif angle > 0:
            return oldCords[cIdx[0]] - (velocity[cIdx[1]] * math.sin(-angle)) - (velocity[cIdx[0]] * math.sin(-angle)), oldCords[cIdx[1]] - (velocity[cIdx[0]] * math.sin(angle)) + (velocity[cIdx[1]] * math.cos(angle))
