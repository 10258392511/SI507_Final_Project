# This file contains functions for common use
import json


def construct_unique_key(base_url, params, connector="_"):
    """
    Create a unique key for a query.

    Parameters
    ----------
    base_url: str
        API endpoint.
    params: dict
        Query parameters.
    connector: str
        Connecting symbol to string "base_url" and "params".

    Returns
    -------
    str
        The unique key as a str.
    """
    out_key = base_url
    for key in params:
        out_key += connector + f"{key}{connector}{params[key]}"

    return out_key


def open_cache(filename):
    """
    Open or create a cache.json file.

    Parameters
    ----------
    filename: str
        Path to the cache.json file.

    Returns
    -------
    dict
        Loaded or created cache as a dictionary.
    """
    try:
        with open(filename, "r") as rf:
            cache_dict = json.loads(rf.read())
        return cache_dict
    except FileNotFoundError:
        with open(filename, "w") as wf:
            pass
        return {}


def save_cache(cache_dict, filename):
    """
    Save the current cache dict to "filename".

    Parameters
    ----------
    cache_dict: dict
        The current cache dict.
    filename: str
        Cache file path.

    Returns
    -------
    None
    """
    with open(filename, "w") as wf:
        wf.write(json.dumps(cache_dict))
