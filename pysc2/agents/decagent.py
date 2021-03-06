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
import random

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
import random
from operator import itemgetter

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



class DecentralizedAgent(base_agent.BaseAgent):
  def __init__(self):
    super(DecentralizedAgent, self).__init__()
      
  def reset(self):
    super(DecentralizedAgent, self).reset()
    print("Reset")
    self.crystals = []
    self.scvs = []
    self.scvbidlist = []
    self.assignmentlist = []
    self.crystalassignstat = []
    self.crystalbids = {}
    self.numcrystals = 0
    self.numscvs = 0
    self.numassigned = 0
    self.radius = 120
    self.randomscv = 0
    self.commcount = 0
    self.equalcycles = 5
    self.done_initializing = False
    
  def find_minerals(self, nObs):
    for unit in parse_obs.get_units(nObs, alliance = 3):
      x = unit['pos']['x']
      y = unit['pos']['y']
      pt = self._translate_coord.world_to_screen(x, y)
      pos = {}
      pos['x'] = pt.x
      pos['y'] = pt.y
      crystal = {'crystal_tag' : unit['tag'], 'pos' : pos, 'crystal_assigned' : False, 'crystalprice' : 0}
      self.crystals.append(crystal)
        
        
  def find_scvs(self, nObs):
    units = parse_obs.get_units(nObs, alliance = 1)
    for unit in units:
      x = unit['pos']['x']
      y = unit['pos']['y']
      pt = self._translate_coord.world_to_screen(x, y)
      pos = {}
      pos['x'] = pt.x
      pos['y'] = pt.y
      scv = {'scv_tag' : unit['tag'], 'pos' : pos, 'scv_assigned' : False, 'is_active' : False, 'is_selected' : False, 'crystalnear' : False, 'profit' : 0}
      self.scvs.append(scv)
        
  def find_counts(self):
    self.numcrystals = len(self.crystals)
    self.numscvs = len(self.scvs)
    

  def crystals_near(self):
    for scv in self.scvs:
      for crystal in self.crystals:
        if(crystal['crystal_assigned'] ==  True):
          pass
        else:
          xdist = scv['pos']['x'] - crystal['pos']['y']
          ydist = scv['pos']['y'] - crystal['pos']['y']
          dist = xdist*xdist + ydist*ydist
          dist = math.sqrt(dist)
          if dist <= self.radius:
            scv['crystalnear'] = True
            break
          else:
            pass
              
  def initialize_scvbidlist(self):
    self.scvbidlist = []
    for scvcount in range(0, self.numscvs):
      self.scvbidlist.append([])
      
  def initcrystalbids(self):
    for crystal in self.crystals:
      self.crystalbids[crystal['crystal_tag']] = []
  
  def createinitialbidlist(self):
    s = 0
    for scv in self.scvs:
      if(scv['is_active'] == True):
        pass
      else:
        for crystal in self.crystals:
          if(crystal['crystal_assigned'] == True):
            pass
          else:
            xdist = scv['pos']['x'] - crystal['pos']['x']
            ydist = scv['pos']['y'] - crystal['pos']['y']
            dist = xdist*xdist + ydist*ydist
            dist = math.sqrt(dist)
            bid = {}              
            if dist <= self.radius:
              value =  1/dist
              profit = 1/dist
              bid = {'crystal' : crystal['crystal_tag'], 'profit' : profit, 'value' : value, 'bid' : 0, 'scv' : scv['scv_tag'], 'crystal_assigned' : crystal['crystal_assigned'], 'crystalpos' : crystal['pos'], 'scvpos' : scv['pos'], 'is_selected' : scv['is_selected'], 'scv_active' : scv['is_active'], 'crystalprice' : crystal['crystalprice']}     
              self.scvbidlist[s].append(bid)
      s = s + 1                
              
  
  def sortbidlist(self):
    for scvbids in self.scvbidlist:
      scvbids = sorted(scvbids, key = itemgetter('profit'), reverse = True)
      
  
  def updatescvprofit(self):
    for scvbids in self.scvbidlist:
      for bid in scvbids:
        bid['profit'] = bid['value'] - bid['crystalprice']
        if(bid['profit'] < 0 ):
          bid['profit'] = 0
  
  # def updatescvbids(self):
    # for scvbids in self.scvbidlist:
      # for i in range(len(scvbids)):
        # scvbids[i]['bid'] = scvbids[i]['profit'] - scvbids[i + 1]['profit']
        
  def updatescvbids(self):
    for scvbids in self.scvbidlist:
      if(len(scvbids) > 1):
        scvbids[0]['bid'] = scvbids[0]['profit'] - scvbids[1]['profit']
      elif(len(scvbids) == 1):
        scvbids[0]['bid'] = scvbids[0]['profit']
      else:
        pass

        
        
    
  def market(self):
    iterations = 0
    while(iterations < self.equalcycles):
      self.sortbidlist()
      self.updatescvprofit()
      self.sortbidlist()
      self.updatescvbids()
      self.sortbidlist()
      print(self.scvbidlist)
      self.initcrystalbids()
      
      for scvbids in self.scvbidlist:
        crystalbid = {'scv_tag' : scvbids[0]['scv'], 'bid' : scvbids[0]['bid']}
        self.crystalbids[scvbids[0]['crystal']].append(crystalbid)
      
      for crystaltag in self.crystalbids.keys():
        self.crystalbids[crystaltag] = sorted(self.crystalbids[crystaltag], key = itemgetter('bid'), reverse = True)
    
#    for crystaltag in crystalbids.keys():
#      for bid in crystalbids[crystaltag]:
#        if (bid['bid'] == 0):
#          zerocount = zerocount + 1

      # for crystaltag in crystalbids.keys():
        # for scvbids in self.scvbidlist:
          # for bid in scvbids:
            # if(bid('crystal') == crystaltag):
              
      currentprices = {}
      for scvbids in self.scvbidlist:
        for bid in scvbids:
          for crystaltag in self.crystalbids.keys():
#            print(self.scvbidlist)
            if(bid['crystal'] == crystaltag):
              bid['crystalprice'] = bid['crystalprice'] + self.crystalbids[crystaltag][0]['bid']
              currentprices[crystaltag] = bid['crystalprice']
              
      if(runcount == 0):
        pass
      else:
        for crystaltag in self.crystalbids.keys():
          if(savedprices[crystaltag] == currentprices[crystaltag]):
            tempeqcount = tempeqcount + 1
          else:
            pass
        if(tempeqcount == len(currentprices)):
          iterations = iterations + 1
        else:
          iterations = 0
      
      savedprices = {}
      for scvbids in self.scvbidlist:
        for bid in scvbids:
          savedprices[bid['crystal']] = bid['crystalprice']
          
  

  
    # def createbidlist(self):
      # for scv in self.scvs:
        # s = 0
        # print("Checked")
        # for crystal in self.crystals:
          # if(crystal['crystal_assigned'] == True):
            # pass
          # else:
            # xdist = scv['pos']['x'] - crystal['pos']['x']
            # ydist = scv['pos']['y'] - crystal['pos']['y']
            # dist = xdist*xdist + ydist*ydist
            # dist = math.sqrt(dist)
            # bid = {}
            # if dist <= self.radius:
              # bid = {'crystal' : crystal['crystal_tag'], 'bid' : dist, 'scv' : scv['scv_tag'], 'crystal_assigned' : crystal['crystal_assigned'], 'crystalpos' : crystal['pos'], 'scvpos' : scv['pos'], 'is_selected' : scv['is_selected'], 'scv_active' : scv['is_active']}
              # self.scvbidlist[s].append(bid)
        # s = s + 1
      
      
  # def assign(self):
    # i = 0
    # for scvbids in self.scvbidlist
      # if(scvbids[i]['scv_active'] == True):
        # pass
      # else:

  def step(self,oObs, nObs, game_info):
    super(DecentralizedAgent,self).step(oObs)

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
#      self.createinitialbidlist()
#      self.initcrystalbids()
      self.done_initializing = True
      action = _NOOP
      return actions.FunctionCall(_NOOP, [])
	  
    # Main action loop
    else:
      # self.find_counts()
      # self.initialize_crystalbidlist()
      # self.updateposition(nObs)
      # self.find_minerals(nObs)
      # self.find_counts()
      # self.initialize_crystalbidlist()
      # self.createbidlist()
      self.initcrystalbids()
      self.initialize_scvbidlist()
      self.createinitialbidlist()
      self.market()
      exit()
	  
	  
      # for crystalbid in self.crystalbidlist:
        # if(len(crystalbid) == 1):
          # pass
        # else:
          # self.commcount = self.commcount + len(crystalbid)      