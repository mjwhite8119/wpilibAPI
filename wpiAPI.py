#!/usr/bin/env python3
#
# This is a NetworkTables client (eg, the DriverStation/coprocessor side).
# You need to tell it the IP address of the NetworkTables server (the
# robot or simulator).
#
# This shows how to use a listener to listen for all changes in NetworkTables
# values, which prints out all changes. Note that the keys are full paths, and
# not just individual key values.

#
# Make sure to have CoppeliaSim running, with followig scene loaded:
#
# Romi.ttt
#
# Do not launch simulation, then run this script
# Run using python3 wpiAPI.py

import sys
import time
from networktables import NetworkTables

# To see messages from networktables, you must setup logging
import logging
import math

from zmqRemoteApi import RemoteAPIClient

print('Program started')
logging.basicConfig(level=logging.DEBUG)

# Connect to Network Tables
ip = "localhost"
NetworkTables.initialize(server=ip)

# Setup constants
X=0
Y=1
HEADING=0

# Connect to CoppeliaSim
client = RemoteAPIClient()
sim = client.getObject('sim')

executedMovId = 'notReady'

# Get the child script handle
targetModel = '/RomiBase'
romiBase = sim.getObject(targetModel)
scriptHandle = sim.getScript(sim.scripttype_childscript,romiBase)

stringSignalName = targetModel + '_executedMovId'

def waitForMovementExecuted(id_):
    global executedMovId, stringSignalName
    while executedMovId != id_:
        s = sim.getStringSignal(stringSignalName)
        executedMovId = s

def getPose():
    position = sim.getObjectPosition(romiBase, -1)
    orientation = sim.getObjectOrientation(romiBase, -1)
    return [position[0], position[1], orientation[2]]

def getTrajectory():
    linear_vel, angular_vel = sim.getObjectVelocity(romiBase)
    return [linear_vel[0], linear_vel[1], angular_vel[0]]

# Set-up some movement variables:
leftVel = 0
rightVel = 0

# Connect to Network Tables
sd = NetworkTables.getTable("/Shuffleboard/Drivetrain")
left_auto_value = sd.getAutoUpdateValue("Left Volts", 0)
right_auto_value = sd.getAutoUpdateValue("Right Volts", 0)

# Start simulation:
sim.startSimulation()

# Wait until ready:
waitForMovementExecuted('ready')

while True:
    leftVolts = left_auto_value.value
    rightVolts = right_auto_value.value
    if (leftVolts > 0.01 or rightVolts > 0.01):
        print(leftVolts, ":", rightVolts)
    movementData = {
        'id': 'drivetrain',
        'leftVolts': 10,
        'rightVolts': 10
    }
    sim.callScriptFunction('remoteApi_movementDataFunction',scriptHandle,movementData)

    # Execute movement sequence:
    sim.callScriptFunction('remoteApi_executeMovement',scriptHandle,'drivetrain')

    simulation_time = sim.getSimulationTime()
    
    pose = getPose()
    trajectory = getTrajectory()

    print(pose[X], trajectory[X], simulation_time)

# Wait until above movement sequence finished executing:
waitForMovementExecuted('drivetrain')

sim.stopSimulation()

print('Program ended')    
