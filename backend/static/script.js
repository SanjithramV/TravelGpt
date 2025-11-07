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
  try {
    const resp = await fetch("/api/itinerary", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({destination: dest, days: days, interests: interests})
    });
    const data = await resp.json();
    if(!data.ok){ throw new Error("No data"); }
    renderResult(data.generated);
  } catch(err){
    resultArea.innerHTML = `<div class="alert alert-danger">Failed to generate itinerary. See console for details.</div>`;
    console.error(err);
  }
});

function renderResult(generated){
  const resultArea = document.getElementById("resultArea");
  if(generated.source === "openai"){
    resultArea.innerHTML = `<div class="card"><div class="card-body"><pre>${escapeHtml(generated.text)}</pre></div></div>`;
    return;
  }
  // rule-based structure
  const meta = generated.meta || {};
  let out = `<div class="card"><div class="card-body">`;
  out += `<h5>${meta.destination} — ${meta.days} day(s)</h5>`;
  if(meta.weather_note){ out += `<p><strong>Weather:</strong> ${meta.weather_note}</p>`;}
  out += `<div class="list-group">`;
  for(const day of generated.itinerary){
    out += `<div class="list-group-item"><strong>Day ${day.day}</strong><ul>`;
    for(const it of day.items){
      out += `<li><strong>${it.time}:</strong> ${it.activity}</li>`;
    }
    out += `</ul></div>`;
  }
  out += `</div></div></div>`;
  resultArea.innerHTML = out;
}

function escapeHtml(s){ return s.replace(/[&<>"']/g, function(m){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'':'&#39;'}[m];}); }
