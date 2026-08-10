import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import './Dashboard.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/* ─── Helpers ──────────────────────────────────────────────────── */
function getScoreClass(score) {
  if (score === null || score === undefined) return 'na';
  if (score >= 0.70) return 'high';
  if (score >= 0.45) return 'mid';
  return 'low';
}

function fmtPct(score) {
  if (score === null || score === undefined) return 'N/A';
  return `${Math.round(score * 100)}%`;
}

function fmtTime(isoStr) {
  try {
    const d = new Date(isoStr);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      + ' ' + d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  } catch { return '—'; }
}

function getVerdictLabel(score) {
  if (score === null || score === undefined) return { label: 'Unknown', cls: 'verdict-warn' };
  if (score >= 0.70) return { label: 'Pass', cls: 'verdict-pass' };
  if (score >= 0.45) return { label: 'Warning', cls: 'verdict-warn' };
  return { label: 'Fail', cls: 'verdict-fail' };
}

/* ─── Animated Score Ring ──────────────────────────────────────── */
function ScoreRing({ score }) {
  const r = 30;
  const circ = 2 * Math.PI * r;
  const pct = score !== null && score !== undefined ? Math.max(0, Math.min(1, score)) : 0;
  const offset = circ * (1 - pct);
  const cls = getScoreClass(score);
  const strokeColor = cls === 'high' ? 'var(--score-high)' : cls === 'mid' ? 'var(--score-mid)' : cls === 'low' ? 'var(--score-low)' : 'var(--text-disabled)';

  return (
    <svg className="overall-score-ring" viewBox="0 0 72 72">
      <circle className="overall-score-track" cx="36" cy="36" r={r} />
      <circle
        className="overall-score-fill"
        cx="36" cy="36" r={r}
        stroke={strokeColor}
        strokeDasharray={`${circ}`}
        strokeDashoffset={offset}
        style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.16,1,0.3,1), stroke 0.3s ease' }}
      />
    </svg>
  );
}

/* ─── Score Card ───────────────────────────────────────────────── */
function ScoreCard({ title, score, delay = 0 }) {
  const cls = getScoreClass(score);
  const isNA = score === null || score === undefined;

  return (
    <div className={`score-card ${isNA ? '' : cls}`} style={{ animationDelay: `${delay}ms` }}>
      <div className="score-card-label">{title}</div>
      {isNA ? (
        <div className="score-card-na">N/A</div>
      ) : (
        <div className="score-card-value">{fmtPct(score)}</div>
      )}
      <div className="score-bar-track">
        <div
          className="score-bar-fill"
          style={{ width: isNA ? '0%' : `${Math.round(score * 100)}%` }}
        />
      </div>
    </div>
  );
}

/* ─── Document Breakdown Panel ─────────────────────────────────── */
function DocBreakdown({ alignmentResult, docs }) {
  if (!alignmentResult || alignmentResult.parse_error) {
    return (
      <div className="doc-breakdown-list">
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', padding: '8px 0' }}>
          {alignmentResult?.parse_error
            ? 'Alignment parsing failed — breakdown unavailable.'
            : 'No alignment data.'}
        </div>
      </div>
    );
  }

  const usageMap = alignmentResult.usage_map || {};

  return (
    <div className="doc-breakdown-list">
      {docs.map((doc, i) => {
        const key = `doc_${i}`;
        const status = usageMap[key] || 'UNUSED';
        const statusCls = status === 'USED' ? 'status-used'
          : status === 'NOT_RELEVANT' ? 'status-not-relevant'
          : 'status-unused';

        return (
          <div className="doc-breakdown-item" key={i}>
            <div className={`doc-breakdown-status ${statusCls}`}>{status.replace('_', ' ')}</div>
            <div className="doc-breakdown-text">
              <div className="doc-breakdown-idx">Document {i + 1}</div>
              {doc.length > 160 ? doc.slice(0, 160) + '…' : doc}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ─── Citation Report Panel ────────────────────────────────────── */
function CitationReport({ citationResult }) {
  if (!citationResult) return null;

  const details = Array.isArray(citationResult.details) ? citationResult.details : [];
  const total = citationResult.total_citations ?? 0;

  if (total === 0) {
    return (
      <div className="no-citations-msg">
        ✓ No citations found — accuracy scored as 100%
      </div>
    );
  }

  return (
    <div className="citation-list">
      {details.map((c, i) => (
        <div className="citation-item" key={i}>
          <div className="citation-valid-icon">{c.valid ? '✅' : '❌'}</div>
          <div className="citation-body">
            <div className="citation-ref">{c.citation}</div>
            {c.associated_text && (
              <div className="citation-associated">"{c.associated_text.slice(0, 120)}{c.associated_text.length > 120 ? '…' : ''}"</div>
            )}
            <div className="citation-reason">{c.reason}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ─── Trend Chart ──────────────────────────────────────────────── */
function TrendChart({ evaluations }) {
  const svgRef = useRef(null);

  if (!evaluations || evaluations.length < 2) {
    return (
      <div className="no-data-state" style={{ padding: '24px' }}>
        <p>Run at least 2 evaluations to see trend.</p>
      </div>
    );
  }

  const W = 600, H = 120, PAD = { top: 10, right: 10, bottom: 28, left: 36 };
  const chartW = W - PAD.left - PAD.right;
  const chartH = H - PAD.top - PAD.bottom;

  const scores = evaluations.map(e => e.overall_score);
  const minS = Math.min(...scores, 0);
  const maxS = Math.max(...scores, 1);

  const xScale = i => PAD.left + (i / (evaluations.length - 1)) * chartW;
  const yScale = v => PAD.top + (1 - (v - minS) / (maxS - minS || 1)) * chartH;

  const points = evaluations.map((e, i) => [xScale(i), yScale(e.overall_score)]);
  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0]},${p[1]}`).join(' ');
  const areaPath = [
    `M${points[0][0]},${PAD.top + chartH}`,
    ...points.map(p => `L${p[0]},${p[1]}`),
    `L${points[points.length - 1][0]},${PAD.top + chartH}`,
    'Z'
  ].join(' ');

  // Threshold at 0.65
  const threshY = yScale(0.65);
  const yLabels = [0, 0.25, 0.5, 0.75, 1.0];

  return (
    <div className="chart-wrap">
      <div className="chart-title">Score Trend</div>
      <svg
        ref={svgRef}
        className="trend-chart-svg"
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="none"
        style={{ height: '120px' }}
      >
        <defs>
          <linearGradient id="chart-gradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.15" />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Grid lines */}
        {yLabels.map(v => (
          <g key={v}>
            <line
              className="chart-grid-line"
              x1={PAD.left} y1={yScale(v)}
              x2={PAD.left + chartW} y2={yScale(v)}
            />
            <text className="chart-label" x={PAD.left - 4} y={yScale(v) + 3} textAnchor="end">
              {Math.round(v * 100)}
            </text>
          </g>
        ))}

        {/* Threshold line at 0.65 */}
        <line
          className="chart-threshold-line"
          x1={PAD.left} y1={threshY}
          x2={PAD.left + chartW} y2={threshY}
        />
        <text className="chart-threshold-label" x={PAD.left + chartW + 2} y={threshY + 3}>
          65
        </text>

        {/* Area fill */}
        <path className="chart-area" d={areaPath} />

        {/* Line */}
        <path className="chart-line" d={linePath} />

        {/* Dots */}
        {points.map((p, i) => (
          <circle
            key={i}
            className="chart-dot"
            cx={p[0]} cy={p[1]} r={3}
          >
            <title>{`Run ${i + 1}: ${fmtPct(evaluations[i].overall_score)} — ${fmtTime(evaluations[i].timestamp)}`}</title>
          </circle>
        ))}

        {/* X-axis labels — show first and last */}
        {evaluations.length >= 2 && (
          <>
            <text className="chart-label" x={xScale(0)} y={H - 4} textAnchor="middle">
              {fmtTime(evaluations[0].timestamp)}
            </text>
            <text className="chart-label" x={xScale(evaluations.length - 1)} y={H - 4} textAnchor="middle">
              {fmtTime(evaluations[evaluations.length - 1].timestamp)}
            </text>
          </>
        )}
      </svg>
    </div>
  );
}

/* ─── History Table ────────────────────────────────────────────── */
function HistoryTable({ evaluations }) {
  if (!evaluations || evaluations.length === 0) {
    return (
      <div className="no-data-state">
        <p>No evaluation history yet.</p>
        <span>Past evaluations will appear here.</span>
      </div>
    );
  }

  const sorted = [...evaluations].reverse();

  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="history-table">
        <thead>
          <tr>
            <th>Query</th>
            <th>Overall</th>
            <th>Align</th>
            <th>Citation</th>
            <th>Contradict</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((e, i) => {
            const oCls = getScoreClass(e.overall_score);
            return (
              <tr key={i}>
                <td><div className="history-query">{e.query || '—'}</div></td>
                <td>
                  <span className={`score-chip ${oCls}`}>{fmtPct(e.overall_score)}</span>
                </td>
                <td style={{ color: `var(--score-${getScoreClass(e.alignment_score)})` }}>
                  {fmtPct(e.alignment_score)}
                </td>
                <td style={{ color: `var(--score-${getScoreClass(e.citation_accuracy)})` }}>
                  {fmtPct(e.citation_accuracy)}
                </td>
                <td style={{ color: `var(--score-${getScoreClass(e.contradiction_score)})` }}>
                  {fmtPct(e.contradiction_score)}
                </td>
                <td><div className="history-ts">{fmtTime(e.timestamp)}</div></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/* ─── Detail Panel (Accordion) ─────────────────────────────────── */
function DetailPanel({ title, icon, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className={`detail-panel ${open ? 'open' : ''}`}>
      <button className="detail-panel-toggle" onClick={() => setOpen(o => !o)}>
        <span>{icon}</span>
        <span>{title}</span>
        <span className="detail-panel-chevron">▾</span>
      </button>
      <div className="detail-panel-content">
        {children}
      </div>
    </div>
  );
}

/* ─── Results Skeletons ────────────────────────────────────────── */
function ResultsSkeleton() {
  return (
    <div className="skeleton-results">
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 8 }}>
        <div className="sk skeleton" style={{ width: 72, height: 72, borderRadius: '50%' }} />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div className="sk skeleton" style={{ width: '40%', height: 12 }} />
          <div className="sk skeleton" style={{ width: '60%', height: 32 }} />
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 1 }}>
        {[0, 1, 2].map(i => (
          <div key={i} className="sk skeleton" style={{ height: 80 }} />
        ))}
      </div>
      <div className="sk skeleton" style={{ height: 60 }} />
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   Main Dashboard
   ══════════════════════════════════════════════════════════════ */
export default function Dashboard() {
  const [query, setQuery] = useState('');
  const [docs, setDocs] = useState(['']);
  const [answer, setAnswer] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [apiStatus, setApiStatus] = useState('checking');
  const [uploading, setUploading] = useState(false);
  const [uploadedDocs, setUploadedDocs] = useState(null);

  // Check API health on mount
  useEffect(() => {
    axios.get(`${API_URL}/health`, { timeout: 3000 })
      .then(() => setApiStatus('online'))
      .catch(() => setApiStatus('offline'));
  }, []);

  const fetchMonitoring = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/api/evaluate/monitoring`);
      setMetrics(res.data);
    } catch (err) {
      // Silent fail — monitoring is secondary
    }
  }, []);

  useEffect(() => { fetchMonitoring(); }, [fetchMonitoring]);

  const handleEvaluate = async () => {
    // Client-side validation
    const filteredDocs = docs.filter(d => d.trim());
    if (!query.trim()) {
      setError({ title: 'Missing Query', msg: 'Please enter a query before evaluating.' });
      return;
    }
    if (filteredDocs.length === 0) {
      setError({ title: 'No Documents', msg: 'Add at least one retrieved document.' });
      return;
    }
    if (!answer.trim()) {
      setError({ title: 'Missing Answer', msg: 'Please enter the generated answer to evaluate.' });
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const res = await axios.post(`${API_URL}/api/evaluate/rag`, {
        query: query.trim(),
        retrieved_docs: filteredDocs,
        answer: answer.trim(),
      });
      setResults(res.data);
      fetchMonitoring();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError({
        title: 'Evaluation Failed',
        msg: typeof detail === 'string'
          ? detail
          : err.message || 'An unexpected error occurred. Check the backend is running.',
      });
    } finally {
      setLoading(false);
    }
  };

  const pdfInputRef = useRef(null);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Reset so the same file can be re-selected after an error
    if (pdfInputRef.current) pdfInputRef.current.value = '';

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError({ title: 'Invalid File', msg: 'Please select a PDF file (.pdf).' });
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(`${API_URL}/api/upload/pdf`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const documents = res.data.documents;
      setDocs(documents.length > 0 ? documents : ['']);
      setUploadedDocs({ count: documents.length, filename: res.data.filename });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError({
        title: 'PDF Upload Failed',
        msg: typeof detail === 'string'
          ? detail
          : 'Failed to process PDF. Make sure the backend is running and the file is a valid text-based PDF.',
      });
    } finally {
      setUploading(false);
    }
  };

  const addDoc = () => setDocs(prev => [...prev, '']);
  const removeDoc = (i) => setDocs(prev => prev.filter((_, idx) => idx !== i));
  const updateDoc = (i, val) => setDocs(prev => { const n = [...prev]; n[i] = val; return n; });

  const { label: verdictLabel, cls: verdictCls } = getVerdictLabel(results?.overall_score);
  const hasData = metrics && !metrics.no_data;

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <div className="header-logo">
          <div className="header-logo-icon">🛡️</div>
          <span className="header-logo-text">RAG Sentinel</span>
          <span className="header-logo-badge">BETA</span>
        </div>
        <div className="header-spacer" />
        <div className="header-status">
          <div className={`status-dot ${apiStatus === 'offline' ? 'offline' : ''}`} />
          {apiStatus === 'checking' ? 'Connecting…' : apiStatus === 'online' ? 'API Online' : 'API Offline'}
        </div>
      </header>

      <main className="main">
        {/* ═══════════════════════════════════════════════════
            LEFT — Input Panel
            ═══════════════════════════════════════════════════ */}
        <div className="card animate-fade-up">
          <div className="card-header">
            <span className="card-icon">⌨️</span>
            <span className="card-title">Evaluation Input</span>
            <span className="card-subtitle">RAG pipeline components</span>
          </div>
          <div className="card-body">
            {/* Query */}
            <div>
              <label className="field-label">Query</label>
              <textarea
                className="textarea query-textarea"
                placeholder="What question did the user ask?"
                value={query}
                onChange={e => setQuery(e.target.value)}
              />
            </div>


            {/* Retrieved Documents */}
            <div>
              <label className="field-label">Retrieved Documents</label>

              {/* PDF Upload */}
              <div className="pdf-upload-row">
                <input
                  ref={pdfInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={handleFileUpload}
                  style={{ display: 'none' }}
                  id="pdf-upload"
                  disabled={uploading || loading}
                />
                <label
                  htmlFor="pdf-upload"
                  className={`btn-upload-pdf ${uploading || loading ? 'disabled' : ''}`}
                  aria-disabled={uploading || loading}
                >
                  {uploading ? (
                    <><div className="spinner" style={{ borderTopColor: 'currentColor', width: 12, height: 12 }} /> Processing…</>
                  ) : (
                    <>📄 Upload PDF</>
                  )}
                </label>
                {uploadedDocs && (
                  <span className="pdf-upload-status">
                    ✓ {uploadedDocs.count} page{uploadedDocs.count !== 1 ? 's' : ''} from <em>{uploadedDocs.filename}</em>
                  </span>
                )}
              </div>

              <div className="doc-list">
                {docs.map((doc, i) => (
                  <div className="doc-row" key={i}>
                    <div className="doc-number">{i + 1}</div>
                    <textarea
                      className="textarea doc-textarea"
                      placeholder={`Paste document ${i + 1} here…`}
                      value={doc}
                      onChange={e => updateDoc(i, e.target.value)}
                    />
                    {docs.length > 1 && (
                      <button
                        className="doc-remove-btn"
                        onClick={() => removeDoc(i)}
                        title="Remove document"
                        aria-label={`Remove document ${i + 1}`}
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <button className="btn-add-doc" onClick={addDoc} style={{ marginTop: '8px' }}>
                + Add Document
              </button>
            </div>
            

            {/* Generated Answer */}
            <div>
              <label className="field-label">Generated Answer</label>
              <textarea
                className="textarea answer-textarea"
                placeholder="Paste the LLM's generated answer here…"
                value={answer}
                onChange={e => setAnswer(e.target.value)}
              />
            </div>

            {/* Error Banner */}
            {error && (
              <div className="error-banner">
                <div className="error-banner-icon">⚠️</div>
                <div className="error-banner-body">
                  <div className="error-banner-title">{error.title}</div>
                  <div className="error-banner-msg">{error.msg}</div>
                </div>
                <button className="error-banner-close" onClick={() => setError(null)} aria-label="Dismiss error">✕</button>
              </div>
            )}

            {/* Submit */}
            <button
              id="btn-evaluate"
              className="btn-evaluate"
              onClick={handleEvaluate}
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="spinner" />
                  Evaluating…
                </>
              ) : (
                <>🔍 Run Evaluation</>
              )}
            </button>
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════
            RIGHT — Results Panel
            ═══════════════════════════════════════════════════ */}
        <div className="card animate-fade-up" style={{ animationDelay: '60ms' }}>
          <div className="card-header">
            <span className="card-icon">📊</span>
            <span className="card-title">Evaluation Results</span>
            {results && (
              <span className="card-subtitle">
                Overall: {fmtPct(results.overall_score)}
              </span>
            )}
          </div>

          {loading ? (
            <ResultsSkeleton />
          ) : results ? (
            <>
              {/* Overall Score */}
              <div className="overall-score-wrap">
                <div className="overall-score-ring-wrap">
                  <ScoreRing score={results.overall_score} />
                </div>
                <div className="overall-score-info">
                  <div className="overall-score-label">Overall Score</div>
                  <div
                    className="overall-score-value"
                    style={{
                      color: getScoreClass(results.overall_score) === 'high' ? 'var(--score-high)'
                        : getScoreClass(results.overall_score) === 'mid' ? 'var(--score-mid)'
                        : 'var(--score-low)'
                    }}
                  >
                    {fmtPct(results.overall_score)}
                  </div>
                  <span className={`overall-score-verdict ${verdictCls}`}>{verdictLabel}</span>
                </div>
              </div>

              <div className="card-body" style={{ paddingTop: '16px' }}>
                {/* Score Grid */}
                <div className="score-grid">
                  <ScoreCard title="Alignment" score={results.alignment_score} delay={0} />
                  <ScoreCard title="Citations" score={results.citation_accuracy} delay={80} />
                  <ScoreCard title="Consistency" score={results.contradiction_score} delay={160} />
                </div>

                {/* Issues */}
                {results.issues?.length > 0 && (
                  <div className="issues-banner">
                    <div className="issues-banner-header">
                      <span>⚠</span>
                      <span>{results.issues.length} Issue{results.issues.length > 1 ? 's' : ''} Detected</span>
                    </div>
                    <ul className="issues-list">
                      {results.issues.map((issue, i) => (
                        <li key={i}>{issue}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Detail Panels */}
                <div className="detail-panels">
                  <DetailPanel title="Document Breakdown" icon="📄" defaultOpen={true}>
                    <DocBreakdown
                      alignmentResult={results.details?.alignment}
                      docs={docs.filter(d => d.trim())}
                    />
                  </DetailPanel>

                  <DetailPanel title="Citation Report" icon="🔗">
                    <CitationReport citationResult={results.details?.citation} />
                  </DetailPanel>

                  <DetailPanel title="Contradiction Analysis" icon="⚡">
                    {results.details?.contradiction ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{
                            fontSize: '11px',
                            fontWeight: 600,
                            padding: '2px 8px',
                            borderRadius: '99px',
                            color: results.details.contradiction.verdict === 'NO' ? 'var(--score-high)' : results.details.contradiction.verdict === 'PARTIAL' ? 'var(--score-mid)' : 'var(--score-low)',
                            background: results.details.contradiction.verdict === 'NO' ? 'var(--score-high-bg)' : results.details.contradiction.verdict === 'PARTIAL' ? 'var(--score-mid-bg)' : 'var(--score-low-bg)',
                            border: `1px solid ${results.details.contradiction.verdict === 'NO' ? 'var(--score-high-border)' : results.details.contradiction.verdict === 'PARTIAL' ? 'var(--score-mid-border)' : 'var(--score-low-border)'}`,
                            textTransform: 'uppercase',
                            letterSpacing: '0.06em',
                          }}>
                            {results.details.contradiction.verdict}
                          </span>
                          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                            {results.details.contradiction.explanation}
                          </span>
                        </div>
                        {results.details.contradiction.specific_contradictions?.length > 0 && (
                          <div style={{ paddingTop: '8px' }}>
                            <div style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-disabled)', marginBottom: '6px' }}>
                              Specific Contradictions
                            </div>
                            <ul className="issues-list">
                              {results.details.contradiction.specific_contradictions.map((c, i) => (
                                <li key={i}>{c}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ) : <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>No data.</div>}
                  </DetailPanel>
                </div>
              </div>
            </>
          ) : (
            <div className="results-empty">
              <div className="results-empty-icon">🎯</div>
              <div className="results-empty-text">
                Fill in the input panel and run an evaluation to see results here.
              </div>
            </div>
          )}
        </div>

        {/* ═══════════════════════════════════════════════════
            BOTTOM — Monitoring Panel (full width)
            ═══════════════════════════════════════════════════ */}
        <div className="card monitoring animate-fade-up" style={{ animationDelay: '120ms' }}>
          <div className="card-header">
            <span className="card-icon">📡</span>
            <span className="card-title">Production Monitoring</span>
            <span className="card-subtitle">Last 24 hours</span>
          </div>

          {hasData ? (
            <>
              {/* Metric Tiles */}
              <div className="monitoring-grid">
                <div className="metric-tile">
                  <div className="metric-tile-label">Avg Score</div>
                  <div className={`metric-tile-value ${getScoreClass(metrics.avg_score) === 'high' ? '' : getScoreClass(metrics.avg_score) === 'mid' ? 'trend-stable' : 'trend-degrading'}`}>
                    {fmtPct(metrics.avg_score)}
                  </div>
                  <div className="metric-tile-sub">mean of {metrics.total_evaluations} runs</div>
                </div>
                <div className="metric-tile">
                  <div className="metric-tile-label">Min Score</div>
                  <div className={`metric-tile-value ${getScoreClass(metrics.min_score) === 'low' ? 'trend-degrading' : ''}`}>
                    {fmtPct(metrics.min_score)}
                  </div>
                  <div className="metric-tile-sub">worst run</div>
                </div>
                <div className="metric-tile">
                  <div className="metric-tile-label">Max Score</div>
                  <div className="metric-tile-value">{fmtPct(metrics.max_score)}</div>
                  <div className="metric-tile-sub">best run</div>
                </div>
                <div className="metric-tile">
                  <div className="metric-tile-label">Trend</div>
                  <div className={`metric-tile-value trend-${metrics.trend}`}>
                    {metrics.trend === 'improving' ? '↑' : metrics.trend === 'degrading' ? '↓' : '→'}
                    {' '}{metrics.trend}
                  </div>
                  <div className="metric-tile-sub">vs previous period</div>
                </div>
                <div className="metric-tile">
                  <div className="metric-tile-label">Alerts</div>
                  <div className={`metric-tile-value ${metrics.alert_count > 0 ? 'alert-active' : ''}`}>
                    {metrics.alert_count > 0 ? `⚠ ${metrics.alert_count}` : '✓ None'}
                  </div>
                  <div className="metric-tile-sub">quality drops</div>
                </div>
              </div>

              {/* Trend Chart */}
              {metrics.recent_evaluations?.length >= 2 && (
                <TrendChart evaluations={metrics.recent_evaluations} />
              )}

              {/* History Table */}
              <div className="history-section">
                <div className="history-header">
                  <span className="history-title">Evaluation History</span>
                  <span className="history-count">{metrics.recent_evaluations?.length || 0} recent</span>
                </div>
                <HistoryTable evaluations={metrics.recent_evaluations || []} />
              </div>
            </>
          ) : (
            <div className="no-data-state">
              <p>📡 No monitoring data yet</p>
              <span>Run your first evaluation above to start tracking quality over time.</span>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}