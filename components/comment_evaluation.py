import streamlit as st

def render_stage_a(comment: dict, saved: dict) -> dict:

    # Create the top
    st.markdown("## Stage A — Comment-level validation")

    saved = saved or {}
    options = ["Yes", "No", "Uncertain"]

    emotion_ok = st.radio(
        f"Is the overall emotion of this comment correctly labelled as **{comment.get('emotion') or 'not provided'}**",
        options, key=f"emotion_ok_{comment['comment_id']}",
        index=_index(options, saved.get("emotion_verdict")), horizontal=True,
    )

    stance_ok = st.radio(
        f"Is the comment's stance toward AI-generated advertising correctly labelled as **{comment.get('stance_label') or 'not provided'}**",
        options, key=f"stance_ok_{comment['comment_id']}",
        index=_index(options, saved.get("stance_verdict")), horizontal=True,
    )

    relation_ok = st.radio(
        f"Is the comment's relation to its parent comment correctly labelled as **{comment.get('relation_label') or 'not provided'}**",
        options, key=f"relation_ok_{comment['comment_id']}",
        index=_index(options, saved.get("relation_verdict")), horizontal=True,
    )

    reasoning = st.text_area(
        "Brief reasoning / notes (if any)", value=saved.get("reasoning", ""),
        key=f"stage_a_reason_verdict",
        placeholder="Explain the reason for any correction, uncertainty, or unusual case.",
    )

    return {
        "emotion": comment.get('emotion'),
        "stance": comment.get('stance_label'),
        "relation_parent": comment.get('relation_label'),
        "comment_source": comment.get('source'),
        "emotion_verdict": emotion_ok, 
        "stance_verdict": stance_ok, 
        "relation_verdict": relation_ok, 
        "reasoning": reasoning.strip(),
    }


def _index(options: list, value):

    try:
        return options.index(value)
    except ValueError:
        return None
