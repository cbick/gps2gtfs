select 
CASE 
  WHEN scheduled_arrival_time < 0 THEN (scheduled_arrival_time+86400)/3600
  WHEN scheduled_arrival_time >= 86400 THEN (scheduled_arrival_time-86400)/3600
  ELSE scheduled_arrival_time/3600
END as hour_of_arrival,
route_name, vehicle_type,service_id,stop_lat,stop_lon,stop_number,
stop_distance/trip_length as route_proportion,
count(*) as num, avg(lateness) as mean, stddev(lateness) as std

from datamining_table 
where lateness is not null group by stop_id,route_name,gtfs_trip_id,vehicle_type,service_id,
stop_lat,stop_lon,stop_number,stop_distance,trip_length,
CASE 
  WHEN scheduled_arrival_time < 0 THEN (scheduled_arrival_time+86400)/3600
  WHEN scheduled_arrival_time >= 86400 THEN (scheduled_arrival_time-86400)/3600
  ELSE scheduled_arrival_time/3600
END
having count(*) >= 10;






select routes.route_short_name as route_name,
       stops.stop_id as stop_id,
       trips.trip_id as gtfs_trip_id,
       rtypes.description as vehicle_type,
       trips.service_id as service_id,
       stops.stop_lat as stop_lat,
       stops.stop_lon as stop_lon,
       gsti.trip_stop_number as stop_number,
       gsti.cumulative_distance_meters/gti.trip_length_meters 
         as route_proportion,
       gsti.cumulative_distance_meters as dist_into_route,
       gsti.prev_stop_distance_meters as prev_stop_distance,
CASE WHEN gti.first_arrival < 0 THEN (gti.first_arrival+86400)/3600
     WHEN gti.first_arrival >= 86400 THEN (gti.first_arrival-86400)/3600
     ELSE gti.first_arrival/3600
END as hour_of_trip_start,

agg_dmt.hour_of_arrival, agg_dmt.num, agg_dmt.mean, agg_dmt.std

from 
(select gtfs_trip_id,stop_sequence,stop_id,
  CASE 
   WHEN scheduled_arrival_time < 0 THEN (scheduled_arrival_time+86400)/3600
   WHEN scheduled_arrival_time >= 86400 THEN (scheduled_arrival_time-86400)/3600
   ELSE scheduled_arrival_time/3600
  END as hour_of_arrival,
  count(*) as num, avg(lateness) as mean, stddev(lateness) as std
 from datamining_table
 where lateness is not null
 group by gtfs_trip_id,stop_sequence,stop_id,
   CASE 
   WHEN scheduled_arrival_time < 0 THEN (scheduled_arrival_time+86400)/3600
   WHEN scheduled_arrival_time >= 86400 THEN (scheduled_arrival_time-86400)/3600
   ELSE scheduled_arrival_time/3600
   END
) agg_dmt
inner join gtf_stoptimes_information gsti
  on gsti.trip_id = agg_dmt.gtfs_trip_id
  and gsti.stop_sequence = agg_dmt.stop_sequence
inner join gtf_trip_information gti
  on gti.trip_id = agg_dmt.gtfs_trip_id
inner join gtf_trips trips
  on trips.trip_id = agg_dmt.gtfs_trip_id
inner join gtf_routes routes
  on routes.route_id = trips.route_id
inner join gtfs_route_types rtypes 
  on rtypes.route_type=routes.route_type
inner join gtf_stops stops
  on stops.stop_id = agg_dmt.stop_id
where num >= 5
;
