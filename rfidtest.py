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
import string
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

# Set up logging
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
	"""
	Python's level-based logging system is initialized here. A debug.log
	file is created anew each time application is run.
	"""
	
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
	formatter = logging.Formatter(fmt='%(asctime)s: %(message)s', \
		datefmt='%I:%M:%S')

	fh = logging.FileHandler(filename)
	fh.setFormatter(formatter)
	logger.addHandler(fh)


class WindowMaker:
	"""
	Draws a menu window with a nice box around it. Accepts a list
	of strings, each element is a line of a menu.  The window and
	box are drawn parametrically to be of proper size and centered
	on screen, based on max length of menu items and number of
	lines in menu
	"""
	def __init__(self):
		global stdscr	# we need to get parent information from this
		self.menu = []
		self.__cornerX = 0	# window upper left corner X coords
		self.__cornerY = 0	# window upper left corner Y coords
		self.__height = 0	# window height
		self.__width = 0	# window width
		self.__maxLen = 0
		self.__loop = 1		# a loop variable

	def showWindow(self,menu):
		self.__menu = menu
		# Iterate through the items in the menu list, and find
		# max. length of menu line and number of elements in list
		# this will allow proper sizing of the window
		for self.__line in self.__menu:
			self.__lineLen = len(self.__line)
			if self.__maxLen < self.__lineLen:
				self.__maxLen = self.__lineLen
		# Now the size of the window is known
		# add 2 to allow room for the nice border
		self.__width = self.__maxLen + 2
		# returns nbr of elements
		self.__height = self.__menu.__len__() + 2	

		# Calculate corner X and Y to place box in center
		# of screen
		self.__parentHeight = stdscr.getmaxyx()[0]
		self.__parentWidth = stdscr.getmaxyx()[1]
		self.__cornerX = (self.__parentWidth - self.__width)/2
		self.__cornerY = (self.__parentHeight - self.__height)/2
		
		# Draw the window
		self.__subwin = curses.newwin(self.__height, self.__width, \
			self.__cornerY, self.__cornerX)
		self.__subwin.box()
		for self.__line in self.__menu:
			self.__subwin.addstr(self.__loop, 1, self.__line)
			self.__loop += 1
			
		self.__subwin.refresh()
		
	def __del__(self):
		# refresh the main window
		stdscr.touchwin()
		stdscr.refresh()

class WindowEntry:
	"""
	Draws a non-parametrtic window in the center of the screen that
	allows the user to enter 1 memory block of data, which is an 8-digit
	ASCII hex string. Data is checked to verify validity.
	
	Class returns the actual data string, unlike the WindowMaker class.
	"""
	
	def __init__(self):
		global stdscr	# we need to get parent information from this
		self.menu = []
		self.__cornerX = 0		# window upper left corner X coords
		self.__cornerY = 0		# window upper left corner Y coords
		self.__height = 3		# 1 line + 2 for box border
		self.__width = 10		# 8 characters + 2 for box border
		self.__charYX = [1,1]	# list defines character position
		self.__stringLen = 8	# length of string
		self.result = ''		# the returned string

	def showWindow(self):
		# Calculate corner X and Y to place box in center
		# of screen
		self.__parentHeight = stdscr.getmaxyx()[0]
		self.__parentWidth = stdscr.getmaxyx()[1]
		self.__cornerX = (self.__parentWidth - self.__width)/2
		self.__cornerY = (self.__parentHeight - self.__height)/2
		# Draw the window
		self.__subwin = curses.newwin(self.__height, self.__width, \
			self.__cornerY, self.__cornerX)
		self.__subwin.box()
		self.__subwin.refresh()
		
	def getText(self):
		# Iterate through string, starting from leftmost character
		for __x in range(0, self.__stringLen):
			# move cursor to position and get character
			self.__c = self.__subwin.getch(self.__charYX[0],self.__charYX[1])
			# test to see if character is valid
			if chr(self.__c) in string.hexdigits:
				logging.debug("valid hex digit entered")
				self.result += chr(self.__c)
				self.__subwin.addch(self.__charYX[0],self.__charYX[1],self.__c)
				self.__charYX[1] += 1
				logging.debug("result string: %s", self.result)
		
		# The string is finished by now, except for the \r
		# cherry on top
		self.result += '\r'
		return self.result
	
	def __del__(self):
		# refresh the main window
		stdscr.touchwin()
		stdscr.refresh()	

class WindowMonitor:
	"""
	Creates a window that monitors the serial port. RFID data is printed
	out - data over a certin time limit changes color to show its 
	age. Pressing a ? key ends the class
	"""
	def __init__(self):
		global stdscr
		self.__cornerX = 0		# window upper left corner X coords
		self.__cornerY = 0		# window upper left corner Y coords
		self.__height = 3		# 1 line + 2 for box border
		self.__width = 64		# max 7 blocks of 8 chars. + 6 spaces
								# + 2 for border = 64
		self.__tagData = ''		# data from serial port
		self.__clearString = ' ' * (self.__width - 2)
	
	def showWindow(self):
		# Calculate corner X and Y to place box in center
		# of screen
		self.__parentHeight = stdscr.getmaxyx()[0]
		self.__parentWidth = stdscr.getmaxyx()[1]
		self.__cornerX = (self.__parentWidth - self.__width)/2
		self.__cornerY = (self.__parentHeight - self.__height)/2
		# Draw the window
		self.__subwin = curses.newwin(self.__height, self.__width, \
			self.__cornerY, self.__cornerX)
		self.__subwin.timeout(1000)	# getch blocking for x millis
		
		self.__subwin.box()
		self.__subwin.refresh()
		
		while (self.__subwin.getch() == -1):
			self.__tagData = serialPort.readline()
			if self.__tagData <> '':
				self.__subwin.addstr(1, 1, self.__clearString)
			self.__subwin.addstr(1, 1, self.__tagData, curses.A_REVERSE)
			self.__tagData = ''
		
	def __del__(self):
		# refresh the main window
		stdscr.touchwin()
		stdscr.refresh()

def clearField(x, y):
	"""
	Clears the line from y,x coodinates provided to end of screen,
	so that data from last write operaiton is gone
	"""
	global stdscr	# Need to reference this global
	# stdscr.getmaxyx()[1]
	#stdscr.addstr(0, 50, "    ",)
	numSpaces = stdscr.getmaxyx()[1] - x
	spaceStr = " " * numSpaces
	stdscr.addstr(y,x,spaceStr)
	
	
def main():

	initLogging('debug.log')

	# Open serial port
	if (serialPort.isOpen() == False):
		serialPort.open()
		
	# Initialize strings
	outStr = '' # data sent to reader
	inStr = ''	# data read from reader
	readerActive = False	# state of RF field
	
	# Other variables scoped to main
	entryFound = False	# True if entry is found in menu
	
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
	stdscr.addstr(7,0, "(5) Read std data")
	stdscr.addstr(8,0, "(6) Read block (T55xx)")
	stdscr.addstr(9,0, "(7) Write block (T55xx)")
	stdscr.addstr(10,0, "(8) Set max block (T55xx)")
	stdscr.addstr(11,0, "(9) Read RFID tags")
	stdscr.addstr(12,0, "(q) Exit program")
	
	# The options dictionary contains a mapping of command numbers
	# to commands.  Command number >= 50 are not user commands
	# but are sent by the application after some preprocessing
	options = { 0: "VER\r",		# firmware version
				1: "MOF\r",		# measure operating frequency
				4: "LTG\r",		# locate transponder
				5: "RSD\r",		# read standard data
				9:	"",			# read RFID tags (no command string)
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
				64: "WB1",		# write block 1 (8 ASCII hex bytes)
				65: "WB2",		# write block 2 (8 ASCII hex bytes)
				66: "WB3",		# write block 3 (8 ASCII hex bytes)
				67: "WB4",		# write block 4 (8 ASCII hex bytes)
				68: "WB5",		# write block 5 (8 ASCII hex bytes)
				69: "WB6",		# write block 6 (8 ASCII hex bytes)
				70: "WB7",		# write block 7 (8 ASCII hex bytes)
				71: "SM0\r",		# set max block 0 (config block)
				72: "SM1\r",		# set max block 1 (data block 1)
				73: "SM2\r",		# set max block 2 (data block 2)
				74: "SM3\r",		# set max block 3 (data block 3)
				75: "SM4\r",		# set max block 4 (data block 4)
				76: "SM5\r",		# set max block 5 (data block 5)
				77: "SM6\r",		# set max block 6 (data block 6)
				78: "SM7\r",		# set max block 7 (data block 7)
				}

	# Data based on top menu selections are based on a list of
	# tuples
	# (character, command, locx, locy, screenData)
	commandList = [
				('0', 0, 50, 2, ''),	# firmware version
				('1', 1, 50, 3, ''),	# measure frequency
				('2', 2, 50, 4, ''),	# set reader active/deactive		
				('3', 3, 50, 5, ''),	# set tag type
				('4', 4, 50, 6, ''),	# locate transponder
				('5', 5, 18, 7, ''),	# read standard data
				('6', 6, 50, 8, ''),	# read block (T55xx)
				('7', 7, 50, 9, ''),	# write block (T55xx)
				('8', 8, 50, 10, ''),	# set max block
				('9', 9, 50, 11, 'done'),	# read RFID tags(monitor port)
				('q', 0, 0, 0, ''),		# quit
				]

	while (True):
		while (entryFound == False):
			c = stdscr.getch() # read a single character, returns ASCII code
			logging.debug("entered char: %d", c)

			# Interate through commandList and determine command, locX,
			# locY, screenData
			for tupple in commandList:
				if tupple[0] == chr(c):
					command = tupple[1]
					locx = tupple[2]
					locy = tupple[3]
					screenData = tupple[4]
					entryFound = True

		entryFound = False

		# Clear the screen area that will be written to for
		# the command to follow
		clearField(locx, locy)

		# Convert ASCII code to string, and interpret it
		# if/elif caluses evaluate submenu commands only
		if c == ord('2'):	# set reader active/deactive
			if readerActive == False:	# acticate
				command = 50
				readerActive = True
				screenData = "active"
			else:						# deactivate
				command = 51
				readerActive = False
				screenData = "inactive"
		elif c == ord('3'):	# set tag type, requires subwindow menu
		
			# Define menu list
			aMenu = [
					"(1) - EM4100", 
					"(2) - T55xx",
					"(3) - FDX-B/HDX",
					"(4) - TIRIS",
					"(5) - EM4205"
					]
					
			# Instantiate a class of WindowMaker to draw
			# menu window
			subWindow = WindowMaker()
			subWindow.showWindow(aMenu)

			# This selection is for the tag type subwindow
			# Note the that the screenData length is 9 characters,
			# not including carriage return.  This is to insure that
			# the data output areas are wiped clean.  This is a real
			# ghetto way of doing this, and must be improved
			c = stdscr.getch()

			if c == ord('1'):
				command = 52
				screenData = "EM4100   "
				del subWindow
			if c == ord('2'):
				command = 53
				screenData = "T55xx    "
				del subWindow
			if c == ord('3'):
				command = 54
				screenData = "FDX-B/HDX"
				del subWindow
			if c == ord('4'):
				command = 55
				screenData = "TIRIS    "
				del subWindow
			if c == ord('5'):
				command = 56
				screenData = "EM4205   "
				del subWindow
		elif c == ord('6'):	# read block (T55xx)
			#command = 6
			#locx = 50
			#locy = 8
			
			# Define menu list
			aMenu = [
					"(1) - Page 0, Block 1", 
					"(2) - Page 0, Block 2",
					"(3) - Page 0, Block 3",
					"(4) - Page 0, Block 4",
					"(5) - Page 0, Block 5",
					"(6) - Page 0, Block 6",
					"(7) - Page 0, Block 7"
					]
					
			# Instantiate a class of WindowMaker to draw
			# menu window
			subWindow = WindowMaker()
			subWindow.showWindow(aMenu)

			# This selection is for the tag type subwindow
			# Note the that the screenData length is 9 characters,
			# not including carriage return.  This is to insure that
			# the data output areas are wiped clean.  This is a real
			# ghetto way of doing this, and must be improved
			c = stdscr.getch()
			
			if c == ord('1'):	# page 0, block 1
				command = 57
				screenData = ""
				del subWindow
			if c == ord('2'):	# page 0, block 2
				command = 58
				screenData = ""
				del subWindow
			if c == ord('3'):	# page 0, block 3
				command = 59
				screenData = ""
				del subWindow
			if c == ord('4'):	# page 0, block 4
				command = 60
				screenData = ""
				del subWindow
			if c == ord('5'):	# page 0, block 5
				command = 61
				screenData = ""
				del subWindow
			if c == ord('6'):	# page 0, block 6
				command = 62
				screenData = ""
				del subWindow
			if c == ord('7'):	# page 0, block 7
				command = 63
				screenData = ""
				del subWindow
		elif c == ord('7'):	# write block (T55xx)
			# Define menu list
			aMenu = [
					"(1) - Page 0, Block 1", 
					"(2) - Page 0, Block 2",
					"(3) - Page 0, Block 3",
					"(4) - Page 0, Block 4",
					"(5) - Page 0, Block 5",
					"(6) - Page 0, Block 6",
					"(7) - Page 0, Block 7"
					]
			
			# Instantiate a class of WindowMaker to draw
			# menu window
			subWindow = WindowMaker()
			subWindow.showWindow(aMenu)

			# This selection is for the tag type subwindow
			# Note the that the screenData length is 9 characters,
			# not including carriage return.  This is to insure that
			# the data output areas are wiped clean.  This is a real
			# ghetto way of doing this, and must be improved
			c = stdscr.getch()
			
			if c == ord('1'):	# page 0, block 1
				command = 64
				screenData = ""
				del subWindow
			if c == ord('2'):	# page 0, block 2
				command = 65
				screenData = ""
				del subWindow
			if c == ord('3'):	# page 0, block 3
				command = 66
				screenData = ""
				del subWindow
			if c == ord('4'):	# page 0, block 4
				command = 67
				screenData = ""
				del subWindow
			if c == ord('5'):	# page 0, block 5
				command = 68
				screenData = ""
				del subWindow
			if c == ord('6'):	# page 0, block 6
				command = 69
				screenData = ""
				del subWindow
			if c == ord('7'):	# page 0, block 7
				command = 70
				screenData = ""
				del subWindow
				
			# Instantiate a class which allows entering the 8-digit
			# hex value for writing to memory blocks
			dataWindow = WindowEntry()
			# Draw the data window
			dataWindow.showWindow()
			# Custom data for writing block
			blockData = dataWindow.getText()
			del dataWindow
		elif c == ord('8'):	# set max block
			# Define menu list
			aMenu = [
					"(1) - Config Block - page 0, block 0", 
					"(2) - Data Block - page 0, block 1",
					"(3) - Data Block - page 0, block 2",
					"(4) - Data Block - page 0, block 3",
					"(5) - Data Block - page 0, block 4",
					"(6) - Data Block - page 0, block 5",
					"(7) - Data Block - page 0, block 6",
					"(8) - Data Block - page 0, block 7",
					]
					
			# Instantiate a class of WindowMaker to draw
			# menu window
			subWindow = WindowMaker()
			subWindow.showWindow(aMenu)

			# This selection is for the tag type subwindow
			# Note the that the screenData length is 9 characters,
			# not including carriage return.  This is to insure that
			# the data output areas are wiped clean.  This is a real
			# ghetto way of doing this, and must be improved
			c = stdscr.getch()
			
			if c == ord('1'):	# config - page 0, block 1
				command = 71
				screenData = ""
				del subWindow
			if c == ord('2'):	# data 1 - page 0, block 2
				command = 72
				screenData = ""
				del subWindow
			if c == ord('3'):	# data 2 - page 0, block 3
				command = 73
				screenData = ""
				del subWindow
			if c == ord('4'):	# data 3 - page 0, block 4
				command = 74
				screenData = ""
				del subWindow
			if c == ord('5'):	# data 4 - page 0, block 5
				command = 75
				screenData = ""
				del subWindow
			if c == ord('6'):	# data 5 - page 0, block 6
				command = 76
				screenData = ""
				del subWindow
			if c == ord('7'):	# data 6 - page 0, block 7
				command = 77
				screenData = ""
				del subWindow
			if c == ord('8'):	# data 6 - page 0, block 7
				command = 78
				screenData = ""
				del subWindow
		elif c == ord('9'):	# read RFID tags (monitor port)
			subWindow = WindowMonitor()
			subWindow.showWindow()
			del subWindow
		elif c == ord('q') or c == ord('Q'):	# quit
			# Exit cleanly
			getOut()
			
		# Send command to reader - I had to fudge this up to make
		# parameteric commands work
		if (command >= 64) and (command <= 70) : # parametric command - fixme
			outStr = options[command] + blockData
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
		elif command >= 71 and command <= 78:
			# The set max block command has an undocumented feature
			# in that it returns what looks like the configuration
			# block along with the reply (at least if success). To
			# prevent garbage on screen, I will look for the reply
			# in the string
			if 'OK' in inStr:						
				screenData  = "okay       "
			elif "?1" in inStr:
				screenData  = "absent     "
			elif "?2" in inStr:
				screenData  = "fail       "
			elif "?3" in inStr:
				screenData  = "not allowed"
		
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

