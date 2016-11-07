# PepperHHBdx

The goal of this project is to create a module for the Pepper robot which will allow detection and measure of the user's pulse via the video feed frmo the robot's camera.

## Current State

This is a prototype version. It works through a remote conenction to the robot.
To run, launch 'sandbox.py --url ip.of.the.robot'.
Plotting may be broken on linux.
The image buffer copied from the robot might not be the right one.

## TODO

* Switch from remote to embedded prototype version.
    * Running on the robot will allow faster sampling rate for the frequency analysis of the user's face as the image buffer won't need to be copied, which was the bottleneck.
* Switch to a module structure, with a coherent API to be used by other applications.
* Port the code from Python to C++ (performance gain) ?
