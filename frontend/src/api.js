// Small fetch wrapper for the Flask API. Every write sends the X-CapSense header,
// which the backend requires as CSRF protection.

export class ApiError extends Error {
  constructor(message, { status, code, fallback, errors } = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.fallback = Boolean(fallback); // true when "use default mode instead" makes sense
    this.errors = errors || [];
  }
}

async function request(method, path, body) {
  const options = { method, credentials: "same-origin", headers: {} };
  if (method !== "GET") options.headers["X-CapSense"] = "1";
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  let response;
  try {
    response = await fetch(`/api${path}`, options);
  } catch {
    throw new ApiError("Can't reach the server. Is the backend running?", { status: 0, code: "network" });
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiError(data.error || `Request failed (${response.status})`, { status: response.status, ...data });
  }
  return data;
}

export const api = {
  get: (path) => request("GET", path),
  post: (path, body = {}) => request("POST", path, body),
  put: (path, body = {}) => request("PUT", path, body),
  patch: (path, body = {}) => request("PATCH", path, body),
  del: (path) => request("DELETE", path),
};

/** Download a file from the API (e.g. a DOCX export) and save it in the browser. */
export async function download(path) {
  const response = await fetch(`/api${path}`, { credentials: "same-origin" });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ApiError(data.error || "Download failed", { status: response.status, ...data });
  }
  const disposition = response.headers.get("Content-Disposition") || "";
  const filename = /filename="([^"]+)"/.exec(disposition)?.[1] || "download";
  const url = URL.createObjectURL(await response.blob());
  const link = Object.assign(document.createElement("a"), { href: url, download: filename });
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
