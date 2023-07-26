/*
 * Quill editor custom config (person form).
 * e-NDP DB administration
 * 2023 - L. Terriel (ENC)
 */
$(document).ready(function () {
    // Quill editor options for the toolbar
    const TOOLBAR_OPTIONS = [
        ['bold', 'italic', 'underline', 'strike', 'script'],
        [{'script': 'super'}],
        ['clean']
    ];

    // List of textarea id that will be converted to quill editor
    const TEXTAREA_TO_QUILL = [
        'comment',
        'bibliography'
    ];

    TEXTAREA_TO_QUILL.forEach(function (textAreaId) {
        // create a selector where the quill editor will be created
        var commentTextAreaField = $(`#${textAreaId}`);
        // get the actual value of the textarea
        var actualTextAreaValue = commentTextAreaField.val();
        // Create a div element that contains the quill editor
        var div = document.createElement('div');
        // add id to the div element for exemple quill-editor-1 ...
        div.setAttribute('id', `quill-editor-${textAreaId}`);
        // add the div element after the textarea element
        commentTextAreaField.parent().append(div, commentTextAreaField);
        // create the quill editor instance
        var quill = new Quill(`#quill-editor-${textAreaId}`, {
            modules: {
                toolbar: TOOLBAR_OPTIONS,
                // ignore backspace for autolist
                keyboard: {
                    bindings: {
                        'list autofill': {
                            prefix: /^\s*()$/,
                        }
                    }
                }
            },
            theme: 'snow',
            placeholder: "Ajouter du texte ici ...",
        });
        // set value of current element to the quill editor content
        quill.root.innerHTML = actualTextAreaValue;
        // add event listener to quill instance to copy the content of the quill editor to the textarea
        quill.on('text-change', function (delta, oldDelta, source) {
            // set value of current element to the quill editor content
            if (source === 'user') {
                commentTextAreaField.val(quill.root.innerHTML);
            }
        });
        // finally, hide the textarea
        commentTextAreaField.hide();
    });
});
