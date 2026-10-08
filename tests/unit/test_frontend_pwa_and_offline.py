# tests/unit/test_frontend_pwa_and_offline.py

import json
import os
import pytest


def test_gate_o6_bundlewatch_and_lighthouse_budgets_configured():
    """
    Gate O-6: Configuration des budgets CI (.bundlewatchrc.json <= 170KB gzip et lighthouserc.json >= 85 performance).
    """
    assert os.path.exists(".bundlewatchrc.json")
    assert os.path.exists("lighthouserc.json")

    with open(".bundlewatchrc.json", "r", encoding="utf-8") as f:
        bw_config = json.load(f)

    # Vérifier que le cap bundle JS est fixé à 170kB
    js_rules = [r for r in bw_config["files"] if "*.js" in r["path"]]
    assert len(js_rules) > 0
    assert js_rules[0]["maxSize"] == "170kB"

    with open("lighthouserc.json", "r", encoding="utf-8") as f:
        lh_config = json.load(f)

    # Vérifier les assertions Lighthouse
    assertions = lh_config["ci"]["assert"]["assertions"]
    assert assertions["categories:performance"][1]["minScore"] == 0.85
    assert assertions["categories:accessibility"][1]["minScore"] == 0.90


def test_gate_o7_offline_queue_and_sw_custom_configured():
    """
    Gate O-7: Stratégie PWA hors-ligne (sw-custom.js et offlineQueueService.ts).
    """
    sw_path = "frontend/src/sw-custom.js"
    queue_path = "frontend/src/lib/services/offlineQueueService.ts"

    assert os.path.exists(sw_path)
    assert os.path.exists(queue_path)

    with open(sw_path, "r", encoding="utf-8") as f:
        sw_content = f.read()

    assert "StaleWhileRevalidate" in sw_content
    assert "CacheFirst" in sw_content
    assert "SKIP_WAITING" in sw_content

    with open(queue_path, "r", encoding="utf-8") as f:
        queue_content = f.read()

    assert "OfflineQueueService" in queue_content
    assert "401" in queue_content
    assert "403" in queue_content
    assert "409" in queue_content
