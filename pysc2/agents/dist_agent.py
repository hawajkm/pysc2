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
    units = parse_obs.get_units(nObs, alliance = 1)				#get units
    crystals = parse_obs.get_units(nObs, alliance = 3)			#get crystals 
    numunits = len(units)										#get number of units
    numcrystals = len(crystals)									#get number of crystals

    print("number of units")
    print(numunits)
    print('')

    print("number of crystals")
    print(numcrystals)
    print('')

#    myunits = copy.deepcopy(units)					#create own version of units so that I can change locations and preserve originals
#    print(myunits)	
#    mycrystals = copy.deepcopy(crystals)			#create own version of crystals so that I can change locations and preserve originals 
    for unit in units:								#loop through individual units to translate position 
      x = unit['pos']['x']							#grab original x position
      y = unit['pos']['y']							#grab original y position
      (x, y) = self._translate_coord.world_to_screen(x, y)					#convert to previous x & y positions to new positions
      unit['pos']['x'] = x 							#set x to new x position
      unit['pos']['y'] = y							#set y to new position
      unit['is_assigned'] = False					#add field to unit called is assigned
      unit['is_active'] = False						#add field to unit called is active

    for crystal in crystals:						#loop through individual crystals
      x = crystal['pos']['x']
      y = crystal['pos']['y']
      (x, y) = self._translate_coord.world_to_screen(x, y)
      crystal['pos']['x'] = x 
      crystal['pos']['y'] = y
      crystal['is_assigned'] = False
      crystal['is_collected'] = False
      crystal['bid_pending'] = False

    print("Units")
    print(units)
    print("Crystals")
    print(crystals)
	
    count = 0
    numassigned = 0
#    dist = 0
#    dist2 = 0
#    numg = 0
    c = 0
    numpending = 0
    crystalcount = 0
#    crystalbidlist = []
#    bid = {}
    if numunits < numcrystals:
      count = numunits
    else:
      count = numcrystals

#    for crystalcount in range(0, numcrystals - 1):
#      crystalbidlist.append([])

	  
    while (numassigned < count):
#      i = 0
      crystalbidlist = []
      for crystalcount in range(0, numcrystals):
        crystalbidlist.append([])
        
      for unit in units:
#        print(crystalbidlist)
#        tempunits = copy.deepcopy(units)
#        tempunits.pop(i)
        if unit['is_assigned'] == True:
          print("Already assigned")
        else:
          radius = 120
          c = 0
#          for crystal in crystals:
#            crystal['bid_pending'] = False
#          numpending = 0
          for crystal in crystals:
            if(crystal['bid_pending'] == True):
              print("Already bid on")
            else:
              xdist = unit['pos']['x'] - crystal['pos']['x']	#find x distance difference
              ydist = unit['pos']['y'] - crystal['pos']['y']	#find y distance difference
              dist = xdist*xdist + ydist*ydist				#find difference of square of distances
              dist = math.sqrt(dist)							#take square root (thus computing the distance)
              bid = {}
              if dist <= radius:
                bid = {'crystal' : crystal['tag'], 'bid' : dist, 'unit' :unit['tag'], 'crystal_assigned' : False, 'unit_assigned' : False, 'crystalpos' : crystal['pos'], 'unitpos' : unit['pos'], 'is_collected' : crystal['is_collected'], 'unit_selected' : unit['is_selected']}
#                bid[crystal['tag']] = {'bid' : dist, 'unit' : unit['tag']}
                print("original bid")
                print(bid)
#                crystal['tag'] = '0000'
#                print("change made to tag of crystal")
#                print(bid)
                crystalbidlist[c].append(bid.copy())
#                crystal['bid_pending'] = True
            c = c + 1
#	  i = 0
      print("crystalbidlist")
      print(crystalbidlist)
      assignmentlist = []
	  
      for crystalbid in crystalbidlist:
#        print("Length of crystal bid")
#        print(len(crystalbid))
        i = 0
        if(crystalbid[i]['crystal_assigned'] == True):
          print("Already assigned")
        
#        elif(crystalbid[i]['crystal_assigned'] == False):
#          if(crystalbid[i]['unit_assigned'] == True
#			print("Unit already assigned")
		
        else:
          while(i < len(crystalbid)):
            tempbid = copy.deepcopy(crystalbid)
            tempbid.pop(i)
            print("tempbid")
            print(tempbid)
            j = 0
            numg = 0
            while(j < len(crystalbid) - 1):
              if(crystalbid[i]['crystal_assigned'] == True):
                break
              if(crystalbid[i]['unit_assigned'] == True):
                break
              if(tempbid[j]['unit_assigned'] == True):
#                j = j + 1
                numg = numg + 1
#                break
              elif(crystalbid[i]['bid'] < tempbid[j]['bid']):
                numg = numg + 1
#              else:
#                break
              print("numg")
              print(numg)
              if(numg == len(crystalbid) - 1):
                assignment = {}
                assignment = {'unit' : crystalbid[i]['unit'], 'crystal' : crystalbid[i]['crystal'], 'bid' : crystalbid[i]['bid'], 'crystalpos' : crystalbid[i]['crystalpos'], 'unitpos' : crystalbid[i]['unitpos'], 'unit_selected' : crystalbid[i]['unit_selected'], 'crystalcollected' : crystalbid[i]['is_collected'], 'unit_active' : False}
                assignmentlist.append(assignment.copy())
                print("assignmentlist")
                print(assignmentlist)
                crystalbid[i]['crystal_assigned'] = True
                numassigned = numassigned + 1
#                for individual in crystalbid:
#                  individual['crystal_assigned'] = True
                for bidcrystal in crystalbidlist:
                  for individual in bidcrystal:
                    if(individual['unit'] == crystalbid[i]['unit']):
                      individual['unit_assigned'] = True
                    if(individual['crystal'] == crystalbid[i]['crystal']):
                      individual['crystal_assigned'] = True
#                    else:
#                      individual['unit_assigned'] = False
                  
                break
              j = j + 1
            i = i + 1				
        #write code for random walk here
#		if(numassigned < count):
#      print(crystalbidlist)
#      print("numassigned")
#      print(numassigned)
      print("assignmentlist")
      print(assignmentlist)
#      exit()

          
    print("assignmentlist")
    print(assignmentlist)    
#    for assignmentmade in assignmentlist:
#      print(assignmentmade)
#      if(assignmentmade['unit_selected'] == False and assignmentmade['unit_active'] == False):
#        x = assignmentmade['unitpos']['x']
#        y = assignmentmade['unitpos']['y']
#        target = (x, y)
#        return actions.FunctionCall(_SELECT_POINT, [_NOT_QUEUED, target])
#      elif(assignmentmade['unit_selected'] == True and assignmentmade['unit_active'] == False):
#        assignmentmade['unit_active'] == True
#        x = assignmentmade['crystalpos']['x']
#        y = assignmentmade['crystalpos']['y']
#        target = (x, y)
#        return actions.FunctionCall(_MOVE_SCREEN, [_NOT_QUEUED, target])
#      elif(assignmentmade['unit_active'] == True):
#        pass
#    if units[1]['is_selected'] == True:									#Check if a unit is selected
#      return actions.FunctionCall(_MOVE_SCREEN, [_NOT_QUEUED, [20, 20]])	#If a unit is selected, move it
#    return actions.FunctionCall(_SELECT_POINT, [_NOT_QUEUED, target])		#Select a unit if one is not selected
    # Stop
    exit()

    return actions.FunctionCall(_NO_OP, [])
