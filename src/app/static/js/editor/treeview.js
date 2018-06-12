var new_xml="", arr=[];
$(document).ready(function(){
    
    convertTextToTree();
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
        var value = $(this).text();
        $('<input type="text" placeholder="Attribute Value" class="textbox" value="'+value+'"><img src="/static/images/tick.png" class="editAttribute"><img src="/static/images/removeNode.png" class="removeAttribute">').insertAfter($(this));
        $(this).css("display","none");
        $(".editAttribute").on("click", function(){
            value = $(this).prev().val().trim();
            if(value == ""){
                alert("The value cannot be empty. Please enter a valid attribute value.");
            }
            else if((/<|>|;|&/).exec(value)){
                alert("Attribute value cannot contain special symbols. Please enter a valid value.");
            }
            else{
                $(this).prev().prev().css("display","inline-block").text(value);
                $(this).prev().remove();
                $(this).next().remove();
                $(this).remove();
                refreshTextEditor();
            }
        })
        $(".removeAttribute").on("click", function(){
            if(confirm("Are you sure you want to delete this attribute? This action cannot be undone.")==true){
                for(var i=0;i<5;i++) $(this).prev().remove();
                $(this).remove();
                refreshTextEditor();
            }
        })
    });
    /* add new attribute */
    $(document).on('click',"img.addAttribute",function(){
        $('<div class="newAttributeContainer"> <input type="text" placeholder="Attribute Name" class="newAttributeName textbox"> = <input type="text" placeholder="Attribute Value" class="newAttributeValue textbox"><button class="addNewAttribute btn btn-success btn-sm">Add Attribute</button><button class="cancel btn btn-sm">Cancel</button></div>').insertAfter($(this));
        $(this).css("display","none");
        $("button.addNewAttribute").click(function(){
            var name = $(this).siblings(".newAttributeName").val().trim();
            var value = $(this).siblings(".newAttributeValue").val().trim();
            if(name=="" || value==""){
                alert("Please enter valid attribute name and value");
            }
            else if((/<|>|\s|;|&/).exec(name)){
                alert("Attribute name cannot contain spaces or special symbols. Please enter valid attribute name.");
            }
            else if((/<|>|;|&/).exec(value)){
                alert("Attribute value cannot contain special symbols. Please enter valid attribute value.");
            }
            else{
                $(this).parent().prev().css("display","inline-block");
                $('<span class="attributeName">'+name+'</span><span class="equal">=</span><span class="attributeValue">'+value+'</span>').insertBefore($(this).parent().siblings(".addAttribute"));
                $(this).parent().remove();
                refreshTextEditor();
            }
        })
        $("button.cancel").click(function(){
            $(this).parent().prev().css("display","inline-block");
            $(this).parent().remove();
        })
    });
    /* delete a tag */
    $(document).on('click','img.deleteNode',function(){
        if(confirm("Are you sure you want to delete this tag? This cannot be undone.")==true){
            $(this).parent().empty();
            $(this).parent().remove();
            refreshTextEditor();
        }
    })
    /* edit text value inside a tag */
    $(document).on('click','li.nodeText',function(){
        var value = $(this).text();
        $('<textarea rows="5" cols="70">'+value+'</textarea><br><button class="editNodeText btn btn-success">Save</button><button class="cancelEditNodeText btn">Cancel</button>').insertAfter($(this));
        $(this).next().focus();
        $(this).css("display","none");
        $(".editNodeText").on("click", function(){
            value = $(this).prevUntil("textarea").prev().val().trim();
            if((/<|>|&|;/).exec(value)){
                alert("Please remove the special symbols from the text.");
            }
            else if(value == ""){
                $(this).prevUntil("li.nodeText").remove();
                $(this).prev("li.nodeText").remove();
                $(this).next("button.cancelEditNodeText").remove();
                $('<li class="emptyText">(No text value. Click to edit.)</li>').insertAfter($(this));
                $(this).remove();
                refreshTextEditor();
            }
            else{
                $(this).prevUntil("li.nodeText").remove();
                $(this).prev("li.nodeText").css("display","inline-block").text(value);
                $(this).next("button.cancelEditNodeText").remove();
                $(this).remove();
                refreshTextEditor();
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
        var value = "";
        $('<textarea rows="5" cols="70"></textarea><br><button class="editNodeText btn btn-success">Save</button><button class="cancelEditNodeText btn">Cancel</button>').insertAfter($(this));
        $(this).next().focus();
        $(this).css("display","none");
        $(".editNodeText").on("click", function(){
            value = $(this).prevUntil("textarea").prev().val().trim();
            if((/<|>|&|;/).exec(value)){
                alert("Please remove the special symbols from the text.");
            }
            else if(value == ""){
                $(this).prevUntil("li.emptyText").remove();
                $(this).prev("li.emptyText").css("display","inline-block");
                $(this).next("button.cancelEditNodeText").remove();
                $(this).remove();
                refreshTextEditor();
            }
            else{
                $(this).prevUntil("li.emptyText").remove();
                $(this).prev("li.emptyText").remove();
                $(this).next("button.cancelEditNodeText").remove();
                $('<li class="nodeText">'+value+'</li>').insertAfter($(this));
                $(this).remove();
                refreshTextEditor();
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
        $('<input type="text" placeholder="Node Name" class="textbox"><button class="buttonAddChild btn btn-success">Create Child</button><button class="cancelAddChild btn">Cancel</button>').insertAfter($(this));
        $(this).css("display","none");
        $(".buttonAddChild").click(function(){
            var value = $(this).prev().val();
            if(value==""){
                alert("The tag name cannot be empty. Please enter a valid node name.");
            }
            else if((/<|>|\s|;|&/).exec(value)){
                alert("Tag name cannot contain spaces or special symbols. Please enter valid tag name.");
            }
            else{
                $(this).parent().append('<li><img src="/static/images/plus.png" class="expand"><img src="/static/images/minus.png" class="collapse"><span class="nodeName">'+value+'</span><img class="addAttribute" src="/static/images/addAttribute.png"><img class="deleteNode" src="/static/images/removeNode.png"><ul><li class="emptyText">(No text value. Click to edit.)</li><li class="addChild last">Add Child Node</li></ul></li>');
                $(this).prev().remove();
                $(this).next().remove();
                $(this).prev().css("display","block");
                $(this).remove();
                refreshTextEditor();
            }
        })
        $(".cancelAddChild").click(function(){
            $(this).prevUntil("li.addChild").remove();
            $(this).prev().css("display","block");
            $(this).remove();
        })
    })

});

function convertTextToTree(){
    var xml = editor.getValue();
    xml = xml.replace(/>\s{0,}</g,"><");
    try{
        var tree = $.parseXML(xml);
    }
    catch(err){
        $(".treeContainer").html('<center><h2 class="xmlParsingErrorMessage">Invalid XML.<br> Please use the text editor to correct the error. Tree editor can only be used with valid XML.</h2></center>');
        return 0;
    }
    $('.treeContainer').html('<ul id="treeView" class="treeView"><li></li></ul>');
    traverse($('.treeView li'),tree.firstChild)
    $('<img src="/static/images/plus.png" class="expand"><img src="/static/images/minus.png" class="collapse">').prependTo('.treeView li:has(li)');
    return 1;
}

function traverse(node,tree) {
    var children=$(tree).children();
    node.append('<span class="nodeName">'+tree.nodeName+'</span>');
    if(tree.attributes){
        $.each(tree.attributes, function(i, attrib){
            node.append('<span class="attributeName">'+attrib.name+'</span><span class="equal">=</span><span class="attributeValue">'+attrib.value+"</span>");
        })
    }
    node.append('<img class="addAttribute" src="/static/images/addAttribute.png"><img class="deleteNode" src="/static/images/removeNode.png">')
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

function refreshTextEditor(){
    new_xml = '<?xml version="1.0" encoding="UTF-8"?>', arr=[];
    if($(".treeContainer").find("ul")){
        convertTreeToText($("#treeView"));
        console.log($("#treeView"));
    }
    editor.setValue(beautify(new_xml));
    editor.refresh();
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
                new_xml+= '> ';
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
