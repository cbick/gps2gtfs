
begin;

CREATE INDEX vehicle_report_times_idx ON vehicle_track (reported_update_time);
CREATE INDEX vehicle_id_idx ON vehicle_track (id);
CREATE INDEX vehicle_routing_idx ON vehicle_track (id,routetag,dirtag);
CREATE INDEX vehicle_dirtag_idx ON vehicle_track (dirtag);

create index gpsarr_time_index on gps_stop_times(actual_arrival_time_seconds);
create index gpsdep_time_index on gps_stop_times(actual_departure_time_seconds);
create index gpsstop_seq_index on gps_stop_times(gps_segment_id,stop_sequence);

create index segid_track_index on tracked_routes(gps_segment_id);
create index seg_sort_idx on tracked_routes(gps_segment_id,reported_update_time);



ALTER TABLE gps_segments ADD CONSTRAINT gpssegs_tid_fkey
      FOREIGN KEY (trip_id)
      REFERENCES gtf_trips(trip_id);
ALTER TABLE gps_segments ADD CONSTRAINT gpssegs_pkey
      PRIMARY KEY (gps_segment_id);

ALTER TABLE gps_stop_times ADD CONSTRAINT gstimes_gstops_fkey
      FOREIGN KEY (gps_segment_id)
      REFERENCES gps_segments(gps_segment_id);
ALTER TABLE gps_stop_times ADD CONSTRAINT gpstimes_sid_fkey
      FOREIGN KEY (stop_id)
      REFERENCES gtf_stops(stop_id);
ALTER TABLE gps_stop_times ADD CONSTRAINT gpstimes_ptype_fkey
      FOREIGN KEY (pickup_type)
      REFERENCES gtfs_pickup_dropoff_types(type_id);
ALTER TABLE gps_stop_times ADD CONSTRAINT gpstimes_dtype_fkey
      FOREIGN KEY (drop_off_type)
      REFERENCES gtfs_pickup_dropoff_types(type_id);
ALTER TABLE gps_stop_times 
      ALTER COLUMN stop_sequence SET NOT NULL;


ALTER TABLE service_combo_ids ADD CONSTRAINT combo_pkey
      PRIMARY KEY (combination_id);
ALTER TABLE service_combinations ADD CONSTRAINT combo_cid_fkey
      FOREIGN KEY (combination_id) REFERENCES service_combo_ids(combination_id);
ALTER TABLE service_combinations ADD CONSTRAINT combo_sid_fkey
      FOREIGN KEY (service_id) REFERENCES gtf_calendar(service_id);
ALTER TABLE tracked_routes ADD CONSTRAINT trackroute_pkey
      PRIMARY KEY (global_id);
ALTER TABLE tracked_routes ADD CONSTRAINT trackroute_gpssid_fkey
      FOREIGN KEY (gps_segment_id) 
      REFERENCES gps_segments(gps_segment_id);


create index tripstart_idx on gtf_trip_information(trip_id);
create index tripstart_time_idx on gtf_trip_information(first_departure);
create index tripstart_idtime_idx on gtf_trip_information(trip_id,first_departure);
create index tripstop_seq_idx on gtf_stoptimes_information(trip_id,stop_sequence);


commit;
