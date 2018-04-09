from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from pysc2.maps import lib

class MyMap(lib.Map):
  directory = "my_maps"
  download = None
  players = 1
  score_index = 0
  game_steps_per_episode = 0
  step_mul = 8


my_games = [
    "SingleMarineTest",
    "TwoMineralsTest",
]


for name in my_games:
  globals()[name] = type(name, (MyMap,), dict(filename=name))
