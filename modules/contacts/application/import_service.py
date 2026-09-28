"""CSV Import Service."""

from __future__ import annotations

import csv
import io
from typing import Any

import phonenumbers
from phonenumbers import timezone as pn_timezone

from modules.tenancy.domain.crypto import CryptoService


class CSVImportService:
    """Processes contact CSV imports."""

    @staticmethod
    def process_csv(
        csv_content: str,
        tenant_id: str,
        column_mappings: dict[str, str],
        default_region: str = "US",
    ) -> list[dict[str, Any]]:
        """Process a CSV file given column mappings."""
        results = []
        seen_hashes = set()
        
        reader = csv.DictReader(io.StringIO(csv_content))
        phone_col = column_mappings.get("phone_number")
        
        if not phone_col:
            raise ValueError("phone_number column mapping is required")
            
        for row in reader:
            raw_phone = row.get(phone_col)
            if not raw_phone:
                continue
                
            try:
                # Normalize phone number to E.164
                parsed_number = phonenumbers.parse(raw_phone, default_region)
                if not phonenumbers.is_valid_number(parsed_number):
                    continue
                e164_number = phonenumbers.format_number(
                    parsed_number, phonenumbers.PhoneNumberFormat.E164
                )
                
                # Infer timezone
                timezones = pn_timezone.time_zones_for_number(parsed_number)
                inferred_tz = timezones[0] if timezones and timezones[0] != "unknown" else "UTC"
                
                # Generate phone hash
                phone_hash_bytes = CryptoService.hash_value(e164_number, tenant_id)
                phone_hash = phone_hash_bytes.hex()
                
                # Deduplicate
                if phone_hash in seen_hashes:
                    continue
                seen_hashes.add(phone_hash)
                
                parsed_contact = {
                    "raw_phone": raw_phone,
                    "e164_number": e164_number,
                    "timezone": inferred_tz,
                    "phone_hash_hex": phone_hash,
                    "phone_hash": phone_hash_bytes,
                    "original_data": row
                }
                results.append(parsed_contact)
                
            except phonenumbers.NumberParseException:
                continue
                
        return results
