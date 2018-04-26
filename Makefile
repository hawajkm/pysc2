# Huh

PWD=$(shell pwd)

export PYTHONPATH=$(PWD)

#----------------------------------------------------------------------
# Default target
#----------------------------------------------------------------------
default: all


#----------------------------------------------------------------------
# Run default stuff
#----------------------------------------------------------------------
all:
	python pysc2/bin/agent.py --map=MoveToBeacon


#----------------------------------------------------------------------
# Test dynamic maps
#----------------------------------------------------------------------
dynamics:
	python pysc2/bin/agent.py --map=TwoMineralShards --agent=pysc2.agents.test_agent.TestAgent
