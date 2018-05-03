from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from pysc2.agents import base_agent
from pysc2.lib import actions
from pysc2.lib import features
from pysc2.lib import point
from pysc2.lib import translate_coord
from pysc2.lib import parse_obs

import time
import numpy as np
import json
import math
import copy

# Functions
_SELECT_POINT = actions.FUNCTIONS.select_point.id
_NOOP = actions.FUNCTIONS.no_op.id
_SELECT_UNIT = actions.FUNCTIONS.select_unit.id
_MOVE_SCREEN = actions.FUNCTIONS.Move_screen.id
_MOVE_MINIMAP = actions.FUNCTIONS.Move_minimap.id
_MOVE_CAM = actions.FUNCTIONS.move_camera.id

# Observation features
_PLAYER_RELATIVE = features.SCREEN_FEATURES.player_relative.index
_UNIT_TYPE = features.SCREEN_FEATURES.unit_type.index

# Unit IDs
_TERRAN_MARINE = 48
_SCV           = 45
_MINERAL_SHARD = 1680

# Parameters
_PLAYER_SELF = 1
_NOT_QUEUED = [0]
_QUEUED = [1]

# Mineral states
_ASSIGNED   = 0
_SELECTED   = 1
_MOVED      = 2

_UNASSIGNED = 1

class DistributedAgent(base_agent.BaseAgent):
  def __init__(self):
    super(DistributedAgent, self).__init__()
    #self.minerals = {}    # Found minerals - state and position info
    #self.scvs = {}        # Found scvs -  position info
    #self.scv_states = {}  # SCV states - assigned mineral, position, state
    #self.scv_keys = None  # List of SCV tags, to be iterated through
    #self.curr_scv = -1    # Current SCV of step
    #self.done_initializing = False

  def reset(self):
    super(DistributedAgent, self).reset()
    print("RESET")
#    self.crystals = {}    # Found crystals - state and position info
#    self.scvs = {}        # Found scvs -  position info
    self.crystals = []
    self.scvs = []
    self.crystalbidlist = []
    self.assignmentlist = []
    self.numcrystals = 0	  # Number of crystals
    self.numscvs = 0
    self.numassigned = 0
    self.radius = 120
#    self.scv_states = {}  # SCV states - assigned mineral, position, state
#    self.scv_keys = None  # List of SCV tags, to be iterated through
#    self.curr_scv = -1    # Current SCV of step
    self.done_initializing = False

  # Find the locations of each mineral on screen
  # Save position and intialize each minerals state to unassigned
  def find_minerals(self, nObs):
    for unit in parse_obs.get_units(nObs, alliance = 3):
#      if (unit['unit_type'] == _MINERAL_SHARD):
      x = unit['pos']['x']
      y = unit['pos']['y']
      pt = self._translate_coord.world_to_screen(x,y)
      pos = {}
      pos['x'] = pt.x
      pos['y'] = pt.y
#        self.minerals[unit['tag']] = {'pos':pos, 'state':_UNASSIGNED}
      crystal = {'crystal_tag' : unit['tag'], 'pos' : pos, 'crystal_assigned' : False}
      self.crystals.append(crystal)
  
#    print("MINERALS FOUND:")
#    print(json.dumps(self.minerals, indent=4, sort_keys=True))  
	
	
  # Find the locations of each SCV screen
  # Save position
  def find_scvs(self, nObs):
    # Initialize dictionary of SCVS, with position, state, and assigned_mineral
    units = parse_obs.get_units(nObs, alliance = 1)
    for unit in units:
#      if (unit['unit_type'] == _SCV):
      x = unit['pos']['x']
      y = unit['pos']['y']
      pt = self._translate_coord.world_to_screen(x,y)
      pos = {}
      pos['x'] = pt.x
      pos['y'] = pt.y
#        self.scvs[unit['tag']] = {'pos': pos}
      scv = {'scv_tag' : unit['tag'], 'pos' : pos, 'scv_assigned' : False, 'is_active': False, 'is_selected' : False}
      self.scvs.append(scv)

  def find_counts(self):
    self.numcrystals = len(self.crystals)
    self.numscvs = len(self.scvs)
		
  def initialize_crystalbidlist(self):
    for crystalcount in range(0, self.numcrystals):
      self.crystalbidlist.append([])
	  
  def createbidlist(self):
    for scv in self.scvs:
      if(scv['scv_assigned'] == True):
        print("scv assigned")
      else:
        c = 0
        for crystal in self.crystals:
          xdist = scv['pos']['x'] - crystal['pos']['x']
          ydist = scv['pos']['y'] - crystal['pos']['y']
          dist = xdist*xdist + ydist*ydist
          dist = math.sqrt(dist)
          bid = {}
          if dist <= self.radius:
            bid = {'crystal' : crystal['crystal_tag'], 'bid' : dist, 'scv' : scv['scv_tag'], 'crystal_assigned' : crystal['crystal_assigned'], 'scv_assigned' : scv['scv_assigned'], 'crystalpos' : crystal['pos'], 'scvpos' : scv['pos'], 'is_selected' : scv['is_selected'], 'scv_active' : scv['is_active']}
            self.crystalbidlist[c].append(bid)
          c = c + 1
		  
		  
  def assign(self):
    for crystalbid in self.crystalbidlist:
      i = 0
      while(i < len(crystalbid)):
        tempbid = copy.deepcopy(crystalbid)
        tempbid.pop(i)
        j = 0
        numg = 0
        while(j < len(crystalbid) - 1):
          if(crystalbid[i]['crystal_assigned'] == True):
            break
          if(crystalbid[i]['scv_assigned'] == True):
            break
          if(tempbid[j]['scv_assigned'] == True):
            numg = numg + 1
          elif(crystalbid[i]['bid'] < tempbid[j]['bid']):
            numg = numg + 1
			
          if(numg == len(crystalbid) - 1):
            assignment = {}
            assignment = {'scv' : crystalbid[i]['scv'], 'crystal' : crystalbid[i]['crystal'], 'bid' : crystalbid[i]['bid'], 'crystalpos' : crystalbid[i]['crystalpos'], 'scvpos' : crystalbid[i]['scvpos'], 'is_selected' : crystalbid[i]['is_selected'], 'scv_active' : crystalbid[i]['scv_active']}
            self.assignmentlist.append(assignment)
            crystalbid[i]['crystal_assigned'] = True
            self.numassigned = self.numassigned + 1
            for bidcrystal in self.crystalbidlist:
              for individual in bidcrystal:
                if(individual['scv'] == crystalbid[i]['scv']):
                  individual['scv_assigned'] = True
                if(individual['crystal'] == crystalbid[i]['crystal']):
                  individual['crystal_assigned'] = True
            
            for scv in self.scvs:
              if(scv['scv_tag'] == crystalbid[i]['scv']):
                scv['scv_assigned'] = True
            break
          j = j + 1
        i = i + 1
	

  def step(self,oObs, nObs, game_info):
    super(DistributedAgent,self).step(oObs)

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

    # Initialize
    if not self.done_initializing:
      print("INITIALIZING")
      self.find_scvs(nObs)
      self.find_minerals(nObs)
      self.find_counts()
      self.initialize_crystalbidlist()	  
      #self.init_scv_dict()
      # For every scv in self.scv_states, assign a mineral
      #for scv_tag in self.scv_states:
      #  self.assign(scv_tag)
      self.done_initializing = True
      #self.createbidlist()
      action = _NOOP
      return actions.FunctionCall(_NOOP, [])
	  
    # Main action loop
    else:
      self.createbidlist()
#      print("initial crystal bid list")
#      print(self.crystalbidlist)
      self.assign()
#      print("list of assignments")
#      print(self.assignmentlist)
#      print("crystal bid list after assignments are made")
 #     print(self.crystalbidlist)
	
	
    for assignmentmade in self.assignmentlist:
      if(assignmentmade['is_selected'] == False and assignmentmade['scv_active'] == False):
        x = assignmentmade['scvpos']['x']
        y = assignmentmade['scvpos']['y']
        target = (x, y)
        print(self.scvs)
        assignmentmade['is_selected'] = True
        return actions.FunctionCall(_SELECT_POINT, [_NOT_QUEUED, target])
      elif(assignmentmade['is_selected'] == True and assignmentmade['scv_active'] == False):
        x = assignmentmade['crystalpos']['x']
        y = assignmentmade['crystalpos']['y']
        target = (x, y)
        assignmentmade['scv_active'] = True
        print("scvs")
        print(self.scvs)
        return actions.FunctionCall(_MOVE_SCREEN, [_NOT_QUEUED, target])
      elif(assignmentmade['scv_active'] == True):
        continue
    
    return actions.FunctionCall(_NOOP, [])

