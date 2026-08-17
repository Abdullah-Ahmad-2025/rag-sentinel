# 🛡️ RAG Sentinel

> Advanced RAG evaluation and monitoring for production systems

**[Live Demo](https://rag-sentinel.netlify.app)** • **[GitHub](https://github.com/Abdullah-Ahmad-2025/rag-sentinel)**

---

## 🎯 The Problem

Standard RAG evaluation tools like RAGAS can give systems a "production-ready" score of 0.91 while silently failing in critical ways:

- 1 in 6 responses miss critical information
- Citations are hallucinated 
- LLMs ignore half the retrieved context
- Systems look perfect on paper but fail in reality

**RAGAS said: great. Reality said: broken.**

---

## ✨ What I Built

RAG Sentinel — a deployed MVP for evaluating and monitoring RAG systems with custom metrics that answer the questions that actually matter:

### 🔹 Alignment Scoring
Does the answer actually **USE** the retrieved documents? A system can score 0.9 faithfulness while ignoring half the context.

### 🔹 Citation Accuracy  
Do citations actually **exist** in source documents? Or are they hallucinated?

### 🔹 Contradiction Detection
Does the answer **contradict** its own sources? Standard metrics don't check for this.

### 🔹 Production Monitoring Dashboard
Track quality trends and detect degradation before users notice.

---

## 🚀 Features

- **Custom Evaluation Metrics**: Alignment, Citation Accuracy, Contradiction Detection
- **Real-time Dashboard**: Monitor RAG quality over time with trend analysis
- **Batch Processing**: Upload CSV files to evaluate multiple query/document/answer sets
- **PDF Upload**: Extract and evaluate documents directly from PDF files
- **Session-Based Isolation**: Each user's evaluations are private and isolated
- **Production Monitoring**: Detect quality drops before they impact users
- **Interactive Results**: Detailed breakdowns with document usage analysis

---

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React 
- **Database**: SQLite (development) → PostgreSQL (production)
- **LLM**: Groq (Mixtral 8x7B)
- **Deployment**: Railway (backend) + Netlify (frontend)

---

## 📊 Metrics Explained

### Alignment Score
Measures how many retrieved documents are actually used in the answer. High score = answer uses most relevant context. Low score = answer ignores retrieved docs (dangerous!).

### Citation Accuracy
Verifies that citations actually exist in source documents and catches hallucinated citations.

### Contradiction Detection
Uses LLM-based comparison to detect if answers contradict their own sources.

### Overall Score
Weighted combination of all metrics:
- Alignment: 30%
- Citation Accuracy: 35%  
- Contradiction Score: 35%

---

## 🏗️ Architecture

```
User Input → FastAPI → Evaluation Pipeline → Results
                     ├─ Alignment Evaluator
                     ├─ Citation Accuracy  
                     ├─ Contradiction Detector
                     └─ Quality Monitoring
```

---

## 🚦 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- Groq API Key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Abdullah-Ahmad-2025/rag-sentinel.git
cd rag-sentinel
```

2. **Backend Setup**
```bash
cd backend
pip install -r ../requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY to .env
python -m uvicorn main:app --reload
```

3. **Frontend Setup**
```bash
cd frontend
npm install
npm start
```

4. **Run the Application**
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

---

## 📖 Usage

### Single Evaluation
1. Enter your query
2. Add retrieved documents (or upload PDF)
3. Paste the generated answer
4. Click "Run Evaluation"

### Batch Evaluation
1. Download the CSV template
2. Fill in query, documents, and answer columns
3. Upload the CSV file
4. View aggregated results and common issues

### Monitoring
- View real-time quality metrics
- Track score trends over time
- Get alerts for quality degradation
- Review evaluation history

---

## 🔒 Privacy & Security

- **Session-Based Isolation**: Each user's evaluations are isolated to their session
- **No Authentication Required**: Maintains privacy while allowing anonymous use
- **24-Hour Session Duration**: Sessions persist for 24 hours
- **Secure Cookie Handling**: HttpOnly, SameSite lax for security

---

## 🎨 Screenshots

### Evaluation Dashboard
- Real-time scoring with animated visualizations
- Document-by-document breakdown analysis
- Citation verification with detailed reports
- Contradiction detection with specific issue identification

### Production Monitoring  
- Quality trend charts
- Alert system for degradation
- Historical evaluation tracking
- Performance metrics over time

---

## 🛣️ Roadmap

- [ ] User authentication and account management
- [ ] Custom threshold configuration
- [ ] Integration with popular RAG frameworks
- [ ] Export evaluation reports
- [ ] API for programmatic evaluation
- [ ] Custom metric creation
- [ ] Team collaboration features

---

## 🤝 Contributing

Contributions are welcome! This is an open-source project aimed at improving RAG evaluation for everyone.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## 📝 License

MIT License - feel free to use this project for your own RAG systems.

---

## 🙏 Acknowledgments

Built with ❤️ by a 1st year BS AI student over 8 weeks. Special thanks to the open-source AI community for the tools and frameworks that made this possible.

---

## 📬 Contact & Feedback

If you're building RAG systems, I'd genuinely love for you to try this and tell me where it breaks.

- **Issues**: [GitHub Issues](https://github.com/Abdullah-Ahmad-2025/rag-sentinel/issues)
- **Live Demo**: [rag-sentinel.netlify.app](https://rag-sentinel.netlify.app)
- **LinkedIn**: [Connect with me](https://linkedin.com)

---

## 🏷️ Tags

#RAG #LLMOps #GenerativeAI #AIEngineering #LLM #MachineLearning #MLOps #AITools #BuildInPublic #OpenSource #AI #ArtificialIntelligence #StudentDeveloper #ShippedIt

---

**Built solo. 8 weeks. 1st year BS AI student.**

*If you're building RAG systems: what does your current evaluation workflow look like? Do you trust RAGAS scores alone?*