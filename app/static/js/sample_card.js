// 順位カードを順番にフェードイン
document.querySelectorAll(".ranking-card").forEach((card, i) => {
  card.style.opacity = "0";
  card.style.transform = "translateY(20px)";
  setTimeout(() => {
    card.style.transition = "all 0.5s ease";
    card.style.opacity = "1";
    card.style.transform = "translateY(0)";
    // 1位はちょっと弾む
    if (i === 0) {
      card.style.transform = "scale(1.05)";
      setTimeout(() => { card.style.transform = "scale(1)"; }, 300);
    }
  }, i * 200);
});

// メニューボタンとサイドメニューを制御
/*
document.addEventListener("DOMContentLoaded", () => {//"DOMContentLoaded" でJSがHTMLより先に動いてエラーになるのを防ぐ。
  const menuButton = document.getElementById("menu-button");
  const sideMenu = document.getElementById("side-menu");

  menuButton.addEventListener("click", () => {
    sideMenu.classList.toggle("open");
  });
});
*/
document.addEventListener("DOMContentLoaded", () => {//オーバーレイ表示
  const menuButton = document.getElementById("menu-button");
  const sideMenu = document.getElementById("side-menu");
  const overlay = document.getElementById("overlay");

  menuButton.addEventListener("click", () => {
    sideMenu.classList.toggle("open");
    overlay.classList.toggle("active");
  });

  // 背景をクリックしたら閉じる
  overlay.addEventListener("click", () => {
    sideMenu.classList.remove("open");
    overlay.classList.remove("active");
  });
});