window.app = {
  currentPanel: 'dashboard',

  init() {
    this.initNav();
    this.loadEvidence();
    this.loadCases();
    this.loadFeed();
    this.initTerminal();
    this.initGit();
  },

  initNav() {
    document.querySelectorAll('#main-nav button').forEach((btn) => {
      btn.addEventListener('click', () => {
        this.switchPanel(btn.dataset.panel);
      });
    });
  },

  switchPanel(name) {
    this.currentPanel = name;
    document.querySelectorAll('.panel').forEach((panel) => {
      panel.classList.toggle('active', panel.id === `panel-${name}`);
    });
    document.querySelectorAll('#main-nav button').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.panel === name);
    });
  },

  async loadEvidence() {
    try {
      const response = await fetch('/api/ledger');
      if (!response.ok) throw new Error('Unable to load evidence ledger');
      const entries = await response.json();
      const body = document.getElementById('evidence-table-body');
      body.innerHTML = '';

      if (entries.length === 0) {
        body.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#666; padding:2rem">No evidence entries found. Use Command Center to ingest files.</td></tr>';
      } else {
        entries.forEach((entry) => {
          const row = document.createElement('tr');
          row.innerHTML = `
            <td><a href="/evidence/${entry.id}">${entry.id}</a></td>
            <td>${entry.ts}</td>
            <td>${entry.sha256.slice(0, 16)}...</td>
            <td>${entry.filename}</td>
            <td>${entry.size}</td>
            <td>${entry.notes || ''}</td>
          `;
          body.appendChild(row);
        });
      }

      document.getElementById('stat-evidence').textContent = entries.length;
      document.getElementById('evidence-live').textContent = `${entries.length} Evidence Logged`;
    } catch (error) {
      console.error(error);
      alert('Unable to load evidence data. Make sure the backend is running.');
    }
  },

  loadCases() {
    const body = document.getElementById('cases-table-body');
    body.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center; color:#666; padding:2rem">No case files are connected yet. Use the evidence ledger and case notes to begin.</td>
      </tr>`;
    document.getElementById('stat-cases').textContent = '0';
  },

  loadFeed() {
    const feed = document.getElementById('operations-feed');
    feed.innerHTML = `
      <div class="feed-item priority-high">
        <div class="feed-meta">System • Now</div>
        <h4>Interactive command center ready</h4>
        <p>The public interface is connected to the backend ledger and audit routes.</p>
      </div>`;
    document.getElementById('stat-notices').textContent = '1';
  },

  ingestEvidence() {
    alert('Evidence ingestion requires the backend command-line tool.\nUse: python3 scripts/evidence_ingest.py /path/to/file --notes "description"');
  },

  runSync() {
    this.switchPanel('git');
    this.loadGit(false);
  },


  // CASEOPS_GIT_SYNC_V1
  async gitApi(path, payload) {
    const token = document.querySelector('meta[name="caseops-git-token"]')?.content || '';
    const options = payload === undefined ? {} : {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CaseOps-CSRF': token},
      body: JSON.stringify(payload),
    };
    const response = await fetch(path, {...options, credentials: 'same-origin'});
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || 'GitHub request failed');
    return body;
  },

  gitMessage(message) {
    document.getElementById('git-message').textContent = message;
  },

  async loadGit(fetchRemote = false) {
    const refresh = document.getElementById('git-refresh');
    const fetchButton = document.getElementById('git-fetch');
    const apply = document.getElementById('git-apply');
    [refresh, fetchButton, apply].forEach(btn => btn.disabled = true);
    this.gitMessage(fetchRemote ? 'Checking GitHub...' : 'Reading Git status...');
    try {
      const state = await this.gitApi(fetchRemote ? '/api/git/fetch' : '/api/git/status',
        fetchRemote ? {} : undefined);
      this.gitState = state;
      document.getElementById('git-branch').textContent = state.branch;
      document.getElementById('git-ahead').textContent = String(state.ahead);
      document.getElementById('git-behind').textContent = String(state.behind);
      document.getElementById('git-dirty').textContent = state.clean ? 'Clean' : String(state.local_change_count);
      const list = document.getElementById('git-incoming-list');
      list.replaceChildren();
      if (!state.incoming_files.length) {
        const li = document.createElement('li');
        li.textContent = 'No incoming file changes.';
        list.appendChild(li);
      } else {
        state.incoming_files.forEach(name => {
          const li = document.createElement('li');
          li.textContent = name;
          list.appendChild(li);
        });
      }
      this.gitMessage(`Local commit ${state.head.slice(0, 12)}. GitHub main ${state.remote.slice(0, 12)}. ${state.can_update ? 'Update available. Review the files before applying.' : 'No safe fast-forward update is available.'}`);
      apply.disabled = !state.can_update;
    } catch (error) {
      this.gitState = null;
      this.gitMessage(error.message);
    } finally {
      refresh.disabled = false;
      fetchButton.disabled = !document.querySelector('meta[name="caseops-git-token"]')?.content;
    }
  },

  async applyGitUpdate() {
    const state = this.gitState;
    if (!state?.can_update) return;
    const answer = window.prompt(`You are about to apply ${state.behind} incoming commit(s) to local CaseOps code.\nNo files will be pushed.\nType UPDATE to proceed:`);
    if (answer !== 'UPDATE') return;
    const apply = document.getElementById('git-apply');
    apply.disabled = true;
    this.gitMessage('Applying fast-forward update...');
    try {
      const result = await this.gitApi('/api/git/update', {head: state.head, remote: state.remote});
      this.gitMessage(result.message);
      this.gitState = null;
      await this.loadGit(false);
      this.gitMessage(result.message);
    } catch (error) {
      this.gitMessage(error.message);
    }
  },

  initGit() {
    document.getElementById('git-refresh')?.addEventListener('click', () => this.loadGit(false));
    document.getElementById('git-fetch')?.addEventListener('click', () => this.loadGit(true));
    document.getElementById('git-apply')?.addEventListener('click', () => this.applyGitUpdate());
  },

  initTerminal() {
    const input = document.getElementById('terminal-input');
    input.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter') return;
      const command = input.value.trim();
      input.value = '';
      if (!command) return;
      this.printTerminalLine(`$ ${command}`, 'cmd');
      this.processTerminalCommand(command);
    });
  },

  printTerminalLine(text, type = 'out') {
    const output = document.getElementById('terminal-output');
    const line = document.createElement('div');
    line.className = `line ${type}`;
    line.textContent = text;
    output.appendChild(line);
    output.scrollTop = output.scrollHeight;
  },

  processTerminalCommand(command) {
    const normalized = command.toLowerCase();
    if (normalized === 'help') {
      this.printTerminalLine('Available commands: help, ledger, audit, stats', 'out');
      return;
    }

    if (normalized === 'ledger') {
      this.printTerminalLine('Loading evidence ledger...', 'out');
      this.loadEvidence();
      this.switchPanel('evidence');
      return;
    }

    if (normalized === 'stats') {
      this.printTerminalLine(`Evidence items: ${document.getElementById('stat-evidence').textContent}`, 'out');
      this.printTerminalLine(`Cases: ${document.getElementById('stat-cases').textContent}`, 'out');
      this.printTerminalLine(`Audit feed: ${document.getElementById('stat-notices').textContent}`, 'out');
      return;
    }

    if (normalized === 'audit') {
      this.printTerminalLine('Audit view is available at /logs', 'out');
      window.location.href = '/logs';
      return;
    }

    this.printTerminalLine('Command not supported in browser UI. Use the repo CLI tools for actual ingestion and sync.', 'out');
  }
};

window.addEventListener('DOMContentLoaded', () => window.app.init());
