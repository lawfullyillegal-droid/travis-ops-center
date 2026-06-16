# ============================================
#  COMMAND VAULT — TRAVIS / TERMUX OPS CENTER
# ============================================

# -------------------------
# 1. AI / LLM SYSTEM
# -------------------------

## Start Droid AI (Internet Edition)
# Launches llama-server and opens the Droid shell
bash ~/launch-droid.sh

## Kill AI server
# Stops any running llama-server instance
pkill -f llama-server

## Check if AI is running
ps aux | grep llama

## Test AI server
curl -X POST http://127.0.0.1:8080/completion -d '{"prompt":"Hello"}'


# -------------------------
# 2. OSINT / RECON TOOLS
# -------------------------

## ReconDog
cd ~/ReconDog
python3 dog.py

## RED_HAWK
cd ~/RED_HAWK
php rhawk.php

## Storm-Breaker
cd ~/Storm-Breaker
python3 storm.py

## Dork Results Parser
cd ~/Dork_Results
python3 parse.py


# -------------------------
# 3. AUDIT ENGINES
# -------------------------

## Mohave Audit
python3 ~/mohave_audit.py

## Audit Engine Core
cd ~/audit-engine
python3 engine.py

## Audit Pipeline
python3 ~/audit_pipeline.py

## Audit Recorder
python3 ~/audit_recorder.py


# -------------------------
# 4. NETWORK / RF / DEVICE SCANNERS
# -------------------------

## BLE Radar
python3 ~/ble_radar.py

## Hotspot Radar
python3 ~/hotspot_radar.py

## Android Radar
python3 ~/android_radar.py

## Cell Tower Audit
python3 ~/cell_tracker.py

## Network Audit
python3 ~/network_audit.py

## Proximity Radar
python3 ~/proximity_radar.py


# -------------------------
# 5. HARVESTERS / SCRAPERS
# -------------------------

## Mohave Range Harvester
python3 ~/mohave_range_harvest.py

## Live Lead Scraper
python3 ~/live_lead_scraper.py

## Fresh Leads
python3 ~/fresh_leads.csv


# -------------------------
# 6. EVIDENCE / EXHIBIT TOOLS
# -------------------------

## Clean & OCR PDFs
python3 ~/clean_and_ocr.py

## Parse Court Payloads
python3 ~/parse_court_payloads.py

## Get Evidence
python3 ~/get_evidence.py

## Exhibit Hash Checker
cat ~/exhibit_hashes.txt


# -------------------------
# 7. LEGAL / DOCUMENT GENERATORS
# -------------------------

## Generate Notices
python3 ~/generate_notices.py

## Generate PDF
python3 ~/generate_pdf.py

## Generate Report
python3 ~/generate_report.py

## Generate Prover9 Input
python3 ~/generate_prover9_input.py


# -------------------------
# 8. DATABASE / LEDGER OPS
# -------------------------

## Integrity DB Init
python3 ~/init_audit_db.py

## Query Integrity Ledger
python3 ~/query_integrity_ledger.py

## Data Registry
sqlite3 ~/data_registry.db


# -------------------------
# 9. UTILITIES / SYSTEM OPS
# -------------------------

## List everything
ls -lah ~

## Recursive file tree
ls -R ~

## Search for scripts
find ~ -type f -name "*.py"

## Search for folders
find ~ -type d -maxdepth 2

## Check running processes
ps aux

## Kill any stuck process
pkill -f <name>
