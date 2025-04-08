/*
 * Main function to customize specific fields in person form.
 * e-NDP DB administration
 * 2023 - L. Terriel (ENC)
 */

$(document).ready(function () {
    const BASE_URL = "/endp-person/endp-person/admin/person/";
    const API_NAKALA_API = "https://api.nakala.fr/";


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
            url: `${BASE_URL}get_persons_alt_labels/`,
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
            selectElement.data('select2').results.hide();
            // $('.select2-results').css('display', 'none');
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
     * Displays an image preview using an iframe.
     * @param {string} url - The URL of the image to be previewed.
     */
    function openPreview(url) {
        const iframe = $('#imagePreview');
        iframe.attr({'src': url});
        $('#iframeContainer').attr('style', 'display: flex');
        $('#closePreview').on('click', function () {
            // Closes the preview on click.
            $('#iframeContainer').attr('style', 'display: none');
        });
    }


    /**
     * Adds a Select2 input to the event subform to select an image from Nakala.
     * Fetches available images from Nakala and configures the Select2 input accordingly.
     */
    function addSelect2Image() {
        $('input[id^="events-"][id$="-image_url"]').each(function () {
            const select = $(this);
            select.select2({
                placeholder: 'Rechercher...',
                initSelection: function (element, callback) {
                    // Initializes the selection based on the current value of the select element.
                    const id = element.val();
                    callback({id: id, text: id});
                },
                formatSelection: selectData => selectData.text.split(';')[1],
                formatResult: selectData => {
                    // Formats the result based on its content.
                    return selectData.children ? selectData.text : selectData.text.split(';')[1];
                },
                ajax: {
                    url: `${BASE_URL}get_nakala_images/`,
                    dataType: 'json',
                    type: "GET",
                    quietMillis: 250,
                    cache: true,
                    data: function (params) {
                        return {
                            q: params || "",
                        };
                    },
                    results: function (data) {
                        return {results: data};
                    },
                },
            });


            createButtons(select);
        });
    }


    /**
     * Generates 'clear' and 'preview' buttons for a given Select2 input.
     * @param {jQuery} selectElement - The jQuery object representing the select element.
     */
    function createButtons(selectElement) {
        const idEventSelectClear = selectElement.attr('id');
        const idEventSelectClearBtn = `${idEventSelectClear}-clear`;
        const idEventSelectPreviewBtn = `openPreview-${idEventSelectClear}`;

        // Ensures buttons are only created once.
        if (!$(`#${idEventSelectClearBtn}`).length) {
            selectElement.after(`
            <button type="button" id="${idEventSelectClearBtn}" class="btn btn-danger btn-sm" style="margin-right: 10px !important; margin-top: 5px !important;">Effacer l'image</button>
            <button type="button" id="${idEventSelectPreviewBtn}" class="btn btn-primary btn-sm" style=" margin-top: 5px !important;">Aperçu de l'image</button>
        `);

            // Hide buttons if the selectElement has no value.
            if (!selectElement.val()) {
                $(`#${idEventSelectClearBtn}`).hide();
                $(`#${idEventSelectPreviewBtn}`).hide();
            }

            // Show/Hide buttons on selectElement change.
            selectElement.on('change', function () {
                if ($(this).val()) {
                    $(`#${idEventSelectClearBtn}`).show();
                    $(`#${idEventSelectPreviewBtn}`).show();
                } else {
                    $(`#${idEventSelectClearBtn}`).hide();
                    $(`#${idEventSelectPreviewBtn}`).hide();
                }
            });

            $(`#${idEventSelectClearBtn}`).on('click', function () {
                // Clears the Select2 input when the 'clear' button is clicked.
                $(`#${idEventSelectClear}`).val(null).trigger('change');
            });

            $(`#${idEventSelectPreviewBtn}`).on('click', async function () {
                // Generates a preview when the 'preview' button is clicked.
                const selectedValue = $(`#${idEventSelectClear}`).val();
                if (selectedValue) {
                    const [register_identifier, , image_sha1] = selectedValue.split(';');
                    try {
                        const response = await fetch(`${BASE_URL}get_nakala_data_identifiers/`, {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({register_identifier})
                        });
                        const data = await response.json();
                        const url = `${API_NAKALA_API}embed/${data.nakala_identifier}/${image_sha1}`;
                        openPreview(url);
                    } catch (error) {
                        console.error(error);
                    }
                }
            });
        }
    }


    // listener when open a event subform to add a new event
    $('#events-button').on('click', addSelect2Image);
    addSelect2Image();
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

