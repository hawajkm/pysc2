#=========================================================================
# Dynamic maps creation
#=========================================================================
# Dynamically and automatically create maps based on immediate
# sub-directories.
#
# By  : Khalid Al-Hawaj
# Date: 10 April 2018

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# builtin imports
import os

# pysc2 imports
from pysc2.maps import lib

#=========================================================================
# List to hold all dynamic maps
#=========================================================================

dynamic_maps_list = []

#=========================================================================
# Get global variables
#=========================================================================
# Variables needed for dynamic map generation

# File directory name
lpath = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))

# Get immediate subdirectories
for name in os.listdir(lpath):
  if os.path.isdir(os.path.join(lpath, name)):
    dynamic_maps_list.append(name)

#=========================================================================
# DynamicMap
#=========================================================================
# DynamicMap class as a template

class DynamicMap(lib.Map):
  download = None
  players = 1
  score_index = 0
  game_steps_per_episode = 0
  step_mul = 8

#=========================================================================
# Actual maps creation
#=========================================================================

for map_name in dynamic_maps_list:
  filename = map_name
  dir_name = lpath + '/' + map_name
  cls_dict = dict(filename = map_name, directory = dir_name)
  globals()[map_name] = type(map_name, (DynamicMap,), cls_dict)
