import { useState, useEffect, useCallback } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

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

export default function Dashboard() {
  const [apiKey, setApiKey] = useState("");
  const [connected, setConnected] = useState(false);
  const [summary, setSummary] = useState<GatewaySummary | null>(null);
  const [servers, setServers] = useState<McpServer[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Load saved API key from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("popkit_api_key");
    if (saved) {
      setApiKey(saved);
    }
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

      if (!summaryRes.ok || !serversRes.ok) {
        throw new Error("Failed to fetch data. Check your API key.");
      }

      const summaryData = await summaryRes.json();
      const serversData = await serversRes.json();

      setSummary(summaryData);
      setServers(serversData.servers || []);
      setConnected(true);
      localStorage.setItem("popkit_api_key", key);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Connection failed");
      setConnected(false);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleConnect = () => {
    if (apiKey.trim()) {
      fetchData(apiKey.trim());
    }
  };

  const handleDisconnect = () => {
    setConnected(false);
    setSummary(null);
    setServers([]);
    localStorage.removeItem("popkit_api_key");
    setApiKey("");
  };

  // Auto-connect if key is saved
  useEffect(() => {
    if (apiKey && !connected) {
      fetchData(apiKey);
    }
  }, []);

  if (!connected) {
    return (
      <div style={styles.container}>
        <div style={styles.loginCard}>
          <h2 style={styles.loginTitle}>PopKit Observatory</h2>
          <p style={styles.loginDesc}>
            Connect with your PopKit Cloud API key to view gateway analytics.
          </p>
          <div style={styles.inputGroup}>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleConnect()}
              placeholder="pk_live_..."
              style={styles.input}
            />
            <button
              onClick={handleConnect}
              disabled={loading || !apiKey.trim()}
              style={styles.button}
            >
              {loading ? "Connecting..." : "Connect"}
            </button>
          </div>
          {error && <p style={styles.error}>{error}</p>}
          <p style={styles.hint}>
            Don't have a key? <a href="/getting-started/installation/">Get started here</a>
          </p>
        </div>
      </div>
    );
  }

  const chartData = (summary?.daily || [])
    .slice()
    .reverse()
    .map((d) => ({
      date: d.date.slice(5), // "03-25" format
      success: d.success,
      failure: d.failure,
    }));

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>PopKit Observatory</h2>
        <button onClick={handleDisconnect} style={styles.disconnectBtn}>
          Disconnect
        </button>
      </div>

      {/* Stats Cards */}
      <div style={styles.statsGrid}>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{summary?.totals.calls ?? 0}</div>
          <div style={styles.statLabel}>Total Calls (7d)</div>
        </div>
        <div style={styles.statCard}>
          <div
            style={{
              ...styles.statValue,
              color: (summary?.totals.success_rate ?? 100) >= 90 ? "#10b981" : "#f59e0b",
            }}
          >
            {summary?.totals.success_rate ?? 100}%
          </div>
          <div style={styles.statLabel}>Success Rate</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{servers.length}</div>
          <div style={styles.statLabel}>MCP Servers</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{summary?.totals.failure ?? 0}</div>
          <div style={styles.statLabel}>Failures (7d)</div>
        </div>
      </div>

      {/* Chart */}
      {chartData.length > 0 && (
        <div style={styles.chartContainer}>
          <h3 style={styles.sectionTitle}>Gateway Calls (Last 7 Days)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} />
              <Tooltip
                contentStyle={{
                  background: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  color: "#f8fafc",
                }}
              />
              <Bar dataKey="success" fill="#10b981" name="Success" radius={[4, 4, 0, 0]} />
              <Bar dataKey="failure" fill="#ef4444" name="Failure" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Server List */}
      <div style={styles.serversSection}>
        <h3 style={styles.sectionTitle}>Registered MCP Servers ({servers.length})</h3>
        {servers.length === 0 ? (
          <p style={styles.emptyState}>
            No MCP servers registered yet. Use the cloud API to register backend servers.
          </p>
        ) : (
          <div style={styles.serverGrid}>
            {servers.map((s) => (
              <div key={s.id} style={styles.serverCard}>
                <div style={styles.serverName}>{s.name}</div>
                <div style={styles.serverDesc}>{s.description || "No description"}</div>
                <div style={styles.serverTools}>
                  {(s.tools || []).map((t) => (
                    <span key={t} style={styles.toolBadge}>
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

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: "900px",
    margin: "0 auto",
    padding: "1rem 0",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "1.5rem",
  },
  title: {
    fontSize: "1.5rem",
    fontWeight: 700,
    margin: 0,
  },
  disconnectBtn: {
    background: "transparent",
    border: "1px solid #475569",
    color: "#94a3b8",
    padding: "0.375rem 0.75rem",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "0.875rem",
  },
  loginCard: {
    maxWidth: "400px",
    margin: "2rem auto",
    padding: "2rem",
    background: "#1e293b",
    borderRadius: "12px",
    border: "1px solid #334155",
    textAlign: "center" as const,
  },
  loginTitle: {
    fontSize: "1.5rem",
    fontWeight: 700,
    marginBottom: "0.5rem",
  },
  loginDesc: {
    color: "#94a3b8",
    marginBottom: "1.5rem",
    fontSize: "0.9rem",
  },
  inputGroup: {
    display: "flex",
    gap: "0.5rem",
    marginBottom: "1rem",
  },
  input: {
    flex: 1,
    padding: "0.5rem 0.75rem",
    background: "#0f172a",
    border: "1px solid #334155",
    borderRadius: "6px",
    color: "#f8fafc",
    fontSize: "0.875rem",
  },
  button: {
    padding: "0.5rem 1rem",
    background: "#0ea5e9",
    color: "#fff",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontWeight: 600,
    fontSize: "0.875rem",
  },
  error: {
    color: "#ef4444",
    fontSize: "0.875rem",
    marginTop: "0.5rem",
  },
  hint: {
    color: "#64748b",
    fontSize: "0.8rem",
    marginTop: "1rem",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: "1rem",
    marginBottom: "1.5rem",
  },
  statCard: {
    background: "#1e293b",
    border: "1px solid #334155",
    borderRadius: "10px",
    padding: "1.25rem",
    textAlign: "center" as const,
  },
  statValue: {
    fontSize: "2rem",
    fontWeight: 800,
    color: "#0ea5e9",
    lineHeight: 1.1,
  },
  statLabel: {
    fontSize: "0.8rem",
    color: "#94a3b8",
    marginTop: "0.25rem",
  },
  chartContainer: {
    background: "#1e293b",
    border: "1px solid #334155",
    borderRadius: "10px",
    padding: "1.25rem",
    marginBottom: "1.5rem",
  },
  sectionTitle: {
    fontSize: "1rem",
    fontWeight: 600,
    marginBottom: "1rem",
    marginTop: 0,
  },
  serversSection: {
    background: "#1e293b",
    border: "1px solid #334155",
    borderRadius: "10px",
    padding: "1.25rem",
  },
  emptyState: {
    color: "#64748b",
    textAlign: "center" as const,
    padding: "2rem 0",
  },
  serverGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))",
    gap: "0.75rem",
  },
  serverCard: {
    background: "#0f172a",
    border: "1px solid #334155",
    borderRadius: "8px",
    padding: "1rem",
  },
  serverName: {
    fontWeight: 700,
    fontSize: "1rem",
    marginBottom: "0.25rem",
  },
  serverDesc: {
    color: "#94a3b8",
    fontSize: "0.85rem",
    marginBottom: "0.5rem",
  },
  serverTools: {
    display: "flex",
    flexWrap: "wrap" as const,
    gap: "0.25rem",
  },
  toolBadge: {
    background: "#334155",
    color: "#94a3b8",
    fontSize: "0.7rem",
    padding: "0.125rem 0.5rem",
    borderRadius: "999px",
  },
};
