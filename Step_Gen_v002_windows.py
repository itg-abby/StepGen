import os
import sys
import numpy as np
import math
from scikits.audiolab import Sndfile

import subprocess

# itg-Abby 's SM file generator v0.2
#
# Dependent package listing for Linux users trying to run this script:
# sudo apt-get install python-dev python-numpy python-setuptools libsndfile-dev python-scikits
# python-audiolab flac vorbis-tools
#
#
# What is new in this version:
# Now featuring the pitch detection option-set for much more relevant note selection.
#
# What is in this version from before:
# Generates a SM file with arrow placement at every detected note onset via AUBIO options.
# SM file is just a basic skeleton file with left arrows at every note. You need to
# still move these arrows around as desired (Also, don't forget to set your own SM offset)!
#
# General Notes:
# See the AUBIO manpage/website for more details: aubio.org/manpages/latest/aubioonset.1.html
#
# How to run this script with the AUBIO options detailed in their documentation is below:
#
# ./python filename.ogg bpm stepsize -o OnsetMethod -s Silence -t OnsetThreshold
#
# Examples:
# ./python StepGenScriptName Electro411.ogg 130.990 16
# ./python StepGenScriptName Electro411.ogg 130.990 16 -o Default -s -90.0 -t 0.3
#
# Any AUBIO options will use their defaults if not filled in, so in my first example the 
# OnsetMethod = Default, Silence = -90.0, and OnsetThreshold = 0.3
#
# Samplerates are auto-detected and the BPM you enter doesn't even have to be correct.
# The notes will be placed according to the exact time they occur as close as possible
# to the BPM signature of your choice. If you want a 150bpm song written with notes
# from a 98bpm time signature, you can do that (untested, but should work).
#
#
#
# Planned future implementation:
# - Interface and executables
# - Connecting this script to my other "Step Shuffle" script once it is completed
#
# Credits:
# Developers of AUBIO, Python, and all the cool Python packages that made this possible.
#
# *************************************************************************************
# *************************************************************************************
#
# Required inputs:
# Arg1 - Filename,
# Arg2 - BPM estimate,
# Arg3 - desired step/note size to round to.
# Optional Inputs:
# Arg4 (-o) - Onset Type,
# Arg5 (-s) - Silence Threshold,
# Arg6 (-t) - Onset/Peak picking threshold
# Arg7 (-l) - Pitch Tolerance
# Arg8 (-p) - Pitch Type
#
# Sample rates divisible by 4 and (3/25) are supported (i.e. not 11025, i.e. 44100).
# Calculates fineness to the 192th note (higher accuracy isn't relevant), then performs rounding.
#
# Rounding is recommended at the following note lengths: 1,4,8,16,24,32,48,64,192
# BPMs under 100bpm should typically be doubled, i.e. 80bpm entered as 160bpm.


# <<<<<<<<<<< BEGINNING OF MAIN PROGRAM >>>>>>>>>>>>
def main():

	sent_file = sys.argv[1]
	bpm = float(sys.argv[2])
	stepsize = 192
	roundsize = float(sys.argv[3])
	bin_size, shunt_window = bin_calculate(sent_file, bpm, stepsize)
	bin_maximums = populate_list(bin_size)
	bin_maximums_shift = []

# Prepare a set of values and some lists for the Combining, Rounding process.
	sound_file = Sndfile('{0}'.format(sent_file), 'r')
	sr = sound_file.samplerate
# Prepare AUBIO data of soundfile
	if len(sys.argv) > 3 and ('-o' in sys.argv):
		oindex = (sys.argv).index('-o')+1
		onsetType = "{0}".format(sys.argv[oindex])
	else:
		onsetType = "default"
	if len(sys.argv) > 3 and ('-s' in sys.argv):
		sindex = (sys.argv).index('-s')+1
		silenceVal = float(sys.argv[sindex])
	else:
		silenceVal = float(-90.0)
	if len(sys.argv) > 3 and ('-t' in sys.argv):
		tindex = (sys.argv).index('-t')+1
		thresholdVal = float(sys.argv[tindex])
	else:
		thresholdVal = float(0.3)
	if len(sys.argv) > 3 and ('-l' in sys.argv):
		llindex = (sys.argv).index('-l')+1
		ptolerance = float(sys.argv[llindex])
	else:
		ptolerance = float(0.0)
	if len(sys.argv) > 3 and ('-p' in sys.argv):
		ptindex = (sys.argv).index('-P')+1
		pitchType = float(sys.argv[ptindex])
	else:
		pitchType = 'default'

	print "bpm:{0} step:{1} file:{2} onset:{3} thresh:{4}\
	 silence:{5} pitchTolerance:{6} pitchType:{7}\
	 ".format(bpm, roundsize, sent_file, onsetType,\
	  thresholdVal, silenceVal, ptolerance, pitchType)
	  
#	aubiodat = aubiodata(sent_file, onsetType, thresholdVal, silenceVal)
#	aubiopit = aubiopitch(sent_file, pitchType, ptolerance, sr)
	aubioNOTES(sent_file, onsetType, thresholdVal, silenceVal)
	aubiodat = []
	with open('audata','r') as nudatas:
		for line in nudatas:
			aubiodat.append(line)
	
#
	bin_maximums_combined = sorted((bin_maximums + bin_maximums_shift), key=lambda x: x[1])
	oneninetwo_frames = (((60000/float((bpm*(192/4)))))*0.001*sr)
	rounded_frames = round(((60000/float((bpm*(roundsize/4)))))*0.001*sr,10)
	bin_maximums_rounded = []
	bin_maximums_duped = []
	value_shifts = [0, oneninetwo_frames, -oneninetwo_frames, -oneninetwo_frames*2, oneninetwo_frames*2, oneninetwo_frames*3, -oneninetwo_frames*3]
	value_shifts2 = [round(oneninetwo_frames*3/float(sr),3), round(-oneninetwo_frames*3/float(sr),3)]



# Round the data to the desired time lengths, rounding only occurs if an amplitude is
# within a 64th note of the desired note type. A 64th is the smallest reasonable gap
# for the human ear to be able to notice a difference in rounding to less frequent note
# divisions at tempos that are above 100bpm. Silence is favored over an "off-synch" note.
# For example: at 100 bpm, a 64th note is equivalent to 0.037 seconds and a 16th note is
# equivalent to 0.150 seconds . If rounding to the 16th note was desired and a note was
# found at 0.120, a note would be placed at 0.150. If the note was found at 0.036, a note
# would be placed at 0.000. If the note was found at 0.075, no note would be placed.

	previous_time = float(-10)
	for item in bin_maximums_combined:
		if (float(item[1]) != previous_time):
			bin_maximums_rounded.append(item)
		previous_time = float(item[1])


	previous_time = float(0)
	previous_val = float(0)				

# Write the rounded data to file
	for item in bin_maximums_rounded:
		value_check = 1
		for offset in value_shifts:
			offset_time = (item[1] + offset)
			offset_time_sec = round((item[1] + offset)/float(sr),3)
			if value_check:
				if (int(offset_time % rounded_frames) == 0):
					if (float(offset_time_sec) == previous_time) and (float(item[0]) > previous_val):
						try:
							bin_maximums_duped.pop()
						except IndexError:
							pass
						bin_maximums_duped.append((item[0],offset_time))
					if (float(offset_time_sec) != previous_time):
						bin_maximums_duped.append((item[0],offset_time))
					value_check = 0
					previous_time = float(offset_time_sec)
					previous_val = float(item[0])


# Write the rounded data to file
	with open('{0}_stepseconds.txt'.format(sent_file), 'w') as complete_file:
		for item in bin_maximums_duped:
				time_convert = item[1]/float(sr)
				complete_file.write('{0}\n'.format(round((time_convert),3)))

# Combine the two lists. (AUBIO + rounded list)
	with open('{0}_COMBINED.txt'.format(sent_file), 'w') as com_file:
		storedval = 10000
		previous_time = 0
		for item in bin_maximums_duped:
				try:
					time_convert = item[1]/float(sr)
					timediff = abs(float(aubiodat[0]) - time_convert)
					if (timediff <= storedval):
						storedval = timediff
						previous_time = time_convert

					elif (timediff > storedval):
						com_file.write('{0}\n'.format(round((previous_time),3)))
						aubiodat.pop(0)
						previous_time = time_convert
						storedval = abs(float(aubiodat[0]) - time_convert)
				except IndexError:
					pass
# To Do: Attempt guess at Threshold + Silence values? Allow user input?

# Create the SM file template
	sm_template = """#TITLE:{infile};
#SUBTITLE:;
#ARTIST:Template File;
#TITLETRANSLIT:;
#ARTISTTRANSLIT:;
#GENRE:;
#CREDIT:;
#BANNER:Banner.png;
#BACKGROUND:Background.png;
#LYRICSPATH:;
#CDTITLE:;
#MUSIC:{musicfile};
#OFFSET:0.000;
#SAMPLESTART:14.730;
#SAMPLELENGTH:14.769;
#SELECTABLE:YES;
#BPMS:0.000={bpmval};
#STOPS:;
#BGCHANGES:;
#KEYSOUNDS:;

//---------------dance-single - Blank---------------
#NOTES:
     dance-single:
     Blank:
     Expert:
     111:
     0.000,0.000,0.000,0.000,0.000:
"""
	params={}
	params['bpmval'] = '{0}'.format(bpm)
	params['infile'] = '{0}'.format(sent_file.split('.')[0])
	params['musicfile'] = '{0}'.format(sent_file)
	with open('{0}.sm'.format(sent_file.split('.')[0]),'w') as smfile:
		smfile.write(sm_template.format(**params))

# Generate the SM based on the values found (Only 1 arrow in this version)
	with open('{0}_stepseconds.txt'.format(sent_file), 'r') as complete_file:
		with open('{0}_COMBINED.txt'.format(sent_file), 'r') as com_file:
			with open('{0}.sm'.format(sent_file.split('.')[0]),'a') as smfile:
				current_line = com_file.readline()
				line_counter_a = 0
				for line in complete_file:
					if line == current_line:
						smfile.write('1000\n')
						current_line = com_file.readline()
						line_counter_a = line_counter_a + 1
						if float(line_counter_a) == roundsize:
							smfile.write(',\n')
							line_counter_a = 0
					elif line != current_line:
						smfile.write('0000\n')
						line_counter_a = line_counter_a + 1	
						if float(line_counter_a) == roundsize:
							smfile.write(',\n')
							line_counter_a = 0
				smfile.write(';\n')
		
#	os.remove('{0}_stepseconds.txt'.format(sent_file))
#	os.remove('{0}_COMBINED.txt'.format(sent_file))

# <<<<<<<<<<< END OF MAIN PROGRAM >>>>>>>>>>>>


# AUBIO datagen
def aubioNOTES(filename, onsetType, threshold, silence):
#	runstring = 'aubionotes -i {0} -v'.format(filename)
	raN = subprocess.Popen(['aubionotes_local.exe -i {0} -v'.format(filename)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

	stdout, stderr = raN.communicate()

	with open('stdout','w') as f1:
#		stdout= sys.stdout
		f1.write('{0}'.format(stdout))
	with open('stderr','w') as f2:
#		stderr= subprocess.PIPE
		f2.write('{0}'.format(stderr))
		
	with open('stdout','r') as parsed:
		with open('audata','w') as nudatas:
			parsed.readline()
			parsed.readline()
			parsed.readline()
			parsed.readline()
			for line in parsed:
				try:
					nudatas.write('{0}\n'.format(line.split()[1]))
				except IndexError:
					pass
			

		
		


def populate_list(bin_size):
	newbinmaxs = []
	curr_bin = 0
	n = 0
	for zed in range(1, 50):
		for n in range(1,1001):
			curr_bin = curr_bin + bin_size	
			newbinmaxs.append((1,curr_bin))

	return newbinmaxs
# Stepsize will be given as a single digit entry
# Quarter note = 4, Sixteenth note = 16
def bin_calculate(sent_file, bpm, stepsize):
	sound_file = Sndfile('{0}'.format(sent_file), 'r')
	sec_bin_size = ((60000/float((bpm*(stepsize/4)))))*0.001
	sixfour_sec_bin_size = ((60000/float((bpm*((stepsize*2)/4)))))*0.001
	bin_size = sec_bin_size*(sound_file.samplerate)
	shunt_window = int(sixfour_sec_bin_size*(sound_file.samplerate))
	return bin_size, shunt_window


if __name__ == '__main__':
	main()
