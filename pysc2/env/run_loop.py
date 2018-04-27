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
"""A run loop for agent/environment interaction."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import types
import re
import json
import inspect

import time

from pysc2.lib import point

#======================================================================
# Function Classes
#======================================================================
# This function checks if an object is an absolute function/method
#
# By  : Khalid Al-Hawaj
# Date:  9 April 2018

func_classes = [
                types.FunctionType       ,
                types.MethodType         ,
                types.BuiltinFunctionType,
                types.BuiltinMethodType  ,
               ]

def isFunction(obj):

  isFunc = False

  for funcType in func_classes:
    isFunc |= isinstance(obj, funcType)

  return isFunc

#======================================================================
# Wrapper Attributes
#======================================================================
# Checks if an attribute is a wrapper
#
# By  : Khalid Al-Hawaj
# Date:  9 April 2018

wrapperPattern = re.compile('^__[A-z]*__$')

def isWrapper(obj):

  ret  = False
  name = ''
  name = ''

  try:
    name = "{}".format(obj)
  except:
    pass

  ret |= wrapperPattern.match(name) != None

  return ret


#======================================================================
# Terminal Classes and Recursive Classes
#======================================================================
# Checks for classes representing data

data_classes = [int, str, float]

#======================================================================
# Check if we need an object
#======================================================================
# Given a list of checks and an object, this function dynamically
# checks if the objects abide to at least one rule
#
# By  : Khalid Al-Hawaj
# Date:  9 April 2018

def check_object(checks, obj):

  ret = False
  for check in checks:
    if isinstance(check, tuple):
      func = check[0]
      cls  = check[1] if len(check) > 1 else None
    elif isFunction(check):
      func = check
      cls  = None
    else:
      func = None
      cls  = check

    if func != None and cls != None:
      # Just let me stay ...
      # We try to switch obj and cls order if there was an exception thrown
      try:
        ret |= func(obj, cls)
      except:
        ret |= func(cls, obj)

    elif func != None:
      ret |= func(obj)

    elif cls != None:
      ret |= isinstance(obj, cls)

    else:
      assert(False)

  return ret

#======================================================================
# Parse Incoming Observations
#======================================================================
# Parse an incoming observation from Google's protobuf class to a
# nested dict/list structure
#
# By  : Khalid Al-Hawaj
# Date:  9 April 2018

def parse_observations(obj, depth = 0):

  """Parse observations from raw data"""

  obs      = None
  fields   = None
  iterable = False

  fields = hasattr(obj, 'ListFields')

  try:
    iter(obj)
    iterable = not check_object(data_classes, obj)
  except:
    pass

  if fields:
    obs = {}
    for field in obj.ListFields():
      name = field[0].name
      val  = 0

      if name != 'data':
        val = parse_observations(field[1], depth + 1)

      obs[name] = val

  elif iterable:
    obs = []
    for item in obj:
      val = parse_observations(item, depth + 1)
      obs.append(val)

  else:
    obs = obj

  return obs

#======================================================================
# Main run loop
#======================================================================
# Main run loop. Modified to parse raw observations into something more
# comprehensible and more _pythonic_
#
# By  : Khalid Al-Hawaj
# Date:  9 April 2018

def run_loop(agents, env, max_frames=0, max_episodes=1):
  """A run loop to have agents and an environment interact."""
  total_frames = 0
  total_episodes = 0
  start_time = time.time()

  action_spec = env.action_spec()
  observation_spec = env.observation_spec()
  for agent in agents:
    agent.setup(observation_spec, action_spec)

  try:
    while True:
      timesteps = env.reset()
      for a in agents:
        a.reset()
      while True:
        total_frames += 1

        # Get raw observations
        rObs = [parse_observations(mObs) for mObs in env._env._obs]

        # Print the global observations
        #print(json.dumps(rObs, indent=2, sort_keys=True))

        # Get game info
        def get_game_info(controller, obs):
          _game_info    = controller.game_info()
          fl_opts       = _game_info.options.feature_layer
          _screen_size  = point.Point.build(fl_opts.resolution)
          _minimap_size = point.Point.build(fl_opts.minimap_resolution)
          _map_size     = point.Point.build(_game_info.start_raw.map_size)
          _cam_width    = fl_opts.width
          _cam_pos_x    = obs['observation']['raw_data']['player']['camera']['x']
          _cam_pos_y    = obs['observation']['raw_data']['player']['camera']['y']

          game_info                 = {}
          game_info['screen_size' ] = _screen_size
          game_info['minimap_size'] = _minimap_size
          game_info['map_size'    ] = _map_size
          game_info['camera_width'] = _cam_width
          game_info['camera_pos'  ] = {'x': _cam_pos_x,
                                       'y': _cam_pos_y}

          return game_info

        game_infos    = [ get_game_info(controller, obs)
                            for obs, controller in zip(rObs, env._env._controllers) ]

        # Invoke correct step function
        actions = []
        for agent, timestep, obs, game_info in zip(agents, timesteps, rObs, game_infos):

          # Get number of arguments
          try:
            # Try for Python 3.x
            num_args = len(inspect.signature(agent.step).parameters)
          except:
            num_args = len(inspect.getargspec(agent.step)) - 1

          if   num_args == 1:
            action = agent.step(timestep)

          elif num_args == 2:
            action = agent.step(timestep, obs)

          elif num_args == 3:
            action = agent.step(timestep, obs, game_info)

          else:
            raise TypeError

          actions.append(action)

        # Keep track of number of episodes
        if timesteps[0].last():
          total_episodes += 1

        # Terminate when we reach maximum number of episodes
        if max_episodes and total_episodes >= max_episodes:
          return
        elif max_frames and total_frames >= max_frames:
          return

        # Either execute actions and advance observations
        # Or we reset the environment
        if not timesteps[0].last():
          timesteps = env.step(actions)
        else:
          timesteps = env.reset()

  except KeyboardInterrupt:
    pass
  finally:
    elapsed_time = time.time() - start_time
    print("Took %.3f seconds for %s steps: %.3f fps" % (
        elapsed_time, total_frames, total_frames / elapsed_time))
