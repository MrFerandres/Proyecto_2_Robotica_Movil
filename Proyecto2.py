#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Proyecto 2: Creacion de mapas de rejilla de tamaño dinamico
    Equipo:Fernando Andres Chavez Gavaldon
           Marco Antonio Ramirez Perez
    Codigo modificado de Juan-Pablo Ramirez-Paredes <jpi.ramirez@ugto.mx>
"""

import numpy as np
import time
import math as m
import random
import matplotlib.pyplot as plt
import os
import sim as vrep  # access all the VREP elements
from skimage.draw import line


def q2R(x, y, z, w):
    R = np.zeros((3, 3))
    R[0, 0] = 1 - 2 * (y ** 2 + z ** 2)
    R[0, 1] = 2 * (x * y - z * w)
    R[0, 2] = 2 * (x * z + y * w)
    R[1, 0] = 2 * (x * y + z * w)
    R[1, 1] = 1 - 2 * (x ** 2 + z ** 2)
    R[1, 2] = 2 * (y * z - x * w)
    R[2, 0] = 2 * (x * z - y * w)
    R[2, 1] = 2 * (y * z + x * w)
    R[2, 2] = 1 / 2 * (x ** 2 + y ** 2)
    return R


vrep.simxFinish(-1)  # just in case, close all opened connections
clientID = vrep.simxStart('127.0.0.1', -1, True, True, 5000, 5)  # start a connection
if clientID != -1:
    print('Connected to remote API server')
else:
    print('Not connected to remote API server')
    sys.exit("No connection")

# Getting handles for the motors and robot
err, motorL = vrep.simxGetObjectHandle(clientID, 'Pioneer_p3dx_leftMotor', vrep.simx_opmode_blocking)
err, motorR = vrep.simxGetObjectHandle(clientID, 'Pioneer_p3dx_rightMotor', vrep.simx_opmode_blocking)
err, robot = vrep.simxGetObjectHandle(clientID, 'Pioneer_p3dx', vrep.simx_opmode_blocking)

# Assigning handles to the ultrasonic sensors
usensor = []
for i in range(1, 17):
    err, s = vrep.simxGetObjectHandle(clientID, 'Pioneer_p3dx_ultrasonicSensor' + str(i), vrep.simx_opmode_blocking)
    usensor.append(s)

# Sensor initialization
for i in range(16):
    err, state, point, detectedObj, detectedSurfNormVec = vrep.simxReadProximitySensor(clientID, usensor[i],
                                                                                       vrep.simx_opmode_streaming)

ret, carpos = vrep.simxGetObjectPosition(clientID, robot, -1, vrep.simx_opmode_streaming)
ret, carrot = vrep.simxGetObjectOrientation(clientID, robot, -1, vrep.simx_opmode_streaming)

"""
Kv = 0.5
Kh = 2.5
xd = 3
yd = 3
hd = 0
r = 0.1
L = 0.2
errp = 10
"""

tam = 50

if os.path.exists('map.txt'):
    print('Map found. Loading...')
    occgrid = np.loadtxt('map.txt')
    tocc = 1.0 * (occgrid > 0.5)
    occgrid[occgrid > 0.5] = 0
else:
    print('Creating new map')
    occgrid = 0.5 * np.ones((tam, tam))
    tocc = np.zeros((tam, tam))
t = time.time()

initt = t
niter = 0
while time.time() - t < 20:
    ret, carpos = vrep.simxGetObjectPosition(clientID, robot, -1, vrep.simx_opmode_blocking)

    xw = carpos[0]
    yw = carpos[1]
    xr = int(tam / 2) + m.ceil(xw / 0.1)
    yr = int(tam / 2) - m.floor(yw / 0.1)
    if (xr >= tam) or (xr <= 0):
        tam += 20

        occgrid2 = occgrid.copy()
        tocc2 = tocc.copy()
        del (occgrid)
        del (tocc)
        occgrid = 0.5 * np.ones((tam, tam))
        tocc = np.zeros((tam, tam))
        print(occgrid.shape[0], ", ", occgrid.shape[1], "   ", occgrid2.shape[0], ", ", occgrid2.shape[1], '\n')
        print(tocc.shape[0], ", ", tocc.shape[1], "   ", tocc2.shape[0], ", ", tocc2.shape[1], '\n')
        occgrid[10:10 + occgrid2.shape[0], 10:10 + occgrid2.shape[1]] = occgrid2.copy()
        tocc[10:10 + tocc2.shape[0], 10:10 + tocc2.shape[1]] = tocc2.copy()

        # xr = tam
    elif (yr >= tam) or (yr <= 0):
        tam += 20

        occgrid2 = occgrid.copy()
        tocc2 = tocc.copy()
        del (occgrid)
        del (tocc)
        occgrid = 0.5 * np.ones((tam, tam))
        tocc = np.zeros((tam, tam))
        print(occgrid.shape[0], ", ", occgrid.shape[1], "   ", occgrid2.shape[0], ", ", occgrid2.shape[1], "\n")
        print(tocc.shape[0], ", ", tocc.shape[1], "   ", tocc2.shape[0], ", ", tocc2.shape[1], '\n')
        occgrid[10:10 + occgrid2.shape[0], 10:10 + occgrid2.shape[1]] = occgrid2.copy()
        tocc[10:10 + tocc2.shape[0], 10:10 + tocc2.shape[1]] = tocc2.copy()
        # yr = tam
    occgrid[yr - 1, xr - 1] = 0

    ret, carrot = vrep.simxGetObjectOrientation(clientID, robot, -1, vrep.simx_opmode_blocking)

    uread = []
    ustate = []
    upt = []
    for i in range(0, 16, 2):
        err, state, point, detectedObj, detectedSurfNormVec = vrep.simxReadProximitySensor(clientID, usensor[i],
                                                                                           vrep.simx_opmode_buffer)
        ret, objpos = vrep.simxGetObjectPosition(clientID, detectedObj, -1, vrep.simx_opmode_blocking)
        uread.append(np.linalg.norm(point))
        upt.append(point)
        ustate.append(state)
        ret, srot = vrep.simxGetObjectQuaternion(clientID, usensor[i], -1, vrep.simx_opmode_blocking)
        ret, spos = vrep.simxGetObjectPosition(clientID, usensor[i], -1, vrep.simx_opmode_blocking)
        R = q2R(srot[0], srot[1], srot[2], srot[3])
        spos = np.array(spos).reshape((3, 1))
        if i % 2 != 0:
            continue
        if state == True:

            opos = np.array(point).reshape((3, 1))

            pobs = np.matmul(R, opos) + spos
            xs = pobs[0]
            ys = pobs[1]
            xo = int(tam / 2) + m.ceil(xs / 0.1)
            yo = int(tam / 2) - m.floor(ys / 0.1)
            if (xo >= tam) or (xo <= 0):
                tam += 20

                occgrid2 = occgrid.copy()
                tocc2 = tocc.copy()
                del (occgrid)
                del (tocc)
                occgrid = 0.5 * np.ones((tam, tam))
                tocc = np.zeros((tam, tam))
                print(occgrid.shape[0], ", ", occgrid.shape[1], "   ", occgrid2.shape[0], ", ", occgrid2.shape[1], "\n")
                print(tocc.shape[0], ", ", tocc.shape[1], "   ", tocc2.shape[0], ", ", tocc2.shape[1], '\n')
                occgrid[10:10 + occgrid2.shape[0], 10:10 + occgrid2.shape[1]] = occgrid2.copy()
                tocc[10:10 + tocc2.shape[0], 10:10 + tocc2.shape[1]] = tocc2.copy()
                # xo = tam
            elif (yo >= tam) or (yo <= 0):
                tam += 20

                occgrid2 = occgrid.copy()
                tocc2 = tocc.copy()
                del (occgrid)
                del (tocc)
                occgrid = 0.5 * np.ones((tam, tam))
                tocc = np.zeros((tam, tam))
                print(occgrid.shape[0], ", ", occgrid.shape[1], "   ", occgrid2.shape[0], ", ", occgrid2.shape[1], "\n")
                print(tocc.shape[0], ", ", tocc.shape[1], "   ", tocc2.shape[0], ", ", tocc2.shape[1], '\n')
                occgrid[10:10 + occgrid2.shape[0], 10:10 + occgrid2.shape[1]] = occgrid2.copy()
                tocc[10:10 + tocc2.shape[0], 10:10 + tocc2.shape[1]] = tocc2.copy()
                # yo = tam

            rows, cols = line(yr - 1, xr - 1, yo - 1, xo - 1)
            occgrid[rows, cols] = 0
            tocc[yo - 1, xo - 1] = 1

        else:
            # Poner mas profundidad de vision a los sensores
            opos = np.array([0, 0, 1]).reshape((3, 1))

            pobs = np.matmul(R, opos) + spos
            xs = pobs[0]
            ys = pobs[1]
            xo = int(tam / 2) + m.ceil(xs / 0.1)
            yo = int(tam / 2) - m.floor(ys / 0.1)
            if (xo >= tam) or (xo <= 0):
                tam += 20

                occgrid2 = occgrid.copy()
                tocc2 = tocc.copy()
                del (occgrid)
                del (tocc)
                occgrid = 0.5 * np.ones((tam, tam))
                tocc = np.zeros((tam, tam))
                print(occgrid.shape[0], ", ", occgrid.shape[1], "   ", occgrid2.shape[0], ", ", occgrid2.shape[1], "\n")
                print(tocc.shape[0], ", ", tocc.shape[1], "   ", tocc2.shape[0], ", ", tocc2.shape[1], '\n')
                occgrid[10:10 + occgrid2.shape[0], 10:10 + occgrid2.shape[1]] = occgrid2.copy()
                tocc[10:10 + tocc2.shape[0], 10:10 + tocc2.shape[1]] = tocc2.copy()
                # xo = tam
            elif (yo >= tam) or (yo <= 0):
                tam += 20

                occgrid2 = occgrid.copy()
                tocc2 = tocc.copy()
                del (occgrid)
                del (tocc)
                occgrid = 0.5 * np.ones((tam, tam))
                tocc = np.zeros((tam, tam))
                print(occgrid.shape[0], ", ", occgrid.shape[1], "   ", occgrid2.shape[0], ", ", occgrid2.shape[1], "\n")
                print(tocc.shape[0], ", ", tocc.shape[1], "   ", tocc2.shape[0], ", ", tocc2.shape[1], '\n')
                occgrid[10:10 + occgrid2.shape[0], 10:10 + occgrid2.shape[1]] = occgrid2.copy()
                tocc[10:10 + tocc2.shape[0], 10:10 + tocc2.shape[1]] = tocc2.copy()
                # yo = tam
            rows, cols = line(yr - 1, xr - 1, yo - 1, xo - 1)
            occgrid[rows, cols] = 0

    # v = 0.5
    # if v > 0.5:
    #     v = 0.5

    # omega = 0
    # if omega > 2.5:
    #     omega = 2.5
    # elif omega < -2.5:
    #     omega = -2.5

    # if ustate[2] == True and uread[2] < 0.5:
    #     print('Imminent collision at '+str(uread[4]))
    #     omega = -1.5-0.1*random.random()
    #     v = 0.01+0.01*random.random()
    # if ustate[5] == True and uread[5] < 0.5:
    #     print('Imminent collision at '+str(uread[4]))
    #     omega = 1.5+0.1*random.random()
    #     v = 0.01+0.01*random.random()

    # ul = v/r - L*omega/(2*r)
    # ur = v/r + L*omega/(2*r)
"""
    ul = 2.0
    ur = 2.0
    lgains = np.linspace(0,-1,8)
    rgains = np.linspace(-1,0,8)
    for i in range(8):
        if ustate[i]:
            ul = ul + lgains[i]*(1.0 - uread[i])
            ur = ur + rgains[i]*(1.0 - uread[i])
    print('lvel {}   rvel {}'.format(ul, ur))

        #Poner mas velocidad a los motores
    errf = vrep.simxSetJointTargetVelocity(clientID, motorL, ul, vrep.simx_opmode_streaming)
    errf = vrep.simxSetJointTargetVelocity(clientID, motorR, ur, vrep.simx_opmode_streaming)

    niter = niter + 1

print(lgains)
print(rgains)
finalt = time.time()
print('Avg time per iteration ', (finalt-initt)/niter)
"""

plt.imshow(tocc + occgrid)
plt.show()
np.savetxt('map.txt', tocc + occgrid)
errf = vrep.simxSetJointTargetVelocity(clientID, motorL, 0.0, vrep.simx_opmode_streaming)
errf = vrep.simxSetJointTargetVelocity(clientID, motorR, 0.0, vrep.simx_opmode_streaming)
vrep.simxStopSimulation(clientID, vrep.simx_opmode_oneshot)