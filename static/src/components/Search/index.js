const getEl = (id) => document.getElementById(id);

const init = ({
  onSessionsQueryChange,
  onSessionsClear,
  onNewsQueryChange,
  onNewsClear,
} = {}) => {
  const q = getEl("q");
  const clearQ = getEl("clearQ");
  const newsQ = getEl("newsQ");
  const clearNewsQ = getEl("clearNewsQ");

  if (q) {
    q.addEventListener("input", () => {
      const val = String(q.value || "");
      if (typeof onSessionsQueryChange === "function") onSessionsQueryChange(val);
    });
  }
  if (clearQ) {
    clearQ.addEventListener("click", () => {
      if (q) {
        q.value = "";
        q.focus();
      }
      if (typeof onSessionsClear === "function") onSessionsClear();
    });
  }
  if (newsQ) {
    newsQ.addEventListener("input", () => {
      const val = String(newsQ.value || "");
      if (typeof onNewsQueryChange === "function") onNewsQueryChange(val);
    });
  }
  if (clearNewsQ) {
    clearNewsQ.addEventListener("click", () => {
      if (newsQ) {
        newsQ.value = "";
        newsQ.focus();
      }
      if (typeof onNewsClear === "function") onNewsClear();
    });
  }
};

export default {
  init,
};
