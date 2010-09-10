import sys
import sqlite3
from lxml import etree

ROUTE_MINUTES = 21
CORRIDOR_MINUTES = 16
START_TIME = '07:00:00'
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

min_buses = int(round(60 / float(CORRIDOR_MINUTES) * (end-start) / 3600))
min_route_buses = int(round(60 / float(ROUTE_MINUTES) * (end-start) * 24))

print "Finding frequent stops.  This may take a while."

c.execute("CREATE TEMPORARY TABLE stop_arrival_lists AS SELECT stop_id, group_concat(julianday(arrival_time)) AS arrivals, 0 AS frequent FROM weekday_arrivals WHERE arrival_time >= ? AND arrival_time < ? GROUP BY stop_id", (START_TIME, END_TIME));

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

c.execute("CREATE INDEX stop_arrival_stop_id_index ON stop_arrival_lists(stop_id)")
c.execute("CREATE INDEX stop_arrival_frequent_index ON stop_arrival_lists(frequent)")

print "Finding frequent routes.  This may take a while."

c.execute("CREATE TEMPORARY TABLE route_frequency (route_id references routes(route_id), trip_headsign, frequent integer)")

map_data = etree.ElementTree(etree.Element("osm", version="0.6"))

c.execute("SELECT stops.stop_id, stop_lat, stop_lon FROM stops LEFT JOIN stop_arrival_lists ON stops.stop_id=stop_arrival_lists.stop_id WHERE frequent = 1")
for row in c:
    node = etree.SubElement(map_data.getroot(), "node", id=row[0], lat=row[1], lon=row[2])
    tag = etree.SubElement(node, "tag", k="place", v="frequent")
    d.execute("SELECT trips.route_id, trips.trip_headsign, group_concat(strftime('%J', arrival_time)) AS arrivals, route_short_name FROM weekday_arrivals LEFT JOIN trips ON weekday_arrivals.trip_id=trips.trip_id LEFT JOIN routes ON trips.route_id=routes.route_id LEFT JOIN route_frequency on routes.route_id=route_frequency.route_id WHERE frequent IS NULL AND arrival_time >= ? AND arrival_time < ? AND stop_id = ? GROUP BY trips.route_id ORDER BY weekday_arrivals.trip_id, arrival_time", (START_TIME, END_TIME, row[0]))
    route_diff = float(ROUTE_MINUTES) * 60 / 86400
    e = conn.cursor()
    for wor in d:
        if (wor[2].find(',') != -1):
            last = start
            for tim in wor[2].split(','):
                if (float(tim) - last) > route_diff:
                    print "Eliminated %s - %s because of %s %f" % (wor[3], wor[1], tim, last)
                    e.execute("INSERT INTO route_frequency VALUES(?, ?, 0)", (wor[0], wor[1]))
                    break
                last = float(tim)
            if (end - last) <= route_diff:
                e.execute("INSERT INTO route_frequency VALUES (?, ?, 1)",  (wor[0], wor[1]))
                print "Route %s is frequent" % (wor[3],)

c.execute("SELECT DISTINCT trips.shape_id, route_short_name FROM route_frequency LEFT JOIN trips ON route_frequency.route_id=trips.route_id LEFT JOIN routes ON trips.route_id=routes.route_id WHERE frequent=1 AND route_short_name IS NOT NULL")
for row in c:
    print row[0]
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
