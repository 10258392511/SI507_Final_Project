from classes import *

if __name__ == '__main__':
    cache_scraper = "cache_scraper.json"
    cache_twitter = "cache_twitter.json"
    cache_map = "cache_map.json"
    cache_weather = "cache_weather.json"
    db_filename = "MichiganTouristSites.sqlite"

    # create DB
    schema()

    # retrieve static data and store into DB
    print("Initializing database...")
    cache_filename = "cache_scraper.json"
    detail_urls = scrape_main_page(cache_filename)
    for name, site_url in detail_urls.items():
        sites_on_page = scrape_site(site_url, cache_filename)
        for site_key, site in sites_on_page.items():
            print(f"current: {site_key}")
            print("-" * 30)
            tourist_site = TouristSite(**site)
            # TODO: save to DB
            tourist_site.save_to_db(cache_map, db_filename=db_filename)

    print("Done!")

    pass
