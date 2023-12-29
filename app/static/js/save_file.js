$(document).ready(function () {
  $("#upload-form").submit(function (event) {
    event.preventDefault();

    // 입력 값 검증
    var framework = $("#file-framework").val();
    var extension = $("#extension").val();
    var input_type = $("#input-type").val();
    var output_type = $("#output-type").val();
    // var api_type = $("#api-type").val();
    // var api_key = $("#api-key").val();
    // var api_value = $("#api-value").val();
    // 입력 값이 누락된 경우 경고
    if (
      !framework ||
      !extension ||
      !input_type ||
      !output_type
      // !api_type ||
      // !api_key ||
      // !api_value
    ) {
      alert("Please fill in all fields.");
      return;
    }

    // JSON 객체 생성
    var api_data = {};
    // api_data[api_key + ":" + api_type] = api_value;

    $("#api-inputs li").each(function () {
      var api_type = $(this).find("span").eq(0).text().slice(1, -1);
      var api_key = $(this).find("span").eq(1).text().slice(0, -2);
      var api_value = $(this).find("span").eq(2).text();
      if (api_type && api_key && api_value) {
        api_data[api_key + ":" + api_type] = api_value;
      }
    });

    // FormData 객체 생성 및 데이터 추가
    var formData = new FormData(this);
    formData.append("framework", framework);
    formData.append("extension", extension);
    formData.append("input_type", input_type);
    formData.append("output_type", output_type);
    formData.append("api_data", JSON.stringify(api_data));

    // AJAX 요청
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
