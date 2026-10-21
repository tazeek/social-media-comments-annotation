import json
import streamlit as st

def parent_text_dilemma(comment):

    parent_text_nan = isinstance(comment.get('parent_text'), float)
    parent_id_nan = isinstance(comment.get('parent_id'), float)

    if (parent_text_nan) and (parent_id_nan):
        return "[None]"                          

    # Check: If parent_id exists but there is no parent_text
    if (not parent_id_nan) and (parent_text_nan):
        return '[Deleted|Removed]'

    return comment.get('parent_text')


def render_comment(comment: dict) -> list[dict]:

    st.markdown(f"### Comment `{comment['comment_id']}`")

    parent_text = parent_text_dilemma(comment)

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
