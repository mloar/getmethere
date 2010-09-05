CREATE TABLE calendar (service_id primary key, monday integer not null, tuesday integer not null, wednesday integer not null, thursday integer not null, friday integer not null, saturday integer not null, sunday integer not null, start_date integer not null, end_date integer not null);
CREATE TABLE routes (route_id primary key, agency_id, route_short_name not null, route_long_name not null, route_desc, route_type not null, route_url, route_color, route_text_color);
CREATE TABLE trips (route_id references routes(route_id), service_id references calendar(service_id), trip_id primary key, trip_headsign, trip_short_name, direction_id, block_id, shape_id);
CREATE TABLE stops (stop_id primary key, stop_code, stop_name not null, stop_desc, stop_lat not null, stop_lon not null, zone_id, stop_url, location_type, parent_station);
CREATE TABLE stop_times (trip_id references trips(trip_id), arrival_time not null, departure_time not null, stop_id references stops(stop_id), stop_sequence not null, stop_headsign, pickup_type, drop_off_type, shape_dist_traveled);

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
