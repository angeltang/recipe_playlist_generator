#################################
##### Name: Angel Tang
##### Uniqname: rongtang
#################################

import bs4
from bs4 import BeautifulSoup
import requests
import json
import emoji
import re

import playlist_generator
import sqlite
import main

class Recipe:
    def __init__(self, name, rating, url, time='', serving=0, directions=[]):
        self.name = name
        self.rating = rating
        self.time = time
        self.serving = serving
        self.directions = directions
        self.url = url

    def info(self):
        # does not include url
        return f'{emoji.emojize(":pushpin:", use_aliases=True)} {self.name} (Rating: {self.rating})'

def generate_search_url(input):
    base_url = 'https://www.allrecipes.com/search/results/?search='
    param = input.replace(' ','+')
    url = base_url + param + '&page=1'
    return url

def get_recipes(search_url):
    print('Looking for recipes...')

    html = requests.get(search_url).text
    soup = BeautifulSoup(html, 'html.parser')
    recipes_divs = soup.find_all('div', class_='card__detailsContainer-left')

    if recipes_divs:
        recipes = {}
        counter = 1
        for recipe in recipes_divs:
            name = recipe.find(class_='card__titleLink manual-link-behavior')['title']
            url = recipe.find(class_='card__titleLink manual-link-behavior')['href']

            try:
                rating_raw = recipe.find(class_="review-star-text").text
                pattern = r'\d+\.*\d*'
                rating = float(re.search(pattern, rating_raw)[0])
            except: rating = 'No Rating'

            recipe_obj = Recipe(name=name, rating=rating, url=url)
            recipes[counter] = recipe_obj
            counter += 1

            # add recipe data into database
            db_value = [
                recipe_obj.name,
                recipe_obj.rating,
                recipe_obj.url,
                recipe_obj.time,
                recipe_obj.serving,
                ''
            ]
            db_values = [db_value]
            main.recipes_list = sqlite.check_database(name, 'recipes', main.recipes_list, db_values)

        return recipes

    else:
        print(f'{emoji.emojize(":exclamation:", use_aliases=True)} Your search returned nah results.')
        print(f'    Please check your spelling, try a more generic term, or try less terms.')
        ask_param()

def print_recipes(input, recipes):
    header = f'''
============================
Recipes for {input}
============================
    '''
    print(header)
    counter = 1
    for v in recipes.values():
        print(f'{counter} {v.info()}')
        counter += 1
    ask_bar_chart()
    get_recipe_details(recipes)
    return

def get_recipe_details(recipes):
    total = len(recipes)
    user = input(emoji.emojize(':sparkles: Type in the number of the recipe you want to know more about, or type "nah": (To leave, enter "bye":wave:) ', use_aliases=True))
    user = user.strip().lower()

    if user == 'bye':
        exit()
    elif user == 'nah':
        return
    else:
        try:
            user = int(user)
            try:
                recipe = recipes[user]
                url = recipe.url
                html = requests.get(url).text
                soup = BeautifulSoup(html, 'html.parser')
                meta = soup.find_all(class_="two-subcol-content-wrapper")
                recipe.time = meta[0].find_all(class_="recipe-meta-item-body")[-1].text.strip()
                recipe.serving = meta[1].find_all(class_="recipe-meta-item-body")[0].text.strip()
                directions_raw = soup.find_all('li', class_='subcontainer instructions-section-item')
                temp = []
                db_directions = ''
                for item in directions_raw:
                    directions = item.find_all('p')
                    for direction in directions:
                        text = direction.text
                        temp.append(text)
                        db_directions += ('- '+text+'.')
                recipe.directions = temp

                # add recipe data into database
                db_value = [recipe.name, recipe.rating, recipe.url, recipe.time, recipe.serving, db_directions]
                db_values = [db_value]
                # sqlite.update_data('recipes', db_values)
                main.recipes_list = sqlite.check_database(recipe.name, 'recipes', main.recipes_list, db_values)
                # print(main.recipes_list) #################

                yes = print_recipe_detail(recipe)

                if yes == False:
                    return
            except:
                print(f'{emoji.emojize(":exclamation:", use_aliases=True)} Please enter a valid integer from 1 to {total}.')
                get_recipe_details(recipes)
                return

        except:
            print(f'{emoji.emojize(":exclamation:", use_aliases=True)} Please enter a valid integer from 1 to {total}.')
            get_recipe_details(recipes)
            return

def print_recipe_detail(recipe):
    header = f'========= details ==========\n{recipe.info()}\n============================'
    print(header)
    print(f'Time: {recipe.time}\nServing(s): {recipe.serving}')
    print('Directions:')
    directions = recipe.directions
    for direction in directions:
        print(f'- {direction}')
    print('============================')
    yes = ask_playlist(recipe)
    return yes

def ask_playlist(recipe):
    user = input(emoji.emojize(':sparkles: Want to generate a playlist for making this recipe? Type "ya" or "nah" to let me know: ', use_aliases=True))
    user = user.strip().lower()
    yes = False

    if user == 'ya':
        playlist_generator.generate_playlist(recipe)
        yes = True
    elif user == 'nah':
        return yes
    else:
        print(emoji.emojize('Please type "ya" or "nah" so that I can understand :cold_sweat:', use_aliases=True))
        ask_playlist(recipe)

def ask_bar_chart():
    user = input(emoji.emojize(':sparkles: Want to see some stats from all your searches so far? Type "rating", "serving", "time", or "nah" to let me know:  ', use_aliases=True))
    user = user.lower().strip()

    if user == 'nah':
        return
    elif user not in ['rating', 'serving', 'time']:
        print(emoji.emojize('Please type one of the 3 metrics or "nah" so that I can understand :cold_sweat:', use_aliases=True))
    else:
        if user == 'rating':
            data_list = sqlite.bar_chart_data_prep('Rating', 'recipes')
            thresholds = [1, 2, 3, 4, 5]
            bins = ['(0,1]', '(1,2]', '(2,3]', '(3,4]', '(4,5]']
            xaxis = 'Ratings'
        elif user == 'serving':
            data_list = sqlite.bar_chart_data_prep('Serving', 'recipes')
            thresholds = [1, 2, 4, 10, 100]
            bins = ['1', '2', '3-4', '5-10', '>11']
            xaxis = 'Servings'
        elif user == 'time':
            temp_list = sqlite.bar_chart_data_prep('Time', 'recipes')
            data_list = []
            for time in temp_list:
                try:
                    time = playlist_generator.process_time_to_seconds(time)
                    data_list.append(time)
                except:
                    continue
            thresholds = [1800, 3600, 1000000000]
            bins = ['~ 30min', '~ 1hr', '> 1hr']
            xaxis = 'Cooking Time'
        bin_values = sqlite.bar_chart_bins_prep(data_list, thresholds)
        sqlite.show_bar_chart(bins, bin_values, user, xaxis)

    ask_bar_chart()


def ask_param():
    user = input(emoji.emojize(':sparkles: What recipes do you want to explore today? (To leave, enter "bye" :wave:) ', use_aliases=True))
    user = user.strip().lower()
    if user == 'bye':
        exit()
    else:
        url = generate_search_url(user)
        recipes = get_recipes(url)
        print_recipes(user, recipes)
        # get_recipe_details(recipes)
        ask_param()
