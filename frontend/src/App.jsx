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

const MDP_INITIAL = {
  map: [
    ["S", "S", "I", "S"],
    ["S", "I", "I", "S"],
    ["B", "S", "S", "S"],
    ["S", "S", "S", "S"]
  ],
  pirate_ships: {
    pirate_ship_1: { location: [2, 0], capacity: 2 }
  },
  treasures: {
    treasure_1: {
      location: [0, 2],
      possible_locations: [[0, 2]],
      prob_change_location: 0
    }
  },
  marine_ships: {},
  "turns to go": 10,
  optimal: true
}

const VALUE_COLORS = [
  "#eff6ff", "#dbeafe", "#bfdbfe",
  "#93c5fd", "#dcfce7", "#bbf7d0",
  "#86efac", "#4ade80", "#16a34a"
]

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
  const [mdpData, setMdpData] = useState(null)
  const [mdpRunning, setMdpRunning] = useState(false)
  const [mdpIteration, setMdpIteration] = useState(0)


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

const solveMDP = async () => {
  setMdpRunning(true)
  setMdpIteration(0)
  setMdpData(null)

  const res = await fetch("http://127.0.0.1:8000/solve/mdp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ initial: MDP_INITIAL })
  })
  const data = await res.json()
  if (!data.success) {
    alert("Error: " + data.error)
    setMdpRunning(false)
    return
  }
  setMdpData(data)

  // animate through each iteration
  let i = 0
  const interval = setInterval(() => {
    i++
    setMdpIteration(i)
    if (i >= data.iterations.length) {
      clearInterval(interval)
      setMdpRunning(false)
    }
  }, 400)
}


const getValueForCell = (r, c) => {
  if (!mdpData || mdpIteration === 0) return null
  const iterData = mdpData.iterations[mdpIteration - 1]
  // get max value across capacities for this cell
  let maxVal = null
  for (let cap = 0; cap <= 2; cap++) {
    const key = `${r},${c},${cap}`
    if (iterData[key] !== undefined) {
      if (maxVal === null || iterData[key] > maxVal) maxVal = iterData[key]
    }
  }
  return maxVal
}

const getPolicyForCell = (r, c) => {
  if (!mdpData || mdpIteration === 0) return null
  return mdpData.policy_arrows[`${r},${c}`] || null
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
      {/* ── MDP SECTION ── */}
    <div style={{ marginTop: "3rem" }}>
      <h2 style={{ marginBottom: "0.25rem" }}>Value Iteration</h2>
      <p style={{ color: "#6b7280", marginBottom: "1.5rem", fontSize: "0.9rem" }}>
        Color = state value. Arrows = optimal policy. Brighter green = higher expected reward.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: `repeat(${MDP_INITIAL.map[0].length}, 64px)`, gap: 4, marginBottom: "1.5rem" }}>
        {MDP_INITIAL.map.map((row, r) =>
          row.map((cell, c) => {
            const val = getValueForCell(r, c)
            const arrow = getPolicyForCell(r, c)
            const colorIdx = val !== null ? Math.min(Math.floor((val / 8) * 8), 8) : -1
            const bg = cell === "I" ? "#d1fae5"
              : cell === "B" ? "#fef3c7"
              : colorIdx >= 0 && mdpIteration > 0 ? VALUE_COLORS[colorIdx]
              : "#f1f5f9"

            return (
              <div key={`${r}-${c}`} style={{
                width: 64, height: 64,
                background: bg,
                borderRadius: 8,
                display: "flex", flexDirection: "column",
                alignItems: "center", justifyContent: "center",
                border: "1px solid rgba(0,0,0,0.08)",
                transition: "background 0.5s ease",
                fontSize: "0.6rem",
                fontWeight: 600,
                color: colorIdx >= 6 ? "white" : "#374151",
              }}>
                <div style={{ fontSize: "1rem" }}>
                  {cell === "I" ? "🏝️" : cell === "B" ? "🏠" : arrow && mdpIteration > 0 ? arrow : ""}
                </div>
                {val !== null && mdpIteration > 0 && (
                  <div style={{ fontSize: "0.55rem", opacity: 0.7 }}>{val}</div>
                )}
              </div>
            )
          })
        )}
      </div>

      {/* stats */}
      <div style={{ display: "flex", gap: "1rem", marginBottom: "1.5rem" }}>
        <div style={{ background: "#fff1f2", border: "1px solid #fecdd3", borderRadius: 8, padding: "0.5rem 1rem" }}>
          <div style={{ fontSize: "0.6rem", color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em" }}>States</div>
          <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#be123c" }}>{mdpData ? mdpData.num_states : "—"}</div>
        </div>
        <div style={{ background: "#fefce8", border: "1px solid #fde68a", borderRadius: 8, padding: "0.5rem 1rem" }}>
          <div style={{ fontSize: "0.6rem", color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em" }}>Runtime</div>
          <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#92400e" }}>{mdpData ? mdpData.runtime + "s" : "—"}</div>
        </div>
        <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 8, padding: "0.5rem 1rem" }}>
          <div style={{ fontSize: "0.6rem", color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em" }}>Iteration</div>
          <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#15803d" }}>{mdpIteration > 0 ? mdpIteration + " / 10" : "—"}</div>
        </div>
      </div>

      <button onClick={solveMDP} disabled={mdpRunning} style={{
        background: "#be123c", color: "white", border: "none",
        borderRadius: 8, padding: "0.7rem 1.5rem",
        fontWeight: 600, fontSize: "0.85rem",
        cursor: mdpRunning ? "not-allowed" : "pointer",
        opacity: mdpRunning ? 0.6 : 1
      }}>
        {mdpRunning ? "Computing..." : "Run Value Iteration"}
      </button>
    </div>
    </div>
  )
}