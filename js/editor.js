(() => {
  let editor = null;
  let currentSha = null;
  let cachedToken = null;

  const utf8ToBase64 = (str) => {
    const bytes = new TextEncoder().encode(str);
    let binary = '';
    for (let i = 0; i < bytes.length; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  };

  const base64ToUtf8 = (b64) => {
    const binary = atob(b64.replace(/\s/g, ''));
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return new TextDecoder().decode(bytes);
  };

  const cfg = () => window.__zettelkasten_editor || {};

  const getToken = () => {
    if (cachedToken) return Promise.resolve(cachedToken);

    return new Promise((resolve, reject) => {
      const dialog = document.getElementById('zettel-token-dialog');
      const input = document.getElementById('zettel-token-input');
      const submit = document.getElementById('zettel-token-submit');
      if (!dialog || !input || !submit) {
        reject(new Error('Token dialog not found'));
        return;
      }

      input.value = '';
      dialog.showModal();
      input.focus();

      const cleanup = () => {
        submit.removeEventListener('click', onSubmit);
        input.removeEventListener('keydown', onKeydown);
        dialog.removeEventListener('close', onClose);
      };

      const onSubmit = () => {
        const val = input.value.trim();
        if (!val) return;
        cachedToken = val;
        dialog.close();
        cleanup();
        updateForgetButton();
        resolve(val);
      };

      const onKeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          onSubmit();
        }
      };

      const onClose = () => {
        cleanup();
        reject(new Error('cancelled'));
      };

      submit.addEventListener('click', onSubmit);
      input.addEventListener('keydown', onKeydown);
      dialog.addEventListener('close', onClose);
    });
  };

  const forgetToken = () => {
    cachedToken = null;
    updateForgetButton();
    showToast('Token forgotten');
  };

  const updateForgetButton = () => {
    const btn = document.getElementById('zettel-forget-token-btn');
    if (!btn) return;
    btn.style.display = cachedToken ? 'inline-block' : 'none';
  };

  const showToast = (message, type) => {
    const toast = document.createElement('div');
    toast.className = 'zettel-toast' + (type === 'error' ? ' zettel-toast-error' : '');
    toast.textContent = message;
    document.body.appendChild(toast);
    requestAnimationFrame(() => {
      toast.classList.add('show');
    });
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => { toast.remove(); }, 300);
    }, 3000);
  };

  const SAFE_SLUG = /^[\w][\w./-]*$/;

  const validateCfg = () => {
    const c = cfg();
    if (!c.repo || !SAFE_SLUG.test(c.repo)) throw new Error('Invalid repo: ' + c.repo);
    if (!c.branch || !SAFE_SLUG.test(c.branch)) throw new Error('Invalid branch: ' + c.branch);
  };

  const repoPath = () => {
    const c = cfg();
    return c.docsPrefix ? c.docsPrefix + '/' + c.srcPath : c.srcPath;
  };

  const fetchFile = (path, t) => {
    validateCfg();
    const c = cfg();
    return fetch(
      'https://api.github.com/repos/' +
        c.repo +
        '/contents/' +
        path +
        '?ref=' +
        c.branch,
      { headers: { Authorization: 'token ' + t, Accept: 'application/vnd.github.v3+json' } }
    ).then((resp) => {
      if (!resp.ok) throw new Error('GitHub API error: ' + resp.status);
      return resp.json();
    });
  };

  const saveFile = (path, content, sha, t) => {
    validateCfg();
    const c = cfg();
    return fetch(
      'https://api.github.com/repos/' + c.repo + '/contents/' + path,
      {
        method: 'PUT',
        headers: {
          Authorization: 'token ' + t,
          'Content-Type': 'application/json',
          Accept: 'application/vnd.github.v3+json',
        },
        body: JSON.stringify({
          message: 'Update ' + c.srcPath,
          content: utf8ToBase64(content),
          sha: sha,
          branch: c.branch,
        }),
      }
    ).then((resp) => {
      if (!resp.ok)
        return resp.json().then((d) => {
          throw new Error(d.message || 'Save failed: ' + resp.status);
        });
      return resp.json();
    });
  };

  const enterEditMode = () => {
    const c = cfg();
    if (!c.repo || !c.srcPath) return;

    getToken()
      .then((t) => {
        const path = repoPath();
        return fetchFile(path, t);
      })
      .then((data) => {
        currentSha = data.sha;
        const content = base64ToUtf8(data.content);

        document.querySelector('.file-body').style.display = 'none';
        document.getElementById('zettel-editor').style.display = 'block';

        const textarea = document.getElementById('zettel-editor-textarea');
        textarea.value = content;

        editor = new EasyMDE({
          element: textarea,
          spellChecker: false,
          autosave: { enabled: false },
          toolbar: [
            'bold',
            'italic',
            'heading',
            '|',
            'quote',
            'unordered-list',
            'ordered-list',
            '|',
            'link',
            'image',
            '|',
            'preview',
            'side-by-side',
          ],
        });

        document.getElementById('zettel-edit-btn').style.display = 'none';
        document.getElementById('zettel-save-btn').style.display = 'inline-block';
        document.getElementById('zettel-cancel-btn').style.display = 'inline-block';
      })
      .catch((err) => {
        if (err.message === 'cancelled') return;
        showToast('Failed to load file: ' + err.message, 'error');
      });
  };

  const saveEdit = () => {
    if (!editor) return;

    getToken()
      .then((t) => {
        const content = editor.value();
        const path = repoPath();
        return saveFile(path, content, currentSha, t);
      })
      .then(() => {
        showToast('Saved successfully!');
        cancelEdit();
        setTimeout(() => { location.reload(); }, 1000);
      })
      .catch((err) => {
        if (err.message === 'cancelled') return;
        showToast('Save failed: ' + err.message, 'error');
      });
  };

  const cancelEdit = () => {
    if (editor) {
      editor.toTextArea();
      editor = null;
    }
    document.querySelector('.file-body').style.display = 'block';
    document.getElementById('zettel-editor').style.display = 'none';
    document.getElementById('zettel-edit-btn').style.display = 'inline-block';
    document.getElementById('zettel-save-btn').style.display = 'none';
    document.getElementById('zettel-cancel-btn').style.display = 'none';
  };

  let onOutsideListener = null;

  const closeDropdown = () => {
    const existing = document.getElementById('zettel-edit-dropdown');
    if (existing) existing.remove();
    if (onOutsideListener) {
      document.removeEventListener('click', onOutsideListener);
      onOutsideListener = null;
    }
  };

  const handleEditClick = (e) => {
    e.stopPropagation();
    const existing = document.getElementById('zettel-edit-dropdown');
    if (existing) {
      closeDropdown();
      return;
    }

    const btn = document.getElementById('zettel-edit-btn');
    const dropdown = document.createElement('div');
    dropdown.id = 'zettel-edit-dropdown';
    dropdown.className = 'zettel-edit-dropdown';

    const editHere = document.createElement('button');
    editHere.textContent = 'Edit here';
    editHere.className = 'zettel-edit-dropdown-item';
    editHere.addEventListener('click', (ev) => {
      ev.stopPropagation();
      closeDropdown();
      enterEditMode();
    });

    const editGithub = document.createElement('a');
    editGithub.textContent = 'Edit on GitHub';
    editGithub.className = 'zettel-edit-dropdown-item';
    editGithub.href = cfg().editUrl || '#';
    editGithub.addEventListener('click', () => {
      closeDropdown();
    });

    dropdown.appendChild(editGithub);
    dropdown.appendChild(editHere);
    btn.parentNode.appendChild(dropdown);

    onOutsideListener = () => {
      closeDropdown();
    };
    document.addEventListener('click', onOutsideListener);
  };

  document.addEventListener('DOMContentLoaded', () => {
    const editBtn = document.getElementById('zettel-edit-btn');
    const saveBtn = document.getElementById('zettel-save-btn');
    const cancelBtn = document.getElementById('zettel-cancel-btn');
    const forgetBtn = document.getElementById('zettel-forget-token-btn');

    if (editBtn) editBtn.addEventListener('click', handleEditClick);
    if (saveBtn) saveBtn.addEventListener('click', saveEdit);
    if (cancelBtn) cancelBtn.addEventListener('click', cancelEdit);
    if (forgetBtn) forgetBtn.addEventListener('click', forgetToken);

    updateForgetButton();

    const closeBtn = document.querySelector('#zettel-token-dialog .modal-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        document.getElementById('zettel-token-dialog').close();
      });
    }
  });
})();
