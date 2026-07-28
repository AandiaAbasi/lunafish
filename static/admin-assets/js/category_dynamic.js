document.addEventListener("DOMContentLoaded", function () {

    if (!window.django || !django.jQuery) {
        return;
    }

    var $ = django.jQuery;

    $('.admin-autocomplete').each(function () {

        var el = $(this);
        var countryId = el.data("country-id");

        if (!countryId) return;

        var select2 = el.data('select2');
        if (!select2) return;

        var ajax = select2.options.options.ajax;
        var oldData = ajax.data;

        ajax.data = function(params) {

            var data = oldData ? oldData(params) : params;
            data.country_id = countryId;

            return data;
        };

    });

});
