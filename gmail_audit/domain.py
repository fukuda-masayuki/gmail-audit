"""Domain extraction helpers and models."""

from __future__ import annotations

import email.utils
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import tldextract


@dataclass
class DomainRecord:
    domain: str
    count: int = 0
    sample_from: str = ""
    sample_subject: str = ""


def _get_header_value(headers: List[Dict[str, str]], name: str) -> Optional[str]:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value")
    return None


def _extract_email_address(raw_address: str) -> Optional[str]:
    _display, email_addr = email.utils.parseaddr(raw_address)
    if "@" not in email_addr:
        return None
    return email_addr


def extract_domain_from_headers(headers: List[Dict[str, str]]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    reply_to = _get_header_value(headers, "Reply-To")
    from_ = _get_header_value(headers, "From")
    subject = _get_header_value(headers, "Subject")

    address_source = reply_to or from_
    if not address_source:
        return None, from_, reply_to, subject

    email_addr = _extract_email_address(address_source)
    if not email_addr:
        return None, from_, reply_to, subject

    domain_part = email_addr.split("@", 1)[1].lower()
    extracted = tldextract.extract(domain_part)

    if not extracted.domain or not extracted.suffix:
        return None, from_, reply_to, subject

    normalized_domain = f"{extracted.domain}.{extracted.suffix}"
    return normalized_domain, from_, reply_to, subject
