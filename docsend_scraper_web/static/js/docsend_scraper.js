var DOC_INFO_CACHE = {};

var iconExplainText = {
    downloading: "Processing ...",
    complete: "Complete",
    attention: "Information Required",
    download: "Click to Download",
    invalid: "Invalid Entry",
    error: "Inputs are incorrect"
}

/**
 * Collects the entries from the text area and process them to be used elsewhere.
 *
 * Once elements are collected, this will check the ids, add the panels, and inform
 * of any errors.
 **/
function collectEntriesFromInput(){
    var textArea= $("#document-entry");
    var inputs = textArea.val().split('\n');

    var proccesedDocIdInfo = processRawTextToDocIds(inputs);
    var docIds = proccesedDocIdInfo[0]
    var invalidEntries = proccesedDocIdInfo[1];

    if (docIds.length > 0){
        processDocIds(docIds);
    }
    textArea.val("");

    // Alerts if invalid string and then puts them back in the text area.
    if (invalidEntries.length > 0){
        console.log(invalidEntries);
        var alertStr = "These entires are invalid:\n";
        var invalidEntriesStr = invalidEntries.join('\n');
        alertStr = alertStr + invalidEntriesStr
        textArea.val(invalidEntriesStr);
        alert(alertStr);
    }

}

/**
 * Takes a string and returns a list of docIds and invalid entries.
 *
 * textInputs: (array) array of document information.
 **/
function processRawTextToDocIds(textInputs){
    var docIds = [];
    var invalidEntries = [];

    for (var i in textInputs){
        var entry = textInputs[i].replace(/^\s+|\s+$/g, '');  // Strips whitespace
        if (entry.includes(".com")){
            // treat as url
            var reg = /.*docsend\.com\/view\/(\w+)/
            var regResult = reg.exec(entry);
            if (regResult == null){
                invalidEntries.push(entry);
            }
            else{
                docIds.push(regResult[1]);
            }
        }
        else {
            // treat as id
            docIds.push(entry);
        }
    }

    return [docIds, invalidEntries];

}

/**
 * Takes in a list of ids, gathers the information, creates the panels, and if it can
 * will attempt to download the pdf.
 *
 * :docIds: (array) array of ids
 **/
function processDocIds(docIds){
    for (var i in docIds){
        var docId = docIds[i];
        console.log(docId);
        $.get("/get_document_info/"+docId, function(docInfo){
            DOC_INFO_CACHE[docInfo.id] = docInfo;
            createDocPanel(docInfo);
            if (docInfo.is_valid
                && !docInfo.email_required
                && !docInfo.passcode_required){

                downloadDoc(docInfo.id);
            }
        });


    }
}

/**
 * Adds all a new panel to the html document with all the necessary settings
 * and components.
 *
 * :docInfo: (Object) response from the server with document information.
 **/
function createDocPanel(docInfo){
    var panel = $("<div class=\"panel panel-default doc-download-panel\"></div>");
    panel.attr("data-doc-id", docInfo.id)

    var isValid = docInfo.is_valid;
    var isInfoRequired = docInfo.email_required;
    var isPasscodeRequired = docInfo.passcode_required;

    var docStatus;
    if (!isValid){
        docStatus = "invalid";
    }
    else if (isInfoRequired){
        docStatus = "attention";
    }
    else{
        docStatus = "downloading";
    }
    panel.attr("data-doc-status", docStatus);

    var panelHeading = $("<div class=\"panel-heading\"></div>").text("ID: " + docInfo.id);
    var panelBody = $("<div class=\"panel-body\"></div>");

    var leftCol = $("<div class=\"doc-info-panel-left\"></div>");
    var infoList = $("<ul class=\"info-list list-unstyled\"></ul>")
    var urlElem = $("<li><p></p></li>").html('<label>URL: </label> ' + docInfo.url)
    infoList.append(urlElem);

    if (isValid){
        var pageCountElem = $("<li><p></p></li>").html('<label>Page Count: </label> ' + docInfo.page_count)
        infoList.append(pageCountElem);

        if (isInfoRequired){
            var emailElem = $("<li><label>Email Required:&nbsp; </label><span></span><input type=\"text\" class=\"doc-email-input\" /></li>")
            emailElem.find('input').on('input', checkCardInformationStatus);
            infoList.append(emailElem);
        }
        if (isPasscodeRequired){
            var passcodeElem = $("<li><label>Passcode Required:&nbsp; </label><span></span><input type=\"text\" class=\"doc-passcode-input\" /></li>")
            passcodeElem.find('input').on('input', checkCardInformationStatus);
            infoList.append(passcodeElem);

        }
    }
    leftCol.append(infoList);

    //Icons

    var rightCol = $("<div class=\"doc-info-panel-right\"></div>");
    var spinnerIcon = $("<i class=\"fas fa-spinner fa-spin fa-5x\"></i>");

    var warnIcon = $("<i class=\"fas fa-exclamation-circle fa-5x\"></i>");
    var checkIcon = $("<i class=\"fas fa-check-circle fa-5x\"></i>");
    var invalidIcon = $("<i class=\"fas fa-times-circle fa-5x\"></i>");

    var downloadLink = $("<a></a>");
    downloadLink.on('click', collectInfoAndDownloadPdf);
    var downloadIcon = $("<i class=\"fas fa-arrow-alt-circle-down fa-5x pulse\"></i>");
    downloadLink.append(downloadIcon);

    var iconDiv = $("<div></div>")
    var explainDiv = $("<p class=\"icon-explain-p\"></p>").text(iconExplainText[docStatus]);
    iconDiv.append(spinnerIcon);
    iconDiv.append(downloadLink);
    iconDiv.append(warnIcon);
    iconDiv.append(checkIcon);
    iconDiv.append(invalidIcon);
    rightCol.append(iconDiv);
    rightCol.append(explainDiv);

    panelBody.append(leftCol)
    panelBody.append(rightCol)

    panel.append(panelHeading)
    panel.append(panelBody)
    $("section#downloads div.container").append(panel)
}


/**
 * Updates the status on a document
 *
 * :docId: (str) id of the document to change
 * :docStatus: (str) status to change it to. Must be one of the accepted status types.
 **/
function updateDocumentPanel(docId, docStatus){
    var panel = $("div.doc-download-panel[data-doc-id=\""+docId+"\"]");
    panel.attr('data-doc-status', docStatus)
    panel.find(".doc-info-panel-right p").text(iconExplainText[docStatus]);
}


/**
 * Checks to make sure all the information in a panel is filled in to allow the user to
 * click download. If the current status is processing, it will not change.
 **/
function checkCardInformationStatus(elem){
    var new_val = $(this).val()
    $(this).parent().children('span').text(new_val)
    var panel = $(this).parents('div.doc-download-panel');
    var docId = panel.attr('data-doc-id');
    var currentStatus = panel.attr('data-doc-status');
    var dataFilled = panel.find("input")
        .map(function(){return $(this).val() != ""})
        .toArray()
        .reduce(function(acc, cur){ return (acc && cur) }, true);


    if (dataFilled){
        updateDocumentPanel(docId, 'download')
    }
    else{
        updateDocumentPanel(docId, 'attention')
    }
}

/**
 * Collect the email and passcode from the panel and downloads the document from the server.
 *
 **/
function  collectInfoAndDownloadPdf(){
    var panel = $(this).parents('div.doc-download-panel');
    var docId = panel.attr('data-doc-id');
    var docInfo = DOC_INFO_CACHE[docId];
    var email;
    var passcode;

    if (docInfo.email_required){
        email = panel.find('.doc-email-input').val();
    }
    if (docInfo.passcode_required){
        passcode = panel.find('.doc-passcode-input').val();
    }

    updateDocumentPanel(docId, 'downloading');
    downloadDoc(docId, email, passcode);
}

/**
 * Downloads and automatically saves the pdf form the server.
 *
 * :docId: (str) id of the document to download
 * :email: (str) email to attached if necessary
 * :passcode: (str) passcode to attach if necessary
 **/
function downloadDoc(docId, email, passcode){
    var docName = "Docsend-"+docId+".pdf";
    $.ajax({
        url: "/download/"+docId,
        data: {email: email, passcode: passcode},
        success: function(data){
            const url = window.URL.createObjectURL(new Blob([data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', docName);
            document.body.appendChild(link);
            link.click();
            updateDocumentPanel(docId, 'complete');

        },
        statusCode:{
            400: function(response){
                updateDocumentPanel(docId, 'error');
            }
        }
    });
}



