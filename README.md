Genderize API — Stage 0 Submission
A single GET endpoint built with Django that calls the Genderize.io API, processes the response, and returns a structured result.
Tech Stack
Runtime: Python 3.10+
Framework: Django 4.2
HTTP client: requests
Server: Gunicorn
Project Structure
genderize-api/
├── core/
│   ├── settings.py      # Django settings
│   ├── urls.py          # Root URL config
│   └── wsgi.py          # WSGI entry point
├── api/
│   ├── views.py         # ClassifyView logic
│   ├── urls.py          # /api/classify route
│   └── middleware.py    # CORS middleware
├── manage.py
├── requirements.txt
├── Procfile             # For Railway / Heroku
└── railway.json
Endpoint
GET /api/classify?name={name}
Success Response 200 OK
{
  "status": "success",
  "data": {
    "name": "john",
    "gender": "male",
    "probability": 0.99,
    "sample_size": 1234,
    "is_confident": true,
    "processed_at": "2026-04-15T10:30:00Z"
  }
}
Error Responses
Status
Trigger
Message
400
Missing or empty name param
"Missing or empty name parameter"
422
name is not a string
"name must be a string"
200 (error body)
Genderize returns null gender or count: 0
"No prediction available for the provided name"
502
Upstream Genderize API failure or timeout
"Upstream API returned an error"
500
Internal server error
"Internal server error"
All errors:
{ "status": "error", "message": "<error message>" }
Processing Logic
Field
Source
Notes
name
Genderize response
Lowercased by Genderize
gender
response["gender"]
"male" or "female"
probability
response["probability"]
0–1 float
sample_size
response["count"]
Renamed from count
is_confident
Computed
true only if probability >= 0.7 AND sample_size >= 100
processed_at
datetime.now(timezone.utc)
Live UTC ISO 8601, never hardcoded
Run Locally
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the development server
python manage.py runserver

# 4. Test
curl "http://localhost:8000/api/classify?name=john"
curl "http://localhost:8000/api/classify?name=kim"
curl "http://localhost:8000/api/classify"           # → 400
curl "http://localhost:8000/api/classify?name="     # → 400
Deploy to Railway
Push this repo to GitHub
Go to railway.app → New Project → Deploy from GitHub repo
Railway auto-detects Python via railway.json and Procfile
Set these environment variables in Railway dashboard:
SECRET_KEY — any long random string
ALLOWED_HOSTS — your Railway domain e.g. myapp.up.railway.app
DEBUG — False
Your live URL will be https://yourapp.up.railway.app
Deploy to Heroku
heroku create your-app-name
heroku config:set SECRET_KEY=your-secret ALLOWED_HOSTS=your-app-name.herokuapp.com DEBUG=False
git push heroku main
CORS
Access-Control-Allow-Origin: * is applied by a custom middleware on every response, including errors, so the grading script can reach the server from any origin.
