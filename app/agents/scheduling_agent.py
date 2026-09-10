import logging
from app.calendar_service import get_free_slots

logger = logging.getLogger(__name__)


def propose_interview_slots(candidate_name: str, job_title: str) -> dict:
    try:
        slots = get_free_slots()
    except Exception as e:
        logger.warning("Could not fetch real calendar availability: %s", e)
        slots = []

    if not slots:
        return {
            "proposed_slots": [],
            "message": f"Could not find any free calendar slots for {candidate_name}. Please schedule manually.",
        }

    return {
        "proposed_slots": slots,
        "message": f"Here are the next available interview slots for {candidate_name} ({job_title}), based on the actual calendar.",
    }


def build_confirmation_message(candidate_name: str, job_title: str, confirmed_time: str) -> str:
    
    return (
        f"Dear {candidate_name},\n\n"
        f"We're pleased to confirm your interview for the {job_title} position "
        f"on {confirmed_time}.\n\n"
        f"We look forward to speaking with you.\n\n"
        f"Best regards"
    )