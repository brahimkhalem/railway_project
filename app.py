from flask import Flask, render_template, request
import xml.etree.ElementTree as ET
from xml.dom import minidom

app = Flask(__name__)
XML_FILE = "transport.xml"

def get_all_trips():
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    trips = []
    for line in root.findall("line"):
        line_id = line.get("id")
        for trip in line.findall("trip"):
            classes = []
            for cls in trip.findall("class"):
                classes.append({
                    "type": cls.get("type"),
                    "price": int(cls.find("price").text)
                })
            trips.append({
                "line_id": line_id,
                "code": trip.get("code"),
                "departure": trip.find("departure_city").text,
                "arrival": trip.find("arrival_city").text,
                "dep_time": trip.find("schedule/departure_time").text,
                "arr_time": trip.find("schedule/arrival_time").text,
                "train_type": trip.find("train_type").text,
                "classes": classes
            })
    return trips

def get_statistics():
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    stats = []
    train_type_count = {}
    for line in root.findall("line"):
        line_id = line.get("id")
        prices = []
        for trip in line.findall("trip"):
            t_type = trip.find("train_type").text
            train_type_count[t_type] = train_type_count.get(t_type, 0) + 1
            for cls in trip.findall("class"):
                prices.append(int(cls.find("price").text))
        if prices:
            stats.append({
                "line_id": line_id,
                "min_price": min(prices),
                "max_price": max(prices)
            })
    return stats, train_type_count

@app.route("/")
def index():
    trips = get_all_trips()
    cities = sorted(set(t["departure"] for t in trips))
    train_types = sorted(set(t["train_type"] for t in trips))
    return render_template("index.html", trips=trips,
                           cities=cities, train_types=train_types)

@app.route("/search", methods=["GET"])
def search():
    code = request.args.get("code", "").strip()
    departure = request.args.get("departure", "").strip()
    arrival = request.args.get("arrival", "").strip()
    train_type = request.args.get("train_type", "").strip()
    max_price = request.args.get("max_price", "").strip()
    trips = get_all_trips()
    if code:
        trips = [t for t in trips if t["code"].lower() == code.lower()]
    if departure:
        trips = [t for t in trips if t["departure"] == departure]
    if arrival:
        trips = [t for t in trips if t["arrival"] == arrival]
    if train_type:
        trips = [t for t in trips if t["train_type"] == train_type]
    if max_price:
        trips = [t for t in trips if any(
            c["price"] <= int(max_price) for c in t["classes"]
        )]
    dom_detail = None
    if code and trips:
        doc = minidom.parse(XML_FILE)
        for trip_node in doc.getElementsByTagName("trip"):
            if trip_node.getAttribute("code").lower() == code.lower():
                dom_detail = trip_node.toxml()
                break
    stats, train_type_count = get_statistics()
    cities = sorted(set(t["departure"] for t in get_all_trips()))
    train_types = sorted(set(t["train_type"] for t in get_all_trips()))
    return render_template("index.html", trips=trips, cities=cities,
                           train_types=train_types, dom_detail=dom_detail,
                           stats=stats, train_type_count=train_type_count)

if __name__ == "__main__":
    app.run(debug=True, port=3000)
