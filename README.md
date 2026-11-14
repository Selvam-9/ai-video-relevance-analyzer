# AI Video Relevance Analyzer

A Streamlit application that compares a YouTube video's transcript with its supplied title and description using Google's Gemini API.

## What it does

1. Accepts a YouTube video URL or a manually pasted transcript.
2. Retrieves the transcript when a URL is supplied and captions are available.
3. Compares the transcript with the expected title and optional description.
4. Produces a structured analysis containing:
   - Relevance score (0–100) and explanation
   - Summary and key points
   - Content tags
   - Potentially irrelevant or off-topic segments
   - Four summaries covering successive quarters of the transcript
5. Displays the results in a Streamlit dashboard.

The relevance score is an AI-generated estimate, not an objective measure of video quality.

## Requirements

- Python 3.11 (the development container is configured for Python 3.11)
- A Google Gemini API key
- YouTube captions/transcripts for URL-based analysis, or a transcript supplied manually

## Local setup

1. Clone this repository and open a terminal in its directory.
2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   ```

   Windows PowerShell:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   macOS/Linux:

   ```bash
   source .venv/bin/activate
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create the Streamlit secrets file at `.streamlit/secrets.toml`:

   ```toml
   GEMINI_API_KEY = "your-gemini-api-key"
   ```

5. Start the application:

   ```bash
   streamlit run MyVideoProject.py
   ```

## API key and data handling

- Keep your Gemini API key in Streamlit secrets. Never hard-code it or commit it.
- The transcript, title and description are sent to Google's Gemini API for analysis.
- Only analyze content you are permitted to submit to that service. Review Google's applicable API terms and data policies.
- Do not paste passwords, private information or other sensitive data into the application.

## Known limitations

- URL-based analysis depends on transcript availability and the behavior/compatibility of the YouTube transcript library.
- Some videos have captions disabled, unavailable or restricted. Use the manual transcript option when appropriate.
- Transcript retrieval and Gemini requests may fail because of network, quota, rate-limit or API errors.
- AI-generated scores, summaries and segment flags can be inaccurate and should be reviewed by a person.
- The current implementation is a Streamlit application. It is not yet packaged as a standalone command-line tool or AI-agent skill.

## Project files

- `MyVideoProject.py`: Streamlit interface and current analysis implementation.
- `requirements.txt`: Python dependencies.
- `.devcontainer/`: development-container configuration.

## Development status

This project is an experimental prototype. Dependency versions, transcript-library compatibility, input validation, structured-output validation and automated tests should be reviewed before production or commercial use.
