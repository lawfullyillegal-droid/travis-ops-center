# Travis Ops Center - System Architecture

## Overview

Travis Ops Center is a forensic evidence management and command execution platform designed for rapid incident response and cybersecurity investigations. The system integrates automated evidence capture, command vault execution, case management, and web-based operations dashboard.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Web Dashboard (Flask)                       │
│  /workspaces/travis-ops-center/web/app.py                          │
│  - Operations Dashboard (dark-themed)                              │
│  - Evidence Browser                                                │
│  - Command Execution UI                                           │
│  - Case Management Interface                                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Command Center Orchestrator                       │
│  /workspaces/travis-ops-center/scripts/command_center.py           │
│  - Command Validation                                             │
│  - Evidence Capture Coordination                                  │
│  - Case Management Logic                                          │
│  - Audit Logging                                                  │
└────────┬──────────────┬──────────────┬──────────────┬──────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    ┌────────┐  ┌────────────┐  ┌─────────┐  ┌──────────┐
    │ Command│  │ Evidence   │  │  Case   │  │  Audit   │
    │ Vault  │  │ Ingest     │  │ Manager │  │  Logger  │
    │        │  │            │  │         │  │          │
    │commands│  │evidence_   │  │command_ │  │audit_    │
    │.yml    │  │ingest.py   │  │center.py   │logger.py │
    └────────┘  └────────────┘  └─────────┘  └──────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                        │
                        ▼
    ┌───────────────────────────────────────┐
    │      Evidence Storage System          │
    │  /workspaces/travis-ops-center/      │
    │                                      │
    │  ├── evidence/20260619/              │
    │  │   ├── evidence-*.txt              │
    │  │   └── evidence-*.txt.meta.json    │
    │  ├── data/                           │
    │  │   ├── targets.json                │
    │  │   ├── case_notes.md               │
    │  │   └── evidence.db                 │
    │  ├── logs/                           │
    │  │   └── audit.log                   │
    │  └── evidence_notes/                 │
    │      └── *.md                        │
    └───────────────────────────────────────┘
         │              │
         ▼              ▼
    ┌──────────┐   ┌──────────┐
    │ Git Repo │   │ SQLite   │
    │(Evidence │   │Database  │
    │ Vault)   │   │(Index)   │
    └──────────┘   └──────────┘
```

---

## Component Details

### 1. Web Interface (Flask Application)

**Location:** `/workspaces/travis-ops-center/web/app.py`

**Responsibility:** 
- User-facing operations dashboard
- Real-time evidence viewer
- Command execution interface
- Case management UI

**Key Routes:**
```
GET  /                    - Dashboard home
GET  /evidence            - Evidence browser
GET  /cases              - Case management
GET  /targets            - Target investigation
POST /execute            - Command execution
GET  /audit              - Audit log viewer
GET  /status             - System health
```

**Frontend Components:**
- `web/templates/dashboard.html` - Main dashboard layout
- `web/templates/evidence.html` - Evidence viewer
- `web/templates/index.html` - Home page
- `web/static/app.js` - JavaScript application logic
- `web/static/style.css` - Dark-themed styling

**Configuration:**
- Host: 0.0.0.0
- Port: 5000 (configurable in `config/settings.yml`)
- Debug Mode: Enabled in development
- Session Timeout: 60 minutes

---

### 2. Command Center Orchestrator

**Location:** `/workspaces/travis-ops-center/scripts/command_center.py`

**Responsibility:**
- Central orchestration engine
- Command validation and execution
- Evidence capture coordination
- Case file management
- Operator authentication and authorization

**Key Functions:**
```python
def init_case(case_number, operator)
    # Create new investigation case

def add_target(case_number, target_type, target_value)
    # Add investigation target

def execute_command(command_id, target, case_number, operator)
    # Execute command from vault with proper logging

def capture_evidence(output, metadata)
    # Create timestamped evidence file

def sync_vault()
    # Synchronize evidence to git repository

def generate_report(case_number)
    # Create comprehensive case report
```

**Workflow:**
1. Receive command execution request
2. Validate command exists in `config/commands.yml`
3. Check command not in `config/blacklist.txt`
4. Verify operator permissions
5. Set execution context (timeout, environment)
6. Execute command and capture output
7. Create evidence file with metadata
8. Log execution to audit trail
9. Synchronize to git vault
10. Return evidence file reference

---

### 3. Evidence Management System

**Location:** `/workspaces/travis-ops-center/evidence/`

**Structure:**
```
evidence/
├── YYYYMMDD/                    # Date-organized directories
│   ├── evidence-<timestamp>Z-<hash>.txt
│   ├── evidence-<timestamp>Z-<hash>.txt.meta.json
│   └── evidence-<timestamp>Z-<hash>.txt.asc
└── outputs/                     # Generated reports
    └── output-<timestamp>Z.txt
```

**Evidence File Format:**

**Filename:** `evidence-20260619T153037Z-f1688e4b9a.txt`
- `20260619T153037Z` = UTC timestamp (ISO 8601)
- `f1688e4b9a` = First 10 hex digits of SHA256 hash

**File Contents:**
```
=== TRAVIS OPS CENTER EVIDENCE CAPTURE ===
Case Number: 44
Operator: lawfullyillegal-droid
Timestamp: 2026-06-19T15:30:37Z
Command: nmap_scan
Target: 192.168.1.105
===================================

[COMMAND OUTPUT]
Nmap 7.93 ( https://nmap.org )
...
```

**Metadata File:** `evidence-20260619T153037Z-f1688e4b9a.txt.meta.json`
```json
{
  "case_number": 44,
  "evidence_id": "evidence-20260619T153037Z-f1688e4b9a",
  "timestamp": "2026-06-19T15:30:37Z",
  "operator": "lawfullyillegal-droid",
  "command_id": "nmap_scan",
  "target": "192.168.1.105",
  "hash_sha256": "f1688e4b9a...",
  "file_size_bytes": 2847,
  "status": "captured",
  "retention_until": "2026-09-17"
}
```

---

### 4. Configuration System

**Command Vault:** `config/commands.yml`
- 30+ pre-configured reconnaissance commands
- Categorized by type (network, web, system, OSINT, etc.)
- Timeout and resource limits defined
- Role-based execution requirements
- Safe command whitelist approach

**Global Settings:** `config/settings.yml`
- Database paths and retention policies
- Logging configuration
- Operator credentials
- Case management defaults
- Web interface settings
- Security policies

**Blacklist:** `config/blacklist.txt`
- Forbidden command patterns
- Dangerous operations (rm -rf, dd, etc.)
- Network-disruptive commands
- Prevents accidental system damage

---

### 5. Investigation Data

**Targets:** `data/targets.json`
```json
[
  {
    "id": "target_001",
    "case_number": 44,
    "type": "ip_address|domain|username",
    "target_value": "...",
    "status": "active|investigating|resolved",
    "priority": "low|medium|high|critical",
    "commands_executed": 12,
    "artifacts_collected": 4
  }
]
```

**Case Notes:** `data/case_notes.md`
- Structured case documentation
- Timeline of events
- Analysis findings
- Preliminary conclusions
- Next steps

**Evidence Database:** `data/evidence.db` (SQLite3)
- Indexed evidence lookups
- Case metadata
- Audit trail queries
- Evidence chain of custody tracking

---

### 6. Audit and Logging

**Audit Log:** `logs/audit.log`
```
2026-06-19 15:30:37 UTC [INFO] lawfullyillegal-droid EXECUTED nmap_scan on 192.168.1.105 [CASE:44]
2026-06-19 15:30:38 UTC [INFO] Evidence captured: evidence-20260619T153037Z-f1688e4b9a.txt [2847 bytes]
2026-06-19 15:30:39 UTC [INFO] Evidence synced to vault [commit: a7f3c9d]
```

**Log Format:**
- UTC timestamps (ISO 8601)
- Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Operator identifier
- Action taken
- Affected resources
- Case number (if applicable)
- Return code/result

**Log Rotation:**
- Max file size: 100MB
- Backup count: 10 files
- Rotation policy: Daily or size-based

---

### 7. Evidence Note Generator

**Location:** `/workspaces/travis-ops-center/scripts/gen_evidence_note.py`

**Function:**
- Convert raw evidence to human-readable markdown
- Extract key findings
- Generate summary timeline
- Cross-reference with case notes
- Create investigation narratives

**Output:** `evidence_notes/<evidence_id>.md`

**Process:**
1. Read evidence file and metadata
2. Parse command output
3. Identify key patterns/findings
4. Generate formatted markdown
5. Link to related evidence
6. Add analyst notes section

---

### 8. Vault Synchronization

**Location:** `/workspaces/travis-ops-center/scripts/sync_vault.sh`

**Purpose:**
- Version control for evidence files
- Immutable audit trail via git
- Evidence integrity verification
- Decentralized backup capability

**Operations:**
```bash
# Add new evidence to git
git add evidence/ data/

# Create timestamped commit
git commit -m "Evidence captured: Case #44 [2026-06-19 15:30]"

# Create evidence tags
git tag -a "case-44-evidence-20260619" -m "Case 44 evidence set"

# Verify integrity
git log --format="%H %s" | head -10

# Sync to remote
git push origin main
git push origin --tags
```

**Git Structure:**
```
.git/
├── objects/              # Compressed data
├── refs/
│   ├── heads/           # Branch references
│   └── tags/            # Evidence tags
└── logs/                # Git history
```

---

## Data Flow Diagram

```
User Request (Web UI)
        │
        ▼
┌──────────────────────────────────────┐
│  Flask Web Application               │
│  - Parse request                     │
│  - Validate input                    │
└──────────────────┬───────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ Command Center       │
        │ - Validate command   │
        │ - Check permissions  │
        │ - Set context        │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ Execute Command      │
        │ - Run process        │
        │ - Capture output     │
        │ - Record timing      │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ Evidence Ingest      │
        │ - Hash evidence      │
        │ - Create metadata    │
        │ - Write to disk      │
        └──────────┬───────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
    ┌─────────┐          ┌──────────────┐
    │ Audit   │          │ Evidence     │
    │ Logger  │          │ File         │
    └─────────┘          └──────┬───────┘
                                │
                    ┌───────────┴──────────┐
                    │                      │
                    ▼                      ▼
            ┌──────────────┐        ┌───────────────┐
            │ Git Vault    │        │ SQLite Index  │
            │ (persistent) │        │ (fast query)  │
            └──────────────┘        └───────────────┘
```

---

## Security Architecture

### Authentication
- Operator identifier required for all operations
- Web interface: Session-based (60-minute timeout)
- Command execution: Operator name in audit logs
- Case access: Case number verification

### Authorization
- Role-based command execution
- Permission checks before operation
- Blacklist prevents dangerous commands
- Timeout limits resource exhaustion

### Evidence Integrity
- SHA256 hashing on all evidence files
- Git commit SHAs for tamper detection
- Metadata includes integrity checksums
- Read-only evidence archive

### Audit Trail
- All operations logged with timestamps
- Immutable git-based history
- SQLite audit table for quick searches
- Logs retained per retention policy

---

## Deployment Model

### Single-Machine Deployment

```
┌─────────────────────────────┐
│ Travis Ops Center Container │
│                             │
│  Docker Container:          │
│  - Ubuntu 24.04 LTS         │
│  - Python 3.12              │
│  - Flask web server         │
│  - Git repository           │
│  - SQLite database          │
│                             │
│  Ports:                     │
│  - 5000 (Flask app)         │
│  - 22 (SSH - optional)      │
└─────────────────────────────┘
        │
        ▼
    Local Storage:
    - /workspaces/travis-ops-center/
      └── evidence/
      └── data/
      └── logs/
```

### Containerization

**Dockerfile:**
- Base: Ubuntu 24.04 LTS
- Dependencies: Python 3.12, nmap, git, curl, dig
- Working directory: /workspaces/travis-ops-center
- Entrypoint: Flask web server on 0.0.0.0:5000

**docker-compose.yml:**
- Single service (travis-ops-center)
- Volume mounts for persistence
- Environment variables from settings.yml
- Port exposure for web interface

---

## Performance Characteristics

### Command Execution
- Average latency: 100-500ms (network commands)
- Evidence file write: 10-50ms
- Audit log write: 5-20ms
- Git sync: 500ms-2s

### Storage
- Average evidence file: 2-10KB
- With compression: 500B-3KB
- Metadata overhead: ~200B per file
- SQLite index: 100B-500B per entry

### Concurrent Operations
- Max parallel commands: 5 (configurable)
- Session handling: 10 concurrent users
- Evidence capture: 100+ files per day
- Evidence retention: 365 days

---

## Failure Modes and Recovery

### Evidence Capture Failure
**Cause:** Disk full or permission denied
**Recovery:**
1. Check disk space
2. Verify directory permissions
3. Retry capture operation
4. Escalate if persistent

### Git Sync Failure
**Cause:** Network unavailable or merge conflict
**Recovery:**
1. Verify git status
2. Resolve merge conflicts
3. Retry sync operation
4. Escalate if network issue

### Database Lock
**Cause:** Concurrent access or process crash
**Recovery:**
1. Check for stale processes
2. Verify database integrity
3. Rebuild index if needed
4. Restart web service

---

## Future Enhancements

1. **Distributed Evidence Vault**
   - Multi-site evidence replication
   - Evidence API for integration

2. **Advanced Analytics**
   - Threat correlation engine
   - Pattern detection
   - Timeline visualization

3. **Machine Learning**
   - Anomaly detection in evidence
   - Automated finding classification
   - Incident severity prediction

4. **Integration Points**
   - SOAR platform connectivity
   - Ticketing system integration
   - Slack/Teams notifications
   - SIEMs data ingestion

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-19  
**Maintainer:** lawfullyillegal-droid  
**Next Review:** 2026-07-19
