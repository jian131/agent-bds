'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Home, Zap, Shield, BarChart3, Globe, Facebook, MessageCircle } from 'lucide-react';
import { motion } from 'framer-motion';

const FEATURES = [
  {
    icon: Globe,
    title: '10+ Nguồn dữ liệu',
    description: 'Batdongsan, Chợ Tốt, Mogi, Alonhadat, Facebook Groups...',
  },
  {
    icon: Zap,
    title: 'Tốc độ cực nhanh',
    description: 'Crawl song song hàng chục URLs, kết quả trong vài giây.',
  },
  {
    icon: Shield,
    title: '100% dữ liệu thật',
    description: 'Dữ liệu trực tiếp từ websites, không tin ảo.',
  },
  {
    icon: MessageCircle,
    title: 'Đầy đủ liên hệ',
    description: 'SĐT, Zalo, Facebook, Email của người đăng.',
  },
];

const PLATFORMS = [
  'batdongsan.com.vn',
  'chotot.com',
  'mogi.vn',
  'alonhadat.com.vn',
  'nhadat247.com.vn',
  'muaban.net',
  'facebook.com',
];

export default function HomePage() {
  const router = useRouter();
  const [query, setQuery] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query)}`);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Hero Section */}
      <section className="pt-20 pb-16">
        <div className="max-w-4xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            {/* Logo */}
            <div className="flex items-center justify-center gap-3 mb-8">
              <Home className="w-12 h-12 text-blue-600" />
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                BĐS Search
              </h1>
            </div>

            {/* Headline */}
            <h2 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-slate-900 via-blue-900 to-indigo-900 bg-clip-text text-transparent leading-tight">
              Tìm nhà mơ ước
              <br />
              <span className="text-blue-600">nhanh hơn 10x</span>
            </h2>

            <p className="text-xl text-slate-600 mb-8 max-w-2xl mx-auto">
              Tìm kiếm thông minh từ 10+ nguồn: Batdongsan, Chợ Tốt, Mogi, Facebook Groups...
              <br />
              Đầy đủ thông tin liên hệ trong một nốt nhạc.
            </p>

            {/* Search Box */}
            <form onSubmit={handleSearch} className="max-w-2xl mx-auto">
              <div className="relative">
                <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-6 h-6 text-slate-400" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder='VD: "chung cư 2PN Cầu Giấy giá 2-3 tỷ"'
                  className="w-full pl-14 pr-6 py-5 rounded-2xl border-2 border-slate-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 outline-none transition-all text-lg bg-white shadow-lg"
                />
              </div>
              <button
                type="submit"
                className="mt-4 w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-5 rounded-2xl font-semibold text-lg hover:shadow-xl hover:scale-[1.02] transition-all"
              >
                Tìm kiếm ngay
              </button>
            </form>

            {/* Platforms */}
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              {PLATFORMS.map((platform) => (
                <span
                  key={platform}
                  className="px-3 py-1.5 bg-white/80 rounded-full text-sm text-slate-600 border border-slate-200"
                >
                  {platform}
                </span>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 bg-white/50">
        <div className="max-w-6xl mx-auto px-4">
          <h3 className="text-3xl font-bold text-center mb-12 text-slate-900">
            Tại sao chọn BĐS Search?
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURES.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white p-6 rounded-2xl border border-slate-200 hover:shadow-lg transition-all"
              >
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-blue-600" />
                </div>
                <h4 className="font-semibold text-lg text-slate-900 mb-2">
                  {feature.title}
                </h4>
                <p className="text-slate-600 text-sm">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-16">
        <div className="max-w-4xl mx-auto px-4">
          <h3 className="text-3xl font-bold text-center mb-12 text-slate-900">
            Cách hoạt động
          </h3>

          <div className="space-y-6">
            {[
              { step: '1', title: 'Nhập yêu cầu', desc: 'Mô tả bất động sản bạn muốn tìm bằng ngôn ngữ tự nhiên' },
              { step: '2', title: 'AI tìm kiếm', desc: 'Hệ thống crawl song song từ 10+ websites và Facebook groups' },
              { step: '3', title: 'Xem kết quả', desc: 'Nhận danh sách BĐS với đầy đủ thông tin liên hệ ngay lập tức' },
            ].map((item, index) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.2 }}
                className="flex items-start gap-4"
              >
                <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold shrink-0">
                  {item.step}
                </div>
                <div>
                  <h4 className="font-semibold text-lg text-slate-900">{item.title}</h4>
                  <p className="text-slate-600">{item.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-gradient-to-r from-blue-600 to-indigo-600">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h3 className="text-3xl font-bold text-white mb-4">
            Sẵn sàng tìm nhà?
          </h3>
          <p className="text-blue-100 mb-8">
            Bắt đầu tìm kiếm miễn phí ngay hôm nay
          </p>
          <button
            onClick={() => router.push('/search')}
            className="bg-white text-blue-600 px-8 py-4 rounded-xl font-semibold hover:shadow-lg transition-all hover:scale-105"
          >
            Bắt đầu tìm kiếm
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-slate-900 text-slate-400">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <p>© 2024 BĐS Search. Powered by Crawl4AI + Next.js</p>
        </div>
      </footer>
    </div>
  );
}
