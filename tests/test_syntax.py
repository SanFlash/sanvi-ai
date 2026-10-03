from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parents[1]

FILES = [
    "main.py",
    "sanvi_desktop.py",
    "sanvi_universal.py",
    "sanvi_system.py",
    "local_agent.py",
    "sanvi_background.py",
]

for name in FILES:
    py_compile.compile(str(ROOT / name), doraise=True)

print("SANVI Python syntax OK")
