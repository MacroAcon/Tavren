async function fetchReasonStats() {
    try {
        const response = await fetch('/api/dashboard/reason-stats');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching reason stats:', error);
        return []; // Return empty array on error
    }
}

async function renderChart() {
    const statsData = await fetchReasonStats();

    if (statsData.length === 0) {
        console.warn("No data received for the chart.");
        // Optionally display a message to the user
        const ctx = document.getElementById('reasonChart').getContext('2d');
        ctx.font = "16px Arial";
        ctx.textAlign = "center";
        ctx.fillText("No data available to display.", ctx.canvas.width / 2, 50);
        return;
    }

    // Define the color map
    const colorMap = {
        'privacy': 'rgba(54, 162, 235, 0.6)', // blue
        'trust': 'rgba(75, 192, 192, 0.6)', // green (existing color)
        'payout': 'rgba(255, 159, 64, 0.6)', // orange
        'misunderstanding': 'rgba(153, 102, 255, 0.6)', // purple
        'other': 'rgba(201, 203, 207, 0.6)', // gray
        'unspecified': 'rgba(201, 203, 207, 0.6)' // gray
    };
    const defaultColor = 'rgba(201, 203, 207, 0.6)'; // Default gray for unknown categories

    const labels = statsData.map(item => item.reason_category);
    const counts = statsData.map(item => item.count);
    // Generate background colors based on labels and colorMap
    const backgroundColors = labels.map(label => colorMap[label.toLowerCase()] || defaultColor);
    // Generate border colors (optional, could be darker or same)
    const borderColors = backgroundColors.map(color => color.replace('0.6', '1')); // Make borders opaque

    const ctx = document.getElementById('reasonChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Rejection Count',
                data: counts,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            responsive: true,
            maintainAspectRatio: true
        }
    });
}

document.addEventListener('DOMContentLoaded', renderChart); 