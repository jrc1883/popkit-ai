import { useState, useEffect, useCallback } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface DailyData {
  date: string;
  total_calls: number;
  success: number;
  failure: number;
}

interface GatewaySummary {
  period: { days: number };
  totals: {
    calls: number;
    success: number;
    failure: number;
    success_rate: number;
  };
  daily: DailyData[];
}

interface McpServer {
  id: string;
  name: string;
  description: string;
  tools: string[];
  enabled: boolean;
  callCount: number;
}

const API_URL = "https://api.thehouseofdeals.com";

const accentColors = ["#0ea5e9", "#10b981", "#f97316", "#a855f7"];

export default function Dashboard() {
  const [apiKey, setApiKey] = useState("");
  const [connected, setConnected] = useState(false);
  const [summary, setSummary] = useState<GatewaySummary | null>(null);
  const [servers, setServers] = useState<McpServer[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("popkit_api_key");
    if (saved) setApiKey(saved);
  }, []);

  const fetchData = useCallback(async (key: string) => {
    setLoading(true);
    setError("");
    try {
      const headers = {
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
      };
      const [summaryRes, serversRes] = await Promise.all([
        fetch(`${API_URL}/v1/analytics/gateway/summary?days=7`, { headers }),
        fetch(`${API_URL}/v1/mcp/servers`, { headers }),
      ]);
      if (!summaryRes.ok || !serversRes.ok)
        throw new Error("Failed to fetch data. Check your API key.");
      setSummary(await summaryRes.json());
      setServers((await serversRes.json()).servers || []);
      setConnected(true);
      localStorage.setItem("popkit_api_key", key);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Connection failed");
      setConnected(false);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleConnect = () => apiKey.trim() && fetchData(apiKey.trim());

  const handleDisconnect = () => {
    setConnected(false);
    setSummary(null);
    setServers([]);
    localStorage.removeItem("popkit_api_key");
    setApiKey("");
  };

  useEffect(() => {
    if (apiKey && !connected) fetchData(apiKey);
  }, []);

  // ── Login Screen ──
  if (!connected) {
    return (
      <div className="pk-dash">
        <div className="pk-login">
          <div className="pk-login-icon">
            <svg viewBox="0 0 120 120" width="48" height="48" fill="none">
              <circle cx="60" cy="60" r="14" fill="#0ea5e9" />
              <circle cx="60" cy="20" r="8" fill="#0ea5e9" opacity="0.8" />
              <circle cx="94.6" cy="40" r="8" fill="#0ea5e9" opacity="0.7" />
              <circle cx="94.6" cy="80" r="8" fill="#0ea5e9" opacity="0.6" />
              <circle cx="60" cy="100" r="8" fill="#0ea5e9" opacity="0.7" />
              <circle cx="25.4" cy="80" r="8" fill="#0ea5e9" opacity="0.8" />
              <circle cx="25.4" cy="40" r="8" fill="#0ea5e9" opacity="0.6" />
              <line
                x1="60"
                y1="46"
                x2="60"
                y2="28"
                stroke="#0ea5e9"
                strokeWidth="2.5"
                opacity="0.5"
              />
              <line
                x1="72"
                y1="53"
                x2="87"
                y2="44"
                stroke="#0ea5e9"
                strokeWidth="2.5"
                opacity="0.5"
              />
              <line
                x1="72"
                y1="67"
                x2="87"
                y2="76"
                stroke="#0ea5e9"
                strokeWidth="2.5"
                opacity="0.5"
              />
              <line
                x1="60"
                y1="74"
                x2="60"
                y2="92"
                stroke="#0ea5e9"
                strokeWidth="2.5"
                opacity="0.5"
              />
              <line
                x1="48"
                y1="67"
                x2="33"
                y2="76"
                stroke="#0ea5e9"
                strokeWidth="2.5"
                opacity="0.5"
              />
              <line
                x1="48"
                y1="53"
                x2="33"
                y2="44"
                stroke="#0ea5e9"
                strokeWidth="2.5"
                opacity="0.5"
              />
            </svg>
          </div>
          <h2 className="pk-login-title">PopKit Observatory</h2>
          <p className="pk-login-desc">
            Connect with your PopKit Cloud API key to view gateway analytics.
          </p>
          <div className="pk-login-form">
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleConnect()}
              placeholder="pk_live_..."
              className="pk-input"
            />
            <button
              onClick={handleConnect}
              disabled={loading || !apiKey.trim()}
              className="pk-btn-primary"
            >
              {loading ? "Connecting..." : "Connect"}
            </button>
          </div>
          {error && <p className="pk-error">{error}</p>}
          <p className="pk-hint">
            Don't have a key? <a href="/getting-started/installation/">Get started here</a>
          </p>
        </div>
      </div>
    );
  }

  // ── Dashboard ──
  const chartData = (summary?.daily || [])
    .slice()
    .reverse()
    .map((d) => ({
      date: d.date.slice(5),
      Success: d.success,
      Failure: d.failure,
    }));

  const rate = summary?.totals.success_rate ?? 100;

  return (
    <div className="pk-dash">
      <div className="pk-header">
        <div>
          <h2 className="pk-title">PopKit Observatory</h2>
          <p className="pk-subtitle">MCP Gateway Analytics</p>
        </div>
        <button onClick={handleDisconnect} className="pk-btn-ghost">
          Disconnect
        </button>
      </div>

      {/* Stats */}
      <div className="pk-stats">
        <div className="pk-stat" style={{ borderLeftColor: "#0ea5e9" }}>
          <div className="pk-stat-value" style={{ color: "#0ea5e9" }}>
            {summary?.totals.calls ?? 0}
          </div>
          <div className="pk-stat-label">Total Calls (7d)</div>
        </div>
        <div
          className="pk-stat"
          style={{ borderLeftColor: rate >= 90 ? "#10b981" : rate >= 70 ? "#f59e0b" : "#ef4444" }}
        >
          <div
            className="pk-stat-value"
            style={{ color: rate >= 90 ? "#10b981" : rate >= 70 ? "#f59e0b" : "#ef4444" }}
          >
            {rate}%
          </div>
          <div className="pk-stat-label">Success Rate</div>
        </div>
        <div className="pk-stat" style={{ borderLeftColor: "#a855f7" }}>
          <div className="pk-stat-value" style={{ color: "#a855f7" }}>
            {servers.length}
          </div>
          <div className="pk-stat-label">MCP Servers</div>
        </div>
        <div className="pk-stat" style={{ borderLeftColor: "#ef4444" }}>
          <div
            className="pk-stat-value"
            style={{ color: summary?.totals.failure ? "#ef4444" : "#64748b" }}
          >
            {summary?.totals.failure ?? 0}
          </div>
          <div className="pk-stat-label">Failures (7d)</div>
        </div>
      </div>

      {/* Chart */}
      {chartData.length > 0 && (
        <div className="pk-card">
          <h3 className="pk-card-title">Gateway Calls — Last 7 Days</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData} barGap={2}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--pk-border)" />
              <XAxis dataKey="date" stroke="var(--pk-text-muted)" fontSize={12} />
              <YAxis stroke="var(--pk-text-muted)" fontSize={12} allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  background: "var(--pk-card-bg)",
                  border: "1px solid var(--pk-border)",
                  borderRadius: "8px",
                  color: "var(--pk-text)",
                  fontSize: "0.85rem",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "0.8rem" }} />
              <Bar dataKey="Success" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Failure" fill="#ef4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Servers */}
      <div className="pk-card">
        <h3 className="pk-card-title">Registered MCP Servers ({servers.length})</h3>
        {servers.length === 0 ? (
          <p className="pk-empty">
            No MCP servers registered yet. Use the cloud API to register backend servers.
          </p>
        ) : (
          <div className="pk-servers">
            {servers.map((s, i) => (
              <div
                key={s.id}
                className="pk-server"
                style={{ borderLeftColor: accentColors[i % accentColors.length] }}
              >
                <div className="pk-server-header">
                  <span className="pk-server-name">{s.name}</span>
                  <span className={`pk-server-status ${s.enabled ? "enabled" : "disabled"}`}>
                    {s.enabled ? "active" : "disabled"}
                  </span>
                </div>
                <div className="pk-server-desc">{s.description || "No description"}</div>
                <div className="pk-tools">
                  {(s.tools || []).map((t) => (
                    <span key={t} className="pk-tool">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
