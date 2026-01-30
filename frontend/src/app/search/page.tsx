'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  Search, Loader2, MapPin, Home, DollarSign, Maximize2,
  Phone, MessageCircle, Mail, ExternalLink, ChevronDown,
  SlidersHorizontal, X, Facebook, Check, Copy, Eye
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast, Toaster } from 'sonner';

// Types
interface Contact {
  phones: string[];
  zalo: string[];
  facebook: string[];
  email: string[];
  name: string;
  phone?: string;
}

interface Location {
  address: string;
  district: string;
  city?: string;
}

interface Listing {
  id: string;
  title: string;
  price_text: string;
  price_number: number;
  area_m2: number;
  area_text?: string;
  location: Location;
  contact: Contact;
  images: string[];
  source_url: string;
  source_platform: string;
  bedrooms?: number;
  bathrooms?: number;
  description?: string;
}

interface StreamMessage {
  type: 'status' | 'result' | 'complete';
  message?: string;
  data?: Listing;
  total?: number;
  time?: number;
  platforms?: string[];
}

// Components
function SearchInput({
  value,
  onChange,
  onSearch,
  isSearching
}: {
  value: string;
  onChange: (v: string) => void;
  onSearch: () => void;
  isSearching: boolean;
}) {
  return (
    <div className="relative">
      <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && onSearch()}
        placeholder='VD: "chung cư 2 phòng ngủ Cầu Giấy 2-3 tỷ"'
        className="w-full pl-12 pr-4 py-4 rounded-2xl border-2 border-slate-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 outline-none transition-all text-lg bg-white"
        disabled={isSearching}
      />
    </div>
  );
}

function StatusMessage({ message }: { message: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex items-center gap-3 py-3 px-4 bg-blue-50 border border-blue-100 rounded-xl text-blue-700"
    >
      <Loader2 className="w-4 h-4 animate-spin" />
      <span>{message}</span>
    </motion.div>
  );
}

function SourceBadge({ platform }: { platform: string }) {
  const colors: Record<string, string> = {
    'batdongsan.com.vn': 'bg-red-100 text-red-700',
    'chotot.com': 'bg-orange-100 text-orange-700',
    'mogi.vn': 'bg-green-100 text-green-700',
    'alonhadat.com.vn': 'bg-purple-100 text-purple-700',
    'facebook': 'bg-blue-100 text-blue-700',
    'facebook_marketplace': 'bg-blue-100 text-blue-700',
  };

  const names: Record<string, string> = {
    'batdongsan.com.vn': 'Batdongsan',
    'chotot.com': 'Chợ Tốt',
    'mogi.vn': 'Mogi',
    'alonhadat.com.vn': 'Alonhadat',
    'facebook': 'Facebook',
    'facebook_marketplace': 'FB Market',
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[platform] || 'bg-slate-100 text-slate-700'}`}>
      {names[platform] || platform}
    </span>
  );
}

function ContactReveal({ contact, listingId }: { contact: Contact; listingId: string }) {
  const [revealed, setRevealed] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  const copyToClipboard = (text: string, type: string) => {
    navigator.clipboard.writeText(text);
    setCopied(type);
    toast.success(`Đã copy ${type}!`);
    setTimeout(() => setCopied(null), 2000);
  };

  if (!revealed) {
    const hasContact = contact.phones?.length > 0 || contact.zalo?.length > 0 || contact.facebook?.length > 0;

    return (
      <button
        onClick={() => setRevealed(true)}
        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-medium hover:shadow-lg transition-all hover:scale-[1.02]"
      >
        <Eye className="w-4 h-4" />
        {hasContact ? 'Xem liên hệ' : 'Không có liên hệ'}
      </button>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      className="space-y-2"
    >
      {contact.name && (
        <div className="text-sm text-slate-600">
          <span className="font-medium">Người đăng:</span> {contact.name}
        </div>
      )}

      {contact.phones?.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {contact.phones.map((phone, i) => (
            <button
              key={i}
              onClick={() => copyToClipboard(phone, 'SĐT')}
              className="flex items-center gap-2 px-3 py-2 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors"
            >
              <Phone className="w-4 h-4" />
              {phone}
              {copied === 'SĐT' ? <Check className="w-4 h-4" /> : <Copy className="w-3 h-3" />}
            </button>
          ))}
        </div>
      )}

      {contact.zalo?.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {contact.zalo.map((zalo, i) => (
            <a
              key={i}
              href={`https://zalo.me/${zalo}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-3 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors"
            >
              <MessageCircle className="w-4 h-4" />
              Zalo: {zalo}
              <ExternalLink className="w-3 h-3" />
            </a>
          ))}
        </div>
      )}

      {contact.facebook?.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {contact.facebook.map((fb, i) => (
            <a
              key={i}
              href={fb.startsWith('http') ? fb : `https://facebook.com/${fb}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-3 py-2 bg-indigo-50 text-indigo-700 rounded-lg hover:bg-indigo-100 transition-colors"
            >
              <Facebook className="w-4 h-4" />
              Facebook
              <ExternalLink className="w-3 h-3" />
            </a>
          ))}
        </div>
      )}

      {contact.email?.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {contact.email.map((email, i) => (
            <a
              key={i}
              href={`mailto:${email}`}
              className="flex items-center gap-2 px-3 py-2 bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 transition-colors"
            >
              <Mail className="w-4 h-4" />
              {email}
            </a>
          ))}
        </div>
      )}
    </motion.div>
  );
}

function ListingCard({ listing, index }: { listing: Listing; index: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="bg-white rounded-2xl border border-slate-200 overflow-hidden hover:shadow-lg transition-all"
    >
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-3 mb-3">
          <h3 className="font-semibold text-slate-900 line-clamp-2 flex-1">
            {listing.title}
          </h3>
          <SourceBadge platform={listing.source_platform} />
        </div>

        {/* Key Info */}
        <div className="flex flex-wrap gap-3 mb-3">
          <div className="flex items-center gap-1.5 text-green-600 font-semibold">
            <DollarSign className="w-4 h-4" />
            {listing.price_text || 'Thương lượng'}
          </div>

          {listing.area_m2 > 0 && (
            <div className="flex items-center gap-1.5 text-slate-600">
              <Maximize2 className="w-4 h-4" />
              {listing.area_text || `${listing.area_m2} m²`}
            </div>
          )}

          {listing.bedrooms && listing.bedrooms > 0 && (
            <div className="flex items-center gap-1.5 text-slate-600">
              <Home className="w-4 h-4" />
              {listing.bedrooms} PN
            </div>
          )}
        </div>

        {/* Location */}
        <div className="flex items-start gap-1.5 text-slate-500 text-sm mb-4">
          <MapPin className="w-4 h-4 shrink-0 mt-0.5" />
          <span className="line-clamp-1">{listing.location?.address || 'Không rõ địa chỉ'}</span>
        </div>

        {/* Expand/Collapse */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
        >
          {expanded ? 'Thu gọn' : 'Xem chi tiết'}
          <ChevronDown className={`w-4 h-4 transition-transform ${expanded ? 'rotate-180' : ''}`} />
        </button>
      </div>

      {/* Expanded Content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-slate-100"
          >
            <div className="p-4 space-y-4">
              {/* Description */}
              {listing.description && (
                <div className="text-sm text-slate-600">
                  <p className="line-clamp-4">{listing.description}</p>
                </div>
              )}

              {/* Images */}
              {listing.images?.length > 0 && (
                <div className="flex gap-2 overflow-x-auto pb-2">
                  {listing.images.slice(0, 4).map((img, i) => (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      key={i}
                      src={img}
                      alt={`${listing.title} - ${i + 1}`}
                      className="w-24 h-24 object-cover rounded-lg shrink-0"
                      loading="lazy"
                    />
                    ))}
                </div>
              )}

              {/* Contact */}
              <div className="pt-2 border-t border-slate-100">
                <ContactReveal contact={listing.contact} listingId={listing.id} />
              </div>

              {/* Source Link */}
              <a
                href={listing.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700"
              >
                <ExternalLink className="w-4 h-4" />
                Xem trên {listing.source_platform}
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function FilterBar({
  onFilter
}: {
  onFilter: (filters: Record<string, string>) => void;
}) {
  const [showFilters, setShowFilters] = useState(false);
  const [priceRange, setPriceRange] = useState('');
  const [areaRange, setAreaRange] = useState('');
  const [district, setDistrict] = useState('');

  const districts = [
    'Ba Đình', 'Hoàn Kiếm', 'Tây Hồ', 'Long Biên', 'Cầu Giấy',
    'Đống Đa', 'Hai Bà Trưng', 'Hoàng Mai', 'Thanh Xuân', 'Hà Đông',
    'Nam Từ Liêm', 'Bắc Từ Liêm'
  ];

  return (
    <div className="mb-4">
      <button
        onClick={() => setShowFilters(!showFilters)}
        className="flex items-center gap-2 px-4 py-2 bg-slate-100 rounded-xl text-slate-700 hover:bg-slate-200 transition-colors"
      >
        <SlidersHorizontal className="w-4 h-4" />
        Bộ lọc
        <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
      </button>

      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="mt-3 p-4 bg-white rounded-xl border border-slate-200"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Quận/Huyện</label>
                <select
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                  title="Chọn quận/huyện"
                  aria-label="Chọn quận/huyện"
                >
                  <option value="">Tất cả</option>
                  {districts.map(d => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Khoảng giá</label>
                <select
                  value={priceRange}
                  onChange={(e) => setPriceRange(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                  title="Chọn khoảng giá"
                  aria-label="Chọn khoảng giá"
                >
                  <option value="">Tất cả</option>
                  <option value="0-1">Dưới 1 tỷ</option>
                  <option value="1-2">1 - 2 tỷ</option>
                  <option value="2-3">2 - 3 tỷ</option>
                  <option value="3-5">3 - 5 tỷ</option>
                  <option value="5-10">5 - 10 tỷ</option>
                  <option value="10+">Trên 10 tỷ</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Diện tích</label>
                <select
                  value={areaRange}
                  onChange={(e) => setAreaRange(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg"
                  title="Chọn diện tích"
                  aria-label="Chọn diện tích"
                >
                  <option value="">Tất cả</option>
                  <option value="0-50">Dưới 50m²</option>
                  <option value="50-80">50 - 80m²</option>
                  <option value="80-100">80 - 100m²</option>
                  <option value="100-150">100 - 150m²</option>
                  <option value="150+">Trên 150m²</option>
                </select>
              </div>
            </div>

            <button
              onClick={() => onFilter({ district, priceRange, areaRange })}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Áp dụng
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Main Page Component
export default function SearchPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<Listing[]>([]);
  const [statusMessage, setStatusMessage] = useState('');
  const [searchStats, setSearchStats] = useState<{ total: number; time: number; platforms: string[] } | null>(null);
  const [filters, setFilters] = useState<Record<string, string>>({});

  const resultsRef = useRef<HTMLDivElement>(null);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    setResults([]);
    setStatusMessage('');
    setSearchStats(null);

    // Update URL
    router.push(`/search?q=${encodeURIComponent(query)}`);

    try {
      // Use EventSource for streaming
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/search/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, max_results: 50 }),
      });

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(line => line.trim());

        for (const line of lines) {
          try {
            // Handle SSE format: data: {...}
            const jsonStr = line.startsWith('data: ') ? line.slice(6) : line;
            if (!jsonStr || jsonStr === '[DONE]') continue;

            const message: StreamMessage = JSON.parse(jsonStr);

            if (message.type === 'status') {
              setStatusMessage(message.message || '');
            } else if (message.type === 'result' && message.data) {
              setResults(prev => [...prev, message.data!]);
            } else if (message.type === 'complete') {
              setSearchStats({
                total: message.total || 0,
                time: message.time || 0,
                platforms: message.platforms || [],
              });
              setStatusMessage('');
            }
          } catch {
            // Skip invalid JSON
          }
        }
      }

      toast.success(`Tìm thấy ${results.length} bất động sản!`);

    } catch (error) {
      console.error('Search error:', error);
      toast.error('Có lỗi xảy ra. Đang thử lại...');

      // Fallback to non-streaming API
      try {
        const fallbackResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/search`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, max_results: 50 }),
        });

        if (fallbackResponse.ok) {
          const data = await fallbackResponse.json();
          setResults(data.results || []);
          setSearchStats({
            total: data.total || data.results?.length || 0,
            time: data.execution_time_ms ? data.execution_time_ms / 1000 : 0,
            platforms: [],
          });
        }
      } catch (fallbackError) {
        console.error('Fallback error:', fallbackError);
      }

    } finally {
      setIsSearching(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, router]);

  // Filter results
  const filteredResults = results.filter(listing => {
    if (filters.district && listing.location?.district !== filters.district) {
      return false;
    }

    if (filters.priceRange) {
      const [min, max] = filters.priceRange.split('-').map(v => parseFloat(v) * 1_000_000_000);
      if (listing.price_number < min) return false;
      if (max && listing.price_number > max) return false;
    }

    if (filters.areaRange) {
      const [min, max] = filters.areaRange.split('-').map(parseFloat);
      if (listing.area_m2 < min) return false;
      if (max && listing.area_m2 > max) return false;
    }

    return true;
  });

  // Auto-search if query param exists
  useEffect(() => {
    const q = searchParams.get('q');
    if (q && q !== query) {
      setQuery(q);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Toaster position="top-center" richColors />

      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <a href="/" className="flex items-center gap-2">
              <Home className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                BĐS Search
              </h1>
            </a>
            <div className="text-sm text-slate-600">
              Tìm kiếm thông minh từ 10+ nguồn
            </div>
          </div>
        </div>
      </header>

      {/* Search Section */}
      <div className="max-w-4xl mx-auto px-4 pt-8 pb-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {!results.length && !isSearching && (
            <>
              <h2 className="text-4xl md:text-5xl font-bold text-center mb-4 bg-gradient-to-r from-slate-900 via-blue-900 to-indigo-900 bg-clip-text text-transparent">
                Tìm nhà mơ ước của bạn
              </h2>
              <p className="text-center text-slate-600 mb-8 text-lg">
                Tìm kiếm thông minh từ Batdongsan, Chợ Tốt, Mogi, Facebook...
              </p>
            </>
          )}

          {/* Search Form */}
          <div className="space-y-4">
            <SearchInput
              value={query}
              onChange={setQuery}
              onSearch={handleSearch}
              isSearching={isSearching}
            />

            <button
              onClick={handleSearch}
              disabled={isSearching || !query.trim()}
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-4 rounded-2xl font-semibold hover:shadow-lg hover:scale-[1.02] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              {isSearching ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Đang tìm kiếm...
                </span>
              ) : (
                'Tìm kiếm'
              )}
            </button>
          </div>

          {/* Status Message */}
          <AnimatePresence mode="wait">
            {statusMessage && (
              <div className="mt-4">
                <StatusMessage message={statusMessage} />
              </div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* Results Section */}
      <div ref={resultsRef} className="max-w-7xl mx-auto px-4 pb-16">
        {/* Stats */}
        {searchStats && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-4 flex items-center justify-between"
          >
            <div className="text-slate-600">
              Tìm thấy <span className="font-semibold text-slate-900">{searchStats.total}</span> kết quả
              {searchStats.time > 0 && (
                <span> trong <span className="font-semibold">{searchStats.time.toFixed(1)}s</span></span>
              )}
            </div>
            <div className="flex gap-2">
              {Array.isArray(searchStats.platforms) && searchStats.platforms.map(p => (
                <SourceBadge key={p} platform={p} />
              ))}
            </div>
          </motion.div>
        )}

        {/* Filters */}
        {results.length > 0 && (
          <FilterBar onFilter={setFilters} />
        )}

        {/* Results Grid */}
        {filteredResults.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredResults.map((listing, index) => (
              <ListingCard key={listing.id || index} listing={listing} index={index} />
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isSearching && results.length === 0 && query && (
          <div className="text-center py-12">
            <div className="text-slate-400 text-lg">
              Không tìm thấy kết quả cho &quot;{query}&quot;
            </div>
            <p className="text-slate-500 mt-2">
              Thử tìm kiếm với từ khóa khác
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
