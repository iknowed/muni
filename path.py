import requests
import re
from py2neo import neo4j, cypher

graph_db = neo4j.GraphDatabaseService("http://cybre.net:7474/db/data/")
stop_id = graph_db.get_or_create_index(neo4j.Node, "stop_id")
print stop_id
stop_tag = graph_db.get_or_create_index(neo4j.Node, "stop_tag")
print stop_tag

qy1 = "START n=node(*) WHERE n.stop_id='14281' RETURN n"
qy2 = "START n=node(*) WHERE n.stop_id='14337' RETURN n"
s1 = cypher.execute(graph_db,qy1)
s2 = cypher.execute(graph_db,qy2)
n1 = re.match(r'^.*/([\d]+)\'.*$',str(s1))
u1 = n1.group(1)
uri = "http://localhost:7474/db/data/node/00/paths"
uri = re.sub(r'00',str(u1),uri)
n2 = re.match(r'^.*\'([^\']+)\'.*$',str(s2))
u2 = n2.group(1)

print uri
payload = "{ \"to\" : \""+u2+"\" , \"cost_property\" : \"dist\", \"relationships\" : { \"type\" : \"GOESTO\" , \"direction\" : \"out\"} , \"algorithm\" : \"dijkstra\" }"
print payload
#r = requests.post(uri, data=payload)
#print r.text

