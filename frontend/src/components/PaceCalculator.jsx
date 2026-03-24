import { useState, useRef } from "react";
import { calculatePace } from "../api.js";

// ── Static config (mirrors backend) ──────────────────────────────────────────

const DISTANCES = {
  "5K":  { label: "5K",            subtitle: "5 kilometers" },
  "10K": { label: "10K",           subtitle: "10 kilometers" },
  "HM":  { label: "Half Marathon", subtitle: "21.1 km" },
  "FM":  { label: "Full Marathon", subtitle: "42.2 km" },
};

const FRAMEWORKS = {
  "1": { name: "General",      full: "General / Fixed Thresholds" },
  "2": { name: "Jack Daniels", full: "Jack Daniels' VDOT Zones" },
  "3": { name: "Heart Rate",   full: "Heart Rate Zone Model (5-Zone)" },
  "4": { name: "RPE",          full: "Rate of Perceived Exertion" },
};

const ZONE_COLORS = {
  5: "#ef4444",
  4: "#f97316",
  3: "#22c55e",
  2: "#3b82f6",
  1: "#6b7280",
};

// ── Sub-components ────────────────────────────────────────────────────────────

function NumberInput({ value, onChange, min = 0, max = 99, label }) {
  const handle = (e) => {
    const v = parseInt(e.target.value.replace(/\D/g, ""), 10);
    if (!isNaN(v)) onChange(Math.min(max, Math.max(min, v)));
  };
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
      <button onClick={() => onChange(Math.min(max, value + 1))} style={s.arrowBtn} aria-label={`Increase ${label}`}>▲</button>
      <input
        type="text"
        inputMode="numeric"
        value={String(value).padStart(2, "0")}
        onChange={handle}
        style={s.timeInput}
        aria-label={label}
      />
      <button onClick={() => onChange(Math.max(min, value - 1))} style={s.arrowBtn} aria-label={`Decrease ${label}`}>▼</button>
    </div>
  );
}

function StatCard({ label, value, unit, large }) {
  return (
    <div style={s.statCard}>
      <p style={s.statLabel}>{label}</p>
      <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
        <span style={{ ...s.statValue, fontSize: large ? 26 : 20 }}>{value}</span>
        <span style={s.statUnit}>{unit}</span>
      </div>
    </div>
  );
}

function ZoneBadge({ level, label }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
      <span style={{
        background: ZONE_COLORS[level],
        color: "#fff",
        fontSize: 12,
        fontWeight: 600,
        padding: "3px 10px",
        borderRadius: 20,
        whiteSpace: "nowrap",
      }}>
        Zone {level}
      </span>
      <span style={{ fontSize: 14, fontWeight: 500 }}>{label}</span>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function PaceCalculator() {
  const [distance,  setDistance]  = useState("HM");
  const [hours,     setHours]     = useState(1);
  const [minutes,   setMinutes]   = useState(45);
  const [secs,      setSecs]      = useState(0);
  const [framework, setFramework] = useState("1");
  const [result,    setResult]    = useState(null);
  const [error,     setError]     = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [animated,  setAnimated]  = useState(false);
  const resultRef = useRef(null);

  const handleCalculate = async () => {
    setError(null);
    setLoading(true);
    const finishTime = `${String(hours).padStart(2,"0")}:${String(minutes).padStart(2,"0")}:${String(secs).padStart(2,"0")}`;
    try {
      const data = await calculatePace(distance, finishTime, framework);
      setResult(data);
      setAnimated(false);
      setTimeout(() => setAnimated(true), 20);
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }), 80);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={s.page}>

      {/* Header */}
      <div style={{ marginBottom: "2rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
          <span style={{ fontSize: 22 }}>🏃</span>
          <h1 style={s.title}>Pace Calculator</h1>
        </div>
        <p style={s.subtitle}>Enter your target distance and finish time to estimate your required pace.</p>
      </div>

      {/* Distance */}
      <section style={{ marginBottom: "1.5rem" }}>
        <label style={s.sectionLabel}>Distance</label>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
          {Object.entries(DISTANCES).map(([key, d]) => (
            <button key={key} onClick={() => setDistance(key)} style={{
              ...s.distBtn,
              background:  distance === key ? "#1c1c1e"   : s.card.background,
              color:       distance === key ? "#fff"       : "inherit",
              border:      distance === key ? "1px solid #1c1c1e" : s.card.border,
            }}>
              <span style={{ fontSize: 14, fontWeight: 600 }}>{d.label}</span>
              <span style={{ fontSize: 11, opacity: 0.65, marginTop: 2 }}>{d.subtitle}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Time */}
      <section style={{ marginBottom: "1.5rem" }}>
        <label style={s.sectionLabel}>Target finish time</label>
        <div style={{ ...s.card, display: "flex", alignItems: "center", justifyContent: "center", gap: 0 }}>
          <NumberInput value={hours}   onChange={setHours}   max={23} label="Hours"   />
          <span style={s.timeSep}>:</span>
          <NumberInput value={minutes} onChange={setMinutes} max={59} label="Minutes" />
          <span style={s.timeSep}>:</span>
          <NumberInput value={secs}    onChange={setSecs}    max={59} label="Seconds" />
        </div>
        <p style={{ ...s.hint, textAlign: "center", marginTop: 6 }}>HH : MM : SS</p>
      </section>

      {/* Framework */}
      <section style={{ marginBottom: "1.5rem" }}>
        <label style={s.sectionLabel}>Effort zone framework</label>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 8 }}>
          {Object.entries(FRAMEWORKS).map(([key, fw]) => (
            <button key={key} onClick={() => setFramework(key)} style={{
              ...s.fwBtn,
              background: framework === key ? "#eff6ff" : s.card.background,
              border:     framework === key ? "1px solid #3b82f6" : s.card.border,
              color:      framework === key ? "#1d4ed8" : "inherit",
            }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>{fw.name}</span>
              <span style={{ fontSize: 11, opacity: 0.7, marginTop: 2 }}>{fw.full}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Error */}
      {error && (
        <div style={{ background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 10, padding: "10px 14px", marginBottom: "1rem", fontSize: 13, color: "#b91c1c" }}>
          {error}
        </div>
      )}

      {/* Calculate button */}
      <button onClick={handleCalculate} disabled={loading} style={{
        ...s.calcBtn,
        opacity: loading ? 0.7 : 1,
        cursor:  loading ? "not-allowed" : "pointer",
      }}>
        {loading ? "Calculating…" : "Calculate pace"}
      </button>

      {/* Results */}
      {result && (
        <div ref={resultRef} style={{
          opacity:   animated ? 1 : 0,
          transform: animated ? "translateY(0)" : "translateY(12px)",
          transition: "opacity 0.35s ease, transform 0.35s ease",
        }}>
          <div style={{ borderTop: "1px solid #e5e7eb", margin: "2rem 0 1.5rem" }} />

          <p style={{ ...s.hint, marginBottom: "1.25rem" }}>
            {result.distance_label} in {result.finish_time} · {result.zone.framework_name}
          </p>

          {/* Pace + speed cards */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: "1.25rem" }}>
            <StatCard label="Pace per km"   value={result.pace_fmt_km}              unit="/km"  large />
            <StatCard label="Pace per mile" value={result.pace_fmt_mile}            unit="/mi"  large />
            <StatCard label="Speed"         value={result.speed_kmh.toFixed(2)}     unit="km/h" />
            <StatCard label="Speed"         value={result.speed_mph.toFixed(2)}     unit="mph"  />
          </div>

          {/* Effort zone */}
          <div style={{ ...s.card, marginBottom: "1.25rem" }}>
            <p style={s.cardHeading}>Effort zone</p>
            <ZoneBadge level={result.zone.level} label={result.zone.label} />
            <div style={{ height: 6, background: "#f3f4f6", borderRadius: 3, overflow: "hidden" }}>
              <div style={{
                height: "100%",
                width: `${(result.zone.level / 5) * 100}%`,
                background: ZONE_COLORS[result.zone.level],
                borderRadius: 3,
                transition: "width 0.5s ease",
              }} />
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4, fontSize: 11, color: "#9ca3af" }}>
              <span>Recovery</span><span>Elite</span>
            </div>
          </div>

          {/* Splits */}
          <div style={{ ...s.card, marginBottom: "1.25rem" }}>
            <p style={s.cardHeading}>Estimated splits at this pace</p>
            {result.splits.map((split, i) => (
              <div key={split.label} style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: "9px 0",
                borderBottom: i < result.splits.length - 1 ? "1px solid #f3f4f6" : "none",
              }}>
                <span style={{ fontSize: 13, color: "#6b7280" }}>{split.label}</span>
                <span style={{ fontSize: 14, fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>{split.formatted}</span>
              </div>
            ))}
          </div>

          {/* All zones legend */}
          <div style={s.card}>
            <p style={s.cardHeading}>All zones · {FRAMEWORKS[framework].name}</p>
            {result.all_zones && result.all_zones.map((z, i) => (
              <div key={i} style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "7px 8px", borderRadius: 8, marginBottom: 2,
                background: z.is_current ? `${ZONE_COLORS[z.level]}18` : "transparent",
                border: z.is_current ? `1px solid ${ZONE_COLORS[z.level]}60` : "1px solid transparent",
              }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", flexShrink: 0, background: ZONE_COLORS[z.level] }} />
                <span style={{ fontSize: 13, fontWeight: z.is_current ? 600 : 400, flex: 1 }}>{z.label}</span>
                <span style={{ fontSize: 11, color: "#9ca3af", fontVariantNumeric: "tabular-nums" }}>{z.pace_range}</span>
                {z.is_current && (
                  <span style={{ fontSize: 10, background: ZONE_COLORS[z.level], color: "#fff", padding: "2px 6px", borderRadius: 10, fontWeight: 600 }}>you</span>
                )}
              </div>
            ))}
          </div>

        </div>
      )}
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const s = {
  page: {
    maxWidth: 600,
    margin: "0 auto",
    padding: "2rem 1rem 4rem",
    fontFamily: "system-ui, sans-serif",
  },
  title: {
    margin: 0,
    fontSize: 22,
    fontWeight: 700,
    letterSpacing: "-0.5px",
  },
  subtitle: {
    fontSize: 13,
    color: "#6b7280",
    lineHeight: 1.5,
    marginTop: 4,
  },
  sectionLabel: {
    display: "block",
    fontSize: 11,
    fontWeight: 700,
    color: "#9ca3af",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    marginBottom: 8,
  },
  card: {
    background: "#ffffff",
    border: "1px solid #e5e7eb",
    borderRadius: 12,
    padding: "1rem 1.25rem",
  },
  cardHeading: {
    fontSize: 11,
    fontWeight: 700,
    color: "#9ca3af",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    marginBottom: 12,
  },
  distBtn: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    padding: "10px 8px",
    borderRadius: 10,
    cursor: "pointer",
    transition: "all 0.15s",
    fontFamily: "system-ui, sans-serif",
    background: "#ffffff",
    border: "1px solid #e5e7eb",
  },
  fwBtn: {
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-start",
    padding: "10px 12px",
    borderRadius: 10,
    cursor: "pointer",
    transition: "all 0.15s",
    fontFamily: "system-ui, sans-serif",
    background: "#ffffff",
    border: "1px solid #e5e7eb",
    textAlign: "left",
  },
  timeInput: {
    width: 54,
    textAlign: "center",
    fontSize: 28,
    fontVariantNumeric: "tabular-nums",
    fontWeight: 600,
    background: "#f9fafb",
    border: "1px solid #e5e7eb",
    borderRadius: 8,
    color: "inherit",
    padding: "6px 0",
    outline: "none",
    fontFamily: "system-ui, sans-serif",
  },
  arrowBtn: {
    background: "none",
    border: "none",
    cursor: "pointer",
    color: "#9ca3af",
    fontSize: 10,
    padding: "2px 6px",
    borderRadius: 4,
    lineHeight: 1,
  },
  timeSep: {
    fontSize: 28,
    fontWeight: 300,
    color: "#9ca3af",
    padding: "0 2px",
    userSelect: "none",
    marginBottom: 2,
  },
  calcBtn: {
    width: "100%",
    padding: "14px",
    fontSize: 15,
    fontWeight: 600,
    fontFamily: "system-ui, sans-serif",
    background: "#1c1c1e",
    color: "#ffffff",
    border: "none",
    borderRadius: 10,
    marginBottom: "2rem",
    transition: "opacity 0.15s",
  },
  statCard: {
    background: "#f9fafb",
    border: "1px solid #e5e7eb",
    borderRadius: 10,
    padding: "0.75rem 1rem",
  },
  statLabel: {
    margin: "0 0 4px",
    fontSize: 12,
    color: "#6b7280",
  },
  statValue: {
    fontWeight: 700,
    fontVariantNumeric: "tabular-nums",
    letterSpacing: "-0.5px",
  },
  statUnit: {
    fontSize: 12,
    color: "#6b7280",
  },
  hint: {
    fontSize: 12,
    color: "#9ca3af",
  },
};
