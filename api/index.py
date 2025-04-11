from flask import Flask, request, jsonify
import PyPDF2
import requests
import json

app = Flask(__name__)
HUGGINGFACE_API_KEY = "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" 

def extract_text_from_pdf(pdf_file):
    """Extracts text from a PDF file using PyPDF2"""
    reader = PyPDF2.PdfReader(pdf_file)
    text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return text.strip()


def recommend_job(cv_text):
    """Get job recommendation using Hugging Face API with Gemma 2 9B Instruct"""
    prompt = f"""
    Analyze the following CV and output only the most relevant job title and don't add any special symbols :

    CV:
    {cv_text}

    Job Title:
    """
    
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 5, "temperature": 0.7}
    }

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/google/gemma-2-9b-it",
            headers=headers,
            data=json.dumps(payload)
        )
        response.raise_for_status()
        job_title = response.json()[0]["generated_text"].strip()
        
        # Extract and clean the job title
        job_title = job_title.split("\n")[-1].strip()
        return job_title
    except Exception as e:
        return f"Error: {e}"


@app.route("/recommend_job", methods=["POST"])
def job_recommendation_api():
    """Flask API endpoint to get a job recommendation from a CV PDF"""
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded."}), 400
    
    try:
        cv_text = extract_text_from_pdf(file)
        if not cv_text:
            return jsonify({"error": "Failed to extract text from the PDF."}), 400
        
        recommended_job = recommend_job(cv_text)
        return jsonify(recommended_job)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
