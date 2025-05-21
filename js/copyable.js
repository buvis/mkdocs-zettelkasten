(function() {
  const init = () => {
    document.querySelectorAll("[data-copy-value]").forEach((el) => {
      el.addEventListener("click", async () => {
        const value = el.dataset.copyValue;
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
      });
    });
  };

  // Material for MkDocs compatibility
  if (typeof document$ !== "undefined") {
    document$.subscribe(init);
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
