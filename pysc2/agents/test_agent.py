# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A test agent for starcraft."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy
import json
import copy
import math

from pysc2.agents import base_agent
from pysc2.lib import actions
from pysc2.lib import features
from pysc2.lib import point

from pysc2.lib import translate_coord
from pysc2.lib import parse_obs

_PLAYER_RELATIVE = features.SCREEN_FEATURES.player_relative.index
_PLAYER_FRIENDLY = 1
_PLAYER_NEUTRAL = 3  # beacon/minerals
_PLAYER_HOSTILE = 4
_NO_OP = actions.FUNCTIONS.no_op.id
_MOVE_SCREEN = actions.FUNCTIONS.Move_screen.id
_ATTACK_SCREEN = actions.FUNCTIONS.Attack_screen.id
_SELECT_ARMY = actions.FUNCTIONS.select_army.id
_NOT_QUEUED = [0]
_SELECT_ALL = [0]
_SELECT_POINT = actions.FUNCTIONS.select_point.id
class TestAgent(base_agent.BaseAgent):
  """A random agent for starcraft."""

  def step(self, obs, nObs, game_info):
    super(TestAgent, self).step(obs)


    def get_object(arr, x, y):

      if arr[y][x] != 0:

        # Obj id
        id_ = arr[y][x]

        # Upper left corner?
        if arr[y-1][x] != id_ and arr[y][x-1] != id_ and arr[y-1][x+1] != id_:

          # Scan till you reach bottom
          rY = y
          while arr[rY + 1][x] == id_: rY += 1

          # Middle
          mY = int(round((rY + y) / 2))
          nX = x
          while arr[mY][nX - 1] == id_: nX -= 1

          # Scan till you reach right side
          rX = nX
          while arr[mY][rX + 1] == id_: rX += 1

          # Return middle
          return [(rX + nX) / 2, (rY + y) / 2]

      return None

    # Get game_info
    _map_size     = game_info['map_size'    ]
    _screen_size  = game_info['screen_size' ]
    _minimap_size = game_info['minimap_size']
    _camera_width = game_info['camera_width']
    _camera_pos   = game_info['camera_pos'  ]

    # Update translate_coord
    if not hasattr(self, '_translate_coord'):
      self._translate_coord = translate_coord.translate_coord()

    self._translate_coord.update(_map_size   , _minimap_size,
                                 _screen_size, _camera_width,
                                 _camera_pos ,              )

    # Get some units
    units = parse_obs.get_units(nObs, alliance = 1)				
    crystals = parse_obs.get_units(nObs, alliance = 3)			#get crystals 
    myunits = copy.deepcopy(units)					#create own version of units so that I can change locations and preserve originals
    print(myunits)	
    mycrystals = copy.deepcopy(crystals)			#create own version of crystals so that I can change locations and preserve originals 
    for unit in myunits:							#loop through individual units to translate position 
      unit['pos']['x'] = self._translate_coord.world_to_screen(unit['pos']['x'])		#Translate X Position 
      unit['pos']['y'] = self._translate_coord.world_to_screen(unit['pos']['y'])		#Translate Y Position 
    for crystal in mycrystals:						#loop through individual crystals
      crystal['pos']['x'] = self._translate_coord.world_to_screen(crystal['pos']['x'])	#Translate Crystal X Position 
      crystal['pos']['y'] = self._translate_coord.world_to_screen(crystal['pos']['y'])	#Translate Crystal Y Position
    distlist = []									#create an empty list for entering the distances from each agent to a particular crystal
#                                                   #This is a list of lists. Each list is a list of dictionaries that contains the tag along with the distance
#                                                   #to a given crystal. For example, the first list contains a dictionary of each unit tag and their distance
#                                                   #from the first crystal, the second contains the distance to the second crystal and so on. 
    for crystal in mycrystals:						#loop over all crystals
      singlecrystaldist = []						#create (and reset) an empty list for the distances from each individual crystal
      for unit in units:							#loop over the units
        xdist = unit['pos']['x'] - crystal['pos']['x']	#find x distance difference
        ydist = unit['pos']['y'] - crystal['pos']['y']	#find y distance difference
        dist = xdist*xdist + ydist*ydist				#find difference of square of distances
        dist = math.sqrt(dist)							#take square root (thus computing the distance)
        a = {'tag': unit['tag'], 'dist' : dist, 'crystalpos' : crystal['pos'], 'unitpos' : unit['pos'], 'is_closest' : False}			
#		#create(or append) a dictionary with the tag and its distance from a given crystal
        singlecrystaldist.append(a)						#append the list for the given crystal with the distance for the current unit
      distlist.append(singlecrystaldist)				#append the overall list with the distances from the current crystal
    print(distlist)										#print for testing
    print("distlist 0 0")
    print(distlist[0][0])
    

    for crystalList in distlist:						#Loop over all crystal lists
      listlength = len(crystalList)						#find list length
      i = 0												#set(reset) loop counter
      while (i < listlength):							#loop according to number of elements in a single list
#Ok so this loop structure probably looks super weird. What it does is, I want to compare all elements of each list (so each individual unit)
#with all the other units without comparing each individual to itself. This allows us to figure out if that unit is indeed closer to the crystal or not
#I do this by keeping the original list and creating a second independent one with that individual removed (thus the pop instruction)
#I then set is_closest true only in the case that it is closer than the other units.
#If you check out the print instruction, it looks like its working. It is also scalable since I actually count the number of elements in the list
        newlist = copy.deepcopy(crystalList)
        newlist.pop(i)
        j = 0
        while (j < (listlength - 1)):
          if newlist[j]['dist'] > crystalList[i]['dist']:
            crystalList[i]['is_closest'] = True
          else:
            crystalList[i]['is_closest'] = False
          j = j + 1
        i = i + 1
    print(distlist)										#print updated list of lists. This tells you which unit is closest to which crystal and can
#														#further used to set which unit should go to which crystal
    # Testing Minimap Translation
    print('#========================================================#')
    print('#              Testing Minimap Translation               #')
    print('#========================================================#')
    # Get one
    units = parse_obs.get_units(nObs, alliance = 1)
    for unit in units:
      x = unit['pos']['x']
      y = unit['pos']['y']

      print('Alliance 1 Unit at:', self._translate_coord.world_to_minimap(x, y))
    target = self._translate_coord.world_to_screen(x,y)		#calculate a target for testing selecting and moving
    # Get one
    units = parse_obs.get_units(nObs, alliance = 3)
    for unit in units:
      x = unit['pos']['x']
      y = unit['pos']['y']

      print('Alliance 3 Unit at:', self._translate_coord.world_to_minimap(x, y))

    for y, row in enumerate(obs.observation['minimap'][5]):
      for x, pt in enumerate(row):
        if pt != 0:
          print('(',x,', ',y,') = ',pt)

    # Ha
    print('')
    print('')

    # Testing Screen Translation
    print('#========================================================#')
    print('#               Testing Screen Translation               #')
    print('#========================================================#')
    units = parse_obs.get_units(nObs, alliance = 1)
    for unit in units:
      x = unit['pos']['x']
      y = unit['pos']['y']

      print('Alliance 1 Unit at:', self._translate_coord.world_to_screen(x, y))

    units = parse_obs.get_units(nObs, alliance = 3)
    for unit in units:
      x = unit['pos']['x']
      y = unit['pos']['y']

      print('Alliance 3 Unit at:', self._translate_coord.world_to_screen(x, y))

    for y, row in enumerate(obs.observation['screen'][5]):
      for x, v   in enumerate(row):
        pt = get_object(obs.observation['screen'][5], x, y)
        if pt:
          print('(', pt[0], ', ', pt[1], ') = ', v)

    # Ha
    print('')
    print('')

#    if units[1]['is_selected'] == True:									#Check if a unit is selected
#      return actions.FunctionCall(_MOVE_SCREEN, [_NOT_QUEUED, [20, 20]])	#If a unit is selected, move it
#    return actions.FunctionCall(_SELECT_POINT, [_NOT_QUEUED, target])		#Select a unit if one is not selected
    # Stop
    exit()

    return actions.FunctionCall(_NO_OP, [])
