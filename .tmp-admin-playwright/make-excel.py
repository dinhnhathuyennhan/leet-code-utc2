import json
import time
from pathlib import Path

from openpyxl import Workbook

root = Path(__file__).parent
stamp = str(int(time.time()))
manifest = {"teacher_id": "PW" + stamp, "student_ids": ["98" + stamp[-7:] + str(i) for i in (1, 2)], "class_id": "PW.99.T" + stamp, "problem_title": "PW Admin Test " + stamp}
wb = Workbook()
ws = wb.active
ws.title = "Sinh viên"
ws.append(["STT", "Mã sinh viên", "Họ và tên", "Lớp"])
for i, sid in enumerate(manifest["student_ids"], 1):
    ws.append([i, sid, f"Playwright Sinh Vien {i}", manifest["class_id"]])
wb.save(root / "valid-students.xlsx")
(root / "mutation-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print("Created Excel fixture with two synthetic students")
