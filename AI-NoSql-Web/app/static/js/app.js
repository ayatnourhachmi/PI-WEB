document.addEventListener("DOMContentLoaded", function () {
    // File upload handling
    document.addEventListener("DOMContentLoaded", function () {
        const uploadButton = document.getElementById("uploadButton");
        const progressContainer = document.getElementById("progressContainer");
        const progressBar = document.getElementById("progressBar");
        const progressText = document.getElementById("progressText");
      
        uploadButton.addEventListener("click", async function () {
          const fileInput = document.getElementById("fileUpload");
          const file = fileInput.files[0];
      
          if (!file) {
            alert("Please select a file to upload.");
            return;
          }
      
          const formData = new FormData();
          formData.append("file", file);
      
          try {
            // Show progress bar
            progressContainer.classList.remove("hidden");
            progressBar.style.width = "0%";
            progressText.textContent = "0%";
      
            // Start uploading the file
            const response = await fetch("/upload", {
              method: "POST",
              body: formData,
            });
      
            if (response.ok) {
              const data = await response.json();
              alert(data.message);
            } else {
              const errorData = await response.json();
              alert(errorData.error || "Failed to process the file.");
            }
          } catch (error) {
            console.error("Error uploading file:", error);
            alert("An error occurred while uploading the file.");
          }
        });
      
        // EventSource for progress updates
        const eventSource = new EventSource("/progress");
        eventSource.onmessage = function (event) {
          const data = JSON.parse(event.data);
          const progress = data.progress;
      
          // Update progress bar
          progressBar.style.width = `${progress}%`;
          progressText.textContent = `${progress}%`;
      
          // Hide progress bar when complete
          if (progress === 100) {
            setTimeout(() => {
              progressContainer.classList.add("hidden");
            }, 2000);
          }
        };
      });
      
  
    // Dynamically generate key point input fields
    const keyPointsInput = document.getElementById("keyPoints");
    const keyPointInputsDiv = document.getElementById("keyPointInputs");
  
    keyPointsInput.addEventListener("input", function () {
      const numKeyPoints = parseInt(this.value) || 0;
  
      // Preserve existing inputs
      const existingValues = {};
      for (let i = 1; i <= keyPointInputsDiv.children.length; i++) {
        const input = document.getElementById(`keyPoint_${i}`);
        if (input) existingValues[i] = input.value;
      }
  
      keyPointInputsDiv.innerHTML = ""; // Clear previous inputs
  
      for (let i = 1; i <= numKeyPoints; i++) {
        const keyPointDiv = document.createElement("div");
        keyPointDiv.classList.add("mb-4");
  
        const label = document.createElement("label");
        label.classList.add("block", "text-sm", "font-medium", "text-gray-700");
        label.setAttribute("for", `keyPoint_${i}`);
        label.textContent = `Prompt for Key Point ${i}`;
  
        const input = document.createElement("input");
        input.type = "text";
        input.id = `keyPoint_${i}`;
        input.classList.add("border", "border-gray-300", "p-2", "w-full", "rounded-md");
        input.placeholder = `Enter prompt for key point ${i}`;
  
        if (existingValues[i]) input.value = existingValues[i]; // Restore existing values
  
        keyPointDiv.appendChild(label);
        keyPointDiv.appendChild(input);
        keyPointInputsDiv.appendChild(keyPointDiv);
      }
    });
  
    // Handle "Generate Responses" button click
    const generateResponsesButton = document.getElementById("generateResponses");
    const loadingDiv = document.getElementById("loading");
    const responseSection = document.getElementById("responseSection");
    const responsesDiv = document.getElementById("responses");
  
    generateResponsesButton.addEventListener("click", async function () {
      const keyPoints = [];
      const numKeyPoints = parseInt(keyPointsInput.value) || 0;
  
      for (let i = 1; i <= numKeyPoints; i++) {
        const input = document.getElementById(`keyPoint_${i}`);
        if (input) keyPoints.push(input.value.trim());
      }
  
      if (keyPoints.length === 0) {
        alert("Please specify at least one prompt.");
        return;
      }
  
      // Show loading indicator
      loadingDiv.classList.remove("hidden");
  
      try {
        const response = await fetch("/generate", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ key_points: keyPoints, num_key_points: keyPoints.length }),
        });
  
        const data = await response.json();
  
        if (response.ok) {
          responsesDiv.innerHTML = ""; // Clear previous responses
          data.answers.forEach((answer, index) => {
            const responseDiv = document.createElement("div");
            responseDiv.classList.add("mb-4", "border", "p-4", "rounded-md", "bg-gray-100");
  
            responseDiv.innerHTML = `
              <strong class="text-blue-600">Prompt ${index + 1}: ${answer.key_point}</strong>
              <p class="mt-2">${answer.answer}</p>
            `;
            responsesDiv.appendChild(responseDiv);
          });
  
          responseSection.classList.remove("hidden"); // Show the response section
        } else {
          alert(data.error || "Failed to fetch answers.");
        }
      } catch (error) {
        console.error("Error fetching answers:", error);
        alert("An error occurred while fetching answers.");
      } finally {
        // Hide loading indicator
        loadingDiv.classList.add("hidden");
      }
    });
  });
  