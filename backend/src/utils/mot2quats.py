# For OpenSim support
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

import math, os, sys, getopt, numpy
import opensim as osim
import csv
import numpy as np
import quaternion

def saveOutputCSV(outputPath, times, outputNames, outputData):
    file = open(outputPath, "w", newline='')
    writer = csv.writer(file)
    header = []

    for i in range(len(times)):
        row = []

        if i == 0: # Write header
            header.append("time")
            for label in outputNames:
                header.append(label)
            writer.writerow(header)

        row.append(str(times[i]))
        for data in outputData[i]:
            row.append(str(data))
        writer.writerow(row)

    file.close()

def saveMotionCSV(outputPath, bodyNames, times, poseTrajectories, rotationsOnly):
    file = open(outputPath, "w", newline='')
    writer = csv.writer(file)
    header = []

    lastBodyPoses = []
    for i in range(len(times)):
        row = []  # Row is a list of strings

        if i == 0:
            header.append("time")
        row.append(str(times[i]))
        bodyPoses = poseTrajectories[i]
        for body in range(len(bodyPoses)):
            if i == 0: # Add header info
                lastBodyPoses.append(np.quaternion())
                if rotationsOnly == False:
                    header.append(bodyNames[body] + "_x")
                    header.append(bodyNames[body] + "_y")
                    header.append(bodyNames[body] + "_z")
                header.append(bodyNames[body] + "_qw")
                header.append(bodyNames[body] + "_qx")
                header.append(bodyNames[body] + "_qy")
                header.append(bodyNames[body] + "_qz")

            # Add position
            if rotationsOnly == False:
                row.append(str(bodyPoses[body][0][0]))
                row.append(str(bodyPoses[body][0][1]))
                row.append(str(bodyPoses[body][0][2]))

            # Add rotation as quaternion
            # Check Euclidean distance with previous timestep and select antipodal quaternion that minimizes the distance
            # Better continuity of the orientation trajectory makes learning easier
            lastQuat = lastBodyPoses[body]
            currentQuat = bodyPoses[body][1]
            testA = lastQuat.w
            testW = currentQuat.w
            negCurrentQuat = -currentQuat
            distQ = math.sqrt(pow(currentQuat.w-lastQuat.w, 2.0) + pow(currentQuat.x-lastQuat.x, 2.0) + pow(currentQuat.y-lastQuat.y, 2.0) + pow(currentQuat.z-lastQuat.z, 2.0))
            negDistQ = math.sqrt(pow(negCurrentQuat.w-lastQuat.w, 2.0) + pow(negCurrentQuat.x-lastQuat.x, 2.0) + pow(negCurrentQuat.y-lastQuat.y, 2.0) + pow(negCurrentQuat.z-lastQuat.z, 2.0))
            chosenQuat = currentQuat
            if negDistQ < distQ:
                chosenQuat = negCurrentQuat

            lastBodyPoses[body] = chosenQuat # Store the chosen quaternion this timestep to compare next frame

            row.append(str(chosenQuat.w))
            row.append(str(chosenQuat.x))
            row.append(str(chosenQuat.y))
            row.append(str(chosenQuat.z))

        if i == 0: # Write header before 1st timestamp data
            writer.writerow(header)
        writer.writerow(row)

    file.close()

def mot2quats(motionPath, outputPath, jointParents, modelPath, muscleNames, optionsDict):
    """
    Convert OpenSim motion file to quaternion trajectories.
    
    Args:
        motionPath: Path to .mot file
        outputPath: Output path (can be None)
        jointParents: Dictionary of joint parent relationships
        modelPath: Path to OpenSim model
        muscleNames: Set of muscle names
        optionsDict: Configuration options
    
    Returns:
        Tuple of (motion_name, (body_names, times, pose_trajectories))
    """
    colorama_init()

    print(f"Input OpenSim motion path set to: {motionPath}")
    print(f"Input OpenSim model path set to: {modelPath}")
    model = osim.Model(modelPath)
    model.initSystem()

    motion = osim.Storage(motionPath)

    activationStorage = None
    if optionsDict.get("activationSTO", False) == True:
        stoPath = os.path.splitext(motionPath)[0] + "_StaticOptimization_activation.sto"
        activationStorage = osim.Storage(stoPath)
    else:
        print("Activations are in .mot file.")

    if motion.isInDegrees() == True:
        if optionsDict.get("columnsInDegrees"):
            print("Convert given degree data columns to radians.")
            for dof in optionsDict["columnsInDegrees"]:
                print(f"Convert data {dof} to radians.")
                dofIndex = motion.getStateIndex(dof)
                motion.multiplyColumn(dofIndex, math.pi/180.0) # Convert to radians.
            # Edit storage so angles are in radians.
            motion.setInDegrees(False)
        else:
            print(f"{Fore.LIGHTYELLOW_EX}Warning: Motion set is in degrees. Provide columnsInDegrees list to convert. Radians are required.{Style.RESET_ALL}")
            exit(-1)
    else:
        print("Data set is in radians already. No need to convert.")

    motionName = os.path.splitext(os.path.basename(motionPath))[0]
    print (f"Motion name: {motionName}")

    # Results  states in motionTrajectory are in SimTK:Stage:Instance
    motionTrajectory = osim.StatesTrajectory.createFromStatesStorage(model, motion, True, True)
    print("Trajectory size: ", motionTrajectory.getSize(), " is compatible: ", motionTrajectory.isCompatibleWith(model))
    motionState = motionTrajectory.get(0)
    model.realizePosition(motionState) # Need to do this to query positions.

    jointList = model.getJointList()  # Get the Model's BodyList
    jointIter = jointList.begin()  # Start the iterator at the beginning of the list

    bodyList = model.getBodyList()
    bodyIter = bodyList.begin()

    assert(model.getNumBodies() == model.getNumJoints())

    workingBodyDict = dict()
    bodyNames= []
    workingBodyList = []
    while jointIter != jointList.end(): # Stay in the loop until the iterator reaches the end of the list
        workingBodyList.append((bodyIter.getName(), bodyIter.deref(), jointIter.deref()))
        workingBodyDict[bodyIter.getName()] = (bodyIter.deref(), jointIter.deref())
        bodyNames.append(bodyIter.getName())
        jointIter.next()
        bodyIter.next()

    poseTrajectories = []
    times = []

    print("Saving out motion frames...")
    for i in range(motionTrajectory.getSize()):
        motionState = motionTrajectory.get(i)
        model.realizePosition(motionState)
        times.append(motionState.getTime())

        # Loop through bodies in model.
        bodyPoses = []
        for (name, body, joint) in workingBodyList:
            positionGround = body.getPositionInGround(motionState)
            rotationGround = body.getRotationInGround(motionState)

            # Convert the OpenSim quaternion to the numpy quaternion which has more useful attributes.
            localPosition = positionGround
            bodyQuat = rotationGround.convertRotationToQuaternion()
            localRotation = np.quaternion(bodyQuat.get(0), bodyQuat.get(1), bodyQuat.get(2), bodyQuat.get(3))

            if "motionFormat" in optionsDict:
                if optionsDict["motionFormat"] == "localRotationsOnly":
                    # Find parent of body (skip if jointParents is None or empty)
                    if jointParents and name in jointParents:
                        parentName = jointParents[name]
                        if parentName != "ground" and parentName in workingBodyDict:
                            (parentBody, parentJoint) = workingBodyDict[parentName]
                            parentRotationGround = parentBody.getRotationInGround(motionState)
                            parentPosition = parentBody.getPositionInGround(motionState)
                            parentQuat = parentRotationGround.convertRotationToQuaternion()
                            parentRotation = np.quaternion(parentQuat.get(0), parentQuat.get(1), parentQuat.get(2), parentQuat.get(3))
                            localRotation = parentRotation.conjugate() * localRotation
                            localPosition[0] = positionGround[0] - parentPosition[0]
                            localPosition[1] = positionGround[1] - parentPosition[1]
                            localPosition[2] = positionGround[2] - parentPosition[2]
                else:
                    print(f"{Fore.LIGHTRED_EX}Error: Motion format is not recognized..{Style.RESET_ALL}")
                    quit(-1)
            else:
                print(f"{Fore.LIGHTRED_EX}Error: No valid option localRotations for motion file set..{Style.RESET_ALL}")
                quit(-1)

            if math.isnan(localRotation.w) or math.isnan(localRotation.x) or math.isnan(localRotation.y) or math.isnan(localRotation.z):
                localRotation = np.quaternion(1.0, 0.0, 0.0, 0.0) # Make identity
            bodyPoses.append((localPosition, localRotation))
        poseTrajectories.append(bodyPoses)

    if outputPath != None:
        output_dir = optionsDict.get("outputFolder", "./Outputs")
        os.makedirs(output_dir, exist_ok=True)
        saveMotionCSV(output_dir + "/" + motionName + "_motion.csv", bodyNames, times, poseTrajectories, True)

    return motionName, (bodyNames, times, poseTrajectories)

def main(argv):
    print(f"OpenSim version: {osim.GetVersionAndDate()}")

    sessionPath=""
    modelPath = "./Model/LaiArnoldModified2017_poly_withArms_weldHand_scaled_adjusted.osim"
    motionPath = "./Motions/kinematics_activations_left_leg_squat_0.mot"
    inputPath = sessionPath + motionPath
    outputPath = os.path.splitext(inputPath)[0]
    muscleNames = {} # Empty set
    optionsDict = dict()

    optionsDict["localRotations"] = True
    optionsDict["outputFolder"] = "./Outputs"
    optionsDict["columnsInDegrees"] = [
        "pelvis_tilt", "pelvis_list", "pelvis_rotation",
        "hip_flexion_r", "hip_adduction_r", "hip_rotation_r",
        "knee_angle_r", "knee_angle_r_beta", "ankle_angle_r",
        "subtalar_angle_r", "mtp_angle_r",
        "hip_flexion_l", "hip_adduction_l", "hip_rotation_l",
        "knee_angle_l", "knee_angle_l_beta", "ankle_angle_l",
        "subtalar_angle_l", "mtp_angle_l",
        "lumbar_extension", "lumbar_bending", "lumbar_rotation"
    ]
    optionsDict["motionFormat"] = "localRotationsOnly"

    opts, args = getopt.getopt(argv,"im:o:",["input=","model=","output="])
    for opt, arg in opts:
        if opt == "-h":
            print("mot2quats.py -i <inputFile> -o <outputFile> -m <modelFile>")
            sys.exit()
        elif opt in ("-i", "--input"):
            inputPath = arg
        elif opt in ("-o", "--output"):
            outputPath = arg
        elif opt in ("-m", "--model"):
            modelPath = arg

    (name, bodyPoseTrajectories) = mot2quats(inputPath, outputPath, {}, modelPath, muscleNames, optionsDict)

if __name__ == "__main__":
    main(sys.argv[1:]) 