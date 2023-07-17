$(document).ready(function () {
  $(".run-button").click(function (event) {
    event.preventDefault();

    const config = {
      framework: $(this).closest("tr").find(".input-framework").val(),
      model_name: $(this).closest("tr").find(".input-model-name").val(),
      input_type: $(this).closest("tr").find(".input-input-type").val(),
      output_type: $(this).closest("tr").find(".input-output-type").val(),
    };

    console.log("Sending config_data:", config);

    $.ajax({
      url: "/service",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify(config),
      success: function (response) {
        alert("Service started.");
      },
      error: function (error) {
        alert("Error: " + error);
      },
    });
  });
});
