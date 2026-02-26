import asyncio
import httpx
from collections import Counter

URL = "http://localhost:8000/bookings"

SEAT_ID = "c5ce1b9b-9227-49ba-abbc-012eecf17c5d"
BOOKING_DATE = "2026-03-01"

# Replace with 50 real employee JWT tokens
TOKENS = [
    "USER_TOKEN_1",
    "USER_TOKEN_2",
    "USER_TOKEN_3",
]

payload = {
    "seat_id": SEAT_ID,
    "booking_date": BOOKING_DATE
}


async def book_seat(client, token, index):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = await client.post(URL, json=payload, headers=headers)
        print(f"[User {index}] → {response.status_code}")
        return response.status_code
    except Exception as e:
        print(f"[User {index}] → ERROR: {str(e)}")
        return "error"


async def main():
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [
            book_seat(client, token, idx)
            for idx, token in enumerate(TOKENS, start=1)
        ]

        results = await asyncio.gather(*tasks)

        print("\n========== RESULT SUMMARY ==========")
        counts = Counter(results)
        for status, count in counts.items():
            print(f"{status} → {count} times")


if __name__ == "__main__":
    asyncio.run(main())