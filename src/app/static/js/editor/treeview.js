var new_xml="", arr=[];
$(document).ready(function(){
    /* expand and collapse tree */
    $(document).on('click','img.expand, img.collapse',function(){
        var sign=$(this).attr('class');
        if (sign=="collapse"){
            $(this).css("display","none");
            $(this).prev().css("display","inline-block");
            $(this).parent().children().find("li").slideUp("fast","linear");
        }
        else if(sign=="expand"){
            $(this).next().css("display","inline-block");
            $(this).css("display","none");
            $(this).parent().children().find("img.collapse").css("display","inline-block");
            $(this).parent().children().find("img.expand").css("display","none");
            $(this).parent().children().find("li").slideDown();
        }    
    });
    /* edit atttribute value */
    $(document).on('click','span.attributeValue',function(){
        var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id"), treeEditorId;
        activeTab == "tabTreeEditor" ? treeEditorId = "#treeView" : treeEditorId = "#splitTreeView";
        if(!checkPendingChanges(treeEditorId)) return;
        var value = $(this).text();
        $('<input type="text" placeholder="Attribute Value" class="textbox" value="'+value+'"><img src="/static/images/tick.png" class="editAttribute" title="Save Attribute Value" data-placement="top" data-toggle="tooltip"><img src="/static/images/removeNode.png" class="removeAttribute" title="Delete Attribute" data-placement="top" data-toggle="tooltip">').insertAfter($(this));
        $('[data-toggle="tooltip"]').tooltip();
        $(this).css("display","none");
        $(".editAttribute").on("click", function(){
            value = $(this).prev().val().trim();
            if(value == ""){
                displayModal("The value cannot be empty. Please enter a valid attribute value.","alert");
            }
            else if((/<|>|;|&/).exec(value)){
                displayModal("Attribute value cannot contain special symbols. Please enter a valid value.","alert");
            }
            else{
                $(this).prev().prev().css("display","inline-block").text(value);
                $(this).prev().remove();
                $(this).nextUntil('.removeAttribute').remove();
                $(this).next().remove();
                $(this).remove();
                if(activeTab=="tabSplitView") updateTextEditor(splitTextEditor, 'splitTreeView');
            }
        })
        $(".removeAttribute").on("click", function(){
            var node = $(this);
            displayModal("Are you sure you want to delete this attribute? This action cannot be undone.", "confirm");
            $("#modalOk").click(function(){
                node.prevUntil("span.attributeName").remove();
                node.prev().remove();
                node.remove();
                if(activeTab=="tabSplitView") updateTextEditor(splitTextEditor, 'splitTreeView');
            })
        })
    });
    /* add new attribute */
    $(document).on('click',"img.addAttribute",function(){
        var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id"), treeEditorId;
        activeTab == "tabTreeEditor" ? treeEditorId = "#treeView" : treeEditorId = "#splitTreeView";
        if(!checkPendingChanges(treeEditorId)) return;
        $('<div class="newAttributeContainer"> <input type="text" placeholder="Attribute Name" class="newAttributeName textbox"> = <input type="text" placeholder="Attribute Value" class="newAttributeValue textbox"><button class="addNewAttribute btn btn-success btn-sm">Add Attribute</button><button class="cancel btn btn-sm">Cancel</button></div>').insertAfter($(this));
        $(this).css("display","none");
        $("button.addNewAttribute").click(function(){
            var name = $(this).siblings(".newAttributeName").val().trim();
            var value = $(this).siblings(".newAttributeValue").val().trim();
            if(name=="" || value==""){
                displayModal("Please enter valid attribute name and value","alert");
            }
            else if((/<|>|\s|;|&/).exec(name)){
                displayModal("Attribute name cannot contain spaces or special symbols. Please enter valid attribute name.","alert");
            }
            else if((/<|>|;|&/).exec(value)){
                displayModal("Attribute value cannot contain special symbols. Please enter valid attribute value.","alert");
            }
            else{
                $(this).parent().prev().css("display","inline-block");
                $('<span class="attributeName">'+name+'</span><span class="equal">=</span><span class="attributeValue">'+value+'</span>').insertBefore($(this).parent().siblings(".addAttribute"));
                $(this).parent().remove();
                if(activeTab=="tabSplitView") updateTextEditor(splitTextEditor, 'splitTreeView');
            }
        })
        $("button.cancel").click(function(){
            $(this).parent().prev().css("display","inline-block");
            $(this).parent().remove();
        })
    });
    /* delete a tag */
    $(document).on('click','img.deleteNode',function(){
        var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id");
        var node = $(this);
        displayModal("Are you sure you want to delete this tag? This cannot be undone.", "confirm");
        $('#modalOk').click(function(){
            node.parent().empty();
            node.parent().remove();
            if(activeTab=="tabSplitView") updateTextEditor(splitTextEditor, 'splitTreeView');
        })
    })
    /* edit text value inside a tag */
    $(document).on('click','li.nodeText',function(){
        var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id"), treeEditorId;
        activeTab == "tabTreeEditor" ? treeEditorId = "#treeView" : treeEditorId = "#splitTreeView";
        if(!checkPendingChanges(treeEditorId)) return;
        var value = $(this).text();
        $('<textarea rows="5" cols="70">'+value+'</textarea><br><button class="editNodeText btn btn-success">Save</button><button class="cancelEditNodeText btn">Cancel</button>').insertAfter($(this));
        $(this).next().focus();
        $(this).css("display","none");
        $(".editNodeText").on("click", function(){
            value = $(this).prevUntil("textarea").prev().val().trim();
            if((/<|>|&|;/).exec(value)){
                displayModal("Please remove the special symbols from the text.", "alert");
            }
            else if(value == ""){
                $(this).prevUntil("li.nodeText").remove();
                $(this).prev("li.nodeText").remove();
                $(this).next("button.cancelEditNodeText").remove();
                $('<li class="emptyText">(No text value. Click to edit.)</li>').insertAfter($(this));
                $(this).remove();
                if(activeTab=="tabSplitView") updateTextEditor(splitTextEditor, 'splitTreeView');
            }
            else{
                $(this).prevUntil("li.nodeText").remove();
                $(this).prev("li.nodeText").css("display","inline-block").text(value);
                $(this).next("button.cancelEditNodeText").remove();
                $(this).remove();
                if(activeTab=="tabSplitView") updateTextEditor(splitTextEditor, 'splitTreeView');
            }
        })
        $(".cancelEditNodeText").on("click", function(){
            $(this).prevUntil("li.nodeText").remove();
            $(this).prev("li.nodeText").css("display","inline-block");
            $(this).remove();
        })
    })
    /* edit empty text value inside a tag */
    $(document).on('click','li.emptyText',function(){
        var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id"), treeEditorId;
        activeTab == "tabTreeEditor" ? treeEditorId = "#treeView" : treeEditorId = "#splitTreeView";
        if(!checkPendingChanges(treeEditorId)) return;
        var value = "";
        $('<textarea rows="5" cols="70"></textarea><br><button class="editNodeText btn btn-success">Save</button><button class="cancelEditNodeText btn">Cancel</button>').insertAfter($(this));
        $(this).next().focus();
        $(this).css("display","none");
        $(".editNodeText").on("click", function(){
            value = $(this).prevUntil("textarea").prev().val().trim();
            if((/<|>|&|;/).exec(value)){
                displayModal("Please remove the special symbols from the text.", "alert");
            }
            else if(value == ""){
                $(this).prevUntil("li.emptyText").remove();
                $(this).prev("li.emptyText").css("display","inline-block");
                $(this).next("button.cancelEditNodeText").remove();
                $(this).remove();
            }
            else{
                $(this).prevUntil("li.emptyText").remove();
                $(this).prev("li.emptyText").remove();
                $(this).next("button.cancelEditNodeText").remove();
                $('<li class="nodeText">'+value+'</li>').insertAfter($(this));
                $(this).remove();
                if(activeTab=="tabSplitView") updateTextEditor(splitTextEditor, 'splitTreeView');
            }
        })
        $(".cancelEditNodeText").on("click", function(){
            $(this).prevUntil("li.emptyText").remove();
            $(this).prev("li.emptyText").css("display","inline-block");
            $(this).remove();
        })
    })
    /* add new child tag */
    $(document).on('click','li.addChild',function(){
        var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id"), treeEditorId;
        activeTab == "tabTreeEditor" ? treeEditorId = "#treeView" : treeEditorId = "#splitTreeView";
        if(!checkPendingChanges(treeEditorId)) return 0;
        $('<li><input type="text" placeholder="Node Name" class="textbox"><button class="buttonAddChild btn btn-success">Create Child</button><button class="cancelAddChild btn">Cancel</button></li>').insertAfter($(this));
        $(this).css("display","none");
        $(".buttonAddChild").click(function(){
            var value = $(this).prev().val();
            if(value==""){
                displayModal("The tag name cannot be empty. Please enter a valid tag name.", "alert");
            }
            else if((/<|>|\s|;|&/).exec(value)){
                displayModal("Tag name cannot contain spaces or special symbols. Please enter valid tag name.", "alert");
            }
            else{
                $(this).parent().parent().append('<li><img src="/static/images/plus.png" class="expand"><img src="/static/images/minus.png" class="collapse"><span class="nodeName">'+value+'</span><img class="addAttribute" src="/static/images/addAttribute.png" title="Add New Attribute" data-placement="top" data-toggle="tooltip"><img class="deleteNode" src="/static/images/removeNode.png" title="Delete Node" data-placement="top" data-toggle="tooltip"><ul><li class="emptyText">(No text value. Click to edit.)</li><li class="addChild last">Add Child Node</li></ul></li>');
                $(this).parent().prev('li.addChild').css("display","block");
                $(this).parent().remove();
                $('[data-toggle="tooltip"]').tooltip();
                if(activeTab=="tabSplitView") updateTextEditor(splitTextEditor, 'splitTreeView');
            }
        })
        $(".cancelAddChild").click(function(){
            $(this).parent().prev('li.addChild').css("display","block");
            $(this).parent().remove();
        })
    })
});

function convertTextToTree(textEditor, treeEditor){
    var xml = textEditor.getValue().trim();
    xml = xml.replace(/>\s{0,}</g,"><");
    try{
        var tree = $.parseXML(xml);
    }
    catch(err){
        var newParser = new DOMParser();
        var DOM = newParser.parseFromString(xml, "application/xml");
        var errorData = DOM.childNodes[1].firstChild.data;
        var errorMessage = errorData.slice(0,errorData.indexOf('Location')).replace('<','&lt;').replace('>','&gt;')
        if(treeEditor=="treeView"){
            $(".treeContainer").html('<center><h2 class="xmlParsingErrorMessage">Invalid XML.</h2><br><span class="xmlParsingErrorMessage">'+errorMessage+'<br> Please use the text editor to correct the error. Tree editor can only be used with valid XML.</span></center>');
        }
        else{
            $(".splitTreeEditorContainer").html('<center><h2 class="xmlParsingErrorMessage">Invalid XML.</h2><br><span class="xmlParsingErrorMessage">'+errorMessage+'<br> Please use the text editor to correct the error. Tree editor can only be used with valid XML.</span></center>');
        }
        return 0;
    }
    if(treeEditor=="treeView"){
        $('.treeContainer').html('<ul id="treeView" class="treeView"><li></li></ul>');
    }
    else{
        $('.splitTreeEditorContainer').html('<ul id="splitTreeView" class="splitTreeView"><li></li></ul>');
    }
    traverse($('.'+treeEditor+' li'),tree.firstChild);
    $('[data-toggle="tooltip"]').tooltip();
    $('<img src="/static/images/plus.png" class="expand"><img src="/static/images/minus.png" class="collapse">').prependTo('.'+treeEditor+' li:has(li)');
    return 1;
}
/* traverse jquery xml object to generate tree view */
function traverse(node,tree) {
    var children=$(tree).children();
    node.append('<span class="nodeName">'+tree.nodeName+'</span>');
    if(tree.attributes){
        $.each(tree.attributes, function(i, attrib){
            node.append('<span class="attributeName">'+attrib.name+'</span><span class="equal">=</span><span class="attributeValue">'+attrib.value+"</span>");
        })
    }
    node.append('<img class="addAttribute" src="/static/images/addAttribute.png" title="Add New Attribute" data-placement="top" data-toggle="tooltip"><img class="deleteNode" src="/static/images/removeNode.png" title="Delete Node" data-placement="top" data-toggle="tooltip">')
    if (children.length){
        var ul=$("<ul>").appendTo(node);
        var nodeText = $(tree).clone().children().remove().end().text();
        if(nodeText==""){
            $('<li class="emptyText">(No text value. Click to edit.)</li><li class="addChild last">Add Child Node</li>').appendTo(ul);
        }
        else{
            $('<ul><li class="nodeText">'+ nodeText +'</li><li class="addChild last">Add Child Node</li></ul>').appendTo(ul);
        }
        //$('<li class="emptyText">(No text value. Click to edit.)</li><li class="addChild last">Add Child Node</li>').appendTo(ul);
        children.each(function(){
            var li=$('<li>').appendTo(ul);
            traverse(li,this);
        })
    }
    else{
        if($(tree).text()==""){
            $('<ul><li class="emptyText">(No text value. Click to edit.)</li><li class="addChild last">Add Child Node</li></ul>').appendTo(node);
        }
        else{
            $('<ul><li class="nodeText">'+ $(tree).text()+'</li><li class="addChild last">Add Child Node</li></ul>').appendTo(node);
        }
    }
}

function updateTextEditor(textEditor, treeEditor){
    var container = "";
    if(treeEditor=='treeView') container = '.treeContainer';
    else container = '.splitTreeEditorContainer';
    if($(container).find("ul").length){
        new_xml = '<?xml version="1.0" encoding="UTF-8"?>', arr=[];
        convertTreeToText($("#"+treeEditor));
        textEditor.setValue(beautify(new_xml));
        textEditor.refresh();
        return new_xml;
    }
    else{
        return 0;
    }
}

function convertTreeToText(tree){
    var children=$(tree).children();
    if (children.length){    
        $.each(children, function(){
            if(this.nodeName=="SPAN" && this.attributes['class'] && this.attributes['class'].nodeValue=="nodeName"){
                new_xml+= "<"+this.innerText;
                arr.push(this.innerText);
            }
            else if(this.nodeName=="SPAN" && this.attributes['class'] && this.attributes['class'].nodeValue=="attributeName"){
                new_xml+= " "+this.innerText;
                return true;
            }
            else if(this.nodeName=="SPAN" && this.attributes['class'] && this.attributes['class'].nodeValue=="attributeValue"){
                new_xml+= '="'+this.innerText+'"';
                return true;
            }
            else if(this.nodeName=="IMG" && this.attributes['class'] && this.attributes['class'].nodeValue=="addAttribute"){
                new_xml+= '>';
                return true;
            }
            else if(this.nodeName=="LI" && this.attributes['class'] && this.attributes['class'].nodeValue=="nodeText"){
                new_xml+= this.innerText;
                return true;
            }
            if(this.nodeName!="DIV" || (this.nodeName=='LI' && this.attributes['class'] && this.attributes['class'].nodeValue!="emptyText")){
                convertTreeToText(this);
            }
        })
        if ($(tree).prop('nodeName')=="LI"){
            if($(tree).prop('firstChild').className=='nodeText'){
                new_xml += $(tree).prop('firstChild').innerText;
            }
            new_xml += "</"+arr.pop()+">";
        }
    }
}
/* check for open textboxes in tree editor */
function checkPendingChanges(treeEditorId){
    var res = 1;
    $(treeEditorId).find(".editAttribute").each(function(){
        $(this).click();
        if($(document).find(this).length){
            $(this).prev().css("background","rgba(255, 0, 0, 0.1)");
            $(this).prev().css("border-bottom", "2px solid rgb(255, 0, 0)");
            res = 0;
        }
    })
    $(treeEditorId).find(".addNewAttribute").each(function(){
        $(this).click();
        if($(document).find(this).length){
            $(this).prev('.newAttributeValue').css("border-bottom", "2px solid rgb(255, 0, 0)");
            $(this).prev('.newAttributeValue').css("background","rgba(255, 0, 0, 0.1)");
            $(this).prev().prev('.newAttributeName').css("border-bottom", "2px solid rgb(255, 0, 0)");
            $(this).prev().prev('.newAttributeName').css("background","rgba(255, 0, 0, 0.1)");
            res = 0;
        }
    })
    $(treeEditorId).find(".editNodeText").each(function(){
        $(this).click();
    })
    $(treeEditorId).find(".buttonAddChild").each(function(){
        $(this).click();
        if($(document).find(this).length){
            $(this).prev().css("background","rgba(255, 0, 0, 0.1)");
            $(this).prev().css("border-bottom", "2px solid rgb(255, 0, 0)");
            res = 0;
        }
    })
    return res;
}

function displayModal(message, mode){
    $("#modal-body").removeClass("diff-modal-body");
    $(".modal-dialog").removeClass("diff-modal-dialog");
    if(mode=="confirm"){
        $("#modal-header").removeClass("red-modal");
        $("#modal-header").removeClass("green-modal");
        $("#modal-header").addClass("yellow-modal");
        $("#modal-title").html("SPDX License XML Editor");
        $('button.close').remove();
        $(".modal-footer").html('<button class="btn btn-default pull-left" id="modalCancel" data-dismiss="modal"><span class="glyphicon glyphicon-remove"></span> Cancel</button><button class="btn btn-success" id="modalOk" data-dismiss="modal"><span class="glyphicon glyphicon-ok"></span> Confirm</button>')
    }
    else if(mode=="success"){
        $("#modal-header").removeClass("yellow-modal");
        $("#modal-header").removeClass("red-modal");
        $("#modal-header").addClass("green-modal");
        $("#modal-title").html("SPDX License XML Editor");
        $('button.close').remove();
        $('<button type="button" class="close" data-dismiss="modal">&times;</button>').insertBefore($("h4.modal-title"));
        $(".modal-footer").html('<button class="btn btn-default" data-dismiss="modal">OK</button>')
    }
    else if(mode=="alert"){
        $("#modal-header").removeClass("red-modal");
        $("#modal-header").removeClass("green-modal");
        $("#modal-header").addClass("yellow-modal");
        $("#modal-title").html("SPDX License XML Editor");
        $('button.close').remove();
        $('<button type="button" class="close" data-dismiss="modal">&times;</button>').insertBefore($("h4.modal-title"));
        $(".modal-footer").html('<button class="btn btn-default" data-dismiss="modal">OK</button>')
    }
    else if(mode=="error"){
        $("#modal-header").removeClass("yellow-modal");
        $("#modal-header").removeClass("green-modal");
        $("#modal-header").addClass("red-modal");
        $("#modal-title").html("SPDX License XML Editor");
        $('button.close').remove();
        $('<button type="button" class="close" data-dismiss="modal">&times;</button>').insertBefore($("h4.modal-title"));
        $(".modal-footer").html('<button class="btn btn-default" data-dismiss="modal">OK</button>')
    }
    $("#modal-body").html(message);
    $("#myModal").modal({
        backdrop: 'static',
        keyboard: true, 
        show: true
    });
}
