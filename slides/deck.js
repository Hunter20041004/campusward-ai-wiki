(() => {
  "use strict";
  const host = document.querySelector("#slide-host");
  const previous = document.querySelector("#prev");
  const next = document.querySelector("#next");
  const overview = document.querySelector("#overview");
  const pageStatus = document.querySelector("#page-status");
  if (!host || !previous || !next || !overview || !pageStatus) return;

  const el = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = String(text);
    if (className) node.className = className;
    return node;
  };
  const teachingNotice = "固定教學示意，不連線 AI、不代表正式課程";

  function makeDemo() {
    const demo = el("div", undefined, "teaching-demo");
    demo.append(el("p", teachingNotice, "demo-notice"));
    const layout = el("div", undefined, "demo-layout");
    const settings = el("div", undefined, "demo-settings");
    settings.append(el("h3", "先固定一門，再比較另一門"));
    settings.append(el("p", "已排示意課 A「資料思考」：週二 2–3 節，3 學分", "fixed-course"));
    const label = el("label", "想搭配哪一班？");
    label.htmlFor = "demo-section";
    const section = el("select");
    section.id = "demo-section";
    const options = [
      ["B1", "B1 設計入門｜週二 3–4 節，3 學分"],
      ["B2", "B2 設計入門另一班｜週三 3–4 節，3 學分"],
    ];
    for (const [value, text] of options) {
      const option = el("option", text);
      option.value = value;
      section.append(option);
    }
    const freeLabel = el("label", undefined, "checkbox-label");
    const freeDay = el("input");
    freeDay.id = "demo-free-day";
    freeDay.type = "checkbox";
    freeLabel.htmlFor = freeDay.id;
    freeLabel.append(freeDay, el("span", "保留週三，不排課"));
    const check = el("button", "檢查這個組合", "primary");
    check.id = "check-plan";
    check.type = "button";
    settings.append(label, section, freeLabel, check);

    const timetable = el("table", undefined, "demo-timetable");
    timetable.append(el("caption", "示意時段比較：A 是固定課，B 是待檢查的班"));
    const head = el("thead");
    const headRow = el("tr");
    for (const title of ["節次", "週二", "週三"]) {
      const cell = el("th", title);
      cell.scope = "col";
      headRow.append(cell);
    }
    head.append(headRow);
    const tbody = el("tbody");
    const cells = new Map();
    for (const period of [2, 3, 4]) {
      const row = el("tr");
      const heading = el("th", `${period} 節`);
      heading.scope = "row";
      row.append(heading);
      for (const day of [2, 3]) {
        const cell = el("td");
        cells.set(`${day}-${period}`, cell);
        row.append(cell);
      }
      tbody.append(row);
    }
    timetable.append(head, tbody);
    const result = el("div", "選一班後按檢查，這裡會寫出判定和原因", "demo-result");
    result.id = "demo-result";
    result.setAttribute("aria-live", "polite");
    result.setAttribute("aria-atomic", "true");
    const courseA = { name: "資料思考", day: 2, periods: [2, 3] };
    const courseB = () => section.value === "B2"
      ? { name: "設計入門另一班", day: 3, periods: [3, 4] }
      : { name: "設計入門", day: 2, periods: [3, 4] };
    function draw() {
      const b = courseB();
      for (const [key, cell] of cells) {
        const [day, period] = key.split("-").map(Number);
        const hasA = courseA.day === day && courseA.periods.includes(period);
        const hasB = b.day === day && b.periods.includes(period);
        cell.replaceChildren();
        cell.className = "";
        if (hasA) cell.append(el("span", "A 資料思考", "course-block"));
        if (hasB) cell.append(el("span", `B ${b.name}`, "course-block candidate"));
        if (hasA && hasB) {
          cell.classList.add("conflict-cell");
          cell.append(el("span", "同節衝堂", "cell-note"));
        } else if (freeDay.checked && day === 3) {
          cell.classList.add("free-day-cell");
          cell.append(el("span", hasB ? "佔用空堂日" : "保留空堂", "cell-note"));
        } else if (!hasA && !hasB) cell.append(el("span", "—", "empty-slot"));
      }
    }
    const resetResult = () => {
      draw();
      result.className = "demo-result";
      result.textContent = "條件已更新，按「檢查這個組合」看判定";
    };
    section.addEventListener("change", resetResult);
    freeDay.addEventListener("change", resetResult);
    check.addEventListener("click", () => {
      const b = courseB();
      const overlap = courseA.day === b.day ? courseA.periods.filter((period) => b.periods.includes(period)) : [];
      const usesFreeDay = freeDay.checked && b.day === 3;
      result.replaceChildren();
      let title;
      let reason;
      if (overlap.length) {
        title = "拒絕：兩門課衝堂";
        reason = `「資料思考」與「${b.name}」都用到週二第 ${overlap.join("、")} 節，換班後再檢查。`;
        result.className = "demo-result error";
      } else if (usesFreeDay) {
        title = "拒絕：佔用保留的空堂日";
        reason = "這一班和 A 沒有衝堂，但排在你想空下來的週三，取消保留或換別的班。";
        result.className = "demo-result error";
      } else {
        title = "可排入示意課表";
        reason = "兩門課的節次沒有重疊，也沒有佔用保留的空堂日，合計 6 學分；這次只驗證這兩項規則。";
        result.className = "demo-result success";
      }
      result.append(el("strong", title), el("p", reason), el("p", "這是本頁的固定資料計算，沒有修改正式課表或送出選課。", "demo-limit"));
    });
    draw();
    layout.append(settings, timetable);
    demo.append(layout, result);
    return demo;
  }

  function makeQuiz(question, slideId) {
    const quiz = el("fieldset", undefined, "quiz");
    quiz.append(el("legend", question.text));
    const choices = el("div", undefined, "quiz-choices");
    const feedback = el("div", "選一個答案，看看為什麼", "quiz-feedback");
    feedback.id = `${slideId}-feedback`;
    feedback.setAttribute("aria-live", "polite");
    feedback.setAttribute("aria-atomic", "true");
    question.choices.forEach((choice, index) => {
      const button = el("button", choice, "quiz-choice");
      button.type = "button";
      button.setAttribute("aria-describedby", feedback.id);
      button.setAttribute("aria-pressed", "false");
      button.addEventListener("click", () => {
        const correct = index === question.answer;
        for (const item of choices.children) {
          item.classList.remove("selected-correct", "selected-wrong");
          item.setAttribute("aria-pressed", "false");
        }
        button.classList.add(correct ? "selected-correct" : "selected-wrong");
        button.setAttribute("aria-pressed", "true");
        feedback.className = `quiz-feedback ${correct ? "success" : "error"}`;
        feedback.replaceChildren(el("strong", correct ? "答對了" : "再想一下"), el("p", question.explanation));
      });
      choices.append(button);
    });
    quiz.append(choices, feedback);
    return quiz;
  }

  async function start() {
    host.append(el("p", "正在讀取教學內容…", "deck-loading"));
    const response = await fetch("../content.json");
    if (!response.ok) throw new Error(`內容讀取失敗（${response.status}）`);
    const content = await response.json();
    if (!Array.isArray(content.slides) || !content.slides.length) throw new Error("找不到投影片內容");
    const slides = content.slides;
    const wiki = new Map((content.wiki || []).map((entry) => [entry.id, entry.title]));
    const sections = [];
    host.replaceChildren();
    slides.forEach((slide, index) => {
      const section = el("section", undefined, `slide slide-${slide.kind || "text"}`);
      section.id = slide.id;
      section.setAttribute("aria-labelledby", `${slide.id}-title`);
      section.append(el("p", `${String(index + 1).padStart(2, "0")} / ${String(slides.length).padStart(2, "0")}`, "slide-number"));
      const title = el("h1", slide.title);
      title.id = `${slide.id}-title`;
      title.tabIndex = -1;
      section.append(title);
      if (slide.lead) section.append(el("p", slide.lead, "slide-lead"));
      const body = el("div", undefined, "slide-body");
      for (const paragraph of slide.body || []) body.append(el("p", paragraph));
      section.append(body);
      if (Array.isArray(slide.steps)) {
        const steps = el("ol", undefined, "flow slide-flow");
        for (const step of slide.steps) {
          const item = el("li");
          item.append(el("h3", step.title), el("p", step.text));
          steps.append(item);
        }
        section.append(steps);
      }
      if (slide.demo || slide.kind === "demo") section.append(makeDemo());
      if (slide.question) section.append(makeQuiz(slide.question, slide.id));
      const sources = el("details", undefined, "slide-sources");
      sources.append(el("summary", "Wiki 出處與核對編號"));
      const links = el("ul");
      for (const slug of slide.wiki || []) {
        if (!/^[a-z\d-]+$/i.test(slug)) continue;
        const item = el("li");
        const link = el("a", wiki.get(slug) || slug);
        link.href = `../wiki/${slug}.html`;
        item.append(link);
        links.append(item);
      }
      sources.append(links);
      if (slide.claims?.length) sources.append(el("p", `核對編號：${slide.claims.join("、")}，內容與來源對照見 Wiki。`));
      section.append(sources);
      host.append(section);
      sections.push(section);
    });

    let current = 0;
    let expanded = false;
    function indexFromHash() {
      let id;
      try { id = decodeURIComponent(location.hash.slice(1)); } catch { return -1; }
      return slides.findIndex((slide) => slide.id === id);
    }
    function render({ focus = false, updateHash = true } = {}) {
      sections.forEach((section, index) => { section.hidden = !expanded && index !== current; });
      host.classList.toggle("is-overview", expanded);
      document.body.classList.toggle("deck-overview", expanded);
      previous.disabled = current === 0;
      next.disabled = current === slides.length - 1;
      overview.textContent = expanded ? "回到單頁" : "全部展開";
      overview.setAttribute("aria-pressed", String(expanded));
      pageStatus.textContent = expanded ? `全部 ${slides.length} 頁 · 目前第 ${current + 1} 頁` : `${current + 1} / ${slides.length}`;
      document.title = `${slides[current].title}｜Campusward 教學`;
      if (updateHash && location.hash !== `#${slides[current].id}`) history.replaceState(null, "", `#${slides[current].id}`);
      if (focus) {
        sections[current].querySelector("h1").focus({ preventScroll: true });
        if (expanded) sections[current].scrollIntoView({ block: "start" });
        else window.scrollTo({ top: 0, behavior: "instant" });
      }
    }
    const go = (index) => {
      if (index < 0 || index >= slides.length) return;
      current = index;
      render({ focus: true });
    };
    previous.addEventListener("click", () => go(current - 1));
    next.addEventListener("click", () => go(current + 1));
    overview.addEventListener("click", () => { expanded = !expanded; render(); });
    document.addEventListener("keydown", (event) => {
      if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || event.defaultPrevented) return;
      if (event.target.closest("input, select, textarea, [contenteditable='true']")) return;
      const destination = { ArrowLeft: current - 1, ArrowRight: current + 1, Home: 0, End: slides.length - 1 }[event.key];
      if (destination === undefined) return;
      event.preventDefault();
      go(destination);
    });
    window.addEventListener("hashchange", () => {
      const index = indexFromHash();
      if (index >= 0) { current = index; render({ focus: true, updateHash: false }); }
    });
    const initial = indexFromHash();
    if (initial >= 0) current = initial;
    render();
  }

  start().catch((error) => {
    host.replaceChildren(el("h1", "教學內容尚未載入"), el("p", error.message), el("p", "請透過本機預覽網址開啟這份網站，再重新整理；直接點開檔案可能無法讀取投影片資料。"));
    const retry = el("button", "重新載入");
    retry.type = "button";
    retry.addEventListener("click", () => location.reload());
    host.append(retry);
    previous.disabled = true;
    next.disabled = true;
    overview.disabled = true;
    pageStatus.textContent = "載入失敗";
  });
})();
