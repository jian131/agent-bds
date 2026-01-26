import Link from "next/link";
import { ArrowRight, Search, BarChart3, Bell, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SearchBox } from "@/components/search/search-box";
import { Header, Footer } from "@/components/layout/header";

const FEATURES = [
  {
    icon: Search,
    title: "Tìm kiếm thông minh",
    description:
      "AI tự động tìm kiếm trên nhiều nền tảng: Chợ Tốt, Batdongsan.com.vn, Mogi.vn...",
  },
  {
    icon: Zap,
    title: "100% dữ liệu thật",
    description:
      "Dữ liệu được scrape trực tiếp từ các website, không có tin giả hay tin ảo.",
  },
  {
    icon: BarChart3,
    title: "Phân tích thị trường",
    description:
      "Thống kê giá theo quận, xu hướng giá, so sánh với mức trung bình thị trường.",
  },
  {
    icon: Bell,
    title: "Thông báo tức thì",
    description:
      "Nhận thông báo qua Telegram khi có tin mới phù hợp với tiêu chí của bạn.",
  },
];

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="py-20 md:py-32 bg-gradient-to-b from-background to-muted/50">
          <div className="container px-4">
            <div className="mx-auto max-w-3xl text-center">
              <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
                Tìm kiếm BĐS
                <span className="text-primary"> thông minh</span>
                <br />
                với AI
              </h1>
              <p className="mt-6 text-lg text-muted-foreground">
                Hệ thống tự động tìm kiếm bất động sản trên nhiều nền tảng,
                phân tích giá thị trường và thông báo tin mới theo thời gian thực.
              </p>

              <div className="mt-10">
                <SearchBox size="lg" className="max-w-2xl mx-auto" />
              </div>

              <div className="mt-8 flex flex-wrap justify-center gap-4">
                <Button size="lg" asChild>
                  <Link href="/search">
                    Bắt đầu tìm kiếm
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild>
                  <Link href="/analytics">Xem thống kê</Link>
                </Button>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 bg-muted/50">
          <div className="container px-4">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold">Tính năng nổi bật</h2>
              <p className="mt-2 text-muted-foreground">
                Công nghệ AI giúp bạn tìm nhà nhanh và hiệu quả hơn
              </p>
            </div>

            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
              {FEATURES.map((feature) => (
                <div
                  key={feature.title}
                  className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm"
                >
                  <feature.icon className="h-12 w-12 text-primary mb-4" />
                  <h3 className="text-lg font-semibold">{feature.title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20">
          <div className="container px-4">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold">Sẵn sàng tìm nhà mơ ước?</h2>
              <p className="mt-4 text-muted-foreground">
                Bắt đầu tìm kiếm ngay hôm nay với hệ thống AI thông minh của chúng tôi.
                Hoàn toàn miễn phí!
              </p>
              <Button size="lg" className="mt-8" asChild>
                <Link href="/search">
                  Tìm kiếm ngay
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
