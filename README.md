# pi_rfid
RFID test code for the Raspberry Pi model B+

To set up the serial port for use, the following has to be done:

	Disable Serial Port Login
		To enable the serial port for your own use you need to disable login on the port. There are two files that need 		to be edited:

		The first and main one is /etc/inittab

		This file has the command to enable the login prompt and this needs to be disabled. Edit the file and move to 			the end of the file. You will see a line similar to

		T0:23:respawn:/sbin/getty -L ttyAMA0 115200 vt100

		Disable it by adding a # character to the beginning. Save the file.

		#T0:23:respawn:/sbin/getty -L ttyAMA0 115200 vt100
		
	Disable Bootup Messages to Serial Port
		When the Raspberry Pi boots up, all the bootup information is sent to the serial port. Disabling this bootup 				information is optional and you may want to leave this enabled as it is sometimes useful to see what is 					happening at bootup. If you have a device connected (i.e. Arduino) at bootup, it will receive this information 		over the serial port, so it is up to you to decide whether this is a problem or not.

		You can disable it by editing the file /boot/cmdline.txt

		The contents of the file look like this

		dwc_otg.lpm_enable=0 console=ttyAMA0,115200 kgdboc=ttyAMA0,115200 console=tty1 root=/dev/mmcblk0p2 rootfstype				=ext4 elevator=deadline rootwait

		Remove all references to ttyAMA0 (which is the name of the serial port). The file will now look like this

		dwc_otg.lpm_enable=0 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline rootwait
		
	Testing With Minicom
		A great way to test out the serial port is to use the minicom program. If you dont have this installed run

		sudo apt-get install minicom

		Connect your PC to the Raspberry Pi serial port using an appropriate serial port adapter and wiring, then open 		Putty or a similar serial terminal program on PC side. Setup a connection using the serial port at 9600 baud.

		Now run up minicom on the Raspberry Pi using

		minicom -b 9600 -o -D /dev/ttyAMA0
		
The above instructions copied from http://www.hobbytronics.co.uk/raspberry-pi-serial-port


	
	
