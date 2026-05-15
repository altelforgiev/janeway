document.addEventListener("DOMContentLoaded", function() {
    // Ищем все таблицы внутри статьи
    var articleBody = document.getElementById("main_article") || document.querySelector("[itemprop='articleBody']");
    if (!articleBody) return;

    var tables = articleBody.querySelectorAll("table");

    tables.forEach(function(table) {
        // 1. Добавляем классы для красивого оформления (Foundation/Bootstrap)
        // Эти классы добавят границы, полосатый фон и отступы
        table.classList.add("table", "table-bordered", "table-striped", "hover");

        // 2. Делаем таблицы адаптивными (горизонтальный скролл на мобильных)
        // Проверяем, не обернута ли уже таблица в адаптивный блок
        if (!table.parentElement.classList.contains("table-scroll")) {
            var wrapper = document.createElement("div");
            wrapper.classList.add("table-scroll"); // Класс Foundation для скролла таблиц

            // Если вы используете Bootstrap (зависит от темы), то класс может быть 'table-responsive'
            // На всякий случай добавим оба
            wrapper.classList.add("table-responsive");

            // Оборачиваем таблицу
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }

        // 3. Выравниваем текст в заголовках таблиц (опционально)
        var ths = table.querySelectorAll("th");
        ths.forEach(function(th) {
            th.style.textAlign = "center";
            th.style.verticalAlign = "middle";
        });
    });
});