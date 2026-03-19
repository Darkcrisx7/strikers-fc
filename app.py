from flask import Flask, render_template, request, jsonify, session, send_from_directory
import json, os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'strikers-fc-secret-2024-xK9pL2'

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')

# ── Admin credentials (change password if you want!) ────────────
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'StrikersFC2024!'
# ────────────────────────────────────────────────────────────────

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        "players": [
            {"id":1,"name":"Marcus Johnson","position":"Striker","number":9,"goals":14,"assists":5,"matches":18,"photo":"MJ"},
            {"id":2,"name":"Dele Okafor","position":"Midfielder","number":8,"goals":7,"assists":11,"matches":20,"photo":"DO"},
            {"id":3,"name":"Kofi Mensah","position":"Defender","number":5,"goals":2,"assists":3,"matches":19,"photo":"KM"},
            {"id":4,"name":"Ade Williams","position":"Goalkeeper","number":1,"goals":0,"assists":0,"matches":20,"photo":"AW"},
            {"id":5,"name":"Tunde Balogun","position":"Striker","number":11,"goals":10,"assists":4,"matches":17,"photo":"TB"},
            {"id":6,"name":"Emeka Nwosu","position":"Defender","number":4,"goals":1,"assists":2,"matches":20,"photo":"EN"},
            {"id":7,"name":"Seun Adeyemi","position":"Midfielder","number":6,"goals":5,"assists":8,"matches":18,"photo":"SA"},
            {"id":8,"name":"Chidi Okeke","position":"Defender","number":3,"goals":0,"assists":1,"matches":16,"photo":"CO"},
        ],
        "matches": [
            {"id":1,"opponent":"City Wolves","date":"2025-02-01","home":True,"score_us":3,"score_them":1,"status":"completed","scorers":["Marcus Johnson","Tunde Balogun","Seun Adeyemi"]},
            {"id":2,"opponent":"Red Eagles","date":"2025-02-08","home":False,"score_us":1,"score_them":2,"status":"completed","scorers":["Marcus Johnson"]},
            {"id":3,"opponent":"Thunder United","date":"2025-02-22","home":True,"score_us":4,"score_them":0,"status":"completed","scorers":["Marcus Johnson","Dele Okafor","Tunde Balogun","Marcus Johnson"]},
            {"id":4,"opponent":"Bay FC","date":"2025-03-01","home":False,"score_us":2,"score_them":2,"status":"completed","scorers":["Seun Adeyemi","Dele Okafor"]},
            {"id":5,"opponent":"Northside Athletic","date":"2026-03-15","home":True,"score_us":None,"score_them":None,"status":"upcoming","scorers":[]},
            {"id":6,"opponent":"Riverside Rovers","date":"2026-03-22","home":False,"score_us":None,"score_them":None,"status":"upcoming","scorers":[]},
            {"id":7,"opponent":"Golden Stars","date":"2026-04-05","home":True,"score_us":None,"score_them":None,"status":"upcoming","scorers":[]},
        ],
        "attendance": {
            "2025-02-01":["Marcus Johnson","Dele Okafor","Kofi Mensah","Ade Williams","Tunde Balogun","Emeka Nwosu","Seun Adeyemi"],
            "2025-02-08":["Marcus Johnson","Dele Okafor","Ade Williams","Tunde Balogun","Emeka Nwosu","Seun Adeyemi","Chidi Okeke"],
            "2025-02-22":["Marcus Johnson","Kofi Mensah","Ade Williams","Tunde Balogun","Emeka Nwosu","Seun Adeyemi","Chidi Okeke"],
            "2025-03-01":["Marcus Johnson","Dele Okafor","Kofi Mensah","Ade Williams","Emeka Nwosu","Seun Adeyemi","Chidi Okeke"],
        },
        "sponsors": [],
        "news": [],
        "next_id": 9
    }

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify({'error': 'Unauthorized — admin only'}), 403
        return f(*args, **kwargs)
    return decorated

# ── Auth ─────────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    body = request.json
    if body.get('username') == ADMIN_USERNAME and body.get('password') == ADMIN_PASSWORD:
        session['is_admin'] = True
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'error': 'Wrong username or password'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': True})

@app.route('/api/me')
def me():
    return jsonify({'is_admin': bool(session.get('is_admin'))})

# ── Static ───────────────────────────────────────────────────────
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# ── Main page ────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

# ── Public read API ──────────────────────────────────────────────
@app.route('/api/data')
def get_all_data():
    return jsonify(load_data())

@app.route('/api/stats')
def get_stats():
    data = load_data()
    completed = [m for m in data['matches'] if m['status'] == 'completed']
    wins   = sum(1 for m in completed if m['score_us'] > m['score_them'])
    draws  = sum(1 for m in completed if m['score_us'] == m['score_them'])
    losses = sum(1 for m in completed if m['score_us'] < m['score_them'])
    return jsonify({
        "played": len(completed), "wins": wins, "draws": draws, "losses": losses,
        "goals_for": sum(m['score_us'] for m in completed),
        "goals_against": sum(m['score_them'] for m in completed),
        "points": wins * 3 + draws
    })

# ── Admin write API ──────────────────────────────────────────────
@app.route('/api/players', methods=['POST'])
@admin_required
def add_player():
    data = load_data()
    p = request.json
    p['id'] = data['next_id']
    p['photo'] = ''.join([w[0] for w in p['name'].split()[:2]]).upper()
    p.setdefault('goals', 0); p.setdefault('assists', 0); p.setdefault('matches', 0)
    data['players'].append(p)
    data['next_id'] += 1
    save_data(data)
    return jsonify(p), 201

@app.route('/api/players/<int:pid>', methods=['PUT'])
@admin_required
def update_player(pid):
    data = load_data()
    for i, p in enumerate(data['players']):
        if p['id'] == pid:
            data['players'][i].update(request.json)
            data['players'][i]['photo'] = ''.join([w[0] for w in data['players'][i]['name'].split()[:2]]).upper()
            save_data(data)
            return jsonify(data['players'][i])
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/players/<int:pid>', methods=['DELETE'])
@admin_required
def delete_player(pid):
    data = load_data()
    data['players'] = [p for p in data['players'] if p['id'] != pid]
    save_data(data)
    return jsonify({'ok': True})

@app.route('/api/matches', methods=['POST'])
@admin_required
def add_match():
    data = load_data()
    m = request.json
    m['id'] = data['next_id']
    m.setdefault('scorers', [])
    data['matches'].append(m)
    data['next_id'] += 1
    save_data(data)
    return jsonify(m), 201

@app.route('/api/matches/<int:mid>', methods=['PUT'])
@admin_required
def update_match(mid):
    data = load_data()
    for i, m in enumerate(data['matches']):
        if m['id'] == mid:
            data['matches'][i].update(request.json)
            save_data(data)
            return jsonify(data['matches'][i])
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/matches/<int:mid>', methods=['DELETE'])
@admin_required
def delete_match(mid):
    data = load_data()
    data['matches'] = [m for m in data['matches'] if m['id'] != mid]
    save_data(data)
    return jsonify({'ok': True})

@app.route('/api/attendance', methods=['POST'])
@admin_required
def update_attendance():
    data = load_data()
    body = request.json
    data['attendance'][body['date']] = body['players']
    save_data(data)
    return jsonify({'ok': True})

# ── Sponsors API ─────────────────────────────────────────────────
@app.route('/api/sponsors', methods=['POST'])
@admin_required
def add_sponsor():
    data = load_data()
    if 'sponsors' not in data:
        data['sponsors'] = []
    s = request.json
    s['id'] = data['next_id']
    data['sponsors'].append(s)
    data['next_id'] += 1
    save_data(data)
    return jsonify(s), 201

@app.route('/api/sponsors/<int:sid>', methods=['PUT'])
@admin_required
def update_sponsor(sid):
    data = load_data()
    if 'sponsors' not in data:
        data['sponsors'] = []
    for i, s in enumerate(data['sponsors']):
        if s['id'] == sid:
            data['sponsors'][i].update(request.json)
            data['sponsors'][i]['id'] = sid
            save_data(data)
            return jsonify(data['sponsors'][i])
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/sponsors/<int:sid>', methods=['DELETE'])
@admin_required
def delete_sponsor(sid):
    data = load_data()
    if 'sponsors' not in data:
        data['sponsors'] = []
    data['sponsors'] = [s for s in data['sponsors'] if s['id'] != sid]
    save_data(data)
    return jsonify({'ok': True})

# ── News API ─────────────────────────────────────────────────────
@app.route('/api/news', methods=['POST'])
@admin_required
def add_news():
    data = load_data()
    if 'news' not in data:
        data['news'] = []
    n = request.json
    n['id'] = data['next_id']
    from datetime import date
    n.setdefault('date', date.today().isoformat())
    data['news'].insert(0, n)
    data['next_id'] += 1
    save_data(data)
    return jsonify(n), 201

@app.route('/api/news/<int:nid>', methods=['PUT'])
@admin_required
def update_news(nid):
    data = load_data()
    if 'news' not in data:
        data['news'] = []
    for i, n in enumerate(data['news']):
        if n['id'] == nid:
            data['news'][i].update(request.json)
            data['news'][i]['id'] = nid
            save_data(data)
            return jsonify(data['news'][i])
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/news/<int:nid>', methods=['DELETE'])
@admin_required
def delete_news(nid):
    data = load_data()
    if 'news' not in data:
        data['news'] = []
    data['news'] = [n for n in data['news'] if n['id'] != nid]
    save_data(data)
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(debug=True, port=5050)
