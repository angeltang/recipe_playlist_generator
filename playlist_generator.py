#################################
##### Name: Angel Tang
##### Uniqname: rongtang
#################################

from requests_oauthlib import OAuth1
import json
import requests
import re
import emoji
import webbrowser
import math
import base64
import sqlite3

import secrets
import sqlite
import main


CACHE_FILENAME = "spotify_genre_cache.json"
CACHE_DICT = {}

client_key = secrets.CLIENT_ID
client_secret = secrets.CLIENT_SECRET
user_id = secrets.USER_ID

# class Track:
#     def __init__(self, name, artist, duration, uri):
#         self.name = name
#         self.artist = artist
#         self.duration = duration # in seconds
#         self.uri = uri

class Playlist:
    def __init__(self, name, id, href, recipe_name, genre, duration=0):
        self.name = name
        self.id = id
        self.href = href
        self.recipe_name = recipe_name
        self.genre = genre
        self.duration = duration # in seconds

    def info(self):
        total_seconds = int(self.duration)
        minutes = math.floor(total_seconds/60)
        seconds = total_seconds%60
        return f'{self.name} ({minutes} mins {seconds} secs)'

def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary

    Parameters
    ----------
    None

    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk

    Parameters
    ----------
    cache_dict: dict
        The dictionary to save

    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()

def encode_header():
    # Encode as Base64
    message = f"{client_key}:{client_secret}"
    messageBytes = message.encode('ascii')
    base64Bytes = base64.b64encode(messageBytes)
    base64Message = base64Bytes.decode('ascii')
    headers = {}
    headers['Authorization'] = f"Basic {base64Message}"
    return headers

AUTH_HEADERS = encode_header()

def authenticate():

    # HANDLE NO CLIENT INFO
    if not client_key or not client_secret:
        print("You need to fill in CLIENT_KEY and CLIENT_SECRET in secret.py.")
        exit()
    if not user_id:
        print('You need to fill in USER_ID in secret.py')
        exit()

    # GET
    AUTH_CODE_URL = 'https://accounts.spotify.com/authorize'
    auth_code_response = requests.get(AUTH_CODE_URL, params={
        'client_id': client_key,
        'response_type': 'code',
        'redirect_uri': 'http://localhost:8888',
        'scope': 'playlist-modify-public playlist-modify-private',
    })
    print(emoji.emojize(f':exclamation: To use this app properly, you need to run the following authorization.', use_aliases=True))
    print(f'Please go to this url to authorize: {auth_code_response.url}')
    # wait for the user's authentication
    resp_url = input('Please paste the redirected url: ')
    # EXAMPLE: http://localhost:8888/?code=AQAV97Pts7-6h5XEi9VFJrFBIvznjfIZBJkkUAr0-00JLTjnGP-RndV0fdvYhNlvG40AloL2JoQo0BohbB0Wa-G4mOnzOq5ncSWULEaO_Jv4kGWETsa_Rh6t9piJIqSBdqPF5cDqVGWKhd7tIYObD5mD6wlQMIpE6YBmp0hhJza_omg6TxZNuSucSLNf3_T7_jrh8JJzUqzAKITH4u00XO5bSZktyX2A93o
    code = resp_url.split('?code=')[-1]

    # POST
    TOKEN_URL = 'https://accounts.spotify.com/api/token'
    auth_response = requests.post(TOKEN_URL, {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'http://localhost:8888',
    }, headers=AUTH_HEADERS)

    # convert the response to JSON
    auth_response_data = auth_response.json()
    refresh_token = auth_response_data['refresh_token']

    print('Thank you! Authorization completed.')

    return refresh_token

REFRESH_TOKEN = authenticate()

def get_access_token():
    # POST
    TOKEN_URL = 'https://accounts.spotify.com/api/token'
    auth_response = requests.post(TOKEN_URL, {
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN
    }, headers=AUTH_HEADERS).json()
    access_token = auth_response['access_token']
    return access_token

def create_headers():
    access_token = get_access_token()
    headers = {'Authorization': 'Bearer {token}'.format(token=access_token), 'Content-Type': 'application/json'}
    return headers

def make_request(baseurl, params):
    # CHANGE DOCSTRING!
    ''' constructs a key that is guaranteed to uniquely and
    repeatably identify an API request by its baseurl and params

    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs

    Returns
    -------
    string
        the unique key as a string
    '''
    headers = create_headers()
    response = requests.get(baseurl, params=params, headers=headers)
    return response.json()

def make_request_with_cache(baseurl, genre):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new
    request, save it, then return it.

    AUTOGRADER NOTES: To test your use of caching in the autograder, please do the following:
    If the result is in your cache, print "fetching cached data"
    If you request a new result using make_request(), print "making new request"

    Do not include the print statements in your return statement. Just print them as appropriate.
    This, of course, does not ensure that you correctly retrieved that data from your cache,
    but it will help us to see if you are appropriately attempting to use the cache.

    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    hashtag: string
        The hashtag to search for
    count: integer
        The number of results you request from Twitter

    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    if genre in CACHE_DICT.keys():
        print("... fetching cached data ...")
    else:
        print("... making new request ...")
        params = {
            'q':f'genre:{genre}',
            'type':'track',
            'limit':50
        }
        temp_list = make_request(baseurl, params)['tracks']['items']
        track_dict = {}
        counter = 1
        for item in temp_list:
            temp = {}
            temp['name'] = item['name']
            temp['artist'] = item['artists'][0]['name']
            temp['duration'] = int(item['duration_ms'] / 1000)
            temp['uri'] = item['uri']
            temp['genre'] = genre
            # track = Track(name, artist, duration, uri)
            track_dict[counter] = temp
            counter += 1

        CACHE_DICT[genre] = track_dict
        save_cache(CACHE_DICT)
    return CACHE_DICT[genre]

def make_genre_dict():
    baseurl = 'https://api.spotify.com/v1/recommendations/available-genre-seeds'
    params = ''
    temp_dict = make_request(baseurl, params)
    genre_list = temp_dict['genres']
    genre_dict = {}
    counter = 1
    for genre in genre_list:
        genre_dict[counter] = genre
        counter += 1
    return genre_dict

def print_genres(genre_dict):
    header = f'''
=========================================
{emoji.emojize(":musical_note:", use_aliases=True)} All Spotify Genres (Alphabetical)
=========================================
    '''
    print(header)
    for k,v in genre_dict.items():
        print(f'{k} - {v}')
    return

def calculate_playlist_length(current_time, track):
    #retrive track length
    duration = track['duration']
    #add to current_time
    total = current_time + duration
    return total

def create_playlist(genre, recipe):
    name = f'{genre.title()} for Cooking {recipe.name}'
    recipe_name = recipe.name

    if name not in main.playlists_list:
        headers = create_headers()
        baseurl = f'https://api.spotify.com/v1/users/{user_id}/playlists'

        data=json.dumps({
            'name': name,
            'public': True
        })
        response = requests.post(
            baseurl,
            data=data,
            headers=headers
        ).json()
        playlist_id = response['id']
        playlist_href = f'https://open.spotify.com/playlist/{playlist_id}?si={user_id}' # https://open.spotify.com/playlist/323iJk6Ym1egp7KNnm8mg1?si=a66dec6aa55e4751

    else:
        print('... fetching from database ...')
        playlist = sqlite.fetch_data_to_dict(name, 'playlist')
        playlist_id = playlist['Playlist_Id']
        playlist_href = playlist['Href']

    return Playlist(name, playlist_id, playlist_href, recipe_name, genre)

def add_tracks(playlist_id, genre, max_time):

    baseurl_genre = 'https://api.spotify.com/v1/search'
    songs_dict = make_request_with_cache(baseurl_genre, genre)

    counter = 1
    current_time = 0
    baseurl_add_track = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    while current_time < max_time:

        try:
            uris = [songs_dict[counter]['uri']]
        except:
            uris = [songs_dict[1]['uri']]
        data=json.dumps({
            'uris': uris
        })
        headers = create_headers()
        response = requests.post(
            url=baseurl_add_track,
            data=data,
            headers=headers
        ).json()

        current_time = calculate_playlist_length(current_time, songs_dict[counter])
        counter += 1

    return current_time

def ask_genre():
    GENRES = make_genre_dict()
    print_genres(GENRES)
    user = input(emoji.emojize(':sparkles: What genre do you want the playlist to be? (To leave, type "bye" :wave:) ', use_aliases=True))

    if user.strip().lower() == 'bye':
        print('Okie...bye!')
        exit()
    else:
        try:
            genre_id = int(user.strip())
            genre = GENRES[genre_id]
            return genre
        except:
            print('Please enter a valid number.')
            ask_genre()


def process_time_to_seconds(time_string):
    pattern = r'((\d*)\s*hrs?)?\s*(\d+)?'
    time = re.search(pattern, time_string)
    try:
        hour = int(time[2])
    except:
        hour = 0
    minute = int(time[3])
    seconds = (60 * hour + minute) * 60
    return seconds

def ask_table():
    user = input(emoji.emojize(':sparkles: Want to export all the existing recipes with playlists? Type "ya" or "nah" to let me know: ', use_aliases=True))
    user = user.lower().strip()
    if user == 'ya':
        print('... opening the table in browser ...')
        data_dict = sqlite.fetch_combined_to_dict()
        sqlite.show_table(data_dict)
        return
    elif user == 'nah':
        return
    else:
        print(emoji.emojize('Please type "ya" or "nah" so that I can understand :cold_sweat:', use_aliases=True))
        ask_table()

def generate_playlist(recipe):
    max_time = process_time_to_seconds(recipe.time)
    genre = ask_genre()

    try:
        playlist = create_playlist(genre, recipe)
        playlist_id = playlist.id
        length = add_tracks(playlist_id, genre, max_time)
        playlist.duration = length # in seconds

        db_value = [
            playlist.name,
            playlist.id,
            playlist.href,
            playlist.recipe_name,
            playlist.genre,
            playlist.duration,
        ]
        db_values = [db_value]
        main.playlists_list = sqlite.check_database(playlist.name, 'playlists', main.playlists_list, db_values)

        print(f'Opening in browser: {playlist.info()}')
        url = playlist.href
        webbrowser.open(url)
        print(emoji.emojize(f':musical_note: {playlist.info()} generated for {recipe.name} ({recipe.time})', use_aliases=True))

        ask_table()
    except:
        print(emoji.emojize(f'Oops! Looks like the genre {genre} does not actually exist in Spotify\'s API :cold_sweat:', use_aliases=True))
        generate_playlist(recipe)

    return
