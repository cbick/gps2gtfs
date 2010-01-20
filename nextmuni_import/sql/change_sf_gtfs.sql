BEGIN;

update gtf_routes set route_short_name='3' where route_id='1003';
update gtf_routes set route_short_name='4' where route_id='1004';
update gtf_routes set route_short_name='31AX' where route_id='1031';
update gtf_routes set route_short_name='31BX' where route_id='1032';
update gtf_routes set route_short_name='1AX' where route_id='1033';
update gtf_routes set route_short_name='1BX' where route_id='1034';
update gtf_routes set route_short_name='F' where route_id='3725';
update gtf_routes set route_short_name='30X' where route_id='3731';
update gtf_routes set route_short_name='38L' where route_id='3732';


COMMIT;