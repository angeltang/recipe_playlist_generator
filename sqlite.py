#################################
##### Name: Angel Tang
##### Uniqname: rongtang
#################################

import plotly
import plotly.graph_objs as go
import sqlite3

recipes_columns = [
    "Name",
    "Rating",
    "Url",
    "Time",
    "Serving",
    "Directions"
]

playlists_columns = [
    "Playlist_Name",
    "Playlist_Id",
    "Spotify_Link",
    "Recipe_Name",
    "Genre",
    "Duration(s)"
]

def create_data():
    '''Creating database and table if not existed.
    (Optional: If existed, drop the table)

    Parameters
    ----------

    Returns
    -------
    None
    '''
    conn = sqlite3.connect("./recipes_and_playlists.sqlite")
    cur = conn.cursor()

    # OPTIONAL: DROP THE TABLE IF EXISTED TO RESTART THE RECORDS
    # drop_recipes = '''    DROP TABLE IF EXISTS "recipes";'''
    # cur.execute(drop_recipes)
    # drop_playlists = '''    DROP TABLE IF EXISTS "playlists";'''
    # cur.execute(drop_playlists)

    create_recipes = '''
    CREATE TABLE IF NOT EXISTS "recipes"(
        "Id" INTEGER UNIQUE PRIMARY KEY AUTOINCREMENT,
        "Name" TEXT NOT NULL,
        "Rating" REAL NOT NULL,
        "Url" TEXT NOT NULL,
        "Time" TEXT,
        "Serving" INTEGER NOT NULL,
        "Directions" TEXT
    );
    '''
    cur.execute(create_recipes)

    create_playlists = '''
    CREATE TABLE IF NOT EXISTS "playlists"(
        "Id" INTEGER UNIQUE PRIMARY KEY AUTOINCREMENT,
        "Playlist_Name" TEXT NOT NULL,
        "Playlist_Id" TEXT NOT NULL,
        "Spotify_Link" TEXT NOT NULL,
        "Recipe_Name" TEXT NOT NULL,
        "Genre" TEXT NOT NULL,
        "Duration" FLOAT NOT NULL
    );
    '''

    cur.execute(create_playlists)

    conn.commit()
    conn.close()

def update_data(tablename, values):
    '''insert data into the database

    Parameters
    values: list of records(lists)
    ----------
    Returns
    -------
    None
    '''
    conn = sqlite3.connect("./recipes_and_playlists.sqlite")
    cur = conn.cursor()
    insert = f"INSERT INTO {tablename} VALUES (NULL,?,?,?,?,?,?)"
    for value in values:
        cur.execute(insert, value)
        conn.commit()
    conn.close()


def check_database(name, tablename, database_list, data):
    '''check if name is in the specified table
    If so, delete that record and update it with the additional details;
    If not, insert the record with update_data()

    Parameters
    ----------
    name: recipe name or playlist name
    tablename: the table to insert; "recipes" or "playlists"
    database_list: the list of data that are already in the database
    data: the updated data

    Returns
    -------
    database_list: updated data list
    '''

    print('... checking database ...')
    conn = sqlite3.connect("./recipes_and_playlists.sqlite")
    cur = conn.cursor()
    if name not in database_list:
        print('... inserting data into database ...')
        database_list.append(name)
    else:
        print('... fetching from database ...')
        if tablename == 'playlists':
            delete = f'DELETE FROM {tablename} WHERE "Playlist_Name"="{name}"'
        elif tablename == 'recipes':
            delete = f'DELETE FROM {tablename} WHERE "Name"="{name}"'
        cur.execute(delete)
        conn.commit()
        conn.close()

    update_data(tablename, data)

    # updated_record = cur.fetchall()

    conn.close()

    return database_list

def fetch_data_to_dict(name, tablename):
    '''fetch data from database and convert it to a dict

    Parameters
    ----------
    name: recipe name or playlist name
    tablename: the table to insert; "recipes" or "playlists"

    Returns
    -------
    data_dict: a dict with data from the database
    '''

    conn = sqlite3.connect('./recipes_and_playlists.sqlite')
    cur = conn.cursor()
    select = f'SELECT * FROM {tablename} WHERE Name="{name}"'
    cur.execute(select)

    data_dict = {}

    if tablename == 'recipes':
        columns = recipes_columns
    elif tablename == 'playlists':
        columns = playlists_columns

    for row in cur:
        for i,column in enumerate(columns):
            data_dict[column] = row[i]

    conn.close()

    return data_dict

def fetch_combined_to_dict():
    '''fetch combined data from database and convert it to a dict
    Note: data combined with the foreign key (recipe name)

    Parameters
    ----------

    Returns
    -------
    data_dict: a dict with data from the database
    '''

    conn = sqlite3.connect('./recipes_and_playlists.sqlite')
    cur = conn.cursor()
    join = f"SELECT * FROM recipes JOIN playlists ON recipes.Name=playlists.Recipe_Name"
    cur.execute(join)

    data_dict = {}
    skip = ['Id']
    columns = skip + recipes_columns + skip + playlists_columns

    for column in columns:
        data_dict[column] = []
    for row in cur:
        for i,column in enumerate(columns):
            if column in ['Id', 'Directions', 'Recipe_Name','Playlist_Name','Playlist_Id','Duration(s)']:
                continue
            else:
                data_dict[column].append(row[i])

    conn.close()
    return data_dict

def show_table(data_dict):
    '''transfer the dictionary of combined data to display into a table

    Parameters
    ----------
    data_dict: a dict with combined data from the database

    Returns
    -------
    None
    Output: opens a figure in the browser with plotly
    '''
    playlists_columns_copy = playlists_columns
    recipes_columns_copy = recipes_columns

    for table in [playlists_columns_copy, recipes_columns_copy]:
        for column in table:
            if column in ['Id', 'Directions', 'Recipe_Name','Playlist_Name','Playlist_Id','Duration(s)']:
                table.remove(column)

    columns = recipes_columns_copy + playlists_columns_copy
    columns.remove('Playlist_Id')

    values = []

    for column in columns:
        values.append(data_dict[column])

    fig = go.Figure(data=[go.Table(header=dict(values=columns),
                 cells=dict(values=values))
                     ])

    fig.update_layout(
    title="Recipes with Customized Playlists"
    )

    fig.show()

def bar_chart_data_prep(column, tablename):
    '''fetch column data from the specified table in the database
    and translate it to a list

    Parameters
    ----------
    column: the column name
    tablename: the table name (recipes or playlists)

    Returns
    -------
    data_list: a list of retrived data
    '''

    conn = sqlite3.connect('./recipes_and_playlists.sqlite')
    cur = conn.cursor()
    select = f'SELECT {column} FROM {tablename}'
    cur.execute(select)

    data_list = []

    for row in cur:
        data_list.append(row[0])

    conn.close()

    return data_list

def bar_chart_bins_prep(data_list, thresholds):
    '''separates the data by thresholds into bins

    Parameters
    ----------
    data_list: a list of single column data
    thresholds: thresholds to separate bins

    Returns
    -------
    bin_values: a list of counts per bin
    '''

    #thresholds_rating = [1, 2, 3, 4, 5]
    bin_counts = {}
    bin_values = []

    for i in range(len(thresholds)):
        bin_counts[i] = 0

    for data in data_list:
        try:
            data = float(data)
            if data <= thresholds[0]:
                bin_counts[0] += 1
            else:
                for i in range(len(thresholds)-1): #0 #1 #3
                    i += 1 #1  #2 #4
                    if data > thresholds[i-1] and data <= thresholds[i]: #0, 1 #1, 2 #3, 4
                        bin_counts[i] += 1 #1 #2 #4
                        break
        except:
            data_list.remove(data)

    for i in range(len(thresholds)):
        bin_values.append(bin_counts[i])


    return bin_values

def show_bar_chart(bins, bin_values, title, xaxis):
    '''transfer the dictionary of combined data to display into a table

    Parameters
    ----------
    bins: a list of names of the bins
    bin_values: a list of counts per bin
    title: graph title
    xaxis: x-axis title

    Returns
    -------
    None
    Output: opens a figure in the browser with plotly
    '''

    print('... opening browser to show chart ...')
    data = [go.Bar(
        x = bins,
        y = bin_values
    )]

    fig = go.Figure(data=data)

    fig.update_layout(
    title=f"Bar Chart for {title.title()}",
    xaxis_title=f"{xaxis.title()}",
    yaxis_title="Counts"
    )

    fig.show()


