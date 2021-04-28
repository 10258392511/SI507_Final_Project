# Michigan Travel Guide
This is my final project for SI 507 at University of Michigan.

## Requisite Packages
requests, beautifulsoup4, flask, plotly (please use requirements.txt for installation)
```bash
pip install -r requirements.txt
```
or
```bash
python3 -m pip install -r requirements.txt
```

## Supplying API Keys
Please create a "secrets.py" file at the root level of the project (at same level of run_app.py), and supply your API keys in it. You can copy the following code and fill in your keys.
```python
# Twitter
TWITTER_API_KEY = ""
TWITTER_API_SECRET = ""
TWITTER_ACCESS_TOKEN = ""
TWITTER_ACCESS_TOKEN_SECRET = ""

# MapQuest
MAPQUEST_API_KEY = ""

# MapBox
MAPBOX_API_KEY = ""

# OpenWeather
OPENWATHER_API_KEY = ""
```
You can find link and description of data sources in the project document.

## How to Use
After supplying API keys, please run "run_app.py" file. You'll see the server is up; click on the localhost http://127.0.0.1:5000/ to view the index page. There you can enter a place in the text input named "Search Near-By", hit enter and you'll see places sorted by distance. Then select one place to see its description, interact with map and view responsive weather forecast by following the links. Note you can easily return back by clicking on "Back" buttons.
