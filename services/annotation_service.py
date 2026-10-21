from typing import Any


def get_comment_annotation(annotations: dict, comment_id: str) -> dict:

    # Get the annotation of the current comment
    return annotations.get(str(comment_id), {})


def is_comment_complete(annotation: dict, predicted_pairs: list[dict]) -> bool:


    # Check for Stage A
    stage_a = annotation.get("stage_a", {})
    required_a = ["emotion_verdict", "stance_verdict", "relation_verdict"]

    if any(not stage_a.get(key) for key in required_a):
        return False

    # Check for Stage B
    pairs = annotation.get("pairs", [])
    for pair in pairs:

        # Need both aspect and emotion
        if (not pair.get("aspect_verdict")) or (not pair.get("emotion_verdict")):
            return False
        
    return True


def completed_count(comments: list[dict], annotations: dict) -> int:

    # Find the number of comments completed
    return sum(bool(annotations.get(str(c["comment_id"]), {}).get("completed")) for c in comments)


def build_final_submission(user_id: str, comments: list[dict], annotations: dict, submission_reference: str, submitted_at: str) -> dict[str, Any]:
    
    return {
        "schema_version": "1.0",
        "annotator_id": user_id,
        "submission_reference": submission_reference,
        "submitted": True,
        "submitted_at": submitted_at,
        "total_comments": len(comments),
        "completed_comments": completed_count(comments, annotations),
        "annotations": annotations,
    }
