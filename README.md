# YouTube transcript chunking benchmark (RAG)

Small, reproducible benchmark behind the article *"My YouTube transcript chunker was silently dropping 20% of the text from my embeddings"*.

- 7 talks (2 with auto-generated captions, 5 with human captions), 85 paraphrased questions with gold answer phrases (`qa.json`)
- Chunkers: fixed windows, fixed + 20% overlap, sentence/2-second-pause (`actor_v1`), pause-scoring with word-level timings (`pause_aware_v2`)
- Embeddings: `BAAI/bge-small-en-v1.5` via fastembed (CPU), plus BM25
- Metrics: answer split across chunks, dense top-1/top-3, BM25 top-3, top-1 hit from the wrong video; with and without a title/channel prefix

## Run

```bash
pip install -r requirements.txt
export APIFY_TOKEN=...            # transcripts are fetched with the Actor, not stored here
python fetch.py                   # -> transcripts.json
python words.py                   # -> asr_words.json (word-level timings for auto captions)
python exp.py 500 1000 2000       # per-video index
python exp2.py                    # one index over all videos, with/without title prefix
```

Results from my run are in `results_per_video.txt` and `results_global_index.txt`. With 85 questions, differences of about 5 are within noise.

Transcripts come from [YouTube Transcript Extractor](https://apify.com/quiethand098/youtube-transcript-rag-extractor) on Apify. MIT license.
