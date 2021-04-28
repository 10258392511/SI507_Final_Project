import requests
import json
import secrets
from requests_oauthlib import OAuth1
from pprint import pprint
from utilities import *

client_key = secrets.TWITTER_API_KEY
client_secret = secrets.TWITTER_API_SECRET
access_token = secrets.TWITTER_ACCESS_TOKEN
access_token_secret = secrets.TWITTER_ACCESS_TOKEN_SECRET

oauth = OAuth1(client_key,
               client_secret=client_secret,
               resource_owner_key=access_token,
               resource_owner_secret=access_token_secret)

map_quest_key = secrets.MAPQUEST_API_KEY

map_box_key = secrets.MAPBOX_API_KEY

open_weather_key = secrets.OPENWATHER_API_KEY


def make_request(baseurl, params):
    """
    Make a request to the Web API using the baseurl and params

    Parameters
    ----------
    baseurl: str
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs

    Returns
    -------
    dict
        the data returned from making the request in the form of
        a dictionary
    """
    resp = requests.get(baseurl, params=params, auth=oauth)
    return resp.json()


def make_request_with_cache(baseurl, params, cache_filename, count=100):
    """
    A general querying function with caching.

    Parameters
    ----------
    baseurl: str
        Endpoint of API.
    params: dict
        Parameters to use.
    cache_filename: str
        Cache file to use.
    count: int
        Number of queries to return.

    Returns
    -------
    dict
        Query result loaded from JSON response.
    """
    cache = open_cache(cache_filename)
    if "count" not in params:
        params["count"] = count
    unique_key = construct_unique_key(baseurl, params)
    if unique_key in cache:
        print("fetching cached data")
        return cache[unique_key]
    else:
        print("making new request")
        results = make_request(baseurl, params)
        cache[unique_key] = results
        save_cache(cache, cache_filename)
        return results


def get_twitter_data(keywords, cache_filename):
    """
    Querying for Twitter data. Tries to get as many tweets about "keyword" and as accurately  as possible by
    experimenting sequentially different parameters. Returns a dictionary containing possible Twitter users with tweets
    at most one-week old (per Twitter API).

    Parameters
    ----------
    keywords: str
        Name of a tourist site.
    cache_filename: str
        Cache file to use.

    Returns
    -------
    dict
        In the form of
        {
            "user 1": {"posting time 1": "tweet", "posting time 2": "tweet", ...}
            "user 2": {...}
            ...
            "queried by 'keywords'": {"posting time 1": "tweet", ...}
        }
    """
    # retrieve relevant users
    user_baseurl = "https://api.twitter.com/1.1/users/search.json"
    params = {"q": f"{keywords} Michigan"}
    count = 3
    users_resp = make_request_with_cache(user_baseurl, params, cache_filename, count)
    if len(users_resp) == 0:
        params = {"q": f"{keywords}"}
        users_resp = make_request_with_cache(user_baseurl, params, cache_filename, count)
        if len(users_resp) == 0:
            return dict()  # no likely Twitter account

    usernames = [user["screen_name"] for user in users_resp]
    # print(usernames)
    output_dict = dict()

    # retrieve tweets by user
    baseurl = "https://api.twitter.com/1.1/search/tweets.json"
    queries = ["from:{user}".format, "to:{user}".format, "@{user}".format]
    for username in usernames:
        user_dict = {}
        for q_format in queries:
            q = q_format(user=username)
            params = {"q": q, "tweet_mode": "extended"}
            resp = make_request_with_cache(baseurl, params, cache_filename)
            user_dict.update({tweet["created_at"]: tweet["full_text"] for tweet in resp["statuses"]})
        output_dict[username] = user_dict

    # in case no tweets can be retrieved so far: directly query by "keywords"
    params = {"q": keywords, "tweet_mode": "extended"}
    resp = make_request_with_cache(baseurl, params, cache_filename)
    output_dict[f"keywords--{keywords}"] = {tweet["created_at"]: tweet["full_text"] for tweet in resp["statuses"]}

    return output_dict


def get_map_data(place_name, cache_filename):
    """
    Query for map data. Return relevant information specified below.

    Parameters
    ----------
    place_name: str
        Name of the place to search.
    cache_filename: str
        Cache file to use.

    Returns
    -------
    dict
        In the form as:
        {"adminArea6": str, "adminArea6Type": str, ... "adminArea3": str, "adminArea3Type": str, "adminArea1": str,
        "adminArea1Type": str, "lat": float, "lng": float}
    """
    baseurl = "http://www.mapquestapi.com/geocoding/v1/address"
    params = {"key": map_quest_key,
              "location": f"{place_name}, Michigan",
              "maxResults": 5}
    cache = open_cache(cache_filename)
    unique_key = construct_unique_key(baseurl, params)
    if unique_key in cache:
        print("fetching from cache...")
        resp = cache[unique_key]
        # return cache[unique_key]

    else:
        print("making new request...")
        resp = requests.get(baseurl, params=params).json()
        cache[unique_key] = resp
        save_cache(cache, cache_filename)

    # pprint(resp, indent=2)

    locations = resp["results"][0]["locations"]
    location = None
    for loc in locations:
        if loc["adminArea3"] == "MI":
            location = loc
            break

    if location is None:
        return dict()

    output_dict = dict()

    for i in range(1, 7):
        keys = [f"adminArea{i}", f"adminArea{i}Type"]
        for key in keys:
            if key in location:
                output_dict[key] = location[key]

    output_dict["lat"] = location["latLng"]["lat"]
    output_dict["lng"] = location["latLng"]["lng"]

    return output_dict


def get_weather_data(lat, lon, cache_filename):
    """
    Query for 5 days / 3 hours data, i.e. 40 forecasting data points.

    Parameters
    ----------
    lat, lon: float
        Latitude and longitude.

    cache_filename: str
        Cache file to use.

    Returns
    -------
    list
        List of dicts, each of which in the form of:
        {"temp": float, "desc": str, "wind_speed": float}
    """
    baseurl = "https://community-open-weather-map.p.rapidapi.com/forecast"
    params = {"lat": f"{lat}", "lon": f"{lon}", "units": "\"metric\" or \"imperial\""}
    # params = {"lat": f"{lat}", "lon": f"{lon}", "units": "\"metric\""}

    headers = {
        'x-rapidapi-key': f"{open_weather_key}",
        'x-rapidapi-host': "community-open-weather-map.p.rapidapi.com"
    }

    unique_key = construct_unique_key(baseurl, params)
    cache = open_cache(cache_filename)
    if unique_key in cache:
        print("fetching from cache...")
        resp = cache[unique_key]

    else:
        print("making new request...")
        resp = requests.get(baseurl, headers=headers, params=params).json()
        cache[unique_key] = resp
        save_cache(cache, cache_filename)

    # pprint(resp, indent=2)
    out_data_list = []
    data_list = resp["list"]
    for data_pt in data_list:
        dict_pt = dict()
        dict_pt["temp"] = data_pt["main"]["temp"] - 273.15
        # dict_pt["temp"] = data_pt["main"]["temp"]
        dict_pt["desc"] = data_pt["weather"][0]["description"]
        dict_pt["wind_speed"] = data_pt["wind"]["speed"]
        out_data_list.append(dict_pt)

    return out_data_list


if __name__ == '__main__':
    pass
