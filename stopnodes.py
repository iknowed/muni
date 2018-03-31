#!/usr/bin/python
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
from py2neo import neo4j
graph_db = neo4j.GraphDatabaseService("http://cybre.net:7474/db/data/")
graph_db.clear();

#tag    | character varying(8)  | not null
 #lat    | double precision      | not null
 #lon    | double precision      | not null
 #title  | character varying(64) | not null
# x      | double precision      | not null
 #y      | double precision      | not null
 #loc    | geometry              | not null
 #stopid | character varying(16) | 

stop_id = graph_db.get_or_create_index(neo4j.Node, "stop_id")
print stop_id
stop_tag = graph_db.get_or_create_index(neo4j.Node, "stop_tag")
print stop_tag

for stop in Stop.objects.all():
  print stop.stop_id
  node, = graph_db.create({ "type" : "stop" , "stop_tag" : str(stop.tag) , "lat" : stop.lat , "lon" : stop.lon , "title" : stop.title , "x" : stop.x , "y" : stop.y , "stop_id" : stop.stop_id} )
  stop_id.add("stop_id",stop.stop_id,node)
  stop_tag.add("stop_tag",stop.tag,node)
  

