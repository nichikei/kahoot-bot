#!/usr/bin/env python3
"""
Kahoot Answer Bot - Playwright
Nhập PIN + Quiz UUID → tự động vào game và trả lời đáp án đúng.

Chạy: python pw_bot.py <PIN> <QUIZ_UUID> [nickname]
Ví dụ: python pw_bot.py 1466590 2ccff0a5-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        python pw_bot.py 1466590 2ccff0a5-xxxx-xxxx-xxxx-xxxxxxxxxxxx myname
"""

import sys
import re
import json
import time
import random
import string
import html
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout


# ── Helpers ──────────────────────────────────────────────────────────────────
NICKNAMES = ["Phạm Nhật Khánh", "Phạm Khánh", "Nhật Khánh"]

def random_nick():
    return random.choice(NICKNAMES)


def get_answers_by_id(quiz_id: str) -> list:
    """Lấy đáp án từ Kahoot API bằng Quiz UUID"""
    url = f"https://create.kahoot.it/rest/kahoots/{quiz_id}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️  API trả {resp.status_code} cho quiz {quiz_id}")
            return []
        quiz = resp.json()
        answers = []
        allowed = ["quiz", "multiple_select_quiz"]
        title = quiz.get("title", "?")
        print(f"\n📚 Quiz: {title}")
        print(f"   {len(quiz.get('questions', []))} câu hỏi\n")
        for q in quiz.get("questions", []):
            if q.get("type") not in allowed:
                answers.append(None)
                continue
            correct_idx = None
            correct_text = "?"
            for i, choice in enumerate(q.get("choices", [])):
                if choice.get("correct") and correct_idx is None:
                    correct_idx = i
                    correct_text = choice.get("answer", "?")
            answers.append({
                "question": q.get("question", ""),
                "index": correct_idx if correct_idx is not None else 0,
                "answer": correct_text,
            })
        for i, a in enumerate(answers):
            tag = a["answer"] if a else "[survey/slide]"
            print(f"  Câu {i+1}: {tag}")
        print()
        return answers
    except Exception as e:
        print(f"⚠️  Lỗi lấy đáp án: {e}")
        return []


COLORS = {0: "ĐỎ", 1: "XANH", 2: "VÀNG", 3: "LÁ"}


# ── Main Bot ─────────────────────────────────────────────────────────────────
def run_bot(pin: str, quiz_id: str, nickname: str, headless: bool = False, debug: bool = False):
    print(f"\n{'='*50}")
    print(f"  🎮 KAHOOT PLAYWRIGHT BOT")
    print(f"{'='*50}")
    print(f"  PIN       : {pin}")
    print(f"  Quiz ID   : {quiz_id}")
    print(f"  Nickname  : {nickname}")
    print(f"  Mode      : {'headless' if headless else 'visible'}")
    print(f"{'='*50}\n")

    # Lấy đáp án ngay từ UUID
    print("📥 Đang lấy đáp án từ Quiz ID...")
    answers = get_answers_by_id(quiz_id)
    if not answers:
        print("⚠️  Không lấy được đáp án, bot sẽ chọn ngẫu nhiên.")

    quiz_counter = 0
    game_over = False
    game_started = False

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--window-size=1280,800", "--disable-blink-features=AutomationControlled"]
        )
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = ctx.new_page()

        # ── Intercept WebSocket để theo dõi game state ──
        def on_ws(ws):
            def on_msg(payload):
                nonlocal game_over, game_started
                try:
                    if not isinstance(payload, str) or len(payload) < 10:
                        return
                    data_list = json.loads(payload)
                    if not isinstance(data_list, list):
                        return
                    for item in data_list:
                        if not isinstance(item, dict):
                            continue
                        chan = item.get("channel", "")
                        if debug:
                            data_str = json.dumps(item)
                            print(f"  [WS] {chan}: {data_str[:200]}")

                        inner = item.get("data", {})
                        if not isinstance(inner, dict):
                            continue

                        msg_id = inner.get("id", "")
                        if msg_id in (3, "3"):
                            game_over = True
                            print("\n🏆 [WS] Game Over detected!")
                        if msg_id in (9, "9"):
                            game_started = True
                            print("🚀 [WS] Game started!")
                        if msg_id in (10, "10"):
                            game_over = True
                            print("\n⚠️ [WS] Reset/Disconnect")
                except Exception:
                    pass

            ws.on("framereceived", lambda payload: on_msg(payload))

        page.on("websocket", on_ws)

        # ── Bước 1: Mở Kahoot ──
        print("🌐 Đang mở kahoot.it...")
        page.goto("https://kahoot.it/", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # ── Bước 2: Nhập PIN ──
        print(f"🔢 Đang nhập PIN: {pin}")
        try:
            pin_input = page.locator(
                'input[data-functional-selector="game-pin-input"], '
                'input[id="game-input"], '
                'input[name="gameId"], '
                'input[type="tel"], '
                'input[placeholder*="PIN" i], '
                'input[aria-label*="pin" i]'
            )
            pin_input.first.wait_for(state="visible", timeout=10000)
            pin_input.first.fill(pin)
            page.wait_for_timeout(500)

            # Click Enter / submit
            submit_btn = page.locator(
                'button[data-functional-selector="join-button"], '
                'button[type="submit"], '
                'button:has-text("Enter")'
            )
            if submit_btn.count() > 0:
                submit_btn.first.click()
            else:
                page.keyboard.press("Enter")
            page.wait_for_timeout(2000)
        except PwTimeout:
            print("❌ Không tìm thấy ô nhập PIN!")
            browser.close()
            return

        # ── Bước 3: Nhập Nickname ──
        print(f"👤 Đang nhập nickname: {nickname}")
        try:
            nick_input = page.locator(
                'input[data-functional-selector="username-input"], '
                'input[name="nickname"], '
                'input[aria-label*="nick" i], '
                'input[placeholder*="nickname" i], '
                'input[id="nickname"]'
            )
            nick_input.first.wait_for(state="visible", timeout=10000)
            nick_input.first.fill(nickname)
            page.wait_for_timeout(500)

            ok_btn = page.locator(
                'button[data-functional-selector="join-button-username"], '
                'button[type="submit"], '
                'button:has-text("OK"), '
                'button:has-text("Join")'
            )
            if ok_btn.count() > 0:
                ok_btn.first.click()
            else:
                page.keyboard.press("Enter")
            page.wait_for_timeout(2000)
        except PwTimeout:
            print("❌ Không tìm thấy ô nhập nickname!")
            page.screenshot(path="debug_nickname.png")
            browser.close()
            return

        # ── Bước 4: Xác nhận vào lobby ──
        print("⏳ Đang chờ vào lobby...")
        try:
            page.wait_for_timeout(3000)
            body_text = page.locator("body").inner_text()
            if "You're in" in body_text or "are you ready" in body_text.lower() or nickname.lower() in body_text.lower():
                print(f"✅ Đã vào lobby thành công!")
            else:
                print(f"⏳ Có thể đã vào lobby (chờ host start)...")
                if debug:
                    page.screenshot(path="debug_lobby.png")
                    print("  → Screenshot: debug_lobby.png")
        except Exception:
            print("⏳ Đang chờ trong lobby...")

        # ── Bước 5: Vòng lặp chờ câu hỏi và trả lời ──
        print("\n🎯 Chờ game bắt đầu...\n")
        last_state = ""
        no_change_count = 0

        while True:
            try:
                # Kiểm tra game over qua WebSocket flag
                if game_over:
                    print("\n🏆 Game kết thúc!")
                    page.wait_for_timeout(3000)
                    break

                body = page.locator("body").inner_text(timeout=2000)
                body_lower = body.lower()

                # Kiểm tra bị kick
                if "kicked" in body_lower or "removed" in body_lower:
                    print("\n❌ Bị kick khỏi game!")
                    break

                # Phát hiện nút đáp án
                answer_btns = page.locator('button[data-functional-selector^="answer-"]')
                btn_count = answer_btns.count()

                if btn_count >= 2:
                    current_q = quiz_counter + 1
                    print(f"❓ Câu {current_q}:", end=" ")

                    # Delay ngẫu nhiên nhỏ để trông tự nhiên
                    page.wait_for_timeout(random.randint(200, 800))

                    clicked = False
                    if answers and quiz_counter < len(answers):
                        ans = answers[quiz_counter]
                        if ans is None:
                            # Survey → click random
                            idx = random.randint(0, btn_count - 1)
                            print("→ Survey, chọn ngẫu nhiên")
                            try:
                                answer_btns.nth(idx).click(timeout=3000)
                                clicked = True
                            except Exception:
                                pass
                        else:
                            idx = ans["index"]
                            ans_text = ans.get("answer", "")
                            color = COLORS.get(idx, str(idx))
                            print(f"→ {ans_text} [{color}]", end=" ")

                            # Thử click theo text
                            clean_text = html.unescape(re.sub(r'<[^>]+>', '', ans_text)).strip().lower()
                            for i in range(btn_count):
                                try:
                                    btn_text = answer_btns.nth(i).inner_text(timeout=1000).strip().lower()
                                    if clean_text and (clean_text in btn_text or btn_text in clean_text):
                                        answer_btns.nth(i).click(timeout=3000)
                                        print("✓")
                                        clicked = True
                                        break
                                except Exception:
                                    continue

                            # Fallback: click theo index
                            if not clicked and idx < btn_count:
                                try:
                                    answer_btns.nth(idx).click(timeout=3000)
                                    print("✓ (index)")
                                    clicked = True
                                except Exception:
                                    pass

                    if not clicked:
                        # Không có đáp án → click nút đầu tiên
                        print("→ Không rõ đáp án, chọn 0")
                        try:
                            answer_btns.first.click(timeout=3000)
                        except Exception:
                            pass

                    quiz_counter += 1

                    # Chờ nút biến mất (câu hỏi kết thúc)
                    try:
                        page.wait_for_selector(
                            'button[data-functional-selector^="answer-"]',
                            state="hidden", timeout=30000
                        )
                    except PwTimeout:
                        pass
                    page.wait_for_timeout(1000)
                    last_state = "answered"
                    no_change_count = 0
                else:
                    # Chưa có câu hỏi
                    current_state = body[:100]
                    if current_state == last_state:
                        no_change_count += 1
                    else:
                        no_change_count = 0
                        last_state = current_state

                    # Timeout sau 5 phút không thay đổi
                    if no_change_count > 600:
                        print("\n⏰ Quá lâu không có hoạt động, thoát.")
                        break

                    page.wait_for_timeout(500)

            except KeyboardInterrupt:
                print("\n👋 Đã thoát.")
                break
            except Exception as e:
                err = str(e).lower()
                if "closed" in err or "target" in err:
                    print("\n⚠️  Browser đã đóng.")
                    break
                page.wait_for_timeout(500)

        # ── Kết thúc ──
        print(f"\n✅ Bot hoàn tất! Đã trả lời {quiz_counter} câu.")
        try:
            page.screenshot(path="result.png")
            print("📸 Screenshot kết quả: result.png")
        except Exception:
            pass
        try:
            page.wait_for_timeout(3000)
        except Exception:
            pass
        try:
            browser.close()
        except Exception:
            pass


# ── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    debug = "--debug" in sys.argv
    headless = "--headless" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if len(args) >= 2:
        pin = args[0].replace(" ", "")
        quiz_id = args[1].strip()
        nickname = args[2] if len(args) >= 3 else random_nick()
    elif len(args) == 1:
        pin = args[0].replace(" ", "")
        quiz_id = input("🆔 Nhập Quiz UUID: ").strip()
        nick_in = input("👤 Nickname (Enter để dùng tên mặc định): ").strip()
        nickname = nick_in if nick_in else random_nick()
    else:
        pin = input("🔢 Nhập Game PIN: ").strip().replace(" ", "")
        quiz_id = input("🆔 Nhập Quiz UUID: ").strip()
        nick_in = input("👤 Nickname (Enter để dùng tên mặc định): ").strip()
        nickname = nick_in if nick_in else random_nick()

    # Validate UUID format
    uuid_match = re.search(
        r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        quiz_id, re.IGNORECASE
    )
    if not uuid_match:
        print("❌ Quiz UUID không hợp lệ!")
        sys.exit(1)
    quiz_id = uuid_match.group(0)

    run_bot(pin, quiz_id, nickname, headless=headless, debug=debug)
