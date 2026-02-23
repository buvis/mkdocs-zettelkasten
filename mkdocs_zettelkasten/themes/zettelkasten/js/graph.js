(function () {
  'use strict';

  /* ── helpers ─────────────────────────────────────────────── */

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function tagHue(tag) {
    var h = 0;
    for (var i = 0; i < tag.length; i++) h = (h * 31 + tag.charCodeAt(i)) & 0xffffffff;
    return ((h % 360) + 360) % 360;
  }

  function nodeColor(node) {
    if (node.tags && node.tags.length) return 'hsl(' + tagHue(node.tags[0]) + ',55%,50%)';
    return cssVar('--graph-node') || '#0066cc';
  }

  /* ── force simulation ───────────────────────────────────── */

  function ForceGraph(container, data, opts) {
    opts = opts || {};
    var nodes = data.nodes;
    var edges = data.edges;
    var idMap = {};
    var currentId = opts.currentId || null;
    var W, H, dpr;

    var canvas = document.createElement('canvas');
    container.appendChild(canvas);
    var ctx = canvas.getContext('2d');

    var tooltip = document.createElement('div');
    tooltip.className = 'graph-tooltip';
    container.appendChild(tooltip);

    /* init node positions */
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      n.x = (Math.random() - 0.5) * 300;
      n.y = (Math.random() - 0.5) * 300;
      n.vx = 0;
      n.vy = 0;
      idMap[n.id] = n;
    }

    /* resolve edge references */
    var resolvedEdges = [];
    for (var e = 0; e < edges.length; e++) {
      var src = idMap[edges[e].source];
      var tgt = idMap[edges[e].target];
      if (src && tgt) resolvedEdges.push({ source: src, target: tgt });
    }

    /* camera */
    var cam = { x: 0, y: 0, zoom: 1 };
    var dragging = null;
    var panning = false;
    var panStart = { x: 0, y: 0, camX: 0, camY: 0 };
    var hovered = null;

    /* sizing */
    function resize() {
      dpr = window.devicePixelRatio || 1;
      W = container.clientWidth;
      H = container.clientHeight;
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      canvas.style.width = W + 'px';
      canvas.style.height = H + 'px';
    }
    resize();
    window.addEventListener('resize', resize);

    /* coordinate transforms */
    function toScreen(x, y) {
      return {
        x: (x - cam.x) * cam.zoom + W / 2,
        y: (y - cam.y) * cam.zoom + H / 2
      };
    }
    function toWorld(sx, sy) {
      return {
        x: (sx - W / 2) / cam.zoom + cam.x,
        y: (sy - H / 2) / cam.zoom + cam.y
      };
    }

    /* physics */
    var alpha = 1;
    var REPULSION = 800;
    var ATTRACTION = 0.005;
    var CENTER_GRAVITY = 0.01;
    var DAMPING = 0.9;
    var NODE_RADIUS = 5;

    function tick() {
      if (alpha < 0.001) { alpha = 0; return; }
      alpha *= 0.995;

      for (var i = 0; i < nodes.length; i++) {
        var a = nodes[i];
        /* center gravity */
        a.vx -= a.x * CENTER_GRAVITY;
        a.vy -= a.y * CENTER_GRAVITY;

        /* repulsion */
        for (var j = i + 1; j < nodes.length; j++) {
          var b = nodes[j];
          var dx = a.x - b.x;
          var dy = a.y - b.y;
          var d2 = dx * dx + dy * dy || 1;
          var f = REPULSION / d2;
          a.vx += dx * f;
          a.vy += dy * f;
          b.vx -= dx * f;
          b.vy -= dy * f;
        }
      }

      /* attraction along edges */
      for (var e = 0; e < resolvedEdges.length; e++) {
        var edge = resolvedEdges[e];
        var dx2 = edge.target.x - edge.source.x;
        var dy2 = edge.target.y - edge.source.y;
        edge.source.vx += dx2 * ATTRACTION;
        edge.source.vy += dy2 * ATTRACTION;
        edge.target.vx -= dx2 * ATTRACTION;
        edge.target.vy -= dy2 * ATTRACTION;
      }

      /* integrate */
      for (var k = 0; k < nodes.length; k++) {
        var n = nodes[k];
        if (n === dragging) continue;
        n.vx *= DAMPING;
        n.vy *= DAMPING;
        n.x += n.vx * alpha;
        n.y += n.vy * alpha;
      }
    }

    /* rendering */
    function draw() {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, W, H);

      var edgeColor = cssVar('--graph-edge') || '#ddd';
      var labelColor = cssVar('--graph-label') || '#333';
      var currentColor = cssVar('--graph-node-current') || '#333';

      /* edges */
      ctx.strokeStyle = edgeColor;
      ctx.lineWidth = 0.5;
      ctx.globalAlpha = 0.4;
      for (var e = 0; e < resolvedEdges.length; e++) {
        var s = toScreen(resolvedEdges[e].source.x, resolvedEdges[e].source.y);
        var t = toScreen(resolvedEdges[e].target.x, resolvedEdges[e].target.y);
        ctx.beginPath();
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(t.x, t.y);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;

      /* nodes */
      var r = NODE_RADIUS;
      for (var i = 0; i < nodes.length; i++) {
        var n = nodes[i];
        var p = toScreen(n.x, n.y);
        var isCurrent = currentId && n.id === currentId;
        var isHovered = n === hovered;
        var radius = isCurrent ? r * 1.8 : (isHovered ? r * 1.4 : r);

        ctx.beginPath();
        ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = isCurrent ? currentColor : nodeColor(n);
        ctx.fill();

        /* label for hovered or current */
        if (isHovered || isCurrent) {
          ctx.font = '12px sans-serif';
          ctx.fillStyle = labelColor;
          ctx.textAlign = 'center';
          ctx.fillText(n.title, p.x, p.y - radius - 4);
        }
      }
    }

    /* hit test */
    function nodeAt(sx, sy) {
      var w = toWorld(sx, sy);
      var best = null, bestD = Infinity;
      for (var i = 0; i < nodes.length; i++) {
        var dx = nodes[i].x - w.x;
        var dy = nodes[i].y - w.y;
        var d = Math.sqrt(dx * dx + dy * dy);
        var hitR = (NODE_RADIUS + 4) / cam.zoom;
        if (d < hitR && d < bestD) { best = nodes[i]; bestD = d; }
      }
      return best;
    }

    /* mouse events */
    canvas.addEventListener('mousedown', function (ev) {
      var rect = canvas.getBoundingClientRect();
      var sx = ev.clientX - rect.left;
      var sy = ev.clientY - rect.top;
      var hit = nodeAt(sx, sy);
      if (hit) {
        dragging = hit;
        alpha = Math.max(alpha, 0.3);
        ensureRunning();
      } else {
        panning = true;
        panStart = { x: ev.clientX, y: ev.clientY, camX: cam.x, camY: cam.y };
      }
    });

    canvas.addEventListener('mousemove', function (ev) {
      var rect = canvas.getBoundingClientRect();
      var sx = ev.clientX - rect.left;
      var sy = ev.clientY - rect.top;

      if (dragging) {
        var w = toWorld(sx, sy);
        dragging.x = w.x;
        dragging.y = w.y;
        dragging.vx = 0;
        dragging.vy = 0;
        alpha = Math.max(alpha, 0.3);
        ensureRunning();
      } else if (panning) {
        var dx = (ev.clientX - panStart.x) / cam.zoom;
        var dy = (ev.clientY - panStart.y) / cam.zoom;
        cam.x = panStart.camX - dx;
        cam.y = panStart.camY - dy;
        draw();
      } else {
        var hit = nodeAt(sx, sy);
        if (hit !== hovered) { hovered = hit; draw(); }
        canvas.style.cursor = hit ? 'pointer' : 'grab';
        if (hit) {
          tooltip.textContent = hit.title;
          tooltip.style.display = 'block';
          tooltip.style.left = (sx + 12) + 'px';
          tooltip.style.top = (sy - 8) + 'px';
        } else {
          tooltip.style.display = 'none';
        }
      }
    });

    window.addEventListener('mouseup', function (ev) {
      if (dragging) {
        /* click = navigate, drag = reposition */
        var rect = canvas.getBoundingClientRect();
        var sx = ev.clientX - rect.left;
        var sy = ev.clientY - rect.top;
        var hit = nodeAt(sx, sy);
        if (hit === dragging) {
          var moved = Math.abs(hit.vx) + Math.abs(hit.vy);
          if (moved < 0.1) window.location.href = base_url + hit.url;
        }
        dragging = null;
      }
      panning = false;
    });

    canvas.addEventListener('wheel', function (ev) {
      ev.preventDefault();
      var factor = ev.deltaY < 0 ? 1.1 : 0.9;
      cam.zoom = Math.min(Math.max(cam.zoom * factor, 0.1), 10);
      draw();
    }, { passive: false });

    /* animation loop */
    var animId = null;
    function loop() {
      tick();
      draw();
      if (alpha > 0.001) {
        animId = requestAnimationFrame(loop);
      } else {
        animId = null;
      }
    }
    function ensureRunning() {
      if (!animId) loop();
    }

    /* auto-fit after simulation settles */
    function autoFit() {
      if (nodes.length === 0) return;
      var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      for (var i = 0; i < nodes.length; i++) {
        if (nodes[i].x < minX) minX = nodes[i].x;
        if (nodes[i].x > maxX) maxX = nodes[i].x;
        if (nodes[i].y < minY) minY = nodes[i].y;
        if (nodes[i].y > maxY) maxY = nodes[i].y;
      }
      cam.x = (minX + maxX) / 2;
      cam.y = (minY + maxY) / 2;
      var rangeX = (maxX - minX) || 100;
      var rangeY = (maxY - minY) || 100;
      cam.zoom = Math.min(W / (rangeX + 80), H / (rangeY + 80), 2);
    }

    /* run warmup then fit */
    for (var w = 0; w < 200; w++) tick();
    autoFit();
    loop();
  }

  /* ── init ────────────────────────────────────────────────── */

  function initGraph(container, opts) {
    var url = container.getAttribute('data-graph-url');
    if (!url) return;

    var xhr = new XMLHttpRequest();
    xhr.open('GET', url);
    xhr.onload = function () {
      if (xhr.status !== 200) return;
      var data = JSON.parse(xhr.responseText);

      if (opts && opts.currentId) {
        data = filterNeighborhood(data, opts.currentId);
      }

      container.setAttribute('data-node-count', data.nodes.length);
      new ForceGraph(container, data, opts);
    };
    xhr.send();
  }

  function filterNeighborhood(data, centerId) {
    var neighborIds = {};
    neighborIds[centerId] = true;
    for (var i = 0; i < data.edges.length; i++) {
      var e = data.edges[i];
      if (e.source === centerId) neighborIds[e.target] = true;
      if (e.target === centerId) neighborIds[e.source] = true;
    }
    var nodes = data.nodes.filter(function (n) { return neighborIds[n.id]; });
    var edges = data.edges.filter(function (e) {
      return neighborIds[e.source] && neighborIds[e.target];
    });
    return { nodes: nodes, edges: edges };
  }

  /* ── page init ──────────────────────────────────────────── */

  function init() {
    /* full graph page */
    var full = document.getElementById('graph-container');
    if (full && full.getAttribute('data-graph-url')) {
      initGraph(full, {});
    }

    /* local graph on zettel pages */
    var local = document.getElementById('local-graph-container');
    if (local && local.getAttribute('data-graph-url')) {
      var zettelId = local.getAttribute('data-zettel-id');
      if (zettelId) initGraph(local, { currentId: zettelId });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
