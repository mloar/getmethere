import sys
import sqlite3
from lxml import etree

MINUTES = 15
START_TIME = '06:00:00'
END_TIME = '24:00:00'

if len(sys.argv) < 2:
    print >> sys.stderr, "database name required"
    sys.exit(0)

conn = sqlite3.connect(sys.argv[1])

c = conn.cursor()
d = conn.cursor()

c.execute("CREATE TEMPORARY TABLE arrival_lists AS SELECT stop_times.stop_id AS stop_id, group_concat(strftime('%J',arrival_time)) AS arrivals, 0 as frequent FROM stop_times LEFT JOIN trips ON stop_times.trip_id=trips.trip_id LEFT JOIN calendar on trips.service_id = calendar.service_id WHERE monday=1 AND arrival_time >= ? AND arrival_time < ? GROUP BY stop_times.stop_id ORDER BY arrival_time", (START_TIME, END_TIME))

c.execute("SELECT * FROM arrival_lists")

d.execute("SELECT strftime('%J', ?)", (START_TIME,))
for row in d:
    start = float(row[0])

d.execute("SELECT strftime('%J', ?)", (END_TIME,))
for row in d:
    end = float(row[0])

diff = float(MINUTES) * 60 / 86400
for row in c:
    if (row[1].find(',') != -1):
        last = start
        for tim in row[1].split(','):
            if (float(tim) - last) > diff:
                break
            last = float(tim)
        if (end - last) <= diff:
            d.execute("UPDATE arrival_lists SET frequent = 1 WHERE stop_id = ?",  (row[0],))

c.execute("SELECT arrival_lists.stop_id, stop_lat, stop_lon FROM arrival_lists LEFT JOIN stops ON arrival_lists.stop_id=stops.stop_id WHERE frequent = 1")

with open("orig.osm") as o:
    map_data = etree.parse(o)
    for row in c:
        node = etree.SubElement(map_data.getroot(), "node", id=row[0], lat=row[1], lon=row[2])
        tag = etree.SubElement(node, "tag", k="stop", v="frequent")
    with open("data.osm", "w") as d:
        map_data.write(d)

print >> sys.stderr, "Loading stylesheet"
with open("osmarender.xsl") as f:
    xslt_doc = etree.parse(f)
transform = etree.XSLT(xslt_doc)

print >> sys.stderr, "Loading data"
#with open("mine.xml") as g:
#    data_doc = etree.parse(g)
with open("test.xml") as g:
    data_doc = etree.parse(g)

print >> sys.stderr, "Applying stylesheet"
result_tree = transform(data_doc)

print >> sys.stderr, "Saving results"
with open("map.svg", "w") as h:
    result_tree.write(h)
