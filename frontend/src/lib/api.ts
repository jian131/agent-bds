import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Types
export interface Listing {
  id: string;
  title: string | null;
  description: string | null;
  price_display: string | null;
  price_number: number | null;
  price_per_m2: number | null;
  area_m2: number | null;
  address: string | null;
  district: string | null;
  ward: string | null;
  city: string | null;
  property_type: string | null;
  bedrooms: number | null;
  bathrooms: number | null;
  floors: number | null;
  direction: string | null;
  contact_name: string | null;
  contact_phone: string | null;
  source_url: string | null;
  source_platform: string | null;
  status: string;
  scraped_at: string;
  created_at: string;
  updated_at: string;
}

export interface SearchRequest {
  query: string;
  district?: string;
  property_type?: string;
  price_min?: number;
  price_max?: number;
  area_min?: number;
  area_max?: number;
  platforms?: string[];
  limit?: number;
}

export interface SearchResponse {
  listings: Listing[];
  total: number;
  query: string;
  search_time_ms: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface AnalyticsResponse {
  total_listings: number;
  active_listings: number;
  platforms: { platform: string; count: number; percentage: number }[];
  districts: { district: string; count: number; avg_price: number | null; avg_price_per_m2: number | null }[];
  scrape_stats: {
    total_scrapes: number;
    successful_scrapes: number;
    total_listings_found: number;
    total_new_listings: number;
    avg_duration_seconds: number;
  };
  last_updated: string;
}

export interface District {
  name: string;
  price_range_per_m2: {
    min: number;
    max: number;
    display: string;
  };
}

// API functions
export const searchListings = async (params: SearchRequest): Promise<SearchResponse> => {
  const { data } = await api.post("/api/v1/search", params);
  return data;
};

export const quickSearch = async (query: string, limit = 20): Promise<Listing[]> => {
  const { data } = await api.get("/api/v1/search/quick", { params: { q: query, limit } });
  return data.listings;
};

export const getListings = async (params: {
  page?: number;
  size?: number;
  district?: string;
  property_type?: string;
  status?: string;
  sort_by?: string;
  sort_order?: string;
}): Promise<PaginatedResponse<Listing>> => {
  const { data } = await api.get("/api/v1/listings", { params });
  return data;
};

export const getListing = async (id: string): Promise<Listing> => {
  const { data } = await api.get(`/api/v1/listings/${id}`);
  return data;
};

export const getSimilarListings = async (id: string, limit = 5): Promise<Listing[]> => {
  const { data } = await api.get(`/api/v1/listings/${id}/similar`, { params: { limit } });
  return data.listings;
};

export const getAnalytics = async (): Promise<AnalyticsResponse> => {
  const { data } = await api.get("/api/v1/analytics");
  return data;
};

export const getPriceTrends = async (params: {
  district?: string;
  property_type?: string;
  days?: number;
}): Promise<{ data: { date: string; avg_price_per_m2: number; count: number }[] }> => {
  const { data } = await api.get("/api/v1/analytics/price-trends", { params });
  return data;
};

export const getMarketOverview = async (): Promise<{
  districts: {
    district: string;
    count: number;
    actual_avg_per_m2: number | null;
    expected_min_per_m2: number | null;
    expected_max_per_m2: number | null;
  }[];
}> => {
  const { data } = await api.get("/api/v1/analytics/market-overview");
  return data;
};

export const getDistricts = async (): Promise<{ districts: District[] }> => {
  const { data } = await api.get("/api/v1/districts");
  return data;
};

export const getPropertyTypes = async (): Promise<{ property_types: Record<string, string> }> => {
  const { data } = await api.get("/api/v1/property-types");
  return data;
};

export const getHealth = async (): Promise<{ status: string; services: Record<string, string> }> => {
  const { data } = await api.get("/health");
  return data;
};
