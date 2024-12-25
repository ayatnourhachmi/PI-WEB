let currentStatus = 'Married'; // Default status
let currentRegionId = null; // Store the currently selected region

// Function to handle status toggle
function setFamilyStatus(status) {
    currentStatus = status;

    // Update the UI to reflect the active status
    document.getElementById('married-option').classList.toggle('active', status === 'Married');
    document.getElementById('single-option').classList.toggle('active', status === 'Single');

    // If a region is already selected, re-fetch the results for the selected region
    if (currentRegionId) {
        fetchRegionResults(currentRegionId);
    }
}

// Function to display results
function displayResults(data) {
    const resultsContainer = document.getElementById('results');

    if (!data.averages || Object.keys(data.averages).length === 0) {
        resultsContainer.textContent = 'No data available for this selection.';
        return;
    }

    const { message, averages } = data;

    // Create the message element
    const messageElement = document.createElement('p');
    messageElement.textContent = message;

    // Create a list of averages
    const averagesList = document.createElement('ul');
    for (const [key, value] of Object.entries(averages)) {
        const listItem = document.createElement('li');
        listItem.textContent = `${key}: ${value.toFixed(2)} DH`;
        averagesList.appendChild(listItem);
    }

    // Clear the container and append new content
    resultsContainer.innerHTML = ''; // Clear previous content
    resultsContainer.appendChild(messageElement);
    resultsContainer.appendChild(averagesList);
}

// Function to fetch results for a region
async function fetchRegionResults(regionId) {
    const resultsContainer = document.getElementById('results');
    resultsContainer.textContent = 'Loading...';

    try {
        // Fetch data from the backend
        const response = await fetch('/display_results', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ region: regionId, family_status: currentStatus }),
        });

        if (!response.ok) {
            console.error(`[ERROR] Server responded with status ${response.status}`);
            resultsContainer.textContent = 'Error fetching results. Please try again.';
            return;
        }

        const data = await response.json();
        displayResults(data); // Call the display function
    } catch (error) {
        console.error('[ERROR] Fetch failed:', error);
        resultsContainer.textContent = 'An error occurred. Please try again.';
    }
}

// Function to handle region clicks
function handleRegionClick(event) {
    const regionId = event.target.id; // Get the ID of the clicked region
    currentRegionId = regionId; // Store the currently selected region

    // Set the fill color of all paths back to default
    document.querySelectorAll('path').forEach((path) => {
        path.style.fill = '#a7f3d0'; // Default color
    });

    const lbyedElements = document.querySelectorAll('.Lbyed');
    lbyedElements.forEach((el) => {
        el.style.fill = '#FFF'; // Reset Lbyed elements to white
    });

    // Highlight the clicked region
    event.target.style.fill = '#047857'; // Highlighted color for clicked region

    // Fetch results for the clicked region
    fetchRegionResults(regionId);
}

// Function to predict region based on salary and family status
async function predictRegion(salary, familyStatus) {
    try {
        // Construct the API URL
        const apiUrl = `/display_results_byMiniForm?salary=${encodeURIComponent(salary)}&family_status=${encodeURIComponent(familyStatus)}`;

        // Fetch the data
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'An error occurred while predicting the region.');
        }

        return data; // Return the prediction
    } catch (error) {
        console.error('[ERROR] Prediction failed:', error.message);
        throw error;
    }
}

// Function to handle "Predict" button click
async function handlePredictButtonClick() {
    const salaryInput = document.getElementById('salaryInput');
    const salary = parseFloat(salaryInput.value);

    if (isNaN(salary)) {
        alert('Please enter a valid salary.');
        return;
    }

    try {
        const prediction = await predictRegion(salary, currentStatus);

        // Update the UI with the prediction
        const predictionContainer = document.getElementById('predictionResult');
        predictionContainer.textContent = `Predicted Region: ${prediction.predicted_region}`;
    } catch (error) {
        const predictionContainer = document.getElementById('predictionResult');
        predictionContainer.textContent = `Error: ${error.message}`;
    }
}

// Attach event listeners to SVG paths
document.querySelectorAll('svg path').forEach((path) => {
    path.addEventListener('click', handleRegionClick);
});

// Attach event listener to Predict button
document.getElementById('predictButton').addEventListener('click', handlePredictButtonClick);
