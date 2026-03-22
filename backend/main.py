def deep_tuple(obj):
    if isinstance(obj, list):
        return tuple(deep_tuple(i) for i in obj)
    elif isinstance(obj, dict):
        return {k: deep_tuple(v) for k, v in obj.items()}
    return obj

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ex1_322625120_212133219 import OnePieceProblem
import search_322625120_212133219 as search
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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