"""
Creates plots/data as appearing in paper submitted to JPT
"""

import Stats
import dbutils as db
from Stats import DM
import ExcelPrint as EP

# shorthand
split = DM.split_on_attributes
array = Stats.array

def rows_to_data_arrive(rows):
  return array([(r['lateness_arrive'], r['trip_stop_weight_arrive']) for r in rows if r['lateness_arrive'] is not None]);

def rows_to_data_depart(rows):
  return array([(r['lateness_depart'], r['trip_stop_weight_depart']) for r in rows if r['lateness_depart'] is not None]);


## Initial retrieval and sorting of data

# Grab data needed
cur = db.get_cursor()
db.SQLExec(cur,Stats.comparison_sql);
rows = cur.fetchall();
cur.close()


# Service ID split
sids = split( ('service_id',), rows);
weekday_rows = sids[('1',)]
saturday_rows = sids[('2',)]
sunday_rows = sids[('3',)]
weekend_rows = saturday_rows + sunday_rows

# DoW split
dows = split( ('wday',), rows);


# Hour of day splits
weekday_hoas = split( ('hoa',), weekday_rows );
hoas = split( ('hoa',), rows );

# Route progress splits
stop_numbers = split( ('stop_number',), rows);
end_numbers = split( ('stops_before_end',), rows);
portions = split( ('route_portion',), rows);




### Unconditioned plots (no splits) ###

data_arrive = rows_to_data_arrive(rows)
data_depart = rows_to_data_depart(rows)
data = data_arrive
del rows

## ECDF plot ##

x,p,a_n = Stats.ecdf(data,weighted=True,alpha=0.05)
E_bar,E_moe = Stats.E(data,weighted=True,alpha=0.05);
nil,E_p,i = Stats.evaluate_ecdf(E_bar,x,p)
nil,zero_p,i = Stats.evaluate_ecdf(0.0,x,p)
x_q,p_q,i = Stats.find_quantile(0.05,x,p)

figure()

plot(x,p,'k-', label="ECDF")
#plot(x,p+a_n,'k--', label="95% CI")
#plot(x,p-a_n,'k--')

plot((-2000,E_bar),(E_p,E_p),'k-.', label="Expected Value")
plot((E_bar,E_bar),(0,E_p),'k-.')

plot((-2000,0),(zero_p,zero_p),'k--', label="On Time")
plot((0,0),(0,zero_p),'k--')

plot((-2000,x_q),(p_q,p_q),'k:', label="5% Quantile")
plot((x_q,x_q),(0,p_q),'k:')

legend(loc=4)
xlabel("Lateness (seconds)")
ylabel("Cumulative Probability")
title("ECDF of Lateness")

axis((-1000,2000,0,1))


## Prob. of Transfer plot ##

pot_overall = Stats.p_make_transfer_vs_window(data,doplot=True)


## Expected Wait Time vs Headways plot ##

headway_waits = Stats.expected_wait_vs_arrival_plot(
  data, headways=(5*60,15*60,30*60,60*60),
  min_arrival=-10*60, weighted=True,
  ofile="simplot.png",q_half=None)


del data



### Hour of Weekday ###

hoa_data = {}
for i in range(24):
  hoa_data[i] = rows_to_data(hoas[(i,)])

weekday_hoa_data = {}
for i in range(24):
  weekday_hoa_data[i] = rows_to_data(weekday_hoas[(i,)])

hoa_8 = weekday_hoa_data[8]
hoa_17 = weekday_hoa_data[17]
hoa_20 = weekday_hoa_data[20]
hoa_1 = weekday_hoa_data[1]


## ECDF Comparisons ##

#plot
Stats.compare_ecdfs(None,{'8 am':hoa_8,
                          '5 pm':hoa_17,
                          '8 pm':hoa_20,
                          '1 am':hoa_1},
                    plot_CIs=False, plot_Es=False,
                    plot_E_CIs = False)

#excel printout
ecdfs = {}
for whoa,data in weekday_hoa_data.items():
  ecdfs[whoa] = Stats.ecdf(data,weighted=True);
EP.copy(EP.print_ecdfs(ecdfs))

## Prob. of Transfer Comparisons ##

pot_8 = Stats.p_make_transfer_vs_window(hoa_8,doplot=False)
pot_17 = Stats.p_make_transfer_vs_window(hoa_17,doplot=False)
pot_20 = Stats.p_make_transfer_vs_window(hoa_20,doplot=False)
pot_1 = Stats.p_make_transfer_vs_window(hoa_1,doplot=False)

figure()
plot(pot_overall[:,0],pot_overall[:,1],label="Overall")
plot(pot_8[:,0],pot_8[:,1],label="8 am")
plot(pot_12[:,0],pot_12[:,1],label="Noon")
plot(pot_17[:,0],pot_17[:,1],label="5 pm")
plot(pot_1[:,0],pot_1[:,1],label="1 am")

xlabel("Transfer window (s)")
ylabel("Probability of making transfer")
title("Probability of making transfer vs transfer windows")
legend(loc=4)


## Expected Wait Time Comparisons ##


ewait_17 = Stats.expected_wait_vs_arrival_plot(hoa_17, 
                                               headways=(60*15,60*30),
                                               min_arrival=-10*60, 
                                               weighted=True,
                                               ofile="ew_5pm.png")

ewait_1 = Stats.expected_wait_vs_arrival_plot(hoa_1, headways=(60*15,60*30),
                                              min_arrival=-10*60, weighted=True,
                                              ofile="ew_1am.png")


## E/Q values ##

qs=[0.25,0.5,0.75]
Qs,Es = Stats.QEPlot(weekday_hoa_data,qs,weighted=True)
EP.copy(EP.print_QE_tables(Qs,Es,qs))

## Trip Plan Sim ##
xfer_arrive_data = weekday_hoa_data[7]
xfer_depart_data = weekday_hoa_data[7]
dest_arrive_data = weekday_hoa_data[8]

xfer_arrive_time = 7*3600 + 30*60 # 7:30 am
xfer_depart_times = array([ 7*3600 + 10*60, 
                      7*3600 + 30*60, 
                      7*3600 + 50*60,
                      8*3600 + 10*60])
dest_arrive_times = xfer_depart_times + 20*60 #20 minutes later

dest_arrive_results = Stats.trip_plan_evaluation_sim(
  xfer_arrive_data, xfer_arrive_time,
  xfer_depart_data, xfer_depart_times,
  dest_arrive_data, dest_arrive_times);

w_ecdf,p_ecdf,e_ecdf = Stats.ecdf(dest_arrive_results,weighted=False,alpha=0.05)
wmean,err = Stats.E(w_ecdf[w_ecdf<Inf], weighted=False)
figure()
plot(w_ecdf[w_ecdf<Inf],p_ecdf[w_ecdf<Inf], label="Arrival ECDF")
plot( [28800,28800], [0,1], label="8 am" )
plot( [wmean,wmean], [0,1], label="Average arrival time" )
axis((27400,31000,0,1))



### Route Portion Plots ###

begin_route_rows = []
mid_route_rows = []
end_route_rows = []
for k in portions.keys():
  if k[0] < 25: begin_route_rows += portions[k]
  elif k[0] < 75: mid_route_rows += portions[k]
  else: end_route_rows += portions[k]

portion_data = {}
portion_data['Start of Route'] = rows_to_data(begin_route_rows)
portion_data['Middle of Route'] = rows_to_data(mid_route_rows)
portion_data['End of Route'] = rows_to_data(end_route_rows)

begin_data = portion_data['Start of Route']
mid_data = portion_data['Middle of Route']
end_data = portion_data['End of Route']

# ECDF Comparison #

ecdfs = {}
for k,v in portion_data.items():
  ecdfs[k] = Stats.ecdf(v,weighted=True)

EP.copy(EP.print_ecdfs(ecdfs))

# E/Q Values #

qs=[0.25,0.5,0.75]
stopnums = {}
for (sn,),rows in stop_numbers.items():
  stopnums[sn] = rows_to_data(rows);

Qs,Es = Stats.QEPlot(stopnums,qs,weighted=True)
EP.copy(EP.print_QE_tables(Qs,Es,qs))

# Expected Wait #
del rows
ewait_begin = Stats.expected_wait_vs_arrival_plot(begin_data, 
                                                  headways=(60*15,60*30),
                                                  min_arrival=-10*60, 
                                                  weighted=True,
                                                  ofile="ew_beg.png")

ewait_mid = Stats.expected_wait_vs_arrival_plot(mid_data, 
                                                headways=(60*15,60*30),
                                                min_arrival=-10*60, 
                                                weighted=True,
                                                ofile="ew_mid.png")
EP.copy(EP.print_expected_wait_vs_arrival(ewait_begin))
EP.copy(EP.print_expected_wait_vs_arrival(ewait_mid))



### Day of Week plots ###

weekday_data = rows_to_data(weekday_rows)
weekend_data = rows_to_data(weekend_rows)

del weekend_rows
del weekday_rows
del sids
del rows

# ECDF Comparison #
ecdfs = {'Weekdays':Stats.ecdf(weekday_data,weighted=True),
         'Weekends':Stats.ecdf(weekend_data,weighted=True)}
EP.copy(EP.print_ecdfs(ecdfs))

# E/Q Values #

# unused because pylab can't handle categories (stupid)
# but kept here for reference.
dowmap = { 0:'Sunday',
           1:'Monday',
           2:'Tuesday',
           3:'Wednesday',
           4:'Thursday',
           5:'Friday',
           6:'Saturday' }

qs=[0.25,0.5,0.75]
for (dow,),d in dows.items():
  dows[dow] = rows_to_data(d)
  del dows[(dow,)]
  del d

Qs,Es = Stats.QEPlot(dows,qs,weighted=True)
EP.copy(EP.print_QE_tables(Qs,Es,qs))
