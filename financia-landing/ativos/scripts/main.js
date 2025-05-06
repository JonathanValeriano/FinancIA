const apiKey = "49ac59d6a8514448a96622339744bb32";

document.getElementById("searchInput").addEventListener("change", async function () {
  const symbol = this.value.trim().toUpperCase();
  const resultDiv = document.getElementById("result");
  resultDiv.innerHTML = "🔄 Buscando dados...";

  try {
    const url = `https://api.twelvedata.com/quote?symbol=${symbol}.SA&apikey=${apiKey}`;
    const response = await fetch(url);
    const data = await response.json();

    if (data.code || !data.symbol) {
      resultDiv.innerHTML = "<p class='text-red-400'>❌ Ativo não encontrado ou erro na API.</p>";
      return;
    }

    resultDiv.innerHTML = `
      <div class="bg-slate-800 p-6 rounded-lg shadow border border-slate-700">
        <h2 class="text-xl font-bold text-cyan-400 mb-2">${data.name} (${data.symbol})</h2>
        <p><strong>Preço:</strong> R$ ${parseFloat(data.close).toFixed(2)}</p>
        <p><strong>Setor:</strong> ${data.exchange || "Não informado"}</p>
        <p><strong>Volume:</strong> ${data.volume || "N/A"}</p>
        <p><strong>Variação diária:</strong> ${data.percent_change || "N/A"}%</p>
      </div>
    `;
  } catch (error) {
    resultDiv.innerHTML = "<p class='text-red-500'>⚠️ Erro ao buscar dados do ativo.</p>";
    console.error(error);
  }
});
