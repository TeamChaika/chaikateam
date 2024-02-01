#!/bin/bash
cd "$(dirname "$0")"
cd "../../"
git pull origin main
systemctl restart supervisor