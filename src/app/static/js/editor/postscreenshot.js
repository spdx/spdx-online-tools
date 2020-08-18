async function takeScreenshotAndUpload(repositoryNameWithOwner, githubToken) {
  let screenshot = await makeScreenshot();
  let data = await getFileData(screenshot);
  await postToGithub(data, repositoryNameWithOwner, githubToken);
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

async function postToGithub(data, repositoryNameWithOwner, githubToken) {
  let xhr = new XMLHttpRequest();
  let filename =
    Math.random()
      .toString(36)
      .substring(3) + ".png";

  localStorage.setItem("filename", filename);
  apiurl =
    "https://api.github.com/repos/" +
    repositoryNameWithOwner +
    "/contents/" +
    filename;
  xhr.open("PUT", apiurl);
  xhr.setRequestHeader("Authorization", "Token " + githubToken);
  xhr.send(JSON.stringify(data));
}
