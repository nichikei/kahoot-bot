"""Test xem Kahoot session response trả về những gì"""
import requests, json, time, sys

pin = sys.argv[1] if len(sys.argv) > 1 else input("PIN: ").strip()
url = f"https://play.kahoot.it/reserve/session/{pin}/?{int(time.time())}"
print(f"GET {url}")
resp = requests.get(url)
print(f"Status: {resp.status_code}")
print(f"Headers: {dict(resp.headers)}")
if resp.status_code == 200:
    data = resp.json()
    # In tất cả keys (bỏ challenge vì quá dài)
    safe = {k: v for k, v in data.items() if k != 'challenge'}
    print(f"\nResponse keys: {list(data.keys())}")
    print(f"Response data (no challenge): {json.dumps(safe, indent=2, default=str)}")
    print(f"\nHas 'challenge': {'challenge' in data}")
    # Tìm bất kỳ field nào có 'quiz' hoặc 'id' trong tên
    quiz_fields = {k: v for k, v in data.items() if 'quiz' in k.lower() or 'id' in k.lower() or 'name' in k.lower()}
    print(f"\nFields liên quan quiz/id/name: {json.dumps(quiz_fields, indent=2, default=str)}")
else:
    print(f"Error: {resp.text}")
