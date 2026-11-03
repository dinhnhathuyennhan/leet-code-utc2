"""
Render security-regression.sh output (ANSI-stripped) thanh anh PNG giong terminal.
Input : security-regression.out  (sinh ra boi security-regression.sh)
Output: docs/security-regression-result.png
"""
import html
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_TXT = ROOT / "security-regression.out"
HTML_TMP = ROOT / "docs" / "_secreg_render.html"
PNG_OUT = ROOT / "docs" / "security-regression-result.png"

# Chay lai script de lay output that
BASH = r"C:\Program Files\Git\bin\bash.exe"
if BASH and Path(BASH).exists():
    proc = subprocess.run(
        [BASH, "-lc", "./security-regression.sh"],
        cwd=ROOT, capture_output=True, text=True,
        check=False,
    )
    raw = proc.stdout + proc.stderr
else:
    raw = OUT_TXT.read_text(encoding="utf-8", errors="replace")

# Bo ANSI escape
raw = re.sub(r"\x1B\[[0-9;]*[A-Za-z]", "", raw)
lines = raw.replace("\r", "").split("\n")

# Phan loai mau theo noi dung dong
def color_for(line: str) -> str:
    s = line.strip()
    if s.startswith("[PASS]"):
        return "pass"
    if s.startswith("[FAIL]"):
        return "fail"
    if s.startswith("[OK]"):
        return "ok"
    if s.startswith(("[*]", "[!]")):
        return "warn"
    if s.startswith("[X]"):
        return "err"
    if s.startswith("KET QUA"):
        return "res" if "FAIL" in s else "res-pass"
    if re.match(r"^={5,}", s):
        return "rule"
    if s.startswith(("SECURITY REGRESSION", "Target:")):
        return "head"
    if s.startswith("Test case"):
        return "sub"
    if s.startswith("$"):
        return "cmd"
    if s.startswith(("(", "Day chinh")):
        return "dim"
    return "plain"

def esc(t: str) -> str:
    return html.escape(t)

parts = []
for ln in lines:
    c = color_for(ln)
    # highlight token [PASS]/[FAIL] rieng
    m = re.match(r"^(\s*)(\[(PASS|FAIL|OK|X)\])(.*)$", ln)
    if m:
        indent, tag, kind, rest = m.groups()
        parts.append(
            f'<div><span class="plain">{esc(indent)}</span>'
            f'<span class="{c}">{esc(tag)}</span>'
            f'<span class="plain">{esc(rest)}</span></div>'
        )
    else:
        parts.append(f'<div class="{c}">{esc(ln)}</div>')

body = "\n".join(parts)

HTML = f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"><title>Security Regression</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; padding:24px 26px; background:#010409;
    font-family:"Cascadia Mono","Consolas","JetBrains Mono",monospace;
    font-size:15px; line-height:1.5; color:#c9d1d9; }}
  .win {{ background:#0d1117; border:1px solid #30363d; border-radius:8px;
    overflow:hidden; box-shadow:0 10px 36px rgba(0,0,0,.6); }}
  .tb {{ background:#161b22; border-bottom:1px solid #30363d; padding:9px 14px;
    display:flex; align-items:center; gap:8px; }}
  .dot {{ width:12px; height:12px; border-radius:50%; }}
  .ttl {{ margin-left:10px; font-size:13px; color:#8b949e; }}
  .term {{ padding:16px 20px; white-space:pre; }}
  .cmd {{ color:#79c0ff; font-weight:600; }}
  .head {{ color:#58a6ff; font-weight:700; }}
  .sub {{ color:#d2a8ff; font-weight:700; }}
  .rule {{ color:#30363d; }}
  .pass {{ color:#3fb950; font-weight:700; }}
  .fail {{ color:#f85149; font-weight:700; }}
  .ok {{ color:#3fb950; }}
  .warn {{ color:#d29922; }}
  .err {{ color:#f85149; font-weight:700; }}
  .dim {{ color:#6e7681; }}
  .plain {{ color:#c9d1d9; }}
  .res {{ color:#f85149; font-weight:700; }}
  .res-pass {{ color:#3fb950; font-weight:700; }}
</style></head><body>
<div class="win">
  <div class="tb">
    <span class="dot" style="background:#ff5f57"></span>
    <span class="dot" style="background:#febc2e"></span>
    <span class="dot" style="background:#28c840"></span>
    <span class="ttl">bash &mdash; security-regression.sh</span>
  </div>
  <div class="term">
{body}
  </div>
</div>
</body></html>
"""

HTML_TMP.write_text(HTML, encoding="utf-8")
print(f"HTML written: {HTML_TMP}")

# Chup anh bang Edge headless
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
height = 90 + len(lines) * 24
subprocess.run([
    EDGE, "--headless", "--disable-gpu", "--hide-scrollbars",
    f"--screenshot={PNG_OUT}",
    f"--window-size=1120,{height}",
    HTML_TMP.as_uri(),
], check=False)

print(f"PNG written: {PNG_OUT}")
