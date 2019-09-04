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

import click
import google.auth.transport.grpc
import google.auth.transport.requests
import google.oauth2.credentials

from google.assistant.embedded.v1alpha2 import (
    embedded_assistant_pb2,
    embedded_assistant_pb2_grpc
)

try:
    from . import (
        assistant_helpers,
        browser_helpers,
    )
except (SystemError, ImportError):
    import assistant_helpers
    import browser_helpers


ASSISTANT_API_ENDPOINT = 'embeddedassistant.googleapis.com'
DEFAULT_GRPC_DEADLINE = 60 * 3 + 5
PLAYING = embedded_assistant_pb2.ScreenOutConfig.PLAYING

import textinput as ti



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


def TurnOnOffLight(assistant, on_off = "off"):
    pixel_ring.off()
    pixel_ring.think()
    print("turn " + on_off + " livingroom lights")
    response_text, response_html = assistant.assist(text_query="turn " + on_off + " bedroom lights")
    #print("RES: {} ... {}".format(response_text, response_html))
    if assistant.display and response_html:
        system_browser = browser_helpers.system_browser
        system_browser.display(response_html)
    if response_text:
        click.echo('<@assistant> %s' % response_text)
    print("Light toggled")
    pixel_ring.off()


def waitForClaps(threadName, assistant):
    global clap
    global flag
    global wait
    global exitFlag
    global pin
    print ("Waiting for more claps")
    sleep(wait)
    if clap == 2:
        print ("Two claps")
        TurnOnOffLight(assistant)
    if clap == 3:
        print ("Three claps")
        TurnOnOffLight(assistant, "on")
    clap = 0
    flag = 0
    pixel_ring.off()



@click.command()
@click.option('--api-endpoint', default=ASSISTANT_API_ENDPOINT,
              metavar='<api endpoint>', show_default=True,
              help='Address of Google Assistant API service.')
@click.option('--credentials',
              metavar='<credentials>', show_default=True,
              default=os.path.join(click.get_app_dir('google-oauthlib-tool'),
                                   'credentials.json'),
              help='Path to read OAuth2 credentials.')
@click.option('--device-model-id',
              metavar='<device model id>',
              required=True,
              help=(('Unique device model identifier, '
                     'if not specifed, it is read from --device-config')))
@click.option('--device-id',
              metavar='<device id>',
              required=True,
              help=(('Unique registered device instance identifier, '
                     'if not specified, it is read from --device-config, '
                     'if no device_config found: a new device is registered '
                     'using a unique id and a new device config is saved')))
@click.option('--lang', show_default=True,
              metavar='<language code>',
              default='en-US',
              help='Language code of the Assistant')
@click.option('--display', is_flag=True, default=False,
              help='Enable visual display of Assistant responses in HTML.')
@click.option('--verbose', '-v', is_flag=True, default=False,
              help='Verbose logging.')
@click.option('--grpc-deadline', default=DEFAULT_GRPC_DEADLINE,
              metavar='<grpc deadline>', show_default=True,
              help='gRPC deadline in seconds')

def main(api_endpoint, credentials,
         device_model_id, device_id, lang, display, verbose,
         grpc_deadline, *args, **kwargs):
    global clap
    global flag
    global pin


    ######################################
    # Setup Google assistant
    ######################################
    exit_immediate = 0
    print("argc = {}".format(len(sys.argv)))

    if (len(sys.argv) >= 6):
        query_input = sys.argv[5]
        exit_immediate = 1
        click.echo('<you> %s' % query_input)

    # Setup logging.
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    # Load OAuth 2.0 credentials.
    try:
        with open(credentials, 'r') as f:
            credentials = google.oauth2.credentials.Credentials(token=None,
                                                                **json.load(f))
            http_request = google.auth.transport.requests.Request()
            credentials.refresh(http_request)
    except Exception as e:
        logging.error('Error loading credentials: %s', e)
        logging.error('Run google-oauthlib-tool to initialize '
                      'new OAuth 2.0 credentials.')
        return

    # Create an authorized gRPC channel.
    grpc_channel = google.auth.transport.grpc.secure_authorized_channel(
        credentials, http_request, api_endpoint)
    logging.info('Connecting to %s', api_endpoint)

    ######################################

    chunk = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    threshold = 20000
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

    sample_waveform = np.array(np.load("/home/pi/Documents/clap/pi-clap/golden_clap.npy"), dtype=np.float)
    sw_fft = np.fft.fft(sample_waveform)


    with ti.SampleTextAssistant(lang, device_model_id, device_id, display,
                             grpc_channel, grpc_deadline) as assistant:
        try:
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
                        _thread.start_new_thread( waitForClaps, ("waitThread", assistant) )
                        flag = 1
                if exitFlag:
                    sys.exit(0)
                last_intensity = max_value 

        except (KeyboardInterrupt, SystemExit):
            print ("\rExiting")
            stream.stop_stream()
            stream.close()
            p.terminate()
            try:
                pixel_ring.off()
                time.sleep(1)
                power.off()
                GPIO.cleanup()
            except:
                print("whoops")



if __name__ == '__main__':
    main()
