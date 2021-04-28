from flask import Flask, url_for, render_template, redirect, session, request
from pprint import pprint
from utilities import query
from data_api import get_map_data
from classes import *

app = Flask(__name__)
app.config["SECRET_KEY"] = "MI_travel"


@app.route("/", methods=["GET", "POST"])
def index():
    loc = request.form.get("location")
    # print(loc)

    if loc is not None and loc != "":
        session["location"] = loc
        return redirect(url_for("index"))

    print(f"location: {session.get('location')}")
    loc = session.get("location")
    q = """
    SELECT T.Name, PhotoURL, Lat, Lng
    FROM TouristSites T JOIN Maps M ON T.Name = M.Name
    """
    results = query(q, "MichiganTouristSites.sqlite")
    msg = None

    if loc is not None and loc != "":
        # validate input first by make an api call and see if a location in MI is returned
        map_loc = get_map_data(loc, "cache_map.json")
        # print(map_loc)
        if len(map_loc) == 0:
            msg = "invalid input"
        else:
            results = [result for result in results if result[-1] is not None and result[-2] is not None]
            results = sorted(results, key=lambda result: (result[-2] - map_loc["lat"]) ** 2 +
                                                         (result[-1] - map_loc["lng"]) ** 2)
            msg = f"Results sorted by distance (ascending) from {loc}"

    session.clear()
    # pprint(results)

    return render_template("index.html", msg=msg, results=results)


@app.route("/<nm>")
def place_index(nm):
    return render_template("place_index.html", name=nm)


@app.route("/<nm>/desc")
def place_desc(nm):
    pass


@app.route("/<nm>/map")
def place_map(nm):
    pass


@app.route("/<nm>/weather")
def place_weather(nm):
    pass


if __name__ == '__main__':
    app.run(debug=True)