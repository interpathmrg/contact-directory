import React from 'react';

interface Props {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}

export default function Pagination({ currentPage, totalPages, pageSize, total, onPageChange, onPageSizeChange }: Props) {
  const from = Math.min((currentPage - 1) * pageSize + 1, total);
  const to = Math.min(currentPage * pageSize, total);

  const pages = buildPages(currentPage, totalPages);

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
      <div className="flex items-center gap-3 text-sm text-gray-600">
        <span>
          Mostrando <span className="font-medium">{from}–{to}</span> de{' '}
          <span className="font-medium">{total}</span>
        </span>
        <select
          value={pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        >
          {[10, 20, 50, 100].map((n) => (
            <option key={n} value={n}>{n} por página</option>
          ))}
        </select>
      </div>

      <nav className="flex items-center gap-1">
        <PageBtn onClick={() => onPageChange(1)} disabled={currentPage === 1} label="«" />
        <PageBtn onClick={() => onPageChange(currentPage - 1)} disabled={currentPage === 1} label="‹" />

        {pages.map((p, i) =>
          p === '…' ? (
            <span key={`ellipsis-${i}`} className="px-2 text-gray-400">…</span>
          ) : (
            <PageBtn
              key={p}
              onClick={() => onPageChange(p as number)}
              disabled={false}
              active={p === currentPage}
              label={String(p)}
            />
          )
        )}

        <PageBtn onClick={() => onPageChange(currentPage + 1)} disabled={currentPage === totalPages} label="›" />
        <PageBtn onClick={() => onPageChange(totalPages)} disabled={currentPage === totalPages} label="»" />
      </nav>
    </div>
  );
}

function PageBtn({ onClick, disabled, active = false, label }: { onClick: () => void; disabled: boolean; active?: boolean; label: string }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`px-3 py-1 text-sm rounded border transition-colors
        ${active
          ? 'bg-primary-600 text-white border-primary-600'
          : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed'
        }`}
    >
      {label}
    </button>
  );
}

function buildPages(current: number, total: number): (number | '…')[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages: (number | '…')[] = [];
  if (current <= 4) {
    pages.push(1, 2, 3, 4, 5, '…', total);
  } else if (current >= total - 3) {
    pages.push(1, '…', total - 4, total - 3, total - 2, total - 1, total);
  } else {
    pages.push(1, '…', current - 1, current, current + 1, '…', total);
  }
  return pages;
}
