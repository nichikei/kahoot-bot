#!/usr/bin/env python3
"""
Kahoot Answer Bot - Dễ dùng
Chạy: python run_bot.py
"""

import asyncio
import random
import string
import sys
import re
import klib


def random_nick(base="bot"):
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"{base}{suffix}"


def check_uuid(qID):
    res = re.search(r"(([a-zA-Z0-9]){8}(-([a-zA-Z0-9]){4}){3}-([a-zA-Z0-9]){12})", qID)
    if not res:
        print("❌ Quiz ID không hợp lệ!")
        sys.exit(1)
    return res.group(1)


def run(pin, quiz_id=None, nickname=None, debug=False):
    if nickname is None:
        nickname = random_nick()
    print(f"\n{'='*45}")
    print(f"  🎮 KAHOOT BOT")
    print(f"{'='*45}")
    print(f"  PIN       : {pin}")
    print(f"  Nickname  : {nickname}")
    print(f"  Quiz ID   : {quiz_id if quiz_id else '(tự động lấy từ PIN)'}")
    print(f"{'='*45}\n")

    if not debug:
        sys.tracebacklimit = 0

    try:
        bot = klib.Kahoot(pin=pin, nickname=nickname, quizID=quiz_id, DEBUG=debug)
        print("🔍 Đang kiểm tra game PIN...")
        bot.checkPin()
        print("✅ Game hợp lệ! Đang vào lobby...")
        bot.startGame()
    except klib.KahootError as e:
        msg = str(e)
        if "Duplicate name" in msg:
            # Tự động thử lại với nickname khác
            new_nick = random_nick()
            print(f"\n⚠️  Nickname '{nickname}' đã tồn tại → đổi thành '{new_nick}', thử lại...")
            run(pin, quiz_id, new_nick, debug)
        elif "Player not found" in msg:
            print("\n❌ Không tìm thấy người chơi. Game PIN đã hết hạn hoặc host đã đóng phòng.")
            print("   → Hãy tạo game mới và nhập PIN mới.\n")
        elif "does not exist" in msg:
            print(f"\n❌ PIN '{pin}' không tồn tại hoặc đã hết hạn.\n")
        else:
            print(f"\n❌ Lỗi: {msg}\n")
    except (KeyboardInterrupt, asyncio.exceptions.CancelledError):
        print("\n👋 Đã thoát bot.\n")
    except Exception as e:
        print(f"\n❌ Lỗi không xác định: {type(e).__name__}: {e}\n")
        if debug:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("\n╔══════════════════════════════════════════╗")
    print("║        KAHOOT ANSWER BOT  🤖             ║")
    print("╚══════════════════════════════════════════╝\n")

    # Nhận thông tin đầu vào
    if len(sys.argv) >= 2:
        # Lọc bỏ --debug khỏi args
        debug = "--debug" in sys.argv
        args = [a for a in sys.argv[1:] if a != "--debug"]
        pin = args[0].replace(" ", "") if len(args) >= 1 else None
        quiz_id = check_uuid(args[1]) if len(args) >= 2 else None
        nickname = args[2] if len(args) >= 3 else random_nick()
        if not pin:
            pin = input("🔢 Nhập Game PIN: ").strip().replace(" ", "")
    else:
        pin = input("🔢 Nhập Game PIN: ").strip().replace(" ", "")
        quiz_id_raw = input("🆔 Nhập Quiz ID (Enter để tự động): ").strip()
        quiz_id = check_uuid(quiz_id_raw) if quiz_id_raw else None
        nick_input = input("👤 Nhập nickname (Enter để random): ").strip()
        nickname = nick_input if nick_input else random_nick()
        debug = input("🐛 Debug mode? [y/N]: ").strip().lower() == 'y'

    run(pin, quiz_id, nickname, debug)
