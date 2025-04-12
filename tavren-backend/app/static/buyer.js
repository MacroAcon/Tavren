async function fetchBuyerInsights() {
    try {
        const response = await fetch('/api/dashboard/buyer-insights');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching buyer insights:', error);
        return []; // Return empty array on error
    }
}

// Define the color map (consistent with the other dashboard)
const colorMap = {
    'privacy': 'rgba(54, 162, 235, 0.7)', // blue
    'trust': 'rgba(75, 192, 192, 0.7)', // green
    'payout': 'rgba(255, 159, 64, 0.7)', // orange
    'misunderstanding': 'rgba(153, 102, 255, 0.7)', // purple
    'other': 'rgba(201, 203, 207, 0.7)', // gray
    'unspecified': 'rgba(201, 203, 207, 0.7)' // gray
};
const defaultColor = 'rgba(201, 203, 207, 0.7)'; // Default gray

// Helper to get darker border color
const getBorderColor = (rgbaColor) => rgbaColor.replace('0.7', '1');

// Helper to get trust score indicator emoji
const getScoreIndicator = (score) => {
    if (score >= 70) return '🟢'; // Green
    if (score >= 40) return '🟡'; // Yellow
    return '🔴'; // Red
};

// Helper to display trust scores in the dedicated div
function displayTrustScores(buyerData) {
    const scoresListDiv = document.getElementById('trustScoresList');
    if (!scoresListDiv) {
        console.error("Element with ID 'trustScoresList' not found.");
        return;
    }

    if (buyerData.length === 0) {
        scoresListDiv.innerHTML = '<p>No buyer data available to display scores.</p>';
        return;
    }

    let scoresHtml = '<h2>Trust Scores</h2><ul>';
    // Sort buyers by ID for consistent display
    buyerData.sort((a, b) => parseInt(a.buyer_id) - parseInt(b.buyer_id));

    buyerData.forEach(item => {
        const score = item.trust_score;
        const indicator = getScoreIndicator(score);
        const risky_flag_html = item.is_risky ? '<span class="risky-flag">(RISK FLAGGED)</span>' : '';
        scoresHtml += `<li>Buyer ${item.buyer_id}: ${score.toFixed(0)} ${indicator} ${risky_flag_html}</li>`;
    });
    scoresHtml += '</ul>';

    scoresListDiv.innerHTML = scoresHtml;
}

async function renderBuyerChart() {
    const buyerData = await fetchBuyerInsights();

    // Display trust scores separately
    displayTrustScores(buyerData);

    const ctx = document.getElementById('buyerReasonChart').getContext('2d');

    if (buyerData.length === 0) {
        console.warn("No buyer data received for the chart.");
        ctx.font = "16px Arial";
        ctx.textAlign = "center";
        ctx.fillText("No buyer data available to display.", ctx.canvas.width / 2, 50);
        return;
    }

    // Update chart labels to include trust score and risk flag
    const buyerIdsWithScores = buyerData.map(item => {
        const riskText = item.is_risky ? ' (RISKY!)' : '';
        return `Buyer ${item.buyer_id} (Score: ${item.trust_score.toFixed(0)})${riskText}`;
    });

    // Get all unique reason categories across all buyers
    const allReasons = [...new Set(buyerData.flatMap(item => Object.keys(item.reasons)))];
    allReasons.sort(); // Sort for consistent order

    const datasets = allReasons.map(reason => ({
        label: reason, // Reason name for legend/tooltip
        data: buyerData.map(item => item.reasons[reason] || 0), // Get count for this reason per buyer, default 0
        backgroundColor: colorMap[reason.toLowerCase()] || defaultColor,
        borderColor: getBorderColor(colorMap[reason.toLowerCase()] || defaultColor),
        borderWidth: 1
        // Use stack property if you prefer stacked bars:
        // stack: 'buyerStack' // All datasets with the same stack ID will stack
    }));

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: buyerIdsWithScores,
            datasets: datasets
        },
        options: {
            plugins: {
                title: {
                    display: true,
                    text: 'Rejections per Buyer by Reason'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y;
                            }
                            return label;
                        }
                    }
                }
            },
            responsive: true,
            // Set interaction mode to 'index' for grouped tooltips
            interaction: {
                mode: 'index', // Show tooltips for all datasets at the same x-axis index
                intersect: false, // Don't require hover directly over the bar
            },
            scales: {
                x: {
                    // Set stacked to true if using stacked bars
                    // stacked: true,
                },
                y: {
                    // Set stacked to true if using stacked bars
                    // stacked: true,
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Rejections'
                    },
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', renderBuyerChart); 