/* Theme & scheme switching */
(() => {
    const root = ((typeof base_url !== 'undefined' && base_url) || '').replace(/\/+$/, '');
    const getTheme = () => document.documentElement.getAttribute('data-theme') || 'light';

    const getScheme = () => document.documentElement.getAttribute('data-color-scheme') || 'solarized';

    const setTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        updateHljsTheme();
    };

    const setScheme = (scheme) => {
        document.documentElement.setAttribute('data-color-scheme', scheme);
        localStorage.setItem('color-scheme', scheme);
        const link = document.getElementById('scheme-css');
        if (link) {
            link.href = `${root}/css/schemes/${scheme}.css`;
        }
    };

    const updateHljsTheme = () => {
        const link = document.getElementById('hljs-theme');
        if (!link) return;
        const style = getTheme() === 'dark' ? link.dataset.darkStyle : link.dataset.lightStyle;
        link.href = `${root}/css/vendor/hljs/${style}.min.css`;
    };

    window.zkTheme = {
        getTheme,
        getScheme,
        setTheme,
        setScheme
    };

    document.addEventListener('DOMContentLoaded', () => {
        updateHljsTheme();
    });
})();

(() => {

const applyTopPadding = () => {
    const container = document.querySelector('body > .container');
    if (!container) return;
    const offset = container.getBoundingClientRect().top + window.scrollY;
    document.documentElement.style.scrollPaddingTop = `${offset}px`;
    const sidebars = document.querySelectorAll('.bs-sidebar.affix');
    sidebars.forEach((el) => { el.style.top = `${offset}px`; });
};

// See https://www.cambiaresearch.com/articles/15/javascript-char-codes-key-codes
// We only list common keys below. Obscure keys are omitted and their use is discouraged.
const keyCodes = {
    8: 'backspace',
    9: 'tab',
    13: 'enter',
    16: 'shift',
    17: 'ctrl',
    18: 'alt',
    19: 'pause/break',
    20: 'caps lock',
    27: 'escape',
    32: 'spacebar',
    33: 'page up',
    34: 'page down',
    35: 'end',
    36: 'home',
    37: '&larr;',
    38: '&uarr;',
    39: '&rarr;',
    40: '&darr;',
    45: 'insert',
    46: 'delete',
    48: '0',
    49: '1',
    50: '2',
    51: '3',
    52: '4',
    53: '5',
    54: '6',
    55: '7',
    56: '8',
    57: '9',
    65: 'a',
    66: 'b',
    67: 'c',
    68: 'd',
    69: 'e',
    70: 'f',
    71: 'g',
    72: 'h',
    73: 'i',
    74: 'j',
    75: 'k',
    76: 'l',
    77: 'm',
    78: 'n',
    79: 'o',
    80: 'p',
    81: 'q',
    82: 'r',
    83: 's',
    84: 't',
    85: 'u',
    86: 'v',
    87: 'w',
    88: 'x',
    89: 'y',
    90: 'z',
    91: 'Left Windows Key / Left ⌘',
    92: 'Right Windows Key',
    93: 'Windows Menu / Right ⌘',
    96: 'numpad 0',
    97: 'numpad 1',
    98: 'numpad 2',
    99: 'numpad 3',
    100: 'numpad 4',
    101: 'numpad 5',
    102: 'numpad 6',
    103: 'numpad 7',
    104: 'numpad 8',
    105: 'numpad 9',
    106: 'multiply',
    107: 'add',
    109: 'subtract',
    110: 'decimal point',
    111: 'divide',
    112: 'f1',
    113: 'f2',
    114: 'f3',
    115: 'f4',
    116: 'f5',
    117: 'f6',
    118: 'f7',
    119: 'f8',
    120: 'f9',
    121: 'f10',
    122: 'f11',
    123: 'f12',
    124: 'f13',
    125: 'f14',
    126: 'f15',
    127: 'f16',
    128: 'f17',
    129: 'f18',
    130: 'f19',
    131: 'f20',
    132: 'f21',
    133: 'f22',
    134: 'f23',
    135: 'f24',
    144: 'num lock',
    145: 'scroll lock',
    186: '&semi;',
    187: '&equals;',
    188: '&comma;',
    189: '&hyphen;',
    190: '&period;',
    191: '&quest;',
    192: '&grave;',
    219: '&lsqb;',
    220: '&bsol;',
    221: '&rsqb;',
    222: '&apos;',
};

const init = () => {
    applyTopPadding();

    const searchModal = document.getElementById('mkdocs_search_modal');
    const keyboardModal = document.getElementById('mkdocs_keyboard_modal');

    // Close search modal when result is selected
    // The links get added later so listen to parent
    const searchResults = document.getElementById('mkdocs-search-results');
    if (searchResults && searchModal) {
        searchResults.addEventListener('click', (e) => {
            if (e.target.matches('a')) {
                searchModal.close();
            }
        });
    }

    // Populate keyboard modal with proper Keys
    const sc = (typeof shortcuts !== 'undefined' && shortcuts) || {};
    if (keyboardModal) {
        const kbdMap = [
            {sel: '.help.shortcut kbd', key: sc.help},
            {sel: '.prev.shortcut kbd', key: sc.previous},
            {sel: '.next.shortcut kbd', key: sc.next},
            {sel: '.search.shortcut kbd', key: sc.search}
        ];
        kbdMap.forEach((item) => {
            const el = keyboardModal.querySelector(item.sel);
            if (el) el.innerHTML = keyCodes[item.key];
        });
    }

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.target.matches('input, select, textarea, button')) return true;
        const key = e.which || e.keyCode;
        let page;
        switch (key) {
            case sc.next:
            case 39: // right arrow
                const nextLink = document.querySelector('.navbar a[rel="next"]');
                if (nextLink) page = nextLink.href;
                break;
            case sc.previous:
            case 37: // left arrow
                const prevLink = document.querySelector('.navbar a[rel="prev"]');
                if (prevLink) page = prevLink.href;
                break;
            case sc.search:
                e.preventDefault();
                if (keyboardModal) keyboardModal.close();
                if (searchModal) {
                    searchModal.showModal();
                    const qi = searchModal.querySelector('#mkdocs-search-query');
                    if (qi) qi.focus();
                }
                break;
            case sc.help:
                if (searchModal) searchModal.close();
                if (keyboardModal) keyboardModal.showModal();
                break;
            default: break;
        }
        if (page) {
            if (keyboardModal) keyboardModal.close();
            window.location.href = page;
        }
    });

    document.querySelectorAll('table').forEach((t) => {
        t.classList.add('table', 'table-striped', 'table-hover');
    });

    const showInnerDropdown = (item) => {
        const popup = item.nextElementSibling;
        if (!popup || !popup.classList.contains('dropdown-menu')) return;
        popup.classList.add('show');
        item.classList.add('open');

        const container = item.parentElement.parentElement;
        const siblings = container.querySelectorAll(':scope > .dropdown-submenu > a');
        siblings.forEach((el) => {
            if (el !== item) hideInnerDropdown(el);
        });

        const popupMargin = 10;
        const maxBottom = window.innerHeight - popupMargin;
        const bounds = item.getBoundingClientRect();

        popup.style.left = `${bounds.right}px`;
        if (bounds.top + popup.offsetHeight > maxBottom && bounds.top > window.innerHeight / 2) {
            popup.style.top = `${bounds.bottom - popup.offsetHeight}px`;
            popup.style.maxHeight = `${bounds.bottom - popupMargin}px`;
        } else {
            popup.style.top = `${bounds.top}px`;
            popup.style.maxHeight = `${maxBottom - bounds.top}px`;
        }
    };

    const hideInnerDropdown = (item) => {
        const popup = item.nextElementSibling;
        if (!popup || !popup.classList.contains('dropdown-menu')) return;
        popup.classList.remove('show');
        item.classList.remove('open');

        popup.scrollTop = 0;
        popup.querySelectorAll('.dropdown-menu').forEach((m) => {
            m.scrollTop = 0;
            m.classList.remove('show');
        });
        popup.querySelectorAll('.dropdown-submenu > a').forEach((a) => {
            a.classList.remove('open');
        });
    };

    document.querySelectorAll('.dropdown-submenu > a').forEach((el) => {
        el.addEventListener('click', function(e) {
            const nextMenu = this.nextElementSibling;
            if (nextMenu && nextMenu.classList.contains('dropdown-menu') && nextMenu.classList.contains('show')) {
                hideInnerDropdown(this);
            } else {
                showInnerDropdown(this);
            }
            e.stopPropagation();
            e.preventDefault();
        });
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown-menu.show').forEach((m) => {
                m.classList.remove('show');
                m.querySelectorAll('.dropdown-menu').forEach((sub) => { sub.classList.remove('show'); });
                m.querySelectorAll('.dropdown-submenu > a').forEach((a) => { a.classList.remove('open'); });
            });
        }
    });

    document.querySelectorAll('[data-toggle="collapse"]').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(btn.getAttribute('data-target'));
            if (target) {
                target.classList.toggle('show');
                btn.classList.toggle('collapsed');
                btn.setAttribute('aria-expanded', target.classList.contains('show'));
            }
        });
    });

    document.querySelectorAll('[data-toggle="modal"]').forEach((trigger) => {
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            const dialog = document.querySelector(trigger.getAttribute('data-target'));
            if (dialog && dialog.showModal) {
                dialog.showModal();
                const autoFocus = dialog.querySelector('#mkdocs-search-query');
                if (autoFocus) autoFocus.focus();
            }
        });
    });

    document.querySelectorAll('.modal-close').forEach((btn) => {
        btn.addEventListener('click', () => {
            const dialog = btn.closest('dialog');
            if (dialog) dialog.close();
        });
    });

    document.querySelectorAll('dialog').forEach((dialog) => {
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) dialog.close();
        });
    });

    document.querySelectorAll('.dropdown-toggle').forEach((toggle) => {
        toggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const menu = toggle.nextElementSibling;
            if (menu && menu.classList.contains('dropdown-menu')) {
                const wasOpen = menu.classList.contains('show');
                // Close all other dropdowns first
                document.querySelectorAll('.dropdown-menu.show').forEach((m) => {
                    m.classList.remove('show');
                });
                if (!wasOpen) {
                    menu.classList.add('show');
                }
            }
        });
    });

    // Sidebar navigation toggle
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebarNav = document.getElementById('sidebar-nav');
    const sidebarBackdrop = document.getElementById('sidebar-backdrop');
    const sidebarClose = sidebarNav && sidebarNav.querySelector('.sidebar-close');
    if (sidebarToggle && sidebarNav) {
        const sidebarAC = new AbortController();
        const sOpt = {signal: sidebarAC.signal};
        const openSidebar = () => {
            sidebarNav.classList.add('open');
            if (sidebarBackdrop) sidebarBackdrop.classList.add('open');
            sidebarToggle.setAttribute('aria-expanded', 'true');
            sessionStorage.setItem('sidebar-open', '1');
        };
        const closeSidebar = () => {
            sidebarNav.classList.remove('open');
            if (sidebarBackdrop) sidebarBackdrop.classList.remove('open');
            sidebarToggle.setAttribute('aria-expanded', 'false');
            sessionStorage.setItem('sidebar-open', '0');
        };
        sidebarToggle.addEventListener('click', openSidebar, sOpt);
        if (sidebarClose) sidebarClose.addEventListener('click', closeSidebar, sOpt);
        if (sidebarBackdrop) sidebarBackdrop.addEventListener('click', closeSidebar, sOpt);
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && sidebarNav.classList.contains('open')) closeSidebar();
        }, sOpt);
        sidebarNav.querySelectorAll('a.sidebar-link').forEach((link) => {
            link.addEventListener('click', () => closeSidebar(), sOpt);
        });
        if (sessionStorage.getItem('sidebar-open') === '1') openSidebar();
        window.addEventListener('pagehide', () => sidebarAC.abort(), {once: true});
    }

    // Scrollspy via IntersectionObserver
    (() => {
        const tocLinks = document.querySelectorAll('.bs-sidebar .nav a');
        if (!tocLinks.length) return;
        const headings = [];
        tocLinks.forEach((link) => {
            const href = link.getAttribute('href');
            if (href && href.startsWith('#')) {
                const el = document.getElementById(href.slice(1));
                if (el) headings.push({el, link});
            }
        });
        if (!headings.length) return;

        let currentActive = null;
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    const match = headings.find((h) => h.el === entry.target);
                    if (match) {
                        if (currentActive) currentActive.classList.remove('active');
                        match.link.classList.add('active');
                        currentActive = match.link;
                    }
                }
            });
        }, {rootMargin: '-100px 0px -66% 0px'});

        headings.forEach((h) => { observer.observe(h.el); });

        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden') observer.disconnect();
        }, {once: true});
    })();

};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

window.addEventListener('resize', applyTopPadding);

})();
