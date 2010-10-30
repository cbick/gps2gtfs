

begin;

create index obs_attr_ix 
  on observation_attributes (trip_id, stop_sequence, day_of_week);

create index simpl_late_ix
  on simplified_lateness_observations (minutes_late, observed_stop_id);

alter table observation_attributes add constraint obs_attr_pkey
  primary key (observed_stop_id);

alter table simplified_lateness_observations 
  add constraint simpl_late_obsid_fkey
  foreign key (observed_stop_id) 
  references observation_attributes(observed_stop_id);



commit;
