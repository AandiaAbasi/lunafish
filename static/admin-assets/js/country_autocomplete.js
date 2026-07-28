(function($) {
    $(document).ready(function () {

        // برای همه autocompleteهای جنگو
        $('.admin-autocomplete').each(function() {
            var el = $(this);

            // دیتای موجود جنگو
            var oldDataFunc = el.select2.defaults.defaults.ajax.data;

            el.select2({
                ajax: {
                    delay: 250,
                    data: function(params) {
                        var data = oldDataFunc(params);

                        // گرفتن country_id از data-attribute
                        var countryId = el.data("country-id");

                        if (countryId) {
                            data.country_id = countryId;
                        }

                        return data;
                    }
                }
            });

        });

    });
})(django.jQuery);
