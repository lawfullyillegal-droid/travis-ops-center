# Travis Ops Center - Operations Manual

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Evidence Capture Workflow](#evidence-capture-workflow)
4. [Command Execution](#command-execution)
5. [Case Management](#case-management)
6. [Security Procedures](#security-procedures)
7. [Troubleshooting](#troubleshooting)
8. [Incident Response Checklist](#incident-response-checklist)

---

## Overview

Travis Ops Center is an integrated incident response and forensic evidence management platform designed for rapid threat investigation and command execution in security operations. The system provides centralized evidence capture, command vault execution, and case management capabilities.

**Key Capabilities:**
- Automated evidence collection and timestamping
- Real-time command execution with audit logging
- Case-based investigation tracking
- Git-based evidence vault for version control
- Web dashboard for operations monitoring
- Comprehensive audit trails

---

## System Architecture

### Core Components

1. **Command Center (`scripts/command_center.py`)**
   - Central orchestration engine
   - Command execution interface
   - Evidence collection coordinator
   - Case file management

2. **Web Interface (`web/app.py`)**
   - Flask-based operations dashboard
   - Real-time evidence viewer
   - Command execution interface
   - Case management UI

3. **Evidence Management**
   - Atomic evidence file creation with unique IDs
   - Metadata tracking (timestamps, operators, case numbers)
   - Automatic git synchronization
   - Archive and retention management

4. **Command Vault (`config/commands.yml`)**
   - 30+ pre-configured reconnaissance commands
   - Network, system, web, container, and OSINT tools
   - Role-based execution permissions
   - Timeout and resource management

### Directory Structure

```
/workspaces/travis-ops-center/
├── config/
│   ├── commands.yml          # Command vault
│   ├── settings.yml          # System configuration
│   └── blacklist.txt         # Forbidden commands
├── data/
│   ├── targets.json          # Investigation targets
│   ├── case_notes.md         # Case documentation
│   └── evidence.db           # Evidence index database
├── evidence/                 # Evidence files organized by date
├── logs/
│   └── audit.log            # Audit trail
├── scripts/
│   ├── command_center.py    # Main orchestrator
│   ├── evidence_ingest.py   # Evidence processor
│   ├── gen_evidence_note.py # Evidence note generator
│   └── audit_logger.py      # Audit logging system
├── web/
│   ├── app.py               # Flask application
│   ├── static/              # Frontend assets
│   └── templates/           # HTML templates
└── frontend/                # Alternative dashboard
```

---

## Evidence Capture Workflow

### SOP: Evidence Capture Procedure

**Purpose:** Ensure consistent, legally-sound evidence collection with proper chain of custody.

**Prerequisites:**
- Operator credentials verified
- Case number assigned
- Target system identified
- Legal authorization confirmed

### Step 1: Case Initialization
```bash
python3 scripts/command_center.py --init-case --case-number 44 --operator "lawfullyillegal-droid"
```

**Actions:**
- Create case directory in `data/`
- Initialize metadata files
- Create case evidence subdirectory
- Log initialization event to audit trail

### Step 2: Target Identification
```bash
python3 scripts/command_center.py --add-target --case 44 --type ip_address --value 192.168.1.105
```

**Actions:**
- Add target to targets.json
- Generate target documentation
- Create evidence collection plan
- Schedule baseline scan

### Step 3: Command Execution
```bash
python3 scripts/command_center.py --execute --command nmap_scan --target 192.168.1.105 --case 44
```

**Procedure:**
1. Validate command against whitelist
2. Check operator permissions
3. Set execution timeout (300s default)
4. Capture full stdout/stderr
5. Record execution metadata:
   - Operator name
   - Timestamp (UTC)
   - Command arguments
   - Return code
   - Execution duration

### Step 4: Evidence File Creation
```
evidence/20260619/
├── evidence-20260619T153037Z-f1688e4b9a.txt
├── evidence-20260619T153037Z-f1688e4b9a.txt.meta.json
└── evidence-20260619T153037Z-f1688e4b9a.txt.asc
```

**File Contents:**
- Command output (stdout)
- System information (OS, hostname)
- Execution context
- Timestamps with timezone
- Operator identifier

**Metadata (`*.meta.json`):**
```json
{
  "case_number": 44,
  "evidence_id": "evidence-20260619T153037Z-f1688e4b9a",
  "timestamp": "2026-06-19T15:30:37Z",
  "operator": "lawfullyillegal-droid",
  "command_id": "nmap_scan",
  "target": "192.168.1.105",
  "hash_sha256": "...",
  "file_size_bytes": 2847,
  "status": "captured"
}
```

### Step 5: Vault Synchronization
```bash
scripts/sync_vault.sh
```

**Actions:**
1. Add evidence to git
2. Commit with timestamped message
3. Create annotated tag for case
4. Verify integrity hash
5. Log sync event

### Step 6: Evidence Note Generation
```bash
python3 scripts/gen_evidence_note.py --evidence evidence-20260619T153037Z-f1688e4b9a
```

**Output:**
- Human-readable summary in `evidence_notes/`
- Key findings highlighted
- Timeline integration
- Cross-reference with case_notes.md

---

## Command Execution

### Safe Command Execution Checklist

Before executing any command:

- [ ] Command exists in `config/commands.yml`
- [ ] Command is NOT in `config/blacklist.txt`
- [ ] Operator has required permissions
- [ ] Target is authorized for investigation
- [ ] Execution will not harm system stability
- [ ] Command timeout is appropriate
- [ ] Evidence directory is writable

### Command Categories

**Network Reconnaissance (11 commands)**
- `nmap_scan` - Basic network scan
- `nmap_aggressive` - Full enumeration
- `whois_lookup` - WHOIS queries
- `dns_dig` - DNS resolution
- `ping_target` - ICMP connectivity
- `traceroute_path` - Route tracing

**Web Application Testing (3 commands)**
- `curl_headers` - HTTP headers
- `curl_body` - Response body capture
- `gobuster_dir` - Directory enumeration

**System Analysis (6 commands)**
- `netstat_all` - Network statistics
- `process_list` - Running processes
- `disk_usage` - Storage analysis
- `open_files` - File descriptor analysis

**Version Control (3 commands)**
- `git_log_history` - Commit history
- `git_contributors` - Contribution analysis
- `git_diff_recent` - Recent changes

**Container Operations (3 commands)**
- `docker_running` - Container status
- `docker_images_list` - Image inventory
- `docker_logs_view` - Log retrieval

**OSINT (2 commands)**
- `sherlock_username` - Social media search
- `harvester_emails` - Subdomain/email harvesting

---

## Case Management

### Creating a New Investigation

1. **Initialize case:**
   ```bash
   python3 scripts/command_center.py --init-case --case-number 45
   ```

2. **Document incident:**
   ```bash
   cat > data/case_notes_45.md << EOF
   # Case #45: [Incident Title]
   
   ## Timeline
   ...
   EOF
   ```

3. **Add investigation targets:**
   ```json
   {
     "id": "target_001",
     "case_number": 45,
     "type": "ip_address",
     "target_value": "10.0.0.50"
   }
   ```

4. **Execute investigation commands**
5. **Generate evidence notes**
6. **Close case when complete:**
   ```bash
   python3 scripts/command_center.py --close-case --case-number 45 --status RESOLVED
   ```

### Case Status Lifecycle

- **OPEN** - Active investigation
- **SUSPENDED** - Awaiting additional information
- **RESOLVED** - Investigation complete
- **ARCHIVED** - Closed and retained per policy

---

## Security Procedures

### Access Control
- All commands logged with operator identifier
- Audit trail immutable (git-backed)
- Sensitive data redacted from evidence notes
- Case access restricted by permission level

### Evidence Integrity
- SHA256 hash verification on all files
- Digital signatures for authenticated evidence
- Git commit SHAs for tamper detection
- Metadata includes integrity checksums

### Operational Security
- All commands executed in isolated environment
- Network commands use timeout limits
- Resource limits enforced (CPU, memory, disk)
- Suspicious commands require confirmation

### Compliance
- Evidence retention per `config/settings.yml` (90 days)
- Automatic archival of closed cases
- Audit logs retained for legal holds
- Compliance reporting available on demand

---

## Troubleshooting

### Evidence Not Being Captured
**Symptom:** Command executes but no evidence file created

**Diagnosis:**
1. Check evidence directory permissions: `ls -la evidence/`
2. Verify disk space: `df -h`
3. Check logs: `tail -100 logs/audit.log`

**Solution:**
```bash
mkdir -p evidence/$(date +%Y%m%d)
chmod 755 evidence/$(date +%Y%m%d)
python3 scripts/command_center.py --retry-evidence
```

### Command Execution Timeout
**Symptom:** Command times out with "execution exceeded limit"

**Resolution:**
- Increase timeout in `config/commands.yml`
- Break large commands into smaller chunks
- Execute during off-peak hours
- Check system resource usage

### Git Sync Failures
**Symptom:** `sync_vault.sh` exits with error

**Diagnosis:**
```bash
cd /workspaces/travis-ops-center
git status
git log --oneline | head -5
```

**Resolution:**
```bash
git fetch origin
git merge origin/main
scripts/sync_vault.sh --force
```

---

## Incident Response Checklist

Use this checklist for rapid incident response:

### Activation Phase (0-30 min)
- [ ] Create new case
- [ ] Assign lead investigator
- [ ] Identify affected systems
- [ ] Add targets to `data/targets.json`
- [ ] Begin evidence capture

### Investigation Phase (30 min - 4 hours)
- [ ] Execute network reconnaissance
- [ ] Analyze process listings
- [ ] Review network connections
- [ ] Examine disk usage
- [ ] Check git logs for code changes
- [ ] Generate evidence notes

### Analysis Phase (4-24 hours)
- [ ] Correlate findings across evidence
- [ ] Identify attack timeline
- [ ] Determine data exfiltration scope
- [ ] Document threat actor techniques
- [ ] Generate forensic report

### Response Phase (24+ hours)
- [ ] Brief incident stakeholders
- [ ] Execute remediation measures
- [ ] Implement detection improvements
- [ ] Archive case documentation
- [ ] Conduct lessons-learned session

---

## Contact and Support

**On-Call Investigator:** lawfullyillegal-droid  
**Emergency Escalation:** SOC Manager  
**Documentation Updates:** See `docs/ARCHITECTURE.md`

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-19  
**Next Review:** 2026-07-19
