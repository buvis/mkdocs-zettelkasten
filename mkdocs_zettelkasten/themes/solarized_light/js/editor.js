(function () {
  var token = null;
  var editor = null;
  var currentSha = null;

  function cfg() {
    return window.__zettelkasten_editor || {};
  }

  function promptToken() {
    if (token) return token;
    token = prompt("Enter GitHub personal access token:");
    return token;
  }

  function repoPath() {
    var c = cfg();
    return c.docsPrefix ? c.docsPrefix + "/" + c.srcPath : c.srcPath;
  }

  function fetchFile(path, t) {
    var c = cfg();
    return fetch(
      "https://api.github.com/repos/" +
        c.repo +
        "/contents/" +
        path +
        "?ref=" +
        c.branch,
      { headers: { Authorization: "token " + t, Accept: "application/vnd.github.v3+json" } }
    ).then(function (resp) {
      if (!resp.ok) throw new Error("GitHub API error: " + resp.status);
      return resp.json();
    });
  }

  function saveFile(path, content, sha, t) {
    var c = cfg();
    return fetch(
      "https://api.github.com/repos/" + c.repo + "/contents/" + path,
      {
        method: "PUT",
        headers: {
          Authorization: "token " + t,
          "Content-Type": "application/json",
          Accept: "application/vnd.github.v3+json",
        },
        body: JSON.stringify({
          message: "Update " + c.srcPath,
          content: btoa(unescape(encodeURIComponent(content))),
          sha: sha,
          branch: c.branch,
        }),
      }
    ).then(function (resp) {
      if (!resp.ok)
        return resp.json().then(function (d) {
          throw new Error(d.message || "Save failed: " + resp.status);
        });
      return resp.json();
    });
  }

  function enterEditMode() {
    var c = cfg();
    if (!c.repo || !c.srcPath) return;

    var t = promptToken();
    if (!t) return;

    var path = repoPath();

    fetchFile(path, t)
      .then(function (data) {
        currentSha = data.sha;
        var content = decodeURIComponent(escape(atob(data.content)));

        document.querySelector(".file-body").style.display = "none";
        document.getElementById("zettel-editor").style.display = "block";

        var textarea = document.getElementById("zettel-editor-textarea");
        textarea.value = content;

        editor = new EasyMDE({
          element: textarea,
          spellChecker: false,
          autosave: { enabled: false },
          toolbar: [
            "bold",
            "italic",
            "heading",
            "|",
            "quote",
            "unordered-list",
            "ordered-list",
            "|",
            "link",
            "image",
            "|",
            "preview",
            "side-by-side",
          ],
        });

        document.getElementById("zettel-edit-btn").style.display = "none";
        document.getElementById("zettel-save-btn").style.display =
          "inline-block";
        document.getElementById("zettel-cancel-btn").style.display =
          "inline-block";
      })
      .catch(function (err) {
        alert("Failed to load file: " + err.message);
      });
  }

  function saveEdit() {
    var t = promptToken();
    if (!t || !editor) return;

    var content = editor.value();
    var path = repoPath();

    saveFile(path, content, currentSha, t)
      .then(function () {
        alert("Saved successfully!");
        cancelEdit();
        location.reload();
      })
      .catch(function (err) {
        alert("Save failed: " + err.message);
      });
  }

  function cancelEdit() {
    if (editor) {
      editor.toTextArea();
      editor = null;
    }
    document.querySelector(".file-body").style.display = "block";
    document.getElementById("zettel-editor").style.display = "none";
    document.getElementById("zettel-edit-btn").style.display = "inline-block";
    document.getElementById("zettel-save-btn").style.display = "none";
    document.getElementById("zettel-cancel-btn").style.display = "none";
  }

  var onOutsideListener = null;

  function closeDropdown() {
    var existing = document.getElementById("zettel-edit-dropdown");
    if (existing) existing.remove();
    if (onOutsideListener) {
      document.removeEventListener("click", onOutsideListener);
      onOutsideListener = null;
    }
  }

  function handleEditClick(e) {
    e.stopPropagation();
    var existing = document.getElementById("zettel-edit-dropdown");
    if (existing) {
      closeDropdown();
      return;
    }

    var btn = document.getElementById("zettel-edit-btn");
    var dropdown = document.createElement("div");
    dropdown.id = "zettel-edit-dropdown";
    dropdown.className = "zettel-edit-dropdown";

    var editHere = document.createElement("button");
    editHere.textContent = "Edit here";
    editHere.className = "zettel-edit-dropdown-item";
    editHere.addEventListener("click", function (ev) {
      ev.stopPropagation();
      closeDropdown();
      enterEditMode();
    });

    var editGithub = document.createElement("a");
    editGithub.textContent = "Edit on GitHub";
    editGithub.className = "zettel-edit-dropdown-item";
    editGithub.href = cfg().editUrl || "#";
    editGithub.addEventListener("click", function () {
      closeDropdown();
    });

    dropdown.appendChild(editGithub);
    dropdown.appendChild(editHere);
    btn.parentNode.appendChild(dropdown);

    onOutsideListener = function () {
      closeDropdown();
    };
    document.addEventListener("click", onOutsideListener);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var editBtn = document.getElementById("zettel-edit-btn");
    var saveBtn = document.getElementById("zettel-save-btn");
    var cancelBtn = document.getElementById("zettel-cancel-btn");

    if (editBtn) editBtn.addEventListener("click", handleEditClick);
    if (saveBtn) saveBtn.addEventListener("click", saveEdit);
    if (cancelBtn) cancelBtn.addEventListener("click", cancelEdit);
  });
})();
