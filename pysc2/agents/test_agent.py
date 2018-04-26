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

class TestAgent(base_agent.BaseAgent):
  """A random agent for starcraft."""

  def step(self, obs, nObs, game_info):
    super(TestAgent, self).step(obs)

    # Get game_info
    _map_size     = game_info['map_sz'    ]
    _screen_size  = game_info['screen_sz' ]
    _minimap_size = game_info['minimap_sz']
    _camera_width = game_info['cam_width' ]

    # Update translate_coord
    if not hasattr(self, '_translate_coord'):
      self._translate_coord = translate_coord.translate_coord()

    self._translate_coord.update(_map_size, _minimap_size, _screen_size, _camera_width)

    # Get some units
    units = parse_obs.get_units(nObs, alliance = 1)

    # Get one
    for unit in units:
      x = unit['pos']['x']
      y = unit['pos']['y']

      print('Unit at:', self._translate_coord.world_to_minimap(x, y))

    for y, row in enumerate(obs.observation['minimap'][5]):
      for x, pt in enumerate(row):
        if pt != 0:
          print('(',x,', ',y,') = ',pt)

    # Stop
    exit()

    return actions.FunctionCall(_NO_OP, [])