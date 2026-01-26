"use client";

import { useQuery } from "@tanstack/react-query";
import { BarChart3, Building, TrendingUp, Activity } from "lucide-react";
import { Header, Footer } from "@/components/layout/header";
import {
  DistrictChart,
  PlatformChart,
  PriceTrendChart,
  StatsCard,
} from "@/components/analytics/charts";
import { Skeleton } from "@/components/ui/skeleton";
import { getAnalytics, getPriceTrends } from "@/lib/api";

export default function AnalyticsPage() {
  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ["analytics"],
    queryFn: getAnalytics,
  });

  const { data: trends } = useQuery({
    queryKey: ["price-trends"],
    queryFn: () => getPriceTrends({ days: 30 }),
  });

  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="flex-1 container py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Phân tích thị trường</h1>
          <p className="text-muted-foreground mt-1">
            Thống kê và xu hướng thị trường bất động sản Hà Nội
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
          {analyticsLoading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))
          ) : (
            <>
              <StatsCard
                title="Tổng tin đăng"
                value={analytics?.total_listings.toLocaleString() || "0"}
                description="Tất cả tin trong database"
                icon={<Building className="h-4 w-4 text-muted-foreground" />}
              />
              <StatsCard
                title="Tin đang hoạt động"
                value={analytics?.active_listings.toLocaleString() || "0"}
                description="Tin còn hiệu lực"
                icon={<Activity className="h-4 w-4 text-muted-foreground" />}
              />
              <StatsCard
                title="Lượt scrape 7 ngày"
                value={analytics?.scrape_stats.total_scrapes || "0"}
                description={`${analytics?.scrape_stats.total_new_listings || 0} tin mới`}
                icon={<TrendingUp className="h-4 w-4 text-muted-foreground" />}
              />
              <StatsCard
                title="Nguồn dữ liệu"
                value={analytics?.platforms.length || "0"}
                description="Nền tảng được thu thập"
                icon={<BarChart3 className="h-4 w-4 text-muted-foreground" />}
              />
            </>
          )}
        </div>

        {/* Charts */}
        <div className="grid gap-6 lg:grid-cols-2 mb-8">
          {analyticsLoading ? (
            <>
              <Skeleton className="h-[400px]" />
              <Skeleton className="h-[400px]" />
            </>
          ) : (
            <>
              <DistrictChart data={analytics?.districts || []} />
              <PlatformChart data={analytics?.platforms || []} />
            </>
          )}
        </div>

        {/* Price Trend */}
        {trends && (
          <div className="mb-8">
            <PriceTrendChart data={trends.data} />
          </div>
        )}

        {/* Scrape Stats Table */}
        {analytics && (
          <div className="rounded-lg border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">Thống kê thu thập dữ liệu</h3>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="text-center p-4 rounded-lg bg-muted/50">
                <div className="text-2xl font-bold text-primary">
                  {analytics.scrape_stats.total_scrapes}
                </div>
                <div className="text-sm text-muted-foreground">Tổng lượt scrape</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-muted/50">
                <div className="text-2xl font-bold text-green-600">
                  {analytics.scrape_stats.successful_scrapes}
                </div>
                <div className="text-sm text-muted-foreground">Thành công</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-muted/50">
                <div className="text-2xl font-bold text-blue-600">
                  {analytics.scrape_stats.total_listings_found.toLocaleString()}
                </div>
                <div className="text-sm text-muted-foreground">Tin tìm thấy</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-muted/50">
                <div className="text-2xl font-bold text-amber-600">
                  {analytics.scrape_stats.avg_duration_seconds.toFixed(1)}s
                </div>
                <div className="text-sm text-muted-foreground">Thời gian TB</div>
              </div>
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
