import { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function Dashboard() {
  const [query, setQuery] = useState('');
  const [docs, setDocs] = useState(['']);
  const [answer, setAnswer] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleEvaluate = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/api/evaluate/rag`, {
        query,
        retrieved_docs: docs.filter(d => d.trim()),
        answer,
      });
      setResults(res.data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const addDocField = () => {
    setDocs([...docs, '']);
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1>RAG Sentinel – Production Evaluation</h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Input Section */}
        <div>
          <h3>Input</h3>
          <textarea
            placeholder="Query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{ width: '100%', height: '100px', marginBottom: '10px' }}
          />
          <h4>Retrieved Documents</h4>
          {docs.map((doc, i) => (
            <textarea
              key={i}
              placeholder={`Doc ${i+1}`}
              value={doc}
              onChange={(e) => {
                const newDocs = [...docs];
                newDocs[i] = e.target.value;
                setDocs(newDocs);
              }}
              style={{ width: '100%', height: '80px', marginBottom: '10px' }}
            />
          ))}
          <button onClick={addDocField}>+ Add Document</button>

          <textarea
            placeholder="Generated Answer"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            style={{ width: '100%', height: '100px', marginTop: '10px' }}
          />

          <button onClick={handleEvaluate} disabled={loading} style={{ marginTop: '10px' }}>
            {loading ? 'Evaluating...' : 'Evaluate'}
          </button>
        </div>

        {/* Results Section */}
        <div>
          <h3>Results</h3>
          {results && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
                <ScoreCard title="Alignment" score={results.alignment_score} />
                <ScoreCard title="Citations" score={results.citation_accuracy} />
                <ScoreCard title="Contradiction" score={results.contradiction_score} />
              </div>
              <p><strong>Overall Score:</strong> {(results.overall_score * 100).toFixed(0)}%</p>
              {results.issues.length > 0 && (
                <div style={{ border: '1px solid red', padding: '10px', marginTop: '10px' }}>
                  <p style={{ color: 'red' }}><strong>Issues:</strong></p>
                  <ul>
                    {results.issues.map((issue, i) => (
                      <li key={i}>{issue}</li>
                    ))}
                  </ul>
                </div>
              )}
              <details>
                <summary>Detailed Results</summary>
                <pre style={{ fontSize: '12px', background: '#f0f0f0', padding: '10px' }}>
                  {JSON.stringify(results.details, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ScoreCard({ title, score }) {
  const color = score > 0.7 ? 'green' : score > 0.4 ? 'orange' : 'red';
  return (
    <div style={{ border: `2px solid ${color}`, padding: '15px', borderRadius: '8px', textAlign: 'center' }}>
      <p style={{ margin: '0', fontSize: '12px', color: '#666' }}>{title}</p>
      <p style={{ margin: '5px 0', fontSize: '28px', fontWeight: 'bold', color }}>
        {(score * 100).toFixed(0)}%
      </p>
    </div>
  );
}