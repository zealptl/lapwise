# Introduction
OpenF1 is an open-source API providing detailed Formula 1 telemetry, timing, and session data in JSON and CSV formats.

Historical data (from 2023 onwards) is free and accessible without authentication. Real-time data requires a paid subscription.

You can query the API directly through your browser or HTTP client. Explore the endpoints below to get started.

# API Endpoints

## Drivers championship (beta)
Provides championship standings for drivers. Only available for race sessions.

curl "https://api.openf1.org/v1/championship_drivers?session_key=9839&driver_number=4&driver_number=81"
Output:

[
  {
    "driver_number": 4,
    "meeting_key": 1276,
    "points_current": 423,
    "points_start": 408,
    "position_current": 1,
    "position_start": 1,
    "session_key": 9839
  },
  {
    "driver_number": 81,
    "meeting_key": 1276,
    "points_current": 410,
    "points_start": 392,
    "position_current": 3,
    "position_start": 3,
    "session_key": 9839
  }
]
Sample URL
https://api.openf1.org/v1/championship_drivers?session_key=9839&driver_number=4&driver_number=81

Attributes
Name	Description
driver_number	The unique number assigned to an F1 driver for the season (cf. Wikipedia).
meeting_key	The unique identifier for the meeting. Use latest to identify the latest or current meeting.
points_current	Championship points during/after the race (depends on call timing).
points_start	Championship points before the race started.
position_current	Championship position during/after the race (depends on call timing).
position_start	Championship position before the race started.
session_key	The unique identifier for the session. Use latest to identify the latest or current session.

## Teams championship (beta)
Provides championship standings for teams. Only available for race sessions.

curl "https://api.openf1.org/v1/championship_teams?session_key=9839&team_name=McLaren"
Output:

[
  {
    "meeting_key": 1276,
    "points_current": 833,
    "points_start": 800,
    "position_current": 1,
    "position_start": 1,
    "session_key": 9839,
    "team_name": "McLaren"
  }
]
Sample URL
https://api.openf1.org/v1/championship_teams?session_key=9839&team_name=McLaren

Attributes
Name	Description
meeting_key	The unique identifier for the meeting. Use latest to identify the latest or current meeting.
points_current	Championship points during/after the race (depends on call timing).
points_start	Championship points before the race started.
position_current	Championship position during/after the race (depends on call timing).
position_start	Championship position before the race started.
session_key	The unique identifier for the session. Use latest to identify the latest or current session.
team_name	The name of the team.

## Drivers
Retrieve detailed information about the drivers participating in a specific session.

curl "https://api.openf1.org/v1/drivers?driver_number=1&session_key=9158"
Output:

[
  {
    "broadcast_name": "M VERSTAPPEN",
    "driver_number": 1,
    "first_name": "Max",
    "full_name": "Max VERSTAPPEN",
    "headshot_url": "https://www.formula1.com/content/dam/fom-website/drivers/M/MAXVER01_Max_Verstappen/maxver01.png.transform/1col/image.png",
    "last_name": "Verstappen",
    "meeting_key": 1219,
    "name_acronym": "VER",
    "session_key": 9158,
    "team_colour": "3671C6",
    "team_name": "Red Bull Racing"
  }
]
Sample URL
https://api.openf1.org/v1/drivers?driver_number=1&session_key=9158

Attributes
Name	Description
broadcast_name	The driver's name, as displayed on TV.
country_code (deprecated)	A code that uniquely identifies the country. This field will be removed at the end of the 2026 season.
driver_number	The unique number assigned to an F1 driver for the season (cf. Wikipedia).
first_name	The driver's first name.
full_name	The driver's full name.
headshot_url	URL of the driver's face photo.
last_name	The driver's last name.
meeting_key	The unique identifier for the meeting. Use latest to identify the latest or current meeting.
name_acronym	Three-letter acronym of the driver's name.
session_key	The unique identifier for the session. Use latest to identify the latest or current session.
team_colour	The hexadecimal color value (RRGGBB) of the driver's team.
team_name	Name of the driver's team.

## Laps
Provides detailed information about individual laps.

curl "https://api.openf1.org/v1/laps?session_key=9161&driver_number=63&lap_number=8"
Output:

[
  {
    "date_start": "2023-09-16T13:59:07.606000+00:00",
    "driver_number": 63,
    "duration_sector_1": 26.966,
    "duration_sector_2": 38.657,
    "duration_sector_3": 26.12,
    "i1_speed": 307,
    "i2_speed": 277,
    "is_pit_out_lap": false,
    "lap_duration": 91.743,
    "lap_number": 8,
    "meeting_key": 1219,
    "segments_sector_1": [2049, 2049, 2049, 2051, 2049, 2051, 2049, 2049],
    "segments_sector_2": [2049, 2049, 2049, 2049, 2049, 2049, 2049, 2049],
    "segments_sector_3": [2048, 2048, 2048, 2048, 2048, 2064, 2064, 2064],
    "session_key": 9161,
    "st_speed": 298
  }
]
Sample URL
https://api.openf1.org/v1/laps?session_key=9161&driver_number=63&lap_number=8

Attributes
Name	Description
date_start	The UTC starting date and time, in ISO 8601 format. This date is approximate.
driver_number	The unique number assigned to an F1 driver for the season (cf. Wikipedia).
duration_sector_1	The time taken, in seconds, to complete the first sector of the lap.
duration_sector_2	The time taken, in seconds, to complete the second sector of the lap.
duration_sector_3	The time taken, in seconds, to complete the third sector of the lap.
i1_speed	The speed of the car, in km/h, at the first intermediate point on the track.
i2_speed	The speed of the car, in km/h, at the second intermediate point on the track.
is_pit_out_lap	A boolean value indicating whether the lap is an "out lap" from the pit (true if it is, false otherwise).
lap_duration	The total time taken, in seconds, to complete the entire lap.
lap_number	The sequential number of the lap within the session (starts at 1).
meeting_key	The unique identifier for the meeting. Use latest to identify the latest or current meeting.
segments_sector_1	A list of values representing the "mini-sectors" within the first sector (see mapping table below).
segments_sector_2	A list of values representing the "mini-sectors" within the second sector (see mapping table below).
segments_sector_3	A list of values representing the "mini-sectors" within the third sector (see mapping table below).
session_key	The unique identifier for the session. Use latest to identify the latest or current session.
st_speed	The speed of the car, in km/h, at the speed trap, which is a specific point on the track where the highest speeds are usually recorded.

## Meetings
Provides information about meetings. A meeting refers to a Grand Prix or testing weekend and usually includes multiple sessions (practice, qualifying, race, ...). Meetings are updated every day at midnight UTC.

curl "https://api.openf1.org/v1/meetings?year=2026&country_name=Singapore"
Output:

[
  {
    "circuit_key": 61,
    "circuit_info_url": "https://api.multiviewer.app/api/v1/circuits/61/2026",
    "circuit_image": "https://media.formula1.com/content/dam/fom-website/2018-redesign-assets/Track%20icons%204x3/Singapore%20carbon.png",
    "circuit_short_name": "Singapore",
    "circuit_type": "Temporary - Street",
    "country_code": "SGP",
    "country_flag": "https://media.formula1.com/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/singapore-flag.png",
    "country_key": 157,
    "country_name": "Singapore",
    "date_end": "2026-10-11T14:00:00+00:00",
    "date_start": "2026-10-09T09:30:00+00:00",
    "gmt_offset": "08:00:00",
    "is_cancelled": false,
    "location": "Marina Bay",
    "meeting_key": 1296,
    "meeting_name": "Singapore Grand Prix",
    "meeting_official_name": "FORMULA 1 SINGAPORE AIRLINES SINGAPORE GRAND PRIX 2026",
    "year": 2026
  }
]
Sample URL
https://api.openf1.org/v1/meetings?year=2026&country_name=Singapore

Attributes
Name	Description
circuit_key	The unique identifier for the circuit where the event takes place.
circuit_image	An image of the circuit.
circuit_info_url	A URL to a JSON containing detailed circuit info. See FastF1 documentation for details. Data provided by MultiViewer.
circuit_short_name	The short or common name of the circuit where the event takes place.
circuit_type	The type of the circuit ("Permanent", "Temporary - Street", or "Temporary - Road")
country_code	A code that uniquely identifies the country.
country_flag	An image of the country flag.
country_key	The unique identifier for the country where the event takes place.
country_name	The full name of the country where the event takes place.
date_end	The UTC ending date and time, in ISO 8601 format.
date_start	The UTC starting date and time, in ISO 8601 format.
gmt_offset	The difference in hours and minutes between local time at the location of the event and Greenwich Mean Time (GMT).
is_cancelled	A boolean indicating whether the meeting has been cancelled.
location	The city or geographical location where the event takes place.
meeting_key	The unique identifier for the meeting. Use latest to identify the latest or current meeting.
meeting_name	The name of the meeting.
meeting_official_name	The official name of the meeting.
year	The year the event takes place.

## Overtakes
Provides information about overtakes. An overtake refers to one driver (the overtaking driver) exchanging positions with another driver (the overtaken driver). This includes both on-track passes and position changes resulting from pit stops or post-race penalties. This data is only available during races and may be incomplete.

curl "https://api.openf1.org/v1/overtakes?session_key=9636&overtaking_driver_number=63&overtaken_driver_number=4&position=1"
Output:

[
  {
    "date": "2024-11-03T15:50:07.565000+00:00",
    "meeting_key": 1249,
    "overtaken_driver_number": 4,
    "overtaking_driver_number": 63,
    "position": 1,
    "session_key": 9636
  }
]
Sample URL
https://api.openf1.org/v1/overtakes?session_key=9636&overtaking_driver_number=63&overtaken_driver_number=4&position=1

Attributes
Name	Description
date	The UTC date and time, in ISO 8601 format.
meeting_key	The unique identifier for the meeting. Use latest to identify the latest or current meeting.
overtaken_driver_number	The unique number assigned to the overtaken F1 driver (cf. Wikipedia).
overtaking_driver_number	The unique number assigned to the overtaking F1 driver (cf. Wikipedia).
position	The position of the overtaking F1 driver after the overtake was completed (starts at 1).
session_key	The unique identifier for the session. Use latest to identify the latest or current session.

## Pit
Provides information about cars going through the pit lane.

curl "https://api.openf1.org/v1/pit?session_key=9877&stop_duration<2.3"
Output:

[
  {
    "date": "2025-10-26T20:46:37.358000+00:00",
    "driver_number": 16,
    "lane_duration": 22.215,
    "lap_number": 31,
    "meeting_key": 1272,
    "pit_duration": 22.215,
    "session_key": 9877,
    "stop_duration": 2.2
  },
  {
    "date": "2025-10-26T21:09:49.689000+00:00",
    "driver_number": 81,
    "lane_duration": 22.159,
    "lap_number": 47,
    "meeting_key": 1272,
    "pit_duration": 22.159,
    "session_key": 9877,
    "stop_duration": 2.1
  }
]
Sample URL
https://api.openf1.org/v1/pit?session_key=9877&stop_duration<2.3

Attributes
Name	Description
date	The UTC date and time, in ISO 8601 format.
driver_number	The unique number assigned to an F1 driver for the season (cf. Wikipedia).
lane_duration	The time spent in the pit lane, in seconds.
lap_number	The sequential number of the lap within the session (starts at 1).
meeting_key	The unique identifier for the meeting. Use latest to identify the latest or current meeting.
pit_duration (deprecated)	Same as 'lane_duration'. This field will be removed at the end of the 2026 season.
session_key	The unique identifier for the session. Use latest to identify the latest or current session.
stop_duration	The stationary pit stop time, in seconds. This field is only available from the 2024 US GP onwards.

## Position
Provides driver positions throughout a session, including initial placement and subsequent changes.

curl "https://api.openf1.org/v1/position?meeting_key=1217&driver_number=40&position<=3"
Output:

[
  {
    "date": "2023-08-26T09:30:47.199000+00:00",
    "driver_number": 40,
    "meeting_key": 1217,
    "position": 2,
    "session_key": 9144
  },
  {
    "date": "2023-08-26T09:35:51.477000+00:00",
    "driver_number": 40,
    "meeting_key": 1217,
    "position": 3,
    "session_key": 9144
  }
]
Sample URL
https://api.openf1.org/v1/position?meeting_key=1217&driver_number=40&position<=3

Attributes
Name	Description
date	The UTC date and time, in ISO 8601 format.
driver_number	The unique number assigned to an F1 driver for the season (cf. Wikipedia).
meeting_key	The unique identifier for the meeting. Use latest to identify the latest or current meeting.
position	Position of the driver (starts at 1).
session_key	The unique identifier for the session. Use latest to identify the latest or current session.

## Sessions
Provides information about sessions. A session refers to a distinct period of track activity during a Grand Prix or testing weekend (practice, qualifying, sprint, race, ...). Sessions are updated every day at midnight UTC.

curl "https://api.openf1.org/v1/sessions?country_name=Belgium&session_name=Sprint%20Qualifying&year=2023"
Output:

[
  {
    "circuit_key": 7,
    "circuit_short_name": "Spa-Francorchamps",
    "country_code": "BEL",
    "country_key": 16,
    "country_name": "Belgium",
    "date_end": "2023-07-29T15:35:00+00:00",
    "date_start": "2023-07-29T15:05:00+00:00",
    "gmt_offset": "02:00:00",
    "is_cancelled": false,
    "location": "Spa-Francorchamps",
    "meeting_key": 1216,
    "session_key": 9140,
    "session_name": "Sprint Qualifying",
    "session_type": "Sprint Qualifying",
    "year": 2023
  }
]
Sample URL
https://api.openf1.org/v1/sessions?country_name=Belgium&session_name=Sprint%20Qualifying&year=2023

Attributes
Name	Description
circuit_key	The unique identifier for the circuit where the event takes place.
circuit_short_name	The short or common name of the circuit where the event takes place.
country_code	A code that uniquely identifies the country.
country_key	The unique identifier for the country where the event takes place.
country_name	The full name of the country where the event takes place.
date_end	The UTC ending date and time, in ISO 8601 format.
date_start	The UTC starting date and time, in ISO 8601 format.
gmt_offset	The difference in hours and minutes between local time at the location of the event and Greenwich Mean Time (GMT).
is_cancelled	A boolean indicating whether the session has been cancelled.
location	The city or geographical location where the event takes place.
meeting_key	The unique identifier for the meeting. Use latest to identify the latest or current meeting.
session_key	The unique identifier for the session. Use latest to identify the latest or current session.
session_name	The name of the session (Practice 1, Qualifying, Race, ...).
session_type	The type of the session (Practice, Qualifying, Race, ...).
year	The year the event takes place.

## Session result
Provides standings after a session. This data becomes available a few minutes after the official results are published on the official Formula 1 website.

curl "https://api.openf1.org/v1/session_result?session_key=7782&position%3C=3"
Output:

[
  {
    "dnf": false,
    "dns": false,
    "dsq": false,
    "driver_number": 1,
    "duration": 77.565,
    "gap_to_leader": 0,
    "number_of_laps": 24,
    "meeting_key": 1143,
    "position": 1,
    "session_key": 7782
  },
  {
    "dnf": false,
    "dns": false,
    "dsq": false,
    "driver_number": 14,
    "duration": 77.727,
    "gap_to_leader": 0.162,
    "number_of_laps": 26,
    "meeting_key": 1143,
    "position": 2,
    "session_key": 7782
  },
  {
    "dnf": false,
    "dns": false,
    "dsq": false,
    "driver_number": 31,
    "duration": 77.938,
    "gap_to_leader": 0.373,
    "number_of_laps": 23,
    "meeting_key": 1143,
    "position": 3,
    "session_key": 7782
  }
]
Sample URL
https://api.openf1.org/v1/session_result?session_key=7782&position<=3

Attributes
Name	Description
dnf	Indicates whether the driver Did Not Finish the race. This can be true only for qualifying and race sessions.
dns	Indicates whether the driver Did Not Start the race. This can be true only for qualifying and race sessions.
dsq	Indicates whether the driver was disqualified.
driver_number	The unique number assigned to an F1 driver for the season (cf. Wikipedia).
duration	Either the best lap time (for practice or qualifying), or the total race time (for races), in seconds. In qualifying, this is an array of three values for Q1, Q2, and Q3.
gap_to_leader	The time gap to the session leader in seconds, or +N LAP(S) if the driver was lapped. In qualifying, this is an array of three values for Q1, Q2, and Q3.
number_of_laps	Total number of laps completed during the session.
meeting_key	The unique identifier for the meeting. Use latest to identify the latest or current meeting.
position	The driver’s final position at the end of the session.
session_key	The unique identifier for the session. Use latest to identify the latest or current session.

## Starting grid
Provides the starting grid for the upcoming race. This data becomes available a few minutes after the official results are published on the official Formula 1 website.

curl "https://api.openf1.org/v1/starting_grid?session_key=7783&position%3C=3"
Output:

[
  {
    "position": 1,
    "driver_number": 1,
    "lap_duration": 76.732,
    "meeting_key": 1143,
    "session_key": 7783
  },
  {
    "position": 2,
    "driver_number": 63,
    "lap_duration": 76.968,
    "meeting_key": 1143,
    "session_key": 7783
  },
  {
    "position": 3,
    "driver_number": 44,
    "lap_duration": 77.104,
    "meeting_key": 1143,
    "session_key": 7783
  }
]
Sample URL
https://api.openf1.org/v1/starting_grid?session_key=7783&position<=3

Attributes
Name	Description
driver_number	The unique number assigned to an F1 driver for the season (cf. Wikipedia).
lap_duration	Duration, in seconds, of the qualifying lap.
meeting_key	The unique identifier for the meeting. Use latest to identify the latest or current meeting.
position	Position on the grid.
session_key	The unique identifier for the session. Use latest to identify the latest or current session.

## Stints
Provides information about individual stints. A stint refers to a period of continuous driving by a driver during a session.

curl "https://api.openf1.org/v1/stints?session_key=9165&tyre_age_at_start>=3"
Output:

[
  {
    "compound": "SOFT",
    "driver_number": 16,
    "lap_end": 20,
    "lap_start": 1,
    "meeting_key": 1219,
    "session_key": 9165,
    "stint_number": 1,
    "tyre_age_at_start": 3
  },
  {
    "compound": "SOFT",
    "driver_number": 20,
    "lap_end": 62,
    "lap_start": 44,
    "meeting_key": 1219,
    "session_key": 9165,
    "stint_number": 3,
    "tyre_age_at_start": 3
  }
]
Sample URL
https://api.openf1.org/v1/stints?session_key=9165&tyre_age_at_start>=3

Attributes
Name	Description
compound	The specific compound of tyre used during the stint (SOFT, MEDIUM, HARD, ...).
driver_number	The unique number assigned to an F1 driver for the season (cf. Wikipedia).
lap_end	Number of the last completed lap in this stint.
lap_start	Number of the initial lap in this stint (starts at 1).
meeting_key	The unique identifier for the meeting. Use latest to identify the latest or current meeting.
session_key	The unique identifier for the session. Use latest to identify the latest or current session.
stint_number	The sequential number of the stint within the session (starts at 1).
tyre_age_at_start	The age of the tyres at the start of the stint, in laps completed.

## Weather
The weather over the track, updated every minute.

curl "https://api.openf1.org/v1/weather?meeting_key=1208&wind_direction>=130&track_temperature>=52"
Output:

[
  {
    "air_temperature": 27.8,
    "date": "2023-05-07T18:42:25.233000+00:00",
    "humidity": 58,
    "meeting_key": 1208,
    "pressure": 1018.7,
    "rainfall": 0,
    "session_key": 9078,
    "track_temperature": 52.5,
    "wind_direction": 136,
    "wind_speed": 2.4
  }
]
Sample URL
https://api.openf1.org/v1/weather?meeting_key=1208&wind_direction>=130&track_temperature>=52

Attributes
Name	Description
air_temperature	Air temperature (°C).
date	The UTC date and time, in ISO 8601 format.
humidity	Relative humidity (%).
meeting_key	The unique identifier for the meeting. Use latest to identify the latest or current meeting.
pressure	Air pressure (mbar).
rainfall	Whether there is rainfall.
session_key	The unique identifier for the session. Use latest to identify the latest or current session.
track_temperature	Track temperature (°C).
wind_direction	Wind direction (°), from 0° to 359°.
wind_speed	Wind speed (m/s).