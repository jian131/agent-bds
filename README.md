# 🏠 BDS Agent - Hệ Thống Tìm Kiếm Bất Động Sản Tự Động

Hệ thống AI tự động crawl và tìm kiếm bất động sản từ **10+ platforms** với giao diện hiện đại kiểu Perplexity.

## ✨ Tính Năng

- 🔍 **Tìm kiếm thông minh** - Hiểu ngữ cảnh: "chung cư 2PN Cầu Giấy 2-3 tỷ"
- 🌐 **10+ Platforms** - Batdongsan, Chợ Tốt, Mogi, Alonhadat, Facebook Groups...
- 📱 **Extract liên hệ đầy đủ** - SĐT, Zalo, Facebook, Email
- ⚡ **Real-time streaming** - Xem kết quả ngay khi crawl
- 🎨 **UI hiện đại** - Perplexity-style với animations
- 🔔 **Telegram Bot** - Thông báo tin mới

## 🏗️ Tech Stack

| Component     | Technology               |
| ------------- | ------------------------ |
| **Crawler**   | Crawl4AI + Playwright    |
| **Backend**   | FastAPI + Uvicorn        |
| **Frontend**  | Next.js 14 + TailwindCSS |
| **Database**  | PostgreSQL + ChromaDB    |
| **LLM**       | Groq (llama-3.3-70b)     |
| **Scheduler** | APScheduler              |

## 📦 Cài Đặt

### Requirements

- Python 3.11 hoặc 3.12 (⚠️ **KHÔNG dùng Python 3.13** - lỗi với Playwright)
- Node.js 18+
- PostgreSQL (optional)

### 1. Clone & Setup Python

```bash
git clone https://github.com/jian131/agent-bds.git
cd agent-bds/bds-agent

# Tạo virtual environment (QUAN TRỌNG: dùng Python 3.11/3.12)
py -3.12 -m venv venv
# Hoặc trên Linux/Mac
python3.12 -m venv venv

# Activate
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Cấu Hình Environment

Tạo file `.env`:

```env
# === REQUIRED ===
GROQ_API_KEY=gsk_your_groq_api_key_here

# === OPTIONAL ===
# PostgreSQL (nếu không có sẽ dùng SQLite)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/bds_agent

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Google Sheets backup
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials/service_account.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
```

### 3. Setup Frontend

```bash
cd frontend
npm install
```

## 🚀 Chạy Hệ Thống

### Terminal 1: Backend API

```bash
cd bds-agent
.\venv\Scripts\activate  # Windows
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Frontend

```bash
cd bds-agent/frontend
npm run dev
```

### Truy cập

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

## 📡 API Endpoints

### Search

```bash
# Standard search
POST /api/v1/search
{
  "query": "chung cư 2PN Cầu Giấy 2-3 tỷ",
  "max_results": 50
}

# Streaming search (SSE)
POST /api/v1/search/stream
{
  "query": "nhà riêng Ba Đình dưới 5 tỷ",
  "max_results": 30
}

# WebSocket real-time
WS /api/v1/search/ws
```

### Response Format

```json
{
  "results": [
    {
      "id": "abc123",
      "title": "Bán căn hộ 2PN Times City",
      "price_text": "3 tỷ 200 triệu",
      "price_number": 3200000000,
      "area_m2": 85.5,
      "location": {
        "address": "458 Minh Khai, Hai Bà Trưng",
        "district": "Hai Bà Trưng",
        "city": "Hà Nội"
      },
      "contact": {
        "phones": ["0912345678", "0987654321"],
        "zalo": ["0912345678"],
        "facebook": ["agent.bds"],
        "email": ["contact@example.com"],
        "name": "Nguyễn Văn A"
      },
      "images": ["https://..."],
      "source_url": "https://batdongsan.com.vn/...",
      "source_platform": "batdongsan.com.vn",
      "bedrooms": 2,
      "bathrooms": 2
    }
  ],
  "total": 42,
  "execution_time_ms": 45000,
  "from_cache": false
}
```

## 🌐 Supported Platforms

| Platform          | Status | Features              |
| ----------------- | ------ | --------------------- |
| batdongsan.com.vn | ✅     | Full listing + detail |
| chotot.com        | ✅     | Full listing + detail |
| mogi.vn           | ✅     | Full listing + detail |
| alonhadat.com.vn  | ✅     | Full listing + detail |
| nhadat247.com.vn  | ✅     | Listing               |
| muaban.net        | ✅     | Listing               |
| dothi.net         | ✅     | Listing               |
| homedy.com        | ✅     | Listing               |
| nhatot.com        | ✅     | Listing               |
| propzy.vn         | ✅     | Listing               |
| Facebook Groups   | ✅     | Posts + Marketplace   |

## 🔍 Search Query Examples

```
"chung cư 2 phòng ngủ Cầu Giấy 2-3 tỷ"
"nhà riêng Ba Đình dưới 5 tỷ"
"đất nền Hà Đông 1-2 tỷ"
"căn hộ 3PN Tây Hồ view hồ"
"cho thuê chung cư Thanh Xuân 10-15 triệu"
```

## 📊 Performance

- **Search time**: 30-60 seconds
- **Platforms crawled**: 5-10 per search
- **Results**: 30-50 unique listings
- **Contact extraction**: 80%+ accuracy

## 🐛 Troubleshooting

### "NotImplementedError" khi chạy Playwright

**Nguyên nhân**: Python 3.13 không tương thích với Playwright trên Windows.

**Giải pháp**: Dùng Python 3.11 hoặc 3.12:

```bash
# Xóa venv cũ
rm -rf venv

# Tạo lại với Python 3.12
py -3.12 -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### "Cannot connect to database"

**Giải pháp**: Hệ thống sẽ tự động dùng SQLite nếu không có PostgreSQL.

### Frontend không load được

**Kiểm tra**:

1. Backend đang chạy trên port 8000
2. CORS đã cấu hình đúng
3. `.env` có `NEXT_PUBLIC_API_URL=http://localhost:8000`

## 📝 License

MIT License - Sử dụng tự do cho mục đích cá nhân và thương mại.

## 🤝 Contributing

1. Fork repo
2. Tạo branch: `git checkout -b feature/amazing-feature`
3. Commit: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Tạo Pull Request

---

Made with ❤️ by [jian131](https://github.com/jian131)
