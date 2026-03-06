(() => {
  'use strict';

  /* ── helpers ─────────────────────────────────────────────── */

  const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  const tagHue = (tag) => {
    let h = 0;
    for (let i = 0; i < tag.length; i++) h = (h * 31 + tag.charCodeAt(i)) & 0xffffffff;
    return ((h % 360) + 360) % 360;
  };

  const nodeColor = (node) => {
    if (node.tags && node.tags.length) return `hsl(${tagHue(node.tags[0])},55%,50%)`;
    return cssVar('--graph-node') || '#0066cc';
  };

  let colorMode = 'type';

  const typeColors = {
    fleeting: cssVar('--graph-type-fleeting') || '#e8a838',
    literature: cssVar('--graph-type-literature') || '#5b98d2',
    permanent: cssVar('--graph-type-permanent') || '#6bb86b',
  };

  const maturityColors = {
    draft: cssVar('--graph-maturity-draft') || '#e06c75',
    developing: cssVar('--graph-maturity-developing') || '#e8a838',
    evergreen: cssVar('--graph-maturity-evergreen') || '#6bb86b',
  };

  const nodeColorByMode = (node) => {
    if (colorMode === 'type' && node.type) return typeColors[node.type] || cssVar('--graph-node') || '#0066cc';
    if (colorMode === 'maturity' && node.maturity) return maturityColors[node.maturity] || cssVar('--graph-node') || '#0066cc';
    return nodeColor(node);
  };

  /* ── force simulation ───────────────────────────────────── */

  const ForceGraph = (container, data, opts) => {
    opts = opts || {};
    const nodes = data.nodes;
    const edges = data.edges;
    const idMap = {};
    const currentId = opts.currentId || null;
    let W, H, dpr;

    const canvas = document.createElement('canvas');
    container.appendChild(canvas);
    const ctx = canvas.getContext('2d');

    const tooltip = document.createElement('div');
    tooltip.className = 'graph-tooltip';
    container.appendChild(tooltip);

    /* init node positions */
    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i];
      n.x = (Math.random() - 0.5) * 300;
      n.y = (Math.random() - 0.5) * 300;
      n.vx = 0;
      n.vy = 0;
      idMap[n.id] = n;
      n._visible = true;
      n._degree = 0;
    }

    /* resolve edge references */
    const resolvedEdges = [];
    for (let e = 0; e < edges.length; e++) {
      const src = idMap[edges[e].source];
      const tgt = idMap[edges[e].target];
      if (src && tgt) resolvedEdges.push({ source: src, target: tgt, type: edges[e].type || null });
    }

    /* compute degree */
    for (let e = 0; e < resolvedEdges.length; e++) {
      resolvedEdges[e].source._degree++;
      resolvedEdges[e].target._degree++;
    }

    /* camera */
    const cam = { x: 0, y: 0, zoom: 1 };
    let dragging = null;
    let panning = false;
    let panStart = { x: 0, y: 0, camX: 0, camY: 0 };
    let hovered = null;
    let onFocusCb = null;
    let navTimeout = null;

    /* event handlers (stored for cleanup) */
    const onMouseUp = (ev) => {
      if (dragging) {
        const rect = canvas.getBoundingClientRect();
        const sx = ev.clientX - rect.left;
        const sy = ev.clientY - rect.top;
        const hit = nodeAt(sx, sy);
        if (hit === dragging) {
          const moved = Math.abs(hit.vx) + Math.abs(hit.vy);
          if (moved < 0.1) {
            clearTimeout(navTimeout);
            const root = (typeof base_url !== 'undefined' && base_url) || '';
            navTimeout = setTimeout(() => { window.location.href = root + hit.url; }, 250);
          }
        }
        dragging = null;
      }
      panning = false;
    };

    /* sizing */
    const resize = () => {
      dpr = window.devicePixelRatio || 1;
      W = container.clientWidth;
      H = container.clientHeight;
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      canvas.style.width = `${W}px`;
      canvas.style.height = `${H}px`;
    };
    resize();
    window.addEventListener('resize', resize);

    /* coordinate transforms */
    const toScreen = (x, y) => ({
      x: (x - cam.x) * cam.zoom + W / 2,
      y: (y - cam.y) * cam.zoom + H / 2
    });
    const toWorld = (sx, sy) => ({
      x: (sx - W / 2) / cam.zoom + cam.x,
      y: (sy - H / 2) / cam.zoom + cam.y
    });

    /* physics */
    let alpha = 1;
    const REPULSION = 800;
    const ATTRACTION = 0.005;
    const CENTER_GRAVITY = 0.01;
    const DAMPING = 0.9;
    const NODE_RADIUS = 5;
    const BH_THETA = 0.5;

    /* Barnes-Hut quadtree for O(n log n) repulsion */
    const buildQuadtree = (pts) => {
      if (pts.length === 0) return null;
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i];
        if (p.x < minX) minX = p.x;
        if (p.y < minY) minY = p.y;
        if (p.x > maxX) maxX = p.x;
        if (p.y > maxY) maxY = p.y;
      }
      const pad = 1;
      const size = Math.max(maxX - minX, maxY - minY) + pad;
      const cx = (minX + maxX) / 2;
      const cy = (minY + maxY) / 2;
      const root = { cx, cy, size, mass: 0, comX: 0, comY: 0, body: null, children: null };
      for (let i = 0; i < pts.length; i++) insert(root, pts[i]);
      return root;
    };

    const insert = (quad, p) => {
      if (quad.mass === 0) {
        quad.body = p;
        quad.mass = 1;
        quad.comX = p.x;
        quad.comY = p.y;
        return;
      }
      if (quad.children === null) {
        quad.children = subdivide(quad);
        const old = quad.body;
        quad.body = null;
        insert(childFor(quad, old), old);
      }
      quad.comX = (quad.comX * quad.mass + p.x) / (quad.mass + 1);
      quad.comY = (quad.comY * quad.mass + p.y) / (quad.mass + 1);
      quad.mass += 1;
      insert(childFor(quad, p), p);
    };

    const subdivide = (q) => {
      const hs = q.size / 2;
      const qs = hs / 2;
      return [
        { cx: q.cx - qs, cy: q.cy - qs, size: hs, mass: 0, comX: 0, comY: 0, body: null, children: null },
        { cx: q.cx + qs, cy: q.cy - qs, size: hs, mass: 0, comX: 0, comY: 0, body: null, children: null },
        { cx: q.cx - qs, cy: q.cy + qs, size: hs, mass: 0, comX: 0, comY: 0, body: null, children: null },
        { cx: q.cx + qs, cy: q.cy + qs, size: hs, mass: 0, comX: 0, comY: 0, body: null, children: null },
      ];
    };

    const childFor = (quad, p) => {
      const i = (p.x > quad.cx ? 1 : 0) + (p.y > quad.cy ? 2 : 0);
      return quad.children[i];
    };

    const applyRepulsion = (node, quad) => {
      if (quad === null || quad.mass === 0) return;
      if (quad.body === node) return;
      const dx = node.x - quad.comX;
      const dy = node.y - quad.comY;
      const d2 = dx * dx + dy * dy || 1;
      if (quad.body !== null || quad.size * quad.size / d2 < BH_THETA * BH_THETA) {
        const f = REPULSION * quad.mass / d2;
        node.vx += dx * f;
        node.vy += dy * f;
        return;
      }
      for (let c = 0; c < 4; c++) applyRepulsion(node, quad.children[c]);
    };

    const tick = () => {
      if (alpha < 0.001) { alpha = 0; return; }
      alpha *= 0.995;

      const qt = buildQuadtree(nodes);
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        /* center gravity */
        a.vx -= a.x * CENTER_GRAVITY;
        a.vy -= a.y * CENTER_GRAVITY;

        /* repulsion (Barnes-Hut) */
        applyRepulsion(a, qt);
      }

      /* attraction along edges */
      for (let e = 0; e < resolvedEdges.length; e++) {
        const edge = resolvedEdges[e];
        const dx2 = edge.target.x - edge.source.x;
        const dy2 = edge.target.y - edge.source.y;
        const k = edge.type === 'sequence' ? ATTRACTION * 3 : ATTRACTION;
        edge.source.vx += dx2 * k;
        edge.source.vy += dy2 * k;
        edge.target.vx -= dx2 * k;
        edge.target.vy -= dy2 * k;
      }

      /* integrate */
      for (let k = 0; k < nodes.length; k++) {
        const n = nodes[k];
        if (n === dragging) continue;
        n.vx *= DAMPING;
        n.vy *= DAMPING;
        n.x += n.vx * alpha;
        n.y += n.vy * alpha;
      }
    };

    /* rendering */
    const draw = () => {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, W, H);

      const edgeColor = cssVar('--graph-edge') || '#ddd';
      const labelColor = cssVar('--graph-label') || '#333';
      const currentColor = cssVar('--graph-node-current') || '#333';

      /* edges */
      const seqColor = cssVar('--text-link') || '#0066cc';
      for (let e = 0; e < resolvedEdges.length; e++) {
        const edge = resolvedEdges[e];
        if (!edge.source._visible || !edge.target._visible) continue;
        const s = toScreen(edge.source.x, edge.source.y);
        const t = toScreen(edge.target.x, edge.target.y);
        const isSeq = edge.type === 'sequence';
        ctx.strokeStyle = isSeq ? seqColor : edgeColor;
        ctx.lineWidth = isSeq ? 1.5 : 0.5;
        ctx.globalAlpha = isSeq ? 0.7 : 0.4;
        if (isSeq) {
          ctx.setLineDash([4, 3]);
        } else {
          ctx.setLineDash([]);
        }
        ctx.beginPath();
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(t.x, t.y);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
      ctx.setLineDash([]);

      /* nodes */
      const r = NODE_RADIUS;
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        if (!n._visible) continue;
        const p = toScreen(n.x, n.y);
        const isCurrent = currentId && n.id === currentId;
        const isHovered = n === hovered;
        const degScale = Math.min(1 + n._degree * 0.15, 3);
        const baseR = r * degScale;
        const radius = isCurrent ? baseR * 1.5 : (isHovered ? baseR * 1.3 : baseR);

        ctx.beginPath();
        ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = isCurrent ? currentColor : nodeColorByMode(n);
        ctx.fill();

        /* MOC ring */
        if (n.role === 'moc') {
          ctx.beginPath();
          ctx.arc(p.x, p.y, radius + 2, 0, Math.PI * 2);
          ctx.strokeStyle = currentColor;
          ctx.lineWidth = 1.5;
          ctx.stroke();
        }

        /* label for hovered or current */
        if (isHovered || isCurrent) {
          const rootFontSize = parseFloat(getComputedStyle(document.documentElement).fontSize);
          ctx.font = `${rootFontSize * 0.75}px sans-serif`;
          ctx.fillStyle = labelColor;
          ctx.textAlign = 'center';
          ctx.fillText(n.title, p.x, p.y - radius - 4);
        }
      }
    };

    /* hit test */
    const nodeAt = (sx, sy) => {
      const w = toWorld(sx, sy);
      let best = null, bestD = Infinity;
      for (let i = 0; i < nodes.length; i++) {
        if (!nodes[i]._visible) continue;
        const dx = nodes[i].x - w.x;
        const dy = nodes[i].y - w.y;
        const d = Math.sqrt(dx * dx + dy * dy);
        const hitR = (NODE_RADIUS + 4) / cam.zoom;
        if (d < hitR && d < bestD) { best = nodes[i]; bestD = d; }
      }
      return best;
    };

    /* mouse events */
    canvas.addEventListener('mousedown', (ev) => {
      const rect = canvas.getBoundingClientRect();
      const sx = ev.clientX - rect.left;
      const sy = ev.clientY - rect.top;
      const hit = nodeAt(sx, sy);
      if (hit) {
        dragging = hit;
        alpha = Math.max(alpha, 0.3);
        ensureRunning();
      } else {
        panning = true;
        panStart = { x: ev.clientX, y: ev.clientY, camX: cam.x, camY: cam.y };
      }
    });

    canvas.addEventListener('mousemove', (ev) => {
      const rect = canvas.getBoundingClientRect();
      const sx = ev.clientX - rect.left;
      const sy = ev.clientY - rect.top;

      if (dragging) {
        const w = toWorld(sx, sy);
        dragging.x = w.x;
        dragging.y = w.y;
        dragging.vx = 0;
        dragging.vy = 0;
        alpha = Math.max(alpha, 0.3);
        ensureRunning();
      } else if (panning) {
        const dx = (ev.clientX - panStart.x) / cam.zoom;
        const dy = (ev.clientY - panStart.y) / cam.zoom;
        cam.x = panStart.camX - dx;
        cam.y = panStart.camY - dy;
        draw();
      } else {
        const hit = nodeAt(sx, sy);
        if (hit !== hovered) { hovered = hit; draw(); }
        canvas.style.cursor = hit ? 'pointer' : 'grab';
        if (hit) {
          tooltip.textContent = hit.title;
          tooltip.style.display = 'block';
          tooltip.style.left = `${sx + 12}px`;
          tooltip.style.top = `${sy - 8}px`;
        } else {
          tooltip.style.display = 'none';
        }
      }
    });

    window.addEventListener('mouseup', onMouseUp);

    canvas.addEventListener('wheel', (ev) => {
      ev.preventDefault();
      const factor = ev.deltaY < 0 ? 1.1 : 0.9;
      cam.zoom = Math.min(Math.max(cam.zoom * factor, 0.1), 10);
      draw();
    }, { passive: false });

    canvas.addEventListener('dblclick', (ev) => {
      ev.preventDefault();
      clearTimeout(navTimeout);
      const rect = canvas.getBoundingClientRect();
      const sx = ev.clientX - rect.left;
      const sy = ev.clientY - rect.top;
      const hit = nodeAt(sx, sy);
      if (hit && onFocusCb) onFocusCb(hit.id);
    });

    /* animation loop */
    let animId = null;
    const loop = () => {
      tick();
      draw();
      if (alpha > 0.001) {
        animId = requestAnimationFrame(loop);
      } else {
        animId = null;
      }
    };
    const ensureRunning = () => {
      if (!animId) loop();
    };

    /* auto-fit after simulation settles */
    const autoFit = () => {
      if (nodes.length === 0) return;
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      for (let i = 0; i < nodes.length; i++) {
        if (nodes[i].x < minX) minX = nodes[i].x;
        if (nodes[i].x > maxX) maxX = nodes[i].x;
        if (nodes[i].y < minY) minY = nodes[i].y;
        if (nodes[i].y > maxY) maxY = nodes[i].y;
      }
      cam.x = (minX + maxX) / 2;
      cam.y = (minY + maxY) / 2;
      const rangeX = (maxX - minX) || 100;
      const rangeY = (maxY - minY) || 100;
      cam.zoom = Math.min(W / (rangeX + 80), H / (rangeY + 80), 2);
    };

    /* pre-compute adjacency for BFS */
    const adjacency = buildAdjacency(resolvedEdges);

    /* run warmup then fit */
    for (let w = 0; w < 200; w++) tick();
    autoFit();
    loop();

    return {
      nodes,
      resolvedEdges,
      adjacency,
      draw,
      ensureRunning,
      setVisibility: (visibleIds) => {
        for (let i = 0; i < nodes.length; i++) {
          nodes[i]._visible = visibleIds === null || visibleIds.has(nodes[i].id);
        }
        draw();
      },
      centerOn: (nodeId) => {
        const node = idMap[nodeId];
        if (!node) return;
        cam.x = node.x;
        cam.y = node.y;
        cam.zoom = Math.max(cam.zoom, 1.5);
        draw();
      },
      idMap,
      setOnFocus: (cb) => { onFocusCb = cb; },
      destroy: () => {
        if (animId) { cancelAnimationFrame(animId); animId = null; }
        window.removeEventListener('resize', resize);
        window.removeEventListener('mouseup', onMouseUp);
        canvas.remove();
        tooltip.remove();
      },
    };
  };

  /* ── BFS ─────────────────────────────────────────────────── */

  const buildAdjacency = (edges) => {
    const adj = {};
    for (let e = 0; e < edges.length; e++) {
      const s = edges[e].source.id;
      const t = edges[e].target.id;
      (adj[s] || (adj[s] = [])).push(t);
      (adj[t] || (adj[t] = [])).push(s);
    }
    return adj;
  };

  const bfs = (startId, depth, adj) => {
    const visited = new Set();
    visited.add(startId);
    let frontier = [startId];
    for (let d = 0; d < depth; d++) {
      const next = [];
      for (let f = 0; f < frontier.length; f++) {
        const neighbors = adj[frontier[f]] || [];
        for (let n = 0; n < neighbors.length; n++) {
          if (!visited.has(neighbors[n])) {
            visited.add(neighbors[n]);
            next.push(neighbors[n]);
          }
        }
      }
      frontier = next;
    }
    return visited;
  };

  /* ── toolbar ──────────────────────────────────────────── */

  const buildToolbar = (graph, data) => {
    const toolbar = document.getElementById('graph-toolbar');
    if (!toolbar) return;

    /* collect unique values from data */
    const types = new Set();
    const maturities = new Set();
    const roles = new Set();
    const tagCounts = {};
    for (let i = 0; i < data.nodes.length; i++) {
      const n = data.nodes[i];
      types.add(n.type || 'unknown');
      maturities.add(n.maturity || 'unknown');
      roles.add(n.role || 'regular');
      const tags = n.tags || [];
      for (let t = 0; t < tags.length; t++) {
        tagCounts[tags[t]] = (tagCounts[tags[t]] || 0) + 1;
      }
    }
    const sortedTags = Object.keys(tagCounts).sort((a, b) => tagCounts[b] - tagCounts[a]);

    /* filter state — sets of CHECKED values (all checked = show all) */
    const checked = {
      types: new Set(types),
      maturities: new Set(maturities),
      roles: new Set(roles),
      tags: new Set(), /* empty = no tag filter */
      search: '',
      focusId: null,
      focusDepth: 2,
    };

    /* count display */
    const countEl = document.createElement('span');
    countEl.className = 'graph-node-count';
    const updateCount = () => {
      const vis = graph.nodes.filter(n => n._visible).length;
      countEl.textContent = vis + '/' + graph.nodes.length + ' notes';
    };

    /* ── apply all filters ─────────────────────────────── */
    const applyFilters = () => {
      let neighborSet = null;
      if (checked.focusId) {
        neighborSet = bfs(checked.focusId, checked.focusDepth, graph.adjacency);
      }
      const visibleIds = new Set();
      for (let i = 0; i < graph.nodes.length; i++) {
        const n = graph.nodes[i];
        if (neighborSet && !neighborSet.has(n.id)) continue;
        if (checked.search && !n.title.toLowerCase().includes(checked.search)) continue;
        const nType = n.type || 'unknown';
        const nMat = n.maturity || 'unknown';
        const nRole = n.role || 'regular';
        if (types.size > 0 && !checked.types.has(nType)) continue;
        if (maturities.size > 0 && !checked.maturities.has(nMat)) continue;
        if (roles.size > 0 && !checked.roles.has(nRole)) continue;
        if (checked.tags.size > 0) {
          const nTags = n.tags || [];
          if (!nTags.some(t => checked.tags.has(t))) continue;
        }
        visibleIds.add(n.id);
      }
      graph.setVisibility(visibleIds.size === graph.nodes.length ? null : visibleIds);
      updateCount();
    };

    /* ── checkbox group builder ────────────────────────── */
    const makeCheckboxGroup = (label, values, checkedSet) => {
      if (values.size === 0) return null;
      const group = document.createElement('div');
      group.className = 'graph-filter-group';
      const lbl = document.createElement('span');
      lbl.className = 'graph-filter-label';
      lbl.textContent = label;
      group.appendChild(lbl);
      const sorted = Array.from(values).sort();
      for (let i = 0; i < sorted.length; i++) {
        const val = sorted[i];
        const lb = document.createElement('label');
        const cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.checked = true;
        cb.addEventListener('change', () => {
          if (cb.checked) checkedSet.add(val); else checkedSet.delete(val);
          applyFilters();
        });
        lb.appendChild(cb);
        lb.appendChild(document.createTextNode(' ' + val));
        group.appendChild(lb);
      }
      return group;
    };

    const sep = () => { const d = document.createElement('div'); d.className = 'graph-toolbar-sep'; return d; };

    /* ── build groups ──────────────────────────────────── */
    const typeGroup = makeCheckboxGroup('Type', types, checked.types);
    const matGroup = makeCheckboxGroup('Maturity', maturities, checked.maturities);
    const roleGroup = makeCheckboxGroup('Role', roles, checked.roles);

    if (typeGroup) { toolbar.appendChild(typeGroup); toolbar.appendChild(sep()); }
    if (matGroup) { toolbar.appendChild(matGroup); toolbar.appendChild(sep()); }
    if (roleGroup) { toolbar.appendChild(roleGroup); toolbar.appendChild(sep()); }

    /* ── tag pills ───────────────────────────────────────── */
    if (sortedTags.length > 0) {
      const tagGroup = document.createElement('div');
      tagGroup.className = 'graph-filter-group';
      const tagLabel = document.createElement('span');
      tagLabel.className = 'graph-filter-label';
      tagLabel.textContent = 'Tags';
      tagGroup.appendChild(tagLabel);
      const tagScroll = document.createElement('div');
      tagScroll.className = 'graph-tag-scroll';
      for (let i = 0; i < sortedTags.length; i++) {
        const tag = sortedTags[i];
        const pill = document.createElement('span');
        pill.className = 'graph-tag-pill';
        pill.textContent = '#' + tag;
        pill.addEventListener('click', () => {
          if (checked.tags.has(tag)) {
            checked.tags.delete(tag);
            pill.classList.remove('active');
          } else {
            checked.tags.add(tag);
            pill.classList.add('active');
          }
          applyFilters();
        });
        tagScroll.appendChild(pill);
      }
      tagGroup.appendChild(tagScroll);
      toolbar.appendChild(tagGroup);
      toolbar.appendChild(sep());
    }

    /* ── search ──────────────────────────────────────────── */
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.id = 'graph-search';
    searchInput.placeholder = 'Search notes\u2026';
    let searchTimeout = null;
    searchInput.addEventListener('input', () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        checked.search = searchInput.value.trim().toLowerCase();
        applyFilters();
        if (checked.search) {
          const match = graph.nodes.find(n => n._visible);
          if (match) graph.centerOn(match.id);
        }
      }, 200);
    });
    toolbar.appendChild(searchInput);
    toolbar.appendChild(sep());

    /* ── neighborhood focus ──────────────────────────────── */
    const neighGroup = document.createElement('div');
    neighGroup.className = 'graph-neighborhood';
    const depthLabel = document.createElement('label');
    depthLabel.textContent = 'Depth ';
    const depthSlider = document.createElement('input');
    depthSlider.type = 'range';
    depthSlider.min = '1';
    depthSlider.max = '5';
    depthSlider.value = '2';
    depthSlider.addEventListener('input', () => {
      checked.focusDepth = parseInt(depthSlider.value, 10);
      if (checked.focusId) applyFilters();
    });
    depthLabel.appendChild(depthSlider);
    neighGroup.appendChild(depthLabel);

    const clearBtn = document.createElement('button');
    clearBtn.id = 'graph-clear-focus';
    clearBtn.textContent = 'Clear focus';
    clearBtn.style.display = 'none';
    clearBtn.addEventListener('click', () => {
      checked.focusId = null;
      clearBtn.style.display = 'none';
      applyFilters();
    });
    neighGroup.appendChild(clearBtn);
    toolbar.appendChild(neighGroup);
    toolbar.appendChild(sep());

    /* ── color mode ──────────────────────────────────────── */
    const colorGroup = document.createElement('div');
    colorGroup.className = 'graph-color-mode';
    const colorLabel = document.createElement('span');
    colorLabel.className = 'graph-filter-label';
    colorLabel.textContent = 'Color';
    colorGroup.appendChild(colorLabel);
    const colorSelect = document.createElement('select');
    const modes = [['type', 'By type'], ['maturity', 'By maturity'], ['tag', 'By tag']];
    for (let i = 0; i < modes.length; i++) {
      const opt = document.createElement('option');
      opt.value = modes[i][0];
      opt.textContent = modes[i][1];
      colorSelect.appendChild(opt);
    }
    colorSelect.addEventListener('change', () => {
      colorMode = colorSelect.value;
      graph.draw();
    });
    colorGroup.appendChild(colorSelect);
    toolbar.appendChild(colorGroup);
    toolbar.appendChild(sep());

    toolbar.appendChild(countEl);
    updateCount();

    return { checked, applyFilters };
  };

  /* ── init ────────────────────────────────────────────────── */

  const initGraph = (container, opts) => {
    const url = container.getAttribute('data-graph-url');
    if (!url) return;

    fetch(url).then((res) => {
      if (!res.ok) return;
      return res.json();
    }).then((data) => {
      if (!data || !Array.isArray(data.nodes) || !Array.isArray(data.edges)) return;
      if (opts && opts.currentId) {
        data = filterNeighborhood(data, opts.currentId);
      }

      container.setAttribute('data-node-count', data.nodes.length);
      const graph = ForceGraph(container, data, opts);

      if (container.id === 'graph-container') {
        const toolbarState = buildToolbar(graph, data);
        if (toolbarState) {
          graph.setOnFocus((nodeId) => {
            toolbarState.checked.focusId = nodeId;
            const clearBtn = document.getElementById('graph-clear-focus');
            if (clearBtn) clearBtn.style.display = '';
            toolbarState.applyFilters();
            graph.centerOn(nodeId);
          });
        }
      }
    }).catch(() => {
      container.textContent = 'Failed to load graph data.';
    });
  };

  const filterNeighborhood = (data, centerId) => {
    const neighborIds = {};
    neighborIds[centerId] = true;
    for (let i = 0; i < data.edges.length; i++) {
      const e = data.edges[i];
      if (e.source === centerId) neighborIds[e.target] = true;
      if (e.target === centerId) neighborIds[e.source] = true;
    }
    const nodes = data.nodes.filter((n) => neighborIds[n.id]);
    const edges = data.edges.filter((e) => neighborIds[e.source] && neighborIds[e.target]);
    return { nodes, edges };
  };

  /* ── page init ──────────────────────────────────────────── */

  const init = () => {
    /* full graph page */
    const full = document.getElementById('graph-container');
    if (full && full.getAttribute('data-graph-url')) {
      initGraph(full, {});
    }

    /* local graph on zettel pages */
    const local = document.getElementById('local-graph-container');
    if (local && local.getAttribute('data-graph-url')) {
      const zettelId = local.getAttribute('data-zettel-id');
      if (zettelId) initGraph(local, { currentId: zettelId });
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
