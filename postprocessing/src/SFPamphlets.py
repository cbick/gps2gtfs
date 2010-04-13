import Stats
import dbutils as db
from Stats import DM


# shorthand
split = DM.split_on_attributes
array = Stats.array

def rows_to_data(rows):
    return array([(r['lateness'], r['trip_stop_weight']) for r in rows]);


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


data = rows_to_data(rows)
del rows
weekend_data = rows_to_data(weekend_rows)
del weekend_rows
saturday_data = rows_to_data(saturday_rows)
sunday_data = rows_to_data(sunday_rows)
weekday_data = rows_to_data(weekday_rows)
del saturday_rows,sunday_rows,weekday_rows

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


pot_overall = Stats.p_make_transfer_vs_window(data,doplot=False)
pot_8 = Stats.p_make_transfer_vs_window(hoa_8,doplot=False)
#pot_12 = Stats.p_make_transfer_vs_window(hoa_12,doplot=False)
pot_17 = Stats.p_make_transfer_vs_window(hoa_17,doplot=False)
pot_20 = Stats.p_make_transfer_vs_window(hoa_20,doplot=False)
pot_1 = Stats.p_make_transfer_vs_window(hoa_1,doplot=False)
pot_weekend = Stats.p_make_transfer_vs_window(weekend_data,doplot=False)
pot_weekday = Stats.p_make_transfer_vs_window(weekday_data,doplot=False)
pot_saturday = Stats.p_make_transfer_vs_window(saturday_data,doplot=False)
pot_sunday = Stats.p_make_transfer_vs_window(sunday_data,doplot=False)
pot_end_to_begin = Stats.p_make_transfer_vs_window(end_data,begin_data,
                                                   doplot=False)
pot_end_to_mid = Stats.p_make_transfer_vs_window(end_data,mid_data,
                                                 doplot=False)
pot_mid_to_mid = Stats.p_make_transfer_vs_window(mid_data,
                                                 doplot=False)
pot_mid_to_begin = Stats.p_make_transfer_vs_window(mid_data,begin_data,
                                                   doplot=False)

potlabs = {}
potlabs['Overall'] = pot_overall;
potlabs['8am Weekday'] = pot_8;
potlabs['5pm Weekday'] = pot_17;
potlabs['8pm Weekday'] = pot_20;
potlabs['1am Weekday'] = pot_1;

potlabs['Weekday'] = pot_weekday
potlabs['Saturday'] = pot_saturday
potlabs['Sunday'] = pot_sunday

potlabs['End to Start'] = pot_end_to_begin;
potlabs['End to Middle'] = pot_end_to_mid;
potlabs['Middle to Middle'] = pot_mid_to_mid;
potlabs['Middle to Start'] = pot_mid_to_begin;


figure()
plot(pot_overall[:,0],pot_overall[:,1],'k',label="Overall")

plot(pot_8[:,0],pot_8[:,1],'--',label="8 am Weekday")
plot(pot_17[:,0],pot_17[:,1],'--',label="5 pm Weekday")
plot(pot_1[:,0],pot_1[:,1],'--',label="1 am Weekday")

plot(pot_end_to_begin[:,0],pot_end_to_begin[:,1],
     ':',label="End to Start",linewidth=2)
plot(pot_end_to_mid[:,0],pot_end_to_mid[:,1],
     ':',label="End to Middle",linewidth=2)
plot(pot_mid_to_mid[:,0],pot_mid_to_mid[:,1],
     ':',label="Middle to Middle",linewidth=2)
plot(pot_mid_to_begin[:,0],pot_mid_to_begin[:,1],
     ':',label="Middle to Start",linewidth=2)

xlabel("Transfer window (s)")
ylabel("Probability of making transfer")
title("Probability of making transfer vs transfer windows")
legend(loc=4)





#########################################################
#########################################################
#########################################################





