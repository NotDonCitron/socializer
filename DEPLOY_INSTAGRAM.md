# Instagram Deployment (Admin Panel + API)

This guide sets up the Instagram-only flow with `admin-panel-temp` and `socializer-api`.

## Prereqs
- Python 3.11+
- Node 18+

## 1) Seed API Data
```
powershell -ExecutionPolicy Bypass -File .\scripts\seed_api.ps1
```

## 2) Start API
```
powershell -ExecutionPolicy Bypass -File .\scripts\start_api.ps1
```

## 3) Start Admin Panel
```
powershell -ExecutionPolicy Bypass -File .\scripts\start_panel.ps1
```
The UI runs on `http://localhost:5501`.

## 4) Validate
```
powershell -ExecutionPolicy Bypass -File .\scripts\run_checks.ps1
```

## Notes
- Jobs are created from approved content packs.
- This setup targets `instagram_reels` only.
