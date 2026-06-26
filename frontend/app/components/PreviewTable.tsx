"use client";

interface PreviewTableProps {
  columns: string[];
  rows: Record<string, unknown>[];
}

export default function PreviewTable({ columns, rows }: PreviewTableProps) {
  return (
    <div className="w-full max-w-3xl mx-auto px-6 mt-4">
      <div className="overflow-x-auto rounded-lg border border-chroma-border">
        <table className="w-full text-sm font-mono">
          <thead>
            <tr className="bg-chroma-muted">
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-4 py-2 text-left font-medium text-chroma-fg text-xs"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={i}
                className="border-t border-chroma-border"
              >
                {columns.map((col) => (
                  <td
                    key={col}
                    className="px-4 py-2 text-chroma-fg text-xs"
                  >
                    {row[col] != null ? String(row[col]) : ""}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-chroma-muted-fg mt-2">
        Showing first {rows.length} rows
      </p>
    </div>
  );
}
