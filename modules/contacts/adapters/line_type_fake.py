from modules.contacts.ports.line_type import LineTypePort

class FakeLineTypeAdapter(LineTypePort):
    async def lookup_line_type(self, phone_number: str) -> str:
        if phone_number.startswith("+1202"):
            return "landline"
        return "mobile"
