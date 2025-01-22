# Student Experiences Analyzer

A Streamlit application for analyzing and categorizing student experiences using Gemini AI.

## Deployment to Streamlit Cloud

1. Fork this repository to your GitHub account
2. Sign up for Streamlit Cloud at <https://streamlit.io/cloud>
3. Create a new app and connect it to your forked repository
4. In the app settings, add the following secrets:
   - `GEMINI_API_KEY`: Your Google Gemini API key

## Local Development

1. Clone the repository
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create `.streamlit/secrets.toml` with your API key:

   ```toml
   GEMINI_API_KEY = "your-api-key-here"
   ```

4. Run the app:

   ```bash
   streamlit run app.py
   ```

## Project Structure

- `app.py`: Main application file
- `pages/`: Additional pages for the multi-page app
  - `1_detailed_results.py`: Detailed analysis view
  - `2_manage_categories.py`: Category management interface
- `data/`: Contains configuration files like `Classes.txt`
- `static/`: Static assets
  - `css/`: Custom CSS styles
- `examples/`: Sample data files in various formats (TXT, CSV, Excel)
- `.streamlit/`: Streamlit configuration files
- `requirements.txt`: Python dependencies

## Features

- Upload and process student responses from various file formats (TXT, CSV, Excel)
- Automatic categorization using Gemini AI
- Detailed analysis and visualization of results
  - Interactive charts and plots using Plotly
  - Customizable data views
- Export results to Excel
- Manage and customize categories
