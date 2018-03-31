from urllib2 import urlopen
import sys
import os
import django
sys.path.append('./django/municonsole')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from xml.dom import minidom
import formatter
import psycopg2
import time
import math
import re
import os
import muni
import csv
from muni.models import Vehicle
from muni.models import Route
from muni.models import RouteStop
from muni.models import Run
from muni.models import Path
from muni.models import Point
from muni.models import Stop
from muni.models import Direction
from muni.models import DirectionStop
from muni.models import DirectionPath
from muni.models import Speed
from muni.models import Line
import django.contrib.gis
from django.db import connection, transaction
from django.contrib.gis.gdal import SpatialReference, CoordTransform,OGRGeometry
from py2neo import neo4j, cypher
graph_db = neo4j.GraphDatabaseService("http://cybre.net:7474/db/data/")

conn1 = psycopg2.connect("dbname=municonsole1")
cur1 = conn1.cursor()
#sql = "select l.tag,l.line,r.tag from lines l left outer join muni_route r on ( l.tag=r.tag)"
#cur1.execute(sql)

for route in Route.objects.all():
  for dir in Direction.objects.filter(route=route):
    for stop in DirectionStop.objects.filter(direction=dir):
      sql = "select \
            s2.stop_id,r.line,d.tag \
        from \
            muni_stop s1, \
            muni_stop s2, \
            muni_directionstop ds, \
            muni_direction d, \
            muni_route r \
        where \
            (s1.stop_id=%s) \
        and \
            (ST_Distance(s1.loc,s2.loc) < 100) \
        and \
            (s1.stop_id != s2.stop_id and ds.stop_id=s2.id and ds.direction_id=d.id and d.route_id = r.id)"
      cur1.execute(sql,[stop.stop.stop_id])
      for trans in cur1.fetchall():
        trans_stop_id = trans[0]
        trans_line = trans[1]
        trans_dir_tag = trans[2]
        express = 0
        if(trans_dir_tag.find('X') != -1):
          express = 1
        if((trans_line == route.line) and not express):
          continue
        qy = " \
          START \
            s1=node:stop_id(stop_id = \""+str(stop.stop.stop_id)+"\"), \
            s2=node:stop_id(stop_id = \""+str(trans_stop_id)+"\") \
            CREATE s1-[r:GOESTO{ transferfromroute: \""+route.line+"\" , transfertoroute: \""+trans_line+"\" , transferfromdir : \""+dir.tag+"\" , transfertodir : \""+trans_dir_tag+"\" , to_express : "+str(express)+" }]->s2 \
          RETURN r"
        print qy
        #rel = cypher.execute(graph_db,qy)
        #print rel
      
      
