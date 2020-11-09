async function takeScreenshotAndUpload() {
  let screenshot = await makeScreenshot();
  let data = await getFileData(screenshot);
  return await postToGithub(data);
}

async function makeScreenshot(selector = ".modal-content") {
  return new Promise((resolve, reject) => {
    let region = document.querySelector(selector);

    html2canvas(region, {
      onrendered: canvas => {
        let pngUrl = canvas.toDataURL();
        resolve(pngUrl);
      }
    });
  });
}

async function getFileData(imgUrl) {
  return new Promise((resolve, reject) => {
    resolve({
      message: "Upload diff image",
      content: imgUrl.split(",")[1]
    });
  });
}

async function postToGithub(data) {
  let fileurl = null;
  $.ajax({
        type: "POST",
        enctype: 'multipart/form-data',
        url: "/app/post_to_github/",
        dataType: 'json',
		async: false,
        timeout: 600000,
        data: data,
        success: function (data) {
            var githubCode = data.statusCode;
            if(githubCode == '201'){
              fileurl = data.fileurl
            }
            else {
              var warningMessage = "Please note that there was a problem opening the issue for the SPDX legal team. Please email spdx-legal@lists.spdx.org with SPDX ID for the license you are submitting";
              $("#messages").html('<div class="alert alert-warning alert-dismissable fade in"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a><strong>Warning! </strong>'+ warningMessage +'</div>');
                  setTimeout(function() {
                    $("#messages").html("");
                  }, 7000);
            }
        },
        error: function (e) {
            console.log("ERROR : ", e);
            $("#modal-header").removeClass("green-modal");
            try {
            var obj = JSON.parse(e.responseText);
            if (obj.type=="error"){
                $("#modal-header").removeClass("yellow-modal");
                $("#modal-header").addClass("red-modal");
                $("#modal-title").html("Error!");
            }
            $("#modal-body").text(obj.data);
            $(".modal-footer").html('<button id="ok"><span class="glyphicon glyphicon-ok"></span> Ok</button>');
            $("#ok").on("click",function(){
                $("#myModal").modal("hide");
                $(".modal-footer").html("");
            })
            }
            catch (e){
                $("#modal-header").removeClass("yellow-modal");
                $("#modal-header").addClass("red-modal");
                $("#modal-title").html("Error!");
                $("#modal-body").text("The application could not be connected. Please try later.");
            }
            $("#myModal").modal({
                backdrop: 'static',
                keyboard: true,
                show: true
            });
        }
    });
  return fileurl;
}
