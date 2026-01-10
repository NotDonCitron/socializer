# Architecture Plan

This plan outlines a clean separation between the UI panel, API/scheduler, and the automation worker.
It is intentionally minimal and scoped to the current repo layout.

## Components

1. admin-panel-temp/
- UI and orchestration layer.
- Initiates jobs and streams logs/screenshots.

2. socializer-api/
- Scheduling, API access, and persistent state.
- Owns job records and status transitions.

3. radar/ (worker)
- Executes automation flows (TikTok, Instagram).
- Emits structured logs and screenshots.

## Proposed Process Separation

- Panel starts jobs by writing to API (REST or WebSocket).
- API enqueues jobs (APScheduler for local, RQ/Celery for scale).
- Worker pulls jobs from the queue and runs automation.
- Worker sends logs/screenshots back to panel via API or websocket relay.

## Queue Options

Local/dev:
- APScheduler inside socializer-api for simplicity.
- Single machine, low volume.

Scale:
- RQ + Redis or Celery + Redis/RabbitMQ.
- Separate worker process for isolation and retries.

## Interfaces

- Job schema: id, platform, account_id, content_ref, status, retry_count, created_at.
- Worker output: JSON lines with level, timestamp, message, screenshot_base64.

## Next Steps

- Define a job schema in socializer-api.
- Add a lightweight job runner in radar/ (entrypoint).
- Add a websocket relay in admin-panel-temp to stream logs.
