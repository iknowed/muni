from py2neo import neo4j, cypher
import fileinput

graph_db = neo4j.GraphDatabaseService("http://cybre.net:7474/db/data/")
for qy in fileinput.input():
  rel = cypher.execute(graph_db,qy)
      
      
