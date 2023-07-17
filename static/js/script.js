$(document).ready(function () {
  $(".run-button").click(function (event) {
    event.preventDefault();

    const config = {
      framework: $(this).closest("tr").find(".framework").val(),
      model_name: $(this).closest("tr").find(".model-name").val(),
      input_type: $(this).closest("tr").find(".input-type").val(),
      output_type: $(this).closest("tr").find(".output-type").val(),
    };

    console.log("Sending config_data:", config);

    $.ajax({
      url: "/service",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify(config),
    })
      .done(function (response) {
        alert("Service started!");
      })
      .fail(function (error) {
        alert("Error: " + error);
      });
  });
});
