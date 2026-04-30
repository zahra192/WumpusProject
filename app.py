from flask import Flask, jsonify, render_template, request
import random

app = Flask(__name__, template_folder='temp')

# ─── Global Game State ───────────────────────────────────────────
game = {}

# ─── Helper: Get all neighbors of a cell ─────────────────────────
def get_neighbors(row, col, total_rows, total_cols):
    neighbors = []
    if row > 0:
        neighbors.append((row - 1, col))  # up
    if row < total_rows - 1:
        neighbors.append((row + 1, col))  # down
    if col > 0:
        neighbors.append((row, col - 1))  # left
    if col < total_cols - 1:
        neighbors.append((row, col + 1))  # right
    return neighbors

# ─── Helper: Generate percepts for each cell ─────────────────────
def generate_percepts(grid, total_rows, total_cols):
    for r in range(total_rows):
        for c in range(total_cols):
            neighbors = get_neighbors(r, c, total_rows, total_cols)
            for nr, nc in neighbors:
                if grid[nr][nc]['has_pit']:
                    grid[r][c]['breeze'] = True
                if grid[nr][nc]['has_wumpus']:
                    grid[r][c]['stench'] = True
    return grid

# ─── API: Start New Game ──────────────────────────────────────────
@app.route('/new_game', methods=['POST'])
def new_game():
    global game

    data = request.json
    rows = int(data.get('rows', 4))
    cols = int(data.get('cols', 4))

    # Build empty grid
    grid = []
    for r in range(rows):
        row_list = []
        for c in range(cols):
            cell = {
                'has_pit':    False,
                'has_wumpus': False,
                'visited':    False,
                'safe':       False,
                'breeze':     False,
                'stench':     False,
            }
            row_list.append(cell)
        grid.append(row_list)

    # Agent starts at (0,0) — mark it safe and visited
    grid[0][0]['safe']    = True
    grid[0][0]['visited'] = True

    # Place Wumpus randomly (not at start, not adjacent to start)
    while True:
        wr = random.randint(0, rows - 1)
        wc = random.randint(0, cols - 1)
        # Keep wumpus away from (0,0) and its neighbors
        start_neighbors = get_neighbors(0, 0, rows, cols)
        if (wr, wc) != (0, 0) and (wr, wc) not in start_neighbors:
            grid[wr][wc]['has_wumpus'] = True
            break

    # Place Pits randomly (not at start, not adjacent to start)
    num_pits = max(1, (rows * cols) // 5)
    placed = 0
    attempts = 0
    start_neighbors = get_neighbors(0, 0, rows, cols)
    while placed < num_pits and attempts < 100:
        pr = random.randint(0, rows - 1)
        pc = random.randint(0, cols - 1)
        if (pr, pc) != (0, 0) and (pr, pc) not in start_neighbors \
                and not grid[pr][pc]['has_pit'] \
                and not grid[pr][pc]['has_wumpus']:
            grid[pr][pc]['has_pit'] = True
            placed += 1
        attempts += 1

    # Generate breeze and stench percepts
    grid = generate_percepts(grid, rows, cols)

    # Save game state
    game = {
        'grid':            grid,
        'rows':            rows,
        'cols':            cols,
        'agent_row':       0,
        'agent_col':       0,
        'agent_alive':     True,
        'inference_steps': 0,
        'kb_clauses':      [],
        'safe_cells':      [(0, 0)],
        'pit_cells':       [],
        'wumpus_cell':     None,
        'status_msg':      'Game started! Agent is at (0,0).',
    }

    # Tell KB about starting cell
    kb_tell(0, 0)

    # Always mark (0,0) neighbors as safe at start
    # Because pits/wumpus are never placed adjacent to start
    start_neighbors = get_neighbors(0, 0, rows, cols)
    for nr, nc in start_neighbors:
        if (nr, nc) not in game['safe_cells']:
            game['safe_cells'].append((nr, nc))
            game['grid'][nr][nc]['safe'] = True

    return jsonify(get_state())

# ─── Knowledge Base: TELL ────────────────────────────────────────
def kb_tell(row, col):
    rows = game['rows']
    cols = game['cols']
    cell = game['grid'][row][col]
    neighbors = get_neighbors(row, col, rows, cols)

    if not cell['breeze']:
        for nr, nc in neighbors:
            clause = [('NOT_PIT', nr, nc)]
            if clause not in game['kb_clauses']:
                game['kb_clauses'].append(clause)
                if (nr, nc) not in game['safe_cells']:
                    game['safe_cells'].append((nr, nc))
                    game['grid'][nr][nc]['safe'] = True

    if not cell['stench']:
        for nr, nc in neighbors:
            clause = [('NOT_WUMPUS', nr, nc)]
            if clause not in game['kb_clauses']:
                game['kb_clauses'].append(clause)

    if cell['breeze']:
        clause = [('PIT', nr, nc) for nr, nc in neighbors]
        if clause not in game['kb_clauses']:
            game['kb_clauses'].append(clause)

    if cell['stench']:
        clause = [('WUMPUS', nr, nc) for nr, nc in neighbors]
        if clause not in game['kb_clauses']:
            game['kb_clauses'].append(clause)

# ─── Resolution Refutation: ASK ──────────────────────────────────
def kb_ask_safe(row, col):
    game['inference_steps'] += 1

    if (row, col) in game['safe_cells']:
        return True

    kb = game['kb_clauses']

    assumption_pit = [('PIT', row, col)]
    clauses = kb + [assumption_pit]
    pit_safe = resolve(clauses, ('NOT_PIT', row, col))

    assumption_wumpus = [('WUMPUS', row, col)]
    clauses = kb + [assumption_wumpus]
    wumpus_safe = resolve(clauses, ('NOT_WUMPUS', row, col))

    return pit_safe and wumpus_safe

# ─── Resolution Engine ────────────────────────────────────────────
def resolve(clauses, goal):
    goal_literal = goal

    all_literals = []
    for clause in clauses:
        for lit in clause:
            all_literals.append(lit)

    if goal_literal in all_literals:
        return True

    r, c = goal[1], goal[2]
    if goal[0] == 'NOT_PIT':
        positive = ('PIT', r, c)
        negative = ('NOT_PIT', r, c)
    else:
        positive = ('WUMPUS', r, c)
        negative = ('NOT_WUMPUS', r, c)

    has_positive = positive in all_literals
    has_negative = negative in all_literals

    if has_positive and has_negative:
        return True

    for clause in clauses:
        if len(clause) == 1 and clause[0] == goal_literal:
            return True

    return False

# ─── API: Move Agent ─────────────────────────────────────────────
@app.route('/move', methods=['POST'])
def move():
    global game

    if not game.get('agent_alive', False):
        return jsonify({'error': 'Game over!'}), 400

    data    = request.json
    new_row = int(data.get('row'))
    new_col = int(data.get('col'))
    rows    = game['rows']
    cols    = game['cols']

    curr_r = game['agent_row']
    curr_c = game['agent_col']
    neighbors = get_neighbors(curr_r, curr_c, rows, cols)

    if (new_row, new_col) not in neighbors:
        return jsonify({'error': 'Not a valid move!'}), 400

    is_safe = kb_ask_safe(new_row, new_col)

    if not is_safe:
        game['status_msg'] = f'KB says ({new_row},{new_col}) is NOT safe! Move blocked.'
        return jsonify(get_state())

    game['agent_row'] = new_row
    game['agent_col'] = new_col
    game['grid'][new_row][new_col]['visited'] = True

    cell = game['grid'][new_row][new_col]

    if cell['has_pit']:
        game['agent_alive'] = False
        game['status_msg']  = f'Agent fell into a PIT at ({new_row},{new_col})! Game Over.'
        return jsonify(get_state())

    if cell['has_wumpus']:
        game['agent_alive'] = False
        game['status_msg']  = f'Agent eaten by WUMPUS at ({new_row},{new_col})! Game Over.'
        return jsonify(get_state())

    kb_tell(new_row, new_col)

    percepts = []
    if cell['breeze']: percepts.append('Breeze')
    if cell['stench']: percepts.append('Stench')
    if not percepts:   percepts.append('None')

    game['status_msg'] = f'Moved to ({new_row},{new_col}). Percepts: {", ".join(percepts)}'

    return jsonify(get_state())

# ─── Helper: Build state to send to frontend ─────────────────────
def get_state():
    return {
        'grid':            game['grid'],
        'rows':            game['rows'],
        'cols':            game['cols'],
        'agent_row':       game['agent_row'],
        'agent_col':       game['agent_col'],
        'agent_alive':     game['agent_alive'],
        'inference_steps': game['inference_steps'],
        'safe_cells':      game['safe_cells'],
        'status_msg':      game['status_msg'],
        'kb_size':         len(game['kb_clauses']),
    }

# ─── API: Get Current State ───────────────────────────────────────
@app.route('/state', methods=['GET'])
def get_game_state():
    if not game:
        return jsonify({'error': 'No game started'}), 400
    return jsonify(get_state())

# ─── Main Route ──────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

# ─── Run App ─────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)