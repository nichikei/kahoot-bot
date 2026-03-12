#!/usr/bin/env python3
"""
Kahoot Answer Bot - Playwright (Browser thật)
Host sẽ thấy tên người chơi trong lobby.

Chạy: python browser_bot.py <PIN> <QuizID> <Nickname>
Ví dụ: python browser_bot.py 1234567 2ccff0a5-... phamkhanh
"""

import sys
import re
import time
import asyncio
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ── Lấy đáp án từ Kahoot API ──────────────────────────────────────────────────
def get_answers(quiz_id: str) -> list:
    url = f"https://create.kahoot.it/rest/kahoots/{quiz_id}"
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        print(f"❌ Không lấy được đáp án (status {resp.status_code})")
        return []

    quiz = resp.json()
    answers = []
    allowed = ["quiz", "multiple_select_quiz"]
    print(f"\n📚 Quiz: {quiz.get('title','?')} — {quiz.get('creator_username','?')}")
    print(f"   {len(quiz.get('questions', []))} câu hỏi\n")

    for q in quiz.get("questions", []):
        if q.get("type") not in allowed:
            answers.append(None)  # survey/slide → skip
            continue
        correct_idx = None
        for i, choice in enumerate(q.get("choices", [])):
            if choice.get("correct") and correct_idx is None:
                correct_idx = i
        answers.append({
            "question": q.get("question", ""),
            "index": correct_idx,
            "answer": q["choices"][correct_idx]["answer"] if correct_idx is not None else "?"
        })

    for i, a in enumerate(answers):
        if a:
            print(f"  Câu {i+1}: {a['answer']}")
        else:
            print(f"  Câu {i+1}: [survey - bỏ qua]")
    print()
    return answers


# ── Màu → vị trí button (0=đỏ trái trên, 1=xanh phải trên, 2=vàng trái dưới, 3=xanh lá phải dưới)
BUTTON_COLORS = {0: "RED", 1: "BLUE", 2: "YELLOW", 3: "GREEN"}

# Selector cho từng nút theo thứ tự xuất hiện trong DOM
ANSWER_SELECTORS = [
    '[data-functional-selector="answer-0"]',
    '[data-functional-selector="answer-1"]',
    '[data-functional-selector="answer-2"]',
    '[data-functional-selector="answer-3"]',
]
# Fallback selectors nếu data-functional-selector không có
FALLBACK_SELECTORS = [
    'button[class*="answer"]:nth-of-type(1)',
    'button[class*="answer"]:nth-of-type(2)',
    'button[class*="answer"]:nth-of-type(3)',
    'button[class*="answer"]:nth-of-type(4)',
]


def click_answer_by_text(page, answer_text: str) -> bool:
    """Click button đáp án khớp với text (ưu tiên hơn index)"""
    # Làm sạch HTML entities trong text
    import html
    clean = html.unescape(re.sub(r'<[^>]+>', '', answer_text)).strip().lower()
    try:
        buttons = page.locator('button[data-functional-selector^="answer-"]')
        count = buttons.count()
        for i in range(count):
            btn = buttons.nth(i)
            btn_text = btn.inner_text().strip().lower()
            if clean in btn_text or btn_text in clean:
                btn.click(timeout=3000)
                return True
    except Exception:
        pass
    return False


def click_answer_by_index(page, answer_index: int) -> bool:
    """Fallback: click theo index nếu không tìm được theo text"""
    try:
        sel = ANSWER_SELECTORS[answer_index]
        btn = page.locator(sel)
        if btn.count() > 0:
            btn.first.click(timeout=3000)
            return True
    except Exception:
        pass
    try:
        buttons = page.locator('button[data-functional-selector^="answer-"]')
        if buttons.count() > answer_index:
            buttons.nth(answer_index).click(timeout=3000)
            return True
    except Exception:
        pass
    return False


def run_bot(pin: str, quiz_id: str, nickname: str, headless: bool = False):
    print(f"\n{'='*48}")
    print(f"  🎮 KAHOOT BROWSER BOT")
    print(f"{'='*48}")
    print(f"  PIN      : {pin}")
    print(f"  Nickname : {nickname}")
    print(f"  Quiz ID  : {quiz_id}")
    print(f"{'='*48}")

    # Lấy đáp án trước
    answers = get_answers(quiz_id)
    if not answers:
        print("⚠️  Không có đáp án, bot sẽ dùng mặc định")

    quiz_counter = 0  # đếm số câu quiz thật

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--window-size=1280,720"]
        )
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        page = ctx.new_page()

        # ── Bước 1: Vào kahoot.it ──────────────────────────────────────────
        print("\n🌐 Đang mở Kahoot...")
        page.goto(f"https://kahoot.it/?pin={pin}&refer_method=link", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # Nhập PIN nếu bị hỏi lại
        try:
            pin_field = page.locator('input[data-functional-selector="game-pin-input"], input[aria-label*="pin" i], input[placeholder*="PIN" i]')
            if pin_field.count() > 0:
                pin_field.first.fill(pin)
                page.keyboard.press("Enter")
                page.wait_for_timeout(1500)
        except Exception:
            pass

        # ── Bước 2: Nhập nickname ──────────────────────────────────────────
        print("👤 Đang nhập nickname...")
        try:
            nick_field = page.locator(
                'input[data-functional-selector="username-input"], '
                'input[aria-label*="nick" i], '
                'input[placeholder*="nickname" i], '
                'input[name="nickname"]'
            )
            nick_field.first.wait_for(timeout=10000)
            nick_field.first.fill(nickname)
            page.wait_for_timeout(500)
            page.keyboard.press("Enter")
        except PlaywrightTimeout:
            print("❌ Không tìm thấy ô nhập nickname. Kiểm tra PIN.")
            browser.close()
            return

        # ── Bước 3: Chờ vào lobby ─────────────────────────────────────────
        print("⏳ Đang vào lobby...")
        try:
            # Chờ xuất hiện màn hình chờ game bắt đầu
            page.wait_for_selector(
                '[data-functional-selector="lobby"], '
                '[class*="lobby"], '
                'div[class*="Lobby"], '
                'div:has-text("You\'re in!")',
                timeout=15000
            )
            print(f"✅ Đã vào lobby với nickname: {nickname}")
            print("⏳ Đang chờ host bắt đầu game...")
        except PlaywrightTimeout:
            # Có thể đã vào rồi, tiếp tục
            print("⚠️  Không nhận diện được lobby, tiếp tục chờ...")

        # ── Bước 4: Vòng lặp chờ câu hỏi ─────────────────────────────────
        print("\n🎯 Chờ câu hỏi...\n")
        while True:
            try:
                # Kiểm tra game over
                game_over = page.locator('div:has-text("You finished"), div[class*="GameOver"], div[class*="podium"]')
                if game_over.count() > 0:
                    print("\n🏆 Game kết thúc!")
                    page.wait_for_timeout(5000)
                    break

                # Phát hiện câu hỏi đang hiển thị
                answer_btns = page.locator('button[data-functional-selector^="answer-"]')
                if answer_btns.count() >= 2:
                    current_q = quiz_counter + 1
                    print(f"❓ Câu {current_q}:", end=" ")

                    # Xác định đáp án
                    if answers and quiz_counter < len(answers):
                        ans = answers[quiz_counter]
                        if ans is None:
                            # Survey - click ngẫu nhiên
                            import random
                            idx = random.randint(0, min(3, answer_btns.count() - 1))
                            print(f"→ Survey, chọn ngẫu nhiên")
                            page.wait_for_timeout(500)
                            answer_btns.nth(idx).click()
                        else:
                            idx = ans["index"]
                            answer_text = ans["answer"]
                            print(f"→ {answer_text} [{BUTTON_COLORS.get(idx, str(idx))}]", end=" ")
                            page.wait_for_timeout(300)
                            # Ưu tiên click theo text, fallback theo index
                            if click_answer_by_text(page, answer_text):
                                print("(text match ✓)")
                            elif click_answer_by_index(page, idx):
                                print("(index fallback)")
                            else:
                                print("(❌ không click được)")
                    else:
                        print(f"→ Không có đáp án, chọn 0")
                        page.wait_for_timeout(300)
                        answer_btns.first.click()

                    quiz_counter += 1

                    # Chờ hết câu hỏi (nút biến mất)
                    try:
                        page.wait_for_selector(
                            'button[data-functional-selector^="answer-"]',
                            state="hidden",
                            timeout=30000
                        )
                    except PlaywrightTimeout:
                        pass
                    page.wait_for_timeout(1000)

                else:
                    page.wait_for_timeout(500)

            except KeyboardInterrupt:
                print("\n👋 Đã thoát.")
                break
            except Exception as e:
                if "closed" in str(e).lower():
                    break
                page.wait_for_timeout(500)

        print("\n✅ Bot hoàn tất.")
        page.wait_for_timeout(3000)
        browser.close()


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        pin = sys.argv[1].replace(" ", "")
        quiz_id_raw = sys.argv[2]
        res = re.search(r"([a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12})", quiz_id_raw)
        if not res:
            print("❌ Quiz ID không hợp lệ")
            sys.exit(1)
        quiz_id = res.group(1)
        nickname = sys.argv[3] if len(sys.argv) >= 4 else "kahootbot"
        headless = "--headless" in sys.argv
    else:
        pin = input("🔢 Game PIN: ").strip().replace(" ", "")
        quiz_id = input("🆔 Quiz ID: ").strip()
        nickname = input("👤 Nickname: ").strip() or "kahootbot"
        headless = False

    run_bot(pin, quiz_id, nickname, headless)
