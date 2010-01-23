# Copyright (c) 2010 Colin Bick, Robert Damphousse

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

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

config_file = "config/db.config"
for i in range(5):
  try:
    db_params = read_config(config_file);
  except:
    config_file = "../" + config_file
    continue
  break

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
