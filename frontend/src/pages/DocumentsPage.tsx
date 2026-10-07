import { useState, useEffect } from 'react';
import { getSources, SourceSchema } from '../api/client';
import { z } from 'zod';

export default function DocumentsPage() {
  const [sources, setSources] = useState<z.infer<typeof SourceSchema>[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSources().then(data => {
      setSources(data);
      setLoading(false);
    }).catch(e => {
      console.error(e);
      setLoading(false);
    });
  }, []);

  return (
    <div className="flex flex-col h-full bg-bg">
      <header className="h-14 border-b border-border flex items-center px-6 bg-surface-2">
        <h2 className="font-serif text-lg font-medium">Documents</h2>
      </header>
      
      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        
        {/* Upload Form (Mock) */}
        <section className="p-6 border border-border rounded-xl bg-surface">
          <h3 className="text-sm font-medium mb-4">Ingest Document</h3>
          <div className="grid grid-cols-2 gap-4 max-w-xl">
            <div className="flex flex-col space-y-1">
              <label className="text-xs text-text-muted">Title</label>
              <input className="border border-border rounded px-3 py-1.5 text-sm bg-bg" placeholder="Circular 101" />
            </div>
            <div className="flex flex-col space-y-1">
              <label className="text-xs text-text-muted">Authority Level</label>
              <input type="number" className="border border-border rounded px-3 py-1.5 text-sm bg-bg" defaultValue={3} />
            </div>
            <div className="col-span-2 flex flex-col space-y-1 mt-2">
              <label className="text-xs text-text-muted">File (PDF, MD)</label>
              <input type="file" className="text-sm text-text-muted file:mr-4 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-sm file:bg-surface-2 file:text-text hover:file:bg-border" />
            </div>
            <div className="col-span-2 mt-4">
              <button className="px-4 py-2 bg-primary text-primary-fg rounded-md text-sm font-medium">Upload & Ingest</button>
            </div>
          </div>
        </section>

        {/* Source Register */}
        <section>
          <h3 className="text-sm font-medium mb-4">Source Register</h3>
          {loading ? (
            <div className="h-32 bg-surface-2 animate-pulse rounded-xl border border-border"></div>
          ) : (
            <div className="border border-border rounded-xl overflow-hidden">
              <table className="w-full text-left text-sm">
                <thead className="bg-surface-2 border-b border-border text-text-muted text-xs uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-3 font-medium">Doc ID</th>
                    <th className="px-4 py-3 font-medium">Title</th>
                    <th className="px-4 py-3 font-medium">Version</th>
                    <th className="px-4 py-3 font-medium">Effective</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {sources.map(s => (
                    <tr key={s.doc_id} className="hover:bg-surface transition-colors">
                      <td className="px-4 py-3 font-mono text-text-muted">{s.doc_id}</td>
                      <td className="px-4 py-3">{s.title}</td>
                      <td className="px-4 py-3">{s.version || '-'}</td>
                      <td className="px-4 py-3 tabular-nums">{s.effective_from || '-'}</td>
                    </tr>
                  ))}
                  {sources.length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-4 py-8 text-center text-text-muted">No documents found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
