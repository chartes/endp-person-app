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
    function openPreview(url) {
        let iframe = $('#imagePreview');
        console.log(iframe);
        console.log(url);
        iframe.attr({'src': url});
        $('#iframeContainer').attr('style', 'display: flex');
        $('#closePreview').on('click', function () {
            $('#iframeContainer').attr('style', 'display: none');
        });
    }

    /**
     * Function to add a Select2 input to the event subform to select an image from Nakala.
     */
    function addSelect2Image() {
        let idEventSelect = $('input[id^="events-"][id$="-image_url"]');
        fetch('/endp-person/endp-person/admin/person/get_nakala_images/').then(response => response.json()).then(data => {
            idEventSelect.each(function () {
                $(this).select2({
                    data: $.parseJSON(JSON.stringify(data)),
                    placeholder: 'Choisir une image',
                });
                // add a button to clear the select2 input add a id based on idEventSelect
                let idEventSelectClear = $(this).attr('id');
                let idEventSelectClearBtn = idEventSelectClear + '-clear';
                // if not exist add a button to clear the select2 input
                if (!$('#' + idEventSelectClearBtn).length) {
                    $(this).after('<br><button type="button" id="' + idEventSelectClearBtn + '" class="btn btn-danger btn-sm">Effacer l\'image</button><br>');
                    // listener when click on the button to clear the select2 input
                    $('#' + idEventSelectClearBtn).on('click', function () {
                        $('#' + idEventSelectClear).val(null).trigger('change');
                    });
                    // add a listener when change the value of the select2 input
                    $(this).on('change', function () {
                        console.log('change');
                    });
                    // create a button with id based on idEventSelect to open a preview of the image "openPreview-<idEventSelect>"
                    let idEventSelectPreviewBtn = 'openPreview-' + idEventSelectClear;
                    $(this).after('<br><button type="button" id="' + idEventSelectPreviewBtn + '" class="btn btn-primary btn-sm">Aperçu de l\'image</button>');
                    // listener when click on the button to open a preview of the image
                    $('#' + idEventSelectPreviewBtn).on('click', function () {
                       // get the value of the select2 input
                       let idEventSelectPreview = $('#' + idEventSelectClear).val();
                       console.log(idEventSelectPreview);
                          // if not empty open a preview of the image
                            if (idEventSelectPreview !== null) {
                                // split in ";" and get the second part of the string
                                let idEventSelectPreviewSplit = idEventSelectPreview.split(';');
                                let idEventSelectPreviewSplit2 = idEventSelectPreviewSplit[1];
                                let url = "https://api.nakala.fr/embed/10.34847/nkl.8bdfe89g/" + idEventSelectPreviewSplit2;
                                openPreview(url);
                                console.log(url);
                            }
                    });
                }
            });
        });
    }

    // listener when open a event subform to add a new event
    let idEventBtn = $('#events-button');
    idEventBtn.on('click', function () {
        addSelect2Image();
    });

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

