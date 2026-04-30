# 🐉 Wumpus World - Logic Agent

A Web-based AI Agent that navigates a Wumpus World grid using **Propositional Logic** and **Resolution Refutation** to deduce safe cells.

---

## 🎮 Live Demo
> Link: _Add your Vercel URL here after deployment_

---

## 📌 Project Overview

This project implements a **Knowledge-Based Agent** that:
- Navigates a dynamic grid (user-defined size)
- Receives percepts (Breeze, Stench) from the environment
- Uses a **Propositional Logic Knowledge Base (KB)** to store what it knows
- Applies **Resolution Refutation** to prove whether a cell is safe before moving

---

## 🗂️ Project Structure

```
WumpusProject/
├── app.py              ← Flask server + Game Logic + KB + Resolution (Python)
├── requirements.txt    ← Python dependencies
├── temp/
│   └── index.html      ← Web UI (HTML)
├── static/
│   ├── style.css       ← Styling
│   └── agent.js        ← Frontend logic (grid render + API calls)
└── README.md
```

---

## ⚙️ How It Works

### 1. Environment
- Grid size is defined by the user (Rows × Cols)
- **Wumpus** and **Pits** are randomly placed at game start
- Agent always starts at **(0,0)**

### 2. Percepts
| Percept | Meaning |
|---------|---------|
| 💨 Breeze | A Pit is in an adjacent cell |
| 💀 Stench | The Wumpus is in an adjacent cell |
| ✅ None | All adjacent cells are safe |

### 3. Knowledge Base (KB)
- When agent visits a cell, it **TELLs** the KB new clauses
- Example: No breeze at (0,0) → NOT_PIT(0,1) and NOT_PIT(1,0)
- All clauses are stored in **CNF (Conjunctive Normal Form)**

### 4. Resolution Refutation
- Before moving, agent **ASKs** KB: "Is this cell safe?"
- KB tries to prove **NOT_PIT** and **NOT_WUMPUS** for that cell
- If proven → agent moves ✅
- If not proven → move is blocked ❌

---

## 🎨 Grid Color Legend

| Color | Meaning |
|-------|---------|
| 🔵 Blue | Agent's current position |
| 🟢 Green | KB proven Safe cell |
| 🟠 Orange | Visited cell |
| ⬛ Gray | Unknown / Unvisited |
| 🔴 Red | Confirmed Pit or Wumpus |

---

## 📊 Metrics Dashboard

- **Inference Steps** — Total times Resolution was called
- **KB Clauses** — Total clauses currently in Knowledge Base
- **Agent Position** — Current (row, col) of agent

---

## 🚀 How To Run Locally

**Step 1:** Clone the repository
```bash
git clone https://github.com/yourusername/WumpusProject.git
cd WumpusProject
```

**Step 2:** Install dependencies
```bash
pip3 install flask
```

**Step 3:** Run the app
```bash
python3 app.py
```

**Step 4:** Open browser
```
http://127.0.0.1:5000
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3 | Backend logic |
| Flask | Web server + API |
| HTML/CSS | Frontend UI |
| JavaScript | Grid rendering + API calls |

---

## 👩‍💻 Developer

**Your Name**
Mawaddat Zahra
AI Course 