document.addEventListener("change", function(e) {

    if (e.target.name.includes("field")) {
        const row = e.target.closest("tr");

        const typeInput = row.querySelector("input[name$='type']");
        const conditional = row.querySelector("input[name$='is_conditional']");

        if (!typeInput || !conditional) return;

        if (typeInput.value === "radioButton") {
            conditional.closest(".form-row").style.display = "block";
        } else {
            conditional.closest(".form-row").style.display = "none";
        }

    }

});
