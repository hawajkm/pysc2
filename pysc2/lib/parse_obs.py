#======================================================================
# Functions to parse observations easily
#======================================================================
# :)
#
# By  : Khalid Al-Hawaj
# Date:  9 April 2018

#----------------------------------
# Get units from raw observations
#----------------------------------
def get_units(obs, **raw_filters):

  # Match function
  def match(obj, filters, key):

    try:
      value = obj[key]

      for val in filters[key]:
        if val == value:
          return True

    except:
      pass

    return False

  # Assume we have raw observations passed to us
  try:
    _units = obs['observation']['raw_data']['units']
  except:
    _units = obs

  # Parse Filters
  filters = {}
  for key in raw_filters:

    # Get value of the key
    values = raw_filters[key]

    # Make the values a list
    if not type(values) is list:
      values = [values]

    # If we encountered the filter before, append extra values
    if not key in filters:
      filters[key] = []

    filters[key].extend(values)

  # Apply filters
  
  units = [ unit for unit in _units if 
              len([ fltr for fltr in filters
                if match(unit, filters, fltr) ]) > 0 ]

  # DONE!
  return units
