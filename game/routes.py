from flask import render_template,session,redirect,request,url_for,jsonify,flash
from game import app
from uuid import uuid4
from datetime import datetime
import os
import json
import random

avatars=os.listdir("game/static/avatars")

lang_file=open('game/lang.json','r')
lang_file_data=lang_file.read()
home_lang = json.loads(lang_file_data)['home']

games_file=open('game/games.json','r')
games_file_data=games_file.read()
games = json.loads(games_file_data)['games']

game_rooms={}
players={}
@app.route('/')
def home():
    if not 'lang' in session:
        session['lang']='english'
    return render_template('home.html',home=home_lang[session['lang']])

@app.route('/lang')
def lang():
    session['lang']=request.args.get('name')
    return redirect('/')

@app.route('/get-avatars')
def get_avatars():
    avatars=os.listdir("game/static/avatars")
    avatar_list=[]
    for i in avatars:
        avatar_list.append({
            "name": i,
            "path": "/static/avatars/"+i,
            "bg": i.split(".")[0].split("-")[1]
        })
    return jsonify({
        "success":True,
        "data":avatar_list
    })

@app.route("/chosen-avatar", methods=["POST"])
def chosen_avatar():
    player_id=session["player_id"]
    avatar=request.form["avatar"]
    room_code=request.form["room_code"]
    if room_code in game_rooms:
        pass
    else:
        return jsonify({
            "success":False,
            "message":"Room does not exists",
            "data":[]
        })
        
    if player_id in game_rooms[room_code]["players"]:
        game_rooms[room_code]['player_info'][player_id]['img']=avatar
    else:
        return jsonify({
            "success":False,
            "message":"Player is not in this game",
            "data":[]
        })
    
    return jsonify({
            "success":True,
            "message":"Avatar Added"
        })

@app.route('/create', methods=["POST"])
def create_game():
    player_name=request.form['player_name']
    room_code = str(uuid4())[:8]
    player_id = str(uuid4())[:15]
    session['player_id']=player_id
    players[player_id]=player_name
    game_rooms[room_code]={"players":[player_id]}
    game_rooms[room_code]["winner"]=None
    game_rooms[room_code]["creator"]={"id":player_id,"name":player_name,"time":datetime.now()}
    game_rooms[room_code]['player_info']={}
    game_rooms[room_code]["rounds"]=[]
    game_rooms[room_code]['player_info'][session['player_id']]={}
    game_rooms[room_code]['player_info'][session['player_id']]['time']=datetime.now()
    game_rooms[room_code]['player_info'][session['player_id']]['img']=random.choice(avatars)
    game_rooms[room_code]['player_info'][session['player_id']]['name']=player_name
    game_rooms[room_code]["player_info"][session['player_id']]["points"]=0
    return redirect('game/'+room_code)

@app.route('/game/<string:room_id>')
def game(room_id):
    if room_id in game_rooms:
        return render_template('game.html', room_id=room_id)
    else:
        return redirect("/")
    
@app.route('/check/<string:room_id>')
def check_players(room_id):
    if room_id in game_rooms:
        players=game_rooms[room_id]['players']
        # Only update time if player_id exists in session and in this room
        if 'player_id' in session and session['player_id'] in game_rooms[room_id]['player_info']:
            game_rooms[room_id]['player_info'][session['player_id']]['time']=datetime.now()
        rlist=[]
        for pid in players:
            # Calculate the difference between datetime objects
            time_difference = datetime.now() - game_rooms[room_id]['player_info'][pid]['time']
            # Extract the difference in seconds
            seconds_difference = time_difference.total_seconds()
            if seconds_difference>10:
                rlist.append(pid)
        for pid in rlist:
            game_rooms[room_id]['players'].remove(pid)
        return jsonify(players)
    else:
        return jsonify([])

@app.route('/homeimg')
def homeimg():
    return render_template('home-img.html')

@app.route('/join',methods=["POST"])
def join():
    room_code = request.form["room_code"]
    if room_code in game_rooms:
        player_name=request.form['player_name']
        player_id = str(uuid4())[:15]
        session['player_id']=player_id
        players[player_id]=player_name
        game_rooms[room_code]["players"].append(player_id)
        game_rooms[room_code]['player_info'][session['player_id']]={}
        game_rooms[room_code]['player_info'][session['player_id']]['time']=datetime.now()
        game_rooms[room_code]['player_info'][session['player_id']]['img']=random.choice(avatars)
        game_rooms[room_code]['player_info'][session['player_id']]['name']=player_name
        game_rooms[room_code]["player_info"][session['player_id']]["points"]=0
        return redirect('game/'+room_code)
    flash('No such room')
    return redirect('/')

@app.route('/get-game-data')
def getgamedata():
  room_code=request.args.get("id")
  if room_code in game_rooms:
    a = {
      "room_data":game_rooms[room_code],
      "my_id":session['player_id'],
      "creator":game_rooms[room_code]["creator"]
    }
    return jsonify(a)
  else:
    return jsonify({"message":"No such room"})

@app.route('/get-round-data')
def getrounddata():
  room_code=request.args.get("id")
  if room_code in game_rooms:
    a = {
        "game":game_rooms[room_code],
        "success":True,
        "round_data":game_rooms[room_code]["rounds"],
        "player_info":game_rooms[room_code]["player_info"],
        "my_id":session['player_id'],
        "creator":game_rooms[room_code]["creator"]
    }
    if game_rooms[room_code]["rounds"]:
        if game_rooms[room_code]["rounds"][-1]["winner"]:
            a["player_name"]=players[game_rooms[room_code]["rounds"][-1]["winner"]]
    return jsonify(a)
  else:
    return jsonify({"success":False,"message":"No such room"})

@app.route("/choose-game")
def choose_game():
    room_code = request.args.get("room_code")
    
    # If room doesn't exist or no round selection cached, generate new games
    if room_code and room_code in game_rooms:
        current_round = len(game_rooms[room_code]["rounds"])
        cache_key = f"round_{current_round}_games"
        
        # Check if we already have games for this round
        if cache_key not in game_rooms[room_code]:
            temp_games = games.copy()
            choose_game_list = []
            for _ in range(3):
                random_game = random.choice(list(temp_games.keys())) 
                data = {
                    "name": random_game,
                    "path": temp_games[random_game]["path"],
                    "bg": temp_games[random_game]["bg"]
                }
                choose_game_list.append(data)
                del temp_games[random_game]
            # Cache the games for this round
            game_rooms[room_code][cache_key] = choose_game_list
        else:
            choose_game_list = game_rooms[room_code][cache_key]
    else:
        # Fallback if no room code provided
        temp_games = games.copy()
        choose_game_list = []
        for _ in range(3):
            random_game = random.choice(list(temp_games.keys())) 
            data = {
                "name": random_game,
                "path": temp_games[random_game]["path"],
                "bg": temp_games[random_game]["bg"]
            }
            choose_game_list.append(data)
            del temp_games[random_game]
    
    return jsonify({
        "games": choose_game_list
    })
    
@app.route("/chosen-game", methods=["POST"])
def chosen_game():
    player_id=session["player_id"]
    game=request.form["game"]
    room_code=request.form["room_code"]
    if room_code in game_rooms:
        pass
    else:
        return jsonify({
            "success":False,
            "message":"Room does not exists",
            "data":[]
        })
        
    if player_id in game_rooms[room_code]["players"]:
        game_rooms[room_code]["rounds"].append({"round":1,"name":game,"winner":None, "creator":player_id})
    else:
        return jsonify({
            "success":False,
            "message":"Player is not in this game",
            "data":[]
        })
    return jsonify({
            "success":True,
            "message":"Game Added",
            "data":{
                "game":game,
                "my_id":session["player_id"],
                "rounds":game_rooms[room_code]["rounds"],
                "all":[request.referrer,game,session["player_id"],game_rooms[room_code]["rounds"]]
                }
        })

@app.route("/chosen-winner", methods=["POST"])
def chosen_winner():
    player_id=session["player_id"]
    winner_id=request.form["winner_id"]
    room_code=request.form["room_code"]
    if room_code in game_rooms:
        pass
    else:
        return jsonify({
            "success":False,
            "message":"Room does not exists",
            "data":[]
        })
        
    if player_id in game_rooms[room_code]["players"]:
        game_rooms[room_code]["rounds"][-1]["winner"]=winner_id
        game_rooms[room_code]["rounds"][-1]["winner_name"]=players[winner_id]
        game_rooms[room_code]["player_info"][winner_id]["points"]+=len(game_rooms[room_code]["rounds"])
    else:
        return jsonify({
            "success":False,
            "message":"Player is not in this game",
            "data":[]
        })
    player_ids=game_rooms[room_code]["player_info"].keys()
    for i in player_ids:
        if game_rooms[room_code]["player_info"][i]["points"]>50:
            game_rooms[room_code]["winner"]={"winner_id":i,"winner_name":players[i]}
        
    return jsonify({
            "success":True,
            "message":"Game Added",
            "data":{
                    "game":game_rooms[room_code],
                    "my_id":session["player_id"],
                    "player_name": players[winner_id],
                    "rounds":game_rooms[room_code]["rounds"],
                    "all":[request.referrer,game_rooms[room_code],session["player_id"],game_rooms[room_code]["rounds"]]
                }
        })



@app.route('/get-game-ui')
def getgameui():
    return jsonify({"style":"""
        :root {
            --primary-color: #00d4ff;
            --secondary-color: #ff00ea;
            --accent-color: #ffea00;
            --dark-bg: #0a0e27;
            --card-bg: rgba(15, 23, 42, 0.9);
            --glow-color: rgba(0, 212, 255, 0.5);
            --blue-rgb: 92 192 249;
            --green-rgb: 125 161 35;
            --brown-rgb: 127 46 23;
            --purple-rgb: 128 0 128;
            --red-rgb: 255 88 46;
            --grey-rgb: 143 143 143;
        }

        *,
        *:before,
        *:after {
            box-sizing: border-box;
        }

        html,
        body {
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0a0e27 100%);
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Orbitron', sans-serif;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: #dee2e6;
            transition: background-color 1000ms;
            position: relative;
        }

        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 50%, rgba(0, 212, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(255, 0, 234, 0.1) 0%, transparent 50%);
            animation: bgPulse 10s ease-in-out infinite;
            z-index: 0;
        }

        @keyframes bgPulse {
            0%, 100% { opacity: 0.5; }
            50% { opacity: 1; }
        }

        body:has(.card[data-color="blue"]:hover) {
            background: linear-gradient(135deg, rgb(var(--blue-rgb) / 25%), #0a0e27);
        }

        body:has(.card[data-color="purple"]:hover) {
            background: linear-gradient(135deg, rgb(var(--purple-rgb) / 25%), #0a0e27);
        }

        body:has(.card[data-color="green"]:hover) {
            background: linear-gradient(135deg, rgb(var(--green-rgb) / 25%), #0a0e27);
        }

        body:has(.card[data-color="brown"]:hover) {
            background: linear-gradient(135deg, rgb(var(--brown-rgb) / 25%), #0a0e27);
        }

        body:has(.card[data-color="grey"]:hover) {
            background: linear-gradient(135deg, rgb(var(--grey-rgb) / 25%), #0a0e27);
        }

        body:has(.card[data-color="red"]:hover) {
            background: linear-gradient(135deg, rgb(var(--red-rgb) / 25%), #0a0e27);
        }

        .center {
            position: relative;
            z-index: 1;
            width: 100%;
            max-width: 1400px;
            padding: 2rem;
        }

        /* Round Display */
        .round {
            font-family: 'Orbitron', sans-serif;
            font-weight: 900;
            color: var(--primary-color);
            text-shadow: 0 0 30px var(--glow-color);
            animation: slideInDown 0.8s ease-out;
            text-transform: uppercase;
            letter-spacing: 3px;
        }

        @keyframes slideInDown {
            from {
                opacity: 0;
                transform: translateY(-50px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Player Cards */
        .player-card {
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 2rem;
            border: 2px solid rgba(0, 212, 255, 0.3);
            transition: all 0.4s;
            animation: fadeInUp 0.8s ease-out;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(50px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .player-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 60px rgba(0, 212, 255, 0.4);
            border-color: var(--primary-color);
        }

        .pimg {
            border-radius: 50%;
            border: 4px solid rgba(0, 212, 255, 0.5);
            box-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
            transition: all 0.4s;
            animation: pulse 3s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { 
                transform: scale(1);
                box-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
            }
            50% { 
                transform: scale(1.05);
                box-shadow: 0 0 50px rgba(0, 212, 255, 0.6);
            }
        }

        .pimg:hover {
            transform: scale(1.1) rotate(5deg);
            border-color: var(--accent-color);
        }

        /* VS Section - Improved */
        .vs-container {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem 0;
        }

        img[src*="vs.png"] {
            filter: drop-shadow(0 0 30px var(--secondary-color)) drop-shadow(0 0 60px var(--primary-color));
            animation: vsFloat 3s ease-in-out infinite;
            transition: all 0.3s;
        }

        img[src*="vs.png"]:hover {
            filter: drop-shadow(0 0 40px var(--accent-color)) drop-shadow(0 0 80px var(--secondary-color));
            transform: scale(1.15) rotate(5deg);
        }

        @keyframes vsFloat {
            0%, 100% { 
                transform: translateY(0) scale(1) rotate(0deg); 
            }
            50% { 
                transform: translateY(-15px) scale(1.08) rotate(-3deg); 
            }
        }

        @keyframes rotate {
            0%, 100% { transform: rotate(0deg) scale(1); }
            50% { transform: rotate(10deg) scale(1.1); }
        }

        /* Buttons */
        .eightbit-btn {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            display: inline-block;
            position: relative;
            text-align: center;
            font-size: 1rem;
            padding: 1rem 2.5rem;
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            text-decoration: none;
            color: white;
            border: none;
            border-radius: 15px;
            cursor: pointer;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 2px;
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0, 212, 255, 0.3);
        }

        .eightbit-btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }

        .eightbit-btn:hover::before {
            width: 300px;
            height: 300px;
        }

        .eightbit-btn:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 212, 255, 0.6);
        }

        .eightbit-btn:active {
            transform: translateY(-2px);
        }

        /* Cards for Game Selection */
        #cards {
            width: 100%;
            display: flex;
            justify-content: space-evenly;
            gap: 2rem;
            flex-wrap: wrap;
        }

        .card {
            background-size: cover;
            background-position: center;
            position: relative;
            cursor: pointer;
            outline: none;
            transition: scale 100ms;
            border-radius: clamp(0.5rem, 0.75vw, 2rem);
            overflow: visible;
        }

        .card .card-front-image {
            position: relative;
            z-index: 2;
        }

        .card .card-image {
            width: clamp(150px, 20vw, 250px);
            aspect-ratio: 2 / 3;
            border-radius: clamp(0.5rem, 0.75vw, 2rem);
        }

        .card-faders {
            height: 100%;
            width: 100%;
            position: absolute;
            left: 0px;
            top: 0px;
            z-index: 1;
            opacity: 0;
            transition: opacity 1500ms;
            pointer-events: none;
        }

        .card:hover .card-faders {
            opacity: 1;
        }

        .card:active {
            scale: 0.98;
        }

        .card-fader {
            position: absolute;
            left: 0px;
            top: 0px;
        }

        .card-fader:nth-child(odd) {
            animation: fade-left 3s linear infinite;
        }

        .card-fader:nth-child(even) {
            animation: fade-right 3s linear infinite;
        }

        .card-fader:is(:nth-child(3), :nth-child(4)) {
            animation-delay: 750ms;
        }

        .card-fader:is(:nth-child(5), :nth-child(6)) {
            animation-delay: 1500ms;
        }

        .card-fader:is(:nth-child(7), :nth-child(8)) {
            animation-delay: 2250ms;
        }

        @keyframes fade-left {
            from {
                scale: 1;
                translate: 0%;
                opacity: 1;
            }
            to {
                scale: 0.8;
                translate: -30%;
                opacity: 0;
            }
        }

        @keyframes fade-right {
            from {
                scale: 1;
                translate: 0%;
                opacity: 1;
            }
            to {
                scale: 0.8;
                translate: 30%;
                opacity: 0;
            }
        }

        /* Modal Styles */
        #exampleModal, #declareWinnerModal, #avatarModal {
            z-index: 100000;
        }

        .modal-dialog {
            max-width: 1000px;
        }

        .modal-body {
            background: rgba(10, 14, 39, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 2rem;
        }

        .modal-content {
            background: transparent;
            border: none;
        }

        /* Game Selection Modal */
        #exampleModal .modal-body {
            padding: 3rem 2rem;
        }

        #exampleModal #cards {
            justify-content: center;
            gap: 3rem;
        }

        /* Avatar Selection Modal - Carousel Design */
        #avatarModal .modal-dialog {
            max-width: 1400px !important;
            width: 85vw !important;
            margin: 2rem auto;
        }

        #avatarModal .modal-content {
            background: rgba(10, 14, 39, 0.98) !important;
            border: 2px solid rgba(0, 212, 255, 0.4);
            border-radius: 25px;
            box-shadow: 0 30px 90px rgba(0, 212, 255, 0.3);
        }

        #avatarModal .modal-body {
            padding: 3rem 2rem;
            overflow: hidden;
        }

        /* Modal Header */
        .modal-title {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
            color: white !important;
            font-family: 'Orbitron', sans-serif !important;
            font-size: clamp(1.3rem, 2.5vw, 2rem) !important;
            font-weight: 900 !important;
            padding: 1.8rem 2rem !important;
            text-align: center !important;
            border-radius: 23px 23px 0 0 !important;
            text-shadow: 0 4px 10px rgba(0, 0, 0, 0.5);
            letter-spacing: 3px;
            text-transform: uppercase;
        }

        /* Avatar Carousel Container */
        .avatar-carousel-container {
            position: relative;
            width: 100%;
            padding: 2rem 0;
        }

        .avatar-choose {
            display: flex !important;
            gap: 2rem !important;
            padding: 2rem !important;
            justify-content: center;
            align-items: center;
            flex-wrap: nowrap !important;
        }

        .avatar-choose > div {
            flex: 0 0 auto;
            width: 350px !important;
            max-width: 350px;
            margin: 0 !important;
            padding: 0 !important;
            display: none;
        }

        .avatar-choose > div.active {
            display: block;
        }

        /* Avatar Card Styling - Large Size */
        .avatar-choose .card {
            width: 100%;
            background: rgba(15, 23, 42, 0.8);
            border: 3px solid rgba(0, 212, 255, 0.3);
            border-radius: 25px;
            padding: 1.5rem;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            cursor: pointer;
            position: relative;
            overflow: visible;
        }

        .avatar-choose .card::before {
            content: '';
            position: absolute;
            top: -3px;
            left: -3px;
            right: -3px;
            bottom: -3px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border-radius: 25px;
            opacity: 0;
            z-index: -1;
            transition: opacity 0.4s;
        }

        .avatar-choose .card:hover {
            transform: scale(1.05);
            border-color: var(--accent-color);
            box-shadow: 0 25px 60px rgba(0, 212, 255, 0.6);
        }

        .avatar-choose .card:hover::before {
            opacity: 1;
        }

        /* Avatar Image - Very Large */
        .avatar-choose .card-image {
            width: 100% !important;
            height: auto !important;
            aspect-ratio: 1 / 1;
            object-fit: cover;
            border-radius: 20px;
            border: 4px solid rgba(0, 212, 255, 0.4);
            transition: all 0.4s;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }

        .avatar-choose .card:hover .card-image {
            border-color: var(--accent-color);
            box-shadow: 0 15px 50px rgba(255, 234, 0, 0.5);
            transform: scale(1.02);
        }

        /* Hide parallax effects */
        .avatar-choose .card-faders {
            display: none !important;
        }

        /* Navigation Arrows */
        .avatar-nav-btn {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            width: 70px;
            height: 70px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            color: white;
            cursor: pointer;
            transition: all 0.3s;
            z-index: 10;
            box-shadow: 0 10px 30px rgba(0, 212, 255, 0.5);
        }

        .avatar-nav-btn:hover {
            transform: translateY(-50%) scale(1.1);
            box-shadow: 0 15px 40px rgba(0, 212, 255, 0.7);
            background: linear-gradient(135deg, var(--secondary-color), var(--accent-color));
        }

        .avatar-nav-btn:active {
            transform: translateY(-50%) scale(0.95);
        }

        .avatar-nav-btn.disabled {
            opacity: 0.3;
            cursor: not-allowed;
            pointer-events: none;
        }

        .avatar-nav-prev {
            left: -90px;
        }

        .avatar-nav-next {
            right: -90px;
        }

        /* Page Indicator */
        .avatar-page-indicator {
            text-align: center;
            margin-top: 2rem;
            font-family: 'Orbitron', sans-serif;
            color: var(--primary-color);
            font-size: 1.2rem;
            font-weight: bold;
        }

        .avatar-page-dots {
            display: flex;
            justify-content: center;
            gap: 0.8rem;
            margin-top: 1rem;
        }

        .avatar-page-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: rgba(0, 212, 255, 0.3);
            transition: all 0.3s;
            cursor: pointer;
        }

        .avatar-page-dot.active {
            background: var(--primary-color);
            box-shadow: 0 0 15px var(--primary-color);
            transform: scale(1.3);
        }

        /* Responsive */
        @media (max-width: 1600px) {
            .avatar-choose > div {
                width: 300px !important;
                max-width: 300px;
            }
            
            .avatar-nav-prev {
                left: -80px;
            }
            
            .avatar-nav-next {
                right: -80px;
            }
        }

        @media (max-width: 1200px) {
            .avatar-choose > div {
                width: 250px !important;
                max-width: 250px;
            }

            .avatar-nav-btn {
                width: 60px;
                height: 60px;
                font-size: 1.5rem;
            }
            
            .avatar-nav-prev {
                left: -70px;
            }
            
            .avatar-nav-next {
                right: -70px;
            }
        }

        @media (max-width: 768px) {
            #avatarModal .modal-dialog {
                width: 95vw !important;
            }

            .avatar-choose {
                gap: 1rem !important;
            }

            .avatar-choose > div {
                width: 200px !important;
                max-width: 200px;
            }

            .avatar-nav-btn {
                width: 50px;
                height: 50px;
                font-size: 1.2rem;
            }

            .avatar-nav-prev {
                left: 10px;
            }

            .avatar-nav-next {
                right: 10px;
            }

            .modal-title {
                font-size: 0.9rem !important;
                padding: 1.2rem !important;
            }
        }

        /* Divider */
        hr {
            margin: 40px auto;
            max-width: 200px;
            height: 2px;
            border: 0;
            background: linear-gradient(90deg, transparent, var(--primary-color), transparent);
            animation: glow 2s ease-in-out infinite;
        }

        @keyframes glow {
            0%, 100% { opacity: 0.5; }
            50% { opacity: 1; }
        }

        /* Text Styles */
        h1 {
            font-size: clamp(1.5rem, 4vw, 2.8rem);
            font-family: 'Press Start 2P', cursive;
            color: var(--primary-color);
        }

        h2 {
            font-size: clamp(1.2rem, 3vw, 2rem);
            font-family: 'Press Start 2P', cursive;
        }

        h3, h5 {
            font-family: 'Orbitron', sans-serif;
            color: var(--primary-color);
        }

        .declare-winner {
            display: none;
        }

        /* Responsive Design */
        @media(max-width: 1200px) {
            #cards {
                flex-direction: column;
                align-items: center;
                gap: 3rem;
            }

            .card .card-image {
                width: 300px;
            }
        }

        @media(max-width: 768px) {
            .center {
                padding: 1rem;
            }

            .player-card {
                padding: 1rem;
            }

            .eightbit-btn {
                font-size: 12px;
                padding: 12px 20px;
            }

            #cards {
                gap: 2rem;
                padding: 1rem;
            }

            .card .card-image {
                width: 250px;
            }
        }

        /* Modern Modal Styles */
        .modern-modal-content {
            background: linear-gradient(135deg, rgba(10, 14, 39, 0.98) 0%, rgba(26, 31, 58, 0.98) 100%);
            border: 2px solid rgba(0, 212, 255, 0.3);
            border-radius: 30px;
            box-shadow: 0 30px 90px rgba(0, 212, 255, 0.4);
            overflow: hidden;
        }

        .modern-modal-body {
            padding: 2rem;
        }

        .modern-modal-header {
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 2px solid rgba(0, 212, 255, 0.2);
        }

        .modern-modal-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
            letter-spacing: 2px;
            animation: titlePulse 3s ease-in-out infinite;
        }

        @keyframes titlePulse {
            0%, 100% { opacity: 0.9; }
            50% { opacity: 1; }
        }

        /* Game Selection Modal Styles */
        .game-carousel-container {
            position: relative;
            padding: 2rem 0;
        }

        .game-cards-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 2.5rem;
            flex-wrap: wrap;
            padding: 1rem;
        }

        #game-choose #cards .card {
            width: 280px;
            height: 360px;
            background: rgba(15, 23, 42, 0.8);
            border: 3px solid rgba(0, 212, 255, 0.3);
            border-radius: 25px;
            padding: 1.2rem;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            cursor: pointer;
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        #game-choose #cards .card::before {
            content: '';
            position: absolute;
            top: -3px;
            left: -3px;
            right: -3px;
            bottom: -3px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border-radius: 25px;
            opacity: 0;
            z-index: -1;
            transition: opacity 0.4s;
        }

        #game-choose #cards .card:hover {
            transform: translateY(-15px) scale(1.05);
            border-color: var(--accent-color);
            box-shadow: 0 30px 70px rgba(0, 212, 255, 0.6);
        }

        #game-choose #cards .card:hover::before {
            opacity: 1;
        }

        #game-choose #cards .card-front-image {
            width: 100% !important;
            height: 100% !important;
            object-fit: cover;
            border-radius: 20px;
            border: 4px solid rgba(0, 212, 255, 0.4);
            transition: all 0.4s;
        }

        #game-choose #cards .card:hover .card-front-image {
            border-color: var(--accent-color);
            box-shadow: 0 15px 50px rgba(255, 234, 0, 0.5);
        }

        /* Winner Selection Modal Styles */
        .winner-selection-container {
            padding: 2rem 0;
        }

        .winner-cards-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 4rem;
            flex-wrap: wrap;
        }

        .winner-card {
            width: 280px;
            background: rgba(15, 23, 42, 0.8);
            border: 3px solid rgba(0, 212, 255, 0.3);
            border-radius: 25px;
            padding: 1.5rem;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }

        .winner-card::before {
            content: '';
            position: absolute;
            top: -3px;
            left: -3px;
            right: -3px;
            bottom: -3px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border-radius: 25px;
            opacity: 0;
            z-index: -1;
            transition: opacity 0.4s;
        }

        .winner-card:hover {
            transform: translateY(-20px) scale(1.08);
            border-color: var(--accent-color);
            box-shadow: 0 35px 80px rgba(0, 212, 255, 0.7);
        }

        .winner-card:hover::before {
            opacity: 1;
        }

        .winner-card-inner {
            position: relative;
            text-align: center;
        }

        .winner-avatar {
            width: 220px;
            height: 220px;
            object-fit: cover;
            border-radius: 20px;
            border: 4px solid rgba(0, 212, 255, 0.4);
            transition: all 0.4s;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            margin-bottom: 1rem;
        }

        .winner-card:hover .winner-avatar {
            border-color: var(--accent-color);
            box-shadow: 0 20px 60px rgba(255, 234, 0, 0.6);
            transform: scale(1.05);
        }

        .winner-name {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-top: 0.5rem;
            letter-spacing: 1px;
            text-shadow: 0 0 15px rgba(0, 212, 255, 0.5);
        }

        .winner-badge {
            position: absolute;
            top: -10px;
            right: -10px;
            font-size: 2.5rem;
            opacity: 0;
            transform: scale(0) rotate(-20deg);
            transition: all 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        }

        .winner-card:hover .winner-badge {
            opacity: 1;
            transform: scale(1) rotate(0deg);
        }

        .winner-vs-divider {
            font-family: 'Orbitron', sans-serif;
            font-size: 2.5rem;
            font-weight: 900;
            color: var(--accent-color);
            text-shadow: 0 0 30px rgba(255, 234, 0, 0.8);
            animation: pulse 2s ease-in-out infinite;
        }

        /* Responsive for modals */
        @media (max-width: 1200px) {
            .game-cards-wrapper,
            .winner-cards-wrapper {
                gap: 1.5rem;
            }

            #game-choose #cards .card {
                width: 240px;
                height: 320px;
            }

            .winner-card {
                width: 240px;
            }

            .winner-avatar {
                width: 180px;
                height: 180px;
            }
        }

        @media (max-width: 768px) {
            .modern-modal-body {
                padding: 1rem;
            }

            .modern-modal-title {
                font-size: 1.5rem;
            }

            #game-choose #cards .card {
                width: 200px;
                height: 280px;
            }

            .winner-card {
                width: 200px;
            }

            .winner-avatar {
                width: 150px;
                height: 150px;
            }

            .winner-vs-divider {
                font-size: 1.8rem;
            }

            .winner-name {
                font-size: 1.2rem;
            }
        }
                    """,
      "body":"""<div class="center align-middle">
        <div class="round text-center h1 py-5" id="round">
            🎮 Round <span id="round_num">1</span>
        </div>
        
        <div class="container-fluid">
            <div class="row align-items-center justify-content-center g-4">
                <div class="col-lg-4 col-md-5">
                    <div class="player-card text-center">
                        <div class="mb-3">
                            <img class="img-fluid pimg" src="/static/avatars/4.jpg" alt="Player 1" width="200px" height="200px"
                                id="player_1_img">
                        </div>
                        <div class="h3 py-2" id="player_1_name" style="color: var(--primary-color); font-family: 'Orbitron', sans-serif; font-size: 1.4rem; font-weight: 800; text-transform: uppercase; letter-spacing: 2px;">Player 1</div>
                        <div style="font-size: 1.6rem; color: var(--accent-color); font-weight: 800; font-family: 'Orbitron', sans-serif;">
                            <span id="player_1_points">0</span> Points
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-2 col-md-2">
                    <div class="vs-container">
                        <img src="/static/images/vs.png" alt="VS" class="img-fluid" style="max-width: 220px; height: auto;">
                    </div>
                </div>
                
                <div class="col-lg-4 col-md-5">
                    <div class="player-card text-center">
                        <div class="mb-3">
                            <img class="img-fluid pimg" src="/static/avatars/9.jpg" alt="Player 2" width="200px" height="200px"
                                id="player_2_img">
                        </div>
                        <div class="h3 py-2" id="player_2_name" style="color: var(--secondary-color); font-family: 'Orbitron', sans-serif; font-size: 1.4rem; font-weight: 800; text-transform: uppercase; letter-spacing: 2px;">Player 2</div>
                        <div style="font-size: 1.6rem; color: var(--accent-color); font-weight: 800; font-family: 'Orbitron', sans-serif;">
                            <span id="player_2_points">0</span> Points
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <hr />
        
        <div class="d-flex justify-content-center align-items-center" style="min-height: 80px;">
            <div class="round text-center h5 px-5" id="wait-for-choose" style="display: none; color: var(--accent-color); animation: pulse 2s infinite;">
                ⏳ Waiting for other player to choose a game...
            </div>
            <button type="button" class="eightbit-btn" data-toggle="modal" data-target="#exampleModal" id="choose-game">
                🎯 Choose Game
            </button>
        </div>
        
        <hr />
        
        <div class="d-flex justify-content-center">
            <button type="button" class="eightbit-btn declare-winner" data-toggle="modal" data-target="#declareWinnerModal" id="declare-winner">
                🏆 Declare Winner
            </button>
        </div>
        <hr class="declare-winner"/>
    </div>
    """,
    "script":"""
    <script>
        const chooseGame = async () => {
            const response = await fetch("/choose-game");
            const data = await response.json();
            console.log(data.games);
            let imgs = data.games.map((game) => {
                console.log("game bg:- ", game.bg);
                return `
                <div class="card" data-color="${game.bg}">
                    <img class="card-front-image card-image" src="${game.path}" />
                <div class="card-faders">
                    <img class="card-fader card-image" src="${game.path}" />
                    <img class="card-fader card-image" src="${game.path}" />
                    <img class="card-fader card-image" src="${game.path}" />
                    <img class="card-fader card-image" src="${game.path}" />
                    <img class="card-fader card-image" src="${game.path}" />
                    <img class="card-fader card-image" src="${game.path}" />
                    <img class="card-fader card-image" src="${game.path}" />
                    <img class="card-fader card-image" src="${game.path}" />
                </div>
                </div>
            `})
            document.getElementById('cards').innerHTML = imgs;

        }
        $('#exampleModal').on('show.bs.modal', async function (event) {
            console.log("hi");
            chooseGame();
            var button = $(event.relatedTarget) // Button that triggered the modal
            var recipient = button.data('whatever') // Extract info from data-* attributes
            var modal = $(this)
        })
    </script>
</body>
    """})

