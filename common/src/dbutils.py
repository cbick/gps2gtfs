import psycopg2 as db
import psycopg2.extras
from ServiceDateHandler import ServiceDateHandler

def read_config(fname):
  f = open(fname,'r');
  lines = f.readlines();
  f.close()
  ret = {}
  lines = filter(lambda line: line and not line.startswith("#"),
                 map(str.strip,lines));
  for line in lines:
    key,val = line.split();
    ret[key] = val;
  return ret;

config_file = "../../config/db.config"
db_params = read_config(config_file);

conn = None
SDHandler = None

def SQLCopy(cur,copy_stmt,rowList):
  gtx = cur.greentrunk;
  copier = gtx.query(copy_stmt);
  copier(rowList);

def SQLExec(cur,sql,params=None):
  if params:
    cur.execute(sql,params);
  else:
    cur.execute(sql);

def commit():
  conn.commit();

def get_db_conn(params=db_params):
  global conn,SDHandler;
  if conn:
    close_db_conn();
  conn = db.connect(**params);
  SDHandler = ServiceDateHandler(conn,True,True);
  return conn

def get_cursor():
  cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
  #cur = conn.cursor()
  return cur

def close_db_conn():
  global conn;
  if not conn:
    return;
  conn.close()
  conn = None;

conn = get_db_conn();




import atexit
atexit.register(close_db_conn)
