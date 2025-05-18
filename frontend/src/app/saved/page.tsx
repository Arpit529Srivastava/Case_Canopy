"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Bookmark, Clock, Search, Trash2, ExternalLink } from "lucide-react";
import { getAuthState } from "@/utils/auth";

interface SavedCase {
  id: string;
  query: string;
  analysis: string;
  date: string;
  sourcesCount: number;
}

export default function SavedCasesPage() {
  const router = useRouter();
  const [savedCases, setSavedCases] = useState<SavedCase[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check authentication
    const authState = getAuthState();
    if (!authState?.token) {
      router.push("/login");
      return;
    }

    // Load saved cases from localStorage
    try {
      const cases = JSON.parse(localStorage.getItem("savedCases") || "[]");
      setSavedCases(cases);
    } catch (error) {
      console.error("Error loading saved cases:", error);
    } finally {
      setLoading(false);
    }
  }, [router]);

  const handleDeleteCase = (id: string) => {
    // Filter out the case with the given id
    const updatedCases = savedCases.filter((item) => item.id !== id);

    // Update state and localStorage
    setSavedCases(updatedCases);
    localStorage.setItem("savedCases", JSON.stringify(updatedCases));
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return "Unknown date";
    }
  };

  return (
    <div className="min-h-screen bg-black text-white pb-16 pt-24">
      {/* Background gradients */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-[#CD9A3C]/20 via-black to-black opacity-80" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,_var(--tw-gradient-stops))] from-[#E3B448]/10 via-black to-black opacity-80" />

      <div className="relative max-w-7xl mx-auto px-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-12"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <span className="h-6 w-1 bg-[#E3B448] rounded-full mr-3"></span>
              <h1 className="text-2xl font-serif font-bold text-white">
                Saved Cases
              </h1>
            </div>
            <Link
              href="/dashboard"
              className="flex items-center text-sm text-[#E3B448] hover:underline"
            >
              Back to Dashboard
            </Link>
          </div>
          <p className="text-gray-300 max-w-2xl">
            Access your saved legal analyses and case research
          </p>
          <div className="mt-4 h-1 w-40 bg-gradient-to-r from-transparent via-[#E3B448]/80 to-transparent"></div>
        </motion.div>

        {/* Content */}
        {loading ? (
          <div className="grid grid-cols-1 gap-6">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="animate-pulse h-40 bg-gradient-to-br from-[#1A1A1A] to-black rounded-2xl border border-[#CD9A3C]/20"
              ></div>
            ))}
          </div>
        ) : savedCases.length > 0 ? (
          <div className="grid grid-cols-1 gap-6">
            {savedCases.map((caseItem) => (
              <motion.div
                key={caseItem.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-gradient-to-br from-[#1A1A1A] to-black rounded-2xl overflow-hidden shadow-xl border border-[#CD9A3C]/20 p-6"
              >
                <div className="flex flex-col md:flex-row md:items-start gap-4">
                  <div className="flex-1">
                    <div className="flex items-center mb-3">
                      <Bookmark className="h-5 w-5 text-[#E3B448] mr-2" />
                      <h3 className="text-lg font-serif text-white line-clamp-1">
                        {caseItem.query}
                      </h3>
                    </div>

                    <p className="text-gray-300 text-sm mb-4 line-clamp-3">
                      {caseItem.analysis.substring(0, 200)}...
                    </p>

                    <div className="flex flex-wrap items-center text-sm text-gray-400 gap-x-4 gap-y-2">
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 mr-1" />
                        <span>{formatDate(caseItem.date)}</span>
                      </div>

                      {caseItem.sourcesCount > 0 && (
                        <div className="flex items-center">
                          <span className="px-2 py-0.5 text-xs bg-[#E3B448]/20 text-[#E3B448] rounded">
                            {caseItem.sourcesCount} Sources
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-row md:flex-col gap-3 justify-end">
                    <button
                      onClick={() => handleDeleteCase(caseItem.id)}
                      className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                      title="Delete case"
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>

                    <Link
                      href="/response"
                      className="p-2 text-gray-400 hover:text-[#E3B448] hover:bg-[#E3B448]/10 rounded-lg transition-colors"
                      title="View full analysis"
                    >
                      <ExternalLink className="h-5 w-5" />
                    </Link>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="bg-gradient-to-br from-[#1A1A1A] to-black rounded-2xl overflow-hidden shadow-xl border border-[#CD9A3C]/20 p-8 text-center"
          >
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[#E3B448]/20 mb-4">
              <Bookmark className="h-8 w-8 text-[#E3B448]" />
            </div>
            <h3 className="text-lg font-serif text-white mb-3">
              No saved cases yet
            </h3>
            <p className="text-gray-400 max-w-md mx-auto mb-6">
              When you save a case from your analysis results, it will appear
              here for easy access
            </p>
            <Link
              href="/search"
              className="inline-flex items-center px-4 py-2 bg-[#E3B448]/20 text-[#E3B448] rounded-lg border border-[#CD9A3C]/30 hover:bg-[#E3B448]/30 transition-colors"
            >
              <Search className="h-4 w-4 mr-2" />
              Start a new search
            </Link>
          </motion.div>
        )}
      </div>

      <style jsx global>{`
        @import url("https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&display=swap");

        .font-serif {
          font-family: "Playfair Display", serif;
        }
      `}</style>
    </div>
  );
}
