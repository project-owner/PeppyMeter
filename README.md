## Picasso Edition 2024.02.10

* Moved a screen update functionality to the main event loop
* Removed redundant animation threads
* Redesigned meter folders structure. Introduced naming convention for meter folders.

## Malevich Edition 2024.01.08

* Introduced a parameter which allows to switch random meters programmatically

## Kandinsky Edition 2023.07.30

* Implemented new linear meter movement directions (top-bottom, center-edges, edges-center)
* Implemented knob based linear meter (indicator.type = single)
* Added four new meters of the medium size (chillout, fantasy, relax, steam-punk). The meters use AI generated backgrounds.

## Marc Edition 2023.03.21

* Fixed HTTP output for VU Meter screensaver
* Eliminated lag in multiple VU Meter types running concurrently

## Signac Edition 2022.10.16

* Refactored the algorithms for circular and linear meters 
* The changes allow to create vertical linear and  circular meters
* The circular meter range can be more than 180 degrees now
* Fixed rendering issues for several default meters

## Renoir Edition 2021.07.17

* PeppyMeter can send HTTP requests with volume data to remote web servers
* PeppyMeter can receive HTTP requests and display volume data from those requests
* Added cache for needle sprites. It makes transition from one meter to another much faster. It also fixed the Pygame/SDL memory leak
* Implemented ability to embed PeppyMeter to larger screens
* New configuration parameter enables exit on touch event

## Hiroshige Edition 2021.04.18

* Now the meters to display can be defined as a comma separated names
* It's possible to enable/disable Double Buffering in the configuration file

## Hokusai Edition 2020.11.15

* Added 8 new meters to the large, medium and small groups.
* Added new group 'wide' with resolution 1280x400px. The group has 8 new meters.

## Constable Edition 2020.08.08

* Refactored the named pipe data source functionality. The meters became responsive
* Eliminated the startup delays
* Introduced the smooth buffer which helped to make all indicator animations smooth.
* Improved the meters' performance. Now the meters add about 7% to the CPU usage
* Added file logging

## Hogarth Edition 2020.04.27

* Fixed the issues with the testing data sources (sine, saw etc)

## Durer Edition 2018.01.26

New features:
* Fixed 'Display' output. If disabled it will be possible to output signal to a hardware only. No UI will be displaied in this case.
* Added 'PWM' output. It will allow to use LEDs and gas tubes as a hardware VU Meters.

## El Greco Edition 2018.11.12

New features:
* Added new native resolution 800x480px

## Goya Edition 2018.10.14

New features:
* Modified named pipe data source to leverage peppyalsa ALSA plugin instead of file ALSA plugin

## Vermeer Edition 2018.05.28

New features:
* Added new native resolution 320x240px
* Redesigned volume data extraction from named pipe
* Handling of data input from different audio players through ALSA file plugin
* Implemented support for output to Serial Interafce and I2C interface

## Michelangelo Edition 2016.09.05

PeppyMeter is a software VU Meter written in Python. It was originally developped as the new 'VU Meter' screensaver for [Peppy Player](https://github.com/project-owner/Peppy.doc/wiki). With minor modifications it became a stand-alone application.
PeppyMeter gets audio data from media players (e.g. mpd) via fifo and displays current volume level in a Graphical User Interface
 in a form of traditional VU Meter.
