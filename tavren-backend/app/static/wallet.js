const userIdInput = document.getElementById('userIdInput');
const fetchWalletBtn = document.getElementById('fetchWalletBtn');
const walletInfoContainer = document.getElementById('walletInfoContainer');
const loadingMessage = document.getElementById('loadingMessage');
const errorMessage = document.getElementById('errorMessage');

// Balance elements
const totalEarnedEl = document.getElementById('totalEarned');
const totalClaimedEl = document.getElementById('totalClaimed');
const availableBalanceEl = document.getElementById('availableBalance');

// History elements
const historyListEl = document.getElementById('historyList');

// Claim status elements
const claimStatusAreaEl = document.getElementById('claimStatusArea');

// --- Constants (mirror backend or fetch from config) ---
const MINIMUM_PAYOUT_THRESHOLD_FRONTEND = 5.00;
// -----------------------------------------------------

// Function to fetch wallet data (balance and history)
async function loadWalletData() {
    const userId = userIdInput.value.trim();
    if (!userId) {
        errorMessage.textContent = 'Please enter a User ID.';
        errorMessage.style.display = 'block';
        walletInfoContainer.style.display = 'none';
        return;
    }

    // Reset UI
    errorMessage.style.display = 'none';
    loadingMessage.style.display = 'block';
    walletInfoContainer.style.display = 'none'; // Hide until data is loaded
    historyListEl.innerHTML = '<li>Loading history...</li>'; // Reset history list
    claimStatusAreaEl.innerHTML = ''; // Clear claim status area

    try {
        // Fetch balance and history in parallel
        const [balanceResponse, historyResponse] = await Promise.all([
            fetch(`/api/wallet/${userId}`),
            fetch(`/api/rewards/history/${userId}`)
        ]);

        // Check balance response
        if (!balanceResponse.ok) {
            let errorMsg = `Balance fetch failed: ${balanceResponse.status} ${balanceResponse.statusText || ''}`;
            try { errorMsg += ` - ${JSON.stringify(await balanceResponse.json())}`; } catch(e) {} // Append details if possible
            throw new Error(errorMsg);
        }
        const balanceData = await balanceResponse.json();

        // Check history response
        if (!historyResponse.ok) {
            let errorMsg = `History fetch failed: ${historyResponse.status} ${historyResponse.statusText || ''}`;
            try { errorMsg += ` - ${JSON.stringify(await historyResponse.json())}`; } catch(e) {} // Append details if possible
            throw new Error(errorMsg);
        }
        const historyData = await historyResponse.json();

        // Update UI with fetched data
        updateBalanceUI(balanceData);
        updateHistoryUI(historyData);
        updateClaimStatusUI(balanceData);

        walletInfoContainer.style.display = 'flex'; // Show the container

    } catch (error) {
        console.error('Error loading wallet data:', error);
        errorMessage.textContent = `Failed to load wallet: ${error.message}. Please check the User ID.`;
        errorMessage.style.display = 'block';
        walletInfoContainer.style.display = 'none';
    } finally {
        loadingMessage.style.display = 'none';
    }
}

// Function to update balance summary UI
function updateBalanceUI(balance) {
    // Format numbers as currency
    const formatCurrency = (amount) => `$${amount.toFixed(2)}`;

    totalEarnedEl.textContent = formatCurrency(balance.total_earned);
    totalClaimedEl.textContent = formatCurrency(balance.total_claimed);
    availableBalanceEl.textContent = formatCurrency(balance.available_balance);
}

// Function to update reward history UI
function updateHistoryUI(history) {
    historyListEl.innerHTML = ''; // Clear loading/previous items

    if (history.length === 0) {
        historyListEl.innerHTML = '<li>No reward history found.</li>';
        return;
    }

    history.forEach(reward => {
        const listItem = document.createElement('li');

        const offerSpan = document.createElement('span');
        offerSpan.className = 'offer-id';
        offerSpan.textContent = `Offer: ${reward.offer_id}`; // Display offer ID

        const amountSpan = document.createElement('span');
        amountSpan.className = 'amount';
        amountSpan.textContent = `+$${reward.amount.toFixed(2)}`;

        listItem.appendChild(offerSpan);
        listItem.appendChild(amountSpan);

        historyListEl.appendChild(listItem);
    });
}

// --- New Function to Update Claim Status UI ---
function updateClaimStatusUI(balance) {
    claimStatusAreaEl.innerHTML = ''; // Clear previous status
    const userId = userIdInput.value.trim(); // Get user ID for the request

    if (balance.is_claimable) {
        const claimButton = document.createElement('button');
        claimButton.textContent = `Claim $${balance.available_balance.toFixed(2)} Now`;
        claimButton.className = 'claim-button';
        claimButton.onclick = async () => {
            claimButton.disabled = true;
            claimButton.textContent = 'Processing...';
            errorMessage.style.display = 'none'; // Hide previous general errors
            claimStatusAreaEl.querySelector('.claim-error')?.remove(); // Remove previous claim errors

            try {
                const response = await fetch('/api/wallet/claim', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        user_id: userId, 
                        amount: balance.available_balance 
                    }),
                });

                if (!response.ok) {
                    let errorDetails = `HTTP error! Status: ${response.status}`;
                    try {
                        const errorData = await response.json();
                        errorDetails += ` - ${errorData.detail || JSON.stringify(errorData)}`;
                    } catch (e) { /* Ignore if response body isn't JSON */ }
                    throw new Error(errorDetails);
                }

                // Success!
                const result = await response.json(); // Get the created PayoutRequest
                console.log('Claim request successful:', result);
                claimStatusAreaEl.innerHTML = `<p style="color: green;">Claim request for $${balance.available_balance.toFixed(2)} submitted! Status: ${result.status}</p>`;
                // Optionally, refresh wallet balance after successful claim submission
                // loadWalletData(); // Uncomment to refresh immediately

            } catch (error) {
                console.error('Claim request failed:', error);
                const errorP = document.createElement('p');
                errorP.textContent = `Error submitting claim: ${error.message}`;
                errorP.style.color = 'red';
                errorP.className = 'claim-error'; // Class for specific styling/removal
                // Insert error before the button if it still exists
                if (claimStatusAreaEl.contains(claimButton)) {
                     claimStatusAreaEl.insertBefore(errorP, claimButton);
                     claimButton.disabled = false; // Re-enable button on error
                     claimButton.textContent = `Claim $${balance.available_balance.toFixed(2)} Now`; // Restore text
                } else {
                    // If button was already replaced (shouldn't normally happen on error)
                    claimStatusAreaEl.appendChild(errorP);
                }
            }
        };
        claimStatusAreaEl.appendChild(claimButton);
    } else {
        const needed = MINIMUM_PAYOUT_THRESHOLD_FRONTEND - balance.available_balance;
        const message = document.createElement('p');
        message.textContent = `Earn $${needed.toFixed(2)} more to claim.`;
        claimStatusAreaEl.appendChild(message);
    }
}
// -------------------------------------------

// Event Listeners
fetchWalletBtn.addEventListener('click', loadWalletData);
userIdInput.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        loadWalletData();
    }
}); 