#!/usr/bin/env python

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

def speech_segregation():

    while True:
        segregatedFrames = []
        data = None
        # check if any audio inputs have been captured
        try:
            wav = wave.open(Audio.WAVE_OUTPUT_FILENAME, 'r')
            length = wav.getnframes()

            waveData = wav.readframes(length)
            segregatedFrames.append(waveData)
            data = struct.unpack("<{0}h".format(length), waveData)
            wav.close()
            os.remove(Audio.WAVE_OUTPUT_FILENAME)
        except Exception:
            time.sleep(1)
            continue
            
        # do speech segregation to found single channel audio

        # publish segregated channels
        for i in range(0, len(segregatedFrames)):
            dt = datetime.datetime.now()
            timestamp = "%04d%02d%02d%02d%02d%02d" % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

            # tallennetaan eroteltu puhe filuina aikaleiman kanssa jotta uniikit tiedostonimet
            wf = wave.open(os.path.join(getPublishFolder(), "{0}_{1}".format(timestamp, i+1)), 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(Audio.getSampleSize())
            wf.setframerate(Audio.RESPEAKER_RATE)
            wf.writeframes(segregatedFrames[i])
            wf.close()


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
    # listen inputs in separate thread
    process = Process(target=speech_segregation)
    process.start()
    # run main in current thread
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        process.terminate()