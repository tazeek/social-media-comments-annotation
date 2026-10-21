import streamlit as st


def render_navigation(comments: list[dict], annotations: dict, current_index: int) -> int:
    
    """Render a searchable, compact comment selector with completion indicators."""

    # For the searchbar
    st.subheader("Select a comment")

    # Show completion status for every comment.
    options = [
        f"{'✅' if annotations.get(comment['comment_id'], {}).get('completed') else '🟡'}  "
        f"{comment['comment_id']}"
        for comment in comments
    ]

    selected_pos = st.selectbox(
        "✅ complete · 🟡 incomplete",
        options=range(len(comments)),
        format_func=lambda pos: options[pos],
        index=current_index,
    )

    return selected_pos
