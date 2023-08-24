function doRequest(dict1) {
  $.ajax({
    ...dict1,
    success: function (data) {
      console.log("SUCCESS : ", data);
      var matchType = data.matchType;
      var matchIds = data.matchIds;
      if (matchType == "Close match") {
        $("#modal-header").addClass("yellow-modal");
        var inputLicenseText = data.inputLicenseText.replace(/\r\n/g, "\n");
        var originalLicenseText = data.originalLicenseText;
        var matchingGuidelinesUrl =
          "https://spdx.org/spdx-license-list/matching-guidelines";
        var message = `Close match found! The license closely matches with the license ID(s): <strong>${matchIds}</strong> based on the SPDX Matching guidelines. Press show differences to continue.`;
        $("#modal-header").removeClass("red-modal green-modal");
        $("#modal-header").addClass("yellow-modal");
        $(".modal-footer").html(
          `<a href=${matchingGuidelinesUrl} target="_blank"><button class="btn btn-success btn-space" id="matchingguidelines"><span class="glyphicon glyphicon-link"></span> SPDX Matching Guidelines</button></a><button class="btn btn-success btn-space" id="showDiff"><span class="glyphicon glyphicon-link"></span> Show differences</button>`
        );
        $("#modal-body").html(message);
        $("#myModal").modal({
          backdrop: "static",
          keyboard: true,
          show: true,
        });
        $(document).on("click", "button#ok", function (event) {
          $("#myModal").modal("hide");
        });
        $(document)
          .off()
          .on("click", "button#showDiff", function (event) {
            generate_text_diff(
              originalLicenseText.split("\n\n"),
              inputLicenseText.split("\n\n")
            );
          });
      } else if (
        matchType == "Perfect match" ||
        matchType == "Standard License match"
      ) {
        var message = `Perfect match found! The license matches with the license ID(s): <strong>${matchIds}</strong>`;
        $("#modal-header").addClass("green-modal");
        $("#modal-title").html("Found!");
        $("#modal-body").html(message);
      } else {
        $("#modal-header").addClass("red-modal");
        $("#modal-title").html("Not Found!");
        var message = "The given license was not found in the SPDX database.";
        $("#modal-body").html("<h3>" + message + "</h3>");
      }
      $("#myModal").modal({
        backdrop: "static",
        keyboard: true,
        show: true,
      });
      $("#licensediffbutton").text("License diff");
      $("#licensediffbutton").prop("disabled", false);
    },
    error: function (e) {
      console.log("ERROR : ", e);
      $("#modal-header").removeClass("green-modal");
      try {
        var obj = JSON.parse(e.responseText);
        $("#modal-header").addClass("red-modal");
        $("#modal-title").html("Error!");
        $("#modal-body").text(obj.data);
      } catch (e) {
        $("#modal-header").addClass("red-modal");
        $("#modal-title").html("Error!");
        $("#modal-body").text(
          "The application could not be connected. Please try later."
        );
      }
      $("#myModal").modal({
        backdrop: "static",
        keyboard: true,
        show: true,
      });
      $("#licensediffbutton").text("Check License");
      $("#licensediffbutton").prop("disabled", false);
    },
  });
}
