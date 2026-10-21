from pathlib import Path
import json

import pandas as pd
import streamlit as st

REQUIRED_COLUMNS = [
    "comment_id", "comment_text", "parent_text", "llm_emotion",
    "llm_stance", "llm_relation", "llm_pairs",
]


def authenticate(user_id: str, password: str) -> bool:

    if user_id not in st.secrets:
        return False

    real_password = st.secrets[user_id]['password']

    if real_password != password:
        return False

    return True

def load_comments_json():

    # Check for path
    path = Path("comments.json")

    if not path.exists():
        raise FileNotFoundError(f"Could not find {path.resolve()}")

    all_comments = []
    with open(f'comments.json', "r", encoding="utf-8") as f:
        all_comments = json.load(f) 

    # Convert to Dataframe and add the ID
    df = pd.DataFrame(all_comments)
    df["comment_id"] = [f"ANN_{i}" for i in range(1, len(df) + 1)]

    return df.to_dict(orient="records")


def load_comments(csv_path: str = "comments.csv") -> list[dict]:

    # Check for the path
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Could not find {path.resolve()}")

    # Load the file (Replace to JSON)
    df = pd.read_csv(path, dtype=str, keep_default_na=False)

    # Check for the columns
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]

    if missing:
        raise ValueError(f"comments.csv is missing required columns: {', '.join(missing)}")
    
    df = df[REQUIRED_COLUMNS]
    if df["comment_id"].duplicated().any():
        duplicate_ids = df.loc[df["comment_id"].duplicated(), "comment_id"].tolist()
        raise ValueError(f"comment_id values must be unique. Duplicates: {duplicate_ids[:10]}")
    
    if not len(df):
        raise ValueError("comments.csv has no rows.")
    
    return df.to_dict(orient="records")
