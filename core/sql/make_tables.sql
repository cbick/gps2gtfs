drop table vehicle_track cascade;
drop table config cascade;

begin;

create table vehicle_track (
  id   text ,
  routeTag text ,
  dirTag text ,
  lat numeric ,
  lon numeric ,
  secsSinceReport int ,
  predictable text ,
  heading int ,
  update_time timestamp ,
  reported_update_time timestamp
  
);

CREATE TABLE routeid_dirtag (
    route_id text,
    dirtag text
);

create table config (
  key text,
  value text

);

insert into config (key,value) values ('key','460656910362');

-- create table service_combo_ids
-- (
-- combination_id serial --primary key
-- );

-- create table service_combinations
-- (
-- combination_id int , --references service_combo_ids(combination_id),
-- service_id text --references gtf_calendar(service_id)
-- );

create table tracked_routes (
  global_id serial , --primary key
  gps_segment_id bigint , --represents gps_segments(gps_segment_id)
  lat numeric ,
  lon numeric ,
  reported_update_time timestamp 

);


create table gps_stop_times (
  gps_segment_id bigint , --references gps_segments(gps_segment_id)
  stop_id text,
  stop_sequence integer,
  stop_headsign text,
  pickup_type integer,
  drop_off_type integer,
  shape_dist_traveled numeric,
  timepoint integer,
  arrival_time_seconds integer,
  departure_time_seconds integer,
  actual_arrival_time_seconds integer,
  actual_departure_time_seconds integer,
  seconds_since_last_stop integer,
  prev_stop_id text
);


create table gps_segments (
  gps_segment_id bigint , --unique identifier for this gps trip
  trip_id text, --references gtf_trips(trip_id)
  schedule_error numeric, --unique for (trip_id,trip_date) only
  schedule_offset_seconds integer, --seconds to subtract from GTFS times
  trip_date date, --the day of the trip
  vehicle_id text  --same as in vehicle_track

);


create table gtf_trip_information (
  trip_id text, --references gtf_trips(trip_id)
  first_arrival integer,
  first_departure integer,
  trip_length_meters numeric,
  trip_duration_seconds integer
  
);

create table gtf_stoptimes_information (
  trip_id text, --references gtf_trips(trip_id)
  stop_sequence integer, --references gtf_stop_times(stop_sequence)
  trip_stop_number integer, -- the number of this stop along the trip
  prev_stop_distance_meters numeric, --distance from previous stop to this one
  cumulative_distance_meters numeric, --distance of the trip up to this stop
  travel_time_seconds integer --according to the schedule, how long it takes
                              --to get from the previous stop to this stop.
);

commit;
