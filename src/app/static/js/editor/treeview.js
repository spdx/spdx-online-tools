$(document).ready(function(){
    var xml = $("#xmlText").val();
    xml = xml.replace(/>\s{0,}</g,"><");
    var tree = $.parseXML(xml);
    traverse($('#treeView li'),tree.firstChild)
    $('<img src="/static/images/plus.png" class="expand"><img src="/static/images/minus.png" class="collapse">').prependTo('#treeView li:has(li)');

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
    
    $(document).on('click','span.attribute-value',function(){
        var value = $(this).text();
        $('<input type="text" value="'+value+'"><img src="/static/images/tick.png" class="editAttribute"><img src="/static/images/removeNode.png" class="removeAttribute">').insertAfter($(this));
        $(this).css("display","none");
        $(".editAttribute").on("click", function(){
            value = $(this).prev().val();
            if(value == ""){
                alert("Please enter a valid attribute value.");
            }
            else{
                $(this).prev().prev().css("display","inline-block").text(value);
                $(this).prev().remove();
                $(this).next().remove();
                $(this).remove();
            }
        })
        $(".removeAttribute").on("click", function(){
            if(confirm("Are you sure you want to delete this attribute? This action cannot be undone.")==true){
                for(var i=0;i<5;i++) $(this).prev().remove();
                $(this).remove();
            }
        })
    });

    $(document).on('click',"img.addAttribute",function(){
        $(this).next().css("display","inline-block");
        $(this).css("display","none");
    });

    $(document).on('click','button.cancel',function(){
        $(this).parent().css("display","none");
        $(this).parent().prev().css("display","inline-block");
    });

    $(document).on('click','button.addNewAttribute',function(){
        var name = $(this).siblings(".newAttributeName").val();
        var value = $(this).siblings(".newAttributeValue").val();
        if(name=="" || value==""){
            alert("Please enter both attribute name and value");
        }
        else{
            $(this).parent().css("display","none");
            $(this).parent().prev().css("display","inline-block");
            $('<span class="attribute-name">'+name+'</span><span class="equal">=</span><span class="attribute-value">'+value+'</span>').insertBefore($(this).parent().siblings(".addAttribute"));
            $(this).siblings(".newAttributeName").val("");
            $(this).siblings(".newAttributeValue").val("");
        }
    });

    $(document).on('click','img.deleteNode',function(){
        if(confirm("Are you sure you want to delete this tag? This cannot be undone.")==true){
            $(this).parent().empty();
            $(this).parent().remove();
        }
    })

    $(document).on('click','li.nodeText',function(){
        var value = $(this).text();
        $('<textarea rows="5" cols="70">'+value+'</textarea><br><button class="editNodeText">Save</button><button class="cancelEditNodeText">Cancel</button>').insertAfter($(this));
        $(this).next().focus();
        $(this).css("display","none");
        $(".editNodeText").on("click", function(){
            value = $(this).prevUntil("textarea").prev().val();
            if(value == ""){
                value = "empty value";
            }
            $(this).prevUntil("li.nodeText").remove();
            $(this).prev("li.nodeText").css("display","inline-block").text(value);
            $(this).next("button.cancelEditNodeText").remove();
            $(this).remove();
        })
        $(".cancelEditNodeText").on("click", function(){
            $(this).prevUntil("li.nodeText").remove();
            $(this).prev("li.nodeText").css("display","inline-block");
            $(this).remove();
        })
    })

    $(document).on('click','li.emptyText',function(){
        var value = "";
        $('<textarea rows="5" cols="70">'+value+'</textarea><br><button class="editNodeText">Save</button><button class="cancelEditNodeText">Cancel</button>').insertAfter($(this));
        $(this).next().focus();
        $(this).css("display","none");
        $(".editNodeText").on("click", function(){
            value = $(this).prevUntil("textarea").prev().val();
            if(value == ""){
                value = "(No text value. Click to edit.)";
                $(this).prevUntil("li.emptyText").remove();
                $(this).prev("li.emptyText").css("display","inline-block").text(value);
                $(this).next("button.cancelEditNodeText").remove();
                $(this).remove();
            }
            else{
                $(this).prevUntil("li.emptyText").remove();
                $(this).prev("li.emptyText").remove();
                $(this).next("button.cancelEditNodeText").remove();
                $('<li class="nodeText">'+ value +'</li>').insertAfter($(this));
                $(this).remove();
            }
        })
        $(".cancelEditNodeText").on("click", function(){
            $(this).prevUntil("li.emptyText").remove();
            $(this).prev("li.emptyText").css("display","inline-block");
            $(this).remove();
        })
    })

    $(document).on('click','li.addChild',function(){
        $('<input type="text"><button class="buttonAddChild">Create Child</button><button class="cancelAddChild">Cancel</button>').insertAfter($(this));
        $(this).css("display","none");
        $(".buttonAddChild").click(function(){
            var value = $(this).prev().val();
            if(value==""){
                alert("Please enter a valid child name.");
            }
            else{
                $(this).parent().append('<li><img src="/static/images/plus.png" class="expand"><img src="/static/images/minus.png" class="collapse"><span class="nodeName">'+value+'</span><img class="addAttribute" src="/static/images/addAttribute.png"><div class="newAttributeContainer"> <input type="text" class="newAttributeName">=<input type="text" class="newAttributeValue"><button class="addNewAttribute">Add Attribute</button><button class="cancel">Cancel</button></div><img class="deleteNode" src="/static/images/removeNode.png"><ul><li class="emptyText">(No text value. Click to edit.)</li><li class="addChild last">Add Child</li></ul></li>');
                $(this).prev().remove();
                $(this).next().remove();
                $(this).prev().css("display","block");
                $(this).remove();
            }
        })
        $(".cancelAddChild").click(function(){
            $(this).prevUntil("li.addChild").remove();
            $(this).prev().css("display","block");
            $(this).remove();
        })
    })
});

function traverse(node,tree) {
    var children=$(tree).children();
    node.append('<span class="nodeName">'+tree.nodeName+'</span>');
    if(tree.attributes){
        $.each(tree.attributes, function(i, attrib){
            node.append('<span class="attribute-name">'+attrib.name+'</span><span class="equal">=</span><span class="attribute-value">'+attrib.value+"</span>");
        })
    }
    node.append('<img class="addAttribute" src="/static/images/addAttribute.png"><div class="newAttributeContainer"> <input type="text" class="newAttributeName">=<input type="text" class="newAttributeValue"><button class="addNewAttribute">Add Attribute</button><button class="cancel">Cancel</button></div><img class="deleteNode" src="/static/images/removeNode.png">')
    if (children.length){
        var ul=$("<ul>").appendTo(node);
        $('<li class="emptyText">(No text value. Click to edit.)</li><li class="addChild last">Add Child</li>').appendTo(ul);
        children.each(function(){
            var li=$('<li>').appendTo(ul);
            traverse(li,this);
        })
    }
    else{
        $('<ul><li class="nodeText">'+ $(tree).text()+'</li><li class="addChild last">Add Child</li></ul>').appendTo(node);
    }
}