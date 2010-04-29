from scipy import array,sort
from pylab import find,hist,figure,repeat
import subprocess

def copy(txt):
  """
  Copies txt to the clipboard (OSX only)
  """
  p=subprocess.Popen(['pbcopy'],stdin=subprocess.PIPE)
  p.stdin.write(txt)
  p.stdin.close()


def print_QE_tables(Qs,Es,qs,delim="\t"):
  """
  Returns string of 'delim'-delimited printout. Assumes that
  Qs,Es are of the form returned by the Stats.QEPlot method, and that
  qs is the list of quantile percentages that were supplied to the same
  method.
  """

  ret = ""

  rows = array(Qs.keys())
  rows.sort()

  # we want 3 values for each Q and also the E
  qs = map(str,repeat(qs,3))
  for i in range(len(qs)/3):
    qs[i*3+0] += " lower CI"
    qs[i*3+1] += " upper CI"
  cols = qs+["E","E-moe","E+moe"]

  ret += delim + delim.join(cols) + "\n"
  
  for row in rows:
    Q = Qs[row]
    E,moe = Es[row]

    ret += str(row) + delim

    for qlh in Q: 
      #excel wants low,high,middle
      ret += delim.join(map(str,(qlh[1],qlh[2],qlh[0]))) + delim
    
    ret += str(E) + delim + str(E-moe) + delim + str(E+moe)
    ret += "\n"
  
  return ret
  


def print_ecdf_annotations(ecdf,data,minx=-2000,weighted=True,delim="\t"):
  """
  Returns string of 'delim'-delimited printout. Assumes that
  ecdf is of the form (x,p,a_n) as returned by the Stats.ecdf()
  method, and that data is the (optionally weighted) data 
  provided to the same.
  """
  import Stats

  ret = ""

  x,p,a_n = ecdf
  E_bar,E_moe = Stats.E(data,weighted=weighted,alpha=0.05);
  E_x,E_p,i = Stats.evaluate_ecdf(E_bar,x,p)
  zero_x,zero_p,j = Stats.evaluate_ecdf(0.0,x,p)
  x_q,p_q,i = Stats.find_quantile(0.05,x,p)
  
  ret += "x"+delim+"Expected Value\n"
  ret += str(minx) + delim + str(E_p) + "\n"
  ret += str(E_bar) + delim + str(E_p) + "\n"
  ret += str(E_bar) + delim + str(0) + "\n"
  ret += "\n"

  ret += "x"+delim+"On Time\n"
  ret += str(minx) + delim + str(zero_p) + "\n"
  ret += str(0) + delim + str(zero_p) + "\n"
  ret += str(0) + delim + str(0) + "\n"
  ret += "\n"

  ret += "x"+delim+"5% Quantile\n"
  ret += str(minx) + delim + str(p_q) + "\n"
  ret += str(x_q) + delim + str(p_q) + "\n"
  ret += str(x_q) + delim + str(0) + "\n"
  ret += "\n"

  return ret


def print_ecdfs(ecdfs,delim="\t"):
  """
  Returns string of 'delim'-delimited printout. Assumes the result
  provided is of the form
    { label : (x,p,a_n) }
  where each (x,p,a_n) are as returned by the Stats.ecdf() method.
  """

  ret = ""

  cols = array(ecdfs.keys())
  cols.sort()

  cols_per_series = 2

  # Header
  ret += (delim*(cols_per_series-1))
  ret += (delim*cols_per_series).join(map(str,cols)) + "\n"

  still_printing = list(cols)
  i = 0

  while still_printing:
    for k in cols:
      x,p,a_n = ecdfs[k]
      if i >= len(x):
        if k in still_printing: 
          still_printing.remove(k)
        ret += delim+delim
      else:
        ret += str(x[i]) + delim + str(p[i]) + delim

    ret += "\n"
    i += 1

  return ret



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



