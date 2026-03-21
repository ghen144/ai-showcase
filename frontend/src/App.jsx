import { useState } from "react"

function App() {
  const [ping, setPing] = useState(null)

  const testBackend = async () => {
    const res = await fetch("http://127.0.0.1:8000/")
    const data = await res.json()
    setPing(data.status)
  }

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>AI Algorithms Showcase</h1>
      <p>Frontend is working.</p>
      <button onClick={testBackend}>Test backend connection</button>
      {ping && <p style={{ color: "green" }}>Backend says: {ping}</p>}
    </div>
  )
}

export default App