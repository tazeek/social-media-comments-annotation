import streamlit as st

ASPECTS = [
    "Realism", "Narrative & Creativity", "Authenticity / Human Touch & Craft",
    "Labor", "Corporate Motives", "Cost / Efficiency", "Product / Brand",
    "Audience Response", "Other", "Not an aspect",
]
EMOTIONS = ["positive", "negative", "neutral", "mixed", "other"]


def render_pair_validation(comment_id: str, predicted_pairs: list[dict], saved_pairs: list[dict], saved_missing_feedback: str = "") -> tuple[list[dict], str]:
    """Stage B: validate each predicted pair and capture omitted pairs."""

    # Create the titles
    st.markdown("## Stage B — Aspect–emotion pair validation")
    st.caption("Validate each predicted pair separately. Use the evidence field to assess whether the pair is grounded in the comment.")

    saved_pairs = saved_pairs or []
    results = []

    options = ["Yes", "No", "Uncertain"]

    if not predicted_pairs:
        st.info("The LLM predicted no aspect–emotion pairs. Please still consider whether any pair is missing below.")

    for idx, pair in enumerate(predicted_pairs):

        old = saved_pairs[idx] if idx < len(saved_pairs) else {}

        # Add in the pair
        with st.container(border=True):

            # Display the information
            st.markdown(f"**Aspect-Emotion Pair #{idx + 1}**")
            st.markdown(f"Aspect: **{pair['aspect']}** · Emotion: **{pair['emotion']}**")
            st.markdown(f"Evidence from the comment: _{pair['evidence']}_")

            # Add the buttons
            aspect_ok = st.radio(
                f"Is the aspect of the comment accurate?",
                options, key=f"aspect_verdict_{comment_id}_{idx}",
                index=_index(options, old.get("aspect_verdict")), horizontal=True,
            )

            emotion_ok = st.radio(
                f"Is the emotion of the given aspect accurate?",
                options, key=f"emotion_verdict_{comment_id}_{idx}",
                index=_index(options, old.get("emotion_verdict")), horizontal=True,
            )

            note = st.text_input(
                "Optional note for this pair", value=old.get("note", ""),
                key=f"pair_note_{comment_id}_{idx}",
            )

            # Add to the array
            results.append({
                "aspect": pair["aspect"], 
                "emotion": pair["emotion"],
                "evidence": pair.get("evidence", ""), 
                "aspect_verdict": aspect_ok, 
                "emotion_verdict": emotion_ok,
                "note": note.strip(),
            })

    missing_feedback = st.text_area(
        "Identify any aspect–emotion pair missed (if any)",
        value=saved_missing_feedback, key=f"missing_pairs_{comment_id}",
        placeholder="Example: Missing pair — Corporate Motives / negative; evidence: they only did this to save money. Or: None.",
    )

    return results, missing_feedback.strip()


def _index(options: list, value):
    try:
        return options.index(value)
    except ValueError:
        return None
