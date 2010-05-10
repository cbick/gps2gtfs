BEGIN;

update gtfs_directions set description = 'Inbound' where direction_id=1;
update gtfs_directions set description = 'Outbound' where direction_id=0;

COMMIT;
