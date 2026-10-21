from datetime import datetime, timezone

import streamlit as st
from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError


@st.cache_resource
def get_collection():
    config = st.secrets["mongodb"]
    client = MongoClient(config["uri"], serverSelectionTimeoutMS=10000, connectTimeoutMS=10000)
    client.admin.command("ping")

    collection = client[config["database"]][config["collection"]]
    collection.create_index([("user_id", ASCENDING)], unique=True)

    return collection


def load_progress(user_id: str) -> dict:

    # Get the database connection
    collection = get_collection()

    # Find via the user ID
    document = collection.find_one({"user_id": user_id})

    # If no document -> create one instead
    if document is None:
        initial = {
            "user_id": user_id, "annotations": {}, "status": "in_progress",
            "final_submission": None, "submitted_at": None, "email_status": "not_sent",
            "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
        }

        # Insert new entry into the database
        try:
            collection.update_one({"user_id": user_id}, {"$setOnInsert": initial}, upsert=True)
        except DuplicateKeyError:
            # Another session for the same user created the record first.
            pass

        # Get the entry back
        document = collection.find_one({"user_id": user_id})

    if not document:
        raise RuntimeError("Could not load or initialize the annotator record.")
    
    document.pop("_id", None)
    
    return document


def save_progress(user_id: str, progress: dict) -> None:
    
    result = get_collection().update_one(
        {"user_id": user_id, "status": {"$ne": "completed"}},
        {"$set": {"annotations": progress.get("annotations", {}), "status": "in_progress", "updated_at": datetime.now(timezone.utc)}},
        upsert=False,
    )

    if result.matched_count == 0:
        raise ValueError("No editable submission exists for this user. It may already be completed.")


def finalize_submission(user_id: str, final_json: dict) -> dict:
    
    collection = get_collection()
    now = datetime.now(timezone.utc)

    # Update in MongoDB
    result = collection.update_one(
        {"user_id": user_id, "status": {"$ne": "completed"}},
        {"$set": {"status": "completed", "final_submission": final_json,
                  "submitted_at": now, "email_status": "pending", "updated_at": now}},
    )

    # Check if saved or not
    if result.matched_count == 0:
        existing = collection.find_one({"user_id": user_id})
        if existing and existing.get("status") == "completed":
            existing.pop("_id", None)
            return existing
        raise RuntimeError("Could not finalize the submission. Please try again or contact the researcher.")
    
    document = collection.find_one({"user_id": user_id})
    document.pop("_id", None)

    return document


def update_email_status(user_id: str, status: str) -> None:
    if status not in {"pending", "sent", "failed"}:
        raise ValueError("Invalid email status.")
    get_collection().update_one(
        {"user_id": user_id, "status": "completed"},
        {"$set": {"email_status": status, "updated_at": datetime.now(timezone.utc)}},
    )


def get_final_submission(user_id: str) -> dict | None:
    document = get_collection().find_one(
        {"user_id": user_id, "status": "completed"},
        {"_id": 0, "final_submission": 1},
    )
    return document.get("final_submission") if document else None
