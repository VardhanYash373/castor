"""Stage 5 - Flask web UI: /sign and /verify endpoints."""

import os
import uuid
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")

UPLOAD_FOLDER = "/tmp/castor_uploads"
SIGNED_FOLDER = "/tmp/castor_signed"
ALLOWED_EXTENSIONS = {"jpg", "jpeg"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SIGNED_FOLDER, exist_ok=True)

PRIVATE_KEY = os.path.abspath("keys/private.pem")
PUBLIC_KEY  = os.path.abspath("keys/public.pem")


def allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Castor — Chain-of-Trust</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #111111; --surface: #1c1c1c; --border: #2a2a2a;
      --orange: #e8611a; --orange-d: #c44e10;
      --white: #f0f0f0; --muted: #888888;
      --green: #2ecc71; --red: #e74c3c;
      --font: "Inter", "Segoe UI", system-ui, sans-serif;
    }
    body { background: var(--bg); color: var(--white); font-family: var(--font); min-height: 100vh; display: flex; flex-direction: column; }

    header { border-bottom: 1px solid var(--border); padding: 1.25rem 2rem; display: flex; align-items: center; gap: 0.75rem; }
    .logo-dot { width: 10px; height: 10px; background: var(--orange); border-radius: 50%; }
    header h1 { font-size: 1rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; }
    header span { color: var(--muted); font-size: 0.8rem; margin-left: auto; }

    main {
      flex: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 1px;
      background: var(--border); max-width: 1100px; width: calc(100% - 4rem);
      margin: 2.5rem auto; border: 1px solid var(--border); border-radius: 6px; overflow: hidden;
    }
    .panel { background: var(--surface); padding: 2rem; display: flex; flex-direction: column; gap: 1.25rem; }

    .panel-title {
      display: flex; align-items: center; gap: 0.6rem;
      font-size: 0.7rem; font-weight: 700; letter-spacing: 0.12em;
      text-transform: uppercase; color: var(--orange);
    }
    .panel-title::before { content: ''; display: block; width: 3px; height: 14px; background: var(--orange); border-radius: 2px; }

    h2 { font-size: 1.4rem; font-weight: 700; }
    p  { color: var(--muted); font-size: 0.875rem; line-height: 1.6; }

    .drop-zone {
      border: 1.5px dashed var(--border); border-radius: 6px; padding: 2rem;
      text-align: center; cursor: pointer; transition: border-color 0.2s, background 0.2s; position: relative;
    }
    .drop-zone:hover   { border-color: var(--orange); background: rgba(232,97,26,0.04); }
    .drop-zone.over    { border-color: var(--orange); background: rgba(232,97,26,0.08); }
    .drop-zone input   { position: absolute; inset: 0; opacity: 0; cursor: pointer; width: 100%; height: 100%; }
    .drop-zone .icon   { font-size: 1.75rem; margin-bottom: 0.5rem; }
    .drop-zone .hint   { font-size: 0.85rem; color: var(--muted); }
    .drop-zone .hint strong { color: var(--orange); }
    .drop-zone .fname  { font-size: 0.8rem; color: var(--white); margin-top: 0.5rem; min-height: 1.2em; }

    button {
      background: var(--orange); color: #fff; border: none; border-radius: 4px;
      padding: 0.75rem 1.5rem; font-size: 0.875rem; font-weight: 600;
      cursor: pointer; transition: background 0.2s; letter-spacing: 0.03em;
    }
    button:hover    { background: var(--orange-d); }
    button:disabled { background: var(--border); color: var(--muted); cursor: not-allowed; }

    .result { border-radius: 4px; padding: 1rem 1.25rem; font-size: 0.82rem; display: none; }
    .result.show     { display: block; }
    .result.success  { background: rgba(232,97,26,0.1);  border: 1px solid rgba(232,97,26,0.3); }
    .result.valid    { background: rgba(46,204,113,0.1); border: 1px solid rgba(46,204,113,0.3); }
    .result.tampered { background: rgba(231,76,60,0.1);  border: 1px solid rgba(231,76,60,0.3); }
    .result.error    { background: rgba(231,76,60,0.1);  border: 1px solid rgba(231,76,60,0.3); }

    .status-line { font-weight: 700; font-size: 0.95rem; margin-bottom: 0.4rem; }
    .meta { color: var(--muted); margin-top: 0.4rem; word-break: break-all; }
    .meta span { color: var(--white); }

    .dl { display: inline-block; margin-top: 0.75rem; padding: 0.5rem 1rem; background: var(--orange); color: #fff; border-radius: 4px; font-size: 0.8rem; font-weight: 600; text-decoration: none; }
    .dl:hover { background: var(--orange-d); }

    footer { text-align: center; padding: 1.5rem; color: var(--muted); font-size: 0.75rem; border-top: 1px solid var(--border); }

    @media (max-width: 700px) { main { grid-template-columns: 1fr; width: calc(100% - 2rem); margin: 1rem auto; } }
  </style>
</head>
<body>

<header>
  <div class="logo-dot"></div>
  <h1>Castor</h1>
  <span>Cryptographic Image Provenance &amp; Tamper Detection</span>
</header>

<main>
  <div class="panel">
    <div class="panel-title">Sign</div>
    <h2>Sign an Image</h2>
    <p>Embeds a cryptographic manifest into the JPEG — locking pixel hash, timestamp, and ECDSA signature into XMP metadata.</p>
    <div class="drop-zone" id="sZone">
      <input type="file" id="sFile" accept=".jpg,.jpeg">
      <div class="icon">&#128274;</div>
      <div class="hint"><strong>Choose a JPEG</strong> or drag it here</div>
      <div class="fname" id="sFname"></div>
    </div>
    <button id="sBtn" disabled>Sign &amp; Embed Manifest</button>
    <div class="result" id="sResult"></div>
  </div>

  <div class="panel">
    <div class="panel-title">Verify</div>
    <h2>Verify an Image</h2>
    <p>Re-hashes pixel data and checks the ECDSA signature. Any pixel-level alteration triggers an immediate tamper alert.</p>
    <div class="drop-zone" id="vZone">
      <input type="file" id="vFile" accept=".jpg,.jpeg">
      <div class="icon">&#128269;</div>
      <div class="hint"><strong>Choose a signed JPEG</strong> or drag it here</div>
      <div class="fname" id="vFname"></div>
    </div>
    <button id="vBtn" disabled>Verify Authenticity</button>
    <div class="result" id="vResult"></div>
  </div>
</main>

<footer>Castor &middot; Chain-of-Trust &middot; CodeBlitz 2026 &middot; ECDSA P-256 + SHA-256 + XMP</footer>

<script>
  function wire(zoneId, inputId, fnameId, btnId) {
    const zone = document.getElementById(zoneId);
    const inp  = document.getElementById(inputId);
    const fn   = document.getElementById(fnameId);
    const btn  = document.getElementById(btnId);
    inp.addEventListener("change", () => { if (inp.files[0]) { fn.textContent = inp.files[0].name; btn.disabled = false; } });
    zone.addEventListener("dragover",  e => { e.preventDefault(); zone.classList.add("over"); });
    zone.addEventListener("dragleave", () => zone.classList.remove("over"));
    zone.addEventListener("drop", e => {
      e.preventDefault(); zone.classList.remove("over");
      const f = e.dataTransfer.files[0];
      if (f) { const dt = new DataTransfer(); dt.items.add(f); inp.files = dt.files; fn.textContent = f.name; btn.disabled = false; }
    });
  }

  wire("sZone", "sFile", "sFname", "sBtn");
  wire("vZone", "vFile", "vFname", "vBtn");

  document.getElementById("sBtn").addEventListener("click", async () => {
    const file = document.getElementById("sFile").files[0];
    const btn  = document.getElementById("sBtn");
    const box  = document.getElementById("sResult");
    if (!file) return;
    btn.disabled = true;
    box.className = "result show"; box.innerHTML = "Signing&hellip;";
    const fd = new FormData(); fd.append("image", file);
    try {
      const r = await fetch("/sign", { method: "POST", body: fd });
      const d = await r.json();
      if (r.ok) {
        box.className = "result success show";
        box.innerHTML = `<div class="status-line">&#10022; Manifest Embedded</div>
          <div class="meta">Hash: <span>${d.pixel_hash}</span></div>
          <div class="meta">Signed at: <span>${d.timestamp}</span></div>
          <a class="dl" href="/download/${d.filename}">&#8659; Download Signed JPEG</a>`;
      } else {
        box.className = "result error show";
        box.innerHTML = `<div class="status-line">&#10007; Error</div><div class="meta">${d.error}</div>`;
      }
    } catch { box.className = "result error show"; box.innerHTML = `<div class="status-line">&#10007; Request failed</div>`; }
    btn.disabled = false;
  });

  document.getElementById("vBtn").addEventListener("click", async () => {
    const file = document.getElementById("vFile").files[0];
    const btn  = document.getElementById("vBtn");
    const box  = document.getElementById("vResult");
    if (!file) return;
    btn.disabled = true;
    box.className = "result show"; box.innerHTML = "Verifying&hellip;";
    const fd = new FormData(); fd.append("image", file);
    try {
      const r = await fetch("/verify", { method: "POST", body: fd });
      const d = await r.json();
      if (d.status === "VALID") {
        box.className = "result valid show";
        box.innerHTML = `<div class="status-line" style="color:var(--green)">&#10004; Authentic</div>
          <div class="meta">Hash: <span>${d.pixel_hash}</span></div>
          <div class="meta">Signed at: <span>${d.timestamp}</span></div>
          <div class="meta">Author: <span>${d.author}</span></div>`;
      } else if (d.status === "TAMPERED") {
        box.className = "result tampered show";
        box.innerHTML = `<div class="status-line" style="color:var(--red)">&#10007; Tampered</div>
          <div class="meta">Pixel data has been modified since signing.</div>
          <div class="meta">Expected: <span>${d.stored_hash}</span></div>
          <div class="meta">Got:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span>${d.current_hash}</span></div>`;
      } else {
        box.className = "result error show";
        box.innerHTML = `<div class="status-line" style="color:var(--red)">&#10007; ${d.status.replace(/_/g," ")}</div>
          <div class="meta">${d.message}</div>`;
      }
    } catch { box.className = "result error show"; box.innerHTML = `<div class="status-line">&#10007; Request failed</div>`; }
    btn.disabled = false;
  });
</script>
</body>
</html>"""


@app.get("/")
def index():
    return render_template_string(HTML)


@app.post("/sign")
def sign():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    f = request.files["image"]
    if not f.filename or not allowed(f.filename):
        return jsonify({"error": "Only JPEG files are supported"}), 400

    uid = uuid.uuid4().hex[:8]
    original_name = secure_filename(f.filename)
    upload_path = os.path.join(UPLOAD_FOLDER, f"{uid}_{original_name}")
    f.save(upload_path)

    try:
        from src.pipeline import sign_and_embed
        base, ext = os.path.splitext(original_name)
        signed_name = f"{uid}_{base}_signed{ext}"
        signed_path = os.path.join(SIGNED_FOLDER, signed_name)
        result   = sign_and_embed(upload_path, PRIVATE_KEY, output_path=signed_path)
        manifest = result["manifest"]
        return jsonify({
            "filename":   signed_name,
            "pixel_hash": manifest["integrity"]["pixelHash"],
            "timestamp":  manifest["timestamp"],
            "author":     manifest["author"],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(upload_path):
            os.remove(upload_path)


@app.post("/verify")
def verify():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    f = request.files["image"]
    if not f.filename or not allowed(f.filename):
        return jsonify({"error": "Only JPEG files are supported"}), 400

    uid = uuid.uuid4().hex[:8]
    upload_path = os.path.join(UPLOAD_FOLDER, f"{uid}_{secure_filename(f.filename)}")
    f.save(upload_path)

    try:
        from src.pipeline import verify_signed_image
        result   = verify_signed_image(upload_path, PUBLIC_KEY)
        manifest = result.get("manifest") or {}
        payload  = {
            "status":     result["status"],
            "message":    result["message"],
            "pixel_hash": manifest.get("integrity", {}).get("pixelHash", ""),
            "timestamp":  manifest.get("timestamp", ""),
            "author":     manifest.get("author", ""),
        }
        if result["status"] == "TAMPERED":
            details = result.get("details", {})
            payload["stored_hash"]  = details.get("stored_hash", "")
            payload["current_hash"] = details.get("current_hash", "")
        return jsonify(payload)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(upload_path):
            os.remove(upload_path)


@app.get("/download/<filename>")
def download(filename: str):
    return send_from_directory(SIGNED_FOLDER, filename, as_attachment=True)


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    print(f"[castor] Running on http://localhost:{port}")
    app.run(port=port, debug=False)
