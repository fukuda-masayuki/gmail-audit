"""Post-processing pipeline to build a categorized sites catalog."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd
import yaml

from . import config


logger = logging.getLogger(__name__)

INPUT_COLUMNS: List[str] = ["domain", "count", "sample_from", "sample_subject"]
OPTIONAL_COLUMNS: List[str] = ["sample_list_id"]
OUTPUT_COLUMNS: List[str] = [
    "domain",
    "count",
    "sample_from",
    "sample_subject",
    "service_name",
    "category",
    "source",
    "notes",
]

NEWSLETTER_KEYWORDS: List[str] = ["newsletter", "unsubscribe", "メルマガ", "配信停止"]
TRANSACTION_KEYWORDS: List[str] = ["receipt", "invoice", "領収書", "ご注文", "配送", "shipped"]

CATEGORY_SAMPLE_TEMPLATE: Dict[str, str] = {
    "github.com": "developer",
    "amazon.co.jp": "shopping",
    "notion.so": "productivity",
}


def ensure_categories_file(path: Path) -> None:
    if path.exists():
        return

    logger.info("categories.yml が存在しないため雛形を生成します: %s", path)
    path.write_text(
        yaml.safe_dump(
            CATEGORY_SAMPLE_TEMPLATE,
            allow_unicode=True,
            sort_keys=True,
            default_flow_style=False,
        ),
        encoding="utf-8",
    )


def load_categories(path: Path) -> Dict[str, str]:
    ensure_categories_file(path)

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        logger.warning("categories.yml の読み込みに失敗しました: %s", exc)
        return {}
    except FileNotFoundError:
        return {}

    if not data:
        return {}
    if not isinstance(data, dict):
        logger.warning("categories.yml の形式が不正です (dict が必要)")
        return {}

    normalized: Dict[str, str] = {}
    for domain, category in data.items():
        if not isinstance(domain, str) or not isinstance(category, str):
            continue
        domain_key = domain.strip().lower()
        if not domain_key:
            continue
        normalized[domain_key] = category.strip()
    return normalized


def read_sites_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        logger.warning("入力ファイル %s が存在しません", path)
        return pd.DataFrame(columns=INPUT_COLUMNS + OPTIONAL_COLUMNS)

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        logger.warning("入力ファイル %s が空でした", path)
        return pd.DataFrame(columns=INPUT_COLUMNS + OPTIONAL_COLUMNS)

    missing = [col for col in INPUT_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"sites_from_gmail.csv に必要な列が不足しています: {missing}")

    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    return df


def guess_service_name(domain: str) -> str:
    if not isinstance(domain, str) or not domain:
        return ""

    host = domain.split(".")[0]
    host = host.replace("_", " ").replace("-", " ")
    parts = [part.capitalize() for part in host.split() if part]
    if parts:
        return " ".join(parts)
    return domain.capitalize()


def _contains_keyword(subject: str, keywords: Iterable[str]) -> bool:
    subject_lower = subject.lower()
    for keyword in keywords:
        if keyword.isascii():
            if keyword.lower() in subject_lower:
                return True
        else:
            if keyword in subject:
                return True
    return False


def detect_category(row: pd.Series, categories: Dict[str, str]) -> Tuple[str, str]:
    domain = str(row.get("domain", "") or "").lower()
    subject = str(row.get("sample_subject", "") or "")
    list_id = str(row.get("sample_list_id", "") or "")

    if domain and domain in categories:
        return categories[domain], "dict"

    if list_id.strip():
        return "newsletter", "rule"

    if _contains_keyword(subject, NEWSLETTER_KEYWORDS):
        return "newsletter", "rule"

    if _contains_keyword(subject, TRANSACTION_KEYWORDS):
        return "transaction", "rule"

    return "unknown", "unknown"


def build_catalog_df(df_sites: pd.DataFrame, categories: Dict[str, str]) -> pd.DataFrame:
    if df_sites.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    rows: List[Dict[str, str]] = []
    for record in df_sites.to_dict(orient="records"):
        domain = str(record.get("domain", ""))
        category, source = detect_category(pd.Series(record), categories)
        rows.append(
            {
                "domain": domain,
                "count": record.get("count", 0),
                "sample_from": record.get("sample_from", ""),
                "sample_subject": record.get("sample_subject", ""),
                "service_name": guess_service_name(domain),
                "category": category,
                "source": source,
                "notes": "",
            }
        )

    catalog_df = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    return catalog_df.sort_values(by=["category", "domain", "service_name"]) if not catalog_df.empty else catalog_df


def save_catalog_csv(df: pd.DataFrame, path: Path) -> None:
    if df.empty:
        pd.DataFrame(columns=OUTPUT_COLUMNS).to_csv(path, index=False)
        logger.info("%s を出力しました (行数=0)", path)
        return

    df.to_csv(path, index=False)
    logger.info("%s を出力しました (行数=%d)", path, len(df))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

    sites_path = config.OUTPUT_CSV_PATH
    catalog_path = config.SITES_CATALOG_CSV_PATH
    categories_path = config.CATEGORIES_YAML_PATH

    df_sites = read_sites_csv(sites_path)
    categories = load_categories(categories_path)
    catalog_df = build_catalog_df(df_sites, categories)
    save_catalog_csv(catalog_df, catalog_path)


if __name__ == "__main__":
    main()
