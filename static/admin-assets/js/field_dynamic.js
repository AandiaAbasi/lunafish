document.addEventListener("DOMContentLoaded", function () {
    const typeField = document.querySelector("#id_type");
    if (!typeField) return;

    function hide(selector) {
        const el = document.querySelector(selector);
        if (el) {
            const row = el.closest(".form-row");
            if (row) row.style.display = "none";
        }
    }

    function show(selector) {
        const el = document.querySelector(selector);
        if (el) {
            const row = el.closest(".form-row");
            if (row) row.style.display = "";
        }
    }

    function updateVisibility() {
        const type = typeField.value;

        // همگی را اول مخفی می‌کنیم
        hide("#id_des");
        hide("#id_image_path");
        hide("#id_icon_name");
        hide("#id_is_required");
        hide("#id_is_package");

        // des → visible وقتی type ≠ image و type ≠ description
        if (!["image", "description"].includes(type)) {
            show("#id_des");
        }

        // image_path → فقط وقتی type == image
        if (type === "image") {
            show("#id_image_path");
        }

        // icon_name → فقط وقتی type ≠ image و type ≠ description
        if (!["image", "description"].includes(type)) {
            show("#id_icon_name");
        }

        // is_required → وقتی type in [counter, checkbox, radioButton]
        if (["counter", "checkbox", "radioButton"].includes(type)) {
            show("#id_is_required");
        }

        // is_package → فقط counter
        if (type === "counter") {
            show("#id_is_package");
        }
    }

    updateVisibility();
    typeField.addEventListener("change", updateVisibility);
});
