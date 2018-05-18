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
    self.initial_crystal_list = []
    self.collected_crystals = []
    self.initial_crystal_count = 0
    self.numcrystals = 0	  # Number of crystals
    self.reset_state_count = 0
    self.numscvs = 0
    self.numassigned = 0
    self.numcollected = 0
    self.radius = 20
    self.randomscv = 0
    self.new_assignment_count = 0
    self.rwalktargs = []
    self.rwalkscv = 0
    self.rwalk_reset_count = 0
    self.commcount = 0
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
      x = unit['pos']['x']
      y = unit['pos']['y']
      pt = self._translate_coord.world_to_screen(x,y)
      pos = {}
      pos['x'] = pt.x
      pos['y'] = pt.y
      scv = {'scv_tag' : unit['tag'], 'pos' : pos, 'scv_assigned' : False, 'is_active': False, 'is_active_rwalk' : False, 'is_selected' : False, 'is_selected_rwalk' : False, 'rwalktarg' : (0, 0), 'rwalkcount' : 0}
      self.scvs.append(scv)
  
  def find_initial_counts(self):
    self.initial_crystal_count = len(self.crystals)
    self.numscvs = len(self.scvs)
    
  def update_crystal_count(self):
    self.numcrystals = len(self.crystals)
    
    
  def find_num_collected(self):
    self.numcollected = self.initial_crystal_count - self.numcrystals
    
  def initialize_crystalbidlist(self):
    self.crystalbidlist = []
    for crystalcount in range(0, self.numcrystals):
      self.crystalbidlist.append([])
    
  def init_rwalktargs(self):
    self.rwalktargs = []
    for scvcount in range(0, self.numscvs):
      self.rwalktargs.append([])
      
  def create_initial_crystal_list(self):
    self.initial_crystal_list = copy.deepcopy(self.crystals)
    
    
  def update_crystals(self, nObs):
    crystals = []
    for unit in parse_obs.get_units(nObs, alliance = 3):
      for crystal in self.crystals:
        if(crystal['crystal_tag'] == unit['tag']):
          crystals.append(crystal)
    self.crystals = crystals
    
  def update_collected_crystals(self):
    self.collected_crystals = []
    for initcrystal in self.initial_crystal_list:
      cryscount = 0
      for currcrystal in self.crystals:
        if(initcrystal['crystal_tag'] != currcrystal['crystal_tag']):
          cryscount = cryscount + 1
      if(cryscount == len(self.crystals)):
        self.collected_crystals.append(initcrystal)         

  def updateposition(self, nObs):
    units = parse_obs.get_units(nObs, alliance = 1) 
    for unit in units:
      for scv in self.scvs:
        if(scv['scv_tag'] == unit['tag']):
          x = unit['pos']['x']
          y = unit['pos']['y']
          pt = self._translate_coord.world_to_screen(x,y)
          pos = {}
          pos['x'] = pt.x
          pos['y'] = pt.y
          scv['pos'] = pos        
          

        
  def createbidlist(self, nObs):
    for scv in self.scvs:
      if(scv['scv_assigned'] == True):  #comment back in
	    continue
#        print("scv assigned")
#      if(crystal['crystal_assigned'] == True):
#        pass
#      elif(scv['is_active'] == True): #put back in as elif
#        continue
      elif(scv['is_active_rwalk'] == True):
        continue
      else:
        c = 0
#        print("Checked")
        for crystal in self.crystals:
          if(crystal['crystal_assigned'] == True):
            continue
          if(True):
#            print("right here")
            self.updateposition(nObs)
            xdist = scv['pos']['x'] - crystal['pos']['x']
            ydist = scv['pos']['y'] - crystal['pos']['y']
            dist = xdist*xdist + ydist*ydist
            dist = math.sqrt(dist)
            bid = {}
            if dist <= self.radius:
#              print("right here")
              bid = {'crystal' : crystal['crystal_tag'], 'bid' : dist, 'scv' : scv['scv_tag'], 'crystal_assigned' : crystal['crystal_assigned'], 'scv_assigned' : scv['scv_assigned'], 'crystalpos' : crystal['pos'], 'scvpos' : scv['pos'], 'is_selected' : scv['is_selected'], 'is_selected_rwalk' : scv['is_selected_rwalk'], 'is_active' : scv['is_active'], 'is_active_rwalk' : scv['is_active_rwalk']}
              self.crystalbidlist[c].append(bid)
          c = c + 1

  def update_scv_assign_bids(self):
    for crystalbid in self.crystalbidlist:
      for scvbid in crystalbid:
        for scv in self.scvs:
          if(scvbid['scv'] == scv['scv_tag']):
            scvbid['scv_assigned'] = scv['scv_assigned']
            
  def assign(self):
    for crystalbid in self.crystalbidlist:
#      i = 0
      if(len(crystalbid) == 1):
        if(crystalbid[0]['scv_assigned'] == True):
          continue
        assignment = {}
        assignment = {'scv' : crystalbid[0]['scv'], 'crystal' : crystalbid[0]['crystal'], 'bid' : crystalbid[0]['bid'], 'crystalpos' : crystalbid[0]['crystalpos'], 'scvpos' : crystalbid[0]['scvpos'], 'is_selected' : crystalbid[0]['is_selected'], 'is_selected_rwalk' : crystalbid[0]['is_selected_rwalk'], 'is_active' : crystalbid[0]['is_active'], 'is_active_rwalk' : crystalbid[0]['is_active_rwalk']}
        self.assignmentlist.append(assignment)
        crystalbid[0]['crystal_assigned'] = True
        self.numassigned = self.numassigned + 1
        
        for bidcrystal in self.crystalbidlist:
          for individual in bidcrystal:
            if(individual['scv'] == crystalbid[0]['scv']):
              individual['scv_assigned'] = True
            if(individual['crystal'] == crystalbid[0]['crystal']):
              individual['crystal_assigned'] = True
            
        for scv in self.scvs:
          if(scv['scv_tag'] == crystalbid[0]['scv']):
            scv['scv_assigned'] = True
        for crystal in self.crystals:
          if(crystal['crystal_tag'] == crystalbid[0]['crystal']):
            crystal['crystal_assigned'] = True        
      else:
        i = 0
        while(i < len(crystalbid)):
          if(crystalbid[i]['scv_assigned'] == True):
            i = i + 1
            break
          tempbid = copy.deepcopy(crystalbid)
          tempbid.pop(i)
          j = 0
          numg = 0
#          print("len of crystalbid")
#          print(len(crystalbid))
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
#              assignment = {'scv' : crystalbid[i]['scv'], 'crystal' : crystalbid[i]['crystal'], 'bid' : crystalbid[i]['bid'], 'crystalpos' : crystalbid[i]['crystalpos'], 'scvpos' : crystalbid[i]['scvpos'], 'is_selected' : crystalbid[i]['is_selected'], 'is_active' : crystalbid[i]['is_active']}
              assignment = {'scv' : crystalbid[i]['scv'], 'crystal' : crystalbid[i]['crystal'], 'bid' : crystalbid[i]['bid'], 'crystalpos' : crystalbid[i]['crystalpos'], 'scvpos' : crystalbid[i]['scvpos'], 'is_selected' : crystalbid[i]['is_selected'], 'is_selected_rwalk' : crystalbid[i]['is_selected_rwalk'], 'is_active' : crystalbid[i]['is_active'], 'is_active_rwalk' : crystalbid[i]['is_active_rwalk']}
              self.assignmentlist.append(assignment)
              crystalbid[i]['crystal_assigned'] = True
              self.numassigned = self.numassigned + 1
              for bidcrystal in self.crystalbidlist:
                for individual in bidcrystal:
                  if(individual['scv'] == crystalbid[i]['scv']):
                    individual['scv_assigned'] = True
                  if(individual['crystal'] == crystalbid[i]['crystal']):
                    if(individual['scv_assigned'] == True):
                      continue
                    else:
                      individual['crystal_assigned'] = True
            
              for scv in self.scvs:
                if(scv['scv_tag'] == crystalbid[i]['scv']):
                  scv['scv_assigned'] = True
              for crystal in self.crystals:
                if(crystal['crystal_tag'] == crystalbid[i]['crystal']):
                  crystal['crystal_assigned'] = True
              break
            j = j + 1
          i = i + 1

  def update_assignment_scv_position(self, nObs):
    units = parse_obs.get_units(nObs, alliance = 1)
    for unit in units:
      for assign in self.assignmentlist:
        if(unit['tag'] == assign['scv']):
          x = unit['pos']['x']
          y = unit['pos']['y']
          pt = self._translate_coord.world_to_screen(x,y)
          pos = {}
          pos['x'] = pt.x
          pos['y'] = pt.y
          assign['scvpos'] = pos  
	
  def remove_misassigned_scvs(self):
    a = 0
    for assignment in self.assignmentlist:
      for collected in self.collected_crystals:
        if(collected['crystal_tag'] == assignment['crystal']):
          assignment['is_active'] = False
          assignment['is_selected'] = False
          assignment['scv_assigned'] = False
          for scv in self.scvs:
            if(scv['scv_tag'] == assignment['scv']):
              scv['is_active'] = False
              scv['is_selected'] = False
              scv['scv_assigned'] = False
          self.assignmentlist.pop(a)
      a = a + 1
      
  def remove_duplicate_assignments(self):
    a = 0
    for assignment in self.assignmentlist:
      tempassign = copy.deepcopy(self.assignmentlist)
      tempassign.pop(a)
      b = 0
      for assign in tempassign:
        if(assign['crystal'] == assignment['crystal']):
          if(assign['bid'] > assignment['bid']):
            assignment['scv_assigned'] = False
            assignment['is_active'] = False
            assignment['is_selected'] = False
            
            for scv in self.scvs:
              if(scv['scv_tag'] == assignment['scv']):
                scv['scv_assigned'] = False
                scv['is_active'] = False
                scv['is_selected'] = False
            self.assignmentlist.pop(a)
      a = a + 1
  def remove_false_assignments(self):
    for scv in self.scvs:
      if(len(self.assignmentlist) == 0):
        scv['is_assigned'] = False
        scv['is_active'] = False
        scv['is_selected'] = False
      else:
        not_in_count = 0
        for assignment in self.assignmentlist:
          if(assignment['scv'] == scv['scv_tag']):
            continue
          else:
            not_in_count = not_in_count + 1
      
        if(not_in_count == len(self.assignmentlist)):
          scv['is_assigned'] = False
          scv['is_active'] = False
          scv['is_selected'] = False
          
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
      self.create_initial_crystal_list()
      self.find_initial_counts()
#      print("count of crystals")
#      print(self.numcrystals)
      self.init_rwalktargs()
#      self.find_counts()
#      self.initialize_crystalbidlist()	  
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
      # self.find_counts()
      # self.initialize_crystalbidlist()
      self.updateposition(nObs)
      self.update_crystals(nObs)
      self.update_collected_crystals()
      print("initial crystal list length")
      print(len(self.initial_crystal_list))
      print("current crystals list length")
      print(len(self.crystals))
      print("collected crystals length")
      print(len(self.collected_crystals))
      print("assignment list")
      print(self.assignmentlist)
      print("length of assignment list")
      print(len(self.assignmentlist))
      self.update_crystal_count()
      self.find_num_collected()
      self.initialize_crystalbidlist()
      self.createbidlist(nObs)
      self.remove_misassigned_scvs()
      self.update_scv_assign_bids()
#      print("crystal bid list")
#      print(self.crystalbidlist)
	  
      for crystalbid in self.crystalbidlist:
        if(len(crystalbid) == 1):
          continue
        else:
          self.commcount = self.commcount + 2*(len(crystalbid)*(len(crystalbid)-1))
	  
	  

      self.assign()
      self.remove_misassigned_scvs()
      self.remove_duplicate_assignments()
      self.remove_false_assignments()
      assignment_count = 0
      for assignmentmade in self.assignmentlist:
        if(assignmentmade['is_selected'] == False and assignmentmade['is_active'] == False):
  #      if(assignmentmade['is_selected'] == False):
          x = assignmentmade['scvpos']['x']
          y = assignmentmade['scvpos']['y']
          target = (x, y)
  #        print(self.scvs)
          assignmentmade['is_selected'] = True
          assignmentmade['is_selected_rwalk'] - False
          assignmentmade['is_active_rwalk'] = False
  #        assignmentmade['is_active'] = False
          for scv in self.scvs:
            if(scv['scv_tag'] == assignmentmade['scv']):
              scv['is_selected'] = True
              scv['is_selected_rwalk'] = False
              scv['is_active_rwalk'] = False
  #            scv['is_active'] = False
          return actions.FunctionCall(_SELECT_POINT, [_NOT_QUEUED, target])
        elif(assignmentmade['is_selected'] == True and assignmentmade['is_active'] == False):
          x = assignmentmade['crystalpos']['x']
          y = assignmentmade['crystalpos']['y']
          target = (x, y)
          assignmentmade['is_active'] = True
          assignmentmade['is_selected_rwalk'] = False
          assignmentmade['is_active_rwalk'] = False
          for scv in self.scvs:
            if(scv['scv_tag'] == assignmentmade['scv']):
              scv['is_active'] = True
              scv['is_selected_rwalk'] = False
              scv['is_active_rwalk'] = False
  #        print("scvs")
  #        print(self.scvs)
          return actions.FunctionCall(_MOVE_SCREEN, [_NOT_QUEUED, target])
        elif(assignmentmade['is_active'] == True):
          self.update_assignment_scv_position(nObs)
          for collected in self.collected_crystals:
            if(collected['crystal_tag'] == assignmentmade['crystal']):
#              print("in here")
              assignmentmade['is_active'] = False
              assignmentmade['is_selected'] = False
              assignmentmade['is_assigned'] = False
              for scv in self.scvs:
                if(scv['scv_tag'] == assignmentmade['scv']):
                  scv['scv_assigned'] = False
                  scv['is_active'] = False
                  scv['is_selected'] = False
              self.assignmentlist.pop(assignment_count)
              self.new_assignment_count = self.new_assignment_count + 1
        assignment_count = assignment_count + 1
          # if((assignmentmade['scvpos']['x'] == assignmentmade['crystalpos']['x'] and assignmentmade['scvpos']['y'] == assignmentmade['crystalpos']['y']) == True):
            # print("I'm here")
            # assignmentmade['is_active'] = False
            # assignmentmade['is_selected'] = False
  # #          self.assignmentlist.pop(assignment_count)
  # #          assignment_count = assignment_count + 1
            # for scv in self.scvs:
              # if(scv['scv_tag'] == assignmentmade['scv']):
                # scv['scv_assigned'] = False
                # scv['is_active'] = False
                # scv['is_selected'] =  False
            # self.assignmentlist.pop(assignment_count)
            # assignment_count = assignment_count + 1
  #        continue


      print("commcount")
      print(self.commcount)


  #    print(self.rwalktargs)
  #    print("numassigned")
  #    print(self.numassigned)
#      print("numcollected")
#      print(self.numcollected)
#      print("number of assignments completed")
#      print(self.new_assignment_count)
      self.remove_misassigned_scvs()
      self.remove_duplicate_assignments()
      self.remove_false_assignments()
      for scv in self.scvs:
        print("scv tag")
        print(scv['scv_tag'])
        print("scv active status")
        print(scv['is_active'])
        print("scv selection status")
        print(scv['is_selected'])
        print("scv assignment status")
        print(scv['scv_assigned'])
        print("scv position")
        print(scv['pos'])
        print("scv random target")
        print(scv['rwalktarg'])
        print("scv rwalk status")
        print(scv['is_active_rwalk'])
      if(True):
        if(self.numcollected < self.initial_crystal_count):
          for scv in self.scvs:
  #          print(self.scvs)
            if(scv['scv_assigned'] == True):
  #            pass
              continue
            if(scv['is_active'] == True):
              continue
            if(True):
              if(scv['is_selected_rwalk'] == False and scv['is_active_rwalk'] == False):
  #            if(scv['is_selected'] == False):
                x = scv['pos']['x']
                y = scv['pos']['y']
                target = (x, y)
                scv['is_selected_rwalk'] = True
  #              scv['is_active'] = False
                return actions.FunctionCall(_SELECT_POINT, [_NOT_QUEUED, target])
              elif(scv['is_selected_rwalk'] == True and scv['is_active_rwalk'] == False):
                x = round(random.uniform(22.3125, 43.6874), 4)
                y = round(random.uniform(20.3125, 35.6874), 4)
                rtarg = self._translate_coord.world_to_screen(x, y)
                rtarg = (rtarg.x, rtarg.y)
  #              print("rtarg")
  #              print(rtarg)
  #              exit()
                if(self.numscvs == 1):
                  scv['rwalktarg'] = rtarg
  #                self.rwalktargs = (x, y)
                else:
                  scv['rwalktarg'] = rtarg
                scv['is_active_rwalk'] = True
  #              scv['is_selected'] = False
                if(self.numscvs == 1):
                  return actions.FunctionCall(_MOVE_SCREEN, [_NOT_QUEUED, scv['rwalktarg']])
                else:
                  return actions.FunctionCall(_MOVE_SCREEN, [_NOT_QUEUED, scv['rwalktarg']])
              elif(scv['is_active_rwalk'] == True):
                if(self.numscvs == 1):
#                  print("herehere")
                  ax = (scv['rwalktarg'][0]) - 8
                  bx = (scv['rwalktarg'][0]) + 8
                  ay = (scv['rwalktarg'][1]) - 8
                  by = (scv['rwalktarg'][1]) + 8
                  
                  self.updateposition(nObs)
                  
                  if(((ax <= scv['pos']['x'] <= bx) and (ay <= scv['pos']['y'] <= by)) == True):
                    scv['is_active_rwalk'] = False
                    scv['is_selected_rwalk'] = False
                else:
#                  print("herehere")
                  ax = (scv['rwalktarg'][0]) - 8
                  bx = (scv['rwalktarg'][0]) + 8
                  ay = (scv['rwalktarg'][1]) - 8
                  by = (scv['rwalktarg'][1]) + 8
                  scv['rwalkcount'] = scv['rwalkcount'] + 1
                  self.updateposition(nObs)
                  
                  if(((ax <= scv['pos']['x'] <= bx) and (ay <= scv['pos']['y'] <= by)) or (scv['rwalkcount'] % 2 == 0)):
  #                if(((ax <= scv['pos']['x'] <= bx) and (ay <= scv['pos']['y'] <= by))):                
                    scv['is_active_rwalk'] = False
                    scv['is_selected_rwalk'] = False
                    scv['is_active_rwalk'] = False
                    scv['is_assigned'] = False
                    scv['is_active'] = False
                    for assign in self.assignmentlist:
                      if(assign['scv'] == scv['scv_tag']):
                        assign['is_active_rwalk'] = False
                        assign['is_selected'] = False
                        assign['scv_assigned'] = False
                        assign['is_active'] = False
                        assign['is_selected_rwalk'] = False
                        
      # if(self.reset_state_count % 10 == 0):              
        # for scv in self.scvs:
          # scv['is_active'] = False
  # #        scv['is_selected'] = False          
      # self.reset_state_count = self.reset_state_count + 1
      # if(self.reset_state_count == 1000):
        # self.reset_state_count = 0
            
      print("commcount")
      print(self.commcount)
    return actions.FunctionCall(_NOOP, [])