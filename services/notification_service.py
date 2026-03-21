import logging

logger = logging.getLogger(__name__)


def send_mock_email(email: str, code: str):
    logger.info("Verification code sent to %s", email)
    logger.debug("[MOCK EMAIL] To: %s, Code: %s", email, code)
