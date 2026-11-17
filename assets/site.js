(() => {
  "use strict";
  const search = document.querySelector("#search-wiki");
  if (!search) return;
  const entries = [...document.querySelectorAll(".wiki-entry[data-search]")];
  const count = document.querySelector("#search-count");
  const filter = () => {
    const terms = search.value.trim().normalize("NFKC").toLocaleLowerCase("zh-TW").split(/\s+/).filter(Boolean);
    let visible = 0;
    for (const entry of entries) {
      const haystack = `${entry.dataset.search} ${entry.textContent}`.normalize("NFKC").toLocaleLowerCase("zh-TW");
      entry.hidden = !terms.every((term) => haystack.includes(term));
      if (!entry.hidden) visible += 1;
    }
    if (count) count.textContent = visible ? `顯示 ${visible} / ${entries.length} 個條目` : "找不到符合的條目，試試「排課」「課綱」或清除搜尋";
  };
  search.addEventListener("input", filter);
  filter();
})();
