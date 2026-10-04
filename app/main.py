"""Tiny URL shortener microservice (Flask).

Endpoints
---------
GET  /            -> service info (includes container/instance id)
GET  /health      -> health check used by Docker and CI
POST /shorten     -> {"url": "https://example.com"} -> short code
GET  /<code>      -> redirect to original URL
GET  /stats       -> number of stored links
"""
import os
import re
import secrets
import socket
import string
from urllib.parse import urlparse

from flask import Flask, jsonify, redirect, request

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 6
CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{%d}$" % CODE_LENGTH)


def is_valid_url(url) -> bool:
    """Return True only for well-formed http/https URLs."""
    if not isinstance(url, str) or len(url) > 2048:
        return False
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def generate_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["STORE"] = {}  # in-memory store: code -> url
    # Hostname == container id when running inside Docker.
    app.config["INSTANCE_ID"] = os.environ.get("INSTANCE_ID", socket.gethostname())

    @app.get("/")
    def index():
        return jsonify(
            service="url-shortener",
            version=os.environ.get("APP_VERSION", "1.0.0"),
            served_by=app.config["INSTANCE_ID"],
        )

    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    @app.post("/shorten")
    def shorten():
        data = request.get_json(silent=True) or {}
        url = data.get("url")
        if not is_valid_url(url):
            return jsonify(error="A valid http/https 'url' is required"), 400

        store = app.config["STORE"]
        code = generate_code()
        while code in store:  # avoid collisions
            code = generate_code()
        store[code] = url

        return (
            jsonify(
                code=code,
                short_url=request.host_url + code,
                original_url=url,
                served_by=app.config["INSTANCE_ID"],
            ),
            201,
        )

    @app.get("/stats")
    def stats():
        return jsonify(total_links=len(app.config["STORE"]))

    @app.get("/<code>")
    def follow(code):
        url = app.config["STORE"].get(code) if CODE_PATTERN.match(code) else None
        if url is None:
            return jsonify(error="Short code not found"), 404
        return redirect(url, code=302)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
