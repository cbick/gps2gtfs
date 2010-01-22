names=BusTrack GPSDataTools GPSBusTrack GTFSBusTrack dbqueries
ppath=$(PYTHONPATH):../core/src/:../common/src/

doc::
	for name in $(names); do \
	  env PYTHONPATH=$(ppath) pydoc -w $$name; \
	  echo $$name; \
	done;
