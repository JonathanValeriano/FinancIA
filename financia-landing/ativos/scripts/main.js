let debounceTimer;
const BRAPI_TOKEN = '5Bqwnn1inhRd9pk4g5kVt3'; 
const GNEWS_API_KEY = '8d76307fb764d497df65b11f4dafcf95'; 
const NEWSAPI_KEY = 'pub_8175177f57f2b8b4387a8ff9cceabee1fb4c7';

async function fetchStockData(symbol) {
  const resultDiv = document.getElementById("result");
  const loading = document.getElementById("loading");

  try {
    // 1. Busca dados da cotação e fundamentos
    const stock = await fetchStockFundamentals(symbol);
    if (!stock) {
      resultDiv.innerHTML = "<p class='text-red-400'>❌ Ativo não encontrado.</p>";
      return;
    }

    // 2. Processa os dados do ativo
    const { name, price, change, volume, sector } = formatStockData(stock);
    const indicatorsHtml = buildIndicatorsHtml(stock.fundamental);
    // 3. Busca notícias com fallback entre APIs
    const newsHtml = await fetchNewsWithFallback(name, sector);

    // 4. Monta o HTML final
    resultDiv.innerHTML = buildFinalHtml(name, stock.symbol, price, change, sector, volume, indicatorsHtml, newsHtml);

  } catch (error) {
    resultDiv.innerHTML = `
      <div class="p-4 bg-red-900/50 rounded-lg border border-red-700">
        <p class="text-red-300">⚠️ Erro ao buscar dados do ativo</p>
        <p class="text-sm text-red-400 mt-1">${error.message}</p>
      </div>
    `;
    console.error("Erro completo:", error);
  } finally {
    loading.classList.add("hidden");
  }
}

// Busca dados fundamentais do ativo
async function fetchStockFundamentals(symbol) {
  try {
    let url = `https://brapi.dev/api/quote/${symbol}?token=${BRAPI_TOKEN}&range=1d&interval=1d`;
    if (!symbol.toUpperCase().startsWith('MXRF')) {
      url += '&fundamental=true';
    }
    const response = await fetch(url);

    if (!response.ok) throw new Error(`Erro ${response.status} na API`);

    const data = await response.json();
    return data.results?.[0];
  } catch (error) {
    console.error("Erro ao buscar fundamentos:", error);
    return null;
  }
}

// Formata os dados básicos do ativo
function formatStockData(stock) {
  return {
    name: stock.longName || stock.shortName || stock.symbol,
    price: formatNumber(stock.regularMarketPrice, 2, 'R$ '),
    change: formatNumber(stock.regularMarketChangePercent, 2, '', '%'),
    volume: formatNumber(stock.regularMarketVolume, 0),
    sector: stock.sector || "Não informado"
  };
}

// Constrói o HTML dos indicadores
function buildIndicatorsHtml(fundamentals) {
  if (!fundamentals) {
    return '<p class="text-slate-400 mt-4">Indicadores não disponíveis para este ativo.</p>';
  }

  const indicators = [
    { name: 'P/L', value: fundamentals.priceToEarnings, format: 'number' },
    { name: 'DY', value: fundamentals.dividendYield, format: 'percent' },
    { name: 'ROE', value: fundamentals.returnOnEquity, format: 'percent' },
    { name: 'P/VP', value: fundamentals.priceToBook, format: 'number' },
    { name: 'VPA', value: fundamentals.bookValuePerShare, format: 'currency' },
    { name: 'LPA', value: fundamentals.earningsPerShare, format: 'currency' },
    { name: 'EV/EBITDA', value: fundamentals.enterpriseValueOverEBITDA, format: 'number' },
    { name: 'Margem Líquida', value: fundamentals.netProfitMargin, format: 'percent' },
    // Adicione outros indicadores que você queira exibir aqui
  ].filter(indicator => indicator.value !== null && indicator.value !== undefined);

  if (indicators.length === 0) {
    return '<p class="text-slate-400 mt-4">Nenhum indicador fundamental disponível.</p>';
  }

  return `
    <div class="mt-4">
      <h3 class="text-lg font-bold text-cyan-400 mb-2">📊 Indicadores Fundamentais</h3>
      <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
        ${indicators.map(ind => `
          <div class="bg-slate-700 p-3 rounded-lg">
            <span class="block text-sm text-slate-300">${ind.name}</span>
            <span class="text-teal-300 font-bold">${formatIndicator(ind.value, ind.format)}</span>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

// Busca notícias com fallback entre múltiplas APIs
async function fetchNewsWithFallback(assetName, sector) {
  const searchTermsSpecific = [
    assetName,
    `${assetName} ações`,
    `${assetName} notícias`,
    sector !== "Não informado" ? `${sector} notícias` : null,
  ].filter(term => term);

  let specificNews = [];
  for (const term of searchTermsSpecific) {
    try {
      // 1. Tenta GNews primeiro
      const gnews = await fetchGNews(term);
      specificNews = specificNews.concat(gnews.map(news => ({ ...news, relevance: 'specific' })));

      // 2. Se falhar, tenta NewsAPI
      const newsapi = await fetchNewsAPI(term);
      specificNews = specificNews.concat(newsapi.map(news => ({ ...news, relevance: 'specific' })));

    } catch (error) {
      console.warn(`Erro ao buscar notícias para "${term}":`, error);
    }
  }

  let generalNews = [];
  const generalTerms = ["mercado financeiro", "investimentos"];
  for (const term of generalTerms) {
    try {
      const gnews = await fetchGNews(term);
      generalNews = generalNews.concat(gnews.map(news => ({ ...news, relevance: 'general' })));

      const newsapi = await fetchNewsAPI(term);
      generalNews = generalNews.concat(newsapi.map(news => ({ ...news, relevance: 'general' })));

    } catch (error) {
      console.warn(`Erro ao buscar notícias gerais para "${term}":`, error);
    }
  }

  const allNews = [...specificNews, ...generalNews];
  const uniqueNews = allNews.filter((news, index, self) =>
    index === self.findIndex((t) => (
      t.title === news.title && t.url === news.url
    ))
  );

  const specificNewsCount = specificNews.length;
  const generalNewsCount = generalNews.length;

  let newsHtml = "";

  if (specificNewsCount > 0) {
    newsHtml += createNewsHtml(uniqueNews.filter(news => news.relevance === 'specific'), `📰 Notícias sobre ${assetName}`);
  }

  if (generalNewsCount > 0) {
    const generalTitle = specificNewsCount > 0 ? `📰 Também sobre o Mercado Financeiro` : `📰 Notícias sobre o Mercado Financeiro`;
    const generalNewsToShow = uniqueNews.filter(news => news.relevance === 'general').slice(0, 3); // Limita as notícias gerais
    if (generalNewsToShow.length > 0) {
      newsHtml += `<div class="mt-4"><p class="text-slate-400">${specificNewsCount === 0 ? '⚠️ Nenhuma notícia específica sobre o ativo encontrada.' : ''}</p>` + createNewsHtml(generalNewsToShow, generalTitle) + `</div>`;
    } else if (specificNewsCount === 0) {
      newsHtml = `<p class="text-slate-400 mt-4">⚠️ Nenhuma notícia relevante encontrada para ${assetName} ou sobre o mercado financeiro.</p>`;
    }
  } else if (specificNewsCount === 0) {
    newsHtml = `<p class="text-slate-400 mt-4">⚠️ Nenhuma notícia relevante encontrada para ${assetName}.</p>`;
  }

  return newsHtml;
}

// Busca notícias no GNews
async function fetchGNews(query) {
  try {
    const url = `https://gnews.io/api/v4/search?q=${encodeURIComponent(query)}&lang=pt&max=3&apikey=${GNEWS_API_KEY}`;
    const response = await fetch(url);

    if (!response.ok) throw new Error(`GNews error: ${response.status}`);

    const data = await response.json();
    return data.articles?.map(article => ({
      title: article.title,
      description: article.description,
      url: article.url,
      source: 'GNews'
    })) || [];
  } catch (error) {
    console.error("Erro no GNews:", error);
    return [];
  }
}

// Busca notícias no NewsAPI
async function fetchNewsAPI(query) {
  try {
    const url = `https://newsapi.org/v2/everything?q=${encodeURIComponent(query)}&language=pt&pageSize=3&apiKey=${NEWSAPI_KEY}`;
    const response = await fetch(url);

    if (!response.ok) throw new Error(`NewsAPI error: ${response.status}`);

    const data = await response.json();
    return data.articles?.map(article => ({
      title: article.title,
      description: article.description,
      url: article.url,
      source: 'NewsAPI'
    })) || [];
  } catch (error) {
    console.error("Erro no NewsAPI:", error);
    return [];
  }
}

// Cria HTML para as notícias
function createNewsHtml(articles, title) {
  return `
    <div class="mt-6">
      <h3 class="text-xl font-bold text-cyan-400 mb-3">${title}</h3>
      <div class="space-y-4">
        ${articles.slice(0, 3).map(article => `
          <div class="p-4 bg-slate-700 rounded-lg hover:bg-slate-600 transition-colors">
            <h4 class="font-semibold text-teal-300">${article.title || 'Sem título'}</h4>
            ${article.description ? `<p class="text-sm text-slate-300 mt-1">${article.description}</p>` : ''}
            <div class="flex justify-between items-center mt-2">
              ${article.url ? `<a href="${article.url}" target="_blank" class="text-sm text-cyan-400 hover:underline">
                Ler mais <i class="fas fa-external-link-alt ml-1"></i>
              </a>` : ''}
              <span class="text-xs text-slate-400">${article.source || ''}</span>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

// Funções auxiliares de formatação
function formatNumber(value, decimals = 2, prefix = '', suffix = '') {
  if (value === undefined || value === null || isNaN(value)) return 'N/A';
  const number = typeof value === 'string' ? parseFloat(value) : value;
  return prefix + number.toFixed(decimals).replace('.', ',') + suffix;
}

function formatIndicator(value, type = 'number') {
  if (value === undefined || value === null) return 'N/A';

  switch(type) {
    case 'percent':
      return formatNumber(value * 100, 2, '', '%'); // Converte decimal para porcentagem
    case 'currency':
      return formatNumber(value, 2, 'R$ ');
    default:
      return formatNumber(value, 2);
  }
}

// Monta o HTML final
function buildFinalHtml(name, symbol, price, change, sector, volume, indicatorsHtml, newsHtml) {
  return `
    <div class="p-6 bg-slate-800 rounded-lg shadow-lg border border-slate-700 space-y-4">
      <div>
        <h2 class="text-2xl font-bold text-cyan-400">${name} (${symbol})</h2>
        <ul class="mt-2 text-lg text-slate-200 space-y-1">
          <li><strong>💰 Preço atual:</strong> ${price}</li>
          <li><strong>📈 Variação diária:</strong> ${change}</li>
          <li><strong>🏭 Setor:</strong> ${sector}</li>
          <li><strong>📊 Volume:</strong> ${volume}</li>
        </ul>
      </div>
      ${indicatorsHtml}
      ${newsHtml}
    </div>
  `;
}

// Configuração do debounce
document.getElementById("searchInput").addEventListener("input", function() {
  const symbol = this.value.trim().toUpperCase();
  const resultDiv = document.getElementById("result");
  const loading = document.getElementById("loading");

  clearTimeout(debounceTimer);

  if (!symbol) {
    resultDiv.innerHTML = "";
    loading.classList.add("hidden");
    return;
  }

  loading.classList.remove("hidden");
  resultDiv.innerHTML = "";

  debounceTimer = setTimeout(() => fetchStockData(symbol), 500);
});