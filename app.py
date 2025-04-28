from flask import Flask, request, jsonify
import requests
import logging
import io
import PyPDF2

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenRouter API Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = "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"  # Replace with your actual OpenRouter API key

# Prompts
ANALYZE_PROMPT = """
You are a professional career coach. Analyze the following resume text and provide specific, actionable suggestions to improve the candidate's skills and profile for the given job description:

Resume:
{}

Job Description:
{}
"""

SKILL_IMPROVE_PROMPT = """
You are a professional career coach. Review the following resume text and suggest targeted skill development opportunities to align with the provided job description:

Resume:
{}

Job Description:
{}
"""

PERCENTAGE_MATCH_PROMPT = """
You are a professional career coach. Evaluate the following resume text against the provided job description and estimate a percentage match :

Resume:
{}

Job Description:
{}
"""

# OpenRouter API call
def query_openrouter(prompt, retries=3, delay=5):
    for attempt in range(retries):
        try:
            payload = {
                "model": "openai/gpt-4o",  # Replace with the desired model
                "messages": [
                    {"role": "system", "content": "You are a helpful career coach."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 500
            }
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional. Your site URL
                "X-Title": "<YOUR_SITE_NAME>"  # Optional. Your site title
            }

            response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)

            # Check for errors
            if response.status_code != 200:
                logger.error(f"OpenRouter error response: {response.status_code} - {response.text}")
                return None, f"Error querying OpenRouter API: {response.text}"

            result = response.json()
            return result["choices"][0]["message"]["content"].strip(), None

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API error: {str(e)}")
            return None, f"Error querying OpenRouter API: {str(e)}"

    return None, "Error querying OpenRouter API: Max retries reached"

# PDF text extraction
def extract_pdf_text(file):
    try:
        if not file or file.filename == '':
            return None, "No file provided"
        if not file.filename.lower().endswith('.pdf'):
            return None, "Invalid file type; only PDF files are accepted"
        file_content = file.read()
        if not file_content:
            return None, "Empty file received"

        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        if len(pdf_reader.pages) == 0:
            return None, "PDF has no pages"

        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text() or ""
            text += page_text

        if not text.strip():
            return None, "No text could be extracted from PDF (may be scanned or image-based)"
        return text, None
    except Exception as e:
        return None, f"PDF processing error: {str(e)}"

# --- API Routes ---

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        file = request.files.get("resume")
        job_desc = request.form.get("job_desc", "").strip()
        if not file or not job_desc:
            return jsonify({"error": "Missing resume file or job description"}), 400

        resume_text, error = extract_pdf_text(file)
        if error:
            return jsonify({"error": error}), 500

        prompt = ANALYZE_PROMPT.format(resume_text, job_desc)
        response, error = query_openrouter(prompt)
        if error:
            return jsonify({"error": error}), 500

        return jsonify({"suggestions": response})
    except Exception as e:
        logger.error(f"Analyze error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/skill_improve", methods=["POST"])
def skill_improve():
    try:
        file = request.files.get("resume")
        job_desc = request.form.get("job_desc", "").strip()
        if not file or not job_desc:
            return jsonify({"error": "Missing resume file or job description"}), 400

        resume_text, error = extract_pdf_text(file)
        if error:
            return jsonify({"error": error}), 500

        prompt = SKILL_IMPROVE_PROMPT.format(resume_text, job_desc)
        response, error = query_openrouter(prompt)
        if error:
            return jsonify({"error": error}), 500

        return jsonify({"suggestions": response})
    except Exception as e:
        logger.error(f"Skill improve error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/percentage_match", methods=["POST"])
def percentage_match():
    try:
        file = request.files.get("resume")
        job_desc = request.form.get("job_desc", "").strip()
        if not file or not job_desc:
            return jsonify({"error": "Missing resume file or job description"}), 400

        resume_text, error = extract_pdf_text(file)
        if error:
            return jsonify({"error": error}), 500

        prompt = PERCENTAGE_MATCH_PROMPT.format(resume_text, job_desc)
        response, error = query_openrouter(prompt)
        if error:
            return jsonify({"error": error}), 500

        return jsonify({"match_percentage": response})
    except Exception as e:
        logger.error(f"Percentage match error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "Server is running"})

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "500 Internal Server Error"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "404 Not Found"}), 404

# Run the server
if __name__ == "__main__":
    app.run(debug=False)
