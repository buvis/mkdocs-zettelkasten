(function () {
  'use strict';

  var POP_DELAY = 300; // ms
  var POP_HIDE_DELAY = 100; // ms

  var tooltip = null;
  var showTimer = null;
  var hideTimer = null;
  var previews = {};

  /* ── helpers ─────────────────────────────────────────────── */

  function createTooltip() {
    tooltip = document.createElement('div');
    tooltip.id = 'zettel-preview-popover';
    tooltip.className = 'zettel-preview-popover';
    document.body.appendChild(tooltip);

    // Keep visible if mouse moves over the tooltip
    tooltip.addEventListener('mouseenter', function () {
      if (hideTimer) {
        clearTimeout(hideTimer);
        hideTimer = null;
      }
    });

    tooltip.addEventListener('mouseleave', function () {
      hide();
    });
  }

  function show(link, data) {
    if (hideTimer) clearTimeout(hideTimer);

    // Set content
    var title = document.createElement('div');
    title.className = 'preview-title';
    title.textContent = data.title;

    var excerpt = document.createElement('div');
    excerpt.className = 'preview-excerpt';
    excerpt.textContent = data.excerpt || 'No preview available.';

    tooltip.innerHTML = '';
    tooltip.appendChild(title);
    tooltip.appendChild(excerpt);

    // Show to calculate dimensions
    tooltip.style.display = 'block';
    tooltip.style.opacity = '0';

    // Position
    var rect = link.getBoundingClientRect();
    var tipRect = tooltip.getBoundingClientRect();

    var top = rect.bottom + 10;
    var left = rect.left + (rect.width / 2) - (tipRect.width / 2);

    // Viewport boundary checks
    if (left < 10) left = 10;
    if (left + tipRect.width > window.innerWidth - 10) {
      left = window.innerWidth - tipRect.width - 10;
    }

    if (top + tipRect.height > window.innerHeight - 10) {
      // Flip to top if not enough space below
      top = rect.top - tipRect.height - 10;
      tooltip.classList.add('flipped');
    } else {
      tooltip.classList.remove('flipped');
    }

    tooltip.style.top = (top + window.scrollY) + 'px';
    tooltip.style.left = (left + window.scrollX) + 'px';

    // Fade in
    requestAnimationFrame(function () {
      tooltip.style.opacity = '1';
    });
  }

  function hide() {
    if (showTimer) clearTimeout(showTimer);
    hideTimer = setTimeout(function () {
      if (tooltip) {
        tooltip.style.opacity = '0';
        setTimeout(function () {
          tooltip.style.display = 'none';
        }, 200);
      }
    }, POP_HIDE_DELAY);
  }

  /* ── init ────────────────────────────────────────────────── */

  function initPreviews() {
    var url = base_url + '/previews.json';
    if (base_url.slice(-1) === '/') {
       url = base_url + 'previews.json';
    }

    fetch(url).then(function (res) {
      if (!res.ok) return;
      return res.json();
    }).then(function (data) {
      if (!data) return;
      previews = data;
      bindLinks();
    });
  }

  function bindLinks() {
    createTooltip();

    // Match links that look like zettel IDs: /YYYYMMDDHHMMSS/
    // This regex might need tuning based on exact URL structure,
    // but looking for the ID pattern in href is a safe bet for internal links.
    var links = document.querySelectorAll('a');
    var idRegex = /\/(\d{14})\/?/;

    for (var i = 0; i < links.length; i++) {
      var link = links[i];
      var href = link.href;
      if (!href) continue;

      var match = href.match(idRegex);
      if (match) {
        var id = match[1];
        if (previews[id]) {
          (function (l, d) {
            l.addEventListener('mouseenter', function () {
              if (showTimer) clearTimeout(showTimer);
              showTimer = setTimeout(function () {
                show(l, d);
              }, POP_DELAY);
            });

            l.addEventListener('mouseleave', function () {
              if (showTimer) clearTimeout(showTimer);
              hide();
            });
          })(link, previews[id]);
        }
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPreviews);
  } else {
    initPreviews();
  }

})();
