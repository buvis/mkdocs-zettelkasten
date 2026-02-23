/* Settings modal — scheme grid, code theme picker, dark mode toggle */
(function() {
    var REGISTRY_URL;
    var HLJS_BASE = base_url + '/css/vendor/hljs/';

    function fetchRegistry(callback) {
        fetch(REGISTRY_URL).then(function(res) {
            if (res.ok) return res.json();
        }).then(function(data) {
            if (data) callback(data);
        });
    }

    function renderSchemeGrid(schemes) {
        var grid = document.getElementById('scheme-grid');
        if (!grid) return;
        grid.innerHTML = '';
        var current = window.zkTheme.getScheme();
        var isDark = window.zkTheme.getTheme() === 'dark';

        schemes.forEach(function(scheme) {
            var card = document.createElement('div');
            card.className = 'scheme-card' + (scheme.id === current ? ' active' : '');
            card.dataset.schemeId = scheme.id;

            var colors = isDark ? scheme.preview.dark : scheme.preview.light;
            var swatch = document.createElement('div');
            swatch.className = 'scheme-swatch';

            for (var i = 0; i < colors.length; i++) {
                var strip = document.createElement('span');
                strip.className = 'swatch-strip';
                strip.style.background = colors[i];
                swatch.appendChild(strip);
            }

            var label = document.createElement('span');
            label.className = 'scheme-label';
            label.textContent = scheme.name;

            card.appendChild(swatch);
            card.appendChild(label);
            card.addEventListener('click', function() {
                window.zkTheme.setScheme(scheme.id);
                grid.querySelectorAll('.scheme-card').forEach(function(c) {
                    c.classList.remove('active');
                });
                card.classList.add('active');
            });
            grid.appendChild(card);
        });
    }

    function initCodeThemePicker() {
        var select = document.getElementById('hljs-theme-select');
        if (!select) return;

        var isDark = window.zkTheme.getTheme() === 'dark';
        var key = isDark ? 'hljs-theme-dark' : 'hljs-theme-light';
        var current = localStorage.getItem(key);
        if (current) select.value = current;

        select.addEventListener('change', function() {
            var theme = select.value;
            var isDark = window.zkTheme.getTheme() === 'dark';
            var key = isDark ? 'hljs-theme-dark' : 'hljs-theme-light';
            localStorage.setItem(key, theme);

            var link = document.getElementById('hljs-theme');
            if (link) {
                if (isDark) link.dataset.darkStyle = theme;
                else link.dataset.lightStyle = theme;
                link.href = HLJS_BASE + theme + '.min.css';
            }

            var preview = document.querySelector('#hljs-preview code');
            if (preview && window.hljs) {
                preview.removeAttribute('data-highlighted');
                window.hljs.highlightElement(preview);
            }
        });
    }

    function initDarkModeToggle() {
        var toggle = document.getElementById('dark-mode-toggle');
        if (!toggle) return;

        toggle.checked = window.zkTheme.getTheme() === 'dark';

        toggle.addEventListener('change', function() {
            var theme = toggle.checked ? 'dark' : 'light';
            window.zkTheme.setTheme(theme);

            var select = document.getElementById('hljs-theme-select');
            if (select) {
                var key = theme === 'dark' ? 'hljs-theme-dark' : 'hljs-theme-light';
                var current = localStorage.getItem(key);
                if (current) select.value = current;
            }

            fetchRegistry(renderSchemeGrid);
        });
    }

    document.addEventListener('DOMContentLoaded', function() {
        REGISTRY_URL = base_url + '/css/schemes/registry.json';
        fetchRegistry(renderSchemeGrid);
        initCodeThemePicker();
        initDarkModeToggle();

        var preview = document.querySelector('#hljs-preview code');
        if (preview && window.hljs) {
            window.hljs.highlightElement(preview);
        }
    });
})();
