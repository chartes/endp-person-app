/*
 * Main function to customize specific fields in person form.
 * e-NDP DB administration
 * 2023 - L. Terriel (ENC)
 */
$(document).ready(function () {
    // Select the elements with class 'input-select-tag-form-1' and 'input-select-tag-form-2'
    let selectForename = $('.input-select-tag-form-1');
    let selectSurname = $('.input-select-tag-form-2');

    // Get the pref label of the person
    let pref_label = $('#pref_label').val();

    /**
     * Function to fetch alternative labels from the server and populate a select element (Select2).
     * @param {jQuery} selectElement - The jQuery object representing the select element.
     * @param {string} typeLabel - The type of label to fetch ('forename' or 'surname').
     * @param {string} prefLabel - The preferred label of the person to fetch alternate labels.
     */
    function fetchLabels(selectElement, typeLabel, prefLabel) {
        $.ajax({
            url: "/endp-person/endp-person/admin/person/get_persons_alt_labels/",
            type: 'POST',
            data: {
                type_label: typeLabel,
                person_pref_label: prefLabel
            },
            success: function (data) {
                // Set the fetched data as the value of the select element and trigger the 'change' event.
                selectElement.val(data).trigger("change");
            },
            error: function (data) {
                console.log(data);
            }
        });
    }

    /**
     * Function to configure a Select2 input with appropriate options and tokenization.
     * @param {jQuery} selectElement - The jQuery object representing the select element.
     */
    function configureSelect2(selectElement) {
        selectElement.select2({
            tags: [''], // Allow custom tags
            //multiple: true, // Allow multiple selections
            tokenSeparators: [';'], // Use semicolon as the token separator,
            separator: ';', // Use semicolon as the separator
        }).on('select2-open', function () {
            // Hide the results container when the select2 dropdown is opened.
            $('.select2-results').css('display', 'none');
        })
    }

    // Initialize the select2 inputs with correct tokenization and configuration.
    configureSelect2(selectForename);
    configureSelect2(selectSurname);



    // Fetch the alternate labels for the select2 inputs if 'pref_label' is not empty.
    if (pref_label !== '') {
        fetchLabels(selectForename, 'forename', pref_label);
        fetchLabels(selectSurname, 'surname', pref_label);
    }

    /**
     * Function to format the value of the image_url field.
     */

    function format_image_value() {
        let events = $('#events');
        let image_urls = events.find('textarea[id$="-image_url"]');
        image_urls.each(function () {
            let value = $(this).val();
            console.log(value);
            if (value) {
                let split_value = value.split(';');
                // this.value = split_value[0] + ';' + split_value[1];
                // block the textarea
                $(this).attr('disabled', true);
                // create a button to edit the value (clean the textarea)
                let button = $('<button type="button" class="btn btn-primary btn-sm">Remplacer l\'image</button>');
                $(this).after(button);
                button.click(function () {
                    confirm('Êtes-vous sûr de vouloir remplacer l\'image ? (l\'ancienne image sera supprimée)');
                    $(this).prev().attr('disabled', false);
                    // erase the value
                    $(this).prev().val('');
                    // remove the button
                    $(this).remove();
                });
            }
        });
    }
    format_image_value();

});


// Collections of KB URLs
const KB_URL_MAP = {
        "Wikidata": "www.wikidata.org/entity/<ID>",
        "Biblissima": "data.biblissima.fr/w/Item:<ID>",
        "VIAF": "www.viaf.org/viaf/<ID>/",
        "DataBnF": "data.bnf.fr/fr/<ID>/",
        "Studium Parisiense": "studium-parisiense.univ-paris1.fr/individus/<ID>",
        "Collecta": "www.collecta.fr/p/COL-IMG-<ID>",
};

/**
 * Function to fetch the correct URL string from a Select2 input based on the selected option.
 * @param {Event} event - The event object triggered by the Select2 input.
 */
function fetchCorrectUrlStringFromKbSelect(event) {
    // get id of the select2 input
    let UserKbSelected = event.id;
    // Extract the number from the ID
    let number = UserKbSelected.split('-')[1];
    // Get the value of the selected option
    let KbType = $(event).select2('val');
    // Format the string to get the correct input ID
    let formattedString = `#kb_links-${number}-url`;
    // Set the value of the input with the correct URL
    $(formattedString).val(KB_URL_MAP[KbType]);
}
