"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search, Loader2, Sparkles } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface SearchBoxProps {
  className?: string;
  placeholder?: string;
  defaultValue?: string;
  onSearch?: (query: string) => void;
  size?: "default" | "lg";
  showAIBadge?: boolean;
}

const EXAMPLE_QUERIES = [
  "Nhà 3 tầng Cầu Giấy dưới 5 tỷ",
  "Chung cư 2 phòng ngủ gần hồ Tây",
  "Đất nền Long Biên 50-80m2",
  "Biệt thự Thanh Xuân có gara",
];

export function SearchBox({
  className,
  placeholder = "Tìm kiếm bất động sản...",
  defaultValue = "",
  onSearch,
  size = "default",
  showAIBadge = true,
}: SearchBoxProps) {
  const [query, setQuery] = useState(defaultValue);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);

    if (onSearch) {
      await onSearch(query);
      setIsLoading(false);
    } else {
      router.push(`/search?q=${encodeURIComponent(query)}`);
    }
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
  };

  return (
    <div className={cn("w-full", className)}>
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <Search className={cn(
            "absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground",
            size === "lg" ? "h-5 w-5" : "h-4 w-4"
          )} />
          <Input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            className={cn(
              "pl-10 pr-24",
              size === "lg" && "h-14 text-lg"
            )}
          />
          {showAIBadge && (
            <div className="absolute right-20 top-1/2 -translate-y-1/2 hidden sm:flex items-center gap-1 text-xs text-muted-foreground">
              <Sparkles className="h-3 w-3" />
              <span>AI</span>
            </div>
          )}
          <Button
            type="submit"
            disabled={isLoading || !query.trim()}
            className={cn(
              "absolute right-1 top-1/2 -translate-y-1/2",
              size === "lg" && "h-12"
            )}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              "Tìm kiếm"
            )}
          </Button>
        </div>
      </form>

      {/* Example queries */}
      <div className="mt-3 flex flex-wrap gap-2">
        <span className="text-sm text-muted-foreground">Ví dụ:</span>
        {EXAMPLE_QUERIES.map((example) => (
          <button
            key={example}
            onClick={() => handleExampleClick(example)}
            className="text-sm text-primary hover:underline"
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  );
}
