// ─── Global State ────────────────────────────────────────────────
let gameState = null;

// ─── Start New Game ───────────────────────────────────────────────
function startNewGame() {
    let rows = document.getElementById('rows').value;
    let cols = document.getElementById('cols').value;

    fetch('/new_game', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rows: rows, cols: cols })
    })
    .then(res => res.json())
    .then(data => {
        gameState = data;
        renderGrid(data);
        updateMetrics(data);
    });
}

// ─── Move Agent ───────────────────────────────────────────────────
function moveAgent(row, col) {
    if (!gameState || !gameState.agent_alive) return;

    fetch('/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ row: row, col: col })
    })
    .then(res => res.json())
    .then(data => {
        gameState = data;
        renderGrid(data);
        updateMetrics(data);
    });
}

// ─── Auto Move ────────────────────────────────────────────────────
// Agent automatically picks a safe unvisited neighbor to move to
function autoMove() {
    if (!gameState || !gameState.agent_alive) {
        alert('Start a new game first!');
        return;
    }

    let ar = gameState.agent_row;
    let ac = gameState.agent_col;
    let rows = gameState.rows;
    let cols = gameState.cols;

    // Get all neighbors
    let neighbors = getNeighbors(ar, ac, rows, cols);

    // Find a safe unvisited neighbor
    let target = null;
    for (let n of neighbors) {
        let cell = gameState.grid[n[0]][n[1]];
        if (cell.safe && !cell.visited) {
            target = n;
            break;
        }
    }

    // If no safe unvisited found, try any safe neighbor
    if (!target) {
        for (let n of neighbors) {
            let cell = gameState.grid[n[0]][n[1]];
            if (cell.safe) {
                target = n;
                break;
            }
        }
    }

    if (target) {
        moveAgent(target[0], target[1]);
    } else {
        document.getElementById('status_msg').innerText =
            'No safe moves available! Agent is stuck.';
    }
}

// ─── Get Neighbors (same logic as Python) ────────────────────────
function getNeighbors(row, col, rows, cols) {
    let neighbors = [];
    if (row > 0)        neighbors.push([row - 1, col]); // up
    if (row < rows - 1) neighbors.push([row + 1, col]); // down
    if (col > 0)        neighbors.push([row, col - 1]); // left
    if (col < cols - 1) neighbors.push([row, col + 1]); // right
    return neighbors;
}

// ─── Render Grid ─────────────────────────────────────────────────
function renderGrid(data) {
    let container = document.getElementById('grid-container');
    container.innerHTML = '';

    let table = document.createElement('table');
    table.className = 'grid-table';

    for (let r = 0; r < data.rows; r++) {
        let tr = document.createElement('tr');

        for (let c = 0; c < data.cols; c++) {
            let td = document.createElement('td');
            td.className = 'cell';

            let cell = data.grid[r][c];
            let isAgent = (r === data.agent_row && c === data.agent_col);

            // ── Decide cell color ──
            if (isAgent) {
                td.classList.add('agent');
                td.innerHTML = '🧑';

            } else if (!data.agent_alive && cell.has_pit) {
                td.classList.add('danger');
                td.innerHTML = '🕳️<br><small>Pit</small>';

            } else if (!data.agent_alive && cell.has_wumpus) {
                td.classList.add('danger');
                td.innerHTML = '👹<br><small>Wumpus</small>';

            } else if (cell.visited) {
                td.classList.add('visited');
                // Show percepts on visited cells
                let percepts = '';
                if (cell.breeze) percepts += '💨';
                if (cell.stench) percepts += '💀';
                td.innerHTML = '(' + r + ',' + c + ')<br><small>' + (percepts || '✅') + '</small>';

            } else if (cell.safe) {
                td.classList.add('safe');
                td.innerHTML = '(' + r + ',' + c + ')<br><small>Safe</small>';

            } else {
                td.classList.add('unknown');
                td.innerHTML = '(' + r + ',' + c + ')';
            }

            // ── Click to move ──
            let row = r;
            let col = c;
            td.onclick = function() { moveAgent(row, col); };

            tr.appendChild(td);
        }

        table.appendChild(tr);
    }

    container.appendChild(table);
}

// ─── Update Metrics Dashboard ─────────────────────────────────────
function updateMetrics(data) {
    document.getElementById('steps').innerText    = data.inference_steps;
    document.getElementById('kb_size').innerText  = data.kb_size;
    document.getElementById('position').innerText =
        '(' + data.agent_row + ',' + data.agent_col + ')';
    document.getElementById('status_msg').innerText = data.status_msg;

    // Game over styling
    if (!data.agent_alive) {
        document.getElementById('status_msg').classList.add('game-over');
    } else {
        document.getElementById('status_msg').classList.remove('game-over');
    }
}