from datetime import timedelta
import dbutils as db

class ServiceDateHandler(object):
  """
  A ServiceDateHandler translates between GTFS "service IDs" and
  actual calendar dates. In other words it helps you figure out
  what buses are running on a certain day.

  Optionally, a ServiceDateHandler can populate an unprocessed 
  database with the information necessary to do its job.
  """
  
  def __init__(self,dbconn,autoFill=False,autoCommit=False):
    """
    Creates a ServiceDateHandler using the database from dbconn.
    If autoFill is True, then any missing service combinations
    are added to the database. If autoCommit is True, these
    changes will be committed immediately.
    """
    cur = db.get_cursor()

    ## Prepare calendar data
    
    db.SQLExec(cur,"""select monday,tuesday,wednesday,thursday,friday,saturday,
                 sunday, service_id, start_date, end_date from gtf_calendar""");
    self.calendar_rows = cur.fetchall();
    db.SQLExec(cur,"""select * from gtf_calendar_dates""");
    self.calendar_date_rows = cur.fetchall();

    ## Load existing combos

    db.SQLExec(cur,"""select * from service_combinations 
                   order by combination_id, service_id""");
    service_combo_rows = cur.fetchall();

    self.combos = {};  # map from combo_id to combo
    # note that combo lists are sorted by service_id
    for row in service_combo_rows:
      service_id, combo_id = row['service_id'],int(row['combination_id']);
      if not self.combos.has_key(combo_id):
        self.combos[combo_id] = []
      self.combos[combo_id].append(service_id)

    # map from combo to combo_id (reverse of self.combos)
    self.existing_combos = {}; 
    for combo_id in self.combos:
      self.existing_combos[tuple(self.combos[combo_id])] = int(combo_id);
    
    cur.close()

    ## Fill in missing combos

    if autoFill:
      self.fill_unique_service_combinations(dbconn,autoCommit);


  @staticmethod
  def parseDate(text):
    """Given a date in yyyy-mm-dd format, returns a datetime.date object"""
    #date conveniently returned in format yyyy-mm-dd
    return date(*map(int,text.split("-")))



  def effective_service_ids(self,day):
    """Given a day (date object), returns a collection of service IDs
    that are in effect on that day"""
    service_ids = set()
    dayOfWeek = day.weekday() #0-6 for Mon-Sun
    for row in self.calendar_rows:     
      # recall we selected mon,tues,... first in the query
      if int(row[dayOfWeek]): 
        #this service runs on this day of the week
        if row['start_date'] <= day and row['end_date'] >= day: 
          #this service applies to this date
          service_ids.add(row['service_id']);

    for row in self.calendar_date_rows:
      rowDate = row['date'];
      if rowDate == day:
        if int(row['exception_type'])-2: # 1 means added, 2 means removed
          #so this means added
          service_ids.add(row['service_id']);
        else:
          #and this means removed
          service_ids.discard(row['service_id']);
          
    ret = list(service_ids);
    ret.sort(); # to prevent permuted duplicates
    return tuple(ret);



  def getComboID(self,day):
    service_ids = tuple(self.effective_service_ids(day));
    if self.existing_combos.has_key(service_ids):
      return self.existing_combos[service_ids]
    return None

  def getCombos(self):
    ret= {}; ret.update(self.combos);
    return ret;


  def fill_unique_service_combinations(self,dbconn,commit):
    """Throughout all dates which have service IDs in effect, this method
    finds every unique combination of service IDs that are in effect
    simultaneously. The service_combinations table is then populated with
    a 1-to-many map from combination_id to service_id where each combination_id
    represents a unique combination of service IDs. If a matching combination_id
    already exists, then it is left alone."""

    cur = db.get_cursor()  
  
    ## Find all unique combos in effective service dates, put new
    ## ones in db

    db.SQLExec(cur,"""select min(start_date), max(end_date) from 
                    (select start_date, end_date from gtf_calendar 
                    union select date as start_date, date as end_date 
                    from gtf_calendar_dates) as t""");

    min_date,max_date = cur.fetchone()[0:2]    
    one_day = timedelta(days=1);

    day = min_date  
    while day <= max_date:
      service_ids = tuple(self.effective_service_ids(day));

      # If it already exists, don't do anything
      if self.existing_combos.has_key(service_ids):
        pass;
      # Otherwise, put it in the db
      else:
        db.SQLExec(cur,"""insert into service_combo_ids values (DEFAULT)""");
        db.SQLExec(cur,"""select currval('service_combo_ids_combination_id_seq')""");
        combo_id = int(cur.fetchone()[0]);

        self.existing_combos[service_ids] = combo_id;
        self.combos[combo_id] = service_ids;

        insert_sql = """insert into service_combinations (combination_id,
                        service_id) values (%(combo)s,%(service)s)"""

        if __debug__:
          db.SQLExec(cur,"""select count(*) from gtf_trips 
                         where service_id in ('%(sids)s')""" %
                      {'sids':"','".join(service_ids)}
                  );
          print "======== Creating Combo ========="
          print "ID:",combo_id
          print "Service IDs:",service_ids
          print "Trips with ID:",cur.fetchone()[0]
          print "================================="
          print

        for service_id in service_ids:
          db.SQLExec(cur,insert_sql,{'combo':str(combo_id),'service':service_id});

      day = day + one_day

    cur.close()
    if commit:
      dbconn.commit()
