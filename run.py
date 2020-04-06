from flask import Flask, render_template, send_file, g, request, jsonify, session, escape, redirect, json
from passlib.hash import pbkdf2_sha256
import os, time
from db import Database

app = Flask(__name__, static_folder='public', static_url_path='')
app.secret_key = b'lkj98t&%$3rhfSwu3D'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = Database()
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Point to Index.html by default. That is, point to the scoring algorithm page.
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/course/<path:path>')
def base_static(path):
    return send_file(os.path.join(app.root_path, 'course', path))


# Get all games from the system. Given to the system by the Contribute page
@app.route('/api/games')
def api_games():
    if 'user' in session:
        response = get_db().get_games()
        return jsonify(response)
    else:
        return jsonify('Error: User not authenticated')


# Return all games which are associated with the user's personal library
@app.route('/api/usergames')
def api_usergames():
    if 'user' in session:
        user_id = session['user']['user_id']
        response = get_db().get_user_games(user_id)
        set_of_jsons = {json.dumps(d, sort_keys=True) for d in response}
        response = [json.loads(t) for t in set_of_jsons]
        return jsonify(response)
    else:
        return jsonify('Error: User not authenticated')


# Score all of the game's within the user's library compared to the attributes the user requests
@app.route('/api/score')
def api_score():
    if 'user' in session:
        user_id = session['user']['user_id']
        players = request.args.get('players')
        difficulty = request.args.get('difficulty')
        length = request.args.get('length')
        usergames = get_db().get_user_games(user_id)
        set_of_jsons = {json.dumps(d, sort_keys=True) for d in usergames}
        usergames = [json.loads(t) for t in set_of_jsons]

        # score each game one at a time
        for game in usergames:
            totalscore = 300
            # compare player difference with recommended player differences
            playerdifference = abs(int(players) - int(game["players"]))
            playerpenalty = playerdifference * 20
            totalscore = totalscore - playerpenalty

            if difficulty == "Nopref":
                totalscore = totalscore - 100
            else:
                gamedifficulty = game["difficulty"]
                if gamedifficulty == "Complex":
                    gamedifficulty = 3
                if gamedifficulty == "Medium":
                    gamedifficulty = 2
                if gamedifficulty == "Simple":
                    gamedifficulty = 1
                if difficulty == "Complex":
                    difficulty = 3
                if difficulty == "Medium":
                    difficulty = 2
                if gamedifficulty == "Simple":
                    difficulty = 1
                # Convert Simple - Complex into numbers and subtract from score based on difference
                difficultydifference = abs(int(gamedifficulty) - int(difficulty))
                difficultypenalty = difficultydifference * 50
                totalscore = totalscore - difficultypenalty

            if length == "Nopref":
                totalscore = totalscore - 100
            else:
                lengthdifference = abs(int(length) - int(game["length"]))
                lengthpenalty = lengthdifference * 0.84
                totalscore = totalscore - lengthpenalty

            totalscore = int(round(totalscore))
            game.update(scorevalue=str(totalscore))

        highestscore = -10000
        gametoreturn = None
        # for each game loop through and return the highest score and return it
        for game in usergames:
            if int(game["scorevalue"]) > highestscore:
                highestscore = int(game["scorevalue"])
                print("new high score is " + str(highestscore) + " set by " + game["name"])
                gametoreturn = game
        print(gametoreturn)
        return jsonify(gametoreturn)
    else:
        return jsonify('Error: User not authenticated')

# create new user from user create page
@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        typed_password = request.form['password']
        if name and username and typed_password:
            encrypted_password = pbkdf2_sha256.encrypt(typed_password, rounds=200000, salt_size=16)
            get_db().create_user(name, username, encrypted_password)
            return redirect('/login')
    return render_template('create_user.html')

# add a game to a user's personal library of games
@app.route('/api/create_game_user')
def create_game_user():
    game = request.args.get('gameinput')
    user_id = session['user']['user_id']
    if game and user_id:
        get_db().add_game_user(game, user_id)
        return "success"
    else:
        return "fail"

# Create a new game and add it to the overall system's library of games so that all users can add it to their library's
@app.route('/api/create_game', methods=['GET', 'POST'])
def create_game():
    name = request.form.get('name')
    players = request.form.get('players')
    difficulty = request.form.get('difficulty')
    length = request.form.get('length')
    picture = request.files['file']
    filename = str(picture.filename)
    picture.save(os.path.join(app.root_path, 'public', 'img', 'games', filename))
    get_db().add_game(name, players, difficulty, length, filename)
    return "success"

# delete a game currently within the user's library
@app.route('/api/delete_game_user')
def delete_game_user():
    game = request.args.get('gameinput')
    user_id = session['user']['user_id']
    if game and user_id:
        get_db().delete_game_user(game, user_id)
        return "success"
    else:
        return "fail"

# Loging functionality handles logging the user in given a valid username and password
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None
    if request.method == 'POST':
        username = request.form['username']
        typed_password = request.form['password']
        if username and typed_password:
            user = get_db().get_user(username)
            if user:
                if pbkdf2_sha256.verify(typed_password, user['encrypted_password']):
                    session['user'] = user
                    return redirect('/')
                else:
                    message = "Incorrect password, please try again"
            else:
                message = "Unknown user, please try again"
        elif username and not typed_password:
            message = "Missing password, please try again"
        elif not username and typed_password:
            message = "Missing username, please try again"
    return render_template('login.html', message=message)

# logs the user out of the application and disables some basic application functionality
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')


@app.route('/<name>')
def generic(name):
    if 'user' in session:
        return render_template(name + '.html')
    else:
        return redirect('/login')


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)
