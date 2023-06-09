# Firework Launcher
## About
This is the source code for a firework launcher.

## Hardware
I do not have any guides on building one yourself, and I don't sell them. You can however, design and build one yourself. This is the message it sends for when a firework is launched: `/digital/<pin>/0` (0.5 second delay) `/digital/<pin>/1`. For our launcher, we have a Raspberry Pi connected through serial to an Arduino Mega. The Arduino Mega is setup to have all pins set to high, then the program on the RPI uses those commands to tell the Arduino to set a specific pin to low, then back to high. This also works through IP, and there is also a mode for using the SN74HC595N shift register.

## Images
![Launcher Image 1](/launcher_images/1.jpg "Launcher Image 1")
![Launcher Image 2](/launcher_images/2.jpg "Launcher Image 2")
