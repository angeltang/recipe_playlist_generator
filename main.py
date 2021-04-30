#################################
##### Name: Angel Tang
##### Uniqname: rongtang
#################################

import scrape_recipe
import playlist_generator
import sqlite

recipes_list = []
playlists_list = []

if __name__ == "__main__":
    sqlite.create_data()
    CACHE_DICT = playlist_generator.open_cache()
    scrape_recipe.ask_param()
