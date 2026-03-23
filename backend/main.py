from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ex1_322625120_212133219 import OnePieceProblem
from ex2_212133219_322625120 import OptimalPirateAgent, simplify_state
import search_322625120_212133219 as search
import time
import re
import traceback


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def deep_tuple(obj):
    if isinstance(obj, list):
        return tuple(deep_tuple(i) for i in obj)
    elif isinstance(obj, dict):
        return {k: deep_tuple(v) for k, v in obj.items()}
    return obj

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/solve/astar")
def solve_astar(data: dict):
    initial = deep_tuple(data["initial"])
    start = time.time()
    try:
        problem = OnePieceProblem(initial)
        node = search.astar_search(problem, problem.h_2)
        elapsed = round(time.time() - start, 3)
        if node is None:
            return {"success": False, "error": "No solution found"}
        solution = node.solution()
        return {
            "success": True,
            "actions": [str(a) for a in solution],
            "num_steps": len(solution),
            "runtime": elapsed,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/solve/mdp")
def solve_mdp(data: dict):
    initial = data["initial"]
    start = time.time()
    try:
        agent = OptimalPirateAgent(initial)
        elapsed = round(time.time() - start, 3)

        # collect values per iteration
        all_iterations = []
        for t in range(1, initial["turns to go"] + 1):
            iter_values = {}
            for state_tuple, value in agent.optimal_values[t].items():
                match = re.search(r"'location', \((\d+), (\d+)\).*?'capacity', (\d+)", str(state_tuple))
                if match:
                    r, c, cap = match.group(1), match.group(2), match.group(3)
                    key = f"{r},{c},{cap}"
                    if key not in iter_values or value > iter_values[key]:
                        iter_values[key] = round(value, 2)
            all_iterations.append(iter_values)

        # policy arrows for each cell
        policy_arrows = {}
        for state_tuple, action in agent.optimal_policies[initial["turns to go"]].items():
            match = re.search(r"'location', \((\d+), (\d+)\).*?'capacity', 0", str(state_tuple))
            if match:
                r, c = match.group(1), match.group(2)
                action_str = str(action)
                arrow = "·"
                if "sail" in action_str:
                    coords = re.findall(r'\((\d+),\s*(\d+)\)', action_str)
                    if len(coords) >= 2:
                        fr, fc = int(coords[0][0]), int(coords[0][1])
                        tr, tc = int(coords[1][0]), int(coords[1][1])
                        if tr < fr: arrow = "↑"
                        elif tr > fr: arrow = "↓"
                        elif tc < fc: arrow = "←"
                        elif tc > fc: arrow = "→"
                elif "collect" in action_str: arrow = "⊕"
                elif "deposit" in action_str: arrow = "⊛"
                policy_arrows[f"{r},{c}"] = arrow

        return {
            "success": True,
            "runtime": elapsed,
            "num_states": len(agent.all_states),
            "iterations": all_iterations,
            "policy_arrows": policy_arrows,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "trace": traceback.format_exc()}