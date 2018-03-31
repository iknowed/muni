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
stop_id = graph_db.get_or_create_index(neo4j.Node, "stop_id")
print stop_id
stop_tag = graph_db.get_or_create_index(neo4j.Node, "stop_tag")
print stop_tag

proj4 = '+proj=lcc +lat_1=37.06666666666667 +lat_2=38.43333333333333 +lat_0=36.5 +lon_0=-120.5 +x_0=2000000 +y_0=500000.0000000001 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=us-ft +no_defs'
srid='100000'
ccsf = SpatialReference(proj4)
wgs84 = SpatialReference('WGS84')
ct = CoordTransform(wgs84,ccsf)

def fixlat(n):
    return float(n)
    lat = float(n)- 37.0
    lat = lat * (pow(10,(len(str(lat)) - 2)))
    return int(lat)

def fixlon(n):
    return float(n)
    lon = float(n) + 122.0
    lon = -1.0 * lon * (pow(10,(len(str(lon)) - 3)))
    return int(lon)
   

def latlon2city(lon,lat):
  lat = float(lat)
  lon = float(lon)

  west = -122.515003
  east = -122.355684
  north = 37.832365
  south = 37.706032
  
  
  west_coord_1 = 5973058
  east_coord_1 = 6022571
  north_coord_1 = 2132800
  south_coord_1 = 2085080

  west_coord = 5979762.107179
  east_coord = 6024890.063509
  north_coord = 2130875.573550
  south_coord = 2085798.824452

  west_delta = west_coord - west_coord_1 
  east_delta = east_coord - east_coord_1
  north_delta = north_coord - north_coord_1
  south_delta = south_coord - south_coord_1
  
  lon_range = abs(abs(west) - abs(east)) 
  lat_range = north - south 

  ew_range = (east_coord - west_coord) 
  ns_range = (north_coord - south_coord) 
  
  lat_pct = (north - lat)/lat_range
  lon_pct = (abs(west) - abs(lon))/lon_range
  
  #x = west_coord + (lon_pct * ew_range)
  #y = south_coord + (lat_pct * ns_range)
  x = west_coord + (lon_pct * ew_range) 
  y = north_coord - (lat_pct * ns_range) 

  point = "POINT("+str(lon)+" "+str(lat)+")"
  geom = OGRGeometry(point)
  geom.transform(ct)
  res = geom.ewkt
  r = re.compile('([0-9\.]+)')
  (x,y) = r.findall(res)
  return((x,y))
  return((float(x),float(y)))

      #cursor = connection.cursor()
      #cursor.execute(sql,[direction.id,direction_stop.stop_id])
      #row = cursor.fetchone()
      #if(row == None):

conn1 = psycopg2.connect("dbname=municonsole1")
cur1 = conn1.cursor()
#sql = "select l.tag,l.line,r.tag from lines l left outer join muni_route r on ( l.tag=r.tag)"
#cur1.execute(sql)

for line in Line.objects.all():
  #if(line.tag != '14' and line.tag != '22'):
  #  continue
  route = Route.objects.filter(tag=line.tag)
  for dir in Direction.objects.filter(route=route):
    stop1 = None
    stop2 = None
    if(dir.name == 'Outbound'):
      direction = 1
    if(dir.name == 'Inbound'):
      direction = 0
    for stop in DirectionStop.objects.filter(direction=dir).order_by('seq'):
      if(stop1 == None):
        stop1 = stop
        continue
      stop2 = stop1
      stop1 = stop
      cur1 = conn1.cursor()
      sql = "select ST_Line_Locate_Point(l.line_geom,s1.loc),ST_Line_Locate_Point(l.line_geom,s2.loc) from muni_stop s1, muni_stop s2, muni_line l where (s1.stop_id=%s and s2.stop_id=%s) and (l.tag = %s and l.direction = %s)"
      cur1.execute(sql,(str(stop1.stopid),str(stop2.stopid),line.tag,str(direction)))
      row = cur1.fetchone()
      if(row == None):
        break
      s1pos = row[0]
      s2pos = row[1]
      if(s1pos > s2pos):
         smaller = s2pos
         larger = s1pos
      else:
         smaller = s1pos
         larger = s2pos
      sql = "select ST_Length(ST_Line_Substring(l.line_geom,%s,%s )) from muni_line l where l.tag= %s and l.direction = %s"
      cur1.execute(sql,(smaller,larger,line.tag,line.direction))
      dist, = cur1.fetchone()
      if(row == None):
        break
      qy = "\
        START \
          s1=node:stop_id(stop_id = \""+stop1.stop.stop_id+"\"), \
          s2=node:stop_id(stop_id = \""+stop2.stop.stop_id+"\") \
          CREATE s1-[r:GOESTO{ dist : "+str(dist)+" , route_tag : \""+line.tag+"\" , dir_tag : \""+dir.tag+"\" , direction : \""+dir.name+"\" , transfer : 0 }]->s2 \
        RETURN r"
      rel = cypher.execute(graph_db,qy)
      print rel
      
      
