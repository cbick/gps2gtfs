import StatsIF as SIF

def parse_query_string(qstr):
  ret = {}
  items = qstr.split("&");
  for item,val in map(lambda iv: iv.split("="), items):
    ret[item] = val
  return ret

def parse_bounds_string(boundstr):
  return map( lambda mm: map(int,mm.split("-")), boundstr.split("."))


class yamwfw(object):
  def handle_error(self):
    pass

  def return_json(self,obj):
    pass

  def querycall(self,something):
    querystr = something.whatever
    values = parse_query_string(querystr)
    try:
      result = self.handle_query(values)
      self.return_json(result)
    except:
      self.handle_error();


class GetStop(yamwfw):
  def handle_query(values):
    return SIF.get_stops(**values)
      
