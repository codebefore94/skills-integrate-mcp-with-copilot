"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from . import db

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")



@app.on_event("startup")
def on_startup():
    # Initialize database and seed with a small default dataset if empty
    try:
        db.init_db()
        db.seed_default_activities_if_needed()
    except Exception:
        # If SQLModel or DB isn't available yet (e.g. dependencies not installed), skip and let the server run
        pass


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return db.get_activities_dict()


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity (persistent)."""
    participant, status = db.signup_for_activity(activity_name, email)
    if status == "not_found":
        raise HTTPException(status_code=404, detail="Activity not found")
    if status == "already_signed":
        raise HTTPException(status_code=400, detail="Student is already signed up")
    if status == "full":
        raise HTTPException(status_code=400, detail="Activity is full")
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity (persistent)."""
    participant, status = db.unregister_from_activity(activity_name, email)
    if status == "not_found":
        raise HTTPException(status_code=404, detail="Activity not found")
    if status == "not_signed":
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")
    return {"message": f"Unregistered {email} from {activity_name}"}
