/* Object for autosuggestions based on SPDX license schema*/
var xml_schema = {
    "!top": ["SPDXLicenseCollection"],
    SPDXLicenseCollection: {
        children: ['license', 'exception'],
        attrs: {
            "xmlns": null,
        }
    },
    exception: {
        attrs: {
            licenseId: null,
            name: null,
        },
        children: ["notes", "crossRefs", "text", ],
    },
    license: {
        attrs: {
            licenseId: null,
            name: null,
            isOsiApproved: ["true", "false"],
            listVersionAdded: null,
            isDeprecated: ["true", "false"],
            deprecatedVersion: null,
        },
        children: ["notes", "crossRefs", "text", "obsoletedBys", "standardLicenseHeader"],
    },
    crossRefs: {
        children: ["crossRef"],
    },
    obsoletedBys: {
        children: ["obsoletedBy"]
    },
    obsoletedBy: {
        attrs: {
            experssion: null,
        }
    },
    standardLicenseHeader: {
        children: ["p", "alt", "bullet", "br"]    
    },
    alt: {
        attrs:{
            name: null,
            match: null,
        }
    },
    p: {
        children: ["optional", "br"],
    },
    optional: {
        children: ["p", "standardLicenseHeader", "optional", "alt"],
    },
    text: {
        children: ["titleText", "list", "copyrightText", "optional", "p", "alt", "standardLicenseHeader", "br", ]
    },
    titleText: {
        children: ["p", "alt", "optional", "br"]
    },
    copyrightText: {
        children: ["p", "alt", "optional"]
    },
    list: {
        children: ["item", "list"]
    },
    item: {
        children: ["p", "bullet", "br"]
    }
}
var editor = "", splitTextEditor = "", initialXmlText = "", latestXmlText = '';
$(document).ready(function(){
    /* initialize bootstrap tooltip */
    $('[data-toggle="tooltip"]').tooltip();
    /* initialize the editor */
    var fontSize = 14, fullscreen = false;
    $(".starter-template").css('text-align','');
    editor = CodeMirror.fromTextArea($(".codemirror-textarea")[0], {
        lineNumbers: true,
        mode: "xml",
        indentUnit: 4,
        gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
        lineWrapping: true,
        showCursorWhenSelecting: true,
        lineWiseCopyCut: false,
        autofocus: true,
        cursorScrollMargin: 5,
        styleActiveLine: true,
        styleActiveSelected: true,
        autoCloseBrackets: true,
        matchTags: {bothTags: true},
        extraKeys: {
            "F11": fullScreen,
            "Esc": exitFullScreen,
            "Ctrl-J": "toMatchingTag",
            "'<'": completeAfter,
            "'/'": completeIfAfterLt,
            "' '": completeIfInTag,
            "'='": completeIfInTag,
        },
        hintOptions: {schemaInfo: xml_schema},
        showTrailingSpace: true,
        autoCloseTags: true,
        foldGutter: true,
    });
    splitTextEditor = CodeMirror.fromTextArea($(".codemirror-textarea")[1], {
        lineNumbers: true,
        mode: "xml",
        indentUnit: 4,
        gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
        lineWrapping: true,
        showCursorWhenSelecting: true,
        lineWiseCopyCut: false,
        autofocus: true,
        cursorScrollMargin: 5,
        styleActiveLine: true,
        styleActiveSelected: true,
        autoCloseBrackets: true,
        matchTags: {bothTags: true},
        extraKeys: {
            "F11": fullScreen,
            "Esc": exitFullScreen,
            "Ctrl-J": "toMatchingTag",
            "'<'": completeAfter,
            "'/'": completeIfAfterLt,
            "' '": completeIfInTag,
            "'='": completeIfInTag,
        },
        hintOptions: {schemaInfo: xml_schema},
        showTrailingSpace: true,
        autoCloseTags: true,
        foldGutter: true,
    });
    $(".CodeMirror").css("font-size",fontSize+'px');
    editor.setSize(($(window).width)*(0.9), 500);
    splitTextEditor.setSize(($(".splitTextEditorContainer").width)*(0.9), 550);
    initialXmlText = beautify(editor.getValue().trim());
    latestXmlText = beautify(editor.getValue().trim());
    /* Decrease editor font size */
    $("#dec-fontsize").click(function(){
        fontSize -= 1;
        $(".CodeMirror").css("font-size",fontSize+'px');
        editor.refresh();
    })
    /* Increase editor font size */
    $("#inc-fontsize").click(function(){
        fontSize += 1;
        $(".CodeMirror").css("font-size",fontSize+'px');
        editor.refresh();
    })
    /* Show autocomplete hints */
    function completeAfter(cm, pred) {
        var cur = cm.getCursor();
        if (!pred || pred()) setTimeout(function() {
          if (!cm.state.completionActive)
            cm.showHint({completeSingle: false});
        }, 100);
        return CodeMirror.Pass;
    }
    function completeIfAfterLt(cm) {
        return completeAfter(cm, function() {
          var cur = cm.getCursor();
          return cm.getRange(CodeMirror.Pos(cur.line, cur.ch - 1), cur) == "<";
        });
    }
    function completeIfInTag(cm) {
        return completeAfter(cm, function() {
          var tok = cm.getTokenAt(cm.getCursor());
          if (tok.type == "string" && (!/['"]/.test(tok.string.charAt(tok.string.length - 1)) || tok.string.length == 1)) return false;
          var inner = CodeMirror.innerMode(cm.getMode(), tok.state).state;
          return inner.tagName;
        });
    }
    /* Enter and Exit fullscreen */
    $("#fullscreen").click(fullScreen);
    function fullScreen(){
        if (!editor.getOption("fullScreen")) editor.setOption("fullScreen", true);
        display_message("Press Esc to exit fullscreen");
        fullscreen = true;
        editor.focus();
    }
    function exitFullScreen(){
        if (editor.getOption("fullScreen")) editor.setOption("fullScreen", false);
        fullscreen = false;
        editor.focus();
    }
    /* make editor responsive */
    $(window).resize(function(){
        splitTextEditor.setSize(($(".splitTextEditorContainer").width)*(0.9), 500);
        editor.setSize(($(window).width)*(0.9), 500);
        if (fullscreen){
            $(".CodeMirror-fullscreen").css("height","auto");   
        }
        splitTextEditor.refresh();
        editor.refresh();
    })
    /* beautify XML */
    $("#beautify").on("click",function(){
        var xmlText = editor.getValue().trim();
        editor.setValue(beautify(xmlText));
        editor.focus();
    })
    /* update split tree editor when split text editor loses focus */
    splitTextEditor.on('blur', function(){
        convertTextToTree(splitTextEditor, 'splitTreeView');
    })

    $("#tabTextEditor").click(function(){
        var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id");
        if(activeTab=='tabTreeEditor'){
            if(checkPendingChanges("#treeView")){
                $('#tabSplitView, #tabTreeEditor').removeAttr("data-toggle");
                $(this).attr("data-toggle","tab");
                var temp = updateTextEditor(editor, 'treeView');
                if(temp===0) editor.setValue(latestXmlText);
                else latestXmlText = temp;
                setTimeout(function(){
                    editor.refresh();
                    editor.focus();
                },200);
            }
        }
        else if(activeTab=='tabSplitView'){
            if(checkPendingChanges("#splitTreeView")){
                $('#tabSplitView, #tabTreeEditor').removeAttr("data-toggle");
                $(this).attr("data-toggle","tab");
                latestXmlText = beautify(splitTextEditor.getValue().trim());
                editor.setValue(latestXmlText);
                setTimeout(function(){
                    editor.refresh();
                    editor.focus();
                },200);
            }
        }
    })
    $("#tabTreeEditor").click(function(){
        var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id");
        if(activeTab=='tabTextEditor'){
            $('#tabSplitView, #tabTextEditor').removeAttr("data-toggle");
            $(this).attr("data-toggle","tab");
            convertTextToTree(editor, 'treeView')
            latestXmlText = beautify(editor.getValue().trim());
        }
        else if(activeTab=='tabSplitView'){
            if(checkPendingChanges("#splitTreeView")){
                $('#tabSplitView, #tabTextEditor').removeAttr("data-toggle");
                $(this).attr("data-toggle","tab");
                convertTextToTree(splitTextEditor, 'treeView')
                latestXmlText = beautify(splitTextEditor.getValue().trim());
            }
        }
    })
    $("#tabSplitView").click(function(){
        var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id");
        if(activeTab=='tabTreeEditor'){
            if(checkPendingChanges("#treeView")){
                $('#tabTreeEditor, #tabTextEditor').removeAttr("data-toggle");
                $(this).attr("data-toggle","tab");
                var temp = updateTextEditor(splitTextEditor, 'treeView');
                if(temp===0) splitTextEditor.setValue(latestXmlText);
                else latestXmlText = temp;
                convertTextToTree(splitTextEditor, 'splitTreeView');
                setTimeout(function(){
                    splitTextEditor.refresh();
                    splitTextEditor.focus();
                },200);
            }
        }
        else if(activeTab=='tabTextEditor'){
            $('#tabTreeEditor, #tabTextEditor').removeAttr("data-toggle");
            $(this).attr("data-toggle","tab");
            latestXmlText = beautify(editor.getValue().trim());
            splitTextEditor.setValue(latestXmlText);
            convertTextToTree(splitTextEditor, 'splitTreeView');
            setTimeout(function(){
                splitTextEditor.refresh();
                splitTextEditor.focus();
            },200);
        }
    })

    $("#generateDiff").click(function(event){
        event.preventDefault();
        $("#messages").html("");
        var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id");
        if(activeTab=="tabTextEditor"){
            text2 = editor.getValue().trim();
        }
        else if(activeTab=="tabTreeEditor"){
            text2 = updateTextEditor(editor, 'treeView');
            if(text2==0){
                text2 = latestXmlText
            }
        }
        else if(activeTab=="tabSplitView"){
            text2 = splitTextEditor.getValue().trim()
        }
        else{
            text2 = latestXmlText
        }
        /* removing extra sapces from text */
        initialXmlText = initialXmlText.replace(/\s{2,}/g,' ').replace(/\n/g,' ');
        text2 = text2.replace(/\s{2,}/g,' ').replace(/\n/g,' ');
        generate_diff(initialXmlText.replace(/>\s{0,}</g,"><").replace(/\s{0,}</g,"~::~<").split('~::~'),text2.replace(/>\s{0,}</g,"><").replace(/\s{0,}</g,"~::~<").split('~::~'));
        $("div.tooltip").remove();
    })

    $("#validateXML").click(function(event){
        event.preventDefault();
        $("#validateXML").text("Validating...");
        $("#validateXML").prop('disabled', true);
        var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id");
        if(activeTab=="tabTextEditor"){
            xmlText = editor.getValue().trim();
        }
        else if(activeTab=="tabTreeEditor"){
            xmlText = updateTextEditor(editor, 'treeView');
            if(xmlText==0){
                xmlText = latestXmlText
            }
        }
        else if(activeTab=="tabSplitView"){
            xmlText = splitTextEditor.getValue().trim()
        }
        else{
            xmlText = latestXmlText
        }
        var form = new FormData($("#form")[0]);
        form.append("xmlText", xmlText);
        $.ajax({
            type: "POST",
            enctype: 'multipart/form-data',
            url: "/app/validate_xml/",
            processData: false,
            contentType: false,
            cache: false,
            dataType: 'json',
            timeout: 600000,
            data: form,
            success: function (data) {
                if(data.type=="valid"){
                    displayModal("<h3>"+data.data+"</h3>","success");
                }
                else{
                    displayModal("<h3>"+data.data+"</h3>","alert");
                }
                $("#validateXML").text("Validate");
                $("#validateXML").prop('disabled', false);
            },
            error: function (e) {
                try {
                    var obj = JSON.parse(e.responseText);
                    if (obj.type=="warning"){
                        displayModal(obj.data, "alert");
                    }
                    else if (obj.type=="error"){
                        displayModal(obj.data, "error");
                    }
                }
                catch (e){
                    displayModal("The application could not be connected. Please try later.","error");
                }
                $("#validateXML").text("Validate");
                $("#validateXML").prop('disabled', false);
            }
        });
    })

    $("#makePullRequest").click(function(){
        var githubLogin = $("#githubLogin").text();
        $("#modal-body").removeClass("diff-modal-body");
        $(".modal-dialog").removeClass("diff-modal-dialog");
        $("#modal-title").html("SPDX License XML Editor");
        $('button.close').remove();
        if(githubLogin == "False"){
            $("#modal-header").removeClass("red-modal green-modal");
            $("#modal-header").addClass("yellow-modal");
            $(".modal-footer").html('<button class="btn btn-default pull-left" data-dismiss="modal"><span class="glyphicon glyphicon-remove"></span> Cancel</button><button class="btn btn-success" id="github_auth_begin"><span class="glyphicon glyphicon-ok"></span> Confirm</button>');
            $("#modal-body").html("You will now be redirected to the GitHub website to authenticate with the SPDX GitHub App. Please allow all the requested permissions for the app to work properly. After coming back to this page please click the Submit Changes button again to create a Pull Request.");
        }
        else if(githubLogin == "True"){
            $("#modal-header").removeClass("red-modal yellow-modal");
            $("#modal-header").addClass("green-modal");
            $(".modal-footer").html('<button class="btn btn-default pull-left" id="prCancel" data-dismiss="modal"><span class="glyphicon glyphicon-remove"></span> Cancel</button><button class="btn btn-success" id="prOk"><span class="glyphicon glyphicon-ok"></span> Confirm</button>');
            $("#modal-body").html($("#prFormContainer").html());
            $("#githubPRForm").css("display","block");
            $(".ajax-loader").css("display","none");
            $("#modal-body").addClass("pr-modal-body");
            $("#prOk, #prCancel").prop('disabled', false);
        }
        $("div.tooltip").remove();
        $('[data-toggle="tooltip"]').tooltip();
        $("#myModal").modal({
            backdrop: 'static',
            keyboard: true,
            show: true
        });
    })
});

$(document).on('click','button#prOk',function(event){
    event.preventDefault();
    var response = makePR();
    if(response!=true){
        $('<div class="alert alert-danger" style="font-size:15px;"><strong>Error! </strong>'+response+'</div>').insertBefore("#githubPRForm");
        setTimeout(function() {
            $(".alert").remove();
        }, 3000);
    }
});

/* update session variables */
$(document).on('click','button#github_auth_begin',function(event){
    event.preventDefault();
    var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id");
    if(activeTab=="tabTextEditor"){
        xmlText = editor.getValue().trim();
    }
    else if(activeTab=="tabTreeEditor"){
        xmlText = updateTextEditor(editor, 'treeView');
        if(xmlText==0){
            xmlText = latestXmlText
        }
    }
    else if(activeTab=="tabSplitView"){
        xmlText = splitTextEditor.getValue().trim()
    }
    else{
        xmlText = latestXmlText
    }
    var githubLoginLink = $("#githubLoginLink").text();
    var page_url = window.location.href;
    githubLoginLink += "?next=" + page_url;
    page_id = page_url.split("/");
    page_id = page_id[page_id.length-2];
    var form = new FormData($("#form")[0]);
    form.append("xml_text",xmlText);
    form.append("page_id",page_id);
    $.ajax({
        type: "POST",
        enctype: 'multipart/form-data',
        url: "/app/update_session/",
        processData: false,
        contentType: false,
        cache: false,
        dataType: 'json',
        timeout: 600000,
        data: form,
        async: false,
        success: function (data) {
            window.location = githubLoginLink;
        },
        error: function(e){
            displayModal("The application could not be connected. Please try later.","error");
        }
    });
});

function checkPRForm(){
    var branchName = $("#branchName").val();
    if(branchName=="" || branchName.search(/^[\./]|\.\.|@{|[\/\.]$|^@$|[~^:\x00-\x20\x7F\s?*[\\]/g)>-1){
        return "Invalid branch name";
    }
    if(/^\s*$/.test($("#fileName").val())){
        return "Invalid file name";
    }
    if(/^\s*$/.test($("#commitMessage").val())){
        return "Invalid commit message";
    }
    if(/^\s*$/.test($("#prTitle").val())){
        return "Invalid pull request title"
    }
    return true;
}
/* checks pr form and sends ajax request to pr view */
function makePR(){
    var check = checkPRForm();
    if(check!=true) return check;
    $("#prOk, #prCancel").html("Processing...");
    $("#prOk, #prCancel").prop('disabled', true);
    $("#githubPRForm").css("display","none");
    $(".ajax-loader").css({"display":"block"});
    var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id");
    if(activeTab=="tabTextEditor"){
        xmlText = editor.getValue().trim();
    }
    else if(activeTab=="tabTreeEditor"){
        xmlText = updateTextEditor(editor, 'treeView');
        if(xmlText==0){
            xmlText = latestXmlText
        }
    }
    else if(activeTab=="tabSplitView"){
        xmlText = splitTextEditor.getValue().trim()
    }
    else{
        xmlText = latestXmlText
    }
    var form = new FormData($("#githubPRForm")[0]);
    form.append("branchName", $("#branchName").val());
    form.append("updateUpstream", $("#updateUpstream").is(":checked"));
    form.append("fileName", $("#fileName").val());
    form.append("commitMessage", $("#commitMessage").val());
    form.append("prTitle", $("#prTitle").val());
    form.append("prBody", $("#prBody").val());
    form.append("xmlText", xmlText);
    $.ajax({
        type: "POST",
        enctype: 'multipart/form-data',
        url: "/app/make_pr/",
        processData: false,
        contentType: false,
        cache: false,
        dataType: 'json',
        timeout: 600000,
        data: form,
        success: function (data) {
            if(data.type=="success"){
                displayModal('<h3>Your Pull Request was created successfully <a href="'+data.data+'">here</a></h3>',"success");
            }
            $("#prOk").html('<span class="glyphicon glyphicon-ok"></span> Confirm');
            $("#prCancel").html('<span class="glyphicon glyphicon-remove"></span> Cancel');
            $("#prOk, #prCancel").prop('disabled', false);
        },
        error: function (e) {
            try {
                var obj = JSON.parse(e.responseText);
                if (obj.type=="pr_error"){
                    displayModal(obj.data, "error");
                }
                else if (obj.type=="auth_error"){
                    displayModal(obj.data, "alert");
                }
                else if (obj.type=="error"){
                    displayModal(obj.data, "error");
                }
            }
            catch (e){
                displayModal("The application could not be connected. Please try later.","error");
            }
            $("#prOk").html('<span class="glyphicon glyphicon-ok"></span> Confirm');
            $("#prCancel").html('<span class="glyphicon glyphicon-remove"></span> Cancel');
            $("#prOk, #prCancel").prop('disabled', false);
        }
    });
    return true;
}

/* generate diff of initial xml and current xml text */
function generate_diff(base, newtxt){
    var sm = new difflib.SequenceMatcher(base, newtxt);
    var opcodes = sm.get_opcodes();
    
    // build the diff view and add it to the current DOM
    var diff = $(diffview.buildView({
        baseTextLines: base,
        newTextLines: newtxt,
        opcodes: opcodes,
        // set the display titles for each resource
        baseTextName: "Base Text",
        newTextName: "New Text",
        contextSize: null,
        viewType: 1
    }))
    diff.children().remove("thead");
    diff.children().children().remove("th");
    displayModal("","success");
    $("#modal-body").html(diff);
    $("#modal-title").text("Diff between initial and current XML");
    $("#modal-body").addClass("diff-modal-body");
    $(".modal-dialog").addClass("diff-modal-dialog");
}

/* XML beautify script */
function beautify(text){
    var shift = ['\n'], i;
    for(i=0;i<100;i++){
        shift.push(shift[i]+'    '); 
    }
    var array = text.replace(/>\s{0,}</g,"><")
                 .replace(/\s{0,}</g,"~::~<")
                 .replace(/\s*xmlns\:/g,"~::~xmlns:")
                 .replace(/\s*xmlns\=/g,"~::~xmlns=")
                 .split('~::~');
    var len = array.length;
    var inComment = false;
    var deep = 0;
    var str = "";
        
    for(i=0;i<len;i++){
        /* if start comment or <![CDATA[...]]> or <!DOCTYPE */
        if(array[i].search(/<!/) > -1){ 
            str += shift[deep]+array[i];
            inComment = true;
            // if end comment  or <![CDATA[...]]> //
            if(array[i].search(/-->/) > -1 || array[i].search(/\]>/) > -1 || array[i].search(/!DOCTYPE/) > -1 ){ 
                inComment = false; 
            }
        } 
        /* end comment  or <![CDATA[...]]> */
        else if(array[i].search(/-->/)>-1 || array[i].search(/\]>/) > -1){ 
            str += array[i];
            inComment = false; 
        }
        /* <elm></elm> */
        else if( /^<\w/.exec(array[i-1]) && /^<\/\w/.exec(array[i]) &&
        /^<[\w:\-\.\,]+/.exec(array[i-1]) == /^<\/[\w:\-\.\,]+/.exec(array[i])[0].replace('/','')){
            str += array[i];
            if(!inComment) deep--;
        }
        /* <elm> */
        else if(array[i].search(/<\w/) > -1 && array[i].search(/<\//) == -1 && array[i].search(/\/>/) == -1 ){
            str = !inComment ? str += shift[deep++]+array[i] : str += array[i];
        } 
        /* <elm>...</elm> */
        else if(array[i].search(/<\w/) > -1 && array[i].search(/<\//) > -1){
            str = !inComment ? str += shift[deep]+array[i] : str += array[i];
        } 
        /* </elm> */
        else if(array[i].search(/<\//) > -1){
            str = !inComment ? str += shift[--deep]+array[i] : str += array[i];
        }
        /* <elm/> */
        else if(array[i].search(/\/>/) > -1 ){ 
            str = !inComment ? str += shift[deep]+array[i] : str += array[i];
        } 
        /* <? xml ... ?> */
        else if(array[i].search(/<\?/) > -1){ 
            str += shift[deep]+array[i];
        } 
        /* xmlns */
        else if( array[i].search(/xmlns\:/) > -1  || array[i].search(/xmlns\=/) > -1){ 
            str += ' '+array[i];
        }
        else {
            str += array[i];
        }
    }
    return  (str[0] == '\n') ? str.slice(1) : str;
}

/* display message using modal */
function display_message(message){
    $("#modal-body").removeClass("diff-modal-body pr-modal-body");
    $("#modal-header").removeClass("red-modal");
    $("#modal-header").removeClass("yellow-modal");
    $("#modal-header").addClass("green-modal");
    $("#modal-title").html("SPDX License XML Editor");
    $("#modal-body").html("<h3>"+message+"</h3>");
    $('button.close').remove();
    $('<button type="button" class="close" data-dismiss="modal">&times;</button>').insertBefore($("h4.modal-title"));
    $(".modal-footer").html('<button class="btn btn-default" data-dismiss="modal">OK</button>')
    $("#myModal").modal({
        backdrop: 'static',
        keyboard: true, 
        show: true
    });
    setTimeout(function() {
        $(".close").click();
    }, 2000);
    $(".close").click(function(){
        editor.focus();
    })
}

/* File download functions */
function saveTextAsFile() {
    var xmlText = "";
    var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id");
    if(activeTab=="tabTextEditor"){
        if(!convertTextToTree(editor, 'treeView')){
            displayModal("The file you are downloading is not a valid XML.", "alert");
        }
        xmlText = editor.getValue().trim();
    } 
    else if(activeTab=="tabTreeEditor"){
        xmlText = updateTextEditor(editor, 'treeView');
        if(xmlText==0){
            displayModal("The file you are downloading is not a valid XML.", "alert");
            xmlText = latestXmlText;
        }
    }
    else if(activeTab=="tabSplitView"){
        if(!convertTextToTree(splitTextEditor, 'splitTreeView')){
            displayModal("The file you are downloading is not a valid XML.", "alert");
        }
        xmlText = splitTextEditor.getValue().trim();
    }
    var textBlob = new Blob([xmlText], { type: 'application/xml' });
    var fileName = "license.xml";
    
    var downloadLink = document.createElement("a");
    downloadLink.download = fileName;
    downloadLink.innerHTML = "Hidden Download Link";
    window.URL = window.URL || window.webkitURL;

    downloadLink.href = window.URL.createObjectURL(textBlob);
    downloadLink.onclick = destroyClickedElement;
    downloadLink.style.display = "none";
    document.body.appendChild(downloadLink);
    downloadLink.click();
}
function destroyClickedElement(e){
    document.body.removeChild(e.target);
}
$("#download").click(function(e){
    e.preventDefault();
    saveTextAsFile();
});
/* alert before leaving the page */
window.onbeforeunload = function (e) {
    return "Are you sure you want to leave? All the changes will be lost. You can either download the XML document or submit changes for review.";
}
