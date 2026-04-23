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
<title>Castor</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#ffffff;
  --dark:#1c1c1c;
  --darkgrey:#2a2a2a;
  --darkgrey2:#222222;
  --orange:#e8611a;
  --orange-d:#c44e10;
  --lgrey:#f0f0f0;
  --mgrey:#888;
  --font-title:'Bebas Neue',sans-serif;
  --font-body:'DM Sans',sans-serif;
}
body{background:var(--bg);font-family:var(--font-body);overflow:hidden;height:100vh;width:100vw}

.page{position:absolute;inset:0;display:none;opacity:0;transition:opacity .4s}
.page.active{display:flex;opacity:1}

/* ── PAGE 1 ── */
#p1{flex-direction:column;align-items:center;justify-content:center;background:var(--bg);overflow:hidden}
.split-top,.split-bottom{
  position:absolute;left:0;width:100%;height:50%;
  background:var(--dark);
  display:flex;align-items:center;justify-content:center;
  transition:transform .7s cubic-bezier(.77,0,.18,1);z-index:2;
}
.split-top{top:0;transform:translateY(0)}
.split-bottom{bottom:0;transform:translateY(0)}
.split-top.open{transform:translateY(-100%)}
.split-bottom.open{transform:translateY(100%)}

/* Title sits exactly at the 50% midpoint so the split line bisects it */
.title-wrap{
  position:absolute;
  bottom:50%;
  left:50%;
  transform:translateX(-50%);
  padding-bottom:18px;
  z-index:3;
  text-align:center;
  display:flex;flex-direction:column;align-items:center;gap:8px;
  cursor:pointer;user-select:none;
}
.app-title{
  font-family:var(--font-title);font-size:clamp(64px,12vw,120px);
  color:var(--bg);letter-spacing:.06em;line-height:1;transition:color .3s;
  /* push the title up by exactly half its own height so the
     horizontal centre of the glyph aligns with the 50% split line */
  margin-bottom:0;
}
.title-wrap:hover .app-title{color:var(--orange)}
.app-sub{font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:rgba(255,255,255,.5);font-weight:300;display:none}
.click-hint{margin-top:16px;font-size:11px;letter-spacing:.15em;text-transform:uppercase;color:rgba(255,255,255,.3);animation:pulse 2s ease-in-out infinite;display:none}
.title-below{
  position:absolute;
  top:50%;
  left:50%;
  transform:translateX(-50%);
  padding-top:18px;
  z-index:3;
  text-align:center;
  display:flex;flex-direction:column;align-items:center;gap:8px;
  pointer-events:none;
}
.title-below .app-sub{display:block}
.title-below .click-hint{display:block}
@keyframes pulse{0%,100%{opacity:.3}50%{opacity:.7}}
.ripple{
  position:absolute;border-radius:50%;background:rgba(232,97,26,.25);
  transform:scale(0);pointer-events:none;z-index:4;
  animation:ripple-out .8s ease-out forwards;
}
@keyframes ripple-out{to{transform:scale(6);opacity:0}}
.bg-grid{
  position:absolute;inset:0;
  background-image:linear-gradient(var(--lgrey) 1px,transparent 1px),linear-gradient(90deg,var(--lgrey) 1px,transparent 1px);
  background-size:40px 40px;opacity:.5;z-index:1;
}

/* ── PAGE 2 ── */
#p2{flex-direction:column;align-items:center;justify-content:center;background:var(--bg);gap:48px}
.p2-title{font-family:var(--font-title);font-size:48px;color:var(--dark);letter-spacing:.05em;text-align:center}
.p2-sub{font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:var(--mgrey);margin-top:4px;text-align:center}
.hex-row{display:flex;gap:60px;align-items:center}
.hex-btn{display:flex;flex-direction:column;align-items:center;gap:16px;cursor:pointer}

/* Hexagons scaled to ~55% of a page-3 column width.
   Page 3 body is split 50/50 minus a 1px gap, so one column ≈ 50vw.
   55% of 50vw = 27.5vw. We clamp between a min of 140px and max of 260px
   and keep the SVG native 120:138 aspect ratio → height = width * 1.15 */
.hex-shape{
  width:clamp(140px,27.5vw,260px);
  height:calc(clamp(140px,27.5vw,260px) * 1.15);
  position:relative;
  transition:transform .25s cubic-bezier(.34,1.56,.64,1);
}
.hex-btn:hover .hex-shape{transform:scale(1.06)}
.hex-shape svg{width:100%;height:100%}
.hex-label{font-family:var(--font-title);font-size:clamp(24px,3.5vw,36px);letter-spacing:.1em;color:var(--dark);transition:color .2s}
.hex-btn:hover .hex-label{color:var(--orange)}
.hex-desc{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--mgrey);margin-top:-8px}

/* ── BACK BTN ── */
.back-btn{
  font-size:13px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--mgrey);cursor:pointer;border:none;background:none;
  font-family:var(--font-body);display:flex;align-items:center;gap:6px;transition:color .2s;
}
.back-btn:hover{color:var(--orange)}

/* ── PAGE 3 SHARED ── */
#p3a,#p3b{flex-direction:column;background:var(--darkgrey)}
.p3-header{
  padding:20px 32px;border-bottom:1px solid rgba(255,255,255,.08);
  display:flex;align-items:center;gap:16px;flex-shrink:0;
  background:var(--darkgrey);
}
.p3-mode{font-family:var(--font-title);font-size:32px;letter-spacing:.06em}
.p3-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.p3-hint{font-size:11px;letter-spacing:.12em;text-transform:uppercase;margin-left:auto}
.p3-body{flex:1;display:grid;grid-template-columns:1fr 1fr;gap:1px;background:rgba(255,255,255,.06);overflow:hidden}
.p3-col{padding:32px;display:flex;flex-direction:column;gap:20px;overflow-y:auto}
.col-label{
  font-size:10px;letter-spacing:.2em;text-transform:uppercase;
  display:flex;align-items:center;gap:8px;
}
.col-label::after{content:'';flex:1;height:1px}

/* ── PAGE 3A  (SIGN): col-1 = dark, col-2 = white ── */
#p3a .p3-col:first-child{background:var(--darkgrey2);}
#p3a .p3-col:first-child .col-label{color:rgba(255,255,255,.35);}
#p3a .p3-col:first-child .col-label::after{background:rgba(255,255,255,.1);}
#p3a .p3-col:first-child .dz-text{color:rgba(255,255,255,.4);}
#p3a .p3-col:first-child .dz-text strong{color:var(--orange);}
#p3a .p3-col:first-child .dz-icon{border-color:rgba(255,255,255,.15);}
#p3a .p3-col:first-child .dz-icon-inner{background:rgba(255,255,255,.08);}
#p3a .p3-col:first-child .drop-zone{border-color:rgba(255,255,255,.15);}
#p3a .p3-col:first-child .drop-zone:hover,#p3a .p3-col:first-child .drop-zone.over{border-color:var(--orange);background:rgba(232,97,26,.05);}
#p3a .p3-col:first-child .dz-fname{color:rgba(255,255,255,.8);}
#p3a .p3-col:first-child .img-preview{border-color:rgba(255,255,255,.12);}
#p3a .p3-col:first-child .processing{color:rgba(255,255,255,.4);}
#p3a .p3-col:first-child .spinner{border-color:rgba(255,255,255,.1);border-top-color:var(--orange);}

#p3a .p3-col:last-child{background:#ffffff;}
#p3a .p3-col:last-child .col-label{color:#aaa;}
#p3a .p3-col:last-child .col-label::after{background:#e8e8e8;}
#p3a .p3-col:last-child .info-label{color:#aaa;}
#p3a .p3-col:last-child .info-value{color:#1c1c1c;}
#p3a .p3-col:last-child .info-value.mono{color:#555;}
#p3a .p3-col:last-child .ph-bar{background:#efefef;}

#p3a .p3-mode{color:var(--orange);}
#p3a .p3-dot{background:var(--orange);}
#p3a .p3-hint{color:rgba(255,255,255,.3);}
#p3a .back-btn{color:rgba(255,255,255,.4);}
#p3a .back-btn:hover{color:var(--orange);}

/* action btn in 3a dark col */
#p3a .p3-col:first-child .action-btn{background:var(--orange);color:#fff;}
#p3a .p3-col:first-child .action-btn:hover{background:var(--orange-d);}
#p3a .p3-col:first-child .action-btn:disabled{background:rgba(255,255,255,.1);color:rgba(255,255,255,.25);}

/* ── PAGE 3B  (VERIFY): col-1 = orange, col-2 = dark ── */
#p3b .p3-col:first-child{background:var(--orange);}
#p3b .p3-col:first-child .col-label{color:rgba(255,255,255,.5);}
#p3b .p3-col:first-child .col-label::after{background:rgba(255,255,255,.2);}
#p3b .p3-col:first-child .dz-text{color:rgba(255,255,255,.6);}
#p3b .p3-col:first-child .dz-text strong{color:#fff;font-weight:600;}
#p3b .p3-col:first-child .dz-icon{border-color:rgba(255,255,255,.35);}
#p3b .p3-col:first-child .dz-icon-inner{background:rgba(255,255,255,.2);}
#p3b .p3-col:first-child .drop-zone{border-color:rgba(255,255,255,.35);}
#p3b .p3-col:first-child .drop-zone:hover,#p3b .p3-col:first-child .drop-zone.over{border-color:#fff;background:rgba(255,255,255,.08);}
#p3b .p3-col:first-child .dz-fname{color:#fff;}
#p3b .p3-col:first-child .img-preview{border-color:rgba(255,255,255,.25);}
#p3b .p3-col:first-child .processing{color:rgba(255,255,255,.6);}
#p3b .p3-col:first-child .spinner{border-color:rgba(255,255,255,.2);border-top-color:#fff;}
#p3b .p3-col:first-child .action-btn{background:#fff;color:var(--orange-d);font-weight:600;}
#p3b .p3-col:first-child .action-btn:hover{background:rgba(255,255,255,.88);}
#p3b .p3-col:first-child .action-btn:disabled{background:rgba(255,255,255,.2);color:rgba(255,255,255,.4);}

#p3b .p3-col:last-child{background:var(--darkgrey2);}
#p3b .p3-col:last-child .col-label{color:rgba(255,255,255,.35);}
#p3b .p3-col:last-child .col-label::after{background:rgba(255,255,255,.1);}
#p3b .p3-col:last-child .info-label{color:rgba(255,255,255,.4);}
#p3b .p3-col:last-child .info-value{color:rgba(255,255,255,.85);}
#p3b .p3-col:last-child .info-value.mono{color:rgba(255,255,255,.55);}
#p3b .p3-col:last-child .ph-bar{background:rgba(255,255,255,.07);}

#p3b .p3-mode{color:#fff;}
#p3b .p3-dot{background:#fff;}
#p3b .p3-hint{color:rgba(255,255,255,.3);}
#p3b .back-btn{color:rgba(255,255,255,.4);}
#p3b .back-btn:hover{color:#fff;}

/* drop zone (base — overridden per page above) */
.drop-zone{
  flex:1;min-height:200px;border:1.5px dashed #ddd;border-radius:8px;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:12px;cursor:pointer;transition:border-color .2s,background .2s;position:relative;
}
.drop-zone:hover,.drop-zone.over{border-color:var(--orange);background:rgba(232,97,26,.03)}
.drop-zone input{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%}
.dz-icon{width:48px;height:48px;border:1.5px solid #ddd;border-radius:8px;display:flex;align-items:center;justify-content:center;transition:border-color .2s}
.drop-zone:hover .dz-icon,.drop-zone.over .dz-icon{border-color:var(--orange)}
.dz-icon-inner{width:20px;height:20px;background:var(--lgrey);border-radius:3px}
.dz-text{font-size:13px;color:var(--mgrey);text-align:center;line-height:1.5}
.dz-text strong{color:var(--orange);font-weight:500}
.dz-fname{font-size:12px;color:var(--dark);font-weight:500;text-align:center}
.img-preview{width:100%;border-radius:6px;object-fit:contain;max-height:220px;border:1px solid var(--lgrey);display:none}

/* action btn (base) */
.action-btn{
  padding:14px;border:none;border-radius:6px;background:var(--dark);color:#fff;
  font-family:var(--font-body);font-size:13px;font-weight:500;
  letter-spacing:.08em;text-transform:uppercase;cursor:pointer;transition:background .2s,transform .1s;
}
.action-btn:hover{background:var(--orange)}
.action-btn:active{transform:scale(.98)}
.action-btn:disabled{background:var(--lgrey);color:var(--mgrey);cursor:not-allowed}

/* info panel */
.info-panel{display:flex;flex-direction:column;gap:12px}
.info-row{display:flex;flex-direction:column;gap:4px}
.info-label{font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--mgrey)}
.info-value{font-size:13px;color:var(--dark);word-break:break-all;line-height:1.5}
.info-value.mono{font-family:monospace;font-size:11px;color:#555}
.info-placeholder{flex:1;display:flex;flex-direction:column;gap:10px;justify-content:center}
.ph-bar{height:12px;background:var(--lgrey);border-radius:3px;animation:ph-pulse 1.5s ease-in-out infinite}
.ph-bar:nth-child(2){width:70%}
.ph-bar:nth-child(3){width:85%}
.ph-bar:nth-child(4){width:60%}
@keyframes ph-pulse{0%,100%{opacity:.4}50%{opacity:.8}}

/* status */
.status-badge{padding:12px 16px;border-radius:6px;display:flex;align-items:center;gap:10px;font-size:13px;font-weight:500;display:none}
.status-badge.show{display:flex}
.status-badge.valid{background:rgba(46,160,67,.08);border:1px solid rgba(46,160,67,.2);color:#1a7f37}
.status-badge.tampered{background:rgba(231,76,60,.08);border:1px solid rgba(231,76,60,.2);color:#c0392b}
.status-badge.error,.status-badge.success{background:rgba(232,97,26,.08);border:1px solid rgba(232,97,26,.2);color:var(--orange-d)}
.sb-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.valid .sb-dot{background:#2ea043}
.tampered .sb-dot{background:#e74c3c}
.error .sb-dot,.success .sb-dot{background:var(--orange)}

/* processing */
.processing{display:none;align-items:center;gap:10px;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--mgrey)}
.processing.show{display:flex}
.spinner{width:14px;height:14px;border:2px solid var(--lgrey);border-top-color:var(--orange);border-radius:50%;animation:spin .7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>

<!-- PAGE 1 -->
<div class="page active" id="p1">
  <div class="bg-grid"></div>
  <div class="split-top" id="st"></div>
  <div class="split-bottom" id="sb"></div>
  <div class="title-wrap" id="titleBtn">
    <div class="app-title">CASTOR</div>
  </div>
  <div class="title-below">
    <div class="app-sub">Cryptographic Image Provenance</div>
    <div class="click-hint">click to enter</div>
  </div>
</div>

<!-- PAGE 2 -->
<div class="page" id="p2">
  <button class="back-btn" style="position:absolute;top:24px;left:24px" onclick="goTo('p1')">&#9664; back</button>
  <div>
    <div class="p2-title">CASTOR</div>
    <div class="p2-sub">Choose an action</div>
  </div>
  <div class="hex-row">
    <div class="hex-btn" onclick="goTo('p3a')">
      <div class="hex-shape">
        <svg viewBox="0 0 120 138" fill="none" xmlns="http://www.w3.org/2000/svg">
          <polygon points="60,4 116,34 116,104 60,134 4,104 4,34" fill="#1c1c1c"/>
          <rect x="42" y="68" width="36" height="28" rx="4" fill="white" opacity=".9"/>
          <path d="M48 68V58a12 12 0 0 1 24 0v10" stroke="white" stroke-width="3" stroke-linecap="round" fill="none" opacity=".9"/>
          <circle cx="60" cy="82" r="4" fill="#1c1c1c"/>
        </svg>
      </div>
      <div class="hex-label">SIGN</div>
      <div class="hex-desc">Embed manifest</div>
    </div>
    <div class="hex-btn" onclick="goTo('p3b')">
      <div class="hex-shape">
        <svg viewBox="0 0 120 138" fill="none" xmlns="http://www.w3.org/2000/svg">
          <polygon points="60,4 116,34 116,104 60,134 4,104 4,34" fill="#e8611a"/>
          <rect x="42" y="68" width="36" height="28" rx="4" fill="white" opacity=".9"/>
          <path d="M48 68V58a12 12 0 0 1 24 0" stroke="white" stroke-width="3" stroke-linecap="round" fill="none" opacity=".9"/>
          <circle cx="60" cy="82" r="4" fill="#e8611a"/>
        </svg>
      </div>
      <div class="hex-label">VERIFY</div>
      <div class="hex-desc">Check authenticity</div>
    </div>
  </div>
</div>

<!-- PAGE 3A: SIGN -->
<div class="page" id="p3a" style="flex-direction:column">
  <div class="p3-header">
    <button class="back-btn" onclick="goTo('p2')">&#9664;</button>
    <div class="p3-dot"></div>
    <div class="p3-mode">SIGN IMAGE</div>
    <div class="p3-hint">ECDSA P-256 &middot; SHA-256 &middot; XMP</div>
  </div>
  <div class="p3-body">
    <div class="p3-col">
      <div class="col-label">Image Input</div>
      <div class="drop-zone" id="signZone">
        <input type="file" id="signFile" accept=".jpg,.jpeg">
        <div class="dz-icon"><div class="dz-icon-inner"></div></div>
        <div class="dz-text"><strong>Choose a JPEG</strong><br>or drag it here</div>
        <div class="dz-fname" id="signFname"></div>
      </div>
      <img class="img-preview" id="signPreview" alt="preview">
      <div class="processing" id="signProc"><div class="spinner"></div>Signing image...</div>
      <button class="action-btn" id="signBtn" disabled onclick="doSign()">Sign &amp; Embed Manifest</button>
    </div>
    <div class="p3-col">
      <div class="col-label">Manifest Properties</div>
      <div class="info-placeholder" id="signPlaceholder">
        <div class="ph-bar"></div><div class="ph-bar"></div><div class="ph-bar"></div><div class="ph-bar"></div>
      </div>
      <div class="info-panel" id="signInfo" style="display:none">
        <div class="info-row"><div class="info-label">Schema</div><div class="info-value" id="si-schema">—</div></div>
        <div class="info-row"><div class="info-label">Timestamp</div><div class="info-value" id="si-ts">—</div></div>
        <div class="info-row"><div class="info-label">Author</div><div class="info-value" id="si-author">—</div></div>
        <div class="info-row"><div class="info-label">Algorithm</div><div class="info-value">ECDSA P-256 &middot; SHA-256</div></div>
        <div class="info-row"><div class="info-label">Pixel Hash</div><div class="info-value mono" id="si-hash">—</div></div>
        <div class="info-row"><div class="info-label">Ledger</div><div class="info-value" id="si-ledger">—</div></div>
      </div>
      <div class="status-badge" id="signStatus"></div>
    </div>
  </div>
</div>

<!-- PAGE 3B: VERIFY -->
<div class="page" id="p3b" style="flex-direction:column">
  <div class="p3-header">
    <button class="back-btn" onclick="goTo('p2')">&#9664;</button>
    <div class="p3-dot"></div>
    <div class="p3-mode">VERIFY IMAGE</div>
    <div class="p3-hint">Re-hash &middot; Compare &middot; Authenticate</div>
  </div>
  <div class="p3-body">
    <div class="p3-col">
      <div class="col-label">Signed Image Input</div>
      <div class="drop-zone" id="verifyZone">
        <input type="file" id="verifyFile" accept=".jpg,.jpeg">
        <div class="dz-icon"><div class="dz-icon-inner"></div></div>
        <div class="dz-text"><strong>Choose a signed JPEG</strong><br>or drag it here</div>
        <div class="dz-fname" id="verifyFname"></div>
      </div>
      <img class="img-preview" id="verifyPreview" alt="preview">
      <div class="processing" id="verifyProc"><div class="spinner"></div>Verifying...</div>
      <button class="action-btn" id="verifyBtn" disabled onclick="doVerify()">Verify Authenticity</button>
    </div>
    <div class="p3-col">
      <div class="col-label">Verification Result</div>
      <div class="info-placeholder" id="verifyPlaceholder">
        <div class="ph-bar"></div><div class="ph-bar"></div><div class="ph-bar"></div><div class="ph-bar"></div>
      </div>
      <div class="info-panel" id="verifyInfo" style="display:none">
        <div class="info-row"><div class="info-label">Status</div><div class="info-value" id="vi-status">—</div></div>
        <div class="info-row"><div class="info-label">Signed At</div><div class="info-value" id="vi-ts">—</div></div>
        <div class="info-row"><div class="info-label">Author</div><div class="info-value" id="vi-author">—</div></div>
        <div class="info-row"><div class="info-label">Pixel Hash</div><div class="info-value mono" id="vi-hash">—</div></div>
        <div class="info-row" id="vi-tamper-row" style="display:none">
          <div class="info-label">Expected Hash</div><div class="info-value mono" id="vi-stored">—</div>
        </div>
      </div>
      <div class="status-badge" id="verifyStatus"></div>
    </div>
  </div>
</div>

<script>
const pages=['p1','p2','p3a','p3b'];
function goTo(id){
  pages.forEach(p=>{
    const el=document.getElementById(p);
    el.style.display='none';el.classList.remove('active');el.style.opacity='0';
  });
  const t=document.getElementById(id);
  t.style.display='flex';
  requestAnimationFrame(()=>{t.style.opacity='1';t.classList.add('active');});
}


document.getElementById('titleBtn').addEventListener('click',function(e){
  const rip=document.createElement('div');
  const size=120;rip.className='ripple';
  rip.style.cssText=`width:${size}px;height:${size}px;top:${e.clientY-size/2}px;left:${e.clientX-size/2}px`;
  document.getElementById('p1').appendChild(rip);
  setTimeout(()=>rip.remove(),900);
  document.getElementById('st').classList.add('open');
  document.getElementById('sb').classList.add('open');
  setTimeout(()=>{
    goTo('p2');
    document.getElementById('st').classList.remove('open');
    document.getElementById('sb').classList.remove('open');
  },750);
});

function wireZone(zoneId,inputId,fnameId,previewId,btnId){
  const zone=document.getElementById(zoneId),inp=document.getElementById(inputId);
  const fn=document.getElementById(fnameId),preview=document.getElementById(previewId);
  const btn=document.getElementById(btnId);
  inp.addEventListener('change',()=>{
    const f=inp.files[0];if(!f)return;
    fn.textContent=f.name;btn.disabled=false;
    preview.src=URL.createObjectURL(f);preview.style.display='block';
  });
  zone.addEventListener('dragover',e=>{e.preventDefault();zone.classList.add('over');});
  zone.addEventListener('dragleave',()=>zone.classList.remove('over'));
  zone.addEventListener('drop',e=>{
    e.preventDefault();zone.classList.remove('over');
    const f=e.dataTransfer.files[0];if(!f)return;
    const dt=new DataTransfer();dt.items.add(f);inp.files=dt.files;
    fn.textContent=f.name;btn.disabled=false;
    preview.src=URL.createObjectURL(f);preview.style.display='block';
  });
}
wireZone('signZone','signFile','signFname','signPreview','signBtn');
wireZone('verifyZone','verifyFile','verifyFname','verifyPreview','verifyBtn');

async function doSign(){
  const file=document.getElementById('signFile').files[0];if(!file)return;
  const btn=document.getElementById('signBtn'),proc=document.getElementById('signProc');
  const status=document.getElementById('signStatus'),info=document.getElementById('signInfo');
  const ph=document.getElementById('signPlaceholder');
  btn.disabled=true;proc.classList.add('show');
  status.className='status-badge';info.style.display='none';ph.style.display='flex';
  const fd=new FormData();fd.append('image',file);
  try{
    const r=await fetch('/sign',{method:'POST',body:fd});
    const d=await r.json();
    proc.classList.remove('show');
    if(r.ok){
      ph.style.display='none';info.style.display='flex';
      document.getElementById('si-schema').textContent='chain-of-trust/v1';
      document.getElementById('si-ts').textContent=new Date(d.timestamp).toLocaleString();
      document.getElementById('si-author').textContent=d.author||'chain-of-trust';
      document.getElementById('si-hash').textContent=d.pixel_hash;
      document.getElementById('si-ledger').textContent='Mock ledger \u00b7 anchored';
      status.className='status-badge success show';
      status.innerHTML='<div class="sb-dot"></div>Manifest embedded \u2014 downloading signed image...';
      const a=document.createElement('a');
      a.href='/download/'+d.filename;a.download=d.filename;
      document.body.appendChild(a);a.click();document.body.removeChild(a);
    }else{
      ph.style.display='none';
      status.className='status-badge error show';
      status.innerHTML='<div class="sb-dot"></div>'+(d.error||'Unknown error');
    }
  }catch(e){
    proc.classList.remove('show');ph.style.display='none';
    status.className='status-badge error show';
    status.innerHTML='<div class="sb-dot"></div>Request failed';
  }
  btn.disabled=false;
}

async function doVerify(){
  const file=document.getElementById('verifyFile').files[0];if(!file)return;
  const btn=document.getElementById('verifyBtn'),proc=document.getElementById('verifyProc');
  const status=document.getElementById('verifyStatus'),info=document.getElementById('verifyInfo');
  const ph=document.getElementById('verifyPlaceholder');
  btn.disabled=true;proc.classList.add('show');
  status.className='status-badge';info.style.display='none';ph.style.display='flex';
  const fd=new FormData();fd.append('image',file);
  try{
    const r=await fetch('/verify',{method:'POST',body:fd});
    const d=await r.json();
    proc.classList.remove('show');ph.style.display='none';info.style.display='flex';
    document.getElementById('vi-ts').textContent=d.timestamp?new Date(d.timestamp).toLocaleString():'—';
    document.getElementById('vi-author').textContent=d.author||'—';
    document.getElementById('vi-hash').textContent=d.pixel_hash||'—';
    const tamperRow=document.getElementById('vi-tamper-row');
    if(d.status==='VALID'){
      document.getElementById('vi-status').textContent='Authentic';
      status.className='status-badge valid show';
      status.innerHTML='<div class="sb-dot"></div>Image is authentic \u2014 pixels and signature verified.';
      tamperRow.style.display='none';
    }else if(d.status==='TAMPERED'){
      document.getElementById('vi-status').textContent='Tampered';
      document.getElementById('vi-stored').textContent=d.stored_hash||'—';
      tamperRow.style.display='flex';
      status.className='status-badge tampered show';
      status.innerHTML='<div class="sb-dot"></div>Pixel data has been modified since signing.';
    }else{
      document.getElementById('vi-status').textContent=d.status.replace(/_/g,' ');
      tamperRow.style.display='none';
      status.className='status-badge error show';
      status.innerHTML='<div class="sb-dot"></div>'+(d.message||'Verification failed');
    }
  }catch(e){
    proc.classList.remove('show');ph.style.display='none';
    status.className='status-badge error show';
    status.innerHTML='<div class="sb-dot"></div>Request failed';
  }
  btn.disabled=false;
}
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
