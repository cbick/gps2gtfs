from scipy import array,sort
from pylab import find,hist,figure
import subprocess

def copy(txt):
  """
  Copies txt to the clipboard (OSX only)
  """
  p=subprocess.Popen(['pbcopy'],stdin=subprocess.PIPE)
  p.stdin.write(txt)
  p.stdin.close()

def print_expected_wait_vs_arrival(result,delim="\t"):
  """
  Returns string of 'delim'-delimited printout. Assumes the result provided
  is of the format
    { headway : (arrivals, expected_waits, expected_wait_random) }  
  """

  ret = ""

  rows = set()
  for arrs,ews,ewr in result.values():
    rows = rows.union(arrs)
  rows = array(list(rows))
  rows.sort()

  cols = array(result.keys())
  cols.sort()
  
  # Header; note the blank first entry
  ret += delim + delim.join(map(str,cols)) + "\n"
  
  for r in rows:
    ret += str(r) + delim
    for c in cols:
      arrs,ews,ewr = result[c]
      ri = find(arrs==r)
      if len(ri)==1:
        ret += str(ews[ri[0]])
      elif len(ri) > 1:
        print "INSANITY"
      ret += delim
    ret += "\n"
    
  ret += "Random" + delim
  for c in cols:
    ret += str(result[c][2]) + delim
    
  ret += "\n"

  return ret


def print_prob_transfer(result,delim="\t"):
  """
  Returns string of 'delim'-delimited printout. Assumes the result
  provided is of the format
    { label : winprobs }
  where winprobs is a Nx2 array where the first column is window size
  and the second column is the probability.
  """
  
  ret = ""
  
  rows = set()
  for winprobs in result.values():
    rows = rows.union(winprobs[:,0])
  rows = array(list(rows))
  rows.sort()

  cols = array(result.keys())
  cols.sort()

  # Header; note the blank first entry
  ret += delim + delim.join(map(str,cols)) + "\n"
  
  for r in rows:
    ret += str(r) + delim
    for c in cols:
      winprobs = result[c]
      wins,probs=winprobs[:,0],winprobs[:,1]
      ri = find(wins==r)
      if len(ri)==1:
        ret += str(probs[ri[0]])
      elif len(ri) > 1:
        print "INSANITY"
      ret += delim
    ret += "\n"


  return ret



def print_histogram(result,delim="\t",weighted=True,bins=10,normed=False):
  """
  Returns string of 'delim'-delimited printout. Assumes the result
  provided is of the format
    { label : values }
  where values is a 1D list or array of values, if weighted is False,
  or a 2D array of values (1st column values, 2nd column weight) if
  weighted is True. 
  Note that this function takes care of all the binning and 
  histogramming for you, you just need to provide the data.
  """
  
  ret = ""
  
  figure() #to avoid clobbering someone else's figure

  ## Since the pylab.hist() method doesn't actually implement
  ## barstacking with different-lengthed datasets, we have to
  ## first merge all data sets into one big histogram in order
  ## to determine the bin divisions; afterwards we can use that
  ## bin division to separately get each dataset's hist.

  if weighted:
    all_values = reduce( lambda accum,next: accum + list(next[:,0]),
                         result.values(), [] )
    all_weights = reduce( lambda accum,next: accum + list(next[:,1]),
                          result.values(), [] )
  else:
    all_values = reduce( lambda accum,next: concatenate(accum,next),
                         result.values() )
    all_weights = None

  # Note we are overriding bins here
  ns,bins,patches = hist(all_values,normed=normed,bins=bins,weights=all_weights)

  figure()

  ns = []
  # Keeps the keys consistently ordered
  keys = list(result.keys())

  for k in keys:
    v = result[k]
    if weighted:
      v,w = v[:,0],v[:,1]
    else:
      w = None
    n,b,p = hist(v,normed=normed,bins=bins,weights=w,label=str(k))
    ns.append(n)
  
  rows = bins
  cols = array(keys)
  cols.sort()

  # Note space for two columns
  ret += delim + delim + delim.join(map(str,cols)) + "\n"
  
  for i in range(len(rows)-1):
    ret += str(rows[i]) + delim
    ret += str((rows[i]+rows[i+1])/2.0) + delim
    for n in ns:
      # Each n is a list of "how many" per bin
      ret += str(n[i]) + delim
    ret += "\n"
  ret += str(rows[-1]) + "\n"

  return ret
