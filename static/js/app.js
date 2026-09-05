// Medical Records System Client Script

document.addEventListener("DOMContentLoaded", () => {
    // Auto-dismiss alerts after 6 seconds
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 6000);
    });

    // Image Zoom Controls in Verification Interface
    const reportImg = document.getElementById("reportViewerImg");
    const zoomInBtn = document.getElementById("zoomInBtn");
    const zoomOutBtn = document.getElementById("zoomOutBtn");
    const resetZoomBtn = document.getElementById("resetZoomBtn");

    if (reportImg && zoomInBtn && zoomOutBtn && resetZoomBtn) {
        let currentScale = 1.0;

        zoomInBtn.addEventListener("click", () => {
            currentScale = Math.min(currentScale + 0.25, 3.0);
            reportImg.style.transform = `scale(${currentScale})`;
            reportImg.style.transformOrigin = "top center";
        });

        zoomOutBtn.addEventListener("click", () => {
            currentScale = Math.max(currentScale - 0.25, 0.5);
            reportImg.style.transform = `scale(${currentScale})`;
            reportImg.style.transformOrigin = "top center";
        });

        resetZoomBtn.addEventListener("click", () => {
            currentScale = 1.0;
            reportImg.style.transform = "scale(1.0)";
        });
    }

    // Dynamic Filter for Profile Laboratory Results Table
    const searchInput = document.getElementById("labTableSearch");
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            const query = e.target.value.toLowerCase();
            const rows = document.querySelectorAll("#labResultsTable tbody tr");
            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(query) ? "" : "none";
            });
        });
    }
});
