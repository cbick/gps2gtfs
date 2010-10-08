#!/bin/bash

for f in `find ~/dev/DATA/gps -name \*.xml`; do 
    t=`basename $f | sed 's,[.].*,,g'`; 
    cat $f | sed 's,<lastTime.*/>,<retrieveTime time="'$t'"/>,g' > $f.tmp; 
    python test.py $1 $f.tmp;  
    rm $f.tmp
done
