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

const ICONS = [
    '/static/images/1.svg',
    '/static/images/2.svg',
    '/static/images/3.svg',
    '/static/images/4.svg',
    '/static/images/5.svg',
];

// Function to handle region clicks
async function handleRegionClick(event) {
    const regionId = event.target.id; // Get the ID of the clicked region
    currentRegionId = regionId; // Store the currently selected region

    console.log('[INFO] Region clicked. Region ID:', regionId);

    // Reset the fill color of all paths
    document.querySelectorAll('path').forEach((path) => {
        path.style.fill = '#a7f3d0'; // Default color
    });

    const lbyedElements = document.querySelectorAll('.Lbyed');
    lbyedElements.forEach((el) => {
        el.style.fill = '#FFF'; // Reset Lbyed elements to white
    });

    // Highlight the clicked region
    event.target.style.fill = '#047857'; // Highlighted color for clicked region

    // Fetch and display results for the clicked region
    console.log('[INFO] Fetching results...');
    await fetchRegionResults(regionId);
}

// Function to render results dynamically
function renderResults(data) {
    console.log('[INFO] Rendering results:', data);

    if (!data || !data.averages || Object.keys(data.averages).length === 0) {
        return `
            <p class="text-red-600 font-medium">No data available for this selection.</p>
        `;
    }

    const { message, averages } = data;

    // Ensure "Average Total Monthly Expenses (DH)" is last
    const sortedAverages = Object.entries(averages).sort(([keyA], [keyB]) => {
        if (keyA === "Average Total Monthly Expenses (DH)") return 1; // Place at the end
        if (keyB === "Average Total Monthly Expenses (DH)") return -1; 
        return 0; // Maintain order for other items
    });

    // Build the result items with icons
    const resultItems = sortedAverages.map(([key, value], index) => {
        const iconPath = ICONS[index % ICONS.length]; // Use icons in order or cycle if more items

        // Apply special styling for "Average Total Monthly Expenses (DH)"
        if (key === "Average Total Monthly Expenses (DH)") {
            return `
                <li class="flex items-center text-gray-700 font-medium">
                    <img src="${iconPath}" alt="${key} Icon" class="w-6 h-6 mr-2"> <!-- Larger Icon -->
                    <span class="text-lg text-emerald-700">${key}</span> <!-- Larger and bolder text -->
                    <span class="ml-auto text-lg font-bold text-emerald-700">${value.toFixed(2)} DH</span> <!-- Larger and bolder value -->
                </li>
            `;
        }

        // Default styling for other items
        return `
            <li class="flex items-center text-gray-700 font-medium">
                <img src="${iconPath}" alt="${key} Icon" class="w-6 h-6 mr-2">
                <span>${key}</span>
                <span class="ml-auto font-semibold text-gray-800">${value.toFixed(2)} DH</span>
            </li>
        `;
    }).join('');

    return `
        <p class="text-gray-600 font-semibold mb-4 text-lg">${message}</p>
        <ul class="space-y-3">
            ${resultItems}
        </ul>
    `;
}


// Function to fetch results for a region
async function fetchRegionResults(regionId) {
    console.log('[INFO] Fetching results for region ID:', regionId);

    const resultContainer = document.getElementById('result-container');
    resultContainer.innerHTML = '<p class="text-gray-600">Loading...</p>';

    try {
        const response = await fetch('/display_results', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ region: regionId, family_status: currentStatus }),
        });

        if (!response.ok) {
            console.error(`[ERROR] Server responded with status ${response.status}`);
            resultContainer.innerHTML = '<p class="text-red-600">Error fetching results. Please try again.</p>';
            return;
        }

        const data = await response.json();
        console.log('[INFO] Data received:', data);

        // Render the results dynamically
        resultContainer.innerHTML = renderResults(data);
    } catch (error) {
        console.error('[ERROR] Fetch failed:', error);
        resultContainer.innerHTML = '<p class="text-red-600">An error occurred. Please try again.</p>';
    }
}

// Attach event listeners to SVG paths
document.addEventListener('DOMContentLoaded', () => {
    console.log('[INFO] DOM fully loaded. Attaching event listeners.');
    document.querySelectorAll('svg path').forEach((path) => {
        path.addEventListener('click', handleRegionClick);
    });

    // Initialize the results container with a prompt
    const resultContainer = document.getElementById('result-container');
    if (resultContainer) {
        resultContainer.innerHTML = `
            <p class="text-gray-600 font-medium">Click on a region to display results.</p>
        `;
    }
});



// Function to handle "Predict" button click
async function handlePredictButtonClick() {
    const salaryInput = document.getElementById('salaryInput');
    const salary = parseFloat(salaryInput.value);
    const familyStatusSelect = document.getElementById('familyStatusSelect');
    const familyStatus = familyStatusSelect.value;

    // Validate inputs
    if (isNaN(salary)) {
        alert('Please enter a valid salary.');
        return;
    }

    if (!['Single', 'Married'].includes(familyStatus)) {
        alert('Please select a valid family status.');
        return;
    }

    try {
        // Call the backend API
        const response = await fetch(`/display_results_byMiniForm?salary=${salary}&family_status=${familyStatus}`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error);
        }

        // Parse the response JSON
        const prediction = await response.json();

        // Define region images
        const REGION_IMAGES = {
            "Tanger-Tétouan-Al Hoceima": "static/images/tanger.jpg",
            "L’Oriental": "static/images/oujda.jpg",
            "Fès-Meknès": "static/images/taza.jpg",
            "Rabat-Salé-Kénitra": "static/images/rabat.jpg",
            "Béni Mellal-Khénifra": "static/images/benimelal.jpg",
            "Casablanca-Settat": "static/images/casa.jpg",
            "Marrakech-Safi": "static/images/kech.jpg",
            "Drâa-Tafilalet": "static/images/zagoura.jpg",
            "Souss-Massa": "static/images/agadir.jpg",
            "Guelmim-Oued Noun": "static/images/guelmim.jpg",
            "Laâyoune-Sakia Al Hamra": "static/images/laayoune.jpg",
            "Dakhla-Oued Eddahab": "static/images/dakhla.jpg",
        };

        // Get the image for the predicted region
        const regionImage = REGION_IMAGES[prediction.predicted_region];

        // Update the UI with the predicted region as an image
        const predictionContainer = document.getElementById('predictionResult');
        predictionContainer.innerHTML = `
            <div class="relative">
                <img src="${regionImage}" alt="${prediction.predicted_region}" class="w-full h-64 object-cover rounded-md">
                <div class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 rounded-md">
                    <span class="text-white text-2xl font-bold">${prediction.predicted_region}</span>
                </div>
            </div>
        `;

        // Scroll to the results section
        const resultContainer = document.getElementById('predictionResult');
        resultContainer.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        // Handle errors
        const predictionContainer = document.getElementById('predictionResult');
        predictionContainer.innerHTML = `
            <h2 class="text-lg font-bold text-center text-red-600">Error:</h2>
            <p class="text-center">${error.message}</p>
        `;

        // Scroll to the results section (optional for error visibility)
        const resultContainer = document.getElementById('result-container');
        resultContainer.scrollIntoView({ behavior: 'smooth' });
    }
}

// Attach event listener to Predict button
document.getElementById('predictButton').addEventListener('click', handlePredictButtonClick);



function toggleMenu() {
    const menu = document.getElementById('menu-links');
    const overlay = document.getElementById('menu-overlay');
    if (menu.classList.contains('-translate-x-full')) {
      menu.classList.remove('-translate-x-full');
      menu.classList.add('translate-x-0');
      overlay.classList.remove('hidden');
      overlay.classList.add('block');
    } else {
      menu.classList.add('-translate-x-full');
      menu.classList.remove('translate-x-0');
      overlay.classList.remove('block');
      overlay.classList.add('hidden');
    }
  }

  function closeMenu() {
    const menu = document.getElementById('menu-links');
    const overlay = document.getElementById('menu-overlay');
    menu.classList.add('-translate-x-full');
    menu.classList.remove('translate-x-0');
    overlay.classList.remove('block');
    overlay.classList.add('hidden');
  }