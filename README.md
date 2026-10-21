# Reddit AI-generated-ad annotation platform

A Streamlit prototype for human validation of LLM annotations on Reddit comments about AI-generated advertisements. It uses MongoDB Atlas for persistent per-annotator progress and sends the final JSON snapshot as an email attachment.

## 1. Project layout

```text
reddit_annotation/
├── app.py                       # Streamlit entry point, login, navigation, workflow
├── requirements.txt             # Python dependencies
├── comments.csv                 # Small demo dataset; replace with your real data
├── .gitignore
├── .streamlit/
│   ├── config.toml              # Optional UI theme
│   └── secrets.toml.example     # Copy to secrets.toml and fill in credentials
├── components/
│   ├── navigation.py            # Searchable comment selector and progress indicators
│   ├── comment_view.py          # Reddit comment + parent context + LLM predictions
│   ├── comment_evaluation.py    # Stage A: comment-level emotion, stance, relation
│   └── pair_evaluation.py       # Stage B: validate aspect–emotion pairs
├── services/
│   ├── database.py              # MongoDB read/write/finalize/email-status operations
│   ├── annotation_service.py    # Annotation structure, validation and completion checks
│   └── email_service.py         # Email final JSON as an attachment
└── utils/
    └── config.py                # Secrets and data-loading helpers
```

## 2. Setup

1. Install Python 3.10+.
2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   # Windows: .venv\\Scripts\\activate
   # macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Create a MongoDB Atlas cluster and database user. Add your deployment host to the cluster's Network Access allowlist. For Streamlit Community Cloud, follow Atlas's guidance for a secure deployment/network setup; do not leave a broad IP allowlist enabled longer than necessary.
4. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, then fill in MongoDB, annotator credentials, and SMTP values. **Never commit `secrets.toml` to Git.**
5. Replace `comments.csv` with the real dataset (schema below).
6. Run locally:

   ```bash
   streamlit run app.py
   ```

## 3. Dataset schema

Required CSV columns:

- `comment_id`: unique, stable identifier for each Reddit comment.
- `comment_text`: comment being annotated.
- `parent_text`: parent comment text; blank if unavailable.
- `llm_emotion`: predicted overall emotion label.
- `llm_stance`: predicted stance toward AI use in the ad.
- `llm_relation`: predicted relationship to the parent comment.
- `llm_pairs`: JSON array encoded as a string. Each item should contain `aspect`, `emotion`, and optionally `evidence`. Example:

  ```json
  [{"aspect":"Realism","emotion":"negative","evidence":"looks completely fake"}]
  ```

The sample `comments.csv` contains only synthetic/demo examples. It is not research data.

## 4. Annotation flow

- Annotators sign in with an ID/password configured in Streamlit secrets.
- Each comment has Stage A (overall emotion, AI stance, parent-comment relation) and Stage B (each predicted aspect–emotion pair, with corrected values and evidence when needed).
- Predictions remain visible beside the validation controls.
- Draft progress is saved to MongoDB when navigating, saving, or moving between comments.
- The app prevents marking a comment complete until all required fields and each predicted pair's decision have been provided.
- Submission is written to MongoDB before the email is sent. Email failure does not delete the submission; a completed annotator can retry email delivery.
- The unique MongoDB key is `user_id`, matching the login ID. Each annotator session only loads/updates its own document.

## 5. Important configuration notes

- Update the choice lists and wording in `components/comment_evaluation.py` and `components/pair_evaluation.py` to match your final annotation protocol before recruiting annotators. Current choices are illustrative defaults.
- This is a controlled-study prototype. Passwords are stored as values in Streamlit secrets, so use unique strong passwords, share them privately, and do not reuse personal credentials. For larger or higher-risk studies, use a proper identity provider and hashed credentials.
- MongoDB documents store both the editable annotation map and a final submission snapshot. With 200–300 comments this should normally be manageable, but MongoDB has a 16 MB document limit; avoid storing full source data or large blobs in each document.
- Email delivery uses SMTP STARTTLS. For Gmail, use an app password where applicable, not your normal account password.
- Email is best-effort. A network timeout can occur after the mail server accepted a message, so a retry could result in a duplicate email. The database submission itself is protected from being finalized twice.
- Test with demo data and test annotator accounts first. This code has been assembled as a complete starter project, but it has not been run against your Atlas cluster or your final annotation wording.

## 6. MongoDB document shape

```json
{
  "user_id": "annotator01",
  "annotations": {"comment_id_1": {"stage_a": {}, "pairs": []}},
  "status": "in_progress",
  "final_submission": null,
  "submitted_at": null,
  "email_status": "not_sent"
}
```

After submission, `final_submission` contains an immutable snapshot of the submitted annotations and `status` becomes `completed`.
