document.addEventListener("DOMContentLoaded", () => {
    // Graphique d'état
    const stateChartElement = document.getElementById('stateChart');
    const totalUp = parseInt(stateChartElement.dataset.totalUp);
    const totalDown = parseInt(stateChartElement.dataset.totalDown);

    new Chart(stateChartElement, {
        type: 'pie',
        data: {
            labels: ['Up', 'Down'],
            datasets: [{
                label: "Nombre d'hôtes",
                data: [totalUp, totalDown],
                backgroundColor: ['#36A2EB', '#FF6384'],
            }]
        }
    });

    // Graphique des plages IP
    const ipChartElement = document.getElementById('ipChart');
    const ipLabels = JSON.parse(ipChartElement.dataset.ipLabels);
    const ipData = JSON.parse(ipChartElement.dataset.ipData);

    new Chart(ipChartElement, {
        type: 'bar',
        data: {
            labels: ipLabels,
            datasets: [{
                label: "Nombre d'hôtes par plage IP",
                data: ipData,
                backgroundColor: '#FFCE56',
            }]
        }
    });
});