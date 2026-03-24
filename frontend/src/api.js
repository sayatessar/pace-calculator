const BASE = "/api";

/**
 * POST /calculate
 * @param {string} distance  - "5K" | "10K" | "HM" | "FM"
 * @param {string} finishTime - "HH:MM:SS"
 * @param {string} framework  - "1" | "2" | "3" | "4"
 * @returns {Promise<CalculateResponse>}
 */
export async function calculatePace(distance, finishTime, framework = "1") {
  const res = await fetch(`${BASE}/calculate`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({
      distance,
      finish_time: finishTime,
      framework,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed (${res.status})`);
  }

  return res.json();
}

/**
 * GET /meta
 * Returns all supported distances and frameworks.
 * @returns {Promise<MetaResponse>}
 */
export async function fetchMeta() {
  const res = await fetch(`${BASE}/meta`);
  if (!res.ok) throw new Error("Failed to load metadata");
  return res.json();
}
