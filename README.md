# 🏠 BDS Agent - Hệ thống tìm kiếm & quản lý tin BĐS tự động

Hệ thống AI Agent tự động thu thập, lưu trữ và tìm kiếm thông tin bất động sản từ nhiều nguồn.

## ✨ Tính năng chính

- **🤖 AI Agent thông minh**: Tự động tìm kiếm và thu thập dữ liệu từ nhiều nguồn
- **🌐 Multi-source scraping**: Chợ Tốt, Batdongsan.com.vn, Mogi, Alonhadat, Facebook, Google
- **✅ Data validation**: Kiểm tra số điện thoại, giá hợp lý, địa chỉ thực
- **🔍 Semantic search**: Tìm kiếm ngữ nghĩa với ChromaDB
- **📊 Database + Backup**: PostgreSQL + Google Sheets
- **🔔 Notifications**: Telegram Bot alerts
- **🎯 100% FREE stack**: Ollama local LLM, browser-use automation

## 🛠️ Tech Stack

| Component          | Technology             |
| ------------------ | ---------------------- |
| LLM                | Ollama (qwen2.5:14b)   |
| Browser Automation | browser-use            |
| Backend            | FastAPI                |
| Database           | PostgreSQL             |
| Vector DB          | ChromaDB               |
| Frontend           | Next.js 14 + Shadcn/UI |
| Scheduler          | APScheduler            |
| Backup             | Google Sheets API      |
| Notifications      | Telegram Bot API       |

## 📁 Project Structure

```
bds-agent/
├── main.py                 # Entry point
├── config.py               # Settings (Pydantic)
├── docker-compose.yml      # PostgreSQL + Redis
│
├── agents/
│   ├── search_agent.py     # Core AI agent
│   ├── tools.py            # Custom tools
│   └── prompts.py          # LLM prompts
│
├── storage/
│   ├── database.py         # SQLAlchemy models
│   ├── vector_db.py        # ChromaDB wrapper
│   └── sheets.py           # Google Sheets
│
├── services/
│   ├── scraper.py          # Scraper orchestrator
│   ├── validator.py        # Data validation
│   └── matcher.py          # Buyer-seller matching
│
├── api/
│   └── routes/             # FastAPI endpoints
│
├── frontend/               # Next.js app
│
└── scheduler/
    └── jobs.py             # Background jobs
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Ollama installed locally
- Node.js 18+ (for frontend)

### 2. Install Ollama & Model

```bash
# Install Ollama (Windows)
# Download from https://ollama.ai/download

# Pull the model
ollama pull qwen2.5:14b

# Verify
ollama list
```

### 3. Setup Project

```bash
# Clone repo
cd bds-agent

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install browser-use playwright browsers
python -m playwright install chromium
```

### 4. Configure Environment

```bash
# Copy example env
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Edit .env with your settings
```

### 5. Start Database

```bash
# Start PostgreSQL & Redis
docker-compose up -d

# Verify
docker-compose ps
```

### 6. Run Agent

```bash
# Demo mode
python main.py demo

# Interactive mode
python main.py interactive

# Quick search
python main.py search "chung cư 2PN Cầu Giấy 2-3 tỷ"

# Start API server
python main.py api
```

## 📖 Usage Examples

### Python API

```python
import asyncio
from agents.search_agent import RealEstateSearchAgent

async def main():
    agent = RealEstateSearchAgent()

    result = await agent.search(
        "Tìm chung cư 2PN Cầu Giấy 2-3 tỷ",
        max_results=10,
        platforms=["chotot", "batdongsan"]
    )

    print(f"Found {result.total_found} listings")

    for listing in result.listings:
        print(f"- {listing['title']}")
        print(f"  Price: {listing['price_text']}")
        print(f"  URL: {listing['source_url']}")

    await agent.close()

asyncio.run(main())
```

### REST API

```bash
# Search
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "chung cư 2PN Cầu Giấy 2-3 tỷ"}'

# Get listings
curl http://localhost:8000/api/listings

# Get listing detail
curl http://localhost:8000/api/listings/{id}
```

## 🔧 Configuration

### Environment Variables

| Variable           | Description                | Default                    |
| ------------------ | -------------------------- | -------------------------- |
| `OLLAMA_MODEL`     | Ollama model name          | `qwen2.5:14b`              |
| `OLLAMA_BASE_URL`  | Ollama server URL          | `http://localhost:11434`   |
| `DATABASE_URL`     | PostgreSQL connection      | `postgresql+asyncpg://...` |
| `HEADLESS_MODE`    | Run browser headless       | `false`                    |
| `SCRAPE_DELAY_MIN` | Min delay between requests | `2`                        |
| `SCRAPE_DELAY_MAX` | Max delay between requests | `5`                        |

### Price Validation by District

Giá được validate theo khoảng hợp lý cho từng quận (triệu VND/m²):

| Quận      | Min | Max |
| --------- | --- | --- |
| Hoàn Kiếm | 100 | 300 |
| Ba Đình   | 80  | 250 |
| Tây Hồ    | 80  | 250 |
| Cầu Giấy  | 60  | 180 |
| Hà Đông   | 35  | 100 |
| ...       | ... | ... |

## 🔒 Data Validation

Mỗi listing được validate:

1. **Required fields**: `source_url`, `title`
2. **Phone validation**: Format VN (0xxx-xxx-xxxx)
3. **Price validation**: Trong khoảng hợp lý cho khu vực
4. **Deduplication**: Hash(url + phone + title)
5. **Spam detection**: Lọc tin môi giới, ký gửi

## 📊 Listing Schema

```json
{
  "id": "md5_hash",
  "title": "Bán chung cư 2PN tại Cầu Giấy",
  "price_text": "3 tỷ 500 triệu",
  "price_number": 3500000000,
  "area_m2": 85.5,
  "location": {
    "address": "123 Đường ABC",
    "ward": "Nghĩa Đô",
    "district": "Cầu Giấy",
    "city": "Hà Nội"
  },
  "contact": {
    "name": "Anh Minh",
    "phone": "0912 345 678",
    "phone_clean": "0912345678"
  },
  "images": ["url1", "url2"],
  "source_url": "https://...",
  "source_platform": "chotot",
  "scraped_at": "2024-01-20T10:30:00Z",
  "property_type": "chung cư",
  "bedrooms": 2,
  "bathrooms": 2
}
```

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

## 🐳 Docker Deployment

```bash
# Build & run all services
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 📝 Development

### Code Style

```bash
# Format
black .

# Lint
ruff check .

# Type check
mypy .
```

### Adding New Platform

1. Add platform config to `config.py`:

```python
SCRAPING_PLATFORMS["newplatform"] = {
    "name": "New Platform",
    "base_url": "https://...",
    "priority": 7,
}
```

2. Implement scraper in `agents/search_agent.py`:

```python
async def _search_newplatform(self, intent: SearchIntent) -> list[dict]:
    # Implementation
    pass
```

## ⚠️ Legal Notice

- This tool is for educational purposes only
- Respect robots.txt and terms of service
- Use reasonable delays between requests
- Do not overload target websites

## 📄 License

MIT License

## 🤝 Contributing

1. Fork the repo
2. Create feature branch
3. Commit changes
4. Open PR

---

**Built with ❤️ using browser-use + Ollama**
