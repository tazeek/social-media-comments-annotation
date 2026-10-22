import uuid
from datetime import datetime, timezone

import streamlit as st

from components.comment_evaluation import render_stage_a
from components.comment_view import render_comment
from components.navigation import render_navigation
from components.pair_evaluation import render_pair_validation
from services.annotation_service import (
    build_final_submission, completed_count, get_comment_annotation, is_comment_complete,
)
from services.database import (
    finalize_submission, get_final_submission, load_progress, save_progress, update_email_status,
)
from services.email_service import send_submission_email
from utils.config import authenticate, load_comments_json

st.set_page_config(page_title="Reddit AI-Ad Annotation", page_icon="🗂️", layout="wide")

@st.dialog("Aspect Definition Guideline")
def show_annotation_help():
    definitions = {
        "Realism": (
            "Evaluates how realistic, natural, and consistent the ad looks "
            "and sounds, including visual glitches, unnatural movements "
            "or faces, inconsistent objects, and awkward audio."
        ),
        "Visual Centric": (
            "Evaluates the ad's visual qualities, including style, color, "
            "lighting, composition, animation, camera work, detail, "
            "and visual polish."
        ),
        "Authenticity": (
            "Evaluates whether the ad feels human-made, creative, skillful, "
            "or soulful, including comparisons between AI and human artistry "
            "or traditional production."
        ),
        "Labor & Employability": (
            "Evaluates concerns or opinions about AI replacing human workers, "
            "causing job losses, changing industries, or making human labor "
            "unnecessary or less efficient."
        ),
        "Corporate Motives": (
            "Evaluates the company's perceived intentions and priorities in "
            "using AI, including greed, laziness, cutting corners, and "
            "prioritizing profits over quality or people."
        ),
        "Cost & Efficiency": (
            "Evaluates the financial and operational benefits or drawbacks "
            "of using AI, including production costs, savings, speed, budgets, "
            "and return on investment."
        ),
        "Transparency & Detectability": (
            "Evaluates whether AI use is disclosed honestly and whether "
            "audiences can identify AI-generated content, including concerns "
            "about deception, misleading advertising, and missing disclosures."
        ),
        "Brand Perception": (
            "Evaluates how the ad influences the brand's reputation, identity, "
            "heritage, trust, and relationship with its audience, including "
            "intentions to boycott or continue supporting the brand."
        ),
        "AI Capability": (
            "Evaluates AI's technical and creative abilities, limitations, "
            "accessibility, and improvement, including its capacity to produce "
            "compelling stories, humor, or coherent content."
        ),
        "Use-case Appropriateness": (
            "Evaluates whether using AI is suitable for the ad's purpose, "
            "message, or product, including whether AI fits emotional, "
            "creative, practical, or social contexts."
        ),
        "Societal & Ethical Implications": (
            "Evaluates broader ethical, legal, and societal consequences of AI, "
            "including copyright, training data, misinformation, regulation, "
            "and impacts on culture and society."
        ),
        "General Reaction": (
            "Captures an overall reaction to the ad without identifying a "
            "specific aspect, such as general praise, criticism, surprise, "
            "or amusement."
        ),
        "N/A": (
            "Applies to comments unrelated to AI-generated ads or content, "
            "including bot messages, deleted-comment placeholders, gibberish, "
            "or off-topic discussion."
        ),
    }

    for aspect, definition in definitions.items():
        st.markdown(f"**{aspect}**")
        st.write(definition)
        st.divider()

    if st.button("Close", use_container_width=True):
        st.rerun()

def show_stance_information():

    st.markdown("# Definition of Stance and Parent Relation labels")

    st.markdown("### AI Stance")
    st.markdown("""
    - **Favor:** Supports or welcomes the use of AI in this context.
    - **Against:** Criticizes or opposes the use of AI in this context.
    - **Neutral:** Discusses AI without taking a clear position.
    - **None:** Does not engage with AI (e.g., discusses only the product or is off-topic).
    """)

    st.markdown("### Relation to Parent Comment")
    st.markdown("""
    - **Agree:** Supports or reinforces the parent's point.
    - **Disagree:** Challenges or contradicts the parent's point.
    - **Neutral:** Responds without clearly agreeing or disagreeing.
    - **Unrelated:** Does not meaningfully engage with the parent's point.
    - **Not applicable:** No parent comment is provided.
    """)

    return None

def find_next_incomplete(comments, annotations, current_index):

    for idx, comment in enumerate(comments):
        comment_id = comment["comment_id"]
        state = annotations.get(comment_id, {})

        if not state.get("completed", False):
            return idx

    # All comments are completed so we stay on the current page
    return current_index

def init_state():
    defaults = {"active_annotator": None, "progress": None, "current_index": 0, "login_error": ""}

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def login_screen():
    st.title("Social Media Comment Annotation")
    st.markdown("## Welcome Back!")

    st.markdown("""
    Thank you for participating in this annotation exercise again.

    In this round, you will review comments from social media platforms. Each comment has been labelled with the following:

    - **Overall emotion:** The emotion conveyed by the comment as a whole.
    - **AI stance:** The comment's stance toward AI-generated advertising.
    - **Relation to parent comment:** How the comment relates to its parent comment, if one is provided.
    - **Aspect-emotion pairs:** The aspects discussed in the comment and the emotions associated with each aspect.

    We would appreciate your help in evaluating these labels based on your own interpretation of each comment. There are no right or wrong answers in terms of personal opinion; we are interested in your independent assessment of whether the labels accurately represent the comments.

    Thank you for your time and contribution!
    """)

    comments = None

    with st.form("login_form"):
        st.write("Sign in with the annotator ID and password provided")
        user_id = st.text_input("Annotator ID", autocomplete="username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)

    if submitted:
        if authenticate(user_id.strip(), password):

            try:
                progress = load_progress(user_id.strip())
            except Exception as exc:
                st.error(f"Could not connect to the annotation database: {exc}")
                return
            
            st.session_state.active_annotator = user_id.strip()
            st.session_state.progress = progress

            st.rerun()
        else:
            st.error("The annotator ID or password is incorrect.")

    return comments


def persist_current(show_success: bool = False):

    # For saving progress
    user_id = st.session_state.active_annotator
    progress = st.session_state.progress

    if not user_id or not progress or progress.get("status") == "completed":
        return
    
    save_progress(user_id, progress)

    if show_success:
        st.success("Progress saved to the database.")


def attempt_email(final_json: dict):
    user_id = st.session_state.active_annotator

    try:
        send_submission_email(user_id, final_json["submission_reference"], final_json)
        update_email_status(user_id, "sent")

        st.session_state.progress["email_status"] = "sent"
        st.success("Final JSON emailed to the researcher.")

    except Exception as exc:

        update_email_status(user_id, "failed")
        st.session_state.progress["email_status"] = "failed"
        st.error(f"The submission is safely stored in MongoDB, but the email could not be confirmed: {exc}")


def submit_all(comments: list[dict]):
    user_id = st.session_state.active_annotator
    progress = st.session_state.progress

    # Check if completed
    count = completed_count(comments, progress["annotations"])

    if count != len(comments):
        st.error(f"Please complete all comments before submitting. Completed: {count}/{len(comments)}.")
        return

    # Prepare the final submission
    final_json = build_final_submission(
        user_id=user_id, comments=comments, annotations=progress["annotations"],
        submission_reference=str(uuid.uuid4()), submitted_at=datetime.now(timezone.utc).isoformat(),
    )

    # Send the submission
    try:
        saved = finalize_submission(user_id, final_json)
    except Exception as exc:
        st.error(f"Could not save the final submission: {exc}")
        return
    
    st.session_state.progress = saved
    snapshot = saved.get("final_submission")

    if not snapshot:
        st.error("The finalized JSON snapshot is missing from the database record.")
        return

    # Send the email
    if saved.get("email_status") != "sent":
        attempt_email(snapshot)

    st.rerun()


def retry_email():
    user_id = st.session_state.active_annotator
    snapshot = get_final_submission(user_id)
    if not snapshot:
        st.error("No finalized submission was found to email.")
        return
    attempt_email(snapshot)
    st.rerun()


def render_completed():

    progress = st.session_state.progress
    st.title("Submission completed")
    st.success("Your final annotation snapshot is stored in the database.")

    snapshot = progress.get("final_submission") or {}
    st.write(f"Submission reference: `{snapshot.get('submission_reference', 'Unavailable')}`")
    st.write(f"Email status: **{progress.get('email_status', 'unknown')}**")

    if progress.get("email_status") == "failed":
        if st.button("Retry email to researcher", type="primary"):
            retry_email()
    
    st.info("This account's submission is locked after final submission. Contact the researcher if a correction is needed.")
    if st.button("Sign out"):
        st.session_state.active_annotator = None
        st.session_state.progress = None
        st.session_state.current_index = 0
        st.rerun()


def render_app(comments: list[dict]):

    # Load the progress
    user_id = st.session_state.active_annotator
    progress = st.session_state.progress

    if progress.get("status") == "completed":
        render_completed()
        return

    # Load the annotations and display
    annotations = progress.setdefault("annotations", {})
    total = len(comments)
    done = completed_count(comments, annotations)

    st.title("Reddit AI-generated Ad Annotation")
    st.markdown(f"Signed in as `{user_id}`")
    st.progress(done / total, text=f"Completed {done} of {total} comments")

    if st.button("Submit all annotations", type="primary", use_container_width=True):
            submit_all(comments)

    # For the sidebar
    with st.sidebar:

        show_stance_information()

        # For annotation help
        if st.button("❓ Aspect Definition Help", use_container_width=True):
            show_annotation_help()

        st.divider()

        # For signing out
        if st.button("Sign out", use_container_width=True):
            try:
                persist_current()
            except Exception as exc:
                st.error(f"Could not save progress before signing out: {exc}")
                return
            
            st.session_state.active_annotator = None
            st.session_state.progress = None
            st.session_state.current_index = 0
            st.rerun()

    # Get the current index of the previous session
    index = st.session_state.current_index
    comment = comments[index]
    comment_id = str(comment["comment_id"])

    # Old annotations
    current_labels = get_comment_annotation(annotations, comment_id)
    predicted_pairs = render_comment(comment)

    # Saved annotations
    stage_a_saved = current_labels.get("stage_a", {})
    pair_saved = current_labels.get("pairs", [])
    missing_saved = current_labels.get("missing_pairs_feedback", "")

    with st.form(f"annotation_form_{comment_id}"):

        # Stage A: The comment-level evaluation
        stage_a = render_stage_a(comment, stage_a_saved)

        st.divider()

        # Stage B: The aspect-pair evaluation
        pair_results, missing_feedback = render_pair_validation(comment_id, predicted_pairs, pair_saved, missing_saved)

        # Save once all done
        save_clicked = st.form_submit_button("Save comment", type="primary", use_container_width=True)

        if save_clicked:

            # Prepare the database storage
            candidate = {
                "stage_a": stage_a,
                "pairs": pair_results,
                "missing_pairs_feedback": missing_feedback,
                "completed": False,
                "last_saved_at": datetime.now(timezone.utc).isoformat(),
            }

            # Check for completion
            incomplete = False
            
            if not is_comment_complete(candidate, predicted_pairs):
                st.error("This comment cannot be marked complete yet. Fill all required fields.")
                incomplete = True

            if not incomplete:

                candidate["completed"] = True

                # Save to the database
                annotations[comment_id] = candidate
                progress["annotations"] = annotations

                try:
                    save_progress(user_id, progress)
                    st.session_state.progress = progress
                    st.success("Comment saved to MongoDB.")

                    next_index = find_next_incomplete(comments, annotations, st.session_state.current_index)
                    st.session_state.current_index = next_index
                    st.rerun()

                except Exception as exc:
                    st.error(f"Could not save this comment: {exc}")


def main():

    init_state()

    # Otherwise: Login
    if not st.session_state.active_annotator:
        login_screen()
        return

    # Load the comments for global usage
    user_id = st.session_state.active_annotator
    comments = load_comments_json(st.secrets[user_id]['split'])

    # Get the next selected index
    st.session_state.current_index = find_next_incomplete(comments,st.session_state.progress['annotations'],0)

    # Check for active annotator from the database
    # Load the progress from what was completed
    if st.session_state.get("active_annotator") != st.session_state.get("progress", {}).get("user_id"):
        st.session_state.progress = load_progress(st.session_state.active_annotator)

    # Create the app layout
    render_app(comments)

if __name__ == "__main__":
    main()
