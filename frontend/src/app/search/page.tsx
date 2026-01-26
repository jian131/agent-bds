"use client";

import { useSearchParams } from "next/navigation";
import { useState, useEffect, Suspense } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { Header, Footer } from "@/components/layout/header";
import { SearchBox } from "@/components/search/search-box";
import { FilterPanel } from "@/components/search/filter-panel";
import { ListingCard, ListingCardSkeleton } from "@/components/listings/listing-card";
import { searchListings, type SearchRequest } from "@/lib/api";

function SearchContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";

  const [query, setQuery] = useState(initialQuery);
  const [filters, setFilters] = useState<{
    district?: string;
    property_type?: string;
    price_min?: string;
    price_max?: string;
    area_min?: string;
    area_max?: string;
  }>({});

  const searchRequest: SearchRequest = {
    query,
    district: filters.district,
    property_type: filters.property_type,
    price_min: filters.price_min ? parseInt(filters.price_min) : undefined,
    price_max: filters.price_max ? parseInt(filters.price_max) : undefined,
    area_min: filters.area_min ? parseInt(filters.area_min) : undefined,
    area_max: filters.area_max ? parseInt(filters.area_max) : undefined,
    limit: 50,
  };

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["search", searchRequest],
    queryFn: () => searchListings(searchRequest),
    enabled: !!query,
  });

  const handleSearch = (newQuery: string) => {
    setQuery(newQuery);
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="flex-1 container py-8">
        {/* Search Box */}
        <div className="mb-6">
          <SearchBox
            defaultValue={query}
            onSearch={handleSearch}
            placeholder="Nhập yêu cầu tìm kiếm của bạn..."
          />
        </div>

        {/* Filters */}
        <div className="mb-6">
          <FilterPanel
            filters={filters}
            onChange={setFilters}
            onReset={() => setFilters({})}
          />
        </div>

        {/* Results */}
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold">
            {query ? `Kết quả tìm kiếm "${query}"` : "Nhập từ khóa để tìm kiếm"}
          </h2>
          {data && (
            <span className="text-muted-foreground">
              {data.total} kết quả ({data.search_time_ms}ms)
            </span>
          )}
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="mt-4 text-muted-foreground">
              AI đang tìm kiếm trên các nền tảng...
            </p>
          </div>
        )}

        {/* Error State */}
        {isError && (
          <div className="text-center py-12">
            <p className="text-destructive">Đã xảy ra lỗi: {(error as Error).message}</p>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && query && data?.listings.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">
              Không tìm thấy kết quả phù hợp. Thử thay đổi từ khóa hoặc bộ lọc.
            </p>
          </div>
        )}

        {/* Results Grid */}
        {data && data.listings.length > 0 && (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {data.listings.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>
        )}

        {/* Initial State */}
        {!query && !isLoading && (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <ListingCardSkeleton key={i} />
            ))}
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><Loader2 className="h-8 w-8 animate-spin" /></div>}>
      <SearchContent />
    </Suspense>
  );
}
