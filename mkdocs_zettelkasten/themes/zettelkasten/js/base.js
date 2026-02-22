/* Theme & scheme switching */
(function() {
    function getTheme() {
        return document.documentElement.getAttribute('data-theme') || 'light';
    }

    function getScheme() {
        return document.documentElement.getAttribute('data-color-scheme') || 'solarized';
    }

    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        updateHljsTheme();
    }

    function setScheme(scheme) {
        document.documentElement.setAttribute('data-color-scheme', scheme);
        localStorage.setItem('color-scheme', scheme);
        var link = document.getElementById('scheme-css');
        if (link) {
            link.href = base_url + '/css/schemes/' + scheme + '.css';
        }
    }

    function updateHljsTheme() {
        var link = document.getElementById('hljs-theme');
        if (!link) return;
        var style = getTheme() === 'dark' ? link.dataset.darkStyle : link.dataset.lightStyle;
        link.href = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/' + style + '.min.css';
    }

    window.zkTheme = {
        getTheme: getTheme,
        getScheme: getScheme,
        setTheme: setTheme,
        setScheme: setScheme
    };

    document.addEventListener('DOMContentLoaded', function() {
        updateHljsTheme();
    });
})();

function getSearchTerm() {
    var sPageURL = window.location.search.substring(1);
    var sURLVariables = sPageURL.split('&');
    for (var i = 0; i < sURLVariables.length; i++) {
        var sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] == 'q') {
            return sParameterName[1];
        }
    }
}

function applyTopPadding() {
    var container = document.querySelector('body > .container');
    if (!container) return;
    var offset = container.getBoundingClientRect().top + window.scrollY;
    document.documentElement.style.scrollPaddingTop = offset + 'px';
    var sidebars = document.querySelectorAll('.bs-sidebar.affix');
    sidebars.forEach(function(el) { el.style.top = offset + 'px'; });
}

// See https://www.cambiaresearch.com/articles/15/javascript-char-codes-key-codes
// We only list common keys below. Obscure keys are omitted and their use is discouraged.
var keyCodes = {
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

function init() {
    applyTopPadding();

    var search_term = getSearchTerm(),
        searchModal = document.getElementById('mkdocs_search_modal'),
        keyboardModal = document.getElementById('mkdocs_keyboard_modal');

    if (search_term) {
        searchModal.showModal();
        var qi = searchModal.querySelector('#mkdocs-search-query');
        if (qi) qi.focus();
    }

    // Close search modal when result is selected
    // The links get added later so listen to parent
    var searchResults = document.getElementById('mkdocs-search-results');
    if (searchResults) {
        searchResults.addEventListener('click', function(e) {
            if (e.target.matches('a')) {
                searchModal.close();
            }
        });
    }

    // Populate keyboard modal with proper Keys
    var kbdMap = [
        {sel: '.help.shortcut kbd', key: shortcuts.help},
        {sel: '.prev.shortcut kbd', key: shortcuts.previous},
        {sel: '.next.shortcut kbd', key: shortcuts.next},
        {sel: '.search.shortcut kbd', key: shortcuts.search}
    ];
    kbdMap.forEach(function(item) {
        var el = keyboardModal.querySelector(item.sel);
        if (el) el.innerHTML = keyCodes[item.key];
    });

    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (e.target.matches('input, select, textarea, button')) return true;
        var key = e.which || e.keyCode;
        var page;
        switch (key) {
            case shortcuts.next:
                var nextLink = document.querySelector('.navbar a[rel="next"]');
                if (nextLink) page = nextLink.href;
                break;
            case shortcuts.previous:
                var prevLink = document.querySelector('.navbar a[rel="prev"]');
                if (prevLink) page = prevLink.href;
                break;
            case shortcuts.search:
                e.preventDefault();
                keyboardModal.close();
                searchModal.showModal();
                var qi = searchModal.querySelector('#mkdocs-search-query');
                if (qi) qi.focus();
                break;
            case shortcuts.help:
                searchModal.close();
                keyboardModal.showModal();
                break;
            default: break;
        }
        if (page) {
            keyboardModal.close();
            window.location.href = page;
        }
    });

    document.querySelectorAll('table').forEach(function(t) {
        t.classList.add('table', 'table-striped', 'table-hover');
    });

    // Improve the scrollspy behaviour when users click on a TOC item.
    document.querySelectorAll('.bs-sidenav a').forEach(function(link) {
        link.addEventListener('click', function() {
            var clicked = this;
            setTimeout(function() {
                var actives = document.querySelectorAll('.nav li.active a');
                var active = actives[actives.length - 1];
                if (clicked !== active && active) {
                    active.parentElement.classList.remove('active');
                }
                clicked.parentElement.classList.add('active');
            }, 50);
        });
    });

    function showInnerDropdown(item) {
        var popup = item.nextElementSibling;
        if (!popup || !popup.classList.contains('dropdown-menu')) return;
        popup.classList.add('show');
        item.classList.add('open');

        var container = item.parentElement.parentElement;
        var siblings = container.querySelectorAll(':scope > .dropdown-submenu > a');
        siblings.forEach(function(el) {
            if (el !== item) hideInnerDropdown(el);
        });

        var popupMargin = 10;
        var maxBottom = window.innerHeight - popupMargin;
        var bounds = item.getBoundingClientRect();

        popup.style.left = bounds.right + 'px';
        if (bounds.top + popup.offsetHeight > maxBottom && bounds.top > window.innerHeight / 2) {
            popup.style.top = (bounds.bottom - popup.offsetHeight) + 'px';
            popup.style.maxHeight = (bounds.bottom - popupMargin) + 'px';
        } else {
            popup.style.top = bounds.top + 'px';
            popup.style.maxHeight = (maxBottom - bounds.top) + 'px';
        }
    }

    function hideInnerDropdown(item) {
        var popup = item.nextElementSibling;
        if (!popup || !popup.classList.contains('dropdown-menu')) return;
        popup.classList.remove('show');
        item.classList.remove('open');

        popup.scrollTop = 0;
        popup.querySelectorAll('.dropdown-menu').forEach(function(m) {
            m.scrollTop = 0;
            m.classList.remove('show');
        });
        popup.querySelectorAll('.dropdown-submenu > a').forEach(function(a) {
            a.classList.remove('open');
        });
    }

    document.querySelectorAll('.dropdown-submenu > a').forEach(function(el) {
        el.addEventListener('click', function(e) {
            var nextMenu = this.nextElementSibling;
            if (nextMenu && nextMenu.classList.contains('dropdown-menu') && nextMenu.classList.contains('show')) {
                hideInnerDropdown(this);
            } else {
                showInnerDropdown(this);
            }
            e.stopPropagation();
            e.preventDefault();
        });
    });

    document.addEventListener('click', function(e) {
        if (!e.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown-menu.show').forEach(function(m) {
                m.classList.remove('show');
                m.querySelectorAll('.dropdown-menu').forEach(function(sub) { sub.classList.remove('show'); });
                m.querySelectorAll('.dropdown-submenu > a').forEach(function(a) { a.classList.remove('open'); });
            });
        }
    });

    document.querySelectorAll('[data-toggle="collapse"]').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            var target = document.querySelector(btn.getAttribute('data-target'));
            if (target) {
                target.classList.toggle('show');
                btn.classList.toggle('collapsed');
            }
        });
    });

    document.querySelectorAll('[data-toggle="modal"]').forEach(function(trigger) {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            var dialog = document.querySelector(trigger.getAttribute('data-target'));
            if (dialog && dialog.showModal) {
                dialog.showModal();
                var autoFocus = dialog.querySelector('#mkdocs-search-query');
                if (autoFocus) autoFocus.focus();
            }
        });
    });

    document.querySelectorAll('.modal-close').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var dialog = btn.closest('dialog');
            if (dialog) dialog.close();
        });
    });

    document.querySelectorAll('dialog').forEach(function(dialog) {
        dialog.addEventListener('click', function(e) {
            if (e.target === dialog) dialog.close();
        });
    });

    document.querySelectorAll('.dropdown-toggle').forEach(function(toggle) {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            var menu = toggle.nextElementSibling;
            if (menu && menu.classList.contains('dropdown-menu')) {
                var wasOpen = menu.classList.contains('show');
                // Close all other dropdowns first
                document.querySelectorAll('.dropdown-menu.show').forEach(function(m) {
                    m.classList.remove('show');
                });
                if (!wasOpen) {
                    menu.classList.add('show');
                }
            }
        });
    });

    // Scrollspy via IntersectionObserver
    (function() {
        var tocLinks = document.querySelectorAll('.bs-sidebar .nav a');
        if (!tocLinks.length) return;
        var headings = [];
        tocLinks.forEach(function(link) {
            var href = link.getAttribute('href');
            if (href && href.startsWith('#')) {
                var el = document.getElementById(href.slice(1));
                if (el) headings.push({el: el, link: link});
            }
        });
        if (!headings.length) return;

        var currentActive = null;
        var observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    var match = headings.find(function(h) { return h.el === entry.target; });
                    if (match) {
                        if (currentActive) currentActive.classList.remove('active');
                        match.link.classList.add('active');
                        currentActive = match.link;
                    }
                }
            });
        }, {rootMargin: '-100px 0px -66% 0px'});

        headings.forEach(function(h) { observer.observe(h.el); });
    })();

    /* Prevent disabled links from causing a page reload */
    document.querySelectorAll('li.disabled a').forEach(function(el) {
        el.addEventListener('click', function(e) { e.preventDefault(); });
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

window.addEventListener('resize', applyTopPadding);
