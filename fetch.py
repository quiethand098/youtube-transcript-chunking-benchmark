"""Fetch transcripts (with caption segments) for the 7 benchmark videos via the Apify Actor,
plus word-level timings for the auto-captioned ones straight from YouTube's timed-text track.
Needs APIFY_TOKEN in the environment."""
import json, os
from apify_client import ApifyClient
VIDEOS = ["zjkBMFhNj_g", "wjZofJX0v4M", "SxdOUGdseq4", "8pTEmbeENF4", "aircAruvnKk", "UF8uR6Z6KLc", "kCc8FmEb1nY"]
client = ApifyClient(os.environ["APIFY_TOKEN"])
run = client.actor("quiethand098/youtube-transcript-rag-extractor").call(run_input={"videos": VIDEOS, "includeSegments": True})
items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
json.dump(items, open("transcripts.json", "w"))
print(f"saved {len(items)} transcripts")
