from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parents[1]
for name in ["main.py", "sanvi_desktop.py", "local_agent.py", "sanvi_background.py"]:
    py_compile.compile(str(ROOT / name), doraise=True)
print("SANVI Python syntax OK")
