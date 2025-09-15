// adjustNameFont.js (ランキングの名前表示を、名前が長いと調整してくれる)
function adjustNameFont() {
    const nameLinks = document.querySelectorAll('.info .name a');

    nameLinks.forEach(a => {
        const parentWidth = a.parentElement.offsetWidth;
        a.style.fontSize = ''; // まず元サイズに戻す

        let fontSize = parseFloat(window.getComputedStyle(a).fontSize);

        while(a.scrollWidth > parentWidth && fontSize > 10){ // 最小10px
            fontSize -= 1;
            a.style.fontSize = fontSize + 'px';
        }
    });
}

// ページ読み込み時
window.addEventListener('load', adjustNameFont);

// ウィンドウサイズ変更時（レスポンシブ対応）
window.addEventListener('resize', adjustNameFont);
