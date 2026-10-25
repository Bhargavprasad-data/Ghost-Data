import glob
import os

for p in sorted(glob.glob("dataset/evidence/logs/*.log")):
    fname = os.path.basename(p)
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        head = [f.readline().strip() for _ in range(2)]
    print(f"{fname}:")
    for h in head:
        print(f"  {h[:110]}")
