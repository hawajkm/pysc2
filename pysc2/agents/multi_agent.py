#=========================================================================
# Platform for distributed agents simulation
#=========================================================================
#
#  This will automate the execution of all agents
#
#  Author: Khalid Al-Hawaj
#  Date  : 2 May 2018

""" Here we go """

from __future__   import absolute_import
from __future__   import division
from __future__   import print_function

import numpy
import json

from pysc2.agents import base_agent

from pysc2.lib    import actions
from pysc2.lib    import translate_coord
from pysc2.lib    import parse_obs

from exp.central_market import CentralMarket as CentralMarket

# Constants

class MultiAgent(base_agent.BaseAgent):
  """Multi-agent platform for pySC2."""

  #------------------------
  # State constants
  #------------------------
  __STATE_INIT     = 0
  __STATE_EXEC     = 1
  __STATE_DISPATCH = 2
  __STATE_DONE     = 3

  __DISPATCH_SEL   = 0
  __DISPATCH_ACT   = 1

  #------------------------
  # Actions Constants
  #------------------------
  actions_db = {}
  actions_db['noop'  ] = actions.FUNCTIONS.no_op.id
  actions_db['attack'] = actions.FUNCTIONS.Attack_screen.id
  actions_db['select'] = actions.FUNCTIONS.select_point.id
  actions_db['move'  ] = actions.FUNCTIONS.Move_screen.id 

  #-----------------------------------------------
  # Constructor
  #-----------------------------------------------
  def __init__(self, **kwargs):

    # Call super
    super(self.__class__, self).__init__()

    # States
    self.init_states()

    # Reset flag
    self.flags = {}
    self.flags['reset'] = False

  #-----------------------------------------------
  # Initialize internal variables
  #-----------------------------------------------
  def init_states(self):

    # Needed states
    self.state    = self.__STATE_INIT
    self.acts     = []
    self.lol      = CentralMarket()
    self.dispatch = 0
    self.idx      = 0
    self.repeat   = True

    # Translation
    self._translate_coord = translate_coord.translate_coord()

  #-----------------------------------------------
  # Action Helpers
  #-----------------------------------------------
  def actuate(self, action, args = []):

    action_id = self.actions_db[action]

    return actions.FunctionCall(action_id, args)

  #-----------------------------------------------
  # Reset
  #-----------------------------------------------
  def reset(self, **kwargs):

    # Reset all values
    self.init_states()

    # Reset flags
    self.flags['reset'] = True

  #-----------------------------------------------
  # The bulk of the work
  #-----------------------------------------------
  def step(self, obs, rObs, game_info):

    super(self.__class__, self).step(obs)

    # If reset is not done, we skip this step
    if not self.flags['reset']:
      return

    # Get game_info
    _map_size     = game_info['map_size'    ]
    _screen_size  = game_info['screen_size' ]
    _minimap_size = game_info['minimap_size']
    _camera_width = game_info['camera_width']
    _camera_pos   = game_info['camera_pos'  ]

    # Update translate_coord
    self._translate_coord.update(_map_size   , _minimap_size,
                                 _screen_size, _camera_width,
                                 _camera_pos ,              )

    # Initialize a NOOP for a possible return
    ret_action = self.actuate('noop')

    # The loop
    if self.state == self.__STATE_INIT:

      # For now, nothing special
      self.state = self.__STATE_EXEC

    elif self.state == self.__STATE_EXEC:

      # Execute some logic
      repeat, commands = self.lol.plan(rObs)

      # Collect needed action
      self.acts.extend(commands)

      # Memorize if we want to repeat planning
      self.repeat = repeat

      # Prepare for dispatching
      if len(self.acts) > 0:
        self.dispatch = self.__DISPATCH_SEL
        self.state    = self.__STATE_DISPATCH
        self.idx      = 0

    elif self.state == self.__STATE_DISPATCH:

      # Dispatch one action at a time
      if self.dispatch == self.__DISPATCH_SEL:

        unit_tag = self.acts[self.idx][0]
        unit_pos = parse_obs.get_units(rObs, tag = unit_tag)[0]['pos']
        unit_pos = self._translate_coord.world_to_screen(unit_pos['x'], unit_pos['y'])
        unit_pos = [unit_pos.x, unit_pos.y]

        ret_action = self.actuate('select', [[0], unit_pos])

        if parse_obs.get_units(rObs, tag = unit_tag)[0]['is_selected']:
          self.dispatch = self.__DISPATCH_ACT

      elif self.dispatch == self.__DISPATCH_ACT:

        act         = self.acts[self.idx]
        meta_action = self.lol.parse_action(act[1], self._translate_coord.world_to_screen)

        ret_action  = self.actuate(meta_action[0], meta_action[1])

        self.idx += 1

        # Go back
        self.dispatch = self.__DISPATCH_SEL

      # If we have no more commands, go back to normal eecution
      if self.idx >= len(self.acts):
        # Clear actions
        self.acts = []

        # Debate whether to go back or wait from episode to finish
        if self.repeat:
          self.state = self.__STATE_EXEC
        else:
          self.state = self.__STATE_DONE

    return ret_action
