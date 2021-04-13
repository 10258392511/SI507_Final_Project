# This file implements the scraper
import bs4
import requests
import re
from bs4 import BeautifulSoup
from utilities import *


class TouristSite(object):
    """
    A class for individual tourist site. Used for subsequent data acquisition.

    Attributes
    ----------
    name: str
        Name of the tourist site.
    photo_url: str
        Since each tourist is accompanied by a photo, we want to store the URL of it for later use.
    desc: str
        Description of the tourist site following the photo.
    address: str
        The address of the tourist site. If not available, use default "not available".
    info_url: list
        List of str. URL of additional information if available. Default: [].
    """
    def __init__(self, name, photo_url, desc, address, info_url):
        self.name = name
        self.photo_url = photo_url
        self.desc = desc
        self.address = address
        self.info_url = info_url

    def __repr__(self):
        # only prints first 10 letters of the description
        return f"TS({self.name}, {self.desc.split(' ')[:10].join(' ')}, {self.address})"

    def save_to_cache(self, cache_filename):
        """
        Saves the current instance as a dict in a json cache file. Note the relevant key is "sites".

        Parameters
        ----------
        cache_filename: str
            The cache filename.

        Returns
        -------
        None
        """
        cache = open_cache(cache_filename)  # a dict
        key = "sites"
        if key not in cache:
            cache[key] = {}
        if self.__repr__() not in cache[key]:
            cache[key][self.__repr__()]({
                "name": self.name,
                "photo_url": self.photo_url,
                "desc": self.desc,
                "address": self.address,
                "info_url": self.info_url
            })
        save_cache(cache, cache_filename)


def scrape_main_page(cache_filename):
    """
    Scrapes the main page for detailed pages' urls.

    Parameters
    ----------
    cache_filename: str
        Cache file to use. Don't scrape twice!

    Returns
    -------
    dict
        A dict in the form: {"short title": "url"}
    """
    cache = open_cache(cache_filename)
    key = "main_page"
    if key in cache:
        return cache[key]
    main_url = "https://www.planetware.com/michigan-tourism-vacations-usmi.htm"
    base_url = "https://www.planetware.com"
    resp = requests.get(main_url)
    assert resp.status_code == 200, "GET failed"
    soup = BeautifulSoup(resp.text, "html.parser")
    excluding_pattern = re.compile(r".*(tents|where to stay in detroit).*")
    detail_urls = {}
    dest_anchors = soup.select("div.dest a")
    for anchor in dest_anchors:
        anchor_txt = anchor.text.lower().strip()
        if excluding_pattern.match(anchor_txt):
            continue
        detail_urls[anchor_txt] = base_url + anchor["href"]

    cache[key] = detail_urls
    save_cache(cache, cache_filename)

    return detail_urls


if __name__ == '__main__':
    CACHE_NAME = "cache.json"
