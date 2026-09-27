document.addEventListener("DOMContentLoaded", function() {
    console.log("Sabda Custom StocksLy Modal Engine Active.");

    const tableRows = document.querySelectorAll("tbody tr");
    const modalOverlay = document.getElementById("modalOverlay");
    const modalClose = document.getElementById("modalClose");

    tableRows.forEach(row => {
        row.addEventListener("click", function() {
            // Pemetaan data attributes dari tabel HTML ke elemen Popup
            document.getElementById("popTicker").innerText = this.getAttribute("data-ticker");
            document.getElementById("popCompany").innerText = this.getAttribute("data-company");
            
            // 1. Ringkasan Strategi (Fundamental)
            document.getElementById("popRoe").innerText = this.getAttribute("data-roe") + "%";
            document.getElementById("popPer").innerText = this.getAttribute("data-per") + "x";
            document.getElementById("popMcap").innerText = this.getAttribute("data-mcap");

            // 2. Kondisi Harga Saat Ini
            document.getElementById("popLastPrice").innerText = this.getAttribute("data-price");
            document.getElementById("popRsi").innerText = this.getAttribute("data-rsi");
            document.getElementById("popVolatilitas").innerText = this.getAttribute("data-volatilitas");
            document.getElementById("popLiquidity").innerText = this.getAttribute("data-liquidity");

            // 3. Entry Area & Manajemen Risiko
            document.getElementById("popEntryArea").innerText = this.getAttribute("data-entry");
            document.getElementById("popTargetProfit").innerText = this.getAttribute("data-target");
            document.getElementById("popStopLoss").innerText = this.getAttribute("data-sl");

            // 4. Panel Keputusan Strategi Utama (Big Badge Custom Color)
            const action = this.getAttribute("data-action");
            const badgeClass = this.getAttribute("data-badge");
            const popBigAction = document.getElementById("popBigAction");
            
            popBigAction.innerText = action;
            popBigAction.className = "pop-big-action " + badgeClass;

            // Keterangan deskripsi dinamis ala dashboard
            const popDesc = document.getElementById("popDesc");
            if(action.includes("BUY")) {
                popDesc.innerText = "Sinyal telah terkonfirmasi. Struktur harga mendukung dengan volume akumulasi yang memadai. Eksekusi di area Entry.";
            } else if(action.includes("HOLD")) {
                popDesc.innerText = "Harga sudah naik dari area beli aman atau mendekati target profit teknikal. Direkomendasikan untuk menahan posisi atau pasang trailing stop.";
            } else {
                popDesc.innerText = "Struktur harga berada dalam tren turun (Downtrend) di bawah MA50 atau sepi akumulasi. Wait and See dan cari peluang di saham lain.";
            }

            modalOverlay.classList.add("active");
        });
    });

    modalClose.addEventListener("click", function() {
        modalOverlay.classList.remove("active");
    });

    modalOverlay.addEventListener("click", function(e) {
        if (e.target === modalOverlay) {
            modalOverlay.classList.remove("active");
        }
    });
});
