# Legal Petition Generator - PDF Generator

This script fetches data from a backend API endpoint and generates a legal document PDF based on the response.

## Steps to Run the Script

1. Create a Python 3.10 virtual environment:
   ```
   python3.10 -m venv legal_venv
   ```

2. Activate the virtual environment:
   ```
   source legal_venv/bin/activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your OpenAI API key:
   Create a `.env` file in the root directory with the following content:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
   Replace `your_api_key_here` with your actual OpenAI API key.

5. Ensure the backend API is running at `http://localhost:9000/api/process-backend`

6. Run the script:
   ```
   python fetch_and_generate_pdf.py
   ```

## Script Workflow

1. Fetch data from the backend API endpoint
2. Extract langchain response and user details
3. Use the LegalDocumentAgent to determine the type of document to generate
4. Generate a PDF document based on the response
5. Save the PDF in the `generated_pdfs` directory

## Response Format

The API response is expected to have the following structure:
```json
{
  "langchain_response": "...",
  "retrieved_chunks": [],
  "saved_query": "...",
  "status": "success",
  "user_details": {
    "address": "...",
    "name": "...",
    "phone": "..."
  }
}
```

The PDF generation process extracts the langchain_response and user details to create an appropriate legal document. 