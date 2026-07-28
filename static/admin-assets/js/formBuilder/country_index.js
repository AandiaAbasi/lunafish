let DELETE_STEP_ID = null
const country_id = JSON.parse(
    document.getElementById("country-id").textContent
)

const csrf_token = JSON.parse(
    document.getElementById("csrf-token").textContent
)

const path = window.location.pathname.split("/");
const lang = path[1] || "en";

function loadSteps(){

    fetch(`/${lang}/api/form-builder/country/${country_id}/steps/`)
    .then(res => res.text())
    .then(html => {

        document.getElementById("steps-container").innerHTML = html

        enableStepDrag()
        enableAllFieldsDrag()

    })

}

function openStepForm(){
    document.getElementById("step-form").style.display = "block"
}

function addFieldRow(){

    let container = document.getElementById("fields-repeater")
    let row = container.children[0].cloneNode(true)

    row.querySelector(".conditional-toggle").style.display = "none"
    row.querySelector(".conditional-checkbox").checked = false

    container.appendChild(row)
    const select = row.querySelector('.field-select');
    updateConditionalToggle(select);
}

function removeField(button){

    const row = button.closest(".field-row")

    if(row){
        row.remove()
    }

}

function saveStep(step = null) {

    let rows = document.querySelectorAll(".field-row");

    console.log(csrf_token)
    let data = new FormData();

    rows.forEach(row => {

        let select = row.querySelector(".field-select");
        let checkbox = row.querySelector(".conditional-checkbox");

        let field_id = select.value;
        let is_cond = checkbox && checkbox.checked ? "true" : "false";

        data.append("fields[]", field_id);
        data.append("conditional[]", is_cond);
    });

    let url = `/${lang}/api/form-builder/country/${country_id}/steps/create/`;
    if (step) {
        url = `/${lang}/api/form-builder/country/${country_id}/steps/${step}/edit/`;
    }

    fetch(`${url}`, {
        method: "POST",
        body: data,
        headers: {
            "X-CSRFToken": csrf_token
        }
    })
    .then(res => res.json())
    .then(data => {
        loadSteps();
    });
}

function confirmDeleteStep(){

    fetch(`/${lang}/api/form-builder/country/${country_id}/steps/${DELETE_STEP_ID}/delete/`,{
        method:"POST",
        headers:{
            "X-CSRFToken": csrf_token
        }
    })
    .then(res=>res.json())
    .then(data=>{

        bootstrap.Modal.getInstance(
            document.getElementById("deleteStepModal")
        ).hide()

        loadSteps()

    })
}
function deleteStep(step){

    DELETE_STEP_ID = step

    const modal = new bootstrap.Modal(
        document.getElementById("deleteStepModal")
    )

    modal.show()
}

function editStep(step){

    fetch(`/${lang}/api/form-builder/country/${country_id}/steps/${step}/edit/`)
    .then(res=>res.text())
    .then(html=>{

        document.getElementById("step-form").style.display="block"
        document.getElementById("fields-repeater").innerHTML=html

        window.editingStep = step

    })

}

document.addEventListener("change", function(e){

    if(e.target.classList.contains("field-select")){

        const select = e.target
        const row = select.closest(".field-row")

        const selected = select.options[select.selectedIndex]
        const type = selected.dataset.type

        const toggle = row.querySelector(".conditional-toggle")
        updateConditionalToggle(e.target);
        if(type === "radioButton"){
            toggle.style.display = "flex"
        }else{
            toggle.style.display = "none"
            row.querySelector(".conditional-checkbox").checked = false
        }

    }

})

let stepSortable = null;

function enableStepDrag() {

    const container = document.getElementById("steps-list");
    if (!container) return;

    if (stepSortable && stepSortable.el !== container) {
        stepSortable.destroy();
        stepSortable = null;
    }

    if (!stepSortable) {
        stepSortable = new Sortable(container, {
            animation: 150,
            draggable: ".step-item",
            handle: ".step-header",

            onEnd: function () {

                const order = [];

                container.querySelectorAll(".step-item").forEach((el, i) => {
                    order.push({
                        step: parseInt(el.dataset.step),
                        new_step: i + 1
                    });
                });

                fetch(`/${lang}/api/form-builder/country/${country_id}/steps/reorder/`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrf_token
                    },
                    body: JSON.stringify(order)
                }).then(()=>loadSteps());
            }
        });
    }
}

let fieldSortables = {};

function enableAllFieldsDrag() {

    document.querySelectorAll(".fields-list").forEach(list => {
        const stepId = list.dataset.step;

        if (fieldSortables[stepId] && fieldSortables[stepId].el !== list) {
            fieldSortables[stepId].destroy();
            delete fieldSortables[stepId];
        }

        if (!fieldSortables[stepId]) {
            fieldSortables[stepId] = new Sortable(list, {
                animation: 150,
                draggable: ".field-item",
                handle: ".field-handle",

                onEnd: function () {
                    const order = [];
                    list.querySelectorAll(".field-item").forEach((el, i) => {
                        order.push({
                            id: el.dataset.id,
                            sort: i + 1
                        });
                    });

                    fetch(`/${lang}/api/form-builder/country/${country_id}/fields/reorder/`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": csrf_token
                        },
                        body: JSON.stringify({
                            step: stepId,
                            order: order
                        })
                    });
                }
            });
        }
    });
}

document.addEventListener("DOMContentLoaded",function(){
    loadSteps()
})

function updateConditionalToggle(select) {

    const row = select.closest('.field-row');
    const toggle = row.querySelector('.conditional-toggle');
    const type = select.options[select.selectedIndex]?.dataset?.type;

    if (type === 'radioButton') {
        toggle.style.display = 'flex';
    } else {
        toggle.style.display = 'none';
        const checkbox = row.querySelector('.conditional-checkbox');
        if (checkbox) checkbox.checked = false;
    }

}
function openConditional(countryFieldId){

    window.location.href =
        `/${lang}/api/form-builder/country-field/${countryFieldId}/conditionals/`;

}
