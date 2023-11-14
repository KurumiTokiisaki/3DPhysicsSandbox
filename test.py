import viz
import vizfx
import vizconnect
import steamvr

view = 'k'

# sets the view to VR mode
if view == 'vr':
    initVR()

def initVR():
    hmd = steamvr.HMD()
    # link the headset to the camera
    viz.link(hmd.getSensor(), viz.MainView)
    print(hmd.getSensor())


# vizconnect.go('keyboard_mouse.py')
viz.setMultiSample(4)
viz.fov(60)
viz.go()

# Create an empty array to put some pigeons in.
pigeons = []
# Go through a loop six times.
for eachnumber in range(6):
    # Each time you go through the loop, create a new pigeon
    newPigeon = viz.addAvatar('vcc_male2.cfg')

    # Place the new pigeon on the x-axis.
    # Each time the script goes through the loop, "eachnumber"
    # will be one larger so the pigeons will fall in a line
    # along the x-axis
    newPigeon.setPosition([eachnumber, 0, 5])

    # Add the new pigeon to the "pigeons" array.
    pigeons.append(newPigeon)

    # If the new pigeon is one of the first two created,
    # make it spin around the x #axis.
    if eachnumber < 2:
        newPigeon.add(vizact.spin(1, 0, 0, 90))
    # If the new pigeon is one of the second two, make it spin around the y axis.
    elif eachnumber >= 2 and eachnumber < 4:
        newPigeon.add(vizact.spin(0, 1, 0, 90))
    # If the new pigeon is one of the remaining two,
    # make it spin around the z axis.
    else:
        newPigeon.add(vizact.spin(0, 0, 1, 90))

# move the view to see all pigeons
viz.MainView.move([2.5, -1.5, 1])
viz.MainView.setEuler(0, 0, 0)
def move():
    if viz.key.isDown('w'):
        viz.MainView.setPosition([viz.MainView.getPosition()[0], viz.MainView.getPosition()[1], viz.MainView.getPosition()[2] + 1/144])
    print(viz.getFrameElapsed())
vizact.ontimer(1/144, move)
