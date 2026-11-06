/* Small presentation and accessibility behaviors for the clinical workspace. */
function showNotice(message) {
  const notice = document.getElementById("appNotice");
  notice.querySelector("span").textContent = message;
  notice.hidden = false;
  clearTimeout(showNotice.timer);
  showNotice.timer = setTimeout(() => { notice.hidden = true; }, 9000);
}

document.addEventListener("DOMContentLoaded", () => {
  const copy = {
    "suite-telephony": ["Clinical intake", "From the first conversation to a complete encounter."],
    "suite-pathology": ["Lab results", "Bring lab values into the picture. See what needs attention."],
    "suite-decision": ["Decision support", "Review risk scores and medication interactions in context."],
    "suite-scribe": ["Encounter records", "The conversation, organized. Ready for review and export."],
    "suite-simulator": ["Clinical scenarios", "Explore the workspace with a prepared educational case."]
  };
  const tabs = [...document.querySelectorAll(".suite-tab-btn")];
  tabs.forEach((tab, index) => {
    const update = () => {
      tabs.forEach(item => item.setAttribute("aria-pressed", String(item === tab)));
      const [title, description] = copy[tab.dataset.target];
      document.getElementById("workspaceTitle").textContent = title + ".";
      document.getElementById("workspaceDescription").textContent = description;
      document.querySelector(".eyebrow span").textContent = `/ 0${index + 1}`;
    };
    tab.setAttribute("aria-pressed", String(tab.classList.contains("active")));
    tab.addEventListener("click", update);
    tab.addEventListener("keydown", event => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : (index + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
      tabs[next].focus();
      tabs[next].click();
    });
  });
  document.getElementById("exploreScenariosBtn").addEventListener("click", () => {
    tabs.at(-1).click();
    tabs.at(-1).focus();
  });
  document.querySelector("#appNotice button").addEventListener("click", () => { document.getElementById("appNotice").hidden = true; });

  // Follow the existing dialog class changes, including asynchronous previews.
  document.querySelectorAll('[role="dialog"]').forEach(dialog => {
    let returnFocus = null;
    const focusable = () => [...dialog.querySelectorAll('button, input, [href], [tabindex="0"]')].filter(item => !item.disabled);
    new MutationObserver(() => {
      if (dialog.classList.contains("active")) {
        returnFocus = document.activeElement;
        focusable()[0]?.focus();
        document.body.style.overflow = "hidden";
      } else {
        document.body.style.overflow = "";
        if (returnFocus?.isConnected) returnFocus.focus();
      }
    }).observe(dialog, { attributes: true, attributeFilter: ["class"] });
    dialog.addEventListener("click", event => { if (event.target === dialog) dialog.classList.remove("active"); });
    document.addEventListener("keydown", event => {
      if (!dialog.classList.contains("active")) return;
      if (event.key === "Escape") { event.preventDefault(); dialog.classList.remove("active"); }
      if (event.key !== "Tab") return;
      const items = focusable();
      if (!dialog.contains(document.activeElement)) { event.preventDefault(); (event.shiftKey ? items.at(-1) : items[0])?.focus(); return; }
      if (event.shiftKey && document.activeElement === items[0]) { event.preventDefault(); items.at(-1)?.focus(); }
      else if (!event.shiftKey && document.activeElement === items.at(-1)) { event.preventDefault(); items[0]?.focus(); }
    });
  });
});
