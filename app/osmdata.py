# osmdata.py
"""OpenStreetMap data module.

This module is used for manipulating of OpenStreetMap data. It contains classes
which represent the map data, and utility methods for loading and saving map
files.
"""

from lxml import etree



class OSMData:
    """OpenStreetMap map data object.

    Representation of OSM map data. Incomplete implementation for analysis
    purposes, excluding most metadata.

    Attributes:
        meta: dict with metadata (typically "osm_base")
        bounds: dict with lat/lon extent of data
        nodes: dict with node id as key and Node object as value
        ways: dict with way id as key and Way object as value
        relations: dict with relation id as key and Relation object as value
    """

    def __init__(self):
        """Create empty map."""
        self.meta = {}
        self.bounds = {}
        self.nodes = {}
        self.ways = {}
        self.relations = {}


class Element:
    """Map element parent class.

    Attributes:
        tags: dict of map tags and values
    """

    def __init__(self):
        self.tags = {}


class Node(Element):
    """Map node element.

    Attributes:
        lat: node latitude
        lon: node longitude
    """

    def __init__(self, lat, lon):
        Element.__init__(self)
        self.lat = lat
        self.lon = lon


class Way(Element):
    """Map way element.

    Attributes:
        nodes: list of Node objects
    """

    def __init__(self):
        Element.__init__(self)
        self.nodes = []


class Relation(Element):
    """Map relation element.

    Attributes:
        members: list of Member objects
    """

    def __init__(self):
        Element.__init__(self)
        self.members = []


class Member:
    """Relation member.

    Attributes:
        typestr: string identifying member type (i.e., node or way)
        reference: id reference of member
        role: role of member
    """

    def __init__(self, typestr, reference, role):
        self.typestr = typestr
        self.reference = reference
        self.role = role



def load_osm_file(osmfile):
    """Load OSM data from an OSM XML file."""
    osm = OSMData()
    context = etree.iterparse(osmfile, events=("start", "end"))
    _, root = next(context)
    currenttag = None
    for event, elem in context:
        if event == "start" and currenttag == None:
            currenttag = elem.tag
        if event == "end" and elem.tag == currenttag:
            if elem.tag == "note":
                pass
            elif elem.tag == "meta":
                osm.meta.update({"osm_base": elem.get("osm_base")})
            elif elem.tag == "bounds":
                osm.bounds.update({"minlat": elem.get("minlat")})
                osm.bounds.update({"minlon": elem.get("minlon")})
                osm.bounds.update({"maxlat": elem.get("maxlat")})
                osm.bounds.update({"maxlon": elem.get("maxlon")})
            elif elem.tag == "node":
                node = Node(elem.get("lat"), elem.get("lon"))
                for child in elem.iter(tag="tag"):
                    node.tags.update({child.get("k"): child.get("v")})
                osm.nodes.update({elem.get("id"): node})
            elif elem.tag == "way":
                way = Way()
                for child in elem.iter(tag="nd"):
                    way.nodes.append(child.get("ref"))
                for child in elem.iter(tag="tag"):
                    way.tags.update({child.get("k"): child.get("v")})
                osm.ways.update({elem.get("id"): way})
            elif elem.tag == "relation":
                relation = Relation()
                for child in elem.iter(tag="member"):
                    member = Member(child.get("type"), child.get("ref"),
                            child.get("role"))
                    relation.members.append(member)
                for child in elem.iter(tag="tag"):
                    relation.tags.update({child.get("k"): child.get("v")})
                osm.relations.update({elem.get("id"): relation})
            currenttag = None
            root.clear()
    return osm

def save_osm_file(osmfile, osm):
    """Save OSM data to an OSM XML file."""
    with etree.xmlfile(osmfile, encoding="utf-8", buffered=False) as context:
        context.write_declaration()
        with context.element("osm",
                {"version": "0.6", "generator": "Bike Ottawa"}):
            context.write(etree.Element("meta", osm.meta))
            context.write(etree.Element("bounds", osm.bounds))
            for ref,node in osm.nodes.items():
                context.write(etree.Element("node",
                        {"id": ref, "lat": node.lat, "lon": node.lon}))
            for ref,way in osm.ways.items():
                with context.element("way", {"id": ref}):
                    for node in way.nodes:
                        context.write(etree.Element("nd", {"ref": node}))

def save_geojson_file(jsonfile, osm):
    """Save OSM data to a GeoJSON file."""
    jsonfile.write("{\"type\":\"FeatureCollection\",\"features\":[")
    firstway = True
    for ref,way in osm.ways.items():
        if not firstway:
            jsonfile.write(",")
        firstway = False
        jsonfile.write("{\"type\":\"Feature\",\"id\":\"way/"+ref+"\","
                "\"properties\":{\"id\":\"way/"+ref+"\"},\"geometry\":")
        jsonfile.write("{\"type\":\"LineString\",\"coordinates\":[")
        firstnode = True
        for node in way.nodes:
            if not firstnode:
                jsonfile.write(",")
            firstnode = False
            n = osm.nodes.get(node)
            jsonfile.write("["+n.lon+","+n.lat+"]")
        jsonfile.write("]}}")
    jsonfile.write("]}")
