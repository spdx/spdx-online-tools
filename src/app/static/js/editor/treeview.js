/**
 * Copyright (c) 2018 Tushar Mittal
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *   http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
*/

/* Contains code for the tree editor */

var new_xml="", arr=[];
$(document).ready(function(){
    /* expand and collapse tree using buttons*/
    $(document).on('click','img.expand, img.collapse',function(){
        /* Getting button class, to find type of button */
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
        /* find which tree editor user is using */
        var treeEditorId, activeTab = $(".nav-tabs").find("li.active").find("a").attr("id");
        activeTab == "tabTreeEditor" ? treeEditorId = "#treeView" : treeEditorId = "#splitTreeView";
        if(!checkPendingChanges(treeEditorId)) return;
        /* add textbox for taking user input */
        var value = $(this).text();
        $('<input type="text" placeholder="Attribute Value" class="textbox" value="'+value+'"><img src="/static/images/tick.png" class="editAttribute" title="Save Attribute Value" data-placement="top" data-toggle="tooltip"><img src="/static/images/removeNode.png" class="removeAttribute" title="Delete Attribute" data-placement="top" data-toggle="tooltip">').insertAfter($(this));
        $('[data-toggle="tooltip"]').tooltip();
        $(this).css("display","none");
        $(".editAttribute").on("click", function(){
            /* validate input value */
            value = $(this).prev().val().trim();
            if(value == ""){
                displayModal("The value cannot be empty. Please enter a valid attribute value.","alert");
            }
            else if((/<|>|;|&/).exec(value)){
                displayModal("Attribute value cannot contain special symbols. Please enter a valid value.","alert");
            }
            else{
                /* remove textbox and display new value */
                $(this).prev().prev().css("display","inline-block").text(value);
                $(this).prev().remove();
                $(this).nextUntil('.removeAttribute').remove();
                $(this).next().remove();
                $(this).remove();
                if(activeTab=="tabSplitView") updateTextEditor(splitTextEditor, 'splitTreeView');
            }
        })
        $(".removeAttribute").on("click", function(){
            /* if user clicks on delete attribute button */
            var node = $(this);
            displayModal("Are you sure you want to delete this attribute? This action cannot be undone.", "confirm");
            $("#modalOk").click(function(){
                /* remove attribute name and value */
                node.prevUntil("span.attributeName").remove();
                node.prev().remove();
                node.remove();
                if(activeTab=="tabSplitView") updateTextEditor(splitTextEditor, 'splitTreeView');
            })
        })
    });
    /* add new attribute */
    $(document).on('click',"img.addAttribute",function(){
        /* find which tree editor user is using */
        var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id"), treeEditorId;
        activeTab == "tabTreeEditor" ? treeEditorId = "#treeView" : treeEditorId = "#splitTreeView";
        if(!checkPendingChanges(treeEditorId)) return;
        /* add textboxes for user input */
        $('<div class="newAttributeContainer"> <input type="text" placeholder="Attribute Name" class="newAttributeName textbox"> = <input type="text" placeholder="Attribute Value" class="newAttributeValue textbox"><button class="addNewAttribute btn btn-success btn-sm">Add Attribute</button><button class="cancel btn btn-sm">Cancel</button></div>').insertAfter($(this));
        $(this).css("display","none");
        $("button.addNewAttribute").click(function(){
            /* validate the values input by user */
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
                /* add attribute to the tree and remove textboxes */
                $(this).parent().prev().css("display","inline-block");
                $('<span class="attributeName">'+name+'</span><span class="equal">=</span><span class="attributeValue">'+value+'</span>').insertBefore($(this).parent().siblings(".addAttribute"));
                $(this).parent().remove();
                if(activeTab=="tabSplitView") updateTextEditor(splitTextEditor, 'splitTreeView');
            }
        })
        $("button.cancel").click(function(){
            /* only remove textboxes */
            $(this).parent().prev().css("display","inline-block");
            $(this).parent().remove();
        })
    });
    /* delete a tag */
    $(document).on('click','img.deleteNode',function(){
        /* find which tree editor user is using */
        var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id");
        var node = $(this);
        displayModal("Are you sure you want to delete this tag? This cannot be undone.", "confirm");
        $('#modalOk').click(function(){
            /* remove the tag */
            node.parent().empty();
            node.parent().remove();
            if(activeTab=="tabSplitView") updateTextEditor(splitTextEditor, 'splitTreeView');
        })
    })
    /* edit text value inside a tag */
    $(document).on('click','li.nodeText',function(){
        /* find which tree editor user is using */
        var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id"), treeEditorId;
        activeTab == "tabTreeEditor" ? treeEditorId = "#treeView" : treeEditorId = "#splitTreeView";
        if(!checkPendingChanges(treeEditorId)) return;
        /* display textarea with current text inside tag */
        var value = $(this).text();
        $('<textarea rows="5" cols="70">'+value+'</textarea><br><button class="editNodeText btn btn-success">Save</button><button class="cancelEditNodeText btn">Cancel</button>').insertAfter($(this));
        $(this).next().focus();
        $(this).css("display","none");
        $(".editNodeText").on("click", function(){
            /* validate the text input by user */
            value = $(this).prevUntil("textarea").prev().val().trim();
            if((/<|>|&|;/).exec(value)){
                displayModal("Please remove the special symbols from the text.", "alert");
            }
            else if(value == ""){
                /* if value is empty, display empty text */
                $(this).prevUntil("li.nodeText").remove();
                $(this).prev("li.nodeText").remove();
                $(this).next("button.cancelEditNodeText").remove();
                $('<li class="emptyText">(No text value. Click to edit.)</li>').insertAfter($(this));
                $(this).remove();
                if(activeTab=="tabSplitView") updateTextEditor(splitTextEditor, 'splitTreeView');
            }
            else{
                /* update the text inside tag */
                $(this).prevUntil("li.nodeText").remove();
                $(this).prev("li.nodeText").css("display","inline-block").text(value);
                $(this).next("button.cancelEditNodeText").remove();
                $(this).remove();
                if(activeTab=="tabSplitView") updateTextEditor(splitTextEditor, 'splitTreeView');
            }
        })
        $(".cancelEditNodeText").on("click", function(){
            /* cancle text editing */
            $(this).prevUntil("li.nodeText").remove();
            $(this).prev("li.nodeText").css("display","inline-block");
            $(this).remove();
        })
    })
    /* edit empty text value inside a tag */
    $(document).on('click','li.emptyText',function(){
        /* find which tree editor user is using */
        var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id"), treeEditorId;
        activeTab == "tabTreeEditor" ? treeEditorId = "#treeView" : treeEditorId = "#splitTreeView";
        if(!checkPendingChanges(treeEditorId)) return;
        var value = "";
        /* display empty textarea */
        $('<textarea rows="5" cols="70"></textarea><br><button class="editNodeText btn btn-success">Save</button><button class="cancelEditNodeText btn">Cancel</button>').insertAfter($(this));
        $(this).next().focus();
        $(this).css("display","none");
        $(".editNodeText").on("click", function(){
            /* validate the text input by user */
            value = $(this).prevUntil("textarea").prev().val().trim();
            if((/<|>|&|;/).exec(value)){
                displayModal("Please remove the special symbols from the text.", "alert");
            }
            else if(value == ""){
                /* if value is empty, display empty text */
                $(this).prevUntil("li.emptyText").remove();
                $(this).prev("li.emptyText").css("display","inline-block");
                $(this).next("button.cancelEditNodeText").remove();
                $(this).remove();
            }
            else{
                /* update the text inside tag */
                $(this).prevUntil("li.emptyText").remove();
                $(this).prev("li.emptyText").remove();
                $(this).next("button.cancelEditNodeText").remove();
                $('<li class="nodeText">'+value+'</li>').insertAfter($(this));
                $(this).remove();
                if(activeTab=="tabSplitView") updateTextEditor(splitTextEditor, 'splitTreeView');
            }
        })
        $(".cancelEditNodeText").on("click", function(){
            /* cancle text editing */
            $(this).prevUntil("li.emptyText").remove();
            $(this).prev("li.emptyText").css("display","inline-block");
            $(this).remove();
        })
    })
    /* add new child tag */
    $(document).on('click','li.addChild',function(){
        /* find which tree editor user is using */
        var activeTab = $(".nav-tabs").find("li.active").find("a").attr("id"), treeEditorId;
        activeTab == "tabTreeEditor" ? treeEditorId = "#treeView" : treeEditorId = "#splitTreeView";
        if(!checkPendingChanges(treeEditorId)) return 0;
        /* add textbox for taking user input */
        $('<li><input type="text" placeholder="Node Name" class="textbox"><button class="buttonAddChild btn btn-success">Create Child</button><button class="cancelAddChild btn">Cancel</button></li>').insertAfter($(this));
        $(this).css("display","none");
        $(".buttonAddChild").click(function(){
            var value = $(this).prev().val();
            /* validating input value */
            if(value==""){
                displayModal("The tag name cannot be empty. Please enter a valid tag name.", "alert");
            }
            else if((/<|>|\s|;|&/).exec(value)){
                displayModal("Tag name cannot contain spaces or special symbols. Please enter valid tag name.", "alert");
            }
            else{
                /* adds new node */
                $(this).parent().parent().append('<li><img src="/static/images/plus.png" class="expand"><img src="/static/images/minus.png" class="collapse"><span class="nodeName">'+value+'</span><img class="addAttribute" src="/static/images/addAttribute.png" title="Add New Attribute" data-placement="top" data-toggle="tooltip"><img class="deleteNode" src="/static/images/removeNode.png" title="Delete Node" data-placement="top" data-toggle="tooltip"><ul><li class="emptyText">(No text value. Click to edit.)</li><li class="addChild last">Add Child Node</li></ul></li>');
                $(this).parent().prev('li.addChild').css("display","block");
                $(this).parent().remove();
                $('[data-toggle="tooltip"]').tooltip();
                if(activeTab=="tabSplitView") updateTextEditor(splitTextEditor, 'splitTreeView');
            }
        })
        $(".cancelAddChild").click(function(){
            /* cancel adding node */
            $(this).parent().prev('li.addChild').css("display","block");
            $(this).parent().remove();
        })
    })
});

/**
 * takes xml text and parse into jQuery xml object
 * textEditor: xml text to be converted
 * treeEditor: one of the 2 tree editors
 */
function convertTextToTree(textEditor, treeEditor){
    var xml = textEditor.getValue().trim();
    xml = xml.replace(/>\s{0,}</g,"><");
    /* parse xml text and convert into jQuery object */
    try{
        var tree = $.parseXML(xml);
    }
    catch(err){
        /* if xml is invalid display error message in tree editor */
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
    /* initialize tree editor */
    if(treeEditor=="treeView"){
        $('.treeContainer').html('<ul id="treeView" class="treeView"><li></li></ul>');
    }
    else{
        $('.splitTreeEditorContainer').html('<ul id="splitTreeView" class="splitTreeView"><li></li></ul>');
    }
    /* call traverse to convert into tree */
    traverse($('.'+treeEditor+' li'),tree.firstChild);
    $('[data-toggle="tooltip"]').tooltip();
    /* add expand collapse buttons to tree */
    $('<img src="/static/images/plus.png" class="expand"><img src="/static/images/minus.png" class="collapse">').prependTo('.'+treeEditor+' li:has(li)');
    return 1;
}

/**
 * traverse jQuery xml object to generate tree view
 * node: tree editor to be changed
 * tree: the jQuery xml object
 */
function traverse(node,tree) {
    var children=$(tree).children();
    /* add node and its attributes */
    node.append('<span class="nodeName">'+tree.nodeName+'</span>');
    if(tree.attributes){
        $.each(tree.attributes, function(i, attrib){
            node.append('<span class="attributeName">'+attrib.name+'</span><span class="equal">=</span><span class="attributeValue">'+attrib.value+"</span>");
        })
    }
    /* add 'new attribute' and 'delete node' buttons */
    node.append('<img class="addAttribute" src="/static/images/addAttribute.png" title="Add New Attribute" data-placement="top" data-toggle="tooltip"><img class="deleteNode" src="/static/images/removeNode.png" title="Delete Node" data-placement="top" data-toggle="tooltip">')
    /* if node has children call traverse for every child */
    if (children.length){
        var ul=$("<ul>").appendTo(node);
        /* extract node text and add to the editor */
        var nodeText = $(tree).clone().children().remove().end().text();
        if(nodeText==""){
            $('<li class="emptyText">(No text value. Click to edit.)</li><li class="addChild last">Add Child Node</li>').appendTo(ul);
        }
        else{
            $('<ul><li class="nodeText">'+ nodeText +'</li><li class="addChild last">Add Child Node</li></ul>').appendTo(ul);
        }
        children.each(function(){
            var li=$('<li>').appendTo(ul);
            traverse(li,this);
        })
    }
    /* if no child then only add node text */
    else{
        if($(tree).text()==""){
            $('<ul><li class="emptyText">(No text value. Click to edit.)</li><li class="addChild last">Add Child Node</li></ul>').appendTo(node);
        }
        else{
            $('<ul><li class="nodeText">'+ $(tree).text()+'</li><li class="addChild last">Add Child Node</li></ul>').appendTo(node);
        }
    }
}

/**
 * updates the text editor from tree editor
 * textEditor: text editor to be updated
 * treeEditor: tree editor to be converted into text
 */
function updateTextEditor(textEditor, treeEditor){
    var container = "";
    if(treeEditor=='treeView') container = '.treeContainer';
    else container = '.splitTreeEditorContainer';
    /* if container has ul then xml is valid, tree is present  */
    if($(container).find("ul").length){
        /* new_xml: global variable, contains the converted xml text */
        new_xml = '<?xml version="1.0" encoding="UTF-8"?>', arr=[];
        /* call convert function */
        convertTreeToText($("#"+treeEditor));
        /* update text editor */
        textEditor.setValue(beautify(new_xml));
        textEditor.refresh();
        return new_xml;
    }
    else{
        /* xml not valid, so tree not present */
        return 0;
    }
}

/**
 * converts the tree to xml text and appends to new_xml global variable
 * tree: tree editor HTML DOM
 */
function convertTreeToText(tree){
    var children=$(tree).children();
    if (children.length){    
        $.each(children, function(){
            /* append node name */
            if(this.nodeName=="SPAN" && this.attributes['class'] && this.attributes['class'].nodeValue=="nodeName"){
                new_xml+= "<"+this.innerText;
                /* store node names in array to use for closing tags */
                arr.push(this.innerText);
            }
            /* append attribute name */
            else if(this.nodeName=="SPAN" && this.attributes['class'] && this.attributes['class'].nodeValue=="attributeName"){
                new_xml+= " "+this.innerText;
                return true;
            }
            /* append attribute value */
            else if(this.nodeName=="SPAN" && this.attributes['class'] && this.attributes['class'].nodeValue=="attributeValue"){
                new_xml+= '="'+this.innerText+'"';
                return true;
            }
            /* if addAttribute button then close the tag */
            else if(this.nodeName=="IMG" && this.attributes['class'] && this.attributes['class'].nodeValue=="addAttribute"){
                new_xml+= '>';
                return true;
            }
            /* append node text */
            else if(this.nodeName=="LI" && this.attributes['class'] && this.attributes['class'].nodeValue=="nodeText"){
                new_xml+= this.innerText;
                return true;
            }
            /* if node has any child, call function for that child */
            if(this.nodeName!="DIV" || (this.nodeName=='LI' && this.attributes['class'] && this.attributes['class'].nodeValue!="emptyText")){
                convertTreeToText(this);
            }
        })
        /* add the closing tag using node name values in arr */
        if ($(tree).prop('nodeName')=="LI"){
            if($(tree).prop('firstChild').className=='nodeText'){
                new_xml += $(tree).prop('firstChild').innerText;
            }
            new_xml += "</"+arr.pop()+">";
        }
    }
}

/**
 * checks for open textboxes in tree editor
 * treeEditorId: id of tree editor to be checked
 */
function checkPendingChanges(treeEditorId){
    var res = 1;
    /* checks if any edit attribute textboxes are open */
    $(treeEditorId).find(".editAttribute").each(function(){
        /* click on save button to close textboxes */
        $(this).click();
        /* if textboxes still present, it contains invalid value */
        if($(document).find(this).length){
            /* change css of textbox to highlight them */
            $(this).prev().css("background","rgba(255, 0, 0, 0.1)");
            $(this).prev().css("border-bottom", "2px solid rgb(255, 0, 0)");
            res = 0;
        }
    })
    /* checks if any add new attribute textboxes are open */
    $(treeEditorId).find(".addNewAttribute").each(function(){
        /* click on save button to close textboxes */
        $(this).click();
        /* if textboxes still present, it contains invalid value */
        if($(document).find(this).length){
            /* change css of textbox to highlight them */
            $(this).prev('.newAttributeValue').css("border-bottom", "2px solid rgb(255, 0, 0)");
            $(this).prev('.newAttributeValue').css("background","rgba(255, 0, 0, 0.1)");
            $(this).prev().prev('.newAttributeName').css("border-bottom", "2px solid rgb(255, 0, 0)");
            $(this).prev().prev('.newAttributeName').css("background","rgba(255, 0, 0, 0.1)");
            res = 0;
        }
    })
    /* checks for any open textarea */
    $(treeEditorId).find(".editNodeText").each(function(){
        $(this).click();
        /* if textarea still present, it contains invalid value */
        if($(document).find(this).length) res = 0;
    })
    /* checks for open add child textboxes */
    $(treeEditorId).find(".buttonAddChild").each(function(){
        /* click on save button to close textboxes */
        $(this).click();
        /* if textboxes still present, it contains invalid value */
        if($(document).find(this).length){
            /* change css of textbox to highlight them */
            $(this).prev().css("background","rgba(255, 0, 0, 0.1)");
            $(this).prev().css("border-bottom", "2px solid rgb(255, 0, 0)");
            res = 0;
        }
    })
    /* res=1 if everything is closed, res=0 if any textbox still open */
    return res;
}

/**
 * displays modals of different types
 * message: message to be displayed
 * mode: type of modal
 */
function displayModal(message, mode){
    $("#modal-body").removeClass("diff-modal-body pr-modal-body");
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
