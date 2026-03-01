(() => {
  'use strict';

  const POP_DELAY = 300; // ms
  const POP_HIDE_DELAY = 100; // ms

  let tooltip = null;
  let showTimer = null;
  let hideTimer = null;
  let previews = {};

  /* ── helpers ─────────────────────────────────────────────── */

  const createTooltip = () => {
    tooltip = document.createElement('div');
    tooltip.id = 'zettel-preview-popover';
    tooltip.className = 'zettel-preview-popover';
    document.body.appendChild(tooltip);

    // Keep visible if mouse moves over the tooltip
    tooltip.addEventListener('mouseenter', () => {
      if (hideTimer) {
        clearTimeout(hideTimer);
        hideTimer = null;
      }
    });

    tooltip.addEventListener('mouseleave', () => {
      hide();
    });
  };

  const show = (link, data) => {
    if (hideTimer) clearTimeout(hideTimer);

    // Set content
    const title = document.createElement('div');
    title.className = 'preview-title';
    title.textContent = data.title;

    const excerpt = document.createElement('div');
    excerpt.className = 'preview-excerpt';
    excerpt.textContent = data.excerpt || 'No preview available.';

    tooltip.innerHTML = '';
    tooltip.appendChild(title);
    tooltip.appendChild(excerpt);

    // Show to calculate dimensions
    tooltip.style.display = 'block';
    tooltip.style.opacity = '0';

    // Position
    const rect = link.getBoundingClientRect();
    const tipRect = tooltip.getBoundingClientRect();

    let top = rect.bottom + 10;
    let left = rect.left + (rect.width / 2) - (tipRect.width / 2);

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

    tooltip.style.top = `${top + window.scrollY}px`;
    tooltip.style.left = `${left + window.scrollX}px`;

    // Fade in
    requestAnimationFrame(() => {
      tooltip.style.opacity = '1';
    });
  };

  const hide = () => {
    if (showTimer) clearTimeout(showTimer);
    hideTimer = setTimeout(() => {
      if (tooltip) {
        tooltip.style.opacity = '0';
        setTimeout(() => {
          tooltip.style.display = 'none';
        }, 200);
      }
    }, POP_HIDE_DELAY);
  };

  /* ── init ────────────────────────────────────────────────── */

  const initPreviews = () => {
    let url = `${base_url}/previews.json`;
    if (base_url.slice(-1) === '/') {
       url = `${base_url}previews.json`;
    }

    fetch(url).then((res) => {
      if (!res.ok) return;
      return res.json();
    }).then((data) => {
      if (!data) return;
      previews = data;
      bindLinks();
    }).catch(() => {
      /* previews unavailable — degrade silently */
    });
  };

  const bindLinks = () => {
    createTooltip();

    // Match links that look like zettel IDs: /YYYYMMDDHHMMSS/
    // This regex might need tuning based on exact URL structure,
    // but looking for the ID pattern in href is a safe bet for internal links.
    const links = document.querySelectorAll('a');
    const idRegex = /\/(\d{14})\/?/;

    for (let i = 0; i < links.length; i++) {
      const link = links[i];
      const href = link.href;
      if (!href) continue;

      if (link.hasAttribute('data-preview-bound')) continue;
      const match = href.match(idRegex);
      if (match) {
        const id = match[1];
        if (previews[id]) {
          link.setAttribute('data-preview-bound', '');
          ((l, d) => {
            l.addEventListener('mouseenter', () => {
              if (showTimer) clearTimeout(showTimer);
              showTimer = setTimeout(() => {
                show(l, d);
              }, POP_DELAY);
            });

            l.addEventListener('mouseleave', () => {
              if (showTimer) clearTimeout(showTimer);
              hide();
            });
          })(link, previews[id]);
        }
      }
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPreviews);
  } else {
    initPreviews();
  }

})();
