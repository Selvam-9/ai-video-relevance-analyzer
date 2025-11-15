# ai-video-relevance-analyzer
A Streamlit app that uses AI to analyze YouTube video transcripts for relevance

## 💡 How It Works

This app follows a simple data flow:

1.  **Input:** The user provides a YouTube URL and a title/description to check against.
2.  **Transcript Fetch:** The app uses the `youtube_transcript_api` to download the full, timestamped transcript for the video.
3.  **AI Analysis:** The transcript, title, and description are sent to the Google Gemini API with a specific prompt.
4.  **JSON Response:** The AI returns a structured JSON object containing the score, justification, key points, summaries, etc.
5.  **Display:** Streamlit takes this JSON data and displays it in a clean, tabbed dashboard.

## 🛠️ Tech Stack

* **Language:** Python
* **Framework:** Streamlit (for the web UI)
* **AI Model:** Google Gemini
* **Data:** `youtube-transcript-api`

## 🚀 Future Improvements

This project is a great starting point. Here are some ideas for future versions:

* **Support for More Sources:** Add the ability to analyze plain text files (`.txt`) or audio files (`.mp3`).
* **Relevance-Over-Time Chart:** A visual line chart showing *when* the video is on-topic or off-topic.
* **Multi-Language Support:** Allow the user to select a transcript in other languages.
* **Batch Analysis:** Allow users to upload a CSV of 10-20 URLs and get a full report.
