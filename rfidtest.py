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
import curses

# ********* GLOBAL ****************
serialPort = Serial("/dev/ttyAMA0", 9600, timeout=2)
# Initialize  curses display
stdscr = curses.initscr()	# initialize display
curses.noecho()				# don't echo keys
curses.cbreak()				# no CR required

def sendCommand(command):
	"""
	Send command to reader and return resposnse
	"""
	serialPort.write(command)
	time.sleep(0.05)
	reply = serialPort.readline()
	
	return reply
	
def getOut():
	"""
	Exit, cleaning up after itself.  Especially important
	with ncurses
	"""
	serialPort.close()
	# exit out of curses cleanly
	curses.nocbreak()
	stdscr.keypad(0)
	curses.echo()
	curses.endwin()
	exit(0)

def main():
	# Open serial port
	if (serialPort.isOpen() == False):
		serialPort.open()
		
	# Initialize strings
	outStr = '' # data sent to reader
	inStr = ''	# data read from reader
	readerActive = False	# state of RF field
	
	# Start with a clean toilet
	serialPort.flushInput()
	serialPort.flushOutput()
	
	# Write the main screen
	stdscr.clear()
	stdscr.addstr(0,0, "Commands")
	stdscr.addstr(2,0, "(0) Report version number")
	stdscr.addstr(3,0, "(1) Measure operating frequency")
	stdscr.addstr(4,0, "(2) Toggle reader status (active/inactive)")
	stdscr.addstr(5,0, "(3) Select tag type")
	stdscr.addstr(6,0, "(4) Locate transdponder tag")
	stdscr.addstr(7,0, "(5) Read standard data")
	stdscr.addstr(8,0, "(6) Read atag data")

	stdscr.addstr(11,0, "(9) Exit program")
	
	# The options dictionary contains a mapping of command numbers
	# to commands.  Command number >= 50 are not user commands
	# but are sent by the application after some preprocessing
	options = { 0: "VER\r",		# firmware version
				1: "MOF\r",		# measure operating frequency
				4: "LTG\r",		# locate transponder
				5: "RSD\r",		# read standard data
				6: "RAT\r",		# read atag data
				50: "SRA\r",	# set reader active
				51: "SRD\r",	# set reader deactive
				52: "ST0\r",	# EM4100 tag selecteced (volatile)
				53: "ST1\r",	# T55xx tag selecteced (volatile)
				54: "ST2\r",	# FDX-B/HDX tag selecteced (volatile)
				55: "ST3\r",	# TIRIS tag selecteced (volatile)
				56: "ST4\r"		# EM4205 tag selecteced (volatile)
				}

	while (True):
		c = stdscr.getch() # read a single character, returns ASCII code
		
		# Convert ASCII code to string, and interpret it
		if c == ord('0'):	# firmware version
			command = 0
			locx = 50
			locy = 2
			screenData = ''
		elif c == ord('1'):	# measure frequency
			command = 1
			locx = 50
			locy = 3
			screenData = ''
		elif c == ord('2'):	# set reader active/deactive
			locx = 50
			locy = 4
			if readerActive == False:	# acticate
				command = 50
				readerActive = True
				screenData = "active"
			else:						# deactivate
				command = 51
				readerActive = False
				screenData = "inactive"
						
		elif c == ord('3'):	# set tag type, requires subwindow menu
			locx = 50
			locy = 5
			
			# Create a sub-window for the tag type
			sub_cornerX = 18
			sub_cornerY = 13
			sub_height = 5
			sub_width = 20
			subwin = curses.newwin(sub_height, sub_width, sub_cornerY, \
				sub_cornerX)
			subwin.addstr(0,0, "(1) - EM4100")
			subwin.addstr(1,0, "(2) - T55xx")
			subwin.addstr(2,0, "(3) - FDX-B/HDX")
			subwin.addstr(3,0, "(4) - TIRIS")
			subwin.addstr(4,0, "(5) - EM4205")
			subwin.refresh()

			# This selection is for the tag type subwindow
			# Note the that the screenData length is 9 characters,
			# not including carriage return.  This is to insure that
			# the data output areas are wiped clean.  This is a real
			# ghetto way of doing this, and must be improved
			c = stdscr.getch()
			if c == ord('1'):
				command = 52
				screenData = "EM4100   "
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
			if c == ord('2'):
				command = 53
				screenData = "T55xx    "
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
			if c == ord('3'):
				command = 54
				screenData = "FDX-B/HDX"
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
			if c == ord('4'):
				command = 55
				screenData = "TIRIS    "
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
			if c == ord('5'):
				command = 56
				screenData = "EM4205   "
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
				
		elif c == ord('4'):	# locate transponder
			command = 4
			locx = 50
			locy = 6
			#screenData = ''
		elif c == ord('5'):	# read standard data
			command = 5
			locx = 50
			locy = 7
			#screenData = ''
		elif c == ord('6'):	# read atag data
			command = 6
			locx = 50
			locy = 8
			screenData = ''			
		elif c == ord('9'):
			# Exit cleanly
			getOut()
			
		# Send command to reader, 
		outStr = options[command]
		# There is a short pause, print WAIT on screen
		stdscr.addstr(0, 50, "WAIT", curses.A_REVERSE)
		# Force screen update NOW
		stdscr.refresh()
		inStr = sendCommand(outStr)
		# Need to check here and modify screenData based on
		# response from reader
		if command == 4 and inStr == "?1\r":
			screenData = "absent"
		elif command == 4 and inStr == "OK\r":
			screenData = "present"
		elif command == 5 and inStr == "?1\r":
			screenData = "none"
		elif command == 5 and inStr <> "?1\r":
			screenData = inStr
		elif command == 6 and inStr <> "?1\r":
			screenData = inStr
		
		# What is actually being printed in the screen
		if screenData == '':
			stdscr.addstr(locy, locx, inStr, curses.A_REVERSE)
		else:
			stdscr.addstr(locy, locx, screenData, curses.A_REVERSE)
		# clear out WAIT status
		stdscr.addstr(0, 50, "    ",)

if __name__ == '__main__':
	# supposed to clean up after itself on exceptions
	curses.wrapper(main()) 

