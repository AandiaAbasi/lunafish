let DELETE_STEP = null
let DELETE_FIELD_DETAIL = null

const csrf_token = JSON.parse(
    document.getElementById("csrf-token").textContent
)

const path = window.location.pathname.split("/");
const lang = path[1] || "en";
console.log(lang)
const categoryFieldId = document.getElementById("category_field_id").value;
function loadConditionalSteps(){


    fetch(`/${lang}/api/form-builder/category-field/${categoryFieldId}/conditionals/steps/`)
        .then(res => res.text())
        .then(html => {

            document.getElementById("conditionalStepsContainer").innerHTML = html;

        });

}

document.addEventListener("DOMContentLoaded", function(){

    loadConditionalSteps();

});

document.addEventListener("DOMContentLoaded", function () {
    loadConditionalSteps();
});


function collectConditionalFields() {

    const rows = document.querySelectorAll("#conditional-fields-container .field-row")

    const fields = []
    const conditionals = []

    rows.forEach(row => {

        const fieldId = row.querySelector(".field-select").value
        const conditional = row.querySelector(".conditional-checkbox")?.checked

        fields.push(fieldId)
        conditionals.push(conditional ? "1" : "0")

    })

    return {fields, conditionals}
}





function openCreateConditionalStep(fieldDetailId) {

    fetch(`/${lang}/api/form-builder/category-field/${categoryFieldId}/conditionals/steps/form/?field_detail_id=${fieldDetailId}`)
        .then(res => res.text())
        .then(html => {

            document.getElementById("conditionalModalBody").innerHTML = html;

            const modal = new bootstrap.Modal(document.getElementById("conditionalModal"));
            modal.show();
        });
}



function openConditionalStepEdit(fieldDetailId, step) {

    fetch(`/${lang}/api/form-builder/category-field/${categoryFieldId}/conditionals/steps/${step}/edit/?field_detail_id=${fieldDetailId}`)
        .then(res => res.text())
        .then(html => {

            document.getElementById("conditionalModalBody").innerHTML = html;

            const modal = new bootstrap.Modal(document.getElementById("conditionalModal"));
            modal.show();
        });
}



function saveConditionalStep() {

    const form = document.getElementById("conditionalStepForm")
    const formData = new FormData(form)

    const step = formData.get("step")

    let url

    if (step) {
        url = `/${lang}/api/form-builder/category-field/${categoryFieldId}/conditionals/steps/${step}/edit/`
    } else {
        url = `/${lang}/api/form-builder/category-field/${categoryFieldId}/conditionals/steps/create/`
    }

    fetch(url,{
        method:"POST",
        body:formData,
        headers:{
            "X-CSRFToken":csrf_token
        }
    })
    .then(res=>res.json())
    .then(data=>{

        if(data.success){

            bootstrap.Modal.getInstance(
                document.getElementById("conditionalModal")
            ).hide()

            loadConditionalSteps()
        }

    })
}


function deleteConditionalStep(fieldDetailId, step) {

    DELETE_STEP = step
    DELETE_FIELD_DETAIL = fieldDetailId

    const modal = new bootstrap.Modal(
        document.getElementById("deleteConditionalModal")
    )

    modal.show()
}
function confirmDeleteConditionalStep(){

    const formData = new FormData()
    formData.append("field_detail_id", DELETE_FIELD_DETAIL)

    fetch(`/${lang}/api/form-builder/category-field/${categoryFieldId}/conditionals/steps/${DELETE_STEP}/delete/`,{
        method:"POST",
        body:formData,
        headers:{
            "X-CSRFToken":csrf_token
        }
    })
    .then(res=>res.json())
    .then(data=>{

        if(data.success){

            bootstrap.Modal.getInstance(
                document.getElementById("deleteConditionalModal")
            ).hide()

            loadConditionalSteps()
        }

    })
}

function submitCreateConditionalStep() {

    const fieldDetailId = document.getElementById("conditional-field-detail-id").value
    const categoryFieldId = CURRENT_CATEGORY_FIELD_ID

    const data = collectConditionalFields()

    const formData = new FormData()

    formData.append("category_field_id", categoryFieldId)
    formData.append("field_detail_id", fieldDetailId)

    data.fields.forEach(v => formData.append("fields[]", v))
    data.conditionals.forEach(v => formData.append("conditional[]", v))

    fetch("/formfield/conditional/step/create/", {
        method: "POST",
        body: formData
    })
}
function addConditionalFieldRow(){

    const container = document.getElementById("conditional-fields-container")

    let first = container.querySelector(".field-row")

    if(!first){

    const fields = window.availableFields || []

    let options = ""

    fields.forEach(f=>{
    options += `<option value="${f.id}" data-type="${f.type}">${f.title}</option>`
    })

    const html = `
    <div class="field-row" style="display:flex;gap:10px;margin-bottom:10px;align-items:center;">

    <select name="fields[]" class="field-select  form-select">
    ${options}
    </select>

    <button type="button" class="btn btn-remove" onclick="removeConditionalField(this)">
    Remove
    </button>

    </div>
    `

    container.insertAdjacentHTML("beforeend", html)

    return
}

const clone = first.cloneNode(true)

clone.querySelector("select").selectedIndex = 0

container.appendChild(clone)

}

function removeConditionalField(btn){

const row = btn.closest(".field-row")

row.remove()

}