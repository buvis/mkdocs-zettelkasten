(() => {
  async function copyText(value) {
    try {
      await navigator.clipboard.writeText(value);
    } catch (err) {
      const textarea = document.createElement("textarea");
      textarea.value = value;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
  }

  const init = () => {
    document.querySelectorAll("[data-copy-value]").forEach((el) => {
      el.addEventListener("click", () => copyText(el.dataset.copyValue));
    });

    document.querySelectorAll(".codehilite pre, .highlight pre, pre > code").forEach((el) => {
      const container = el.closest(".codehilite") || el.closest(".highlight") || el.parentElement;
      if (container.querySelector(".copy-btn")) return;

      const btn = document.createElement("button");
      btn.className = "copy-btn";
      btn.setAttribute("aria-label", "Copy code");
      btn.textContent = "\u2398";
      btn.addEventListener("click", () => {
        const code = el.tagName === "CODE" ? el : el.querySelector("code") || el;
        copyText(code.textContent);
        btn.textContent = "\u2713";
        setTimeout(() => { btn.textContent = "\u2398"; }, 2000);
      });
      container.appendChild(btn);
    });
  };

  // Material for MkDocs compatibility
  if (typeof document$ !== "undefined") {
    document$.subscribe(init);
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
