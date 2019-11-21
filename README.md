# Cycling Level of Traffic Stress (LTS) Analysis

[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Models the Level of Traffic Stress (LTS) to evaluate the comfort of cycling on
a given street. Uses OpenStreetMap data for street grid.

#### Data Sources

OSM data can be downloaded directly from the Overpass API using a query file. A
sample query that selects data in the Ottawa-Gatineau region is provided below.

````
(
  way(44.927,-76.361,45.598,-75.052)["highway"];
  node(w);
);
out count;
out;
````
