import logging

from . import config
from .aggregator import aggregate_domains
from .auth import get_credentials
from .gmail_client import GmailClient, build_gmail_service
from .output import save_to_csv


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    max_messages = config.get_env_int("MAX_MESSAGES", 500)
    logger.info("MAX_MESSAGES=%d", max_messages)

    creds = get_credentials()
    service = build_gmail_service(creds)
    client = GmailClient(service)

    message_ids = client.list_message_ids(max_messages)
    if not message_ids:
        logger.info("検索条件に一致するメッセージがありませんでした")
        save_to_csv([], config.OUTPUT_CSV_PATH)
        return

    records = aggregate_domains(client, message_ids)
    if not records:
        logger.info("ドメインを抽出できませんでした")
        save_to_csv([], config.OUTPUT_CSV_PATH)
        return

    save_to_csv(records, config.OUTPUT_CSV_PATH)


if __name__ == "__main__":
    main()
