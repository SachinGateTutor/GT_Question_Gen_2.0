# Minimal Flask AI MCQ & Schemdraw Backend

## Setup

1. **Clone the repository**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment variables:**
   - Create a `.env` file in the root directory:
     ```env
     OPENAI_API_KEY=your_openai_api_key_here
     ```
4. **Run the Flask server:**
   ```bash
   python app/main.py
   ```

## Usage

- **Endpoint:** `POST /api/generate`
- **Request JSON Example:**
  ```json
  {
    "stream": "CS",
    "subject": "Digital Logic",
    "topic": "AND Gate",
    "question_type": "MCQ",
    "requires_diagram": true,
    "custom_prompt": "Focus on basic logic gate operation."
  }
  ```
- **Response:**
  - `question_text`, `options`, `correct_answer`, `explanation`, `diagram_code`, `diagram_image_url`

## Notes
- Generated images are saved in `app/static/images/`.
- The server must have access to the internet for OpenAI API calls. 