/* Settings modal — scheme grid, code theme picker, dark mode toggle */
(() => {
    let REGISTRY_URL;
    const HLJS_BASE = `${base_url}/css/vendor/hljs/`;

    const fetchRegistry = (callback) => {
        fetch(REGISTRY_URL).then((res) => {
            if (res.ok) return res.json();
        }).then((data) => {
            if (data) callback(data);
        });
    };

    const renderSchemeGrid = (schemes) => {
        const grid = document.getElementById('scheme-grid');
        if (!grid) return;
        grid.innerHTML = '';
        const current = window.zkTheme.getScheme();
        const isDark = window.zkTheme.getTheme() === 'dark';

        schemes.forEach((scheme) => {
            const card = document.createElement('div');
            card.className = `scheme-card${scheme.id === current ? ' active' : ''}`;
            card.dataset.schemeId = scheme.id;

            const colors = isDark ? scheme.preview.dark : scheme.preview.light;
            const swatch = document.createElement('div');
            swatch.className = 'scheme-swatch';

            for (let i = 0; i < colors.length; i++) {
                const strip = document.createElement('span');
                strip.className = 'swatch-strip';
                strip.style.background = colors[i];
                swatch.appendChild(strip);
            }

            const label = document.createElement('span');
            label.className = 'scheme-label';
            label.textContent = scheme.name;

            card.appendChild(swatch);
            card.appendChild(label);
            card.addEventListener('click', () => {
                window.zkTheme.setScheme(scheme.id);
                grid.querySelectorAll('.scheme-card').forEach((c) => {
                    c.classList.remove('active');
                });
                card.classList.add('active');
            });
            grid.appendChild(card);
        });
    };

    const initCodeThemePicker = () => {
        const select = document.getElementById('hljs-theme-select');
        if (!select) return;

        const isDark = window.zkTheme.getTheme() === 'dark';
        const key = isDark ? 'hljs-theme-dark' : 'hljs-theme-light';
        const current = localStorage.getItem(key);
        if (current) select.value = current;

        select.addEventListener('change', () => {
            const theme = select.value;
            const isDark = window.zkTheme.getTheme() === 'dark';
            const key = isDark ? 'hljs-theme-dark' : 'hljs-theme-light';
            localStorage.setItem(key, theme);

            const link = document.getElementById('hljs-theme');
            if (link) {
                if (isDark) link.dataset.darkStyle = theme;
                else link.dataset.lightStyle = theme;
                link.href = `${HLJS_BASE}${theme}.min.css`;
            }

            const preview = document.querySelector('#hljs-preview code');
            if (preview && window.hljs) {
                preview.removeAttribute('data-highlighted');
                window.hljs.highlightElement(preview);
            }
        });
    };

    const initDarkModeToggle = () => {
        const toggle = document.getElementById('dark-mode-toggle');
        if (!toggle) return;

        toggle.checked = window.zkTheme.getTheme() === 'dark';

        toggle.addEventListener('change', () => {
            const theme = toggle.checked ? 'dark' : 'light';
            window.zkTheme.setTheme(theme);

            const select = document.getElementById('hljs-theme-select');
            if (select) {
                const key = theme === 'dark' ? 'hljs-theme-dark' : 'hljs-theme-light';
                const current = localStorage.getItem(key);
                if (current) select.value = current;
            }

            fetchRegistry(renderSchemeGrid);
        });
    };

    document.addEventListener('DOMContentLoaded', () => {
        REGISTRY_URL = `${base_url}/css/schemes/registry.json`;
        fetchRegistry(renderSchemeGrid);
        initCodeThemePicker();
        initDarkModeToggle();

        const preview = document.querySelector('#hljs-preview code');
        if (preview && window.hljs) {
            window.hljs.highlightElement(preview);
        }
    });
})();
