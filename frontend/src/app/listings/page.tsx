"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { Header, Footer } from "@/components/layout/header";
import { FilterPanel } from "@/components/search/filter-panel";
import { ListingCard, ListingCardSkeleton } from "@/components/listings/listing-card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getListings } from "@/lib/api";

export default function ListingsPage() {
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState("desc");
  const [filters, setFilters] = useState<{
    district?: string;
    property_type?: string;
    price_min?: string;
    price_max?: string;
    area_min?: string;
    area_max?: string;
  }>({});

  const { data, isLoading, isError } = useQuery({
    queryKey: ["listings", page, sortBy, sortOrder, filters],
    queryFn: () =>
      getListings({
        page,
        size: 12,
        district: filters.district,
        property_type: filters.property_type,
        sort_by: sortBy,
        sort_order: sortOrder,
        status: "active",
      }),
  });

  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="flex-1 container py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">Danh sách tin BĐS</h1>
          <p className="text-muted-foreground mt-1">
            Tất cả tin đăng bất động sản được thu thập tự động
          </p>
        </div>

        {/* Filters */}
        <div className="mb-6">
          <FilterPanel
            filters={filters}
            onChange={setFilters}
            onReset={() => {
              setFilters({});
              setPage(1);
            }}
          />
        </div>

        {/* Sort & Count */}
        <div className="mb-4 flex items-center justify-between">
          <span className="text-muted-foreground">
            {data ? `${data.total} tin đăng` : "Đang tải..."}
          </span>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Sắp xếp:</span>
            <Select
              value={`${sortBy}-${sortOrder}`}
              onValueChange={(v) => {
                const [newSortBy, newSortOrder] = v.split("-");
                setSortBy(newSortBy);
                setSortOrder(newSortOrder);
                setPage(1);
              }}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="created_at-desc">Mới nhất</SelectItem>
                <SelectItem value="created_at-asc">Cũ nhất</SelectItem>
                <SelectItem value="price_number-asc">Giá thấp → cao</SelectItem>
                <SelectItem value="price_number-desc">Giá cao → thấp</SelectItem>
                <SelectItem value="area_m2-asc">Diện tích nhỏ → lớn</SelectItem>
                <SelectItem value="area_m2-desc">Diện tích lớn → nhỏ</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 12 }).map((_, i) => (
              <ListingCardSkeleton key={i} />
            ))}
          </div>
        )}

        {/* Error */}
        {isError && (
          <div className="text-center py-12">
            <p className="text-destructive">Đã xảy ra lỗi khi tải dữ liệu</p>
          </div>
        )}

        {/* Listings Grid */}
        {data && data.items.length > 0 && (
          <>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {data.items.map((listing) => (
                <ListingCard key={listing.id} listing={listing} />
              ))}
            </div>

            {/* Pagination */}
            <div className="mt-8 flex items-center justify-center gap-2">
              <Button
                variant="outline"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                Trang trước
              </Button>
              <span className="px-4 text-sm text-muted-foreground">
                Trang {page} / {data.pages}
              </span>
              <Button
                variant="outline"
                disabled={page >= data.pages}
                onClick={() => setPage(page + 1)}
              >
                Trang sau
              </Button>
            </div>
          </>
        )}

        {/* Empty */}
        {data && data.items.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">
              Không có tin đăng nào phù hợp với bộ lọc
            </p>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
