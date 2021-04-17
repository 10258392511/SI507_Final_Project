import sqlite3
from sites_scraper import *
from data_api import *


def schema(db_filename="MichiganTouristSites.sqlite"):
    """
    Creates database.

    Parameters
    ----------
    db_filename: str
        Database filename.

    Returns
    -------
    None
    """
    conn = sqlite3.connect(db_filename)
    tourist_sites_name = "TouristSites"
    maps_name = "Maps"
    cur = conn.cursor()
    drop_table = """
    DROP TABLE IF EXISTS {name}
    """.format
    cur.execute(drop_table(name=tourist_sites_name))
    conn.commit()

    create_tourist_site = """
    CREATE TABLE IF NOT EXISTS {name} (
        Id INTEGER NOT NULL,
        Name TEXT NOT NULL,
        PhotoURL TEXT,
        Desc TEXT NOT NULL,
        Address TEXT,
        InfoURL TEXT,
        
        PRIMARY KEY (Id AUTOINCREMENT)
    )
    """.format
    cur.execute(create_tourist_site(name=tourist_sites_name))
    conn.commit()

    cur.execute(drop_table(name=maps_name))
    conn.commit()
    create_map = """
    CREATE TABLE IF NOT EXISTS {name} (
        Id INTEGER NOT NULL,
        AdminArea6 TEXT,
        AdminArea6Type TEXT,
        AdminArea5 TEXT,
        AdminArea5Type TEXT,
        AdminArea4 TEXT,
        AdminArea4Type TEXT,
        AdminArea3 TEXT NOT NULL,
        AdminArea3Type TEXT NOT NULL,
        AdminArea1 TEXT,
        AdminArea1Type TEXT,
        Lat REAL NOT NULL,
        Lng REAL NOT NULL,
        
        PRIMARY KEY (Id AUTOINCREMENT)
    )
    """.format
    cur.execute(create_map(name=maps_name))
    conn.commit()


def load_from_db():
    pass


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

    def get_twitter(self, cache_filename):
        """
        A wrapper for data_api.get_twitter_data(.).

        Parameters
        ----------
        cache_filename: str
            Cache file to use.

        Returns
        -------
        dict
            See documentation of data_api.get_twitter_data(.).
        """
        return get_twitter_data(self.name, cache_filename)

    def get_map(self, cache_filename):
        """
        A wrapper for data_api.get_map_data(.). To display an interactive map, pass "lng" and "lat" to Flask template.

        Parameters
        ----------
        cache_filename: str
            Cache file to use.

        Returns
        -------
        dict
            See documentation of data_api.get_map_data(.).
        """
        if self.address is not None:
            return get_map_data(self.address, cache_filename)

        return get_map_data(self.name, cache_filename)

    def get_weather(self, cache_filename):
        """
        A wrapper for data_api.get_weather_data(.).

        Parameters
        ----------
        cache_filename: str
            Cache file to use.

        Returns
        -------
        dict
            See documentation of data_api.get_weather_data(.).
        """
        # TODO: retrieve lon, lat from DB
        lon, lat = None, None

        return get_weather_data(lon, lat, cache_filename)

    def save_to_db(self, cache_map, db_filename="MichiganTouristSites.sqlite"):
        # TODO: Store all attributes and results from .get_map(.)
        conn = sqlite3.connect(db_filename)
        cur = conn.cursor()
        insert_tourist_sites = """
            INSERT INTO TouristSites(Name, PhotoURL, Desc, Address, InfoURL)
            VALUES (?, ?, ?, ?, ?)
        """
        cur.execute(insert_tourist_sites, [self.name, self.photo_url, "!#!".join(self.desc), self.address,
                                           "!#!".join(self.info_url)])
        conn.commit()

        map_data = self.get_map(cache_map)
        insert_maps = """
            INSERT INTO Maps(AdminArea6, AdminArea6Type, AdminArea5, AdminArea5Type, AdminArea4, AdminArea4Type, 
            AdminArea3, AdminArea3Type, AdminArea1, AdminArea1Type, Lat, Lng)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        keys = []
        for i in range(6, 0, -1):
            if i == 2:
                continue
            keys += [f"adminArea{i}", f"adminArea{i}Type"]
        keys += ["lat", "lng"]
        cur.execute(insert_maps, [map_data.get(key) for key in keys])
        conn.commit()
