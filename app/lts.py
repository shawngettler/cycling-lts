# lts.py
"""Level of Traffic Stress analysis module.

This module implements a level of traffic stress model to evaluate the comfort
of cycling on a given street. Uses OpenStreetMap data for street properties.
"""

import argparse
import bz2
import os

import osmdata



class LTSAnalyzer:
    """LTS Analyzer object.

    Attributes:
        options: analyzer options
    """

    def __init__(self, options):
        """Set analyzer options."""
        self.options = options

    def load(self):
        """Load the map data from file."""
        if self.options.bzip:
            with bz2.open(self.options.inputfile) as osmfile:
                self.osm = osmdata.load_osm_file(osmfile)
        elif self.options.overpass:
            with open(self.options.inputfile) as qlfile:
                self.osm = osmdata.load_overpass(qlfile)
        else:
            with open(self.options.inputfile, "rb") as osmfile:
                self.osm = osmdata.load_osm_file(osmfile)

    def save(self):
        """Save the results to file."""
        outputpath = os.path.dirname(self.options.inputfile)+os.sep
        for level in [1,2,3,4]:
            osmout = osmdata.OSMData()
            osmout.meta = self.osm.meta
            osmout.bounds = self.osm.bounds
            for ref,way in self.osm.ways.items():
                if way.level == level:
                    osmout.ways.update({ref: way})
            for _,way in osmout.ways.items():
                for node in way.nodes:
                    osmout.nodes.update({node: self.osm.nodes.get(node)})

            if(self.options.geojson):
                with open(outputpath+"level_"+str(level)+
                        ".json","w") as jsonfile:
                    osmdata.save_geojson_file(jsonfile, osmout)
            else:
                with open(outputpath+"level_"+str(level)+
                        ".osm","wb") as osmfile:
                    osmdata.save_osm_file(osmfile, osmout)

    def run(self):
        """Run the level of traffic stress model."""

        # functions to interpret OSM tags
        def is_cyclable(way):
            if way.tags.get("bicycle") == "no":
                return False
            if way.tags.get("bicycle") == "yes":
                if way.tags.get("piste:type") == "nordic":
                    return False
                return True
            if "highway" in way.tags:
                highway = way.tags.get("highway")
                if highway == "motorway" or highway == "motorway_link":
                    return False
                if highway == "service":
                    service = way.tags.get("service")
                    if service == "parking_aisle" or service == "driveway":
                        return False
                return True
            return False

        def is_path(way):
            if "cycleway" in way.tags:
                return True
            if "highway" in way.tags:
                highway = way.tags.get("highway")
                if (highway == "cycleway" or highway == "footway"
                        or highway == "path" or highway == "track"):
                    return True
            return False

        def is_residential(way):
            return way.tags.get("highway") == "residential"

        def is_oneway(way):
            return way.tags.get("oneway") == "yes"

        def is_service(way):
            return way.tags.get("highway") == "service"

        def get_lanes(way):
            if "lanes" in way.tags:
                lanes = way.tags.get("lanes")
                if lanes.count(";") > 0:
                    maxlanes = 0
                    for n in lanes.split(";"):
                        maxlanes = max(maxlanes, int(n))
                    return maxlanes
                return int(lanes)
            return -1

        def get_maxspeed(way):
            if "maxspeed" in way.tags:
                maxspeed = way.tags.get("maxspeed")
                if "maxspeed" == "national":
                    return 40
                if 'mph' in maxspeed:
                    i = maxspeed.find('mph')
                    # convert mph to approximate km/h
                    return int(maxspeed[:i]) * 1.6 
                return int(maxspeed)
            if way.tags.get("highway") == "motorway":
                return 100
            return 50

        # run stress model
        for _,way in self.osm.ways.items():
            way.level = 0
            if is_cyclable(way):
                if is_path(way):
                    way.level = 1
                elif is_service(way):
                    way.level = 2
                elif get_lanes(way) > 2 and (not is_residential(way)
                        and get_lanes(way) > 1 and is_oneway(way)):
                    if get_maxspeed(way) <= 40:
                        way.level = 3
                    else:
                        way.level = 4
                elif is_residential(way):
                    way.level = 2
                else:
                    if get_maxspeed(way) <= 40:
                        way.level = 2
                    else:
                        way.level = 3



if __name__ == "__main__":
    """Main method for running the module from the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help="OpenStreetMap data source (default"
            " is OSM XML file)")
    parser.add_argument("--bzip", help="input file is a bzip2-compressed OSM"
            " XML file", action="store_true")
    parser.add_argument("--overpass", help="input file is an Overpass API"
            " query file", action="store_true")
    parser.add_argument("--geojson", help="write results files in GeoJSON"
            " format (default is OSM XML)", action="store_true")
    parser.add_argument("--verbose", help="enable verbose output",
            action="store_true")

    ltsa = LTSAnalyzer(parser.parse_args())
    ltsa.load()
    ltsa.run()
    ltsa.save()
