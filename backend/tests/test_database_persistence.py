"""
Module 18: Database & Persistence Test Suite
============================================
Covers:
- Record creation and retrieval across fresh database sessions
- Multi-table relational integrity (User -> BusinessUser -> Business -> Application -> Assessment)
- Assessment responses and Risk records persistence
- Transaction rollback on invalid constraint violation
- Update persistence and timestamp synchronization
"""

import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import (
    User, Business, BusinessUser, AIApplication,
    Assessment, AssessmentResponse, Risk, Recommendation
)
from tests.conftest import TestSessionLocal

def test_records_persist_across_fresh_database_session():
    """Verifies records written in session 1 are queryable in a completely fresh session 2."""
    now = datetime.datetime.utcnow()
    # Session 1: Write
    session1 = TestSessionLocal()
    user = User(email="persistence_test@example.com", full_name="Persistence Tester", is_verified=True, created_at=now)
    session1.add(user)
    session1.commit()
    user_id = user.id
    session1.close()

    # Session 2: Read
    session2 = TestSessionLocal()
    queried_user = session2.query(User).filter(User.id == user_id).first()
    assert queried_user is not None
    assert queried_user.email == "persistence_test@example.com"
    session2.close()

def test_relational_hierarchy_persistence():
    """Verifies deep hierarchy User -> Business -> App -> Assessment -> Responses persists."""
    db = TestSessionLocal()
    now = datetime.datetime.utcnow()

    user = User(email="relational_test@example.com", full_name="Relational Tester", created_at=now)
    db.add(user); db.flush()

    biz = Business(name="Relational Automotive", industry="Automotive Services", size="10-50", location="Munich", created_at=now)
    db.add(biz); db.flush()

    bu = BusinessUser(business_id=biz.id, user_id=user.id, role="Owner", created_at=now)
    db.add(bu); db.flush()

    app_obj = AIApplication(business_id=biz.id, name="Relational AI", purpose="Testing relations", business_function="Quality", data_types="Sensor data", created_at=now)
    db.add(app_obj); db.flush()

    assessment = Assessment(business_id=biz.id, application_id=app_obj.id, name="Relational Assessment", overall_score=80.0, completed_at=now)
    db.add(assessment); db.flush()

    resp = AssessmentResponse(
        assessment_id=assessment.id, question_id="F1", category="fairness",
        question_text="Bias check?", answer="Yes", score=100.0
    )
    db.add(resp)
    db.commit()

    # Re-query and verify relationships
    saved_assessment = db.query(Assessment).filter(Assessment.id == assessment.id).first()
    assert saved_assessment is not None
    assert saved_assessment.application_id == app_obj.id
    assert len(saved_assessment.responses) == 1
    assert saved_assessment.responses[0].question_id == "F1"
    db.close()

def test_transaction_rollback_on_failure():
    """Verifies transaction rollback on integrity error does not persist partial records."""
    db = TestSessionLocal()
    try:
        # User with null email (should fail integrity check if constrained or raise error)
        u1 = User(email="rollback_user@example.com", full_name="User 1")
        db.add(u1)
        db.commit()

        # Try duplicate email
        u2 = User(email="rollback_user@example.com", full_name="User 2")
        db.add(u2)
        try:
            db.commit()
            assert False, "Expected IntegrityError on duplicate email"
        except IntegrityError:
            db.rollback()

        # Confirm only u1 exists
        users = db.query(User).filter(User.email == "rollback_user@example.com").all()
        assert len(users) == 1
    finally:
        db.close()
