import asyncio
import os
import sys

from livekit import rtc


async def main() -> None:
    if len(sys.argv) < 2:
        print("usage: echo_bot.py <BOT_JWT>", file=sys.stderr)
        sys.exit(2)

    url = os.environ.get("LIVEKIT_URL", "ws://localhost:7880")
    token = sys.argv[1]

    room = rtc.Room()

    @room.on("data_received")
    def on_data(packet: rtc.DataPacket) -> None:
        print(f"RECV from={packet.participant.identity} kind={packet.kind} topic={packet.topic} {packet.data.hex()}")
        asyncio.create_task(
            room.local_participant.publish_data(packet.data, reliable=True, topic=packet.topic)
        )

    await room.connect(url, token)
    print(f"Echo bot connected as identity={room.local_participant.identity}. Ctrl-C to exit.")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
