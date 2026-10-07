import { useState } from 'react';
import { askQuestion, AskResponse } from '../api/client';
import ReactMarkdown from 'react-markdown';
import { BookOpen, Calculator, SearchX, HelpCircle, ShieldOff, AlertTriangle, Send } from 'lucide-react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';

type Message = {
  role: 'user' | 'assistant';
  content: string;
  details?: AskResponse;
  pending?: boolean;
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [asOfDate, setAsOfDate] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [pending, setPending] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || pending) return;
    const q = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: q }, { role: 'assistant', content: '', pending: true }]);
    setPending(true);

    try {
      const res = await askQuestion(q, asOfDate, '123'); // hardcoded student id for now
      setMessages(prev => {
        const newMsg = [...prev];
        newMsg[newMsg.length - 1] = { role: 'assistant', content: res.answer, details: res, pending: false };
        return newMsg;
      });
    } catch (e: any) {
      setMessages(prev => {
        const newMsg = [...prev];
        newMsg[newMsg.length - 1] = { role: 'assistant', content: `Error: ${e.message}`, pending: false };
        return newMsg;
      });
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-bg">
      <header className="h-14 border-b border-border flex items-center justify-between px-6 bg-surface-2">
        <h2 className="font-serif text-lg font-medium">Assistant</h2>
        <div className="flex items-center space-x-2 text-sm">
          <label className="text-text-muted">As of</label>
          <input 
            type="date" 
            value={asOfDate} 
            onChange={e => setAsOfDate(e.target.value)}
            className="bg-bg border border-border rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-text"
          />
        </div>
      </header>
      
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-6">
            <h1 className="font-serif text-3xl font-medium tracking-tight">How can I help you today?</h1>
            <p className="text-text-muted">Answers only from your university's documents and your records</p>
            <div className="grid grid-cols-2 gap-4 max-w-2xl w-full mt-8">
              {["What is the minimum attendance to sit exams?", "What is my attendance in CS101?", "Am I eligible for placement?", "Can I condone attendance?"].map(q => (
                <button 
                  key={q} 
                  onClick={() => setInput(q)}
                  className="p-4 text-left border border-border rounded-lg hover:border-border-strong bg-surface transition-colors text-sm"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`flex flex-col max-w-3xl mx-auto ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
              {m.role === 'user' ? (
                <div className="bg-primary text-primary-fg px-4 py-3 rounded-xl rounded-tr-sm text-[15px]">
                  {m.content}
                </div>
              ) : (
                <div className="w-full space-y-3 pb-6 border-b border-border">
                  {m.pending ? (
                    <div className="flex items-center space-x-2 text-text-muted">
                      <span className="animate-pulse">●</span>
                      <span className="animate-pulse animation-delay-200">●</span>
                      <span className="animate-pulse animation-delay-400">●</span>
                    </div>
                  ) : (
                    <>
                      <div className="prose dark:prose-invert max-w-[68ch] text-[15px] leading-relaxed">
                        <ReactMarkdown>{m.content}</ReactMarkdown>
                      </div>
                      
                      {m.details && (
                        <div className="flex flex-wrap items-center gap-3 pt-2 text-xs">
                          {/* Badge */}
                          {m.details.answer_type === 'retrieved_fact' && <span className="flex items-center px-2 py-1 rounded-md border border-border text-info bg-info/10 tracking-wide uppercase font-medium"><BookOpen size={12} className="mr-1"/> Retrieved Fact</span>}
                          {m.details.answer_type === 'calculated' && <span className="flex items-center px-2 py-1 rounded-md bg-text text-bg tracking-wide uppercase font-medium"><Calculator size={12} className="mr-1"/> Calculated</span>}
                          {m.details.answer_type === 'not_found' && <span className="flex items-center px-2 py-1 rounded-md border border-dashed border-border text-text-muted tracking-wide uppercase font-medium"><SearchX size={12} className="mr-1"/> Not Found</span>}
                          {m.details.answer_type === 'clarification_needed' && <span className="flex items-center px-2 py-1 rounded-md border border-border border-y-2 text-text-subtle tracking-wide uppercase font-medium"><HelpCircle size={12} className="mr-1"/> Need more info</span>}
                          {m.details.answer_type === 'refused' && <span className="flex items-center px-2 py-1 rounded-md border border-border text-danger tracking-wide uppercase font-medium"><ShieldOff size={12} className="mr-1"/> Not allowed</span>}
                          {m.details.answer_type === 'conflict_flagged' && <span className="flex items-center px-2 py-1 rounded-md border-l-2 border-warning bg-warning/10 text-warning tracking-wide uppercase font-medium"><AlertTriangle size={12} className="mr-1"/> Sources conflict</span>}
                          
                          {/* Trace ID */}
                          <Link to={`/audit/${m.details.trace_id}`} className="font-mono text-text-subtle hover:text-text transition-colors">
                            {m.details.trace_id.split('-')[0]}...
                          </Link>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
      
      <div className="p-4 border-t border-border bg-bg flex justify-center">
        <div className="relative max-w-3xl w-full">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask a question... (Enter to send, Shift+Enter for new line)"
            className="w-full bg-surface border border-border rounded-xl pl-4 pr-12 py-3 focus:outline-none focus:border-border-strong resize-none text-[15px]"
            rows={1}
          />
          <button 
            onClick={handleSend}
            disabled={pending || !input.trim()}
            className="absolute right-2 bottom-2 p-2 bg-primary text-primary-fg rounded-full disabled:opacity-50"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
