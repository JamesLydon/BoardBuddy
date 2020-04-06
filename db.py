import os
import re
import sqlite3
# search for db file in base directory. db should be called boardbuddy.db
SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'boardbuddy.db')


class Database:

    def __init__(self):
        self.conn = sqlite3.connect(SQLITE_PATH)

    def select(self, sql, parameters=[]):
        c = self.conn.cursor()
        c.execute(sql, parameters)
        return c.fetchall()

    def execute(self, sql, parameters=[]):
        c = self.conn.cursor()
        c.execute(sql, parameters)
        self.conn.commit()

# returns all games and theier attributes in the overall BoardBuddy system
    def get_games(self):
        data = self.select(
            'SELECT * FROM games ORDER BY game_id')
        return [{
            'key': d[0],
            'players': d[2],
            'difficulty': d[3],
            'length': d[4],
            'name': d[1],
            'picture': d[5]
        } for d in data]

# returns all games which are associated with a user's game library based on that user's user_id
    def get_user_games(self, user_id):
        data = self.select(
            'SELECT * FROM (games INNER JOIN user_games ON games.game_id = user_games.game_id AND user_games.user_id=?)',
            [user_id])
        return [{
            'name': d[1],
            'players': d[2],
            'difficulty': d[3],
            'length': d[4],
            'picture': d[5]
        } for d in data]

# creates a new user into the system given a name, username, and password
    def create_user(self, name, username, encrypted_password):
        self.execute('INSERT INTO users (name, username, encrypted_password) VALUES (?, ?, ?)',
                     [name, username, encrypted_password])

# add a game to a user's game library given a game name and a user_id for the logged in user
    def add_game_user(self, game_name, user_id):
        gamedata = self.select('SELECT game_id FROM games WHERE name=?', [game_name])
        game_id = gamedata[0][0]
        self.execute('INSERT INTO user_games (user_id, game_id) VALUES (?, ?)',
                     [user_id, game_id])

# add game to the overall BoardBuddy's game system 
    def add_game(self, name, players, difficulty, length, picture):
        self.execute('INSERT INTO games (name, players, difficulty, length, picture) VALUES (?, ?, ?, ?, ?)',
                     [name, players, difficulty, length, picture])

# delete a game from a user's game library given a name of a game and given the logged in user's user_id
    def delete_game_user(self, game_name, user_id):
        gamedata = self.select('SELECT game_id FROM games WHERE name=?', [game_name])
        game_id = gamedata[0][0]
        self.execute('DELETE FROM user_games WHERE user_games.user_id = ? AND user_games.game_id = ?',
                     [user_id, game_id])

# get a user_id and password given a username
    def get_user(self, username):
        data = self.select('SELECT * FROM users WHERE username=?', [username])
        if data:
            d = data[0]
            return {
                'name': d[0],
                'username': d[1],
                'encrypted_password': d[2],
                'user_id': d[3]
            }
        else:
            return None

    def close(self):
        self.conn.close()
