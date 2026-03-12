# Hướng Dẫn Chạy Bot Kahoot

## Yêu cầu

- Windows 10/11
- Python 3.9+ đã cài sẵn và thêm vào PATH

---

## Cài đặt lần đầu (chỉ làm 1 lần)

Mở PowerShell trong thư mục `bot-kahoot`, chạy lần lượt:

```powershell
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường ảo
.venv\Scripts\Activate.ps1

# Cài thư viện
pip install -r requirements.txt

# Cài trình duyệt Playwright
playwright install chromium
```

---

## Cách dùng mỗi lần chơi

### Bước 1 — Lấy Quiz UUID

Truy cập link game của giáo viên, ví dụ:
```
https://play.kahoot.it/v2/lobby?quizId=e438585b-d212-4eca-a44a-beef8a904adb
```
Phần UUID chính là dãy ký tự sau `?quizId=`:
```
e438585b-d212-4eca-a44a-beef8a904adb
```

### Bước 2 — Lấy Game PIN

Khi giáo viên mở game, sẽ hiện PIN trên màn hình, ví dụ `7451583`.

### Bước 3 — Chạy bot

Mở PowerShell, kích hoạt venv rồi chạy:

```powershell
.venv\Scripts\Activate.ps1

python pw_bot.py <PIN> <UUID>
```

**Ví dụ thực tế:**
```powershell
python pw_bot.py 7451583 e438585b-d212-4eca-a44a-beef8a904adb
```

Tên mặc định sẽ tự điền là **Phạm Nhật Khánh**, **Phạm Khánh**, hoặc **Nhật Khánh** (chọn ngẫu nhiên).

---

## Tùy chọn thêm

| Tùy chọn | Ý nghĩa |
|---|---|
| `--headless` | Chạy ẩn, không hiện cửa sổ trình duyệt |
| `--debug` | In chi tiết quá trình xử lý |

```powershell
# Chạy ẩn
python pw_bot.py 7451583 e438585b-d212-4eca-a44a-beef8a904adb --headless

# Chạy với tên tùy chỉnh
python pw_bot.py 7451583 e438585b-d212-4eca-a44a-beef8a904adb "Nguyễn Văn A"
```

---

## Kiểm tra quiz có dùng được không

Nếu không chắc quiz của thầy/cô có công khai không, chạy lệnh này:

```powershell
python -c "import requests; r = requests.get('https://create.kahoot.it/rest/kahoots/<UUID>', timeout=10); print('OK' if r.status_code==200 else 'PRIVATE - không lấy được đáp án')"
```

- Hiện `OK` → bot sẽ trả lời đúng 100%
- Hiện `PRIVATE` → quiz bị ẩn, bot không lấy được đáp án

---

## Lưu ý

- Trình duyệt sẽ tự mở và chơi, **đừng đóng cửa sổ** trong khi bot đang chạy
- Chỉ dùng khi quiz ở chế độ **Public** thì mới lấy được đáp án
- Nếu gặp lỗi `ExecutionPolicy`, chạy lệnh này trước: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`


## Usage
Open a terminal (Command Prompt on Windows) and navigate to the directory (folder) containing kbot. Then use the following command, replacing `[options]` with any options you want to use (listed below).
```
python kbot [options]
```
```
-e, --email
The email used to login to create.kahoot.it

-a, --password
The corresponding password used to login to create.kahoot.it

-n, --nick
The nickname to join the Kahoot with

-p, --pin
The game pin

-s --search
Search for a quiz without joining a Kahoot. Cancels nick and pin options.

-q, --quizName
The quiz's name

-i, --quizID
The quiz's ID

-d, --debug
Output go print("brrrrrrrrrrrrr") # ;)
```

## Caveats
Does not work when:
- Kahoot is private
- Answers are randomized
- Questions are randomized

This is because this program uses the original question order and answer order, so if these are randomized the wrong answer will be clicked.

## Contributors
* [Raymo111](https://github.com/Raymo111) - Fixing it, adding 2FA and search by ID
* [reteps](https://github.com/reteps) - Main programming
* [idiidk](https://github.com/idiidk) - For the challenge decoding
