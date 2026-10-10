"""Small, deterministic intent recognizers for English and Roman Urdu."""

import re
import unicodedata

from .knowledge import PAGE_CATALOG


def normalize_message(message):
    message = unicodedata.normalize('NFKC', message or '').lower()
    message = message.replace('\u2019', "'").replace('\u2018', "'")
    return re.sub(r'\s+', ' ', message).strip()


def is_roman_urdu(message):
    normalized = normalize_message(message)
    return bool(re.search(
        r'\b(kitne|kitni|naam|kya|kaise|dikhao|batao|kholo|khol|hai|hain|he|hen|mein|mujhe|karna|chahiye|kahan|wala|wali|ke|ki)\b',
        normalized,
    ))


def _clean_name(value):
    value = re.sub(r'[?!.,;:]+$', '', value.strip())
    value = re.sub(r'\s+(?:hain|hai|hen|he|h|please|batao|dikhao)$', '', value)
    value = re.sub(r'\s+', ' ', value).strip(" \t\n\r\"'.,?!")
    return value[:80]


def extract_student_name_lookup(message):
    """Extract a requested student name, e.g. 'Sami name ke kitne students?'"""
    text = normalize_message(message)
    name_pattern = r"(?P<name>[a-z0-9][a-z0-9 .'-]{0,78}?)"
    patterns = (
        rf'{name_pattern}\s+(?:naam|name)\s+(?:(?:ke|ki|kay|ka|k)\s+)?(?:kitne|kitni|how many)\s+(?:students?|talib(?:a|aat)?)\b',
        rf'{name_pattern}\s+(?:naam|name)\s+(?:(?:ke|ki|kay|ka|k)\s+)?(?:saare|saray|sari|all|list)\s+(?:students?|talib(?:a|aat)?)\b',
        rf'{name_pattern}\s+(?:ke|ki|kay)\s+(?:kitne|kitni)\s+(?:students?|talib(?:a|aat)?)\b',
        r'\b(?:students?|talib(?:a|aat)?)\s+(?:named|called|with name)\s+(?P<name>[a-z0-9][a-z0-9 .\'-]{0,78}?)(?:\s+(?:list|please|dikhao|batao)\b|[?!.,]|$)',
        r'\bhow many\s+(?:students?|talib(?:a|aat)?)\s+(?:named|called)\s+(?P<name>[a-z0-9][a-z0-9 .\'-]{0,78}?)(?:\s+(?:are|is|hai|hain|he|hen)\b|[?!.,]|$)',
        r'\b(?:students?|talib(?:a|aat)?)\s+(?:named|called)\s+(?P<name>[a-z0-9][a-z0-9 .\'-]{0,78}?)(?:\s+(?:name|naam|hai|hain|he|hen)\b|[?!.,]|$)',
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            name = _clean_name(match.group('name'))
            if name:
                return name
    return None


def is_student_count_question(message):
    text = normalize_message(message)
    is_count_question = bool(re.search(
        r'\b(?:how many|count|kitne|kitni)\b.*\b(?:students?|talib(?:a|aat)?)\b',
        text,
    ))
    asks_for_a_breakdown = bool(re.search(
        r'\b(absent|present|late|class|section|grade|wing|campus|fee|payment|name|naam|profile|record)\b',
        text,
    ))
    return is_count_question and not asks_for_a_breakdown


def is_school_data_question(message):
    """Prevent private operational questions from reaching an external LLM."""
    text = normalize_message(message)
    mentions_school_data = bool(re.search(
        r'\b(student|students|talib|taliba|fee|fees|payment|receipt|attendance|hazri|hajri|staff|teacher|class|section|leave|chutti|stock|inventory|guardian|parent|defaulter|salary|profile|record|detail|naam|name)\w*\b',
        text,
    ))
    requests_records = bool(re.search(
        r'\b(how many|how much|count|kitne|kitni|list|find|search|who|which|show|dikhao|pending|overdue|absent|present|late|paid|balance|marks|profile|details|record|records|kaun|kis)\b',
        text,
    ))
    return mentions_school_data and requests_records


def is_navigation_request(message):
    return bool(re.search(
        r'\b(open|go to|take me|navigate|mark|manage|kholo|khol|dikhao|where is|kahan)\b',
        normalize_message(message),
    ))


def find_page_intent(message, pages):
    text = normalize_message(message)
    candidates = []
    enabled_by_key = {page['key']: page for page in pages}
    for page in PAGE_CATALOG:
        for alias in page['aliases']:
            normalized_alias = normalize_message(alias)
            if normalized_alias and re.search(
                rf'(?<!\w){re.escape(normalized_alias)}(?!\w)', text
            ):
                candidates.append((len(normalized_alias), page))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return enabled_by_key.get(candidates[0][1]['key'])
