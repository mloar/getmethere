import sys
import sqlite3
from lxml import etree

ROUTE_MINUTES = 30
CORRIDOR_MINUTES = 15
START_TIME = '06:00:00'
END_TIME = '19:00:00'

if len(sys.argv) < 2:
    print >> sys.stderr, "database name required"
    sys.exit(0)

conn = sqlite3.connect(sys.argv[1])

c = conn.cursor()
d = conn.cursor()

d.execute("SELECT strftime('%J', ?)", (START_TIME,))
for row in d:
    start = float(row[0])

d.execute("SELECT strftime('%J', ?)", (END_TIME,))
for row in d:
    end = float(row[0])

#min_buses = 60 / float(CORRIDOR_MINUTES) * (end-start / 3600)
#min_route_buses = 60 / float(ROUTE_MINUTES) * (end-start / 3600)

print "Finding frequent stops.  This may take a while."

c.execute("CREATE TEMPORARY TABLE stop_arrival_lists AS SELECT stop_times.stop_id AS stop_id, group_concat(strftime('%J',arrival_time)) AS arrivals, 0 as frequent FROM stop_times LEFT JOIN trips ON stop_times.trip_id=trips.trip_id LEFT JOIN calendar on trips.service_id = calendar.service_id WHERE monday=1 AND arrival_time >= ? AND arrival_time < ? GROUP BY stop_times.stop_id ORDER BY arrival_time", (START_TIME, END_TIME))

c.execute("CREATE INDEX stop_arrival_id_index ON stop_arrival_lists(stop_id)")

c.execute("SELECT * FROM stop_arrival_lists")

diff = float(CORRIDOR_MINUTES) * 60 / 86400
for row in c:
    if (row[1].find(',') != -1):
        last = start
        for tim in row[1].split(','):
            if (float(tim) - last) > diff:
                break
            last = float(tim)
        if (end - last) <= diff:
            d.execute("UPDATE stop_arrival_lists SET frequent = 1 WHERE stop_id = ?",  (row[0],))

c.execute("CREATE INDEX stop_arrival_frequent_index ON stop_arrival_lists(frequent)")
c.execute("CREATE INDEX stop_arrival_stop_id_index ON stop_arrival_lists(stop_id)")

print "Finding frequent routes.  This may take a while."
c.execute("CREATE TEMPORARY TABLE route_arrival_lists AS SELECT route_id, stop_times.stop_id AS stop_id, group_concat(strftime('%J',arrival_time)) AS arrivals, 0 AS frequent FROM trips LEFT JOIN stop_times ON trips.trip_id=stop_times.trip_id LEFT JOIN stop_arrival_lists ON stop_times.stop_id=stop_arrival_lists.stop_id WHERE arrival_time >= ? AND arrival_time < ? AND stop_arrival_lists.frequent = 1 GROUP BY route_id, stop_times.stop_id ORDER BY arrival_time", (START_TIME, END_TIME))

c.execute("SELECT * FROM route_arrival_lists")

route_diff = float(ROUTE_MINUTES) * 60 / 86400
for row in c:
    if (row[2].find(',') != -1):
        last = start
        for tim in row[2].split(','):
            if (float(tim) - last) > route_diff:
                break
            last = float(tim)
        if (end - last) <= route_diff:
            d.execute("UPDATE route_arrival_lists SET frequent = 1 WHERE route_id = ? AND stop_id = ?",  (row[0], row[1]))
            print "Found one!"

#c.execute("CREATE TEMPORARY TABLE frequent_routes AS SELECT DISTINCT routes.route_id AS route_id FROM routes LEFT JOIN trips ON routes.route_id=trips.route_id LEFT JOIN stop_times ON trips.trip_id=stop_times.trip_id LEFT JOIN stop_arrival_lists ON stop_times.stop_id=stop_arrival_lists.stop_id WHERE frequent = 1")
c.execute("CREATE TEMPORARY TABLE frequent_routes AS SELECT DISTINCT route_id FROM route_arrival_lists WHERE frequent = 1")

map_data = etree.ElementTree(etree.Element("osm", version="0.6"))

#for row in c:
#    node = etree.SubElement(map_data.getroot(), "node", id=row[0], lat=row[1], lon=row[2])
#    tag = etree.SubElement(node, "tag", k="stop", v="frequent")

c.execute("SELECT DISTINCT shape_id, route_short_name FROM routes LEFT JOIN trips ON routes.route_id=trips.route_id LEFT JOIN frequent_routes ON trips.route_id=frequent_routes.route_id")
for row in c:
    d.execute("SELECT shape_pt_lat, shape_pt_lon, shape_pt_sequence FROM shapes WHERE shape_id = ?", (row[0],))
    for wor in d:
        etree.SubElement(map_data.getroot(), "node", id=wor[2], lat=wor[0], lon=wor[1])
    d.execute("SELECT shape_pt_lat, shape_pt_lon, shape_pt_sequence FROM shapes WHERE shape_id = ?", (row[0],))
    way = etree.SubElement(map_data.getroot(), "way", id="%s" % (row[0],))
    tag = etree.SubElement(way, "tag", k="highway", v="bus_guideway")
    ref = etree.SubElement(way, "tag", k="ref", v=row[1])
    for wor in d:
        etree.SubElement(way, "nd", ref=wor[2])

with open("data.osm", "w") as d:
    map_data.write(d)
