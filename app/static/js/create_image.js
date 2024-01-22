$(document).ready(function () {
  $(".image-button").click(function (event) {
    //새로 고침 방지
    event.preventDefault();

    const config = {
      framework: $(this).closest("tr").find(".framework").val(),
      model_name: $(this).closest("tr").find(".model-name").val(),
      input_type: $(this).closest("tr").find(".input-type").val(),
      output_type: $(this).closest("tr").find(".output-type").val(),
      api_data: $(this).closest("tr").find(".api-data").val(),
    };

    console.log("Sending config_data:", config);

    $.ajax({
      url: "/images",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify(config),
    })
      .done(function (response) {
        console.log("Image created!");
      })
      .fail(function (error) {
        console.log("Error: " + error);
      });
  });
});
