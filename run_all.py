import sys, time
from pathlib import Path
import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
import re, glob

ROOT = Path(__file__).parent
NB_DIR = ROOT / "notebooks"
OUT_DIR = ROOT / "reports" / "executed_notebooks"   
OUT_DIR.mkdir(parents=True, exist_ok=True)

paths = sorted(NB_DIR.glob("0[1-6]_*.ipynb"))       # bỏ qua test.ipynb
if sys.argv[1:]:                                    # ví dụ: python run_all.py 01 05
    paths = [p for p in paths if any(p.name.startswith(a) for a in sys.argv[1:])]

for p in paths:
    t0 = time.time()
    print(f"▶ {p.name} ...", flush=True)
    nb = nbformat.read(p, as_version=4)
    # cwd = notebooks/ để "../data/..." và sys.path.append("..") chạy đúng như khi mở trong VS Code
    client = NotebookClient(nb, timeout=1800, resources={"metadata": {"path": str(NB_DIR)}})
    try:
        client.execute()
        status = "OK"
    except CellExecutionError as e:
        status = "FAIL"
        print(e)
    nbformat.write(nb, OUT_DIR / p.name)
    print(f"  {status} ({time.time()-t0:.0f}s) -> {OUT_DIR / p.name}")
    if status == "FAIL":
        sys.exit(1)                                

pat = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|\b[A-Za-z0-9]{20,}\.\d{9,}\b")
for f in glob.glob("notebooks/*.ipynb"): print(f, len(pat.findall(open(f, encoding="utf-8").read())))