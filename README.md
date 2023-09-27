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

These commands are seperated by a newline.

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

You can control more than one launcher through the same controller. This makes it so you can also create sequences involving launching fireworks with multiple launchers.

* Notes

You can create notes for each channel that can be displayed in the sequences, making it easier to know which fireworks are which while creating a show. This can also be useful when launching the fireworks manually.

* Sequences

Sequences can be used to create a show. It is organized into steps, with each step having a list of channels that should go off, and a delay between when the fireworks for that step go off, and the next step. You can also stop a sequence between steps, and monitor the sequence as it is going off.

* Profiles

Profiles are used to categorize a firework. When you first add a launcher, there will be 4 profiles: One shot, two shot, three shot, and finale. You can change these profiles for each launcher by going in the settings.

* Multiple clients

I have made it so multiple people can be on the website launching fireworks. With the help of [Socket.IO](https://socket.io), a lot of aspects of the website do not need a page reload to update each client.

* Updating

In the settings menu, you can upload a .tar.gz file with the launcher source code in the root directory of the archive. It will update and restart automatically. This can be useful in case the launcher does not have internet and cannot be easily updated through `git pull`.

* Terminal

In the settings menu, there is an option for terminals where you can get a linux terminal through the website with the help of [tty-share](https://github.com/elisescu/tty-share). Keep in mind that the resolution of the terminal may not be perfect due to tty-share not having the option to scale automatically.
