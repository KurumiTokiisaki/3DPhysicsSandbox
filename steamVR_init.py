import viz
import vizfx
import vizconnect
import steamvr

viz.setMultiSample(4)
viz.fov(90)
viz.go()

hmdList = steamvr.getExtension()
controllerList = steamvr.getControllerList()
print(hmdList)
print(controllerList)
