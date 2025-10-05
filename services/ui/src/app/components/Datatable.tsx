"use client";

import { motion } from "framer-motion";
import { useState } from "react";

interface DataTableProps<T> {
  data: T[];
  columns: {
    key: keyof T;
    label: string;
    render?: (value: any, row: T) => React.ReactNode;
  }[];
  pageSize?: number;
  scrollHeight?: string; // new
}

export default function DataTable<T extends { id: string }>({
  data,
  columns,
  pageSize = 10,
  scrollHeight = "500px",
}: DataTableProps<T>) {
  const [page, setPage] = useState(1);
  const totalPages = Math.ceil(data.length / pageSize);
  const startIndex = (page - 1) * pageSize;
  const pageData = data.slice(startIndex, startIndex + pageSize);

  return (
    <div className="rounded-xl overflow-hidden bg-white/5 border border-white/10 backdrop-blur-md">
      {/* Scrollable container */}
      <div
        className="overflow-y-auto scrollbar-thin scrollbar-thumb-cyan-600/40 scrollbar-track-transparent"
        style={{ maxHeight: scrollHeight }}
      >
        <motion.table
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="w-full text-sm min-w-max"
        >
          <thead className="bg-white/10 text-gray-300 uppercase tracking-wider text-xs sticky top-0 backdrop-blur-md z-10">
            <tr>
              {columns.map((col) => (
                <th
                  key={String(col.key)}
                  className="px-4 py-3 text-left border-b border-white/10"
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageData.map((row, i) => (
              <motion.tr
                key={row.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                className="border-b border-white/10 hover:bg-white/10 transition"
              >
                {columns.map((col) => (
                  <td key={String(col.key)} className="px-4 py-3">
                    {col.render
                      ? col.render((row as any)[col.key], row)
                      : (row as any)[col.key]}
                  </td>
                ))}
              </motion.tr>
            ))}
          </tbody>
        </motion.table>
      </div>

      {/* Pagination controls */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center py-4 space-x-4 text-gray-400">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 bg-white/10 rounded disabled:opacity-40 hover:bg-white/20 transition"
          >
            Prev
          </button>
          <span className="text-sm text-gray-300">
            Page <span className="text-cyan-400">{page}</span> / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1 bg-white/10 rounded disabled:opacity-40 hover:bg-white/20 transition"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
