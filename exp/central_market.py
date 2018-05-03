import numpy as np
import Queue
import random
import json

from pysc2.lib import parse_obs

class CentralMarket(object):

  def __init__(self):

    self.nothing = ':)'

  def plan(self, obs):

    # Helper functions
    def get_pos(x):
      return x['tag'], {'pos': [x['pos']['x'], x['pos']['y']]}

    def dist(a, b):
      return pow(a[0] - b[0], 2) + pow(a[1] - b[1], 2)

    # Get unit and stuff ...
    raw_units    = parse_obs.get_units(obs, alliance = 1                  )
    raw_minerals = parse_obs.get_units(obs, alliance = 3, unit_type = 1680)

    # Lambda and stuff
    units        = dict([get_pos(x) for x in raw_units])
    minerals     = [get_pos(x) for x in raw_minerals]

    assignments  = {i: None for i in xrange(len(minerals))}

    # Needed states for auction

    # Calculate weights
    for unit in units:

      unit_pos = units[unit]['pos']
      weights  = [(1 / dist(unit_pos, mineral)) for mineral in minerals]

      units[unit]['weights'] = weights

    # Prices for the minerals
    prices = [0 for _ in minerals]

    # Intialize queue to contain all bidders
    q = Queue.Queue(maxsize=len(scvs))

    for unit in units: q.put(unit)

    # Auctioning
    while(not q.empty()):

      # Start with the head of the queue
      bidder = q.get()

      # Get weights
      weights = units[bidder]['weights']

      # Get most profitable mineral
      profit      = [w - p for w, p in zip(weights, prices)]
      max_profit  = max(profit)
      mineral_idx = [i for i, x in enumerate(profit) if x == max_profit][0]

      del profit[mineral_idx]
      s_profit    = max(profit)
      bid         = max_profit - second_profit

      if   assignments[mineral_idx] == None:

        assignments[mineral_idx]  = unit
        prices[mineral_idx]      += bid

      elif assignments[mineral_idx] != unit:

        bastard = assignments[mineral_idx]
        q.put(bastard)
        assignments[mineral_idx] = unit
        prices[mineral_idx]      += bid

    # Parse results
    actions = []
    for mineral in assignments:

      winner = assignments[mineral]

      if winner != None:

        actions.append([winner, minerals[mineral]])

    # Done!
    return actions
