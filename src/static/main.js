let filesArray = [];

// 👇 各模块的正则表达式、错误信息、示例
const moduleConfig = {
    CA: {
        pattern: /^\d+_.*/i,
        reason: "The filename must start with a number",
        example: "Example: 1_sample.xlsx"
    },
    CV: {
        pattern: /^.*\d+mVs/i,
        reason: "The filename must include scan rate (e.g., '100mVs')",
        example: "Example: NiFoam_100mVs.xlsx"
    },
    HDV: {
        pattern: /^.*\d+rpm/i,
        reason: "The filename must include rotation speed (e.g., '800rpm')",
        example: "Example: Ni_P_800rpm.xlsx"
    }
};

// 👇 当前模块，从 URL 中判断
function detectModuleFromURL() {
    const url = window.location.href.toUpperCase();
    if (url.includes("/CV")) return "CV";
    if (url.includes("/HYD")) return "HDV";
    return "CA"; // 默认模块
}

const currentModule = detectModuleFromURL();
console.log("currentmodule:", currentModule);
const {pattern, reason, example} = moduleConfig[currentModule];
const allowedExtensions = [".xlsx", ".tsv", ".txt", ".csv"];

// 👇 更新文件列表并显示错误信息
function updateFileList() {
    const fileListDisplay = document.getElementById('file-list');
    const fileCountDisplay = document.getElementById('file-message');

    fileListDisplay.innerHTML = '';

    filesArray.forEach((file, index) => {
        const filename = file.name;
        const ext = filename.slice(filename.lastIndexOf(".")).toLowerCase();
        const baseName = filename.slice(0, filename.lastIndexOf("."));

        let errorMsg = "";
        if (!allowedExtensions.includes(ext)) {
            errorMsg = "Unsupported file type (.xlsx, .tsv, .txt only)";
        } else if (!pattern.test(baseName)) {
            errorMsg = `${reason}<br>${example}`;
        }

        const div = document.createElement('div');
        div.className = 'file-item';
        div.innerHTML = `
            <button onclick="removeFile(${index})">❌</button>
            <span>${filename}</span>
            ${errorMsg ? `<div style="color: red; font-size: 0.9em;">${errorMsg}</div>` : ''}
        `;

        fileListDisplay.appendChild(div);
    });

    fileCountDisplay.textContent = filesArray.length + ' file(s) selected';
}

function removeFile(index) {
    filesArray.splice(index, 1);
    updateFileList();
}

function handleFiles(files) {
    for (let file of files) {
        const alreadyAdded = filesArray.some(f => f.name === file.name && f.size === file.size);
        if (!alreadyAdded) {
            filesArray.push(file);
        }
    }
    updateFileList();
}

$(document).on('change', '.file-input', function (e) {
    // handleFiles($(this)[0].files);
    handleFiles(e.target.files);
});

$(document).on('dragover', '.file-input', function () {
    const dropArea = document.getElementById('file-drop-area');
    dropArea.classList.add('highlight');
});

$(document).on('dragleave', '.file-input', function () {
    const dropArea = document.getElementById('file-drop-area');
    dropArea.classList.remove('highlight');
});

$(document).on('drop', '.file-input', function () {
    const dropArea = document.getElementById('file-drop-area');
    dropArea.classList.remove('highlight');
    handleFiles($(this)[0].files)
});


function submitForm() {
    // var fileInput = document.querySelector('.file-input');
    // var files = fileInput.files;
    var files = document.getElementById('file-input').files;
    if (files.length === 0) {
        document.getElementById('upload-message').innerText = 'Please upload files';
    } else {
        // Proceed with file upload or other actions
        document.getElementById('upload-message').innerText = '';

        $('#loadingModal').modal('show');

        var formData = new FormData();

        for (var i = 0; i < files.length; i++) {
            formData.append('files[]', files[i]);
        }
        formData.append('module', 'HDV');

        var input_sigma = document.getElementById("input_sigma").value;
        formData.append('sigma', input_sigma);

        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload', true);
        xhr.onload = function () {
            if (xhr.status === 200) {
                var response = JSON.parse(xhr.responseText);
                console.log(response);

                $('#loadingModal').modal('hide');

                if (response.status === true) {
                    // var image1 = document.getElementById('img1');
                    // image1.src = response.file1
                    //
                    // var image2 = document.getElementById('img2');
                    // image2.src = response.file2
                    //
                    // document.getElementById('form_input').style.display = 'none';
                    // document.getElementById('form_result').style.display = 'block';

                    // 指定要跳转的 URL
                    var targetURL = "/hyd_elec/" + response.version + '?step=2';
                    window.location.href = targetURL;
                } else {
                    alert(response.message);
                }
                // alert('Files uploaded successfully');
            } else {
                alert('Error uploading files');
            }
        };
        xhr.send(formData);
    }
}


function submitFormCV1() {
    // var fileInput = document.querySelector('.file-input');
    // var files = fileInput.files;
    var files = document.getElementById('file-input').files;
    if (files.length === 0) {
        document.getElementById('upload-message').innerText = 'Please upload files';
    } else {
        // Proceed with file upload or other actions
        document.getElementById('upload-message').innerText = '';

        $('#loadingModal').modal('show');

        var formData = new FormData();

        for (var i = 0; i < files.length; i++) {
            formData.append('files[]', files[i]);
        }

        var input_sigma = document.getElementById("input_sigma").value;
        var input_cycle = document.getElementById("input_cycle").value;
        formData.append('module', 'CV');
        formData.append('sigma', input_sigma);
        formData.append('cycle', input_cycle);
        formData.append('step', '1');

        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload', true);
        xhr.onload = function () {
            if (xhr.status === 200) {
                var response = JSON.parse(xhr.responseText);
                console.log(response);

                $('#loadingModal').modal('hide');

                if (response.status === true) {
                    // var image1 = document.getElementById('form2_img1');
                    // image1.src = response.file1
                    //
                    // var image2 = document.getElementById('form2_img2');
                    // image2.src = response.file2
                    // var sigma = document.getElementById('form2_sigma');
                    // sigma.textContent = input_sigma
                    //
                    // var version = document.getElementById('version');
                    // version.value = response.version
                    //
                    //
                    // document.getElementById('form1').style.display = 'none';
                    // document.getElementById('form2').style.display = 'block';
                    // document.getElementById('form3').style.display = 'none';

                    // 指定要跳转的 URL
                    var targetURL = "/cv/" + response.version + '?step=2';
                    window.location.href = targetURL;
                } else {
                    alert(response.message);
                }
                // alert('Files uploaded successfully');
            } else {
                alert('Error uploading files');
            }
        };
        xhr.send(formData);
    }
}


function tryAgain() {

    // document.getElementById('form_input').reset();
    document.getElementById('form_input').style.display = '';
    document.getElementById('form_result').style.display = 'none';
}

function goBack() {
    window.history.back();
}

function callAPI(URL) {
    // 模拟调用 API
    const intervalId = setInterval(function () {

        // 发送请求到你的 API
        fetch(URL)
            .then(response => response.json())
            .then(data => {
                // 检查 API 返回结果是否为 "done"
                if (data.result === "done") {
                    // 如果是，则刷新当前页面
                    location.reload();
                } else if (data.result.startsWith("error")) {
                    // 如果是 error，显示服务器错误。
                    clearInterval(intervalId);
                    const progressBarDiv = document.getElementById("progress_bar");
                    progressBarDiv.innerHTML = `
                            <div class="alert alert-danger" role="alert">
                                ${data.result}
                            </div>
                        `;
                } else if (data.result !== "processing") {
                    // 如果是 error，显示服务器错误。
                    clearInterval(intervalId);
                    const progressBarDiv = document.getElementById("progress_bar");
                    progressBarDiv.innerHTML = `
                            <div class="alert alert-danger" role="alert">
                                An error occurred on the server.
                            </div>
                        `;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                clearInterval(intervalId);
                const progressBarDiv = document.getElementById("progress_bar");
                progressBarDiv.innerHTML = `
                        <div class="alert alert-danger" role="alert">
                            Failed to contact the server. Please try again later.
                        </div>
                    `;
            });
    }, 1000); // 每隔一秒调用一次 API
}