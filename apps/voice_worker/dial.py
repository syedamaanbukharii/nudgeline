import asyncio
import os
import sys
from dotenv import load_dotenv
from livekit import api

# Load environment variables
load_dotenv()

async def dial_outbound(target_phone_number: str):
    """
    Triggers an outbound SIP call using LiveKit API.
    The LiveKit SIP Trunk (e.g. Twilio) will dial the target_phone_number.
    Once connected, it will join the specified LiveKit room.
    The local voice_worker should be listening to that same room.
    """
    # Requires LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET in environment
    livekit_client = api.LiveKitAPI()
    
    sip_trunk_id = os.getenv("LIVEKIT_SIP_TRUNK_ID")
    if not sip_trunk_id:
        print("❌ Error: LIVEKIT_SIP_TRUNK_ID is not set in .env")
        sys.exit(1)

    room_name = f"outbound-call-{target_phone_number.strip('+')}"
    
    print(f"📞 Dispatching call to {target_phone_number} via SIP Trunk {sip_trunk_id}...")
    
    try:
        # Create the SIP Participant (this initiates the dial out)
        await livekit_client.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=sip_trunk_id,
                sip_call_to=target_phone_number,
                room_name=room_name,
                participant_identity=f"prospect_{target_phone_number}",
                participant_name="Prospect",
            )
        )
        print(f"✅ Success! Call initiated.")
        print(f"➡️ Make sure your Python LiveKit Voice Agent is running and listening for room: '{room_name}'")
        
    except Exception as e:
        print(f"❌ Failed to initiate call: {e}")
        
    finally:
        await livekit_client.aclose()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dial.py <phone_number>")
        print("Example: python dial.py +15551234567")
        sys.exit(1)
        
    number = sys.argv[1]
    asyncio.run(dial_outbound(number))
