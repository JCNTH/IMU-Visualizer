// Import modules using the import map in index.html
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { DragControls } from 'three/addons/controls/DragControls.js';

document.addEventListener('DOMContentLoaded', () => {

  // ---------------- Global Variables ----------------
  let selectedSensorType = null;  // e.g. "pelvis", "leftThigh", etc.
  const sensorTypes = {
    pelvis: null,
    leftThigh: null,
    rightThigh: null,
    leftShank: null,
    rightShank: null,
    leftToes: null,
    rightToes: null
  };

  let currentSelectedSensor = null; // The active sensor for adjustments.
  let selectedPlacementView = "lateral"; // Informational only.
  let skeleton = null; // Will store the loaded skeleton.
  const raycaster = new THREE.Raycaster();
  const mouse = new THREE.Vector2();

  // Array to hold draggable sensor objects.
  const draggableSensors = [];
  let dragControls = null;  // To be set later.

  // ---------------- Scene Setup ----------------
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x222222);

  const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 5000);
  camera.position.set(0, 200, 600);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  // Append the renderer into the imuContainer instead of document.body.
  document.getElementById("imuContainer").appendChild(renderer.domElement);

  // ---------------- Orbit Controls ----------------
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(0, 100, 0);
  controls.update();

  // ---------------- Lights ----------------
  scene.add(new THREE.AmbientLight(0x888888));
  const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
  directionalLight.position.set(100, 500, 500);
  scene.add(directionalLight);

  // ---------------- UI: Sensor Type Buttons ----------------
  const sensorButtons = {
    pelvis: document.getElementById('btn-pelvis'),
    leftThigh: document.getElementById('btn-leftThigh'),
    rightThigh: document.getElementById('btn-rightThigh'),
    leftShank: document.getElementById('btn-leftShank'),
    rightShank: document.getElementById('btn-rightShank'),
    leftToes: document.getElementById('btn-leftToes'),
    rightToes: document.getElementById('btn-rightToes')
  };

  for (const type in sensorButtons) {
    // Always check that the element exists.
    const btn = sensorButtons[type];
    if (btn) {
      btn.addEventListener('click', () => {
        if (selectedSensorType === type) {
          btn.classList.remove('selected');
          selectedSensorType = null;
          currentSelectedSensor = null;
          document.getElementById('rotation-controls').style.display = 'none';
        } else {
          for (const key in sensorButtons) {
            if (sensorButtons[key]) {
              sensorButtons[key].classList.remove('selected');
            }
          }
          btn.classList.add('selected');
          selectedSensorType = type;
          if (sensorTypes[type]) {
            currentSelectedSensor = sensorTypes[type];
            updateRotationSlidersFromSensor(currentSelectedSensor);
            document.getElementById('rotation-controls').style.display = 'block';
          } else {
            currentSelectedSensor = null;
            document.getElementById('rotation-controls').style.display = 'none';
          }
        }
      });
    } else {
      console.warn(`Element with id ${type} not found in the DOM.`);
    }
  }

  // ---------------- UI: Placement View Buttons ----------------
  const viewButtons = {
    frontal: document.getElementById('view-frontal'),
    lateral: document.getElementById('view-lateral'),
    medial: document.getElementById('view-medial'),
    posterior: document.getElementById('view-posterior')
  };
  for (const view in viewButtons) {
    const btn = viewButtons[view];
    if (btn) {
      btn.addEventListener('click', () => {
        for (const key in viewButtons) {
          if (viewButtons[key]) {
            viewButtons[key].classList.remove('selected');
          }
        }
        btn.classList.add('selected');
        selectedPlacementView = view;
      });
    }
  }
  if (viewButtons["lateral"]) {
    viewButtons["lateral"].classList.add('selected'); // Default
  }

  // ---------------- UI: Rotation Sliders and Degree Displays ----------------
  const rotXSlider = document.getElementById('rot-x');
  const rotYSlider = document.getElementById('rot-y');
  const rotZSlider = document.getElementById('rot-z');
  const rotXValue = document.getElementById('rot-x-value');
  const rotYValue = document.getElementById('rot-y-value');
  const rotZValue = document.getElementById('rot-z-value');

  rotXSlider.addEventListener('input', () => {
    rotXValue.textContent = rotXSlider.value;
    if (currentSelectedSensor) applyCombinedRotation(currentSelectedSensor);
  });
  rotYSlider.addEventListener('input', () => {
    rotYValue.textContent = rotYSlider.value;
    if (currentSelectedSensor) applyCombinedRotation(currentSelectedSensor);
  });
  rotZSlider.addEventListener('input', () => {
    rotZValue.textContent = rotZSlider.value;
    if (currentSelectedSensor) applyCombinedRotation(currentSelectedSensor);
  });

  function updateRotationSlidersFromSensor(sensor) {
    const euler = new THREE.Euler().setFromQuaternion(sensor.quaternion, 'YXZ');
    const degX = THREE.MathUtils.radToDeg(euler.x).toFixed(0);
    const degY = THREE.MathUtils.radToDeg(euler.y).toFixed(0);
    const degZ = THREE.MathUtils.radToDeg(euler.z).toFixed(0);
    rotXSlider.value = degX;
    rotYSlider.value = degY;
    rotZSlider.value = degZ;
    rotXValue.textContent = degX;
    rotYValue.textContent = degY;
    rotZValue.textContent = degZ;
  }

  function showRotationControls() {
    document.getElementById('rotation-controls').style.display = 'block';
  }
  function hideRotationControls() {
    document.getElementById('rotation-controls').style.display = 'none';
  }

  // ---------------- UI: Axes Definition ----------------
  const axisUpSelect = document.getElementById('axis-up');
  const axisLeftSelect = document.getElementById('axis-left');
  const axisOutSelect = document.getElementById('axis-out');

  axisUpSelect.addEventListener('change', () => {
    if (currentSelectedSensor) applyCombinedRotation(currentSelectedSensor);
  });
  axisLeftSelect.addEventListener('change', () => {
    if (currentSelectedSensor) applyCombinedRotation(currentSelectedSensor);
  });
  axisOutSelect.addEventListener('change', () => {
    if (currentSelectedSensor) applyCombinedRotation(currentSelectedSensor);
  });

  function getDefaultAxis(letter) {
    if(letter === 'X') return new THREE.Vector3(1, 0, 0);
    if(letter === 'Y') return new THREE.Vector3(0, 1, 0);
    if(letter === 'Z') return new THREE.Vector3(0, 0, 1);
    return new THREE.Vector3(1, 0, 0);
  }

  // ---------------- Combined Rotation Function ----------------
  // Compose base rotation (from axes mapping) with slider rotation.
  function applyCombinedRotation(sensor) {
    if (!sensor) return;
    const upAxis = getDefaultAxis(axisUpSelect.value);
    const leftAxis = getDefaultAxis(axisLeftSelect.value);
    const outAxis = getDefaultAxis(axisOutSelect.value);
    if (new Set([axisUpSelect.value, axisLeftSelect.value, axisOutSelect.value]).size !== 3) {
      console.warn("Axes selections must be unique.");
      return;
    }
    const baseMat = new THREE.Matrix4();
    baseMat.makeBasis(upAxis, leftAxis, outAxis);
    const baseQuat = new THREE.Quaternion().setFromRotationMatrix(baseMat);
  
    const sx = THREE.MathUtils.degToRad(parseFloat(rotXSlider.value));
    const sy = THREE.MathUtils.degToRad(parseFloat(rotYSlider.value));
    const sz = THREE.MathUtils.degToRad(parseFloat(rotZSlider.value));
    const sliderEuler = new THREE.Euler(sx, sy, sz, 'YXZ');
    const sliderQuat = new THREE.Quaternion().setFromEuler(sliderEuler);
  
    sensor.quaternion.copy(baseQuat.multiply(sliderQuat));
  }

  // ---------------- Helper: Clean Geometry ----------------
  function cleanGeometry(geometry) {
    if (!geometry.isBufferGeometry) return;
    const posAttr = geometry.attributes.position;
    if (posAttr) {
      const arr = posAttr.array;
      let foundNaN = false;
      for (let i = 0; i < arr.length; i++) {
        if (Number.isNaN(arr[i]) || arr[i] === undefined) {
          arr[i] = 0;
          foundNaN = true;
        }
      }
      if (foundNaN) {
        console.warn("Cleaned NaN values in geometry");
        posAttr.needsUpdate = true;
        geometry.computeBoundingBox();
        geometry.computeBoundingSphere();
      }
    }
  }

  // ---------------- Load & Center Skeleton OBJ ----------------
  const objLoader = new OBJLoader();
  objLoader.load(
    './public/skeleton.obj',  // Adjust path if needed.
    (object) => {
      object.traverse((child) => {
        if (child.isMesh && child.geometry) {
          cleanGeometry(child.geometry);
          child.geometry.center();
        }
      });
      const box = new THREE.Box3().setFromObject(object);
      const boxCenter = box.getCenter(new THREE.Vector3());
      object.position.sub(boxCenter);
      
      skeleton = object;
      scene.add(skeleton);
      
      const newBox = new THREE.Box3().setFromObject(skeleton);
      const newBoxSize = newBox.getSize(new THREE.Vector3());
      const newCenter = newBox.getCenter(new THREE.Vector3());
      newCenter.x += 0.5; // This shifts the center point left by 20 units

      const halfSize = (newBoxSize.length() * 1.2) * 0.5;
      const halfFov = THREE.MathUtils.degToRad(camera.fov * 0.5);
      const distance = halfSize / Math.tan(halfFov);
      const direction = new THREE.Vector3().subVectors(camera.position, newCenter);
      direction.y = 0;
      direction.normalize();
      camera.position.copy(direction.multiplyScalar(distance * 0.8).add(newCenter));
      camera.near = newBoxSize.length() / 100;
      camera.far = newBoxSize.length() * 100;
      camera.updateProjectionMatrix();
      camera.lookAt(newCenter);
      
      controls.target.copy(newCenter);
      controls.maxDistance = newBoxSize.length() * 10;
      controls.update();
      
      dragControls = new DragControls(draggableSensors, camera, renderer.domElement);
      dragControls.addEventListener('dragstart', () => { controls.enabled = false; });
      dragControls.addEventListener('dragend', () => { controls.enabled = true; });
      dragControls.addEventListener('drag', (event) => {
        currentSelectedSensor = event.object;
        updateRotationSlidersFromSensor(currentSelectedSensor);
      });
      
      animate();
    },
    (xhr) => {
      if (xhr.total)
        console.log((xhr.loaded / xhr.total * 100).toFixed(2) + '% loaded');
    },
    (error) => {
      console.error('Error loading skeleton:', error);
    }
  );

  // ---------------- Mouse Click Handler ----------------
  renderer.domElement.addEventListener('click', onMouseClick, false);
  function onMouseClick(event) {
    event.preventDefault();
    if (!skeleton || !selectedSensorType) return;
  
    // Get the bounding rectangle of the renderer's DOM element.
    const rect = renderer.domElement.getBoundingClientRect();
    // Convert the mouse coordinates relative to the canvas.
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObject(skeleton, true);
    if (intersects.length > 0) {
      const intersect = intersects[0];
      const localPoint = intersect.point.clone();
      skeleton.worldToLocal(localPoint);
  
      // Compute sensor size relative to the skeleton’s bounding box.
      const box = new THREE.Box3().setFromObject(skeleton);
      const size = box.getSize(new THREE.Vector3());
      const sensorWidth = size.x * 0.05;
      const sensorHeight = size.y * 0.05;
      const sensorDepth = size.z * 0.05;
  
      let sensor = sensorTypes[selectedSensorType];
      if (!sensor) {
        const geom = new THREE.BoxGeometry(sensorWidth, sensorHeight, sensorDepth);
        const mat = new THREE.MeshLambertMaterial({ color: 0xff0000 });
        sensor = new THREE.Mesh(geom, mat);
        sensorTypes[selectedSensorType] = sensor;
        sensor.userData.placementView = selectedPlacementView;
        skeleton.add(sensor);
        draggableSensors.push(sensor);
        dragControls.objects = draggableSensors;
      }
      sensor.position.copy(localPoint);
      currentSelectedSensor = sensor;
      updateRotationSlidersFromSensor(sensor);
      document.getElementById('rotation-controls').style.display = 'block';
      applyCombinedRotation(sensor);
    }
  }
  

  // ---------------- Animation Loop ----------------
  function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
  }

  // ---------------- Resize Handler ----------------
  window.addEventListener('resize', onWindowResize, false);
  function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }
});
