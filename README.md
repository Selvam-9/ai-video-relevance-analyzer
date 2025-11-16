# ai-video-relevance-analyzer
A Streamlit app that uses AI to analyze YouTube video transcripts for relevance

## 💡 How It Works

This app follows a simple data flow:

1.  **Input:** The user provides a YouTube URL and a title/description to check against.
2.  **Transcript Fetch:** The app uses the `youtube_transcript_api` to download the full, timestamped transcript for the video.
3.  **AI Analysis:** The transcript, title, and description are sent to the Google Gemini API with a specific prompt.
4.  **JSON Response:** The AI returns a structured JSON object containing the score, justification, key points, summaries, etc.
5.  **Display:** Streamlit takes this JSON data and displays it in a clean, tabbed dashboard.
