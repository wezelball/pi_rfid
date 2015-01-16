#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  rfidtest.py
#  
#  Copyright 2015  <pi@raspberrypi>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

# This application does not need root priveldges to run

# pyserial
from serial import Serial
import time

serialPort = Serial("/dev/ttyAMA0", 9600, timeout=2)

def sendCommand(command):
	"""
	Send command to reader and return resposnse
	"""
	serialPort.write(command)
	time.sleep(0.05)
	reply = serialPort.readline()
	
	return reply
	

def main():
	# Open serial port
	# serialPort = Serial("/dev/ttyAMA0", 9600, timeout=2)
	if (serialPort.isOpen() == False):
		serialPort.open()
		
	# Initialize strings
	outStr = ''
	inStr = ''
	
	# Start with a clean toilet
	serialPort.flushInput()
	serialPort.flushOutput()

	# ********************************************************	
	# Let's ask the version number - a carriage return (\r) is 
	# required for this and many other commands
	outStr = "VER\r"
	inStr = sendCommand(outStr)
	print "Verson number: " + inStr
    
	time.sleep(0.5)
	inStr = ''
    # ********************************************************
    
    # ********************************************************	
    # Measure the operating frequency 
	outStr = "MOF\r"
	inStr = sendCommand(outStr)
    
	print "Operating frequency: " + inStr
    
	time.sleep(0.5)
	inStr = ''
	# ********************************************************	
    
	# ********************************************************	
    # Set the tage type to FDX-B/HDX
	outStr = "ST2\r"
	inStr = sendCommand(outStr)
    
	print "Set tag type tp FDX-B/HDX: " + inStr
    
	time.sleep(0.5)
	inStr = ''
	# ********************************************************	

    # ********************************************************	
	# Set reader active
	#outStr = "SRA\r"
	#inStr = sendCommand(outStr)

	#print "Setting reader active: " + inStr
	
	#time.sleep(0.5)
	#inStr = ''
	# ********************************************************	

	# ********************************************************	
	# Read standard data
	outStr = "RSD\r"
	inStr = sendCommand(outStr)

	print "Read standard data: " + inStr
	
	time.sleep(0.5)
	inStr = ''
	# ********************************************************	


	# ********************************************************	
    # Is a tag present?
	#outStr = "LTG\r"
	#inStr = sendCommand(outStr)
    
	#print "Tag present: " + inStr
	# ********************************************************	
    
	serialPort.close()
			
	return 0
	

if __name__ == '__main__':
	main()

