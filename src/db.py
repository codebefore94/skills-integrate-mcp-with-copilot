from typing import List, Optional
from sqlmodel import Field, SQLModel, create_engine, Session, select, Relationship
import os


DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./activities.db")


class Participant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    activity_id: int = Field(foreign_key="activity.id")
    activity: Optional["Activity"] = Relationship(back_populates="participants")


class Activity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = ""
    schedule: Optional[str] = ""
    max_participants: int = 0
    participants: List[Participant] = Relationship(back_populates="activity")


engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def init_db():
    SQLModel.metadata.create_all(engine)


DEFAULT_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    }
}


def seed_default_activities_if_needed():
    with Session(engine) as session:
        count = session.exec(select(Activity)).all()
        if count:
            return

        for name, data in DEFAULT_ACTIVITIES.items():
            activity = Activity(
                name=name,
                description=data.get("description", ""),
                schedule=data.get("schedule", ""),
                max_participants=data.get("max_participants", 0),
            )
            session.add(activity)
            session.commit()
            session.refresh(activity)

            for email in data.get("participants", []):
                participant = Participant(email=email, activity_id=activity.id)
                session.add(participant)
            session.commit()


def get_activities_dict():
    """Return activities in the same dict shape as the original app for backward compatibility."""
    result = {}
    with Session(engine) as session:
        activities = session.exec(select(Activity)).all()
        for a in activities:
            participants = [p.email for p in a.participants]
            result[a.name] = {
                "description": a.description,
                "schedule": a.schedule,
                "max_participants": a.max_participants,
                "participants": participants,
            }
    return result


def signup_for_activity(activity_name: str, email: str):
    with Session(engine) as session:
        activity = session.exec(select(Activity).where(Activity.name == activity_name)).first()
        if not activity:
            return None, "not_found"

        emails = [p.email for p in activity.participants]
        if email in emails:
            return None, "already_signed"

        if len(emails) >= activity.max_participants:
            return None, "full"

        participant = Participant(email=email, activity_id=activity.id)
        session.add(participant)
        session.commit()
        return participant, "ok"


def unregister_from_activity(activity_name: str, email: str):
    with Session(engine) as session:
        activity = session.exec(select(Activity).where(Activity.name == activity_name)).first()
        if not activity:
            return None, "not_found"

        participant = session.exec(
            select(Participant).where(Participant.activity_id == activity.id).where(Participant.email == email)
        ).first()
        if not participant:
            return None, "not_signed"

        session.delete(participant)
        session.commit()
        return participant, "ok"
