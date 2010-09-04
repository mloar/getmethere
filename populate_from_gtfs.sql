CREATE TABLE calendar (service_id primary key, monday, tuesday, wednesday, thursday, friday, saturday, sunday, start_date, end_date);
CREATE TABLE routes (route_id primary key, agency_id, route_short_name, route_long_name, route_desc, route_type, route_url, route_color, route_text_color);
CREATE TABLE trips (route_id references routes(route_id), service_id, trip_id primary key, trip_headsign, trip_short_name, direction_id, block_id, shape_id);
CREATE TABLE stops (stop_id primary key, stop_code, stop_name, stop_desc, stop_lat, stop_lon, zone_id, stop_url, location_type, parent_station);
CREATE TABLE stop_times (trip_id references trips(trip_id), arrival_time, departure_time, stop_id references stops(stop_id), stop_sequence, stop_headsign, pickup_type, drop_off_type, shape_dist_traveled);

.mode csv
.import calendar.txt calendar
.import routes.txt routes
.import trips.txt trips
.import stops.txt stops
.import stop_times.txt stop_times

DELETE FROM stop_times WHERE trip_id='trip_id';
DELETE FROM stops WHERE stop_id='stop_id';
DELETE FROM trips WHERE trip_id='trip_id';
DELETE FROM routes WHERE route_id='route_id';
DELETE FROM calendar WHERE service_id='service_id';

CREATE INDEX arrival_times_index ON stop_times(arrival_time);
