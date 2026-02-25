# AWS Diagram Generator (Phase 1 MVP)

This repository contains a Dockerized Phase 1 implementation of the AWS Diagram Generator PRD.

## Included in this MVP

- FastAPI backend with request validation
- Static PNG diagram rendering endpoint
- Browser form for required Phase 1 fields
- AWS region dropdown populated from backend
- PNG preview + automatic download
- Docker and docker-compose startup

## AWS official icons setup

The renderer supports official AWS icon files for `EC2`, `RDS`, and `FSx`.

Preferred file names:

- `/Users/auguststartz/Documents/Code/Diagramer 2000/app/icons/aws/ec2.png`
- `/Users/auguststartz/Documents/Code/Diagramer 2000/app/icons/aws/rds.png`
- `/Users/auguststartz/Documents/Code/Diagramer 2000/app/icons/aws/fsx.png`

It also auto-discovers icons recursively under `/Users/auguststartz/Documents/Code/Diagramer 2000/app/icons/aws` when filenames include `ec2`, `rds`, or `fsx`.

Reference details: [app/icons/aws/README.md](/Users/auguststartz/Documents/Code/Diagramer%202000/app/icons/aws/README.md)

## Run with Docker

```bash
docker compose up --build
```

Open: `http://localhost:8000`

## Run locally (without Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.backend.main:app --reload
```

## API

- `GET /health`
- `GET /api/v1/regions`
- `POST /api/v1/diagram.png`

Example payload:

```json
{
  "customer_name": "Acme Health System",
  "region": "us-east-2",
  "production_server_count": 2,
  "availability_zone_count": 2,
  "non_production_server_count": 1,
  "include_rds": true,
  "include_fsx": true
}
```
