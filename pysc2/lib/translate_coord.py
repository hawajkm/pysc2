#=========================================================================
# translate_coord.pu
#=========================================================================
# Class to translate coordinates between map and world
#
# The question is not why I am not thanking deepmind; the question is why
# in the name of everything that is holy I would need this atrocity ...
#
# Author: Khalid Al-Hawaj
# Date  : April 26 2018

# Future
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# System and stuff ...
import math
import time

# pysc2 stuff ...
from pysc2.lib import transform
from pysc2.lib import point

class translate_coord(object):

  def __init__(self):

    # Constants
    self._map_size     = None
    self._minimap_size = None
    self._screen_size  = None
    self._camera_width = None
    self._camera_pos   = None

  def update(self, map_size, minimap_size, screen_size, camera_width, camera_pos):

    # Require updates
    needs_update = False

    # Constants
    if self._map_size != map_size:
      self._map_size = map_size
      needs_update = True

    if self._minimap_size != minimap_size:
      self._minimap_size = minimap_size
      needs_update = True

    if self._screen_size != screen_size:
      self._screen_size = screen_size
      needs_update = True

    if self._camera_width != camera_width:
      self._camera_width = camera_width
      needs_update = True

    if self._camera_pos != camera_pos:
      self._camera_pos = camera_pos
      needs_update = True

    # If an update is needed
    if needs_update:
      self.update_transformations()

  def update_transformations(self):

    # Create transformations
    self._world_to_minimap = transform.Linear(point.Point(1, -1),
                                              point.Point(0, self._map_size.y))
    max_map_dim = self._map_size.max_dim()
    self._minimap_to_fl_minimap = transform.Linear(
        self._minimap_size / max_map_dim)
    self._world_to_fl_minimap = transform.Chain(
        self._world_to_minimap,
        self._minimap_to_fl_minimap,
        transform.Floor())

    # Flip and zoom to the camera area. Update the offset as the camera moves.
    # Get camera corner
    cam_x   = -1 * (self._camera_pos['x'] - (self._camera_width / 2))
    cam_y   =  1 * (self._camera_pos['y'] + (self._camera_width / 2))
    cam_pos = point.Point(x = cam_x, y = cam_y)

    self._reorient_world  = transform.Linear(point.Point(1, -1), offset=cam_pos)
    self._world_to_screen = transform.Linear(point.Point(1, 1),
                                             point.Point(0, 0))
    #self._world_to_screen = transform.Linear(point.Point(1, -1),
    #                                         point.Point(0, self._map_size.y))
    self._screen_to_fl_screen = transform.Linear(
        self._screen_size / self._camera_width)
    self._world_to_fl_screen = transform.Chain(
        self._reorient_world,
        self._world_to_screen,
        self._screen_to_fl_screen,
        transform.Floor())

  #-----------------------------------------------------------------------
  # Translation Meta-Function
  #-----------------------------------------------------------------------

  @staticmethod
  def __translate__(tf, tf_dir, x, y = None):

    # Either a point or a distance
    pt = None
    dist = None

    # Convert any integers to floats
    if type(x) is int:
      x = float(x)
    if type(y) is int:
      y = float(y)

    if type(x) is point.Point:
      pt = x
    elif (type(x) is float) and (type(y) is float):
      pt = point.Point(x, y)
    elif (type(x) is float) and (y == None):
      dist = x

    func_pt   = getattr(tf, '{}_pt'  .format(tf_dir))
    func_dist = getattr(tf, '{}_dist'.format(tf_dir))

    if   pt   and func_pt:
      return func_pt  (pt  )
    elif dist and func_dist:
      return func_dist(dist)
    else:
      raise ValueError

  #-----------------------------------------------------------------------
  # World to Minimap
  #-----------------------------------------------------------------------

  def world_to_minimap(self, x, y = None):

    cls  = self.__class__
    func = cls.__translate__
    tf   = self._world_to_fl_minimap
    tf_d = 'fwd'

    return func(tf, tf_d, x, y)

  #-----------------------------------------------------------------------
  # Minimap to World
  #-----------------------------------------------------------------------

  def minimap_to_world(self, x, y = None):

    cls  = self.__class__
    func = cls.__translate__
    tf   = self._world_to_fl_minimap
    tf_d = 'back'

    return func(tf, tf_d, x, y)

  #-----------------------------------------------------------------------
  # World to Screen
  #-----------------------------------------------------------------------

  def world_to_screen(self, x, y = None):

    cls  = self.__class__
    func = cls.__translate__
    tf   = self._world_to_fl_screen
    tf_d = 'fwd'

    return func(tf, tf_d, x, y)

  #-----------------------------------------------------------------------
  # Screen to World
  #-----------------------------------------------------------------------

  def screen_to_world(self, x, y = None):

    cls  = self.__class__
    func = cls.__translate__
    tf   = self._world_to_fl_screen
    tf_d = 'back'

    return func(tf, tf_d, x, y)

