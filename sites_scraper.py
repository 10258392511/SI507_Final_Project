# This file implements the scraper
import bs4
import requests
import re
from bs4 import BeautifulSoup
from pprint import pprint
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
    def __init__(self, name="", photo_url="", desc="", address="", info_url=""):
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
    print("fetching...")
    main_url = "https://www.planetware.com/michigan-tourism-vacations-usmi.htm"
    base_url = "https://www.planetware.com"
    resp = requests.get(main_url)
    assert resp.status_code == 200, "GET failed"
    soup = BeautifulSoup(resp.text, "html.parser")
    excluding_pattern = re.compile(r".*(tents|where to stay in detroit|michigan in pictures).*")
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


def scrape_site(site_url, cache_filename):
    """
    Scrape a detail page with caching.

    Parameters
    ----------
    site_url: str
        URL for the detail page.
    cache_filename: str
        Cache filename.

    Returns
    -------
    dict
        A dict containing all places on the page, in the form of:
        {
            "place name 1": {"name": str, "photo_url": str, "desc": list[str], "address": str, "info_url": list[str]},
            "place name 2": {...}
        }
    """
    cache = open_cache(cache_filename)
    key = site_url
    if key in cache:
        return cache[key]
    print("fetching...")
    base_url = "https://www.planetware.com"
    resp = requests.get(site_url)
    assert resp.status_code == 200, "GET failed"
    soup = BeautifulSoup(resp.text, "html.parser")
    blocks = soup.find_all("div", class_="article_block site")
    sites_on_page = {}
    for block in blocks:
        site_obj = dict()
        name = block.find("h2", class_="sitename").text
        # print(name)
        if not re.match(re.compile(r"^\d+"), name):
            break
        site_obj["name"] = re.findall(re.compile(r"[. ]+.*"), name)[0][1:].strip()
        # print(site_obj["name"])
        img = block.find("img")
        if img is None:
            site_obj["photo_url"] = None
        else:
            site_obj["photo_url"] = base_url + img["src"]
        desc_paragraphs = block.find("div", class_="site_desc").find_all("p")
        site_obj["desc"] = [p.text for p in desc_paragraphs if not re.match(re.compile(r"^([a-zA-Z ]+:)"), p.text)]
        address = block.find(string=re.compile(r"Address: .*"))
        if address is not None:
            site_obj["address"] = address[len("Address: "):].strip()
        else:
            site_obj["address"] = None
        anchors = block.find_all("a")
        site_obj["info_url"] = [anchor["href"] for anchor in anchors]
        sites_on_page[site_obj["name"]] = site_obj

    cache[key] = sites_on_page
    save_cache(cache, cache_filename)
    return sites_on_page


if __name__ == '__main__':
    # self-test
    cache_filename = "cache_scraper.json"
    detail_urls = scrape_main_page(cache_filename)
    print(f"main:")
    # print(json.dumps(detail_urls, indent=4))
    pprint(detail_urls, indent=2)
    print("-" * 30)
    num_places = 0
    for name, site_url in detail_urls.items():
        print(f"{name}: {site_url}")
        sites_on_page = scrape_site(site_url, cache_filename)
        print(json.dumps(sites_on_page, indent=4))
        num_places += len(sites_on_page)
        print("-" * 30)

    print(f"{num_places} places in total.")
