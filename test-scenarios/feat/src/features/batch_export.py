"""Batch export capability sample."""

from __future__ import annotations

def introduce_batch_export(records: list[dict[str, str]]) -> list[str]:
    """Introduce batch export capability for selected records."""
    return [f"export:{record['id']}" for record in records if 'id' in record]

def add_archive_option(targets: list[str], archive_name: str) -> list[str]:
    """Add a new archive option for exported files."""
    return [f"{archive_name}/{target}" for target in targets]
