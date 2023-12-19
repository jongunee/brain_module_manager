$(document).ready(function () {
  $("#upload-form").submit(function (event) {
    event.preventDefault();

    var framework = $("#file_framework").val();
    var extension = $("#extension").val();
    var input_type = $("#input_type").val();
    var output_type = $("#output_type").val();
    if (!framework) {
      alert("Please select a framework.");
      return;
    }
    if (!extension) {
      alert("Please select an extension.");
      return;
    }
    if (!input_type) {
      alert("Please select a input type.");
      return;
    }
    if (!output_type) {
      alert("Please select an output type.");
      return;
    }
    var formData = new FormData(this);
    formData.append("framework", framework);
    formData.append("extension", extension);
    formData.append("input_type", input_type);
    formData.append("output_type", output_type);

    $.ajax({
      url: "/upload",
      type: "POST",
      data: formData,
      contentType: false,
      processData: false,
      success: function (response) {
        $("#message").text(response);
      },
      error: function (xhr, status, error) {
        $("#message").text("Failed to upload file: " + xhr.responseText);
      },
    });
  });
});
