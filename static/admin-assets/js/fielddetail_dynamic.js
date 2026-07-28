document.addEventListener("DOMContentLoaded", function () {

    const typeInput = document.querySelector("#id_type");
    if (!typeInput) return;

    function getType() {
        return typeInput.value;
    }

    function toggle(element, show) {
        if (!element) return;
        const row = element.closest(".form-row") || element.closest(".inline-related");
        if (row) row.style.display = show ? "" : "none";
    }

    function updateAllInlines() {
        const type = getType();
        document.querySelectorAll(".inline-related").forEach(function (inline) {
            toggle(inline.querySelector("[id$='second_title']"), type === "input");
            toggle(inline.querySelector("[id$='is_required']"), type === "input");
            toggle(inline.querySelector("[id$='image_path']"), type === "image");

            toggle(inline.querySelector("[id$='score']"), ["counter","checkbox","radioButton"].includes(type));
            toggle(inline.querySelector("[id$='show_score']"), ["counter","checkbox","radioButton"].includes(type));

            toggle(inline.querySelector("[id$='is_checked']"), type === "checkbox");
            toggle(inline.querySelector("[id$='is_jalaali']"), type === "datepicker");

            toggle(inline.querySelector("[id$='has_counter']"), ["checkbox","radioButton"].includes(type));

            toggle(inline.querySelector("[id$='icon_name']"), ["input","description"].includes(type));

            toggle(inline.querySelector("[id$='guide']"), ["counter","checkbox","radioButton","description","input"].includes(type));

            toggle(inline.querySelector("[id$='des']"), ["description","input","checkbox","radioButton"].includes(type));

        });
    }

    typeInput.addEventListener("change", updateAllInlines);

    document.addEventListener("formset:added", function () {
        updateAllInlines();
    });

    updateAllInlines();
});
