function getBaseUrl(): string {
  let url = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  url = url.trim();
  if (url && !url.startsWith("http://") && !url.startsWith("https://")) {
    url = `https://${url}`;
  }
  return url.replace(/\/$/, "");
}

const BASE_URL = getBaseUrl();

async function fetchJson<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      next: { revalidate: 10 },
    });
    if (!res.ok) {
      throw new Error(`API Error: ${res.status} ${res.statusText}`);
    }
    return await res.json();
  } catch (error) {
    console.warn(`Failed fetching from ${url}:`, error);
    throw error;
  }
}

export const api = {
  getHealth: () => fetchJson<any>("/health"),
  getMetrics: () => fetchJson<any>("/metrics"),
  getDisclaimer: () => fetchJson<any>("/disclaimer"),
  
  getNews: (page = 1, pageSize = 20) => 
    fetchJson<any>(`/api/v1/news?page=${page}&page_size=${pageSize}`),
  refreshNews: () => 
    fetchJson<any>("/api/v1/news/refresh", { method: "POST" }),

  getSignals: (direction?: string, page = 1) => {
    const query = direction ? `&direction=${direction}` : "";
    return fetchJson<any>(`/api/v1/signals?page=${page}&page_size=20${query}`);
  },
  getTopSignals: () => fetchJson<any>("/api/v1/signals/top"),
  generateSignals: () => fetchJson<any>("/api/v1/signals/generate", { method: "POST" }),

  getStocks: () => fetchJson<any>("/api/v1/market/stocks"),
  getSectors: () => fetchJson<any>("/api/v1/market/sectors"),
  getMarketStatus: () => fetchJson<any>("/api/v1/market/status"),
  getMarketOverview: () => fetchJson<any>("/api/v1/market/overview"),
  getMarketQuote: (symbol: string) => fetchJson<any>(`/api/v1/market/quote/${symbol}`),
  getMarketIndicators: (symbol: string) => fetchJson<any>(`/api/v1/market/indicators/${symbol}`),
  refreshMarketSnapshot: (symbol: string) => fetchJson<any>(`/api/v1/market/snapshot/${symbol}`, { method: "POST" }),
  
  getPaperPositions: () => fetchJson<any>("/api/v1/paper-trading/positions"),
  getPaperTrades: () => fetchJson<any>("/api/v1/paper-trading/trades"),
  getPaperMetrics: () => fetchJson<any>("/api/v1/paper-trading/metrics"),
  executePaperTradeFromSignal: (signalId: number) => 
    fetchJson<any>(`/api/v1/paper-trading/execute-signal/${signalId}`, { method: "POST" }),
  closePaperPosition: (tradeId: number, exitPrice?: number) => 
    fetchJson<any>(`/api/v1/paper-trading/close/${tradeId}${exitPrice ? `?exit_price=${exitPrice}` : ""}`, { method: "POST" }),
  updatePaperPositions: () => 
    fetchJson<any>("/api/v1/paper-trading/update-positions", { method: "POST" }),
  
  getLatestPreMarketReport: () => fetchJson<any>("/api/v1/reports/pre-market/latest"),
  generatePreMarketReport: () => fetchJson<any>("/api/v1/reports/pre-market/generate", { method: "POST" }),
  
  getPredictionSummary: () => fetchJson<any>("/api/v1/performance/summary"),
  getPredictionEvaluations: (page = 1) => fetchJson<any>(`/api/v1/performance/predictions?page=${page}`),
  triggerEvaluation: (forceAll = false) => 
    fetchJson<any>(`/api/v1/performance/evaluate${forceAll ? "?force_all=true" : ""}`, { method: "POST" }),
  runBacktest: (symbols?: string, periodDays = 60) => {
    const q = symbols ? `&symbols=${symbols}` : "";
    return fetchJson<any>(`/api/v1/performance/backtest?period_days=${periodDays}${q}`, { method: "POST" });
  },
  
  getSettings: () => fetchJson<any>("/api/v1/settings"),
  updateWeights: (weights: any) => 
    fetchJson<any>("/api/v1/settings/weights", { method: "PUT", body: JSON.stringify(weights) }),
};
