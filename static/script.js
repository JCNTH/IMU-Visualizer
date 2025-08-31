document.addEventListener('DOMContentLoaded', () => {
  // --- Sensor Mapping Upload ---
  const sensorMappingInput = document.getElementById('sensorIdUpload');
  const mappingStatus = document.getElementById('mappingStatus');
  sensorMappingInput.addEventListener('change', () => {
    const file = sensorMappingInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      try {
        const mapping = parseSensorMapping(text);
        if (Object.keys(mapping).length === 0) {
          throw new Error("Mapping is empty");
        }
        window.sensorMapping = mapping;
        mappingStatus.textContent = "Sensor Mapping loaded successfully.";
        mappingStatus.style.color = "green";
        console.log("Mapping loaded:", mapping);
      } catch (err) {
        mappingStatus.textContent = "Error parsing sensor mapping file. Please upload a valid file.";
        mappingStatus.style.color = "red";
        window.sensorMapping = null;
        showModal("Sensor ID", "Error parsing sensor mapping file. Please upload a valid sensor_placement.txt file.");
        console.error("Parsing error:", err);
      }
    };
    reader.readAsText(file);
  });

  // Helper function to parse sensor mapping text
  function parseSensorMapping(text) {
    const mapping = {};
    const lines = text.split('\n');
    // Assumes first line is a header; process remaining lines.
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      const parts = line.split(/\s+/);
      if (parts.length >= 2) {
        const sensorName = parts[0].toLowerCase();
        const sensorId = parts[1];
        mapping[sensorId] = sensorName;
      }
    }
    return mapping;
  }
  
  // --- Info Icon Click Handler ---
  const infoIcons = document.querySelectorAll('.info-icon');
  infoIcons.forEach(icon => {
    icon.addEventListener('click', () => {
      const headerText = icon.parentElement.childNodes[0].textContent.trim();
      const infoText = icon.getAttribute('data-info');
      showModal(headerText, infoText);
    });
  });
  
  // -------------------------------
  // Global storage for calibration and main task data
  // -------------------------------
  // Instead of storing calibration task data by task number (old way),
  // we store them keyed by the user-provided task name.
  window.calibrationData = {};
  window.mainTaskData = {};
  
  // --- Dynamic Calibration Tasks & Body Alignment ---
  const generateBtn = document.getElementById('generateCalibrationTasksBtn');
  generateBtn.addEventListener('click', () => {
    generateCalibrationTasks();
    addCalibrationUploadListeners();
  });

  // Get selected sensors for a given calibration task based on checkboxes in the sensor selection table.
  function getSelectedSensorsForTask(taskIndex) {
    const table = document.getElementById("calibrationSensorTable");
    if (!table) return [];
    const checkboxes = table.querySelectorAll(`input[type="checkbox"][data-task="${taskIndex}"]`);
    const selectedSensors = [];
    checkboxes.forEach(cb => {
      if (cb.checked) {
        selectedSensors.push(cb.dataset.sensor);
      }
    });
    return selectedSensors;
  }
  
  // Generate calibration tasks dynamically
  function generateCalibrationTasks() {
    if (!window.sensorMapping) {
      showModal("Calibration Tasks", "Please upload the sensor placement file first.");
      return;
    }
  
    // Define required lower-limb sensor names.
    const requiredNames = ["pelvis", "thigh_l", "shank_l", "foot_l", "thigh_r", "shank_r", "foot_r"];
    const lowerLimbSensorNames = Object.values(window.sensorMapping)
      .map(name => name.toLowerCase())
      .filter(name => requiredNames.includes(name));
  
    const numTasks = parseInt(document.getElementById('numCalibrationTasks').value, 10);
    const container = document.getElementById('calibrationContainer');
    container.innerHTML = "";
  
    // Reset previous calibration data.
    window.calibrationData = {};
    // (Optional) Reset any old sensorDataDicts (if used elsewhere)
    window.sensorDataDicts = {};
  
    // --- Create a global sensor selection table ---
    const table = document.createElement('table');
    table.id = "calibrationSensorTable";
    table.style.marginBottom = "1rem";
    table.style.borderCollapse = "collapse";
    table.style.width = "100%";
  
    // Header row: "Sensor" and then one column per calibration task.
    const headerRow = document.createElement('tr');
    const sensorHeader = document.createElement('th');
    sensorHeader.textContent = "Sensor";
    sensorHeader.style.border = "1px solid #ccc";
    sensorHeader.style.padding = "4px";
    headerRow.appendChild(sensorHeader);
    for (let task = 0; task < numTasks; task++) {
      const th = document.createElement('th');
      th.textContent = `Task ${task + 1}`;
      th.style.border = "1px solid #ccc";
      th.style.padding = "4px";
      headerRow.appendChild(th);
    }
    table.appendChild(headerRow);
  
    // Create a row for each lower-limb sensor, with a checkbox for each task.
    lowerLimbSensorNames.forEach(sensor => {
      const row = document.createElement('tr');
      const sensorCell = document.createElement('td');
      sensorCell.textContent = sensor;
      sensorCell.style.border = "1px solid #ccc";
      sensorCell.style.padding = "4px";
      row.appendChild(sensorCell);
      for (let task = 0; task < numTasks; task++) {
        const cell = document.createElement('td');
        cell.style.border = "1px solid #ccc";
        cell.style.padding = "4px";
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = true;
        checkbox.dataset.sensor = sensor;
        checkbox.dataset.task = task; 
        cell.appendChild(checkbox);
        row.appendChild(cell);
      }
      table.appendChild(row);
    });
    container.appendChild(table);
  
    // --- Create each calibration task block with file input and a task name input ---
    for (let i = 0; i < numTasks; i++) {
      const taskDiv = document.createElement('div');
      taskDiv.className = "calibration-task";
      taskDiv.style.border = "1px solid #ccc";
      taskDiv.style.padding = "0.5rem";
      taskDiv.style.marginBottom = "0.5rem";
      taskDiv.style.borderRadius = "4px";
  
      // Task header
      const taskHeader = document.createElement('h4');
      taskHeader.textContent = `Calibration Task ${i + 1}`;
      taskHeader.style.margin = "0 0 0.5rem 0";
      taskDiv.appendChild(taskHeader);
  
      // NEW: Input for the calibration task name.
      const taskNameLabel = document.createElement('label');
      taskNameLabel.textContent = "Task Name: ";
      const taskNameInput = document.createElement('input');
      taskNameInput.type = 'text';
      taskNameInput.value = "static"; // default value; user can change it (e.g. "static", "treadmill_walking", "cmj")
      taskNameInput.dataset.taskId = i;
      taskDiv.appendChild(taskNameLabel);
      taskDiv.appendChild(taskNameInput);
  
      // File input for calibration files
      const fileLabel = document.createElement('label');
      fileLabel.textContent = " Upload Files: ";
      const fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.accept = '.csv,.txt';
      fileInput.multiple = true;
      fileInput.dataset.taskId = i;
      taskDiv.appendChild(fileLabel);
      taskDiv.appendChild(fileInput);
  
      // Placeholder for selected file names
      const selectedFilesDiv = document.createElement('div');
      selectedFilesDiv.className = 'selected-files';
      selectedFilesDiv.textContent = "No files selected.";
      selectedFilesDiv.style.marginTop = "5px";
      taskDiv.appendChild(selectedFilesDiv);
  
      container.appendChild(taskDiv);
    }
  }
  
  // -------------------------------
  // Add listeners to calibration file inputs.
  // -------------------------------
  function addCalibrationUploadListeners() {
    const calibrationInputs = document.querySelectorAll('#calibrationContainer input[type="file"]');
    calibrationInputs.forEach((input, index) => {
      input.addEventListener('change', () => {
        uploadCalibrationTask(index, input);
      });
    });
  }
  
  // Process calibration task file uploads.
  function uploadCalibrationTask(taskId, fileInput) {
    if (!window.sensorMapping) {
      showModal("Calibration Task " + (taskId + 1), "Please upload the sensor placement file first.");
      fileInput.value = "";
      return;
    }
    const files = Array.from(fileInput.files);
    if (files.length === 0) return;
    const selectedSensors = getSelectedSensorsForTask(taskId);
    const sensorIDsForTask = Object.keys(window.sensorMapping).filter(id => {
      const sensorName = window.sensorMapping[id].toLowerCase();
      return selectedSensors.includes(sensorName);
    });
    if (sensorIDsForTask.length < selectedSensors.length) {
      showModal("Calibration Task " + (taskId + 1), "The sensor placement file does not include all selected sensors.");
      fileInput.value = "";
      return;
    }
    const matchedFiles = files.filter(file => {
      const lowerName = file.name.toLowerCase();
      return sensorIDsForTask.some(id => lowerName.includes(id.toLowerCase()));
    });
    if (matchedFiles.length < sensorIDsForTask.length) {
      const foundIDs = matchedFiles.map(file => {
        const lowerName = file.name.toLowerCase();
        return sensorIDsForTask.find(id => lowerName.includes(id.toLowerCase()));
      }).filter(Boolean);
      const missingIDs = sensorIDsForTask.filter(id => !foundIDs.includes(id));
      const missingSensors = missingIDs.map(id => window.sensorMapping[id]);
      showModal("Calibration Task " + (taskId + 1), "Missing calibration files for: " + missingSensors.join(", "));
      fileInput.value = "";
      return;
    }
    const taskDiv = fileInput.parentElement;
    const selectedFilesDiv = taskDiv.querySelector('.selected-files');
    selectedFilesDiv.innerHTML = "";
    const sensorDataDict = {};
    const fileReadPromises = matchedFiles.map(file => {
      return new Promise((resolve, reject) => {
        const lowerName = file.name.toLowerCase();
        const sensorID = sensorIDsForTask.find(id => lowerName.includes(id.toLowerCase())) || file.name;
        const sensorName = window.sensorMapping[sensorID];
        const p = document.createElement('p');
        p.textContent = sensorName + " (" + file.name + ")";
        selectedFilesDiv.appendChild(p);
        const reader = new FileReader();
        reader.onload = (e) => {
          const fileContent = e.target.result;
          sensorDataDict[sensorName.toLowerCase()] = {
            id: sensorID,
            fileName: file.name,
            content: fileContent
          };
          resolve();
        };
        reader.onerror = reject;
        reader.readAsText(file);
      });
    });
    // Read task name from the text input inside this calibration block.
    const taskNameInput = taskDiv.querySelector('input[type="text"]');
    const calibrationTaskName = taskNameInput ? taskNameInput.value.trim() : `calib_${taskId}`;
    Promise.all(fileReadPromises)
      .then(() => {
        console.log(`Calibration Task ${taskId} data dictionary:`, sensorDataDict);
        // Store calibration data keyed by the task name.
        window.calibrationData = window.calibrationData || {};
        window.calibrationData[calibrationTaskName] = sensorDataDict;
      })
      .catch(err => {
        console.error("Error processing calibration files:", err);
        showModal("Error", "Failed to process calibration files. See console for details.");
      });
  }
  
  // -------------------------------
  // Main Task Upload
  // -------------------------------
  const mainTaskInput = document.getElementById('mainTaskUpload');
  const mainTaskStatus = document.getElementById('mainTaskStatus');
  mainTaskInput.addEventListener('change', () => {
    if (!window.sensorMapping) {
      showModal("Main Task", "Please upload the sensor placement file first.");
      mainTaskInput.value = "";
      return;
    }
    const files = Array.from(mainTaskInput.files);
    if (files.length === 0) return;
    const requiredSensors = ["pelvis", "thigh_l", "shank_l", "foot_l", "thigh_r", "shank_r", "foot_r"];
    const requiredIDs = Object.keys(window.sensorMapping).filter(id => {
      const sensorName = window.sensorMapping[id].toLowerCase();
      return requiredSensors.includes(sensorName);
    });
    if (requiredIDs.length < requiredSensors.length) {
      showModal("Main Task", "The sensor placement file does not include all required lower-limb sensors.");
      mainTaskInput.value = "";
      return;
    }
    const matchedFiles = files.filter(file => {
      const lowerName = file.name.toLowerCase();
      return requiredIDs.some(id => lowerName.includes(id.toLowerCase()));
    });
    if (matchedFiles.length < requiredIDs.length) {
      const foundIDs = matchedFiles.map(file => {
        const lowerName = file.name.toLowerCase();
        return requiredIDs.find(id => lowerName.includes(id.toLowerCase()));
      }).filter(Boolean);
      const missingIDs = requiredIDs.filter(id => !foundIDs.includes(id));
      const missingSensors = missingIDs.map(id => window.sensorMapping[id]);
      showModal("Main Task", "Missing main task files for: " + missingSensors.join(", "));
      mainTaskInput.value = "";
      return;
    }
    mainTaskStatus.innerHTML = "";
    const mainTaskDataDict = {};
    const fileReadPromises = matchedFiles.map(file => {
      return new Promise((resolve, reject) => {
        const lowerName = file.name.toLowerCase();
        const sensorID = requiredIDs.find(id => lowerName.includes(id.toLowerCase())) || file.name;
        const sensorName = window.sensorMapping[sensorID];
        const p = document.createElement('p');
        p.textContent = sensorName + " (" + file.name + ")";
        mainTaskStatus.appendChild(p);
        const reader = new FileReader();
        reader.onload = (e) => {
          const fileContent = e.target.result;
          mainTaskDataDict[sensorName.toLowerCase()] = {
            id: sensorID,
            fileName: file.name,
            content: fileContent
          };
          resolve();
        };
        reader.onerror = reject;
        reader.readAsText(file);
      });
    });
    Promise.all(fileReadPromises)
      .then(() => {
        console.log("Main Task data dictionary:", mainTaskDataDict);
        window.mainTaskData = mainTaskDataDict;
      })
      .catch(err => {
        console.error("Error processing main task files:", err);
        showModal("Error", "Failed to process main task files. See console for details.");
      });
  });
  
  // -------------------------------
  // Modal Functions
  // -------------------------------
  function showModal(title, message) {
    const modal = document.getElementById('customModal');
    const modalTitle = document.querySelector('.modal-title');
    const modalMessage = document.getElementById('modalMessage');
    modalTitle.textContent = title;
    if (/<\/?[a-z][\s\S]*>/i.test(message)) {
      modalMessage.innerHTML = message;
    } else if (message.includes("\n")) {
      modalMessage.innerHTML = message.split("\n").map(item => "• " + item).join("<br>");
    } else {
      modalMessage.textContent = message;
    }
    modal.style.display = 'block';
  }
  
  function hideModal() {
    document.getElementById('customModal').style.display = 'none';
  }
  
  document.getElementById('closeModalBtn').addEventListener('click', hideModal);
  
  // -------------------------------
  // Validate Inputs Before Running IK
  // -------------------------------
  function validateInputs() {
    const missing = [];
    console.log("Sensor Mapping:", window.sensorMapping);
    console.log("Main Task Data:", window.mainTaskData);
    console.log("Calibration Data:", window.calibrationData);
    if (!window.sensorMapping) {
      missing.push("Sensor Mapping file");
    }
    if (!window.mainTaskData) {
      missing.push("Main Task file");
    }
    if (!window.calibrationData || Object.keys(window.calibrationData).length === 0) {
      missing.push("Calibration Task data");
    }
    return missing;
  }
  
  // -------------------------------
  // Run IK Handler
  // -------------------------------
  const runIkBtn = document.getElementById('runIkBtn');
  const genVidBtn = document.getElementById('generateVideoBtn');

  runIkBtn.addEventListener('click', () => {
    const missingFields = validateInputs();
    if (missingFields.length > 0) {
      showModal("Missing Required Inputs", missingFields.join("\n"));
      return;
    }
  
    showModal("Processing", "Running inverse kinematics calculation. This may take a moment...");
  
    // Build main task data payload.
    const mainTaskData = {};
    Object.keys(window.mainTaskData).forEach(sensorName => {
      const sensorData = window.mainTaskData[sensorName];
      mainTaskData[sensorName] = processIMUDataContent(sensorData.content);
    });
  
    // Build calibration data payload.
    // Note: In this updated version, calibration data is stored in window.calibrationData keyed by user-assigned task names.
    const calibrationData = {};
    Object.keys(window.calibrationData).forEach(taskName => {
      const taskDict = window.calibrationData[taskName];
      calibrationData[taskName] = {};
      Object.keys(taskDict).forEach(sensorName => {
        const sensorData = taskDict[sensorName];
        calibrationData[taskName][sensorName] = processIMUDataContent(sensorData.content);
      });
    });
  
    const setupValue = document.getElementById('setupSelector')?.value || "mm";
    const filterValue = document.getElementById('filterSelector')?.value || "Xsens";
    const dimValue = document.getElementById('dimSelector')?.value || "9D";
    const removeOffsetValue = document.getElementById('removeOffsetCheckbox')?.checked || true;
  
    const payload = {
      subject: 1,
      task: "treadmill_walking",
      selected_setup: setupValue,
      filter_type: filterValue,
      dim: dimValue,
      remove_offset: removeOffsetValue,
      main_task_data: mainTaskData,
      calibration_data: calibrationData
    };

    genVidBtn.disabled = false

    console.log("Payload being sent to /run_ik:", payload);

  
    fetch('http://127.0.0.1:5000/run_ik', {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(res => {
        if (!res.ok) {
          return res.text().then(text => {
            try {
              const jsonError = JSON.parse(text);
              throw new Error(jsonError.message || jsonError.details || "Server error");
            } catch (e) {
              throw new Error(`Server error (${res.status}): ${text.substring(0, 100)}...`);
            }
          });
        }
        return res.json();
      })
      .then(data => {
        console.log("IK Results:", data);
        hideModal();
        if (data.status === "error") {
          throw new Error(data.message || "Unknown error");
        }
        window.ikResults = data.ik_results;
        const downloadLinksHTML = `
        <br><br>
        <a href="/download_csv" class="btn btn-primary" download>Download IK Results CSV</a>
        <br><br>
        <a href="/download_graphs_zip" class="btn btn-primary" download>Download IK Graphs (ZIP)</a>
      `;
      showModal("IK Processing Complete",
        "The inverse kinematics calculation has completed successfully." + downloadLinksHTML);
      })
      .catch(err => {
        console.error("Error running IK:", err);
        hideModal();
        showModal("Error", "Failed to run inverse kinematics: " + err.message);
      });
  });

   // Replace the existing video generation event handler with this improved version
genVidBtn.addEventListener('click', () => {
  const overlay = document.getElementById('info');
  const container = document.getElementById('imuContainer');
  
  // Clear the container and hide the IMU placement UI
  overlay.style.display = 'none';
  container.innerHTML = '';
  
  // Create and insert progress UI directly into the right panel
  const progressHTML = `
    <div id="videoProgressContainer" style="display:flex; flex-direction:column; justify-content:center; align-items:center; height:100%; padding:20px; background-color:#f0f0f0;">
      <h2>Generating Video</h2>
      <div style="width:80%; margin:20px 0; background-color:white; padding:20px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.1);">
        <div style="font-weight:bold; margin-bottom:10px;">Rendering Frames</div>
        <div style="width:100%; background:#e0e0e0; height:24px; border-radius:4px; overflow:hidden; position:relative;">
          <div id="progressBarFill" style="width:0%; height:100%; background:#2196F3; transition:width 0.3s;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:5px;">
          <span id="frameCount">Frame: 0/100</span>
          <span id="percentComplete">0%</span>
        </div>
        <div id="statusMessage" style="margin-top:15px; font-style:italic; color:#555;">Starting video generation...</div>
      </div>
    </div>
  `;
  container.innerHTML = progressHTML;
  
  // Get references to our progress elements
  const progressBarFill = document.getElementById('progressBarFill');
  const percentComplete = document.getElementById('percentComplete');
  const frameCount = document.getElementById('frameCount');
  const statusMessage = document.getElementById('statusMessage');
  
  // Build query parameters
  const params = new URLSearchParams({
    modelPath: "/Users/julianng-thow-hing/Documents/GitHub/mbl_osim2obj/Motions/subject22/scaled_model.osim",
    motPath: "/Users/julianng-thow-hing/Documents/GitHub/mbl_osim2obj/Motions/subject6/ik2.mot", 
    calibPath: "/Users/julianng-thow-hing/Documents/GitHub/mbl_osim2obj/Motions/subject6/calib.npz",
    subject: "subject22"
  });

  // Create EventSource for server-sent events
  const es = new EventSource(`/generate_video_stream?${params.toString()}`);

  // Track total frames and progress
  let totalFrames = 100; // Default to 100 frames - this matches what's in your logs
  let currentFrame = 0;
  
  // Handle all messages - log to console and parse for specific information
  es.onmessage = function(e) {
    console.log('[SSE]', e.data);
    
    // Check for total frames info
    if (e.data.includes('Total frames:')) {
      const match = e.data.match(/Total frames: (\d+)/);
      if (match && match[1]) {
        totalFrames = parseInt(match[1], 10);
        frameCount.textContent = `Frame: 0/${totalFrames}`;
      }
    }
    
    // Check for progress updates in the standard messages
    // The Python script outputs lines like "PROGRESS 46"
    if (e.data.includes('PROGRESS')) {
      const progressMatch = e.data.match(/PROGRESS (\d+)/);
      if (progressMatch && progressMatch[1]) {
        currentFrame = parseInt(progressMatch[1], 10);
        const percent = Math.min(Math.floor((currentFrame / totalFrames) * 100), 100);
        
        // Update UI elements
        progressBarFill.style.width = `${percent}%`;
        percentComplete.textContent = `${percent}%`;
        frameCount.textContent = `Frame: ${currentFrame}/${totalFrames}`;
        statusMessage.textContent = `Rendering frame ${currentFrame} of ${totalFrames}...`;
      }
    }
  };
  
  // Special handler for progress events - these come from the server with specific "event: progress" headers
  es.addEventListener("progress", function(e) {
    const percent = parseInt(e.data, 10);
    if (!isNaN(percent)) {
      progressBarFill.style.width = `${percent}%`;
      percentComplete.textContent = `${percent}%`;
      
      // Calculate current frame based on percentage
      currentFrame = Math.round((percent / 100) * totalFrames);
      frameCount.textContent = `Frame: ${currentFrame}/${totalFrames}`;
      statusMessage.textContent = `Rendering frame ${currentFrame} of ${totalFrames}...`;
    }
  });

  // Handle completion
  es.addEventListener("done", function(e) {
    es.close();
    
    if (e.data === "success") {
      // Replace progress UI with video player
      container.innerHTML = `
        <div style="display:flex; justify-content:center; align-items:center; height:100%; background-color:#000;">
          <video controls autoplay style="max-width:100%; max-height:100%;">
            <source src="/static/imu/subject22_ik.mp4" type="video/mp4">
          </video>
        </div>`;
    } else {
      container.innerHTML = `
        <div style="display:flex; justify-content:center; align-items:center; height:100%; background-color:#fff; color:#f44336; font-size:24px;">
          <div>
            <div style="text-align:center; margin-bottom:20px;">❌ Video generation failed</div>
            <button onclick="location.reload()" style="padding:10px 20px; background:#2196F3; color:white; border:none; border-radius:4px; cursor:pointer;">Reload App</button>
          </div>
        </div>`;
    }
  });

  // Handle errors
  es.onerror = function(err) {
    console.error('SSE Error:', err);
    es.close();
    
    // Provide a reload button
    container.innerHTML = `
      <div style="display:flex; justify-content:center; align-items:center; height:100%; background-color:#fff; color:#f44336; font-size:24px;">
        <div>
          <div style="text-align:center; margin-bottom:20px;">⚠️ Connection lost</div>
          <button onclick="location.reload()" style="padding:10px 20px; background:#2196F3; color:white; border:none; border-radius:4px; cursor:pointer;">Reload App</button>
        </div>
      </div>`;
  };
});

  
  // -------------------------------
  // Helper Function: Process IMU Data Content
  // -------------------------------
  function processIMUDataContent(content) {
    const lines = content.split('\n');
    let headerMap = null;
    let data = {};
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line === "" || line.startsWith("//")) continue;
      if (!headerMap) {
        const headers = line.split('\t');
        console.log("Parsed headers:", headers);
        headerMap = {};
        headers.forEach((header, index) => {
          headerMap[header] = index;
          if (
            header.startsWith('Acc_') ||
            header.startsWith('Gyr_') ||
            header.startsWith('Mag_') ||
            header.startsWith('Quat_')
          ) {
            data[header] = [];
          }
        });
        continue;
      }
      const values = line.split('\t');
      if (values.length < 3) continue;
      Object.keys(data).forEach(column => {
        if (headerMap[column] !== undefined && headerMap[column] < values.length) {
          const value = parseFloat(values[headerMap[column]]);
          if (!isNaN(value)) {
            data[column].push(value);
          }
        }
      });
    }
    const columnMapping = {
      'Quat_q0': 'Quat_W',
      'Quat_q1': 'Quat_X',
      'Quat_q2': 'Quat_Y',
      'Quat_q3': 'Quat_Z'
    };
    Object.keys(columnMapping).forEach(oldName => {
      if (data[oldName]) {
        data[columnMapping[oldName]] = data[oldName];
        delete data[oldName];
      }
    });
    console.log("Processed IMU data from file:", data);
    return data;
  }
  
  // // -------------------------------
  // // Video Player & Modal Functions (Unchanged)
  // // -------------------------------
  // const video = document.getElementById("preRenderedVideo");
  // const playPauseBtn = document.getElementById("playPauseBtn");
  // const progressBar = document.getElementById("progressBar");
  // const timeDisplay = document.getElementById("timeDisplay");
  // video.controls = false;
  // video.addEventListener("loadedmetadata", () => {
  //   progressBar.max = video.duration;
  //   updateTimeDisplay();
  // });
  // video.addEventListener("play", () => {
  //   requestAnimationFrame(updateProgress);
  // });
  // function updateProgress() {
  //   progressBar.value = video.currentTime;
  //   updateTimeDisplay();
  //   updateProgressBarBackground();
  //   if (!video.paused && !video.ended) {
  //     requestAnimationFrame(updateProgress);
  //   }
  // }
  // function updateProgressBarBackground() {
  //   const percentage = (video.currentTime / video.duration) * 100;
  //   progressBar.style.background = `linear-gradient(to right, #C41230 0%, #C41230 ${percentage}%, #ddd ${percentage}%, #ddd 100%)`;
  // }
  // playPauseBtn.addEventListener("click", () => {
  //   if (video.paused || video.ended) {
  //     video.play().then(() => {
  //       playPauseBtn.textContent = "Pause";
  //       requestAnimationFrame(updateProgress);
  //     }).catch(err => console.error("Play error:", err));
  //   } else {
  //     video.pause();
  //     playPauseBtn.textContent = "Play";
  //   }
  // });
  // progressBar.addEventListener("input", () => {
  //   video.currentTime = progressBar.value;
  //   updateTimeDisplay();
  //   updateProgressBarBackground();
  // });
  // function updateTimeDisplay() {
  //   const current = formatTime(video.currentTime);
  //   const duration = formatTime(video.duration);
  //   timeDisplay.textContent = `${current} / ${duration}`;
  // }
  // function formatTime(time) {
  //   if (isNaN(time)) return "0:00.0";
  //   const minutes = Math.floor(time / 60);
  //   const seconds = (time % 60).toFixed(1);
  //   return `${minutes}:${seconds}`;
  // }
});
