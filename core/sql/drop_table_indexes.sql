DROP INDEX vehicle_report_times_idx;
DROP INDEX vehicle_id_idx;
DROP INDEX vehicle_routing_idx;
DROP INDEX vehicle_dirtag_idx;
DROP index gpsarr_time_index;
DROP index gpsdep_time_index;
DROP index gpsstop_seq_index;
DROP index segid_track_index;
DROP index seg_sort_idx;
DROP INDEX tripstart_idx;
DROP INDEX tripstart_time_idx;
DROP INDEX tripstart_idtime_idx;
DROP INDEX tripstop_seq_idx;

ALTER TABLE service_combo_ids DROP CONSTRAINT combo_pkey CASCADE;
ALTER TABLE service_combinations DROP CONSTRAINT combo_cid_fkey CASCADE;
ALTER TABLE service_combinations DROP CONSTRAINT combo_sid_fkey CASCADE;
ALTER TABLE tracked_routes DROP CONSTRAINT trackroute_pkey CASCADE;
ALTER TABLE tracked_routes DROP CONSTRAINT trackroute_gpssid_fkey CASCADE;
ALTER TABLE gps_segments DROP CONSTRAINT gpssegs_tid_fkey CASCADE;
ALTER TABLE gps_segments DROP CONSTRAINT gpssegs_pkey CASCADE;
ALTER TABLE gps_stop_times DROP CONSTRAINT gstimes_gstops_fkey CASCADE;
ALTER TABLE gps_stop_times DROP CONSTRAINT gpstimes_sid_fkey CASCADE;
ALTER TABLE gps_stop_times DROP CONSTRAINT gpstimes_ptype_fkey CASCADE;
ALTER TABLE gps_stop_times DROP CONSTRAINT gpstimes_dtype_fkey CASCADE;


