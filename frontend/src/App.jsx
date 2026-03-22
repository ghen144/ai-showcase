import { useState } from "react"

const INITIAL = {
  map: [
    ["S", "S", "I", "S"],
    ["S", "I", "I", "S"],
    ["B", "S", "S", "S"],
    ["S", "S", "S", "S"]
  ],
  pirate_ships: { pirate_1: [2, 0] },
  treasures: { treasure_1: [0, 2] },
  marine_ships: {}
}

const CELL_COLORS = {
  S: "#e0f2fe",
  I: "#d1fae5",
  B: "#fef3c7",
}

export default function App() {
  const [actions, setActions] = useState([])
  const [step, setStep] = useState(-1)
  const [piratePos, setPiratePos] = useState([2, 0])
  const [running, setRunning] = useState(false)
  const [stats, setStats] = useState(null)
  const [collecting, setCollecting] = useState(false)
  const [depositing, setDepositing] = useState(false)
  const [cargo, setCargo] = useState(0)


  const solve = async () => {
    const res = await fetch("http://127.0.0.1:8000/solve/astar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ initial: INITIAL })
    })
    const data = await res.json()
    if (!data.success) return alert("No solution found")
    setActions(data.actions)
    setStats({ steps: data.num_steps, runtime: data.runtime })
    animateSolution(data.actions)
  }

    const animateSolution = (acts) => {
    setRunning(true)
    let pos = [2, 0]
    let carried = 0
    let i = 0

    const interval = setInterval(() => {
      if (i >= acts.length) {
        clearInterval(interval)
        setRunning(false)
        setCollecting(false)
        setDepositing(false)
        return
      }

      const action = acts[i]
      setStep(i)
      setCollecting(false)
      setDepositing(false)

      const sailMatch = action.match(/sail.*?\((\d+),\s*(\d+)\)/)
      if (sailMatch) {
        pos = [parseInt(sailMatch[1]), parseInt(sailMatch[2])]
        setPiratePos([...pos])
      }

      if (action.includes("collect")) {
        setCollecting(true)
        carried++
        setCargo(carried)
      }

      if (action.includes("deposit")) {
        setDepositing(true)
        carried = 0
        setCargo(0)
      }

      i++
    }, 600)
  }

  const reset = () => {
    setActions([])
    setStep(-1)
    setPiratePos([2, 0])
    setStats(null)
    setRunning(false)
    setCollecting(false)   
    setDepositing(false)   
    setCargo(0)            
  }

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: 600 }}>
      <h1 style={{ marginBottom: "0.25rem" }}>A* Pirate Navigation</h1>
      <p style={{ color: "#6b7280", marginBottom: "1.5rem" }}>
        Watch A* find the optimal path to collect all treasures.
      </p>

      {/* GRID */}
      <div style={{ display: "grid", gridTemplateColumns: `repeat(${INITIAL.map[0].length}, 64px)`, gap: 4, marginBottom: "1.5rem" }}>
        {INITIAL.map.map((row, r) =>
          row.map((cell, c) => {
            const isPirate = piratePos[0] === r && piratePos[1] === c
            const isTreasure = Object.values(INITIAL.treasures).some(
              ([tr, tc]) => tr === r && tc === c
            )

            return (
              <div key={`${r}-${c}`} style={{
                width: 64, height: 64,
                background: isPirate ? "#1d4ed8" : isTreasure && collecting ? "#f59e0b" : isTreasure ? "#fde68a" : cell === "B" && depositing ? "#16a34a" : CELL_COLORS[cell] || "#e5e7eb",
                borderRadius: 8,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: isPirate ? "1.4rem" : "0.65rem",
                fontWeight: 600,
                color: isPirate ? "white" : "#374151",
                border: isPirate ? "2px solid #1e40af" : "1px solid rgba(0,0,0,0.08)",
                transition: "all 0.4s ease",
                boxShadow: isPirate ? "0 4px 14px rgba(29,78,216,0.35)" : "none"
              }}>
                {isPirate ? collecting ? "🤿" : depositing ? "🏃" : "⛵" : isTreasure && collecting ? "✨" : isTreasure ? "💰" : cell === "B" ? "🏠" : cell === "I" ? "🏝️" : ""}
              </div>
            )
          })
        )}
      </div>

      {/* STATS */}
      {stats && (
        <div style={{ display: "flex", gap: "1rem", marginBottom: "1.5rem" }}>
          <div style={{ background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: 8, padding: "0.5rem 1rem" }}>
            <div style={{ fontSize: "0.6rem", color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em" }}>Steps</div>
            <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#1d4ed8" }}>{stats.steps}</div>
          </div>
          <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 8, padding: "0.5rem 1rem" }}>
            <div style={{ fontSize: "0.6rem", color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em" }}>Runtime</div>
            <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#15803d" }}>{stats.runtime}s</div>
          </div>
          <div style={{ background: "#fefce8", border: "1px solid #fde68a", borderRadius: 8, padding: "0.5rem 1rem" }}>
            <div style={{ fontSize: "0.6rem", color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em" }}>Current step</div>
            <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#92400e" }}>{step >= 0 ? step + 1 : "—"}</div>
          </div>
        </div>
      )}

      {/* ACTION LOG */}
      {actions.length > 0 && (
        <div style={{ background: "#f9fafb", border: "1px solid #e5e7eb", borderRadius: 8, padding: "1rem", marginBottom: "1.5rem", maxHeight: 140, overflowY: "auto" }}>
          {actions.map((a, i) => (
            <div key={i} style={{
              fontSize: "0.72rem", fontFamily: "monospace",
              color: i === step ? "#1d4ed8" : "#6b7280",
              fontWeight: i === step ? 700 : 400,
              padding: "0.15rem 0"
            }}>
              {i + 1}. {a}
            </div>
          ))}
        </div>
      )}

      
      {cargo > 0 && (
        <div style={{ marginBottom: "1rem", fontSize: "0.8rem", color: "#92400e", background: "#fefce8", border: "1px solid #fde68a", borderRadius: 8, padding: "0.5rem 1rem", display: "inline-block" }}>
          Carrying {cargo} treasure{cargo > 1 ? "s" : ""}
        </div>
      )}

      {/* BUTTONS */}
      <div style={{ display: "flex", gap: "0.75rem" }}>
        <button onClick={solve} disabled={running} style={{
          background: "#1d4ed8", color: "white", border: "none",
          borderRadius: 8, padding: "0.7rem 1.5rem",
          fontWeight: 600, fontSize: "0.85rem", cursor: running ? "not-allowed" : "pointer",
          opacity: running ? 0.6 : 1
        }}>
          {running ? "Solving..." : "Run A*"}
        </button>
        <button onClick={reset} style={{
          background: "white", color: "#374151",
          border: "1px solid #d1d5db", borderRadius: 8,
          padding: "0.7rem 1.5rem", fontWeight: 600,
          fontSize: "0.85rem", cursor: "pointer"
        }}>
          Reset
        </button>
      </div>
    </div>
  )
}