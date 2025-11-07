

console.log("✅ script.js loaded");

document.getElementById("sample").addEventListener("click", ()=>{
  document.getElementById("destination").value = "Bali, Indonesia";
  document.getElementById("days").value = 4;
  document.getElementById("interests").value = "nature, relax, food";
});

document.getElementById("planForm").addEventListener("submit", async (e)=>{
  e.preventDefault();

  const dest = document.getElementById("destination").value;
  const days = parseInt(document.getElementById("days").value || "3");
  const interests = document.getElementById("interests").value || "culture, food";
  const resultArea = document.getElementById("resultArea");

  resultArea.innerHTML = `<div class="alert alert-info">Generating itinerary…</div>`;
  console.log("🛰️ Form submitted:", { destination: dest, days, interests });

  try {
    // Use full Render URL
    const resp = await fetch("https://travelgpt-kc3z.onrender.com/api/itinerary", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ destination: dest, days, interests })
    });

    console.log("📡 Fetch sent. Waiting for response...");
    const data = await resp.json();
    console.log("✅ Got response:", data);

    if(!data.ok){ 
      throw new Error("Response not OK"); 
    }

    renderResult(data.generated);

  } catch(err){
    console.error("❌ Fetch failed:", err);
    resultArea.innerHTML = `<div class="alert alert-danger">
      Failed to generate itinerary. Check console for details.
    </div>`;
  }
});

function renderResult(generated){
  const resultArea = document.getElementById("resultArea");

  if(!generated){
    resultArea.innerHTML = `<div class="alert alert-warning">No data generated.</div>`;
    return;
  }

  // Handle Gemini/OpenAI-style response
  if(generated.source === "openai" || generated.source === "gemini"){
    resultArea.innerHTML = `<div class="card">
      <div class="card-body"><pre>${escapeHtml(generated.text)}</pre></div>
    </div>`;
    return;
  }

  // Fallback: rule-based itinerary
  const meta = generated.meta || {};
  let out = `<div class="card"><div class="card-body">`;
  out += `<h5>${meta.destination || "Trip"} — ${meta.days || "?"} day(s)</h5>`;
  if(meta.weather_note){ out += `<p><strong>Weather:</strong> ${meta.weather_note}</p>`;}
  out += `<div class="list-group">`;

  for(const day of generated.itinerary || []){
    out += `<div class="list-group-item"><strong>Day ${day.day}</strong><ul>`;
    for(const it of day.items || []){
      out += `<li><strong>${it.time}:</strong> ${it.activity}</li>`;
    }
    out += `</ul></div>`;
  }

  out += `</div></div></div>`;
  resultArea.innerHTML = out;
}

function escapeHtml(s){ 
  return s.replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}
