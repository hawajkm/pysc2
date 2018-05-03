#=========================================================================
# Platform for distributed agents simulation
#=========================================================================
#
#  This will automate the execution of all agents
#
#  Author: Khalid Al-Hawaj
#  Date  : 2 May 2018

""" Here we go """

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy

from pysc2.agents import base_agent
from pysc2.lib import actions

# Constants

#------------------------
# State constants
#------------------------
__STATE_INIT    = 0
__STATE_EXEC    = 1
__STATE_DISPATH = 2

class MultiAgent(base_agent.BaseAgent):
  """Multi-agent platform for pySC2."""

  #------------------------
  # Actions Constants
  #------------------------
  actions_db = {}
  actions_db['noop'  ] = actions.FUNCTIONS.no_op.id
  actions_db['select'] = actions.FUNCTIONS.Attack_screen.id
  actions_db['attack'] = actions.FUNCTIONS.select_army.id

  #-----------------------------------------------
  # Constructor
  #-----------------------------------------------
  def __init__(self, **kwargs):

    # Call super
    super(self.__class__, self).__init__( kwargs )

    # States
    s.init_states()

    # Reset flag
    s.flags = {}
    s.flags['reset'] = False

  #-----------------------------------------------
  # Initialize internal variables
  #-----------------------------------------------
  def init_states(self):

    # Needed states
    s.state = __STATE_INIT
    s.acts  = []

    # Translation
    s._translate_coord = translate_coord.translate_coord()

  #-----------------------------------------------
  # Action Helpers
  #-----------------------------------------------
  def actuate(self, action, args = []):

    action_id = self.action_db[action]

    return actions.CallFunction(action_id, args)

  #-----------------------------------------------
  # Reset
  #-----------------------------------------------
  def reset(self, **kwargs):

    # Reset all values
    s.init_states()

    # Reset flags
    s.flags['reset'] = True

  #-----------------------------------------------
  # The bulk of the work
  #-----------------------------------------------
  def step(self, obs, rObs, game_info):

    super(self.__class__, self).step(obs)

    # If reset is not done, we skip this step
    if not s.flags['reset']:
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
    if s.state == __STATE_INIT:

      # For now, nothing special
      s.state = __STATE_EXEC

    elif s.state == __STATE_EXEC:

      # Execute some logic


      # Collect needed action
      s.acts.expand([])

      s.state = __STATE_DISPATCH

    elif s.state == __STATE_DISPATCH:

      # Dispatch one action at a time
      

      # If we have no more commands, go back to normal eecution
      if len(s.acts) == 0:
        s.state = __STATE_EXEC

    return actions.FunctionCall(function_id, args)
