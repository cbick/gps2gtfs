from dbutils import read_config

config = {}

def init_config():
  global config
  try:
    conf_params = read_config("realtime.config")
  except:
    conf_params = {}
    print "realtime.config not found."
  
  defaults = {
    'store_intermediate' : 'False',
    'min_lateness_minutes' : '-20',
    'max_lateness_minutes' : '40'
    }

  for key,default in defaults.items():
    config[key] = eval(conf_params.get(key,default))


init_config()

