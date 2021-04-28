import sqlite3
from sites_scraper import *
from data_api import *

db_str_delimiter = "!#!"


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
        Name TEXT UNIQUE NOT NULL,
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
        Name TEXT UNIQUE NOT NULL,
        AdminArea6 TEXT,
        AdminArea6Type TEXT,
        AdminArea5 TEXT,
        AdminArea5Type TEXT,
        AdminArea4 TEXT,
        AdminArea4Type TEXT,
        AdminArea3 TEXT,
        AdminArea3Type TEXT,
        AdminArea1 TEXT,
        AdminArea1Type TEXT,
        Lat REAL,
        Lng REAL,
        
        PRIMARY KEY (Id AUTOINCREMENT)
    )
    """.format
    cur.execute(create_map(name=maps_name))
    conn.commit()
    conn.close()


def load_from_db(name, db_filename="MichiganTouristSites.sqlite"):
    """
    Create a TouristSite by querying the DB by "name". Used for rendering a detail page when a user clicks on the link
    on index.html.

    Parameters
    ----------
    name: str
        Place name.
    db_filename: str
        Database filename.

    Returns
    -------
    TouristSite
        A TouristSite instance.
    """
    q = """
    SELECT T.Name, PhotoURL, Desc, Address, InfoURL, Lng, Lat
    FROM TouristSites T JOIN Maps M ON T.Name = M.Name
    WHERE T.Name = ? 
    """
    conn = sqlite3.connect(db_filename)
    cur = conn.cursor()
    cur.execute(q, [name])
    record_tuple = None
    for record in cur.fetchall():
        record_tuple = record
        break
    tourist_site = TouristSite()
    tourist_site.name = record_tuple[0]
    tourist_site.photo_url = record_tuple[1]
    tourist_site.desc = record_tuple[2].split(db_str_delimiter)
    tourist_site.address = record_tuple[3]
    tourist_site.info_url = record_tuple[4].split(db_str_delimiter)
    tourist_site.lon, tourist_site.lat = record_tuple[5:]

    return tourist_site


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
    lon, lat: float
        Longitude and Latitude. Only available by loading from DB.
    """
    def __init__(self, name=None, photo_url=None, desc=None, address=None, info_url=None):
        self.name = name
        self.photo_url = photo_url
        self.desc = desc
        self.address = address
        self.info_url = info_url
        self.lon, self.lat = None, None

    def __repr__(self):
        # only prints first 10 words of the description
        desc = "_".join(self.desc[0].split(" ")[:10])
        address = "no address" if self.address is None else self.address
        return f"TS({self.name}, {desc}, {address})"

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

    def get_weather(self, cache_filename, db_filename="MichiganTouristSites.sqlite"):
        """
        A wrapper for data_api.get_weather_data(.).

        Parameters
        ----------
        cache_filename: str
            Cache file to use.
        db_filename: str
            Database filename.

        Returns
        -------
        dict
            See documentation of data_api.get_weather_data(.).
        """
        q = """
        SELECT Lng, Lat
        FROM TouristSites T JOIN Maps M ON T.Name = M.Name
        WHERE T.Name = ?
        """
        conn = sqlite3.connect(db_filename)
        cur = conn.cursor()
        cur.execute(q, [self.name])
        lon, lat = None, None
        for record in cur.fetchall():
            lon, lat = record
            break

        if lon is None or lat is None:
            return dict()

        return get_weather_data(lat, lon, cache_filename)

    def save_to_db(self, cache_map, db_filename="MichiganTouristSites.sqlite"):
        """
        Save instance data to database.

        Parameters
        ----------
        cache_map: str
            Cache file for MapQuest queries.
        db_filename: str
            Database filename.

        Returns
        -------
        None
        """
        conn = sqlite3.connect(db_filename)
        cur = conn.cursor()
        insert_tourist_sites = """
            INSERT INTO TouristSites(Name, PhotoURL, Desc, Address, InfoURL)
            VALUES (?, ?, ?, ?, ?)
        """
        cur.execute(insert_tourist_sites, [self.name, self.photo_url, db_str_delimiter.join(self.desc), self.address,
                                           db_str_delimiter.join(self.info_url)])
        conn.commit()

        map_data = self.get_map(cache_map)
        insert_maps = """
            INSERT INTO Maps(Name, AdminArea6, AdminArea6Type, AdminArea5, AdminArea5Type, AdminArea4, AdminArea4Type, 
            AdminArea3, AdminArea3Type, AdminArea1, AdminArea1Type, Lat, Lng)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        keys = []
        for i in range(6, 0, -1):
            if i == 2:
                continue
            keys += [f"adminArea{i}", f"adminArea{i}Type"]
        keys += ["lat", "lng"]
        vals = [self.name] + [map_data.get(key) for key in keys]
        cur.execute(insert_maps, vals)
        conn.commit()
        conn.close()
