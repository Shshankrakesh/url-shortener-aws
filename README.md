# URL Shortener — Containerized Microservice on AWS

![CI/CD](https://github.com/SHSHANKRAKESH/url-shortener-aws/actions/workflows/ci-cd.yml/badge.svg)

A small Flask microservice that shortens URLs. It is **containerized with Docker**, tested and built by **GitHub Actions**, stored in **Amazon ECR**, and deployed on an **Amazon EC2** instance automatically on every push to `main`.

The goal of the project is hands-on exposure to a real deployment pipeline: code → tests → image → registry → cloud server.

## Architecture

```
                 ┌──────────────────────────────── AWS ─────────────────────────────────┐
                 │                                                                      │
┌────────┐ HTTP  │   ┌─────────────────── EC2 instance (Amazon Linux) ──────────────┐   │
│ Client │──────────▶│  port 80  ──▶  Docker container (Gunicorn + Flask, port 5000)│   │
│ (curl/ │◀──────────│                                                               │   │
│browser)│       │   └───────────────────────────────▲──────────────────────────────┘   │
└────────┘       │                                   │ docker pull                      │
                 │                          ┌────────┴────────┐                         │
                 │                          │   Amazon ECR    │                         │
                 │                          │ (image registry)│                         │
                 │                          └────────▲────────┘                         │
                 └───────────────────────────────────┼──────────────────────────────────┘
                                                     │ docker push
```

## CI/CD pipeline

```
 git push ──▶ GitHub Actions
                 │
                 ├─ Job 1: test      pytest (must pass)
                 │                      │ fails ─▶ pipeline stops, PR cannot be merged
                 │                      ▼ passes
                 └─ Job 2: deploy    build Docker image ─▶ push to ECR ─▶ SSH into EC2
                                     ─▶ pull new image ─▶ restart container
```

- **Tests block bad code:** the `test` job runs on every push and pull request. With branch protection enabled on `main` (see below), a pull request cannot be merged while the job is failing, and the `deploy` job only runs if `test` succeeded.
- **Deploy runs only on `main`.**

## API

| Method | Endpoint     | Description                                   |
|--------|--------------|-----------------------------------------------|
| GET    | `/`          | Service info + `served_by` (container id)     |
| GET    | `/health`    | Health check                                  |
| POST   | `/shorten`   | Body `{"url": "https://..."}` → short code    |
| GET    | `/<code>`    | Redirects (302) to the original URL           |
| GET    | `/stats`     | Number of stored links                        |

Note: links are stored in memory, so they reset when the container restarts. This keeps the project focused on deployment. A database (e.g. DynamoDB or RDS) would be the natural next step.

## Run locally

**With Python**
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -v                        # run tests
python -m app.main               # http://localhost:5000
```

**With Docker**
```bash
docker compose up --build        # http://localhost:5000
```

Try it:
```bash
curl http://localhost:5000/health
curl -X POST http://localhost:5000/shorten \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.github.com"}'
curl -L http://localhost:5000/<code-from-previous-response>
```

## Tests

`tests/test_app.py` contains 9 tests (health, index, shorten, redirect, invalid input, missing body, 404, stats, URL validator). Run with `pytest -v`.

## Deploy to AWS

Full step-by-step instructions are in **[docs/AWS_SETUP.md](docs/AWS_SETUP.md)**. Summary:

1. Create an ECR repository.
2. Launch an EC2 instance with Docker + AWS CLI, an IAM role allowing ECR pull, and port 80 open.
3. Add the GitHub secrets and set the repo variable `DEPLOY_ENABLED=true`.
4. Push to `main`. The pipeline deploys automatically.

### Required GitHub secrets

| Secret                  | Value                                      |
|-------------------------|--------------------------------------------|
| `AWS_ACCESS_KEY_ID`     | IAM user key (ECR push permissions)        |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret                            |
| `AWS_REGION`            | e.g. `ap-south-1`                          |
| `ECR_REPOSITORY`        | e.g. `url-shortener`                       |
| `EC2_HOST`              | EC2 public IP / DNS                        |
| `EC2_USER`              | `ec2-user` (Amazon Linux) / `ubuntu`       |
| `EC2_SSH_KEY`           | Contents of the `.pem` private key         |

### Blocking merges when tests fail

GitHub → **Settings → Branches → Add branch ruleset / protection rule** for `main`:
- Require a pull request before merging
- Require status checks to pass → select **test**

## Tech stack

Python 3.12 · Flask · Gunicorn · pytest · Docker · GitHub Actions · Amazon ECR · Amazon EC2

## Project structure

```
.
├── app/main.py                  # Flask application
├── tests/test_app.py            # pytest tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt / requirements-dev.txt
├── .github/workflows/ci-cd.yml  # test → build → push → deploy
└── docs/AWS_SETUP.md            # AWS setup guide
```
