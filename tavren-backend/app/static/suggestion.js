const loadingMessage = document.getElementById('loadingMessage');
const errorMessage = document.getElementById('errorMessage');
const statsContent = document.getElementById('statsContent');
const suggestionsOfferedEl = document.getElementById('suggestionsOffered');
const suggestionsAcceptedEl = document.getElementById('suggestionsAccepted');
const acceptanceRateEl = document.getElementById('acceptanceRate');
const chartCanvas = document.getElementById('suggestionSuccessChart').getContext('2d');

let successChart = null; // Variable to hold the chart instance

// Function to fetch data and update UI
async function loadSuggestionStats() {
    errorMessage.style.display = 'none';
    loadingMessage.style.display = 'block';
    statsContent.style.display = 'none';

    try {
        const response = await fetch('/api/dashboard/suggestion-success');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status} ${response.statusText || ''}`);
        }
        const stats = await response.json();

        updateStatsSummary(stats);
        renderSuccessChart(stats);

        statsContent.style.display = 'block'; // Show stats after loading

    } catch (error) {        console.error('Error fetching suggestion stats:', error);
        errorMessage.textContent = `Failed to load stats: ${error.message}. Please try again later.`;
        errorMessage.style.display = 'block';
    } finally {
        loadingMessage.style.display = 'none';
    }
}

// Function to update the text summary
function updateStatsSummary(stats) {
    suggestionsOfferedEl.textContent = stats.suggestions_offered;
    suggestionsAcceptedEl.textContent = stats.suggestions_accepted;
    acceptanceRateEl.textContent = `${stats.acceptance_rate}%`;
}

// Function to render the donut chart
function renderSuccessChart(stats) {
    const suggestions_not_accepted_or_not_offered = stats.suggestions_offered - stats.suggestions_accepted;

    const data = {
        labels: [
            'Suggestions Accepted',
            'Suggestions Declined/Not Offered' // Label reflects those offered but not accepted via suggestion flow
        ],
        datasets: [{
            label: 'Suggestion Outcomes',
            data: [stats.suggestions_accepted, suggestions_not_accepted_or_not_offered],
            backgroundColor: [
                'rgba(75, 192, 192, 0.7)', // Green for accepted
                'rgba(255, 99, 132, 0.7)' // Red for declined/not accepted
            ],
            borderColor: [
                'rgba(75, 192, 192, 1)',
                'rgba(255, 99, 132, 1)'
            ],
            borderWidth: 1
        }]
    };

    // Destroy previous chart instance if it exists
    if (successChart) {
        successChart.destroy();
    }

    // Create new chart instance
    successChart = new Chart(chartCanvas, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Suggestion Acceptance Outcomes'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.label || '';
                            let value = context.raw || 0;
                            let total = context.chart.getDatasetMeta(0).total;
                            let percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            if (label) {
                                label += ': ';
                            }
                            label += `${value} (${percentage}%)`;
                            return label;
                        }
                    }
                }
            }
        },
    });
}

// Initial load
document.addEventListener('DOMContentLoaded', loadSuggestionStats); 