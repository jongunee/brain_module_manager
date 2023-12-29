function addApi() {
  // 1. 추가할 값을 input창에서 읽어온다
  const addType = document.getElementById("api-type").value;
  const addKey = document.getElementById("api-key").value;
  const addValue = document.getElementById("api-value").value;

  // 2. 추가할 li element 생성
  const li = document.createElement("li");

  // 키와 값을 위한 span 요소 생성
  const typeSpan = document.createElement("span");
  const keySpan = document.createElement("span");
  const valueSpan = document.createElement("span");

  // span에 텍스트 추가
  typeSpan.textContent = "[" + addType + "]";
  keySpan.textContent = addKey + ": "; // 키와 값 사이에 구분자 추가
  valueSpan.textContent = addValue;

  // li에 span 요소들 추가
  li.appendChild(typeSpan);
  li.appendChild(keySpan);
  li.appendChild(valueSpan);

  // 3. 생성된 li를 ul에 추가
  document.getElementById("api-inputs").appendChild(li);
}
