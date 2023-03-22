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
HEADING=2

# Set-up some movement variables:
leftVel = 0
rightVel = 0
wheelRadius = 0.035
fieldOffset = 2.5 # CoppeliaSim field origin is in the center

# Connect to CoppeliaSim
client = RemoteAPIClient()
sim = client.getObject('sim')

executedMovId = 'notReady'

# Get the child script handle
targetModel = '/RomiBase'
romiBase = sim.getObject(targetModel)
leftMotor = sim.getObject('/leftMotor')
rightMotor = sim.getObject('/rightMotor')
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

# def getOdometry():
#     result, leftWheel = sim.getObjectFloatParameter(leftMotor, sim.jointfloatparam_velocity)
#     result, rightWheel = sim.getObjectFloatParameter(rightMotor, sim.jointfloatparam_velocity)
#     delta_time = sim.getSimulationTimeStep()
#     thetaL = leftWheel * wheelRadius
#     thetaR = rightWheel * wheelRadius
#     return thetaL, thetaR

def getWheelSpeeds():
    leftWheelSpeed = sim.getJointTargetVelocity(leftMotor) * wheelRadius
    rightWheelSpeed = sim.getJointTargetVelocity(rightMotor) * wheelRadius
    return leftWheelSpeed, rightWheelSpeed

# def getWheelPositions():
#     leftWheelPos = sim.getJointTargetPosition(leftMotor)
#     rightWheelPos = sim.getJointTargetPosition(rightMotor)
#     return leftWheelPos, rightWheelPos

# Connect to Network Tables
sb = NetworkTables.getTable("/Shuffleboard/Drivetrain")
left_auto_value = sb.getAutoUpdateValue("Left Volts", 0)
right_auto_value = sb.getAutoUpdateValue("Right Volts", 0)

# Start simulation:
sim.startSimulation()

# Wait until ready:
waitForMovementExecuted('ready')

while True:
    leftVolts = left_auto_value.value
    rightVolts = right_auto_value.value

    # Setting to 15 represents 0.5 meters per/second
    movementData = {
        'id': 'drivetrain',
        'leftVolts': leftVolts * 3,
        'rightVolts': rightVolts * 3
    }
    sim.callScriptFunction('remoteApi_movementDataFunction',scriptHandle,movementData)

    # Execute movement sequence:
    sim.callScriptFunction('remoteApi_executeMovement',scriptHandle,'drivetrain')

    simulation_time = sim.getSimulationTime()
    
    pose = getPose()
    trajectory = getTrajectory()
    leftWheelSpeed, rightWheelSpeed = getWheelSpeeds()
    # leftWheelPos, rightWheelPos = getWheelPositions()
    # print(pose[X], pose[Y], simulation_time)
    # odometry = getOdometry()

    # Update the Java program. Must have the model bounding box set as follows
    # [Menu bar --> Edit --> Reorient bounding box --> With reference frame of world]
    sb.putNumber("poseX", pose[X] + fieldOffset)
    sb.putNumber("poseY", pose[Y] + fieldOffset)
    sb.putNumber("heading", pose[HEADING])
    sb.putNumber("leftWheelSpeed", leftWheelSpeed)
    sb.putNumber("rightWheelSpeed", rightWheelSpeed)

    if (leftVolts > 0.01 or rightVolts > 0.01):
        print(leftVolts, rightVolts, pose[X], simulation_time)
        # print(pose[X], simulation_time)

# Wait until above movement sequence finished executing:
waitForMovementExecuted('drivetrain')

sim.stopSimulation()

print('Program ended')    
