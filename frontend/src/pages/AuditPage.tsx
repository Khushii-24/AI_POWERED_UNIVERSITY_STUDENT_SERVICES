import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function AuditPage() {
  const { traceId } = useParams();
  const [audit, setAudit] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showRaw, setShowRaw] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/audit/${traceId}`)
      .then(r => r.json())
      .then(d => {
        setAudit(d);
        setLoading(false);
      })
      .catch(e => {
        console.error(e);
        setLoading(false);
      });
  }, [traceId]);

  return (
    <div className="flex flex-col h-full bg-bg">
      <header className="h-14 border-b border-border flex items-center px-6 bg-surface-2 justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/" className="text-text-muted hover:text-text"><ArrowLeft size={16} /></Link>
          <h2 className="font-serif text-lg font-medium">Audit Trace <span className="font-mono text-sm text-text-muted ml-2">{traceId}</span></h2>
        </div>
        <button onClick={() => setShowRaw(!showRaw)} className="text-xs px-3 py-1 border border-border rounded-md hover:bg-surface">
          {showRaw ? 'View Formatted' : 'View Raw JSON'}
        </button>
      </header>
      
      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="space-y-4 animate-pulse max-w-3xl">
            <div className="h-4 bg-surface-2 rounded w-1/4"></div>
            <div className="h-4 bg-surface-2 rounded w-1/2"></div>
            <div className="h-32 bg-surface-2 rounded w-full"></div>
          </div>
        ) : !audit ? (
          <div className="text-text-muted">Audit log not found.</div>
        ) : showRaw ? (
          <pre className="font-mono text-xs bg-surface p-4 rounded-xl border border-border overflow-x-auto">
            {JSON.stringify(audit, null, 2)}
          </pre>
        ) : (
          <div className="max-w-3xl space-y-8">
            <dl className="grid grid-cols-2 gap-x-4 gap-y-6 text-sm">
              <div>
                <dt className="text-text-muted text-xs uppercase tracking-wide mb-1">Timestamp</dt>
                <dd className="tabular-nums">{audit.timestamp}</dd>
              </div>
              <div>
                <dt className="text-text-muted text-xs uppercase tracking-wide mb-1">Latency</dt>
                <dd className="tabular-nums">{audit.details?.latency_ms} ms</dd>
              </div>
              <div>
                <dt className="text-text-muted text-xs uppercase tracking-wide mb-1">Answer Type</dt>
                <dd className="font-medium">{audit.details?.answer_type}</dd>
              </div>
              <div>
                <dt className="text-text-muted text-xs uppercase tracking-wide mb-1">Category</dt>
                <dd>{audit.details?.question_category || '-'}</dd>
              </div>
            </dl>
            
            <div className="space-y-4 pt-4 border-t border-border">
              <h3 className="font-medium text-sm">Precedence Decision</h3>
              <p className="text-sm bg-surface p-3 rounded-lg border border-border">{audit.details?.precedence_decision || 'N/A'}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
