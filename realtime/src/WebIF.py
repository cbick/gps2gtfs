import StatsIF as SIF
import json

def parse_query_string(qstr):
  ret = {}
  items = qstr.split("&");
  for item,val in map(lambda iv: iv.split("="), items):
    ret[item] = val
  return ret

def parse_bounds_string(boundstr):
  return map( lambda mm: map(int,mm.split("-")), boundstr.split("."))


class yamwfw(object):
  def handle_error(self,env,start):
    raise Exception, "Bad values"

  def return_json(self,obj):
    return json.dumps(obj);

  def querycall(self,env,start):
    querystr = something.whatever
    values = parse_query_string(querystr)
    try:
      result = self.handle_query(values)
      start( "200 OK", [('Content-type','text/json')] )
      return [ self.return_json(result)+"\n" ]
    except:
      self.handle_error(env,start);


class GetStops(yamwfw):
  def handle_query(values):
    return SIF.get_stops(**values)
  

class GetStopInfo(yamwfw):
  def handle_query(values):
    return SIF.get_stop_info(**values)


class GetLatenessStat(yamwfw):
  def handle_query(values):
    values['bounds'] = parse_bounds_string(values['bounds'])
    return SIF.get_percentile(**values)


get_stops = GetStops()
get_stop_info = GetStopInfo()
get_lateness_stat = GetLatenessStat()
