/*
  [script.js] - 기능(동작)을 담당하는 파일
  JavaScript는 웹페이지를 '움직이게' 만듭니다.
  버튼 클릭, 랜덤 미션 선택, 횟수 카운트 등이 여기에 있어요.
*/


/* ─────────────────────────────────────────
  미션 목록
  배열(Array): 여러 값을 대괄호 [] 안에 쉼표로 나열한 것
  총 15개의 미션이 들어 있습니다.
───────────────────────────────────────── */
var missions = [
  "20초 동안 창밖 바라보기 👀",
  "눈 감고 천천히 숨 쉬기 😌",
  "어깨 힘 빼고 자세 리셋하기 🪑",
  "손바닥 비벼서 눈에 살짝 대기 🙌",
  "눈 천천히 깜빡이기 10번 ✨",
  "목을 좌우로 천천히 돌리기 🔄",
  "화면 밝기 한 칸 낮추기 🌙",
  "허리 쭉 펴고 깊게 숨 쉬기 🌿",
  "물 한 모금 마시기 💧",
  "30초 동안 화면 완전 끄기 🛑",
  "책상에서 잠깐 시선 떼기 🌟",
  "눈 감고 10초 완전히 쉬기 💤",
  "손 털고 손목 가볍게 돌리기 🤲",
  "창밖 제일 먼 곳 찾아보기 🏔️",
  "코로 들이쉬고 입으로 내쉬기 🌬️"
];


/* ─────────────────────────────────────────
  변수 선언
  var: 값을 저장하는 상자(변수)를 만드는 키워드
───────────────────────────────────────── */

// 완료 횟수를 기억하는 변수 (처음엔 0)
var count = 0;


/* ─────────────────────────────────────────
  함수: newMission()
  "새 미션 받기" 버튼을 누르면 실행됩니다.
───────────────────────────────────────── */
function newMission() {

  /* ① 랜덤 번호 뽑기
     - Math.random() : 0 이상 1 미만의 소수를 무작위로 반환 (예: 0.73)
     - missions.length : 배열의 길이, 즉 15
     - 곱하면 0 이상 15 미만의 소수 (예: 10.95)
     - Math.floor() : 소수점을 버려서 정수로 (예: 10)
     - 결과: 0~14 사이의 정수 → 배열 인덱스로 사용 */
  var index = Math.floor(Math.random() * missions.length);

  /* ② 뽑은 번호에 해당하는 미션 텍스트 가져오기 */
  var selectedMission = missions[index];

  /* ③ HTML 요소 찾기
     - document.getElementById('아이디') : HTML에서 id가 일치하는 요소를 가져옴 */
  var beforeArea  = document.getElementById('before');
  var afterArea   = document.getElementById('after');
  var missionNum  = document.getElementById('mission-num');
  var missionText = document.getElementById('mission-text');
  var doneBtn     = document.getElementById('done-btn');

  /* ④ 안내 문구 숨기기 → 미션 내용 보이기
     - classList.add('hidden')    : .hidden 클래스를 붙여서 숨김
     - classList.remove('hidden') : .hidden 클래스를 떼어서 보이게 함 */
  beforeArea.classList.add('hidden');
  afterArea.classList.remove('hidden');

  /* ⑤ 미션 번호 표시 (배열 인덱스는 0부터 시작하니까 +1 해야 1번부터 표시됨) */
  missionNum.textContent = 'MISSION ' + (index + 1);

  /* ⑥ 미션 텍스트 표시
     - textContent : 태그 안의 글자 내용을 바꿔주는 속성
     - 애니메이션을 다시 재생하기 위해 잠깐 none으로 껐다가 켭니다 */
  missionText.style.animation = 'none';
  missionText.offsetHeight;          // 브라우저가 변경사항을 인식하도록 강제
  missionText.style.animation = '';
  missionText.textContent = selectedMission;

  /* ⑦ 완료 버튼 보이기 */
  doneBtn.classList.remove('hidden');
}


/* ─────────────────────────────────────────
  함수: doneMission()
  "미션 완료!" 버튼을 누르면 실행됩니다.
───────────────────────────────────────── */
function doneMission() {

  /* ① 완료 횟수 1 증가 */
  count = count + 1;    // count += 1 이라고 써도 같은 의미

  /* ② 화면의 숫자 업데이트 */
  var countEl = document.getElementById('count');
  countEl.textContent = count;

  /* ③ 숫자가 '통통' 튀는 애니메이션 효과
     - bump 클래스를 잠깐 붙였다가(200ms 후) 다시 떼어냄 */
  countEl.classList.add('bump');
  setTimeout(function () {
    countEl.classList.remove('bump');
  }, 200);
  // setTimeout : 일정 시간(ms) 뒤에 함수를 실행 (200ms = 0.2초)

  /* ④ 미션 카드와 완료 버튼을 초기 상태로 되돌리기 */
  var beforeArea = document.getElementById('before');
  var afterArea  = document.getElementById('after');
  var doneBtn    = document.getElementById('done-btn');

  afterArea.classList.add('hidden');
  doneBtn.classList.add('hidden');
  beforeArea.classList.remove('hidden');
}
