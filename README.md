rpi-clapper
=======

* Infrastructure based on prior art: https://github.com/nikhiljohn10/pi-clap
* Integrated with IFTTT for control of my room lights (no guarantee to work with yours :) ).
* Google home used with IFTTT for pausing, commanding of device.
* Clap detection based on comparative convolution with "golden_clap" model.
* Uses respeaker 4-mic array.

Clap detection and singnaling program for Raspberry Pi

### H/w Requirements

 * Raspberry Pi
 * Microphone

### Dependencies

**Python**

 * RPi.GPIO
 * pyaudio
 * pixel_ring 
 * gpiozero 
 * py_audio
 * requests
 * watchdog

**Other**

 * Rasbian OS [3]
 * Audio Driver [1],[2],[3].

### Setting up

1. [Download Raspbian OS](http://www.raspberrypi.org/downloads/).
2. [Install Raspbian OS in RPi](http://www.raspberrypi.org/documentation/installation/installing-images/).
3. Install all dependecies
4. Connect the output line to BCM #24 Pin on RPi.
5. Run 'sudo python main.py' command in terminal.
6. Setup google home to send webhook with a single number to enable clapper pausing

2 claps to turn off lights, 3 claps to turn on lights.

### References

 1. https://learn.adafruit.com/usb-audio-cards-with-a-raspberry-pi/instructions
 2. http://computers.tutsplus.com/articles/using-a-usb-audio-device-with-a-raspberry-pi--mac-55876
 3. http://forum.kodi.tv/showthread.php?tid=172072
 4. http://www.raspberrypi.org/documentation/installation/installing-images/
