import os
import sys
import re
from random import randint
import random

# Run format: python step_shuffle_stream.py Stepchart.sm
# Output: newstep.sm
#
# Release notes:
#
# WARNING! right now everything will be turned into a single arrow! i.e. dumpstream
#
# The current algorithm is a totally random placement which respects Left Foot/Right Foot
# alternation. The only placement types you will see are single arrow: U,D,L,R
#
# Note that shuffling will only occur on the first stepchart found.
# If there are more stepcharts (i.e. difficulties) in the file, they will simply be ignored.
# This also means the default behavior would shuffle the "Novice" chart...if it as at the top.
#
# Currently does not work for doubles!
#
# Near future plans:
#
# 1. still need to add on/off arguments for sm_file shuffle parameters i.e.:
# mines, jumps, hands, crossovers = a 180, back crossovers = 270s,
# double steps+conducting mines, drills, specific stream patterns (staircases, etc.)
#
# 2. shuffle specific areas of chart instead of whole chart (indicated by measure or beat)
#
# 3. ability shuffle all charts (or specific chart) found in SM file, not just the first one
#
#
#
# This script will be combined to work inside the Step Gen program I have also written.



def main():


#
#	sm_file = '{0}.sm'.format(sent_file.split('.')[0])
	sm_file = sys.argv[1]

	count = 0
	
	while os.path.exists('newstep_'+'{0}'.format(count)+sm_file.split('.sm')[0]+'.sm'):
		count = count + 1

	new_sm_name = 'newstep_'+'{0}'.format(count)+sm_file.split('.sm')[0]+'.sm'

# read the first stepchart found as an array
	smdata = []
	countme = 0
	read_sm = 0
	with open(sm_file, 'r') as infile:
		with open(new_sm_name,'w') as newstep:
			for line in infile:
				if (read_sm == 0 and countme != 6):
					newstep.write(line)
				if (countme >= 1):
					countme = countme + 1
					if countme == 7:
						read_sm = 1
						countme = 0
				try:
					if (line.split()[0] == "#NOTES:"):
						countme = countme+1
				except IndexError:
					pass

				if (read_sm == 1):
					smdata.append(line)

				if (line == ";"):
					break


# begin shuffling the data in smdata
# initial algorithm will be naive implementation...just applying a formula
# final algorithm should make a judgement for how close "arrow blocks" are before apply formula

# find the step blocks -> process -> replace where they were found in original array
# search and build arrow blocks here:
#	step_blocks = []
	step_blocks = smdata

# pick a random number to place arrows for (ideally can be any amt > 1).
# always keep track of L/R foot.
# random start for L or R foot
# step resets? i.e. L+R

# 0 = Left foot start, 1 = Right foot start
#	start_foot = randint(0,1)
	start_foot = 1
#	previous_step = "1001"
	previous_step = "1000"
	previous_foot = 0


	with open(new_sm_name, 'a') as newstep:
#	with open('newstep2.sm', 'w') as newstep:
		for items in step_blocks:

			item = items.split('\n')[0]
			if (item != "0000" and item !="," and item !=";"):
				item = gen_step(start_foot, previous_step, previous_foot)[0]
				previous_step = item
				if (start_foot == 0):
					previous_foot = 0
					start_foot = 1
				elif (start_foot == 1):
					previous_foot = 1
					start_foot = 0

			newstep.write("{0}\n".format(item))
			




#def gen_pat(start_foot, previous_step, previous_foot):
# LDUR = 0000
# 0 = Left foot start, 1 = Right foot start
#
# Given random number of arrows (1~10?), place the arrows in a known pattern
# Inputs: a block of arrows to place OR "commands" to send to "gen_step"
#	if len(step_block) == 1:
#		step_gen()
#	elif len(step_block) == 2:
#	elif len(step_block) == 3:

# ...

#	return placement





def gen_step(start_foot, previous_step, previous_foot):
# LDUR = 0000
# 0 = Left foot start, 1 = Right foot start
	placement = "NA"



#####################
# Placing a left foot:
#####################
	if (start_foot == 0 and previous_step == "1000"):
		# crossover, 270 logic here
		# if is redundant, just for my own references
		# could be useful later when adding double taps
		if (previous_foot == 1):
# crossover, 270
#			placement = random.sample(("0100","0001"), 1)
# crossover, no 270
#			placement = "0100"
			1
# crossover
	elif (start_foot == 0 and previous_step == "0100"):
		if (previous_foot == 1):
#			placement = random.sample(("1000","0010","0001"), 1)
			placement = random.sample(("1000","0010"), 1)

	elif (start_foot == 0 and previous_step == "0010"):
		if (previous_foot == 1):
# crossover
#			placement = random.sample(("1000","0100","0001"), 1)
			placement = random.sample(("1000","0100"), 1)

	elif (start_foot == 0 and previous_step == "0001"):
		if (previous_foot == 1):
			placement = random.sample(("1000","0100","0010"), 1)
#####################
# Placing a right foot:
#####################
	elif (start_foot == 1 and previous_step == "1000"):
		if (previous_foot == 1):
			1
		elif (previous_foot == 0):
			placement = random.sample(("0001","0100","0010"), 1)

	elif (start_foot == 1 and previous_step == "0100"):
		if (previous_foot == 1):
			1
#crossover
		elif (previous_foot == 0):
#			placement = random.sample(("1000","0001","0010"), 1)
			placement = random.sample(("0001","0010"), 1)
	elif (start_foot == 1 and previous_step == "0010"):
		if (previous_foot == 1):
			1
#crossover
		elif (previous_foot == 0):
#			placement = random.sample(("1000","0100","0001"), 1)
			placement = random.sample(("0100","0001"), 1)
	elif (start_foot == 1 and previous_step == "0001"):
		if (previous_foot == 1):
			1
#crossover, 270
		elif (previous_foot == 0):
#			placement = random.sample(("1000","0100"), 1)
#crossover, no 270
#			placement = "0100"
			1
	return placement
	


if __name__ == '__main__':
	main()
