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
