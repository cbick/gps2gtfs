"""
Operations to perform on the pre-processed data
"""

import dbutils as db

from pylab import *
from scipy import stats,array,log,linalg,ones,sqrt


class Clust(object):
  """
  Object representing a cluster of data points
  """
  def __init__(self,sum1,sum2,length,id,left=None,right=None):
    """
    
    """
    self.sum1,self.sum2,self.length = sum1,sum2,length
    self.mean = float(sum1)/length
    self.std = sqrt( float(sum2)/length - self.mean**2 )
    self.id = id
    self.left,self.right = left,right

  def dist(self,other):
    return (self.mean-other.mean)**2 + (self.std-other.std)**2

  def printself(self,ref,levels=0):
    if self.left:
      print "| "*levels+"| (%f,%f)"%(self.mean,self.std)
      self.left.printself(ref,levels+1)
      self.right.printself(ref,levels+1)
    else:
      print "| "*(levels-1)+"+",ref[self.id]['route_name'],
      print ref[self.id]['lateness']


def meanstd_hcluster(rows,key):
  """
  Given a list of dictlike rows and a key indicating the column name,
  hierarchically clusters the data using mean and standard deviation as 
  distance measures.
  """
  def makeClust((i,row)):
    val = row[key]
    return Clust(val,val**2,1,i);


  clusts = map(makeClust, enumerate(rows))
  newid=-1
  dists = {}


  print "calc'ing initial dists..."
  def h1((i,c1)):
    map(lambda c2: dists.__setitem__((c1.id,c2.id),c1.dist(c2)),clusts[i+1:])

  map(h1,enumerate(clusts))

  while len(clusts) > 1:
    print "%d clusters remaining..."%(len(clusts),)
    mindist = clusts[0].dist(clusts[1])+1
    minpair=None
    
    print " Finding min..."
    for i,c1 in enumerate(clusts[:-1]):
      def help( (min_j,min_dist), (j,c2) ):
        d = dists[(c1.id,c2.id)]
        if d < min_dist: return (j,d)
        return (min_j,min_dist)
      min_j,min_dist_i = reduce( help, enumerate(clusts[i+2:]), 
                                 (-1,dists[(c1.id,clusts[i+1].id)]))
      if min_dist_i < mindist:
        minpair=(i,min_j+i+2)
        mindist = min_dist_i
        
    
    # Merge the closest pair
    c1,c2 = clusts[minpair[0]],clusts[minpair[1]]
    newlength = c1.length+c2.length
    newid = newid-1
    newsum1 = c1.sum1 + c2.sum1
    newsum2 = c1.sum2 + c2.sum2
    merged = Clust(newsum1,newsum2,newlength,newid,left=c1,right=c2)

    del clusts[minpair[1]]
    del clusts[minpair[0]]

    print " Updating dists..."
    map(lambda c: dists.__setitem__((c.id,newid),c.dist(merged)), clusts)

    clusts.append(merged)
    

  return clusts[0]
    
          




def get_routehops():
  print "Selecting..."
  cur = db.get_cursor()
  db.SQLExec(cur,
  """select *
     from datamining_table dm 
     natural join random_gps_segments rgs
     inner join gps_segments gs on dm.gps_segment_id=gs.gps_segment_id
     where lateness is not null
     --and rgs.rand < 0.1
     and gs.trip_date = '2009-03-27'
     and dm.route_name in ('1','9','19')
     and dm.service_id='1'
       --and random() < 0.001""")
  print "Retrieving..."
  rows=cur.fetchall()
  cur.close()
  return rows

def get_rows(rsubset=0.1):
  print "Selecting..."
  cur = db.get_cursor()
  if rsubset is not None:
    db.SQLExec(cur,
               """select * from datamining_table dm
               where random() < %f"""%(rsubset,))
  else:
    db.SQLExec(cur,"select * from datamining_table")

  return cur

def get_joined_rows(prev_attrs=(),degree_of_sep=1):
  print "Selecting..."
  if prev_attrs:
    sql="""select d2.*,""" + ",".join(map(lambda a:"d1."+a,prev_attrs))
  else:
    sql="""select d2.* """
  sql += """
from datamining_table d1 inner join datamining_table d2
on d1.gps_segment_id = d2.gps_segment_id
and d1.stop_number+"""+str(degree_of_sep)+"""=d2.stop_number"""

  cur = db.get_cursor()
  db.SQLExec(cur,sql);
  return cur


def split_on_attributes(keys,rows):
  """
  Given a tuple of column names 'keys', and a collection of dict-like
  rows, returns a dictionary where every unique value as defined by keys
  is a key in the dictionary, and the value under that key is a list
  containing the corresponding rows.
  """
  ret = {}
  
  for row in rows:
    key = tuple([row[k] for k in keys])
    vals = ret.get(key)
    if vals is None:
      vals = []
      ret[key] = vals
    vals.append(row)

  return ret

def split_on_attribute_values(tester,rows):
  """
  Given a function 'tester' which, given a row, returns either
  True or False, and a collection of rows, returns
        (trues,falses)
  where trues is a list of the rows where tester returned True,
  and falses is a list of the rows where tester returned False.
  """
  ts,fs = [],[]
  def helper(r):
    if tester(r): ts.append(r)
    else: fs.append(r)

  map(helper,rows)
  return ts,fs






def test_routehop_normality(rows,attributes,key):
  print "Splitting..."
  instances = split_on_attributes(attributes,rows)
  
  print "Processing..."
  toofew=0
  nonnormal=0
  normal=0
  for skey in instances.keys():
    times = array([s[key] for s in instances[skey]])
    n = len(times)
    mean_time = times.mean()
    std_time = times.std()
    
    if n >= 30:
      pval = stats.shapiro(times)[1]
      if pval < .05:
        nonnormal += 1
        #figure()
        #hist(times)
        #title("%s (p-val=%f, %d pts)" %(str(skey),pval,n));
      else:
        normal += 1
    else:
      toofew += 1

  print "Non,toofew,normal:",nonnormal,toofew,normal








if __name__=="__main__":
  rows = get_routehops()
  test_routehop_normality(rows)

