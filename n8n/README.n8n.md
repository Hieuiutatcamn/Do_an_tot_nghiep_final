# Chatbot AI bằng n8n (Text-to-SQL)

Chat widget ở web user → gọi webhook n8n → n8n dùng **Gemini** sinh câu `SELECT` → chạy trên **MySQL** `do_an_tot_nghiep` → Gemini diễn giải kết quả thành câu trả lời tiếng Việt → trả JSON về widget.

```
Chat widget (browser :5500)
        │  POST { noi_dung_tin_nhan, conversation_id }
        ▼
http://127.0.0.1:5678/webhook/chat   (n8n)
        │
   Webhook → Sinh SQL (Gemini) → Làm sạch SQL → MySQL → Gom kết quả → Trả lời (Gemini) → Respond
        │  { "response": "<câu trả lời>" }
        ▼
   Hiển thị trong chat widget
```

> Đây là RAG "không vector DB": LLM tự suy ra câu SQL dựa trên schema + sample data nhúng trong prompt. Đủ để demo/báo cáo.

---

## 1. Khởi động n8n

```bash
# chạy cả hệ thống
docker compose up -d
# hoặc chỉ n8n (kèm db)
docker compose up -d n8n
```

Mở **http://localhost:5678** → lần đầu tạo tài khoản owner (email + mật khẩu tùy ý, chỉ dùng local).

## 2. Tạo 2 credential

**a) Google Gemini** — menu **Credentials → New → "Google Gemini(PaLM) Api"**:
- API Key: dán key Gemini của bạn (lấy ở https://aistudio.google.com/apikey — key thường bắt đầu bằng `AIza...`).

**b) MySQL** — **Credentials → New → "MySQL"**:
| Trường   | Giá trị            |
|----------|--------------------|
| Host     | `db`               |
| Port     | `3306`             |
| Database | `do_an_tot_nghiep` |
| User     | `root`             |
| Password | `123456`           |

> Host là `db` (tên service trong docker-compose) vì n8n và MySQL cùng mạng nội bộ Docker.

## 3. Import workflow

> Workflow **có thể đã được nạp sẵn** (mình đã `import:workflow` qua CLI). Mở **Workflows** xem có **"SunLens Chatbot (Text-to-SQL)"** chưa. Nếu **chưa thấy** (vd sau khi `docker compose down -v` reset volume `n8n_data`) thì import thủ công như dưới.

**Workflows → ⋮ → Import from File** → chọn:
`n8n/sunlens_chatbot_workflow.json` (trong container đã mount sẵn ở `/workflows/sunlens_chatbot_workflow.json`).

Nạp lại nhanh bằng CLI (tùy chọn):
```bash
docker compose exec n8n n8n import:workflow --input=/workflows/sunlens_chatbot_workflow.json
```

Sau khi import, mở workflow và **gán credential** cho 2 node:
- Node **Gemini Model** → chọn credential Google Gemini vừa tạo.
- Node **MySQL - Truy vấn** → chọn credential MySQL vừa tạo.

Model ở node **Gemini Model**: dùng **`models/gemini-2.5-flash-lite`** (mặc định, nhẹ + có free tier). Nếu cần thông minh hơn: `models/gemini-2.5-flash`.

> ⚠️ KHÔNG dùng `gemini-2.0-flash` / `gemini-2.0-flash-lite`: dòng 2.0 hiện **quota free = 0** (lỗi 429 `RESOURCE_EXHAUSTED`). Dòng **2.5** có free tier.

## 4. Activate

Bật công tắc **Active** (góc trên phải workflow). Khi đó webhook production sống ở:
```
http://127.0.0.1:5678/webhook/chat
```
Widget (`hop_thoai_ho_tro.js`) đã trỏ sẵn vào URL này.

## 5. Test

- **Test nhanh bằng curl:**
  ```bash
  curl -X POST http://127.0.0.1:5678/webhook/chat \
    -H "Content-Type: application/json" \
    -d '{"noi_dung_tin_nhan":"Có những máy ảnh nào đang cho thuê?","conversation_id":null}'
  ```
  Kỳ vọng: `{ "response": "..." }`.

- **Trên web:** mở trang user (http://127.0.0.1:5500/DOANTOTNGHIEP_FrontEnd/Webthuemayanh_FE/user/Sunlens_Camera/index.html) → mở chat widget → hỏi:
  - "Có những máy ảnh nào đang cho thuê?"
  - "Máy Canon giá bao nhiêu?"
  - "Có khuyến mãi nào đang chạy không?"

## 6. Cách hoạt động của workflow (9 node)

| Node | Vai trò |
|------|---------|
| **Webhook** | Nhận POST `/webhook/chat`, bật sẵn CORS (`allowedOrigins=*`) cho frontend `:5500` |
| **Gemini Model** | Chat model dùng chung cho 2 LLM chain |
| **Sinh SQL** | Prompt có schema + sample → sinh 1 câu `SELECT` |
| **Làm sạch SQL** | Bỏ ```/markdown, chặn mọi lệnh khác `SELECT` (an toàn) |
| **MySQL - Truy vấn** | Chạy câu SELECT trên DB (Always Output Data để không treo khi 0 dòng) |
| **Gom kết quả** | Gộp các dòng thành 1 JSON + kèm lại câu hỏi |
| **Trả lời** | Gemini vừa diễn giải dữ liệu thành câu trả lời TV, vừa **quyết định escalation** → trả JSON `{tra_loi, can_nhan_vien, loai_yeu_cau}` |
| **Tách kết quả** | Parse JSON của Gemini (robust, có fallback) → `{response, need_staff, loai_yeu_cau}` |
| **Respond to Webhook** | Trả `{ "response", "need_staff", "loai_yeu_cau" }` (kèm header CORS) |

## 6b. Chuyển nhân viên (escalation) + ticket

Khi khách hỏi việc **cần con người quyết định** (bảo trì/sửa chữa, đổi-trả, hoàn tiền, hủy đơn, khiếu nại), node **Trả lời** đặt `can_nhan_vien=true` + chọn `loai_yeu_cau` (KHIEU_NAI / HUY_DON / HOAN_TIEN / CAN_XAC_NHAN / KHAC). Luồng phía sau:

1. n8n trả `{ need_staff: true, loai_yeu_cau }` về widget.
2. Widget (`hop_thoai_ho_tro.js`):
   - Nếu khách **đã đăng nhập** → gọi `POST /api/v1/tro-chuyen/request-staff` kèm `loai_yeu_cau` → tạo cuộc trò chuyện vào **inbox nhân viên** + ghi **ticket** (`chat_ticket`) đúng loại (khi nhân viên offline), rồi tự chuyển khung chat sang tab **Nhân viên**.
   - Nếu **chưa đăng nhập** → widget mời khách đăng nhập (escalation chỉ cho khách đã đăng nhập, theo thiết kế).
3. Nhân viên xử lý ngay trong **trang admin chat** (`/admin/chat/conversations` → assign → reply → close). Không cần trang ticket riêng.

> Backend đã được sửa nhẹ: `request-staff` nhận thêm `loai_yeu_cau` và truyền vào `tao_phieu_chat()` (không đổi schema DB — enum `LOAI_VE_CHAT` đã có sẵn).

## 7. Sự cố thường gặp

- **Widget báo lỗi / không phản hồi:** kiểm tra workflow đã **Active** chưa. Khi đang sửa trong editor (chưa active), webhook test là `/webhook-test/chat` — bấm **"Listen for test event"** rồi mới gọi.
- **Lỗi CORS trên trình duyệt:** đảm bảo node Webhook có `allowedOrigins=*` (đã đặt sẵn trong file). Restart workflow sau khi đổi.
- **Gemini 401/403:** key sai hoặc hết hạn → tạo key mới ở Google AI Studio (key đúng dạng `AIza...`).
- **MySQL "Access denied" / "Unknown database":** kiểm tra credential Host=`db`, DB=`do_an_tot_nghiep`, và stack `db` đang chạy (`docker compose ps`).
- **LLM sinh SQL sai cột:** mở node **Sinh SQL**, chỉnh lại phần SCHEMA/SAMPLE trong prompt cho rõ hơn.

## 8. Bảo mật

- API key Gemini **không** lưu trong file workflow (chỉ nằm trong credential mã hóa của n8n, ở volume `n8n_data`). Không commit key lên git.
