import { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

type Attendance = {
  course_code: string;
  course_name: string;
  classes_held: number;
  classes_attended: number;
  attendance_pct: number;
  eligibility_status: string;
};

export default function RecordsPage() {
  const [attendance, setAttendance] = useState<Attendance[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/records/attendance`, { headers: { 'student-id': '123' } })
      .then(r => r.json())
      .then(d => {
        setAttendance(d.attendance || []);
        setLoading(false);
      })
      .catch(e => {
        console.error(e);
        setLoading(false);
      });
  }, []);

  return (
    <div className="flex flex-col h-full bg-bg">
      <header className="h-14 border-b border-border flex items-center px-6 bg-surface-2">
        <h2 className="font-serif text-lg font-medium">Records</h2>
      </header>
      
      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        
        <section>
          <h3 className="text-sm font-medium mb-4">My Attendance</h3>
          {loading ? (
             <div className="h-32 bg-surface-2 animate-pulse rounded-xl border border-border"></div>
          ) : (
            <div className="border border-border rounded-xl overflow-hidden">
              <table className="w-full text-left text-sm">
                <thead className="bg-surface-2 border-b border-border text-text-muted text-xs uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-3 font-medium">Course</th>
                    <th className="px-4 py-3 font-medium">Attended / Held</th>
                    <th className="px-4 py-3 font-medium">Progress</th>
                    <th className="px-4 py-3 font-medium text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {attendance.map((a, i) => (
                    <tr key={i} className="hover:bg-surface transition-colors">
                      <td className="px-4 py-3">
                        <div className="font-medium">{a.course_code}</div>
                        <div className="text-xs text-text-muted">{a.course_name}</div>
                      </td>
                      <td className="px-4 py-3 tabular-nums">{a.classes_attended} / {a.classes_held}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center space-x-2">
                          <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden relative">
                             {/* 75% threshold marker */}
                             <div className="absolute top-0 bottom-0 left-[75%] w-[1px] bg-bg z-10"></div>
                             <div 
                               className="h-full bg-text transition-all duration-500" 
                               style={{ width: `${a.attendance_pct}%` }}
                             ></div>
                          </div>
                          <span className="text-xs tabular-nums text-text-muted w-10 text-right">{a.attendance_pct.toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className={`inline-flex px-2 py-0.5 rounded text-[11px] font-medium tracking-wide uppercase border ${
                          a.eligibility_status === 'ELIGIBLE' ? 'bg-success/10 text-success border-success/20' : 
                          a.eligibility_status === 'CONDONABLE' ? 'bg-warning/10 text-warning border-warning/20' : 
                          'bg-danger/10 text-danger border-danger/20'
                        }`}>
                          {a.eligibility_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {attendance.length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-4 py-8 text-center text-text-muted">No attendance records found.</td>
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
