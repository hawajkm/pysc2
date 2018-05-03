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

# States
_ASSIGNED   = 0
_SELECTED   = 1
_MOVED      = 2
_UNASSIGNED = 3

class CollectMinerals(base_agent.BaseAgent):
  def __init__(self):
    super(CollectMinerals, self).__init__()
    #self.minerals = {}    # Found minerals - state and position info
    #self.scvs = {}        # Found scvs -  position info
    #self.scv_states = {}  # SCV states - assigned mineral, position, state
    #self.scv_keys = None  # List of SCV tags, to be iterated through
    #self.curr_scv = -1    # Current SCV of step
    #self.done_initializing = False

  def reset(self):
    super(CollectMinerals, self).reset()
    print("RESET")
    self.minerals = {}    # Found minerals - state and position info
    self.found_minerals = {}    # Found minerals - state and position info
    self.scvs = {}        # Found scvs -  position info
    self.scv_states = {}  # SCV states - assigned mineral, position, state
    self.scv_keys = None  # List of SCV tags, to be iterated through
    self.curr_scv = -1    # Current SCV of step
    self.done_initializing = False

  # Find the locations of each mineral on screen
  # Save position and intialize each minerals state to unassigned
  def find_minerals(self,rObs):
    self.found_minerals.clear()
    for unit in rObs['observation']['raw_data']['units']:
      if (unit['unit_type'] == _MINERAL_SHARD):
        x = unit['pos']['x']
        y = unit['pos']['y']
        pt = self._translate_coord.world_to_screen(x,y)
        pos = {}
        pos['x'] = pt.x
        pos['y'] = pt.y
        self.found_minerals[unit['tag']] = {'pos':pos}  
  
    print("MINERALS FOUND:")
    print(json.dumps(self.found_minerals, indent=4, sort_keys=True))  

  def init_mineral_dict(self):
    for key, val in self.found_minerals.items():
      pos = val['pos']
      self.minerals[key] = {'pos':pos, 'state':_UNASSIGNED}  

  # Find the locations of each SCV screen
  # Save position
  def find_scvs(self,rObs):
    # Initialize dictionary of SCVS, with position, state, and assigned_mineral
    for unit in rObs['observation']['raw_data']['units']:
      if (unit['unit_type'] == _SCV):
        x = unit['pos']['x']
        y = unit['pos']['y']
        pt = self._translate_coord.world_to_screen(x,y)
        pos = {}
        pos['x'] = pt.x
        pos['y'] = pt.y
        self.scvs[unit['tag']] = {'pos': pos}
  
  # Initialize dictionary to hold scv states
  # Fields: position, assigned_mineral, state
  def init_scv_dict(self):
    for key, val in self.scvs.items():
      pos = val['pos']
      self.scv_states[key] = {'pos': pos, 'state': _UNASSIGNED, 'assigned_mineral': {'tag':None, 'x':None, 'y':None}}
    #print(json.dumps(self.scv_states, indent=4, sort_keys=True))  
    # Get SCV keys in list
    self.scv_keys = list(self.scv_states.keys())

  # Update the positions of all SCVs with current location
  def update_scv_loc(self,rObs):
    for key in self.scvs:
      self.scv_states[key]['pos'] = self.scvs[key]['pos']

  # Assign all unassigned SCVs
  def assign_all(self): 
      for scv_tag,val in self.scv_states.items():
        if val['state'] == _UNASSIGNED:
          self.assign(scv_tag)

  # Assign closest mineral to self.scv[tag]
  def assign(self,tag):
    print("ASSIGNING")
    print("MINERALS - BEFORE:")
    print(json.dumps(self.minerals, indent=4, sort_keys=True))  
    # Find first unassigned mineral to set as initial closest
    m_keys = list(self.minerals.keys())
    first_min_tag = m_keys[0]
    for m_tag in m_keys:
      if self.minerals[m_tag]['state'] == _UNASSIGNED:
        first_min_tag = m_tag
        break
    # Initialize closest mineral
    scv_pos = self.scv_states[tag]['pos']
    scv_x = scv_pos['x']
    scv_y = scv_pos['y']
    min_x = self.minerals[first_min_tag]['pos']['x']
    min_y = self.minerals[first_min_tag]['pos']['y']
    distance = math.pow(scv_x - min_x, 2) + math.pow(scv_y - min_y, 2)
    closest_mineral_tag = first_min_tag
    closest_mineral_dist = distance
    
    # Find closest mineral
    for mineral_tag in self.minerals:
      if self.minerals[mineral_tag]['state'] == _UNASSIGNED:
        scv_x = scv_pos['x']
        scv_y = scv_pos['y']
        min_x = self.minerals[mineral_tag]['pos']['x']
        min_y = self.minerals[mineral_tag]['pos']['y']
        distance = math.pow(scv_x - min_x, 2) + math.pow(scv_y - min_y, 2)
        if (distance < closest_mineral_dist):
          closest_mineral_tag = mineral_tag
          closest_mineral_dist = distance
    
    # Update 'assigned_mineral' in scv_states
    x = self.minerals[closest_mineral_tag]['pos']['x']
    y = self.minerals[closest_mineral_tag]['pos']['y']
    self.scv_states[tag]['assigned_mineral'] = {'tag':closest_mineral_tag,'x':x, 'y':y}
    self.scv_states[tag]['state'] = _ASSIGNED

    # Update state of mineral to assigned
    self.minerals[closest_mineral_tag]['state'] = _ASSIGNED
      
    print("ASSIGNMENTS:")
    print(json.dumps(self.scv_states, indent=4, sort_keys=True))
    print("MINERALS - AFTER:")
    print(json.dumps(self.minerals, indent=4, sort_keys=True))  

  def step(self,oObs,rObs, game_info):
    super(CollectMinerals,self).step(oObs)

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
      self.find_scvs(rObs)
      self.find_minerals(rObs)    
      self.init_mineral_dict()
      self.init_scv_dict()
      self.done_initializing = True
      action = _NOOP

    # Main action loop
    else:
      # Update SCV locations
      self.find_scvs(rObs)
      self.update_scv_loc(rObs)

      # Update minerals
      self.find_minerals(rObs)

      # Check to see which SCVs have collected minerals
      # Set their states to _UNASSIGNED
      for key, val in self.scv_states.items():
        tag_id = val['assigned_mineral']['tag']
        if not tag_id in self.found_minerals:
          self.scv_states[key]['state'] = _UNASSIGNED
      self.assign_all() 
      # Assign any unassigned SCVs
      
      # Iterate through all SCVs
      # If current SCV is selected, do not toggle SCV
      if (self.scv_states[self.scv_keys[self.curr_scv]]['state'] == _SELECTED):
        self.curr_scv = self.curr_scv
      elif (self.curr_scv < len(self.scv_keys)-1):
        self.curr_scv += 1
      else:
        self.curr_scv = 0

      # Set current SCV
      scv_tag = self.scv_keys[self.curr_scv]
      scv_val = self.scv_states[scv_tag]
      print("\nCURR SCV: ",scv_tag)
      if self.scv_states[scv_tag]['state'] == _ASSIGNED:
        # Select SCV
        x = self.scv_states[scv_tag]['pos']['x']
        y = self.scv_states[scv_tag]['pos']['y']
        target = [x, y]
        print("SELECT TARGET: ", target)
        #for i,row in enumerate(oObs.observation['screen'][5]):
        #  for j,p in enumerate(row):
        #    if p != 0:
        #      print("(",j,i,")", " val: ",p)
        #print(json.dumps(rObs['observation']['raw_data']['units'], indent=4, sort_keys=True))
        #print(json.dumps(rObs, indent=4, sort_keys=True))
        self.scv_states[scv_tag]['state'] = _SELECTED
        action = _SELECT_POINT
      elif self.scv_states[scv_tag]['state'] == _SELECTED:
        # Move SCV to assigned mineral
        x = (self.scv_states[scv_tag]['assigned_mineral']['x'])
        y = (self.scv_states[scv_tag]['assigned_mineral']['y'])
        target = [x, y]
        print("MOVE TARGET: ", target)
        self.scv_states[scv_tag]['state'] = _MOVED
        action = _MOVE_SCREEN
      else:
        action = _NOOP    

    # Execute action
    if (action == _SELECT_POINT):
      return actions.FunctionCall(_SELECT_POINT, [_NOT_QUEUED, target])
    if (action == _MOVE_SCREEN):
      return actions.FunctionCall(_MOVE_SCREEN, [_NOT_QUEUED, target])
    else:
      return actions.FunctionCall(_NOOP, [])

