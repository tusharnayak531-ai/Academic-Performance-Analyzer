import tempfile
from pathlib import Path
import sys

import pandas as pd
import pytest
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from v3_core import (
    Assignment, Attendance, Backlog, DEFAULT_MAX, GradeRule, Mark, User,
    authenticate, cgpa, create_store, delete_owned, grade_point, hash_password,
    import_marks, marks_frame, owned, predict_subjects, register, required_marks,
    rules, save_mark, summary, validate_mark, verify_password,
)


@pytest.fixture
def session():
    with tempfile.TemporaryDirectory() as folder:
        factory, engine = create_store("sqlite:///" + str(Path(folder) / "test.sqlite"))
        with factory() as db:
            yield db
        engine.dispose()


def sample(name="CN", semester=5, earned=17):
    return {"subject":name, "semester":semester, "credits":4, "cie":earned,
            "midsem":16, "practical":45, "ese_pr":25, "ese":32,
            **{"max_" + k:v for k,v in DEFAULT_MAX.items()}}


def test_passwords_are_salted_and_verified():
    a,b=hash_password("good-password"),hash_password("good-password")
    assert a!=b
    assert verify_password("good-password",a)
    assert not verify_password("incorrect",a)
    assert not verify_password("test","malformed")


def test_registration_and_login(session):
    person=register(session,"Student.One","long-secret")
    assert person.id>0
    assert authenticate(session,"student.one","long-secret").id==person.id
    assert authenticate(session,"student.one","wrong-password") is None
    with pytest.raises(ValueError): register(session,"student.one","another-password")
    with pytest.raises(ValueError): register(session,"short","weak")


def test_isolation_between_accounts(session):
    first=register(session,"alice123","password-one")
    second=register(session,"bobby123","password-two")
    save_mark(session,first.id,sample())
    save_mark(session,second.id,sample(name="DAA"))
    assert [x.subject for x in owned(session,Mark,first.id)]==["CN"]
    assert [x.subject for x in owned(session,Mark,second.id)]==["DAA"]
    assert not delete_owned(session,Mark,second.id,owned(session,Mark,first.id)[0].id)
    assert len(owned(session,Mark,first.id))==1


def test_mark_validation_blocks_over_maximum(session):
    person=register(session,"marks-user","password123")
    wrong=sample()
    wrong["cie"]=21
    with pytest.raises(ValueError):
        save_mark(session,person.id,wrong)
    assert not owned(session,Mark,person.id)


def test_mark_upsert_not_duplicated(session):
    p=register(session,"upsert-test","password123")
    save_mark(session,p.id,sample())
    newer=sample(earned=18)
    save_mark(session,p.id,newer)
    assert len(owned(session,Mark,p.id))==1
    assert owned(session,Mark,p.id)[0].cie==18


def test_import_supports_all_components_and_atomic_validation(session):
    p=register(session,"csv-user","password123")
    a,b=sample(),sample("DAA")
    b["ese_pr"]=31
    with pytest.raises(ValueError): import_marks(session,p.id,pd.DataFrame([a,b]))
    assert not owned(session,Mark,p.id)
    b["ese_pr"]=20
    assert import_marks(session,p.id,pd.DataFrame([a,b]))==2


def test_aggregate_and_custom_grade_points(session):
    p=register(session,"grading-user","password123")
    a,b=sample(),sample(name="DAA")
    save_mark(session,p.id,a)
    save_mark(session,p.id,b)
    df=marks_frame(owned(session,Mark,p.id),rules(session,p.id))
    assert len(df)==2 and df.percentage.between(0,100).all()
    assert 0<=cgpa(df)<=10
    assert summary(df).iloc[0].credits==8


def test_grading_customizes_outputs():
    assert grade_point(82,[(85,10),(80,9),(0,0)])==9
    assert grade_point(70,[(85,10),(80,9),(0,0)])==0


def test_required_marks_and_impossible_target():
    result=required_marks(45,60,40,75)
    assert result["required"]==30
    assert result["possible"]
    assert not required_marks(0,60,40,90)["possible"]
    with pytest.raises(ValueError): required_marks(100,60,40,70)


def test_trend_requires_history(session):
    p=register(session,"trend-user","password123")
    save_mark(session,p.id,sample(semester=3))
    single=marks_frame(owned(session,Mark,p.id),rules(session,p.id))
    assert predict_subjects(single).empty
    save_mark(session,p.id,sample(semester=4,earned=18))
    both=marks_frame(owned(session,Mark,p.id),rules(session,p.id))
    assert len(predict_subjects(both))==1


def test_backlog_is_private(session):
    a=register(session,"backlog-a","password123")
    b=register(session,"backlog-b","password123")
    item=Backlog(user_id=a.id,semester=4,subject="CJP",component="ESE Theory",status="Pending",attempts=2)
    session.add(item);session.commit()
    assert len(owned(session,Backlog,a.id))==1
    assert not owned(session,Backlog,b.id)


def test_login_does_not_store_plaintext(session):
    person=register(session,"safe-user","secretsecret")
    assert person.password_hash!="secretsecret"
    assert "secretsecret" not in person.password_hash
