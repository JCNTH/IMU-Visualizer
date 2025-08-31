// import * as THREE from 'three';
// import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
// import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';

// // ---------------- Global Variables ----------------
// let selectedSensorType = null; // e.g. "pelvis", "leftThigh", etc.
// const sensorTypes = {
//   pelvis: null,
//   leftThigh: null,
//   rightThigh: null,
//   leftShank: null,
//   rightShank: null,
//   leftToes: null,
//   rightToes: null
// };
// let currentSelectedSensor = null; // The sensor object currently active for rotation adjustments.
// let skeleton = null; // The loaded skeleton object.
// const raycaster = new THREE.Raycaster();
// const mouse = new THREE.Vector2();

// // ---------------- Scene Setup ----------------
// const scene = new THREE.Scene();
// scene.background = new THREE.Color(0x222222);

// const camera = new THREE.PerspectiveCamera(
//   45,
//   window.innerWidth / window.innerHeight,
//   0.1,
//   5000
// );
// camera.position.set(0, 200, 600);

// const renderer = new THREE.WebGLRenderer({ antialias: true });
// renderer.setSize(window.innerWidth, window.innerHeight);
// document.body.appendChild(renderer.domElement);

// // ---------------- Orbit Controls ----------------
// const controls = new OrbitControls(camera, renderer.domElement);
// controls.target.set(0, 100, 0);
// controls.update();

// // ---------------- Lights ----------------
// scene.add(new THREE.AmbientLight(0x888888));
// const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
// directionalLight.position.set(100, 500, 500);
// scene.add(directionalLight);

// // ---------------- UI: Sensor Type Buttons ----------------
// const sensorButtons = {
//   pelvis: document.getElementById('btn-pelvis'),
//   leftThigh: document.getElementById('btn-leftThigh'),
//   rightThigh: document.getElementById('btn-rightThigh'),
//   leftShank: document.getElementById('btn-leftShank'),
//   rightShank: document.getElementById('btn-rightShank'),
//   leftToes: document.getElementById('btn-leftToes'),
//   rightToes: document.getElementById('btn-rightToes')
// };

// for (const type in sensorButtons) {
//   sensorButtons[type].addEventListener('click', () => {
//     // Toggle selection: if already selected, deselect.
//     if (selectedSensorType === type) {
//       sensorButtons[type].classList.remove('selected');
//       selectedSensorType = null;
//       currentSelectedSensor = null;
//       document.getElementById('rotation-controls').style.display = 'none';
//     } else {
//       // Clear all selections.
//       for (const key in sensorButtons) {
//         sensorButtons[key].classList.remove('selected');
//       }
//       sensorButtons[type].classList.add('selected');
//       selectedSensorType = type;
//       // If a sensor already exists for this type, select it and show rotation sliders.
//       if (sensorTypes[type]) {
//         currentSelectedSensor = sensorTypes[type];
//         updateRotationSlidersFromSensor(currentSelectedSensor);
//         document.getElementById('rotation-controls').style.display = 'block';
//       } else {
//         currentSelectedSensor = null;
//         document.getElementById('rotation-controls').style.display = 'none';
//       }
//     }
//   });
// }

// // ---------------- Rotation Sliders ----------------
// const rotXSlider = document.getElementById('rot-x');
// const rotYSlider = document.getElementById('rot-y');
// const rotZSlider = document.getElementById('rot-z');

// rotXSlider.addEventListener('input', updateSensorRotation);
// rotYSlider.addEventListener('input', updateSensorRotation);
// rotZSlider.addEventListener('input', updateSensorRotation);

// function updateSensorRotation() {
//   if (!currentSelectedSensor) return;
//   const x = THREE.MathUtils.degToRad(parseFloat(rotXSlider.value));
//   const y = THREE.MathUtils.degToRad(parseFloat(rotYSlider.value));
//   const z = THREE.MathUtils.degToRad(parseFloat(rotZSlider.value));
//   currentSelectedSensor.rotation.set(x, y, z);
// }

// function updateRotationSlidersFromSensor(sensor) {
//   rotXSlider.value = THREE.MathUtils.radToDeg(sensor.rotation.x);
//   rotYSlider.value = THREE.MathUtils.radToDeg(sensor.rotation.y);
//   rotZSlider.value = THREE.MathUtils.radToDeg(sensor.rotation.z);
// }

// // ---------------- Helper Function: Clean Geometry ----------------
// function cleanGeometry(geometry) {
//   if (!geometry.isBufferGeometry) return;
//   const posAttr = geometry.attributes.position;
//   if (posAttr) {
//     const arr = posAttr.array;
//     let foundNaN = false;
//     for (let i = 0; i < arr.length; i++) {
//       if (Number.isNaN(arr[i]) || arr[i] === undefined) {
//         arr[i] = 0;
//         foundNaN = true;
//       }
//     }
//     if (foundNaN) {
//       console.warn("Cleaned NaN values in geometry");
//       posAttr.needsUpdate = true;
//       geometry.computeBoundingBox();
//       geometry.computeBoundingSphere();
//     }
//   }
// }

// // ---------------- Load & Center Skeleton OBJ ----------------
// const objLoader = new OBJLoader();
// objLoader.load(
//   '/skeleton.obj',
//   (object) => {
//     // For each mesh in the skeleton, clean and center its geometry.
//     object.traverse((child) => {
//       if (child.isMesh && child.geometry) {
//         cleanGeometry(child.geometry);
//         child.geometry.center(); // Center vertices so each mesh's local origin is its center.
//       }
//     });
    
//     // Compute overall bounding box & center for the skeleton.
//     const box = new THREE.Box3().setFromObject(object);
//     const boxCenter = box.getCenter(new THREE.Vector3());
//     object.position.sub(boxCenter); // Shift the skeleton so its center is at (0,0,0).
    
//     skeleton = object;
//     scene.add(skeleton);
    
//     // Reframe the camera to focus on the skeleton.
//     const newBox = new THREE.Box3().setFromObject(skeleton);
//     const newBoxSize = newBox.getSize(new THREE.Vector3());
//     const newCenter = newBox.getCenter(new THREE.Vector3());
//     const halfSize = (newBoxSize.length() * 1.2) * 0.5;
//     const halfFov = THREE.MathUtils.degToRad(camera.fov * 0.5);
//     const distance = halfSize / Math.tan(halfFov);
//     const direction = new THREE.Vector3().subVectors(camera.position, newCenter);
//     direction.y = 0;
//     direction.normalize();
//     camera.position.copy(direction.multiplyScalar(distance).add(newCenter));
//     camera.near = newBoxSize.length() / 100;
//     camera.far = newBoxSize.length() * 100;
//     camera.updateProjectionMatrix();
//     camera.lookAt(newCenter);
    
//     controls.target.copy(newCenter);
//     controls.maxDistance = newBoxSize.length() * 10;
//     controls.update();
    
//     animate();
//   },
//   (xhr) => {
//     if (xhr.total)
//       console.log((xhr.loaded / xhr.total * 100).toFixed(2) + '% loaded');
//   },
//   (error) => {
//     console.error('Error loading skeleton:', error);
//   }
// );

// // ---------------- Mouse Click Handler ----------------
// // When a sensor type is selected and the user clicks on the skeleton,
// // the raycaster finds the intersection and places/updates the sensor.
// renderer.domElement.addEventListener('click', onMouseClick, false);
// function onMouseClick(event) {
//   event.preventDefault();
//   if (!skeleton || !selectedSensorType) return;
  
//   // Convert mouse click to normalized device coordinates.
//   mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
//   mouse.y = - (event.clientY / window.innerHeight) * 2 + 1;
//   raycaster.setFromCamera(mouse, camera);
//   const intersects = raycaster.intersectObject(skeleton, true);
//   if (intersects.length > 0) {
//     const intersect = intersects[0];
//     // Convert the world-space hit point to skeleton-local coordinates.
//     const localPoint = intersect.point.clone();
//     skeleton.worldToLocal(localPoint);
    
//     // Compute sensor size relative to the skeleton’s bounding box.
//     const box = new THREE.Box3().setFromObject(skeleton);
//     const size = box.getSize(new THREE.Vector3());
//     const sensorWidth = size.x * 0.05;
//     const sensorHeight = size.y * 0.05;
//     const sensorDepth = size.z * 0.05;
    
//     // If a sensor of this type does not exist, create it.
//     let sensor = sensorTypes[selectedSensorType];
//     if (!sensor) {
//       const geom = new THREE.BoxGeometry(sensorWidth, sensorHeight, sensorDepth);
//       const mat = new THREE.MeshLambertMaterial({ color: 0xff0000 });
//       sensor = new THREE.Mesh(geom, mat);
//       sensorTypes[selectedSensorType] = sensor;
//       skeleton.add(sensor);
//     }
    
//     // Place (or update) the sensor at the clicked local point.
//     sensor.position.copy(localPoint);
//     currentSelectedSensor = sensor;
//     updateRotationSlidersFromSensor(sensor);
//     document.getElementById('rotation-controls').style.display = 'block';
//   }
// }

// // ---------------- Animation Loop ----------------
// function animate() {
//   requestAnimationFrame(animate);
//   renderer.render(scene, camera);
// }

// // ---------------- Resize Handler ----------------
// window.addEventListener('resize', onWindowResize, false);
// function onWindowResize() {
//   camera.aspect = window.innerWidth / window.innerHeight;
//   camera.updateProjectionMatrix();
//   renderer.setSize(window.innerWidth, window.innerHeight);
// }
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { DragControls } from 'three/addons/controls/DragControls.js';

// ---------------- Global Variables ----------------
let selectedSensorType = null; // e.g., "pelvis", "leftThigh", etc.
const sensorTypes = {
  pelvis: null,
  leftThigh: null,
  rightThigh: null,
  leftShank: null,
  rightShank: null,
  leftToes: null,
  rightToes: null
};

let currentSelectedSensor = null; // The sensor that's currently active for adjustments.
let selectedPlacementView = "lateral"; // Informational only.
let skeleton = null; // The loaded skeleton object.

const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

// Array to hold draggable sensor objects.
const draggableSensors = [];
let dragControls = null; // Will hold the DragControls instance

// ---------------- Scene Setup ----------------
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x222222);

const camera = new THREE.PerspectiveCamera(
  45,
  window.innerWidth / window.innerHeight,
  0.1,
  5000
);
camera.position.set(0, 200, 600);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

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
  sensorButtons[type].addEventListener('click', () => {
    if (selectedSensorType === type) {
      sensorButtons[type].classList.remove('selected');
      selectedSensorType = null;
      currentSelectedSensor = null;
      hideRotationControls();
    } else {
      for (const key in sensorButtons) {
        sensorButtons[key].classList.remove('selected');
      }
      sensorButtons[type].classList.add('selected');
      selectedSensorType = type;
      if (sensorTypes[type]) {
        currentSelectedSensor = sensorTypes[type];
        updateRotationSlidersFromSensor(currentSelectedSensor);
        showRotationControls();
        applyCombinedRotation(currentSelectedSensor);
      } else {
        currentSelectedSensor = null;
        hideRotationControls();
      }
    }
  });
}

// ---------------- UI: Placement View Buttons ----------------
const viewButtons = {
  frontal: document.getElementById('view-frontal'),
  lateral: document.getElementById('view-lateral'),
  medial: document.getElementById('view-medial'),
  posterior: document.getElementById('view-posterior')
};
for (const view in viewButtons) {
  viewButtons[view].addEventListener('click', () => {
    for (const key in viewButtons) {
      viewButtons[key].classList.remove('selected');
    }
    viewButtons[view].classList.add('selected');
    selectedPlacementView = view;
  });
}
viewButtons["lateral"].classList.add('selected'); // Default

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
  const euler = new THREE.Euler().setFromQuaternion(sensor.quaternion, 'XYZ');
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
  const sliderEuler = new THREE.Euler(sx, sy, sz, 'XYZ');
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

// ---------------- Loading & Centering Skeleton ----------------
const objLoader = new OBJLoader();
objLoader.load(
  './public/skeleton.obj', // Adjust path as needed.
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
    const halfSize = (newBoxSize.length() * 1.2) * 0.5;
    const halfFov = THREE.MathUtils.degToRad(camera.fov * 0.5);
    const distance = halfSize / Math.tan(halfFov);
    const direction = new THREE.Vector3().subVectors(camera.position, newCenter);
    direction.y = 0;
    direction.normalize();
    camera.position.copy(direction.multiplyScalar(distance).add(newCenter));
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
  
  mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
  mouse.y = - (event.clientY / window.innerHeight) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObject(skeleton, true);
  if (intersects.length > 0) {
    const intersect = intersects[0];
    const localPoint = intersect.point.clone();
    skeleton.worldToLocal(localPoint);
    
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
    showRotationControls();
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
