// SPDX-FileCopyrightText: 2025 SPDX Contributors
// SPDX-License-Identifier: Apache-2.0

/* Render a side-by-side diff inline in the result section */
function generate_text_diff(base, newtxt) {
  var sm = new difflib.SequenceMatcher(base, newtxt);
  var opcodes = sm.get_opcodes();
  var diffEl = diffview.buildView({
    baseTextLines: base,
    newTextLines: newtxt,
    opcodes: opcodes,
    baseTextName: "SPDX license text",
    newTextName: "Your license text",
    contextSize: null,
    viewType: 1,
  });
  $(diffEl).find('thead').remove();
  $(diffEl).find('th').remove();

  var body = document.getElementById('result-body');
  body.className = 'result-body diff-result-body';
  body.innerHTML = '';
  body.appendChild(diffEl);

  var section = document.getElementById('result-section');
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });
  section.focus();
}

function findLicenseMatch(request, onComplete) {
  $.ajax({
    ...request,
    success: function (data) {
      console.log("SUCCESS : ", data);
      var matchType = data.matchType;
      var matchIds = data.matchIds;
      if (matchType == "Close match") {
        var inputLicenseText = data.inputLicenseText.replace(/\r\n/g, "\n");
        var originalLicenseText = data.originalLicenseText;
        var matchingGuidelinesUrl =
          "https://spdx.github.io/spdx-spec/latest/annexes/license-matching-guidelines-and-templates/";
        var bodyHtml =
          '<p>Close match found! The license closely matches with the license ID(s): ' +
          '<strong>' + $('<span>').text(matchIds).html() + '</strong> ' +
          'based on the SPDX Matching guidelines.</p>' +
          '<div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;">' +
          '<a href="' + matchingGuidelinesUrl + '" target="_blank" rel="noopener" ' +
          '   class="btn btn-default">' +
          '  <span class="glyphicon glyphicon-link" aria-hidden="true"></span>' +
          '  SPDX Matching Guidelines</a>' +
          '<button type="button" class="btn btn-default" id="showDiff">' +
          '  <span class="glyphicon glyphicon-search" aria-hidden="true"></span>' +
          '  Show differences</button>' +
          '</div>';

        showResult("warning", "Close match", bodyHtml);

        // Store texts for the diff so the click handler can reach them
        document.getElementById("showDiff")._baseText = originalLicenseText;
        document.getElementById("showDiff")._inputText = inputLicenseText;

        $(document).off("click.showDiff").on("click.showDiff", "#showDiff", function () {
          var base = this._baseText.split("\n\n");
          var newtxt = this._inputText.split("\n\n");
          generate_text_diff(base, newtxt);
          });
      } else if (
        matchType == "Perfect match" ||
        matchType == "Standard License match"
      ) {
        showResult(
          "success",
          "Match found",
          '<p>Perfect match! The license matches with the license ID(s): ' +
          '<strong>' + $('<span>').text(matchIds).html() + '</strong></p>'
        );
      } else {
        showResult(
          "error",
          "No match",
          "<p>The given license was not found in the SPDX database.</p>"
        );
      }
      $("#licensediffbutton").text("License diff");
      $("#licensediffbutton").prop("disabled", false);
      if (onComplete) onComplete();
    },
    error: function (e) {
      console.log("ERROR : ", e);
      try {
        var obj = JSON.parse(e.responseText);
        showResult("error", "Error", '<p>' + $('<span>').text(obj.data).html() + '</p>');
      } catch (_) {
        showResult(
          "error",
          "Error",
          "<p>The application could not be connected. Please try later.</p>"
        );
      }
      $("#licensediffbutton").text("Check license");
      $("#licensediffbutton").prop("disabled", false);
      if (onComplete) onComplete();
    },
  });
}
