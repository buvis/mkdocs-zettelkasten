/* Settings modal — scheme grid, code theme picker, dark mode toggle */
(() => {
    let REGISTRY_URL;
    const HLJS_BASE = `${base_url}/css/vendor/hljs/`;

    const fetchRegistry = (callback) => {
        fetch(REGISTRY_URL).then((res) => {
            if (res.ok) return res.json();
        }).then((data) => {
            if (data) callback(data);
        }).catch(() => {
            const grid = document.getElementById('scheme-grid');
            if (grid) grid.textContent = 'Could not load color schemes.';
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
            card.tabIndex = 0;
            card.setAttribute('role', 'button');

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

            const activate = () => {
                window.zkTheme.setScheme(scheme.id);
                grid.querySelectorAll('.scheme-card').forEach((c) => {
                    c.classList.remove('active');
                });
                card.classList.add('active');
            };
            card.appendChild(swatch);
            card.appendChild(label);
            card.addEventListener('click', activate);
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    activate();
                }
            });
            grid.appendChild(card);
        });
    };

    const CODE_THEMES = [
        { value: 'github', name: 'GitHub' },
        { value: 'github-dark', name: 'GitHub Dark' },
        { value: 'monokai', name: 'Monokai' },
        { value: 'solarized-light', name: 'Solarized Light' },
        { value: 'solarized-dark', name: 'Solarized Dark' },
        { value: 'nord', name: 'Nord' },
        { value: 'atom-one-light', name: 'Atom One Light' },
        { value: 'atom-one-dark', name: 'Atom One Dark' },
        { value: 'dracula', name: 'Dracula' },
        { value: 'gruvbox-light', name: 'Gruvbox Light' },
        { value: 'gruvbox-dark', name: 'Gruvbox Dark' },
        { value: 'tokyo-night-dark', name: 'Tokyo Night Dark' },
        { value: 'tokyo-night-light', name: 'Tokyo Night Light' },
        { value: 'a11y-light', name: 'A11y Light' },
        { value: 'a11y-dark', name: 'A11y Dark' },
        { value: 'base16/catppuccin-latte', name: 'Catppuccin Latte' },
        { value: 'base16/catppuccin-mocha', name: 'Catppuccin Mocha' },
        { value: 'base16/rose-pine', name: 'Rose Pine' },
        { value: 'base16/rose-pine-dawn', name: 'Rose Pine Dawn' },
        { value: 'base16/everforest', name: 'Everforest' },
        { value: 'base16/kanagawa', name: 'Kanagawa' },
        { value: 'base16/material', name: 'Material' },
        { value: 'base16/material-lighter', name: 'Material Lighter' },
        { value: 'base16/nord', name: 'Nord (base16)' },
        { value: 'base16/papercolor-light', name: 'PaperColor Light' },
        { value: 'base16/papercolor-dark', name: 'PaperColor Dark' },
        { value: 'base16/zenburn', name: 'Zenburn' },
        { value: 'eink-light', name: 'E-ink Light' },
        { value: 'eink-dark', name: 'E-ink Dark' },
    ];

    const applyCodeTheme = (themeValue) => {
        const isDark = window.zkTheme.getTheme() === 'dark';
        const key = isDark ? 'hljs-theme-dark' : 'hljs-theme-light';
        localStorage.setItem(key, themeValue);

        const link = document.getElementById('hljs-theme');
        if (link) {
            if (isDark) link.dataset.darkStyle = themeValue;
            else link.dataset.lightStyle = themeValue;
            link.href = `${HLJS_BASE}${themeValue}.min.css`;
        }

        const preview = document.querySelector('#hljs-preview code');
        if (preview && window.hljs) {
            preview.removeAttribute('data-highlighted');
            window.hljs.highlightElement(preview);
        }
    };

    const renderCodeThemeGrid = () => {
        const grid = document.getElementById('code-theme-grid');
        if (!grid) return;
        grid.innerHTML = '';

        const isDark = window.zkTheme.getTheme() === 'dark';
        const key = isDark ? 'hljs-theme-dark' : 'hljs-theme-light';
        const current = localStorage.getItem(key) || 'github';

        CODE_THEMES.forEach((theme) => {
            const card = document.createElement('div');
            card.className = `scheme-card${theme.value === current ? ' active' : ''}`;
            card.dataset.themeValue = theme.value;
            card.tabIndex = 0;
            card.setAttribute('role', 'button');

            const label = document.createElement('span');
            label.className = 'scheme-label';
            label.textContent = theme.name;

            const activate = () => {
                applyCodeTheme(theme.value);
                grid.querySelectorAll('.scheme-card').forEach((c) => {
                    c.classList.remove('active');
                });
                card.classList.add('active');
            };
            card.appendChild(label);
            card.addEventListener('click', activate);
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    activate();
                }
            });
            grid.appendChild(card);
        });
    };

    const initCodeThemePicker = () => {
        renderCodeThemeGrid();
    };

    const initDarkModeToggle = () => {
        const toggle = document.getElementById('dark-mode-toggle');
        if (!toggle) return;

        toggle.checked = window.zkTheme.getTheme() === 'dark';

        toggle.addEventListener('change', () => {
            const theme = toggle.checked ? 'dark' : 'light';
            window.zkTheme.setTheme(theme);

            fetchRegistry(renderSchemeGrid);
            renderCodeThemeGrid();
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
