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
from py2neo import neo4j
graph_db = neo4j.GraphDatabaseService("http://cybre.net:7474/db/data/")
graph_db.clear();

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

conn = psycopg2.connect("dbname=routing")
conn1 = psycopg2.connect("dbname=municonsole1")
#cur = conn1.cursor()
#cur.execute("truncate muni_line");
with open('lines.csv', 'rb') as csvfile:
  reader = csv.reader(csvfile, delimiter=',', quotechar='"')
  for csvrow in reader:
    line = csvrow[0]
    dir = csvrow[1]
    shape_id = csvrow[2]
    npoints = csvrow[3]
    cursor = conn.cursor()
    sql = "select shape_pt_lat,shape_pt_lon from shapes where shape_id=%s order by shape_pt_sequence asc"
    cursor.execute(sql,[shape_id])
    points = []
    for point in cursor.fetchall():
      (x,y) = latlon2city(point[1],point[0])
      points.append(str(x) + " " + str(y));
 
    linestring = "LINESTRING(" + ','.join(points) +")"
    #print linestring
    route_tag = re.sub(r'^[0]+',r'',line)
    route_tag = re.sub(r'\-OWL',r' OWL',route_tag)
    route_tag = re.sub(r'(^[\s]+|[\s]+$)',r'',route_tag)
    routes = Route.objects.filter(tag=route_tag)
    print route_tag
    if(route_tag == '81X'):
      continue
    if(routes.__len__() == 0):
      print "no route"
      continue
    r = routes[0]
    #route_id | line | direction | numtag | tag | line_geom
    sql = "insert into muni_line ( line , numtag , tag , route_id, direction , line_geom ) values ('"+line+"','"+r.numtag+"','"+r.tag+"','"+str(r.id)+"','"+dir+"',ST_GeomFromText('"+linestring+"',100000))"
    line_geom = "ST_GeomFromText('"+linestring+"',100000)"
    l = Line(line=line,route_id=r.id,direction=dir,numtag=r.numtag,tag=r.tag,line_geom=linestring)
    l.save()
    #cursor1 = conn1.cursor()
    #cursor1.execute(sql)
    #cursor1.mogrify(sql,(str(line),str(dir),linestring))
      
