import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root.parent / "backend"))
from app.core.database import engine
from app.models import Class, Course, Enrollment, Problem, Submission, User
from sqlmodel import Session, select

m = json.loads((root / "mutation-manifest.json").read_text(encoding="utf-8"))
ids = [m["teacher_id"], *m["student_ids"]]
with Session(engine) as session:
    sub = session.get(Submission, int(m["submission"]["id"]))
    assert sub is not None
    original = m["submission"]["original"]
    # Refuse to overwrite concurrent changes unrelated to this test.
    assert sub.manual_score in (original["manual_score"], 7.5)
    assert sub.status in (original["status"], "accepted")
    assert sub.feedback in (original["feedback"], "Playwright temporary evaluation")
    for field, value in original.items():
        setattr(sub, field, value)
    session.add(sub)
    for uid in ids:
        user = session.get(User, uid)
        if user is None:
            continue
        assert user.full_name.startswith("Playwright ")
        assert user.email == uid + "@st.utc2.edu.vn"
        assert user.role_id in (2, 3)
        assert not session.exec(select(Course).where(Course.created_by == uid)).first()
        assert not session.exec(select(Enrollment).where(Enrollment.student_id == uid)).first()
        assert not session.exec(select(Submission).where(Submission.student_id == uid)).first()
        session.delete(user)
    session.flush()
    classroom = session.get(Class, m["class_id"])
    if classroom is not None:
        assert classroom.type == "PW" and classroom.course_number == 99
        assert not session.exec(select(User).where(User.class_id == m["class_id"])).first()
        session.delete(classroom)
    assert session.get(Problem, m["problem_id"]) is None
    session.commit()
    session.refresh(sub)
    assert all(getattr(sub, field) == value for field, value in original.items())
    assert all(session.get(User, uid) is None for uid in ids)
    assert session.get(Class, m["class_id"]) is None
m["submission"]["restored"] = True
m["submission"]["restoration_method"] = "Scoped local database restoration; API ignores manual_score null"
m["test_accounts_and_class_deleted"] = True
(root / "mutation-manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
print("Verified: original submission fields restored; 3 synthetic accounts and test class removed; source problem absent.")
