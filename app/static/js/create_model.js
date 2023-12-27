$(document).ready(function () {
  // 동적으로 생성된 요소에도 이벤트 핸들러를 적용
  $(document).on("click", ".create-model-btn", function () {
    var model_name = $(this).data("model-name");
    var framework = $(this).data("framework");
    var extension = $(this).data("extension");
    $.ajax({
      url: "/create",
      type: "POST",
      contentType: "application/json;charset=utf-8",
      data: JSON.stringify({
        model_name: model_name,
        framework: framework,
        extension: extension,
      }),
      success: function (response) {
        alert("모델 생성 성공: " + response.model_name);
      },
      error: function (xhr, status, error) {
        alert("모델 생성 실패: " + xhr.responseText);
      },
    });
  });
});