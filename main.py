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
import time
import requests

from watchdog.observers import Observer  
from watcher import MyHandler

iftttkey = os.environ['IFTTTKEY']
def turn_onoff(onoff):
    pixel_ring.off()
    pixel_ring.think()
    print("Turned " + onoff)
    requests.post("https://maker.ifttt.com/trigger/turn_" + onoff + "_bedroom_light_request/with/key/"+iftttkey)
    requests.post("https://maker.ifttt.com/trigger/turn_" + onoff + "_bedside_light/with/key/"+iftttkey)

    pixel_ring.off()

clap = 0
wait = 2
flag = 0
pin = 24
exitFlag = False    

def set_leds():
    '''
    Sets pretty colors
    '''
    global clap
    br = 50
    if clap == 1:
        pixel_ring.show([0, br, br, br, 0, 0, 0, 0, 0, 0, 0, 0]*4)
    elif clap == 2:
        pixel_ring.show([0, br, br, br, 0, br, br, br, 0, 0, 0, 0]*4)
    elif clap == 3:
        pixel_ring.show([0, br, br, br, 0, br, br, br, 0, br, br, br,]*4)


def waitForClaps(threadName):
    '''
    Thread waits for a variable number of seconds (2) and then looks at the
    number of claps that have been registered since the start of the sequence.
    This determines wheter the lights should be turned on or off
    '''
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

    args = sys.argv[1:]
    observer = Observer()
    mh = MyHandler(patterns = ["*/clapper_wait.txt"])
    observer.schedule(mh, '/home/pi/')
    observer.start()

    # exit_immediate = 0

    chunk = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    max_threshold = 4000
    corr_threshold = 8e8
    max_value = 0
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
             channels=CHANNELS, 
             rate=RATE, 
             input=True,
             output=True,
             frames_per_buffer=chunk)          
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)

    # Load the reference wave form. All clappiness is determined in relation to this clap
    sample_waveform = np.array(np.load("/home/pi/Documents/clap/pi-clap/golden_clap.npy"), dtype=np.float)
    sw_fft = np.fft.fft(sample_waveform) # Now you're cooking with gas

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
        if max_value > max_threshold and max_value >= last_intensity: 
            as_float = np.array(as_ints, dtype=np.float)

            # Measure loudness
            mag = np.sum(as_float**2)

            #Measure clappiness
            corr = np.abs(np.fft.ifft(np.fft.fft(as_float)*sw_fft))**2/mag
            corr_value = np.max(corr)

            if corr_value > corr_threshold:
                #print("corr: {}, max: {}, claps: {}".format(corr_value, max_value, clap))
                #np.save("hand_clap" + str(c) + ".npy", as_ints) # save 
                #print("saving {}".format(c))
                c += 1

                now = time.time()
                if (now > last_time + 0.2): #better debounce (prevent samples from being stuck in fifo
                    clap += 1
                    set_leds()
                    last_time = now
                    print("Clapped")
            if mh.check_paused():
                # If Clapper has been paused
                print("Clapper Paused for {} minutes".format(mh.data))
                br = 30 # brightness
                pixel_ring.show([0, 0, br, 0]*12) # visually inform pause
                clap = 0
            else:
                # If clapper has not been paused
                if clap == 1 and flag == 0:
                    _thread.start_new_thread( waitForClaps, ("waitThread",) )
                    flag = 1

        if exitFlag:
            sys.exit(0)
        last_intensity = max_value 




if __name__ == '__main__':
    main()
