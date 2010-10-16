import rtqueries as rtdb



def get_stops( min_lat, max_lat, min_lon, max_lon ):
  stops = rtdb.get_stops( min_lat,max_lat,min_lon,max_lon )
  return map( lambda stop: { 'stop_id' : stop['stop_id'],
                             'lat' : stop['stop_lat'],
                             'lon' : stop['stop_lon'],
                             'stop_name' : stop['stop_name'] },
              stops)

def get_stop_info(stop_id, dow):
  sinfos = rtdb.get_stop_info(stop_id,dow)
  # eventually we'll construct a list of routeinfos
  rinfos = {}
  for sinfo in sinfos:
    route_name = sinfo['route_short_name']
    rinfo = rinfos.get( route_name, { 'route_name' : route_name,
                                      'arrivals' : [] } )
    rinfos[route_name] = rinfo
    arrival = {}
    for uk,dbk in ( ('trip_id','trip_id'),
                    ('arrival_time','arrival_time_seconds'),
                    ('arrival_time_repr','arrival_time'),
                    ('stop_seq','stop_sequence') ):
      arrival[uk] = sinfo[dbk]
    rinfo['arrivals'].append(arrival)                    
  return list(rinfos.values())


def get_percentile( bounds, trip_id, stop_seq, dow ):
  """
  Given bounds [(min1,max1),(min2,max2),...], a sequence of lower and upper 
  bounds on lateness in minutes, and the identifying information for a 
  single stop of a single trip on a single day of the week, returns a 
  list of percentiles  [p1,p2,...], 0 <= p <= 1, defining the probability mass
  that the specified arrival will be between min and max lateness minutes
  late.

  Returns None if the identifying information does not identify a known
  arrival.
  """
  return rtdb.measure_prob_mass( trip_id, None, dow, stop_seq, bounds )




def main():
  import sys
  args = sys.argv

  usage = """\
Usage: %s min_minutes max_minutes trip_id stop_seq stop_id dow
""" % args[0]

  if len(args) != 7:
    print usage
    sys.exit(1)

  print get_percentile(*args[1:])

if __name__=="__main__":
  main()
