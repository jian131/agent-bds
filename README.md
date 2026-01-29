# 🏠 BDS Agent - Hệ thống tìm kiếm BĐS với Crawl4AI

Hệ thống tìm kiếm bất động sản tự động thu thập, phân tích và lọc thông tin từ nhiều nguồn với AI và Vector Search.

## ✨ Tính năng chính

- **⚡ Crawl4AI Integration**: Thu thập dữ liệu siêu nhanh với Playwright + CSS Selectors
- **🌐 Multi-source crawling**: Batdongsan.com.vn, Mogi, Alonhadat, Facebook Groups, Google Search
- **🔍 Smart Search Filtering**:
  - Tự động parse query (giá, địa điểm, loại BĐS)
  - Filter theo city/district với city detection
  - Price range với 30% tolerance
- **🎯 Semantic Search**: ChromaDB + Sentence-Transformers (multilingual)
- **✅ Data Validation**: Parse và validate giá, diện tích, số điện thoại, địa chỉ
- **📊 Backend API**: FastAPI với streaming support
- **🎨 Frontend**: Next.js 14 + Shadcn/UI

## 🛠️ Tech Stack

| Component    | Technology                                       |
| ------------ | ------------------------------------------------ |
| Web Crawling | Crawl4AI 0.3.74 (Playwright + CSS Selectors)     |
| LLM          | Google Gemini 2.0 Flash                          |
| Vector DB    | ChromaDB + paraphrase-multilingual-MiniLM-L12-v2 |
| Backend      | FastAPI                                          |
| Database     | PostgreSQL (optional - currently degraded)       |
| Frontend     | Next.js 14 + TailwindCSS + Shadcn/UI             |
| Language     | Python 3.11+                                     |

## 📁 Cấu trúc dự án

```
bds-agent/
├── main.py                      # Backend API entry point
├── config.py                    # Environment config
├── requirements.txt             # Python dependencies
│
├── agents/
│   └── search_agent.py          # Search orchestration agent
│
├── crawlers/
│   ├── google_crawler.py        # Google Search với Gemini
│   ├── platform_crawlers.py     # Batdongsan, Mogi, Alonhadat crawlers
│   ├── facebook_crawler.py      # Facebook Groups crawler
│   └── css_selectors.py         # CSS selectors cho từng platform
│
├── parsers/
│   └── listing_parser.py        # Parse & validate listings
│
├── services/
│   └── search_service.py        # Main search service (filtering, dedup)
│
├── storage/
│   ├── vector_db.py             # ChromaDB wrapper
│   └── database.py              # PostgreSQL (optional)
│
├── frontend/
│   ├── app/                     # Next.js App Router
│   ├── components/              # React components
│   └── lib/                     # Utils & API client
│
└── data/
    └── models/                  # VectorDB models (420MB, tracked by Git LFS)
```

## 🚀 Cài đặt và Chạy hệ thống

### 1. Yêu cầu hệ thống

- **Python 3.11+** 
- **Node.js 18+** (cho frontend)
- **Git LFS** (để clone model files)
- **Google Gemini API Key** (miễn phí tại https://aistudio.google.com/apikey)

### 2. Clone repository

```bash
# Install Git LFS (nếu chưa có)
git lfs install

# Clone project (bao gồm model 420MB qua LFS)
git clone https://github.com/jian131/agent-bds.git
cd agent-bds/bds-agent
```

### 3. Setup Backend (Python)

```bash
# Tạo virtual environment
python -m venv venv

# Activate venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (cho Crawl4AI)
playwright install chromium
```

### 4. Cấu hình môi trường

```bash
# Copy file .env.example
copy .env.example .env     # Windows
# cp .env.example .env     # Linux/Mac
```

Chỉnh sửa file `.env`:

```ini
# === Google Gemini API (BẮT BUỘC) ===
GOOGLE_API_KEY=your_gemini_api_key_here

# === VectorDB Settings ===
VECTORDB_ENABLED=true
VECTORDB_MODEL=paraphrase-multilingual-MiniLM-L12-v2  # Model đã có sẵn

# === Database (OPTIONAL - hiện tại degraded) ===
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/bds_agent
# Có thể bỏ qua - hệ thống vẫn chạy không cần DB

# === API Settings ===
API_HOST=0.0.0.0
API_PORT=8000
```

### 5. Chạy Backend API

```bash
# Start FastAPI server
python main.py

# Hoặc với uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API sẽ chạy tại: **http://localhost:8000**

Swagger docs: **http://localhost:8000/docs**

### 6. Setup Frontend (Next.js)

Mở terminal mới:

```bash
cd frontend

# Install dependencies
npm install

# Chạy dev server
npm run dev
```

Frontend sẽ chạy tại: **http://localhost:3000**

### 7. Test hệ thống

**Từ giao diện web:**
- Truy cập http://localhost:3000
- Nhập query: `chung cu 3 ty thanh xuan ha noi`
- Xem kết quả real-time

**Từ API:**
```bash
# Test health
curl http://localhost:8000/health

# Test search
curl "http://localhost:8000/api/v1/search?query=chung%20cu%202%20ty%20cau%20giay"
```

**Từ Python:**
```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/search",
    params={"query": "chung cu 5 ty ha noi"}
)
print(response.json())
```

## 📖 API Endpoints

### Search API

**GET** `/api/v1/search`

Query Parameters:
- `query` (required): Search query (VD: "chung cu 2 ty cau giay")
- `max_results` (optional): Số lượng kết quả tối đa (default: 50)

Response:
```json
{
  "listings": [
    {
      "id": "abc123",
      "title": "Bán căn hộ 2PN tại Cầu Giấy",
      "price_text": "2,5 tỷ",
      "price_number": 2500000000,
      "area_text": "75m²",
      "area_m2": 75.0,
      "location": {
        "address": "Đường Trần Duy Hưng",
        "district": "Cầu Giấy",
        "city": "Hà Nội"
      },
      "contact": {
        "name": "Chủ nhà",
        "phones": ["0912345678"]
      },
      "images": ["url1", "url2"],
      "source_url": "https://...",
      "source_platform": "batdongsan.com.vn"
    }
  ],
  "total": 15,
  "query_parsed": {
    "city": "Hà Nội",
    "district": "cau giay",
    "price_min": 1.6,
    "price_max": 2.4,
    "property_type": "apartment"
  }
}
```

### Streaming Search API

**GET** `/api/v1/search/stream`

Server-Sent Events (SSE) endpoint cho real-time updates.

Event types:
- `status`: Thông báo tiến trình
- `result`: Từng listing
- `complete`: Hoàn thành

### Health Check

**GET** `/health`

```json
{
  "status": "healthy",
  "service": "bds-agent",
  "version": "2.0",
  "llm": "ok",
  "database": "degraded"
}
```

## 🔍 Search Query Examples

Hệ thống tự động parse query tiếng Việt:

| Query                              | Parsed                                                  |
| ---------------------------------- | ------------------------------------------------------- |
| "chung cu 2 ty cau giay"           | city=HN, district=Cau Giay, price=1.6-2.4 tỷ            |
| "nha rieng thanh xuan 5 ty"        | city=HN, district=Thanh Xuan, price=4-6 tỷ, type=house |
| "can ho quan 7 hcm 3-4 ty"         | city=HCM, district=Q7, price=3-4 tỷ                     |
| "biet thu da nang duoi 10 ty"      | city=Da Nang, price=0-10 tỷ, type=villa                |
| "chung cu ha noi"                  | city=HN, type=apartment                                 |

## 📊 Listing Data Structure

Mỗi listing có cấu trúc:

```python
{
    "id": str,                    # Unique ID (MD5 hash)
    "title": str,                 # Tiêu đề
    "price_text": str,            # Giá dạng text "2,5 tỷ"
    "price_number": int,          # Giá dạng số (VND)
    "area_text": str,             # Diện tích text "75m²"
    "area_m2": float,             # Diện tích số
    "location": {
        "address": str,           # Địa chỉ đầy đủ
        "ward": str,              # Phường/xã
        "district": str,          # Quận/huyện
        "city": str              # Thành phố
    },
    "contact": {
        "name": str,              # Tên người liên hệ
        "phones": List[str],      # Danh sách SĐT
        "zalo": List[str],        # Zalo IDs
        "facebook": List[str],    # Facebook profiles
        "email": List[str]        # Emails
    },
    "images": List[str],          # URLs ảnh
    "source_url": str,            # URL gốc
    "source_platform": str,       # Platform name
    "property_type": str,         # Loại BĐS
    "bedrooms": int,              # Số phòng ngủ
    "bathrooms": int,             # Số phòng tắm
    "description": str,           # Mô tả
    "scraped_at": datetime,       # Thời gian crawl
    "posted_at": str             # Thời gian đăng (nếu có)
}
```

## 🎯 Smart Filtering

Hệ thống filter listings dựa trên:

### 1. Price Filtering
- Parse giá từ text: "2,5 tỷ", "500 triệu", "3.5 tỷ"
- 30% tolerance: Tìm 3 tỷ → filter 2.1-3.9 tỷ
- Cho phép "Giá thỏa thuận" (negotiate)

### 2. Location Filtering
- **City matching**: "Hà Nội", "HCM", "Đà Nẵng", v.v.
- **District matching**: Hỗ trợ có/không dấu
  - "cau giay" = "cầu giấy" = "Cầu Giấy"
  - "thanh xuan" = "thanh xuân"
- **Auto-detect city** từ location text
  - "Bình Dương" → filter out khi search HN
  - "Quận 7" → auto-detect HCM

### 3. Property Type
- Chung cư / Căn hộ → `apartment`
- Nhà phố / Nhà riêng → `house`
- Biệt thự → `villa`
- Đất / Đất nền → `land`

## 🏗️ Architecture

### Search Flow

```
User Query
    ↓
Query Parser (extract city, district, price, type)
    ↓
URL Generator (platform-specific URLs)
    ↓
Parallel Crawling (Crawl4AI + Playwright)
    ├─ Batdongsan.com.vn
    ├─ Mogi.vn
    ├─ Alonhadat.com.vn
    ├─ Facebook Groups
    └─ Google Search
    ↓
Parser & Validator (clean + validate)
    ↓
Filter by Criteria (price, location, type)
    ↓
Deduplication (by ID hash)
    ↓
VectorDB Storage (optional)
    ↓
Return Results
```

### Crawling Mechanism

**Crawl4AI Features:**
- Async Playwright browser automation
- CSS selector-based extraction
- Auto-scroll and pagination
- Proxy rotation support
- Cache management

**Selectors per Platform:**
```python
# Batdongsan.com.vn
LISTING_SELECTOR = ".re__card-info"
TITLE = ".re__card-title"
PRICE = ".re__card-config-price"
LOCATION = ".re__card-location"

# Mogi.vn
LISTING_SELECTOR = ".property-item"
TITLE = ".property-title"
...
```

## 🔧 Advanced Configuration

### VectorDB Settings

```python
# storage/vector_db.py
VECTORDB_CONFIG = {
    "collection_name": "bds_listings",
    "model_name": "paraphrase-multilingual-MiniLM-L12-v2",
    "dimension": 384,
    "distance_metric": "cosine"
}
```

### Crawling Settings

```python
# config.py
CRAWL_SETTINGS = {
    "timeout": 30,              # Request timeout (seconds)
    "max_retries": 3,           # Max retry attempts
    "concurrent_requests": 10,  # Parallel requests
    "delay_between": 1.0,       # Delay between requests
    "user_agent_rotate": True,  # Rotate user agents
}
```

### Price Range by City

```python
# services/search_service.py
PRICE_MULTIPLIERS = {
    "hà nội": {"min": 0.8, "max": 1.2},
    "hồ chí minh": {"min": 0.9, "max": 1.3},
    "đà nẵng": {"min": 0.7, "max": 1.1},
}
```

## 📝 Development

### Add New Platform

1. **Add CSS selectors** in `crawlers/css_selectors.py`:
```python
CSS_SELECTORS["newplatform.com"] = {
    "listing": ".listing-item",
    "title": ".title",
    "price": ".price",
    ...
}
```

2. **Add platform URL generator** in `services/search_service.py`:
```python
def _generate_fallback_urls(self, query):
    # ... existing code ...
    
    # New platform
    newplatform_url = f"https://newplatform.com/search?q={query}"
    urls.append({
        "url": newplatform_url,
        "platform": "newplatform.com"
    })
```

## 🐞 Troubleshooting

### Model không tải được
```bash
# Check Git LFS
git lfs ls-files

# Re-pull LFS files
git lfs pull
```

### Crawl bị chặn
```python
# Tăng delay giữa requests
DELAY_BETWEEN = 2.0

# Rotate user agents
USER_AGENT_ROTATE = True

# Sử dụng proxy
PROXY_LIST = ["http://proxy1:8080", ...]
```

### VectorDB lỗi
```bash
# Xóa collection và tạo lại
rm -rf data/chroma_db/

# Hoặc disable VectorDB
VECTORDB_ENABLED=false
```

### Database không kết nối
```ini
# System vẫn chạy với degraded DB
# Check logs
tail -f logs/app.log
```

## ⚠️ Lưu ý về Model

**Model được commit vào Git vì:**
- ✅ Tránh phải download mỗi lần setup (420MB)
- ✅ Sử dụng Git LFS để quản lý file lớn
- ✅ Model nhỏ và cần thiết cho VectorDB

**Nếu không muốn model trong repo:**
1. Xóa folder `data/models/`
2. Download runtime:
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"
```

**Git LFS Configuration:**
```bash
# .gitattributes
*.bin filter=lfs diff=lfs merge=lfs -text
*.json filter=lfs diff=lfs merge=lfs -text
```

Files tracked by LFS:
- `pytorch_model.bin` (420MB)
- `tokenizer.json` (2.3MB)

## 📄 License

MIT License

## 🤝 Contributing

1. Fork repo
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -m "Add new feature"`
4. Push: `git push origin feature/new-feature`
5. Open Pull Request

## 📞 Contact

- GitHub: [jian131/agent-bds](https://github.com/jian131/agent-bds)
- Issues: [agent-bds/issues](https://github.com/jian131/agent-bds/issues)

---

Made with ❤️ by BDS Agent Team
