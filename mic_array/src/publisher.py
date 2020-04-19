#!/usr/bin/env python

import separate
import argparse
import struct
import time, datetime
import os
import rospy
import wave
from audio import Audio
from multiprocessing import Process
from std_msgs.msg import Int16
#ROS_PACKAGE_PATH=/home/osboxes/kandi/src:/opt/ros/melodic/share
def getPublishFolder():
    dirname = '~/speech_output'#os.path.dirname(__file__)
    pubDirName = os.path.join(dirname, 'publish')

    if not os.path.exists(pubDirName):
        os.mkdir(pubDirName)
    
    return pubDirName

def speech_segregation(args):

    while True:
        segregatedFrames = []
        data = None
        # check if any audio inputs have been captured
        try:
            wav = wave.open(Audio.WAVE_OUTPUT_FILENAME, 'r')
            # if file is found, append it to wave_scp with timestamp as key
            dt = datetime.datetime.now()
            timestamp = "%04d%02d%02d%02d%02d%02d" % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
            with open(args.wave_scp, 'a') as scp:
                scp.write("{} {}\n".format(timestamp, Audio.WAVE_OUTPUT_FILENAME))

            separationProcess = Process(target=separate.run, args=args)
            separationProcess.start()
        except Exception:
            time.sleep(1)
            continue
        finally:
            wav.close()


def main():
    pubDOA = rospy.Publisher('DOA', Int16)
    prevRecordingStart = datetime.datetime.now()
    audio = Audio()

    rospy.init_node('speech', anonymous=True)

    rate = rospy.Rate(10) #10 Hz
    
    while not rospy.is_shutdown():
        voiceActive = audio.readVAD()

        if voiceActive:
            # publish direction to ROS topic when voice is active
            direction = Int16(data=audio.readDOA())
            pubDOA.publish(direction)

            # start recording if recording should not already be active based on recording duration
            if (datetime.datetime.now() - prevRecordingStart).total_seconds() >= Audio.RECORD_SECONDS:
                print("Kuuntelu alko")
                # start recording in new process so direction publication can continue without waiting for the recording to end
                recordingProcess = Process(target=audio.record)
                recordingProcess.start()
                prevRecordingStart = datetime.datetime.now()

        rate.sleep()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=
        "Command to run speech separation ROS node"
    )
    parser.add_argument(
        "config", type=str, help="Location of training configure files",
        default="tune/train.yaml")
    parser.add_argument(
        "state_dict", type=str, help="Location of networks state file",
        default="tune/epoch.19.pkl")
    parser.add_argument(
        "wave_scp",
        type=str,
        help="Location of input wave scripts in kaldi format",
        default="wave.scp")
    parser.add_argument(
        "--cuda",
        default=False,
        action="store_true",
        dest="cuda",
        help="If true, inference on GPUs")
    parser.add_argument(
        "--dump-dir",
        type=str,
        default="cache",
        dest="dump_dir",
        help="Location to dump seperated speakers")
    parser.add_argument(
        "--dump-mask",
        default=False,
        action="store_true",
        dest="dump_mask",
        help="If true, dump mask matrix")
    args = parser.parse_args()

    # listen inputs in separate thread
    process = Process(target=speech_segregation, args=args)
    process.start()
    # run main in current thread
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        process.terminate()