import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
import re, json, os, time

# ---------------------------
# Setup for GEMINI API
# ---------------------------
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.set_page_config(page_title="Error", page_icon="🚨", layout="wide")
    st.title("🚨 Configuration Error")
    st.error(
        "API Key not found. Please create a file named `.streamlit/secrets.toml` "
        "and add your key: \n\n"
        "```toml\n"
        "GEMINI_API_KEY = \"YOUR_AIza...KEY_HERE\"\n"
        "```"
    )
    st.stop() 
except Exception as e:
    st.set_page_config(page_title="Error", page_icon="🚨", layout="wide")
    st.title("🚨 Configuration Error")
    st.error(f"An unexpected error occurred while configuring the API: {e}")
    st.stop()

# ---------------------------
# Helper Functions
# ---------------------------
def extract_video_id(url):
    pattern = r"(?:v=|youtu\.be/|shorts/|embed/|watch\?v=)([\w\-]{11})"
    m = re.search(pattern, url)
    return m.group(1) if m else None

# --- [Using the older, more compatible get_transcript] ---
def get_youtube_transcript(url):
    video_id = extract_video_id(url)
    if not video_id:
        return None, "❌ Could not extract Video ID from URL."
    try:
        # Using the older function that your library supports.
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        
        transcript = [
            {"text": entry["text"], "start": entry["start"], "duration": entry["duration"]}
            for entry in transcript_data
        ]
        return transcript, None
    except NoTranscriptFound:
        return None, "❌ No transcript found for this video (it may be disabled by the creator)."
    except Exception as e:
        return None, f"❌ Error fetching transcript: {e}"


def transcript_to_text(chunks):
    return " ".join([c["text"].replace("\n", " ") for c in chunks])

def format_timestamp(seconds):
    mins, secs = divmod(int(seconds), 60)
    return f"{mins:02}:{secs:02}"

# ---------------------------
# AI ANALYSIS (FIXED PROMPT)
# ---------------------------
def analyze_video(title, description, transcript_chunks):
    transcript_text = transcript_to_text(transcript_chunks)

    # Schema is simplified
    schema = {
        "type": "object",
        "properties": {
            "relevance_score": {"type": "number"},
            "justification": {"type": "string"},
            "irrelevant_segments": {
                "type": "array",
                "items": {"type": "object", "properties": {"quote": {"type": "string"}, "reason": {"type": "string"}}, "required": ["quote", "reason"]}
            },
            "tags": {"type": "array", "items": {"type": "string"}},
            "summary": {"type": "string", "description": "A 2-3 sentence summary of what the video is about."},
            "key_points": {"type": "array", "items": {"type": "string"}, "description": "A list of the top 5 key points."},
            "quarterly_summaries": {
                "type": "array",
                "items": {"type": "string"},
                "description": "A list of 4 summaries, one for each 25% quarter of the video."
            }
        },
        "required": ["relevance_score", "justification", "irrelevant_segments", "tags", "summary", "key_points", "quarterly_summaries"]
    }

    model = genai.GenerativeModel(
        "gemini-2.5-flash",
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": schema
        }
    )

    # --- [ THE FIX ] ---
    # The prompt is now much stricter to prevent the AI from being "lazy"
    # and giving high scores to unrelated content.
    prompt = f"""
    You are a strict and meticulous content auditor. Your only job is to
    evaluate if a video's transcript matches its stated title and description.
    Be highly critical.

    **BENCHMARK TITLE:**
    {title}

    **BENCHMARK DESCRIPTION:**
    {description}

    **VIDEO TRANSCRIPT TO ANALYZE:**
    {transcript_text}

    ---
    **ANALYSIS TASK:**
    1.  Determine an *overall* `relevance_score` (0-100). This score MUST reflect
        how well the **VIDEO TRANSCRIPT** matches the **BENCHMARK TITLE** and **BENCHMARK DESCRIPTION**.
    2.  Write a `justification` for your score.
    3.  Identify *exact quotes* of any `irrelevant_segments` (sponsorships, off-topic sections).
    4.  Generate 3-5 `tags` *based on the transcript content*.
    5.  Write a brief `summary` (2-3 sentences) *of the transcript*.
    6.  List the **Top 5** `key_points` *from the transcript*.
    7.  Divide the transcript into four 25% parts. Summarize each quarter in 1-2 sentences. Return as a list of 4 strings in `quarterly_summaries`.

    **CRITICAL RULES:**
    - You MUST give a low score (0-30) if the **VIDEO TRANSCRIPT** discusses
      completely different topics than the **BENCHMARK TITLE**.
    - Do not be "helpful" and assume the title is a mistake.
    - Base your score *only* on the comparison.
    - Return STRICTLY VALID JSON matching the schema.
    - All arrays must be empty (`[]`) if no content is found, not null.
    """

    try:
        response = model.generate_content(prompt)
        response_data = json.loads(response.text)

        # 1. Process Irrelevant Segments
        ai_segments = response_data.get("irrelevant_segments", [])
        highlighted_segments = []
        for ai_seg in ai_segments:
            quote = ai_seg.get("quote")
            reason = ai_seg.get("reason")
            if not quote: continue
            for entry in transcript_chunks:
                if quote.strip() in entry["text"]:
                    highlighted_segments.append({
                        "timestamp": entry["start"],
                        "duration": entry["duration"],
                        "text": entry["text"],
                        "reason": reason
                    })
                    break 
        response_data["irrelevant_segments"] = highlighted_segments
        
        # We will also pass back the raw transcript text for debugging
        return response_data, transcript_text, None

    except Exception as e:
        st.error(f"Error during AI analysis: {e}")
        try:
            st.error(f"Raw AI Response (if any): {response.text}")
        except:
            pass
        return None, None, f"Error during AI analysis: {e}"

# ---------------------------
# 
#  STREAMLIT UI (with Manual Fallback)
# 
# ---------------------------
st.set_page_config(page_title="Video Relevance Checker", page_icon="🎥", layout="wide")
st.title("🎥 AI Video Content Relevance Evaluator")

st.warning(
    "**Note on Limits:** This tool uses public APIs. "
    "If you analyze many videos very quickly, you may be temporarily rate-limited. "
    "If you see an error, please wait 10-15 minutes and try again."
)

# --- [UI with Manual Fallback] ---
with st.form("video_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Content to Compare")
        video_title = st.text_input("Video Title (Required)", placeholder="e.g., The Ultimate Guide to Python 3")
        video_desc = st.text_area("Video Description (Optional)", placeholder="e.g., In this video, we cover the basics of Python...", height=245)

    with col2:
        st.subheader("🎬 Content to Analyze")
        st.info("Provide a URL **or** paste a transcript. The URL is preferred and will be used first.")
        yt_url = st.text_input("Method 1: YouTube URL (Preferred)", placeholder="httpss://www.youtube.com/watch?v=...")
        manual_transcript = st.text_area("Method 2: YouTube URL or Manual Transcript (Fallback)", height=150, placeholder="If no URL is provided, paste the transcript here...")

    submit_button = st.form_submit_button("Analyze Video Content", use_container_width=True, type="primary")


if submit_button:
    if not video_title:
        st.error("Please provide a Video Title to analyze.")
        st.stop()

    transcript_data, error = None, None
    raw_transcript_text_for_debug = "" # Initialize here

    with st.spinner("Fetching transcript..."):
        if yt_url:
            transcript_data, error = get_youtube_transcript(yt_url)
        
        # --- [Fallback Logic] ---
        if not transcript_data and manual_transcript.strip():
            if yt_url and error:
                st.info(f"Could not fetch transcript from URL ({error}). **Using manual transcript as fallback.** Timestamps will not be accurate.")
            elif not yt_url:
                st.info("No URL provided. **Using manual transcript.** Timestamps will not be accurate.")
            else:
                st.info("Empty transcript from URL. **Using manual transcript as fallback.** Timestamps will not be accurate.")

            chunks = [{"text": line, "start": i*5.0, "duration": 5.0} for i, line in enumerate(manual_transcript.split('\n')) if line.strip()]
            if not chunks:
                chunks = [{"text": manual_transcript, "start": 0.0, "duration": 9999.0}]
            transcript_data = chunks
            error = None 
        
        elif error:
            st.error(f"{error}. Please provide a valid URL or a manual transcript.")
            st.stop()
        elif not transcript_data:
            st.error("You must provide a YouTube URL or paste a manual transcript.")
            st.stop()

    with st.spinner("AI is analyzing the video... This may take a moment."):
        # Note the new return values
        result, raw_transcript_text_for_debug, error = analyze_video(video_title, video_desc, transcript_data)

    if error:
        st.error(f"Analysis failed: {error}")
        st.stop()
    if not result:
        st.error("Analysis returned no result.")
        st.stop()

    st.success("Analysis Complete!")

    # --- [TABS SIMPLIFIED] ---
    irrelevant_segments = result.get("irrelevant_segments", [])
    tab_list = [
        "📊 Dashboard",
        "⏱️ Quarterly Summary",
        f"🚩 Irrelevant Segments ({len(irrelevant_segments)})",
        "🏷️ Tags & Raw Data"
    ]
    
    tab1, tab2, tab3, tab4 = st.tabs(tab_list.copy())

    # --- Tab 1: Dashboard ---
    with tab1:
        st.subheader("📊 Key Metrics & Summary")
        st.write("This dashboard shows the overall score and the main content summary.")
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Overall Relevance")
            st.write("Compares your **Input (Title/Desc)** vs. the **Actual Video (Transcript)**.")
            
            score = result.get('relevance_score', 0)
            st.metric("Score", f"{score}%")
            
            if irrelevant_segments:
                st.metric("Content Flag", "🚩 IRRELEVANT", 
                          delta=f"{len(irrelevant_segments)} segment(s) detected", 
                          delta_color="inverse")
            else:
                st.metric("Content Flag", "✅ ON-TOPIC", 
                          delta="Looks Good", 
                          delta_color="normal")

            st.info(f"**AI Justification:** {result.get('justification', 'N/A')}")
        
        with col2:
            st.subheader("📃 AI Summary")
            st.write(result.get("summary", "No summary provided."))

            st.subheader("🔑 Top 5 Key Points")
            key_points = result.get("key_points", [])
            if key_points:
                for i, point in enumerate(key_points):
                    st.write(f"**{i+1}.** {point}")
            else:
                st.write("No key points provided.")

    # --- Tab 2: Quarterly Summary ---
    with tab2:
        st.subheader("⏱️ Video at a Glance (Quarterly Summary)")
        st.write("The video's content, summarized in 25% increments.")
        q_summaries = result.get("quarterly_summaries", [])
        
        if q_summaries and len(q_summaries) == 4:
            cols = st.columns(4)
            for i, summary in enumerate(q_summaries):
                with cols[i]:
                    st.markdown(f"**Quarter {i+1} ({(i*25)}%-{(i+1)*25}%)**")
                    st.write(summary)
        else:
            st.warning("Quarterly summaries could not be generated for this video.")

    # --- Tab 3: Irrelevant Segments ---
    with tab3:
        st.subheader(f"🚩 Irrelevant Segments ({len(irrelevant_segments)})")
        st.write("These are segments the AI flagged as off-topic, promotional, or irrelevant to the video's stated purpose.")
        if irrelevant_segments:
            for seg in irrelevant_segments:
                start_time = format_timestamp(seg.get('timestamp', 0))
                end_time = format_timestamp(seg.get('timestamp', 0) + seg.get('duration', 0))

                with st.expander(f"**{start_time} - {end_time}** | {seg.get('reason', 'No reason given')}"):
                    st.warning(f"**Reason:** {seg.get('reason', 'N/A')}")
                    st.markdown(f"**Transcript Text:**\n\n> {seg.get('text', 'N/A')}")
        else:
            st.success("🎉 No off-topic segments detected!")
    
    # --- Tab 4: Tags & Raw Data ---
    with tab4:
        st.subheader("🏷️ AI-Generated Category Tags")
        tags = result.get("tags", [])
        if tags:
            st.write(" ".join(f"` {tag} `" for tag in tags))
        else:
            st.write("No tags provided.")
        
        st.divider()
        
        with st.expander("Show Raw AI JSON Output (for debugging)"):
            st.json(result)
            
        # --- [DEBUGGING FIX] ---
        # Added the raw transcript text here so you can see what the AI saw.
        with st.expander("Show Raw Transcript Sent to AI (for debugging)"):

            st.text(raw_transcript_text_for_debug)
