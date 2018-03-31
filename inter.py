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

conn1 = psycopg2.connect("dbname=municonsole1")
cur1 = conn1.cursor()
cur2 = conn1.cursor()
lines_checked = {}
geom_types = {}
points_seen = {}
stops_seen = {}
transfers = {}

def processPoint(point):
  if(point in points_seen):
    return
  points_seen[point] = 1
  cur = conn1.cursor()
  sql = "select distinct(s.stop_id,s.title,r.tag,d.tag),s.stop_id,s.title,r.tag,d.name from muni_stop s, muni_directionstop ds, muni_direction d, muni_route r  where (ST_Distance(s.loc,GeometryFromText('"+point+"',100000)) < 250) and s.id=ds.stop_id and ds.direction_id=d.id and d.route_id=r.id"
  cur.execute(sql)     
  lines = {}
  for res in cur.fetchall():
    dest_stop = res[1]
    dest_title = res[2]
    if(dest_title.find('Market') != -1): 
      continue
    dest_tag = res[3]
    dest_dir = res[4]
    if(dest_tag not in lines):
      lines[dest_tag] = {}
    lines[dest_tag][dest_dir] =  { "stop" : dest_stop  , "title" : dest_title }
  
  if(lines == {}):
    return  
  for line1 in lines.keys():
    for line2 in lines.keys():
      if(line1 == line2):
        continue
      dests1 = lines[line1]
      dests2 = lines[line2]
      for dest1 in dests1.keys():
        for dest2 in dests2.keys():
          if(dest1 == dest2):
            continue
          if((re.match(r"^[KTLMN]$",line1) != -1) and (dest_tag.find("OWL") != -1)):
            continue
          if((re.match(r"^[KTLMN] OWL$",line1) != None) and (re.match(r"^[KTLMN]",dest1) != None)):
            continue
          stop1 = dests1[dest1]['stop']
          stop2 = dests2[dest2]['stop']
          title1 = dests1[dest1]['title']
          title2 = dests2[dest2]['title']
          outline = line1 + " " + dest1 + " " + title1 + " "  + stop1 + " " + line2 + " " + dest2 + " "  + title2 + " " + stop2
          #print outline
          #out_dict = { 'source_line' : line1, 'source_dest' : dest1, 'source_title' : title1, 'source_stop' : stop1, 'dest_line' : line2 , 'dest_dest' : dest2, 'dest_title' : title2 , 'dest_stop' : stop2 }
          #transfers[outline] = out_dict
          express = ""
          m = re.match(r'^[^X^L]+([XL])$',line2)
          if(m):
            express = m.group(1)
          qy = " \
            START \
              s1=node:stop_id(stop_id = \""+stop1+"\"), \
              s2=node:stop_id(stop_id = \""+stop2+"\") \
              CREATE s1-[r:GOESTO{ \
                source_line : \""+line1+"\" , \
                dest_line : \""+line2+"\" , \
                source_dir : \""+dest1+"\" , \
                dest_dir : \""+dest2+"\" , \
                to_express : \""+express+"\", \
                dist : 0, \
                transfer : 1 \
              }]->s2 \
            RETURN r"
          print qy
          continue
          if qy in transfers:
            return
          transfers[qy] = 1
          #rel = cypher.execute(graph_db,qy)
          #print qy


def processGeometry(geom):
  sql = "SELECT ST_AsEWKT(a.geom) FROM ( SELECT (ST_Dump(p_geom)).geom as geom FROM (SELECT ST_GeomFromEWKT('"+geom[0]+"') as p_geom) as b) as a;"
  cur2.execute(sql)
  geoms = cur2.fetchall()
  for geom in geoms:
    if(geom == None):
      break
    res = re.match(r'^([A-Z]+)\(.*$',geom[0])
    geom_type = res.group(1)
    if(geom_type == 'MULTILINESTRING'):
      continue
    if(geom_type == 'LINESTRING'):
      continue
    if(geom_type == 'MULTIPOINT'):
      processGeometry(geom[0])
    if(geom_type == 'GEOMETRYCOLLECTION'):
      processGeometry(geom[0])
    if(geom_type == 'POINT'):
      processPoint(geom[0])


for line1 in Line.objects.order_by('tag'):
  points = {}
  for line2 in Line.objects.order_by('tag'):
  # if((line1.tag != '14' or line1.tag != '22') and (line2.tag != '14' or line2.tag != '22')):
     # continue
    #if(line2.tag in lines_checked):
    #  continue

    # don't connect this line to this line
    if(line1.tag == line2.tag):
      continue 

    # don't connect metro to owl
    if((re.match(r"^[KTLMN][X]*$",line1.tag) != -1) and (line2.tag.find("OWL") != -1)):
      continue
    if((re.match(r"^[KTLMN] OWL$",line1.tag) != None) and (re.match(r"^[KTLMN][X]*$",line2.tag) != None)):
      continue

    sql = "select distinct(ST_AsText(ST_Intersection(l1.line_geom,l2.line_geom))) from muni_line l1, muni_line l2 where l1.tag=%s and l2.tag=%s and l2.tag != l1.tag"
    cur1.execute(sql,(line1.tag,line2.tag)) 
    geoms = cur1.fetchall()
    for geom in geoms:
      processGeometry(geom)
    if(points.__len__() == 0):
      continue
  lines_checked[line1.tag] = 1

print transfers.__len__()
