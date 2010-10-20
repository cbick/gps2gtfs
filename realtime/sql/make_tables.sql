drop table observation_attributes cascade;
drop table simplified_lateness_observations cascade;

begin;

-- These are similar to the datamining table which is
-- created as an output of the datamining query
-- found in the postprocessing directory.
-- It basically contains lateness observations along
-- with their attributes, for use with the xml API.
-- The primary difference is that it discretizes the observations
-- to the resolution of one minute, instead of one second.

create table observation_attributes (
  -- unique reference (primary key)
  observed_stop_id integer,

  -- identifying values
  trip_id text,
  stop_id text,
  stop_sequence integer,
  day_of_week integer,

  -- redundant values
  route_name text,
  vehicle_type integer,
  service_id integer,
  direction_id integer,
  scheduled_arrival_time integer,
  hour_of_day integer

);

create table simplified_lateness_observations (
  minutes_late integer, -- how many minutes late the bus was
  num_observations integer, -- how many times we saw it be this late
  observed_stop_id integer -- references observation_attributes
);


commit;
