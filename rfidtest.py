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
import sys, os
from serial import Serial
import time
import curses
import logging	# time for debugging

# ********* GLOBAL ****************
serialPort = Serial("/dev/ttyAMA0", 9600, timeout=2)
# Initialize  curses display
stdscr = curses.initscr()	# initialize display
curses.noecho()				# don't echo keys
curses.cbreak()				# no CR required

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

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

def initLogging(filename):
	# remove the file if it exists
	try:
		os.remove(filename)
	except OSError:
		pass
    	
	global logger
	if logger == None:
		logger = logging.getLogger()
	else:  # wish there was a logger.close()
		for handler in logger.handlers[:]:  # make a copy of the list
			logger.removeHandler(handler)

	logger.setLevel(logging.DEBUG)
	formatter = logging.Formatter(fmt='%(asctime)s: %(message)s', datefmt='%I:%M:%S')

	fh = logging.FileHandler(filename)
	fh.setFormatter(formatter)
	logger.addHandler(fh)


class WindowMaker:
	def __init__(self):
		logging.debug ("Entered WindowMaker constructor")
		self.menu = []

	def showWindow(menu):
		logging.debug ("Entered WindowMaker showWindow method")

		
	def __del__(self):
		logging.debug ("Entered WindowMaker destructor")

def main():

	# Set up logging to file
	#logging.basicConfig(filename = 'debug.log', level=logging.DEBUG)
	#logging.debug("Starting application")

	initLogging('debug.log')

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
	stdscr.addstr(8,0, "(6) Read block (T55xx)")
	stdscr.addstr(9,0, "(7) Write block (T55xx)")

	stdscr.addstr(11,0, "(9) Exit program")
	
	# The options dictionary contains a mapping of command numbers
	# to commands.  Command number >= 50 are not user commands
	# but are sent by the application after some preprocessing
	options = { 0: "VER\r",		# firmware version
				1: "MOF\r",		# measure operating frequency
				4: "LTG\r",		# locate transponder
				5: "RSD\r",		# read standard data
				50: "SRA\r",	# set reader active
				51: "SRD\r",	# set reader deactive
				52: "ST0\r",	# EM4100 tag selecteced (volatile)
				53: "ST1\r",	# T55xx tag selecteced (volatile)
				54: "ST2\r",	# FDX-B/HDX tag selecteced (volatile)
				55: "ST3\r",	# TIRIS tag selecteced (volatile)
				56: "ST4\r",	# EM4205 tag selecteced (volatile)
				57: "RB1\r",	# read block 1 (8 ASCII hex bytes)
				58: "RB2\r",	# read block 2 (8 ASCII hex bytes)
				59: "RB3\r",	# read block 3 (8 ASCII hex bytes)
				60: "RB4\r",	# read block 4 (8 ASCII hex bytes)
				61: "RB5\r",	# read block 5 (8 ASCII hex bytes)
				62: "RB6\r",	# read block 6 (8 ASCII hex bytes)
				63: "RB7\r",	# read block 7 (8 ASCII hex bytes)
				64: "WB1",	# write block 1 (8 ASCII hex bytes)
				65: "WB2",	# write block 2 (8 ASCII hex bytes)
				66: "WB3",	# write block 3 (8 ASCII hex bytes)
				67: "WB4",	# write block 4 (8 ASCII hex bytes)
				68: "WB5",	# write block 5 (8 ASCII hex bytes)
				69: "WB6",	# write block 6 (8 ASCII hex bytes)
				70: "WB7",	# write block 7 (8 ASCII hex bytes)
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
			sub_height = 7
			sub_width = 20
			subwin = curses.newwin(sub_height, sub_width, sub_cornerY, \
				sub_cornerX)
			subwin.box()	# put a box around the window
			subwin.addstr(1,1, "(1) - EM4100")
			subwin.addstr(2,1, "(2) - T55xx")
			subwin.addstr(3,1, "(3) - FDX-B/HDX")
			subwin.addstr(4,1, "(4) - TIRIS")
			subwin.addstr(5,1, "(5) - EM4205")
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
		elif c == ord('6'):	# read block (T55xx)
			command = 6
			locx = 50
			locy = 8
			
			# Create a sub-window for the tag type
			sub_cornerX = 18
			sub_cornerY = 13
			sub_height = 9
			sub_width = 25
			subwin = curses.newwin(sub_height, sub_width, sub_cornerY, \
				sub_cornerX)
			subwin.box()	# put a box around the window
			subwin.addstr(1,1, "(1) - Page 0, Block 1")
			subwin.addstr(2,1, "(2) - Page 0, Block 2")
			subwin.addstr(3,1, "(3) - Page 0, Block 3")
			subwin.addstr(4,1, "(4) - Page 0, Block 4")
			subwin.addstr(5,1, "(5) - Page 0, Block 5")
			subwin.addstr(6,1, "(6) - Page 0, Block 6")
			subwin.addstr(7,1, "(7) - Page 0, Block 7")
			subwin.refresh()

			# This selection is for the tag type subwindow
			# Note the that the screenData length is 9 characters,
			# not including carriage return.  This is to insure that
			# the data output areas are wiped clean.  This is a real
			# ghetto way of doing this, and must be improved
			c = stdscr.getch()
			if c == ord('1'):	# page 0, block 1
				command = 57
				screenData = ""
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
			if c == ord('2'):	# page 0, block 2
				command = 58
				screenData = ""
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
			if c == ord('3'):	# page 0, block 3
				command = 59
				screenData = ""
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
			if c == ord('4'):	# page 0, block 4
				command = 60
				screenData = ""
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
			if c == ord('5'):	# page 0, block 5
				command = 61
				screenData = ""
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
			if c == ord('6'):	# page 0, block 6
				command = 62
				screenData = ""
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
			if c == ord('7'):	# page 0, block 7
				command = 63
				screenData = ""
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
		elif c == ord('7'):	# read block (T55xx)
			command = 7
			locx = 50
			locy = 9
			
			# Create a sub-window for the tag type
			sub_cornerX = 18
			sub_cornerY = 13
			sub_height = 9
			sub_width = 25
			subwin = curses.newwin(sub_height, sub_width, sub_cornerY, \
				sub_cornerX)
			subwin.box()	# put a box around the window
			subwin.addstr(1,1, "(1) - Page 0, Block 1")
			subwin.addstr(2,1, "(2) - Page 0, Block 2")
			subwin.addstr(3,1, "(3) - Page 0, Block 3")
			subwin.addstr(4,1, "(4) - Page 0, Block 4")
			subwin.addstr(5,1, "(5) - Page 0, Block 5")
			subwin.addstr(6,1, "(6) - Page 0, Block 6")
			subwin.addstr(7,1, "(7) - Page 0, Block 7")
			subwin.refresh()

			# This selection is for the tag type subwindow
			# Note the that the screenData length is 9 characters,
			# not including carriage return.  This is to insure that
			# the data output areas are wiped clean.  This is a real
			# ghetto way of doing this, and must be improved
			c = stdscr.getch()
			if c == ord('1'):	# page 0, block 1
				command = 64
				screenData = ""
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
			if c == ord('2'):	# page 0, block 2
				command = 65
				screenData = ""
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
			if c == ord('3'):	# page 0, block 3
				command = 66
				screenData = ""
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
			if c == ord('4'):	# page 0, block 4
				command = 67
				screenData = ""
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
			if c == ord('5'):	# page 0, block 5
				command = 68
				screenData = ""
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
			if c == ord('6'):	# page 0, block 6
				command = 69
				screenData = ""
				del subwin
				stdscr.touchwin()
				stdscr.refresh()
			if c == ord('7'):	# page 0, block 7
				command = 70
				screenData = ""
				del subwin
				stdscr.touchwin()
				stdscr.refresh()			
		elif c == ord('9'):
			# Exit cleanly
			getOut()
			
		# Send command to reader - I had to fudge this up to make
		# parameteric commands work
		if (command >= 64) and (command <= 70) : # parametric command - fixme
			outStr = options[command] + "31415927\r"
		else:
			outStr = options[command]
		# There is a short pause, print WAIT on screen
		stdscr.addstr(0, 50, "WAIT", curses.A_REVERSE)
		# Force screen update NOW
		stdscr.refresh()
		# logging can be very useful
		logging.debug("Data written to reader: %s", outStr)
		inStr = sendCommand(outStr)
		logging.debug("Data read from reader: %s", inStr)
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
		elif command == 6 and inStr == "?1\r":
			screenData  = "absent"
		elif command == 7 and inStr == "?1\r":
			screenData  = "absent"
		elif command == 7 and inStr == "?2\r":
			screenData  = "fail"
		
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

