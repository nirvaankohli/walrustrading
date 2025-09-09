from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
import secrets
import string
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
import hmac
import time

load_dotenv()

API_SECRET = os.getenv("API_SECRET")
if not API_SECRET:
    API_SECRET = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))
    print(f"âš ï¸  WARNING: No API_SECRET found in .env. Generated temporary secret: {API_SECRET}")
    print("âš ï¸  Add this to your .env file: API_SECRET=" + API_SECRET)

app = Flask(__name__)

CORS(app,
     origins=["http://localhost:5173", "http://127.0.0.1:5173"],
     methods=["GET", "POST"],
     allow_headers=["Content-Type", "X-API-KEY", "Authorization"],
     supports_credentials=False)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)

@app.after_request
def secure_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["X-XSS-Protection"] = "1; mode=block"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    resp.headers.pop("Server", None)
    return resp

def require_api_key():
    provided_key = request.headers.get("X-API-KEY", "")
    if not provided_key or not hmac.compare_digest(API_SECRET, provided_key):
        time.sleep(0.1)
        abort(401, description="Invalid or missing API key")

@app.route("/api/hello", methods=["GET"])
def hello():
    require_api_key()
    return jsonify({
        "message": "Hi From Flask!",
        "timestamp": int(time.time()),
        "status": "success"
    })

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": int(time.time())
    })

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({ "error": "Unauthorized", "message": "Valid API key required" }), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({ "error": "Not Found", "message": "Endpoint not found" }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({ "error": "Method Not Allowed", "message": "HTTP method not supported for this endpoint" }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({ "error": "Internal Server Error", "message": "An unexpected error occurred" }), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    if not API_SECRET or len(API_SECRET) < 32:
        print("âš ï¸  WARNING: API_SECRET should be at least 32 characters long for security")

    print(f"DEBUG: API_SECRET loaded: {'âœ“' if API_SECRET else 'âœ—'}")
    print(f"DEBUG: API_SECRET length: {len(API_SECRET) if API_SECRET else 0}")
    print(f"DEBUG: First 10 chars: {API_SECRET[:10] if API_SECRET else 'None'}...")

    print(f"ðŸš€ Starting Flask server on http://127.0.0.1:{port}")
    print("ðŸ”’ CORS enabled for: http://localhost:5173, http://127.0.0.1:5173")

    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
