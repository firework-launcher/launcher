# Firework Launcher
## About
This is the source code for a firework launcher.

## Hardware
### Serial and IP Launchers
These launchers are controlled using the same protocol of [aRest](https://github.com/marcoschwartz/aREST). If you want to implement this yourself, the only commands it is using, go like this:
```
/digital/<pin>/<state>
```
An example of a command to set pin 2 to LOW, would look something like this:
```
/digital/2/0
```

### Shift Register Launchers
These launchers use the gpioset command to control SN74HC595N shift registers. The GPIO lines that it uses are set in the `shift_register_mgmt.py` file.

SRCLK - 84\
OE - 86\
SER - 85\
SRCLR - 97\
RCLK - 96

The pinout of the chip itself is explained more in the [datasheet](https://www.ti.com/lit/ds/symlink/sn74hc595.pdf).

## Software
These are some features that the website has:

* Multiple launchers

You can control more than one launcher through the same controller. This makes it so you can also create sequences involving launching fireworks with multiple launchers. Through the LFA page, you can also launch fireworks at the same channel for every launcher connected.

* Notes

You can create notes for each channel that can be displayed in the sequences, making it easier to know which fireworks are which while creating a show. This can also be useful when launching the fireworks manually.

* Sequences

Sequences can be used to create a show. It is organized into steps, with each step having a list of channels that should go off, and a delay between when the fireworks for that step go off, and the next step. You can also stop a sequence between steps, and monitor the sequence as it is going off.

* Profiles

Profiles are used to categorize a firework. Right now, the profiles pre-programmed are one to three shot, and finale. Right now, to edit the profiles, you have to change the JSON file in `config/firework_profiles.json` (this file gets generated after running the launcher for the first time). I will probably make a GUI for this in the future.

* Multiple clients

I have made it so multiple people can be on the website launching fireworks. With the help of [Socket.IO](https://socket.io), a lot of aspects of the website do not need a page reload to update each client.

