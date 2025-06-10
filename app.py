from flask import Flask, request, render_template, jsonify
import PyPDF2
import os
import time
import requests
from werkzeug.utils import secure_filename
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variable to store PDF text context
current_pdf_text = ""

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    try:
        if not os.path.exists(pdf_file):
            logger.error(f"File does not exist: {pdf_file}")
            return f"Error: File {pdf_file} does not exist"
        logger.debug(f"Opening file: {pdf_file}")
        with open(pdf_file, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                logger.debug(f"Page text: {page_text[:100]}...")  # Log first 100 chars
                if page_text:
                    text += page_text + " "
            text = text.strip()
            logger.info(f"Extracted text length: {len(text)}")
            return text if text else "No text extracted from PDF"
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        return f"Error extracting text: {str(e)}"

# Function to summarize text using OpenRouter API
def summarize_text_openrouter(text, max_length=333, min_length=200):
    try:
        if not text or len(text.split()) < 10:
            logger.error("Input text too short or empty")
            return "Error: Input text is too short or empty for summarization"
        
        max_input_length = 4000
        text = text[:max_input_length]
        logger.debug(f"Truncated text length: {len(text)}")
        
        api_key = "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"  # Replace with your API key
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "Research Paper Summarizer"
        }
        data = {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": [
                {"role": "system", "content": "You are an assistant that generates concise summaries of research papers."},
                {"role": "user", "content": f"Summarize the following research paper text in approximately 250 words:\n\n{text}"}
            ],
            "max_tokens": max_length,  # ~250 words
            "min_length": min_length,
            "temperature": 0.7
        }
        logger.debug("Sending OpenRouter API request for summarization")
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('choices') and len(result['choices']) > 0:
                summary = result['choices'][0].get('message', {}).get('content', "Error: No summary text in API response").strip()
                words = len(summary.split())
                logger.info(f"Summary length: {words} words")
                if words < 200 or words > 300:
                    return f"Error: Summary length ({words} words) is outside the desired range (200-300 words)"
                return summary
            logger.error("No choices in API response")
            return "Error: No choices in API response"
        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return f"API error: {response.status_code} - {response.text}"
    except Exception as e:
        logger.error(f"Error summarizing text: {str(e)}")
        return f"Error summarizing text: {str(e)}"

# Function for question-answering using OpenRouter API
def answer_question_openrouter(question, context):
    try:
        if not context or len(context.split()) < 10:
            logger.error("No valid context for question-answering")
            return "Error: No valid context available for question-answering"
        
        api_key = "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"  # Replace with your API key
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "Research Paper Summarizer"
        }
        data = {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": [
                {"role": "system", "content": "You are an assistant that answers questions based on the provided research paper text."},
                {"role": "user", "content": f"Context: {context[:4000]}\n\nQuestion: {question}"}
            ],
            "max_tokens": 200
        }
        logger.debug(f"Sending OpenRouter API request for question: {question}")
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('choices') and len(result['choices']) > 0:
                answer = result['choices'][0].get('message', {}).get('content', "Error: No answer in API response").strip()
                logger.info(f"Answer generated: {answer[:100]}...")
                return answer
            logger.error("No choices in API response")
            return "Error: No choices in API response"
        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return f"API error: {response.status_code} - {response.text}"
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        return f"Error answering question: {str(e)}"

# Function to safely remove file
def safe_remove(file_path, retries=3, delay=1):
    for attempt in range(retries):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
            return True
        except OSError as e:
            logger.error(f"Attempt {attempt + 1} to delete {file_path} failed: {str(e)}")
            if attempt < retries - 1:
                time.sleep(delay)
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_pdf():
    global current_pdf_text
    try:
        logger.debug(f"Files received: {request.files}")
        if 'file' not in request.files:
            logger.error("No file uploaded")
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        logger.info(f"File name: {file.filename}")
        if file.filename == '':
            logger.error("No file selected")
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate .pdf extension
        if not file.filename.lower().endswith('.pdf'):
            logger.error(f"Invalid file extension: {file.filename}")
            return jsonify({'error': 'Invalid file format. Please upload a PDF.'}), 400
        
        filename = secure_filename(file.filename)
        file_path = os.path.join('uploads', filename)
        uploads_dir = os.path.dirname(file_path)
        
        # Ensure uploads directory exists and is writable
        try:
            os.makedirs(uploads_dir, exist_ok=True)
            logger.debug(f"Uploads directory ensured: {uploads_dir}")
            # Test write permissions
            test_file = os.path.join(uploads_dir, 'test.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            logger.error(f"Cannot create/write to uploads directory: {str(e)}")
            return jsonify({'error': f"Server error: Cannot write to uploads directory: {str(e)}"}), 500
        
        # Save file
        logger.debug(f"Saving file to: {file_path}")
        file.save(file_path)
        
        # Verify file was saved
        if not os.path.exists(file_path):
            logger.error(f"File not saved: {file_path}")
            return jsonify({'error': f"Failed to save file: {file_path}"}), 500
        
        text = extract_text_from_pdf(file_path)
        if text.startswith("Error"):
            safe_remove(file_path)
            logger.error(f"Text extraction failed: {text}")
            return jsonify({'error': text}), 500
        
        current_pdf_text = text
        summary = summarize_text_openrouter(text)
        if not safe_remove(file_path):
            logger.warning(f"Failed to delete file: {file_path}")
            return jsonify({'error': f"Failed to delete file: {file_path}"}), 500
        
        if summary.startswith("Error"):
            logger.error(f"Summary failed: {summary}")
            return jsonify({'error': summary}), 500
        
        # Get page count
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                page_count = len(reader.pages)
        except Exception as e:
            logger.error(f"Error getting page count: {str(e)}")
            page_count = 0
        
        logger.info("Upload successful")
        return jsonify({
            'summary': summary,
            'page_count': page_count,
            'text_length': len(text)
        }), 200
    except Exception as e:
        safe_remove(file_path)
        logger.error(f"Server error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.get_json()
        question = data.get('question', '')
        if not question:
            logger.error("No question provided")
            return jsonify({'error': 'No question provided'}), 400
        
        if not current_pdf_text:
            logger.error("No PDF context available")
            return jsonify({'error': 'No PDF context available. Please upload a PDF first.'}), 400
        
        answer = answer_question_openrouter(question, current_pdf_text)
        if answer.startswith("Error"):
            logger.error(f"Question answering failed: {answer}")
            return jsonify({'error': answer}), 500
        
        logger.info(f"Question answered: {question}")
        return jsonify({'answer': answer}), 200
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)