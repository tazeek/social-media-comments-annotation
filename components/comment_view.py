import json
import streamlit as st


def render_comment(comment: dict) -> list[dict]:

    st.markdown(f"### Comment `{comment['comment_id']}`")

    parent_text = comment.get("parent_text") or "No parent comment available."
    st.markdown("**Parent comment / context**")
    st.info(f"{parent_text}")

    st.markdown("**Comment to be evaluated**")
    st.info(comment["post_comment"] or "[Comment text unavailable]")

    # Parse the pairs
    aspect_pairs = comment['aspects']

    with st.expander("Comment label information", expanded=True):

        left, right = st.columns(2)

        with left:
            st.markdown(f"**Overall emotion:** {comment.get('emotion') or 'Not provided'}")
            st.markdown(f"**AI stance:** {comment.get('stance_label') or 'Not provided'}")
            st.markdown(f"**Parent relation:** {comment.get('relation_label') or 'Not provided'}")

        with right:

            st.markdown("**Aspect–emotion pairs:**")
            if not aspect_pairs:
                st.caption("No pairs found from the comment.")

            for i, pair in enumerate(aspect_pairs, 1):
                st.markdown(f"{i}. **{pair['aspect']}** — {pair['emotion']}")
                if pair["evidence"]:
                    st.caption(f"**Evidence**: “{pair['evidence']}”")

    return aspect_pairs
