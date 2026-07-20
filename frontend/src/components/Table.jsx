import LoadingSkeleton from './LoadingSkeleton'

export default function Table({ columns, rows, onRowClick, loading = false, emptyMessage = 'No data available' }) {
  if (loading) {
    return <LoadingSkeleton shape="row" count={5} />
  }

  if (!rows || rows.length === 0) {
    return (
      <div className="panel flex items-center justify-center py-10 text-sm text-slate-400">
        {emptyMessage}
      </div>
    )
  }

  return (
    <div className="panel overflow-x-auto">
      <table className="w-full min-w-[560px] text-left text-sm">
        <thead>
          <tr className="border-b border-border text-xs uppercase tracking-wide text-slate-500">
            {columns.map((col) => (
              <th key={col.key} scope="col" className="px-4 py-3 font-medium">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr
              key={row.id || idx}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className={`border-b border-border/60 last:border-0 ${
                onRowClick ? 'cursor-pointer hover:bg-navy-700/50' : ''
              }`}
            >
              {columns.map((col) => (
                <td key={col.key} className="px-4 py-3 text-slate-200">
                  {col.render ? col.render(row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
