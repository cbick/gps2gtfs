import rtqueries as rtdb



def get_percentile( min_lateness_minutes, max_lateness_minutes,
                    gtfs_trip_id, stop_sequence, stop_id, day_of_week ):
  """
  Given lower and upper bounds on lateness in minutes, and the identifying
  information for a single stop of a single trip on a single day of the
  week, returns a percentile 0 <= p <= 1, defining the probability mass
  that the specified arrival will be between min and max lateness minutes
  late.

  Returns None if the identifying information does not identify a known
  arrival.
  """
  return rtdb.measure_prob_mass( gtfs_trip_id, stop_id, day_of_week, 
                                 stop_sequence, 
                                 min_lateness_minutes, max_lateness_minutes )




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
