document.addEventListener("DOMContentLoaded", function() {
    var tocList = document.getElementById("toc");
    if (!tocList) return;

    // Переносим ID с <sec> на <h2> и добавляем классы
    document.querySelectorAll("sec, div.article-section, section").forEach(function(wrapper) {
        var heading = wrapper.querySelector("h1, h2, h3");
        if (heading && wrapper.id && wrapper.id.startsWith("sec")) {
            heading.id = wrapper.id;
            heading.classList.add("section", "scrollspy");
            wrapper.removeAttribute("id");
        }
    });

    var articleBody = document.getElementById("main_article") || document.querySelector("[itemprop='articleBody']");
    if (!articleBody) return;

    var headings = articleBody.querySelectorAll("h2");
    tocList.innerHTML = "";

    headings.forEach(function(heading, index) {
        if (!heading.id) {
            heading.id = "sec" + (index + 1);
        }

        var li = document.createElement("li");
        var a = document.createElement("a");
        a.href = "#" + heading.id;
        a.textContent = heading.textContent;
        a.classList.add("scroll-link");

        li.appendChild(a);
        tocList.appendChild(li);
    });

    if (headings.length === 0) {
        var tocSection = document.getElementById("toc-section");
        if (tocSection) tocSection.style.display = "none";
    }
});