(() => {
  const app = window.app;
  if (!app) return;

  function addCell(row, value) {
    const cell = document.createElement('td');
    cell.textContent = value ?? '';
    row.appendChild(cell);
  }

  function renderMessages(containerId, items, emptyText) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.textContent = '';

    if (!Array.isArray(items) || items.length === 0) {
      const item = document.createElement('div');
      item.className = 'feed-item priority-low';

      const text = document.createElement('p');
      text.textContent = emptyText;

      item.appendChild(text);
      container.appendChild(item);
      return;
    }

    items.forEach((message) => {
      const item = document.createElement('div');
      item.className = 'feed-item priority-low';

      const text = document.createElement('p');
      text.textContent = message;

      item.appendChild(text);
      container.appendChild(item);
    });
  }

  app.loadCases = async function () {
    const body = document.getElementById('cases-table-body');

    try {
      const response = await fetch('/api/review-data');
      if (!response.ok) {
        throw new Error('Unable to load case review data');
      }

      const data = await response.json();
      const cases = Array.isArray(data.cases) ? data.cases : [];

      body.textContent = '';

      if (cases.length === 0) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 6;
        cell.textContent = 'No case records connected.';
        row.appendChild(cell);
        body.appendChild(row);
      } else {
        cases.forEach((entry) => {
          const row = document.createElement('tr');

          addCell(row, entry.id);
          addCell(row, entry.label);
          addCell(row, entry.status);
          addCell(row, '—');
          addCell(row, '—');
          addCell(row, 'Tracked');

          body.appendChild(row);
        });
      }

      document.getElementById('stat-cases').textContent = cases.length;
      document.getElementById('cases-live').textContent =
        `${cases.length} Cases Tracked`;

    } catch (error) {
      console.error(error);
      body.innerHTML =
        '<tr><td colspan="6">Unable to load case data.</td></tr>';
    }
  };

  app.loadFeed = async function () {
    const feed = document.getElementById('operations-feed');

    try {
      const response = await fetch('/api/review-data');
      if (!response.ok) throw new Error('Unable to load timeline');

      const data = await response.json();
      const timeline = Array.isArray(data.timeline) ? data.timeline : [];

      feed.textContent = '';

      if (timeline.length === 0) {
        const item = document.createElement('div');
        item.className = 'feed-item priority-low';
        item.textContent = 'No timeline events available.';
        feed.appendChild(item);
        return;
      }

      [...timeline].reverse().forEach((entry) => {
        const item = document.createElement('div');
        item.className = 'feed-item priority-low';

        const meta = document.createElement('div');
        meta.className = 'feed-meta';
        meta.textContent = entry.date || 'Undated';

        const title = document.createElement('h4');
        title.textContent = 'CaseOps Timeline';

        const text = document.createElement('p');
        text.textContent = entry.event || '';

        item.appendChild(meta);
        item.appendChild(title);
        item.appendChild(text);
        feed.appendChild(item);
      });

    } catch (error) {
      console.error(error);
      feed.textContent = 'Unable to load operations timeline.';
    }
  };

  app.loadIntelligence = async function () {
    try {
      const [reviewResponse, intelResponse] = await Promise.all([
        fetch('/api/review-data'),
        fetch('/api/identifier-summary')
      ]);

      const review = await reviewResponse.json();
      const intel = await intelResponse.json();

      const counts = intel.counts || {};
      const verifiedEdges = Array.isArray(review.verified_edges)
        ? review.verified_edges
        : [];

      document.getElementById('intel-identifiers').textContent =
        counts.identifiers || 0;

      document.getElementById('intel-entities').textContent =
        counts.entities || 0;

      document.getElementById('intel-snapshots').textContent =
        counts.source_snapshots || 0;

      document.getElementById('intel-links').textContent =
        counts.links || 0;

      document.getElementById('intel-db-status').textContent =
        intel.status === 'ready'
          ? 'Identifier database online'
          : 'Database not initialized';

      // Main dashboard counters.
      document.getElementById('stat-audit').textContent =
        counts.identifiers || 0;

      document.getElementById('stat-notices').textContent =
        verifiedEdges.length;

      const body = document.getElementById('intel-links-body');
      body.textContent = '';

      if (verifiedEdges.length === 0) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 4;
        cell.textContent = 'No verified relationships recorded.';
        row.appendChild(cell);
        body.appendChild(row);
      } else {
        verifiedEdges.forEach((edge) => {
          const row = document.createElement('tr');

          addCell(row, edge.from);
          addCell(row, edge.relation);
          addCell(row, edge.to);
          addCell(row, edge.scope);

          body.appendChild(row);
        });
      }

      renderMessages(
        'intel-open-questions',
        review.open_questions,
        'No open evidentiary questions.'
      );

      renderMessages(
        'intel-limits',
        review.limits,
        'No analysis guardrails recorded.'
      );

    } catch (error) {
      console.error(error);

      const status = document.getElementById('intel-db-status');
      if (status) status.textContent = 'Intelligence API unavailable';
    }
  };

  const originalInit = app.init.bind(app);

  app.init = function () {
    originalInit();
    this.loadIntelligence();
  };

  const originalTerminalCommand =
    app.processTerminalCommand.bind(app);

  app.processTerminalCommand = function (command) {
    const normalized = command.toLowerCase().trim();

    if (normalized === 'intel' || normalized === 'intelligence') {
      this.printTerminalLine(
        'Loading identifier intelligence...',
        'out'
      );

      this.loadIntelligence();
      this.switchPanel('intelligence');
      return;
    }

    if (normalized === 'help') {
      this.printTerminalLine(
        'Available commands: help, ledger, audit, stats, intel',
        'out'
      );
      return;
    }

    originalTerminalCommand(command);
  };
})();
