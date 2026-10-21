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
    path = Path("test.json")

    if not path.exists():
        raise FileNotFoundError(f"Could not find {path.resolve()}")

    all_comments = []
    with open(f'test.json', "r", encoding="utf-8") as f:
        all_comments = json.load(f) 

    # Convert to Dataframe and add the ID
    df = pd.DataFrame(all_comments)
    df["comment_id"] = [f"ANN_{i}" for i in range(1, len(df) + 1)]

    return df.to_dict(orient="records")
