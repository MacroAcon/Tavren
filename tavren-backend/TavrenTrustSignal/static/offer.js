const buyerIdInput = document.getElementById('buyerIdInput');
const fetchOffersBtn = document.getElementById('fetchOffersBtn');
const offerListDiv = document.getElementById('offerList');
const loadingMessage = document.getElementById('loadingMessage');
const errorMessage = document.getElementById('errorMessage');

// Function to fetch and display offers
async function loadOffers() {
    const buyerId = buyerIdInput.value.trim();
    if (!buyerId) {
        errorMessage.textContent = 'Please enter a Buyer ID.';
        errorMessage.style.display = 'block';
        offerListDiv.innerHTML = ''; // Clear previous offers
        return;
    }

    // Reset states
    offerListDiv.innerHTML = '';
    errorMessage.style.display = 'none';
    loadingMessage.style.display = 'block';

    try {
        const response = await fetch(`/api/offers/feed/${buyerId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status} ${response.statusText || ''}`);
        }
        const offers = await response.json();

        if (offers.length === 0) {
            offerListDiv.innerHTML = '<p>No offers available for this buyer.</p>';
        } else {
            renderOffers(offers);
        }

    } catch (error) {
        console.error('Error fetching offers:', error);
        errorMessage.textContent = `Failed to load offers: ${error.message}. Please check the Buyer ID and try again.`;
        errorMessage.style.display = 'block';
    } finally {
        loadingMessage.style.display = 'none';
    }
}

// Function to render offers into the list container
function renderOffers(offers) {
    offerListDiv.innerHTML = ''; // Clear previous offers
    offers.forEach(offer => {
        const card = document.createElement('div');
        card.className = 'offer-card';

        const title = document.createElement('h3');
        title.textContent = offer.title;

        const description = document.createElement('p');
        description.textContent = offer.description;

        const sensitivityTag = document.createElement('span');
        sensitivityTag.textContent = offer.sensitivity_level.toUpperCase();
        sensitivityTag.className = `sensitivity-tag sensitivity-${offer.sensitivity_level.toLowerCase()}`;

        // Action buttons container
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'offer-actions';

        // Function to create the standard action buttons
        const createStandardButtons = () => {
            actionsDiv.innerHTML = ''; // Clear current content

            const acceptBtn = document.createElement('button');
            acceptBtn.textContent = 'Accept Offer';
            acceptBtn.className = 'offer-button accept-button';
            acceptBtn.onclick = () => logOfferAction('accepted', offer, card);

            const skipBtn = document.createElement('button');
            skipBtn.textContent = 'Skip Offer';
            skipBtn.className = 'offer-button skip-button';
            // Changed: skip button now calls promptForSkipReason
            skipBtn.onclick = () => promptForSkipReason(offer, card, actionsDiv, createStandardButtons);

            actionsDiv.appendChild(acceptBtn);
            actionsDiv.appendChild(skipBtn);
        };

        createStandardButtons(); // Initialize with standard buttons
        // -----------------------------------------

        card.appendChild(title);
        card.appendChild(description);
        card.appendChild(sensitivityTag);
        card.appendChild(actionsDiv); // Add actions container to card

        offerListDiv.appendChild(card);
    });
}

// Function to prompt user for skip reason
function promptForSkipReason(offer, cardElement, actionsContainer, restoreButtonsCallback) {
    actionsContainer.innerHTML = ''; // Clear existing buttons

    const reasonSelectorDiv = document.createElement('div');
    reasonSelectorDiv.className = 'reason-selector';

    const label = document.createElement('label');
    label.textContent = 'Why are you skipping this offer?';
    label.htmlFor = `reason-select-${offer.title.replace(/\s+/g, '-')}`; // Unique ID

    const select = document.createElement('select');
    select.id = label.htmlFor;
    const reasons = {
        'privacy': 'Too invasive',
        'payout': 'Not enough payout',
        'trust': 'Don\'t trust buyer',
        'misunderstanding': 'Confusing or unclear',
        'unspecified': 'Other'
    };

    for (const [value, text] of Object.entries(reasons)) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = text;
        select.appendChild(option);
    }

    const buttonsDiv = document.createElement('div');
    buttonsDiv.className = 'reason-selector-buttons';

    const confirmBtn = document.createElement('button');
    confirmBtn.textContent = 'Confirm Skip';
    confirmBtn.className = 'offer-button confirm-button';
    confirmBtn.onclick = () => {
        const selectedReasonValue = select.value;
        const selectedReasonText = select.options[select.selectedIndex].text;
        // Pass the selected reason details to logOfferAction
        logOfferAction('declined', offer, cardElement, {
            category: selectedReasonValue,
            user_text: selectedReasonText // Or a fixed string
        });
    };

    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancel';
    cancelBtn.className = 'offer-button cancel-button';
    cancelBtn.onclick = restoreButtonsCallback; // Restore original buttons

    buttonsDiv.appendChild(confirmBtn);
    buttonsDiv.appendChild(cancelBtn);

    reasonSelectorDiv.appendChild(label);
    reasonSelectorDiv.appendChild(select);
    reasonSelectorDiv.appendChild(buttonsDiv);

    actionsContainer.appendChild(reasonSelectorDiv);
}

// Function to log offer action (Accept/Skip)
async function logOfferAction(action, offer, cardElement, reasonDetails = null) {
    const buyerId = buyerIdInput.value.trim();
    if (!buyerId) {
        alert('Error: Buyer ID not found.');
        return;
    }

    const simpleOfferSlug = offer.title.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    const generatedOfferId = `buyer-${buyerId}-offer-${simpleOfferSlug}`;

    const consentPayload = {
        user_id: buyerId,
        offer_id: generatedOfferId,
        action: action,
        ...(action === 'declined' && reasonDetails && {
            reason_category: reasonDetails.category,
            user_reason: reasonDetails.user_text
        })
    };

    cardElement.querySelectorAll('.offer-button').forEach(btn => btn.disabled = true);

    try {
        // 1. Log Consent Action
        const consentResponse = await fetch('/api/consent/decline', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(consentPayload),
        });

        if (!consentResponse.ok) {
            let errorDetailsStr = '';
            try { errorDetailsStr = JSON.stringify(await consentResponse.json()); } catch (e) { /* Ignore */ }
            throw new Error(`Consent log failed: ${consentResponse.status} ${consentResponse.statusText || ''} ${errorDetailsStr}`);
        }

        console.log(`Consent action ${action} logged successfully:`, consentPayload);

        // 2. Log Reward if Accepted
        if (action === 'accepted') {
            await logReward(buyerId, generatedOfferId); // Call new reward logging function
        }

        // 3. Update UI based on original action
        if (action === 'declined' && reasonDetails && ['privacy', 'trust', 'payout'].includes(reasonDetails.category)) {
            showAlternativeOffer(cardElement, offer, generatedOfferId, reasonDetails.category);
        } else {
            cardElement.classList.add('card-submitted');
            const actionArea = cardElement.querySelector('.offer-actions') || cardElement.querySelector('.reason-selector')?.parentElement;
            if (actionArea) {
                actionArea.innerHTML = '<p style="font-size:0.9em; color:grey;">Action logged.</p>';
            }
        }

    } catch (error) {
        console.error(`Error in logOfferAction for action ${action}:`, error);
        alert(`Failed operation for ${action}. Error: ${error.message}`);
        if (!cardElement.classList.contains('card-submitted')) {
             const buttonsToEnable = cardElement.querySelectorAll('.offer-button');
             buttonsToEnable.forEach(btn => btn.disabled = false);
        }
    }
}

// Function to show alternative offer suggestion
function showAlternativeOffer(cardElement, originalOffer, originalOfferId, reasonCategory) {
    const actionArea = cardElement.querySelector('.offer-actions') || cardElement.querySelector('.reason-selector').parentElement;
    actionArea.innerHTML = ''; // Clear previous content (logged msg or reason selector)

    let suggestionText = '';
    switch (reasonCategory) {
        case 'privacy':
            suggestionText = 'Share app usage summary instead of precise data?';
            break;
        case 'trust':
            suggestionText = 'Would you accept from a verified buyer only?';
            break;
        case 'payout':
            suggestionText = 'Would $0.50 more change your mind?';
            break;
        default:
            // Should not happen based on the check before calling, but handle anyway
            actionArea.innerHTML = '<p style="font-size:0.9em; color:grey;">Action logged.</p>';
            cardElement.classList.add('card-submitted');
            return;
    }

    const suggestionDiv = document.createElement('div');
    suggestionDiv.className = 'suggestion-area';

    const textP = document.createElement('p');
    textP.className = 'suggestion-text';
    textP.textContent = `Suggestion: ${suggestionText}`;

    const acceptSuggestionBtn = document.createElement('button');
    acceptSuggestionBtn.textContent = 'Accept Suggested Offer';
    acceptSuggestionBtn.className = 'offer-button suggestion-accept-button';
    acceptSuggestionBtn.onclick = () => logAlternativeAcceptance(cardElement, originalOfferId);

    suggestionDiv.appendChild(textP);
    suggestionDiv.appendChild(acceptSuggestionBtn);

    actionArea.appendChild(suggestionDiv);
    // Don't add 'card-submitted' yet, allow interaction with the suggestion
}

// Function to log acceptance of the alternative offer
async function logAlternativeAcceptance(cardElement, originalOfferId) {
    const buyerId = buyerIdInput.value.trim();
    if (!buyerId) {
        alert('Error: Buyer ID not found.');
        return;
    }

    const alternativeOfferId = `${originalOfferId}-alt`;

    const consentPayload = {
        user_id: buyerId,
        offer_id: alternativeOfferId,
        action: 'accepted',
        reason_category: 'agent_suggestion',
        user_reason: 'Accepted AI-generated alternative'
    };

    cardElement.querySelectorAll('.suggestion-accept-button').forEach(btn => btn.disabled = true);

    try {
        // 1. Log Consent Action
        const consentResponse = await fetch('/api/consent/decline', { // Still using decline endpoint
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(consentPayload),
        });

        if (!consentResponse.ok) {
            let errorDetailsStr = '';
            try { errorDetailsStr = JSON.stringify(await consentResponse.json()); } catch (e) {} // Ignore
            throw new Error(`Consent log failed: ${consentResponse.status} ${consentResponse.statusText || ''} ${errorDetailsStr}`);
        }
        console.log('Alternative offer consent logged:', consentPayload);

        // 2. Log Reward for Accepted Alternative
        await logReward(buyerId, alternativeOfferId);

        // 3. Update UI
        cardElement.classList.add('card-submitted');
        const suggestionArea = cardElement.querySelector('.suggestion-area');
        if (suggestionArea) {
            suggestionArea.innerHTML = '<p style="font-size:0.9em; color:green;">Alternative accepted and logged!</p>';
        }

    } catch (error) {
        console.error('Error logging alternative acceptance:', error);
        alert(`Failed to log alternative acceptance. Error: ${error.message}`);
        cardElement.querySelectorAll('.suggestion-accept-button').forEach(btn => btn.disabled = false);
    }
}

// --- New Function to Log Reward ---
async function logReward(userId, offerId, amount = 0.25) { // Default reward amount
    const rewardPayload = {
        user_id: userId,
        offer_id: offerId,
        amount: amount
    };

    try {
        const response = await fetch('/api/rewards', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(rewardPayload)
        });

        if (!response.ok) {
            let errorDetailsStr = '';
            try { errorDetailsStr = JSON.stringify(await response.json()); } catch (e) {} // Ignore
            throw new Error(`Reward log failed: ${response.status} ${response.statusText || ''} ${errorDetailsStr}`);
        }

        const rewardResult = await response.json();
        console.log('Reward logged successfully:', rewardResult);
        // Optionally show a subtle confirmation or update a balance display if visible

    } catch (error) {
        console.error('Error logging reward:', error);
        // Decide if user needs notification for reward logging failure
        // alert(`Failed to log reward for offer ${offerId}. Error: ${error.message}`);
    }
}
// ----------------------------------

// Event listeners
fetchOffersBtn.addEventListener('click', loadOffers);
// Optional: Allow fetching by pressing Enter in the input field
buyerIdInput.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        loadOffers();
    }
}); 