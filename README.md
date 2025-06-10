STEP 1: Open VS Code
• Open Visual Studio Code on your system.
STEP 2: Create Project Folder
• Create a new folder, e.g., ResearchPaperSummarizer.
• Inside that folder, create the following subfolders:
o templates/ – for HTML file.
o uploads/ – to store uploaded PDFs (Flask will use this).
• Put your backend .py file in the root of the project folder.
• Put your HTML file in the templates/ folder.
STEP 3: Open Folder in VS Code
• Go to File > Open Folder...
• Select your ResearchPaperSummarizer folder.
STEP 4: Set Up Python Environment
• Make sure Python is installed. Check in terminal:
• python --version
• If not installed, download it from https://www.python.org.
• Create a virtual environment (optional but recommended):
• python -m venv venv
• Activate it:
o On Windows:
o venv\Scripts\activate
o On Mac/Linux:
o source venv/bin/activate
STEP 5: Install Required Python Libraries
Run the following commands in your terminal:
pip install flask
pip install PyPDF2
pip install requests
STEP 6: Create Files
• app.py – Paste the entire backend Python code here.
• templates/index.html – Paste the entire frontend HTML code here.
STEP 7: Run the Flask Server
In your terminal inside VS Code:
python app.py
You should see:
Running on http://127.0.0.1:5000/
STEP 8: Open in Browser
• Go to your browser.
• Type: http://127.0.0.1:5000/
• The Research Paper Summarizer UI will appear.
STEP 9: Test Your Application
• Upload a .pdf file.
• Click "Summarize".
• The system will show the summary.
• You can also ask questions about the PDF content.
NOTES:
• If any error occurs in the backend, check VS Code’s terminal for logs.
• Your backend uses OpenRouter API, so ensure you have internet access and your API key is valid.
• Don’t forget to keep uploads/ folder writable (Flask saves uploaded files here temporarily)
