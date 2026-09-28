from typing import Protocol

class LineTypePort(Protocol):
    async def lookup_line_type(self, phone_number: str) -> str:
        """
        Lookup the line type (e.g. mobile, landline, voip) for a given phone number.
        """
        ...
