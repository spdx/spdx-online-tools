let MAX_FILE_SIZE = 10485760; // 10 MB in bytes
let MAX_FILE_SIZE_STR = "10MB";
function checkFileSize(file, warningElementJQ) {
    if (file && file.size > MAX_FILE_SIZE) {
        $(warningElementJQ).prop("hidden", false)
            .html("WARNING: The file size exceeds the max supported file size " + MAX_FILE_SIZE_STR +
                ". The application may return timeout. Use <a href='https://github.com/spdx/tools/'>cli tools</a> " +
                "for better experience with large files").css("color", "red");
        return true;

    } else {
        return false;
    }
}

function checkFilesSize(files, warningElementJQ) {
    var ret = false;
    for (let i = 0; i < files.length; i++) {
        ret = checkFileSize(files[i], warningElementJQ);
        if (ret) {
            break;
        }
    }
    if (!ret) {
        removeWarningElement(warningElementJQ);
    }
}

function removeWarningElement(warningElementJQ) {
    $(warningElementJQ).prop("hidden", true);
}