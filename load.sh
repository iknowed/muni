#!/bin/bash
export JAVA_HOME=/opt/java/jre1.7.0_21
export PATH=$JAVA_HOME/bin:$PATH
( ./neo4j/bin/neo4j stop ) 
rm -rf neo4j
rm -rf neo4j-advanced-1.9.RC1
zcat neo4j-advanced-1.9.RC1-unix.tar.gz | tar -xf -
ln -s ./neo4j-advanced-1.9.RC1 ./neo4j
cp neo4j-server.properties ./neo4j/conf
cp neo4j.properties ./neo4j/conf
( export JAVA_HOME=/opt/java/jre1.7.0_21 ;  export PATH=$JAVA_HOME/bin:$PATH ; ./neo4j/bin/neo4j start  )
( cd ../municonsole/django/municonsole ;  python manage.py sqlclear muni | psql municonsole1 )
( cd ../municonsole/django/municonsole ; python manage.py syncdb )
( cd ../municonsole ; python routes.py ) 
python shapes.py
python stopnodes.py
python stops.py
python inter.py | sort -n | uniq | python cypher.py
