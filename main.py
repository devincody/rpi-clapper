#!/usr/bin/python

import sys, os
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if not path in sys.path:
    sys.path.insert(1, path)

print("path: {}".format(sys.path))
# LED imports
import time
from pixel_ring import pixel_ring
from gpiozero import LED
import numpy as np
# Initalize LEDS
power = LED(5)
power.on()

pixel_ring.set_brightness(20)
pixel_ring.change_pattern('echo')
pixel_ring.wakeup()


import pyaudio
import _thread
from time import sleep
from array import array
import RPi.GPIO as GPIO

import logging
import json
import time
import requests

iftttkey = os.environ['IFTTTKEY']
def turn_onoff(onoff):
    pixel_ring.off()
    pixel_ring.think()
    print("Turned " + onoff)
    requests.post("https://maker.ifttt.com/trigger/turn_" + onoff + "_bedside_light/with/key/"+iftttkey)
    requests.post("https://maker.ifttt.com/trigger/turn_" + onoff + "_bedroom_light/with/key/"+iftttkey)

    pixel_ring.off()

clap = 0
wait = 2
flag = 0
pin = 24
exitFlag = False    

def set_leds():
    global clap

    br = 50
    if clap == 1:
        pixel_ring.show([0, br, br, br, 0, 0, 0, 0, 0, 0, 0, 0]*4)
    elif clap == 2:
        pixel_ring.show([0, br, br, br, 0, br, br, br, 0, 0, 0, 0]*4)
    elif clap == 3:
        pixel_ring.show([0, br, br, br, 0, br, br, br, 0, br, br, br,]*4)


def waitForClaps(threadName):
    global clap
    global flag
    global wait
    global exitFlag
    global pin
    print ("Waiting for more claps")
    sleep(wait)
    if clap == 2:
        print ("Two claps")
        turn_onoff("off")
    if clap == 3:
        print ("Three claps")
        turn_onoff("on")
    clap = 0
    flag = 0
    pixel_ring.off()

def main():
    global clap
    global flag
    global pin


    exit_immediate = 0
    ######################################

    chunk = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    threshold = 20000
    max_value = 0
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    card_num = 0
    for i in range(numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            nom = p.get_device_info_by_host_api_device_index(0, i).get('name')
            print ("Input Device id ", i, " - ", nom)
            if "seeed" in nom:
                card_num = i
                
    stream = p.open(format=FORMAT,
                    channels=CHANNELS, 
                    input_device_index = card_num,
                    rate=RATE, 
                    input=True,
                    output=True,
                    frames_per_buffer=chunk)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)

    sample_waveform = np.array(np.load("/home/pi/Documents/clap/pi-clap/golden_clap.npy"), dtype=np.float)
    sw_fft = np.fft.fft(sample_waveform)

    print ("Clap detection initialized")
    pixel_ring.off()
    c = 0
    last_intensity = 0
    last_time = time.time()
    while True:
        data = stream.read(chunk)
        as_ints = array('h', data)
        max_value = max(as_ints)
        #print("max: {}, time = {}".format(max_value, time.time())),
        if max_value > 4000 and max_value >= last_intensity: 
            as_float = np.array(as_ints, dtype=np.float)
            mag = np.sum(as_float**2)
            corr = np.abs(np.fft.ifft(np.fft.fft(as_float)*sw_fft))**2/mag
            corr_value = np.max(corr)

            if corr_value > 8e8:
                #print("corr: {}, max: {}, claps: {}".format(corr_value, max_value, clap))
                #np.save("hand_clap" + str(c) + ".npy", as_ints)
                #print("saving {}".format(c))
                c += 1

                #sleep(.5) #debounce
                now = time.time()
                if (now > last_time + 0.2): #better debounce (prevent samples from being stuck in fifo
                    clap += 1
                    set_leds()
                    last_time = now
                    print("Clapped")
            if clap == 1 and flag == 0:
                _thread.start_new_thread( waitForClaps, ("waitThread") )
                flag = 1
        if exitFlag:
            sys.exit(0)
        last_intensity = max_value 




if __name__ == '__main__':
    main()
