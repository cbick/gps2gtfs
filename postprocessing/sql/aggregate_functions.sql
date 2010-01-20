-- Requires the pl/R language to be installed

CREATE or REPLACE FUNCTION r_median(_float8) 
	returns float as $BODY$ median(arg1) $BODY$ language 'plr';

CREATE AGGREGATE median (
  sfunc = plr_array_accum,
  basetype = float8,
  stype = _float8,
  finalfunc = r_median
);

create or replace function r_mad(_float8)
       returns float as $BODY$ mad(arg1) $BODY$ language 'plr';

create aggregate MAD (
  sfunc = plr_array_accum,
  basetype = float8,
  stype = _float8,
  finalfunc = r_mad
);
