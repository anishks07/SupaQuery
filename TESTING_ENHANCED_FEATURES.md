# Testing the Enhanced SupaQuery Architecture

## 🧪 Quick Test Guide

### Prerequisites

1. Backend running on `http://localhost:8000`
2. Frontend running on `http://localhost:3000`
3. At least one document uploaded (PDF or audio file)
4. Ollama running with llama3.2 model

---

## 🎯 Test Scenarios

### Test 1: Basic Query with Citations

**Objective**: Verify that queries return answers with proper citations.

**Steps**:
1. Upload a PDF document
2. Ask: "What is this document about?"
3. Check response includes:
   - Answer text
   - Citations with page numbers
   - Source filename

**Expected Result**:
```
Answer: "This document discusses..."

Sources & Citations:
[1] document.pdf
    📄 pp. 1-2
    "The introduction states..."
    
✨ Quality: 85%
```

---

### Test 2: Audio File with Timestamps

**Objective**: Verify audio transcription includes timestamps.

**Steps**:
1. Upload an audio file (WAV, MP3, etc.)
2. Ask: "What was discussed in the audio?"
3. Check response includes:
   - Transcribed text
   - Citations with timestamps
   - Time ranges

**Expected Result**:
```
Answer: "In the audio, the speaker discusses..."

Sources & Citations:
[1] interview.wav
    🕐 02:05 - 02:25
    "In this section we discuss..."
    
✨ Quality: 78%
```

---

### Test 3: Multi-Query Generation

**Objective**: Verify multiple query variations are generated.

**Check Backend Logs**:
```bash
# In the backend terminal, you should see:
📝 Generated 3 query variations:
   1. What are the main findings?
   2. What are the key results discovered?
   3. What conclusions were reached?
```

---

### Test 4: Evaluation Feedback Loop

**Objective**: Test that low-quality answers trigger retries.

**Steps**:
1. Ask a very complex or ambiguous question
2. Watch backend logs for evaluation and retry attempts

**Expected Backend Logs**:
```
🔍 Evaluating answer quality...
   Overall Score: 0.65
   Quality: 0.70 | Completeness: 0.55 | Relevance: 0.70
   Sufficient: ❌ NO

⚠️  Answer quality insufficient, preparing retry...
   Retry Strategy: {'expand_search': True, 'increase_top_k': 10}

🔄 Attempt 2/3
   Overall Score: 0.82
   Sufficient: ✅ YES
```

---

### Test 5: Direct Reply (No Retrieval)

**Objective**: Verify routing agent handles non-retrieval queries.

**Test Cases**:
```
Query: "Hi"
Expected: Greeting without document search

Query: "What can you do?"
Expected: System capabilities description

Query: "Thanks"
Expected: Acknowledgment
```

**Check Backend Logs**:
```
🎯 Routing Strategy: direct_reply
```

---

### Test 6: Clarification Request

**Objective**: Verify system asks for clarification on vague queries.

**Test Cases**:
```
Query: "it"
Expected: "I need more information..."

Query: "more"
Expected: "Could you be more specific..."
```

---

### Test 7: Context-Aware Multi-Query

**Objective**: Verify conversation history improves query generation.

**Steps**:
1. Ask: "What is LLM performance?"
2. Then ask: "Tell me more"
3. Check that second query uses context from first

**Expected**: Second query should be expanded to "Tell me more about LLM performance" based on conversation history.

---

### Test 8: PDF Page Number Accuracy

**Objective**: Verify page numbers in citations are correct.

**Steps**:
1. Upload a multi-page PDF
2. Ask about specific content
3. Check cited page numbers
4. Manually verify in the PDF that the content is on those pages

---

### Test 9: Audio Timestamp Accuracy

**Objective**: Verify timestamps match audio content.

**Steps**:
1. Upload an audio file
2. Ask about specific content
3. Check timestamp ranges
4. Play audio at those timestamps to verify content

---

### Test 10: Evaluation Scores

**Objective**: Verify evaluation scores are reasonable.

**Steps**:
1. Ask several different types of questions
2. Check evaluation scores in responses
3. Verify:
   - Good answers have scores > 0.7
   - Complex questions might trigger retries
   - Retry attempts shown in UI

---

## 🐛 Troubleshooting

### Issue: No citations returned

**Check**:
1. Document successfully uploaded and processed?
2. Chunks created in database?
3. Memgraph connection working?

**Solution**:
```bash
# Check backend logs for document processing
# Verify chunks were created
curl http://localhost:8000/api/documents
```

---

### Issue: No timestamps for audio

**Check**:
1. Whisper model loaded successfully?
2. Audio file format supported?
3. FFmpeg installed?

**Solution**:
```bash
# Check if FFmpeg is installed
ffmpeg -version

# Reinstall if needed
brew install ffmpeg  # macOS
```

---

### Issue: Evaluation always fails

**Check**:
1. Ollama running and accessible?
2. llama3.2 model downloaded?
3. Quality threshold too high?

**Solution**:
```bash
# Test Ollama
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Hello",
  "stream": false
}'

# Lower threshold if needed in graph_rag_enhanced.py
self.quality_threshold = 0.6  # Lower from 0.7
```

---

### Issue: Multi-query generation slow

**Solution**:
```python
# Reduce number of query variations
num_queries=1  # Instead of 2-3
```

---

## 📊 Performance Benchmarks

### Expected Response Times

| Query Type | Time | Notes |
|------------|------|-------|
| Direct reply | < 0.1s | No LLM or retrieval |
| Simple query | 1-2s | Single pass |
| Complex query | 3-5s | May need retries |
| Audio processing | 10-30s | Whisper transcription |

### Memory Usage

| Component | Memory | Notes |
|-----------|--------|-------|
| Ollama (llama3.2) | ~4GB | Running |
| Whisper (tiny) | ~75MB | When processing |
| Memgraph | ~500MB | Depends on documents |
| Backend | ~200MB | Python + FastAPI |

---

## ✅ Test Checklist

Before considering the feature complete, verify:

- [ ] Multi-query generation works
- [ ] Queries generate multiple variations
- [ ] Routing agent classifies correctly
- [ ] Direct replies work (greetings, meta)
- [ ] Clarification requests work
- [ ] Retrieval finds relevant chunks
- [ ] Evaluation scores are calculated
- [ ] Feedback loop triggers on low scores
- [ ] Retries improve answer quality
- [ ] PDF citations have page numbers
- [ ] Audio citations have timestamps
- [ ] Frontend displays citations properly
- [ ] Timestamps are formatted correctly (MM:SS)
- [ ] Page ranges are formatted correctly (pp. X-Y)
- [ ] Evaluation scores shown in UI
- [ ] Retry attempts shown in UI
- [ ] Citations are clickable/navigable
- [ ] Response times are acceptable
- [ ] No errors in backend logs
- [ ] No errors in frontend console

---

## 🎓 Advanced Testing

### Load Testing

```bash
# Test concurrent queries
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/chat \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message": "What are the findings?"}' &
done
```

### Evaluation Calibration

```python
# Test different quality thresholds
for threshold in [0.5, 0.6, 0.7, 0.8, 0.9]:
    service.quality_threshold = threshold
    test_queries_and_measure_retries()
```

### Citation Accuracy Test

```python
# Randomly sample citations and verify manually
import random

def verify_citations(citations, documents):
    sample = random.sample(citations, min(10, len(citations)))
    for citation in sample:
        # Check page number or timestamp
        verify_in_source_document(citation)
```

---

## 📝 Notes

1. **First run may be slow** - Models need to load
2. **Whisper transcription** takes time for long audio files
3. **Quality scores** may vary - tune threshold for your use case
4. **Multi-query** adds ~0.5s overhead but improves recall significantly
5. **Evaluation** adds ~0.3s but ensures quality

---

## 🚀 Ready to Test!

Start with Test 1 and work through the scenarios. Check both the UI and backend logs to verify everything is working as expected.

Good luck! 🎉
