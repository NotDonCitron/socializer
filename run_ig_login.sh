#!/bin/bash
cd "$(dirname "$0")"
export PYTHONPATH=.
.venv/bin/python -m radar.auth_bridge_ig
