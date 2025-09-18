"use client";

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { OBJLoader } from "three/examples/jsm/loaders/OBJLoader.js";
import { DragControls } from "three/examples/jsm/controls/DragControls.js";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

type SensorType = "pelvis" | "leftThigh" | "rightThigh" | "leftShank" | "rightShank" | "leftToes" | "rightToes";
type ViewType = "frontal" | "lateral" | "medial" | "posterior";
type AxisType = "X" | "Y" | "Z";

interface SensorState {
  pelvis?: THREE.Mesh;
  leftThigh?: THREE.Mesh;
  rightThigh?: THREE.Mesh;
  leftShank?: THREE.Mesh;
  rightShank?: THREE.Mesh;
  leftToes?: THREE.Mesh;
  rightToes?: THREE.Mesh;
}

interface RotationValues {
  x: number;
  y: number;
  z: number;
}

export function IMUVisualization() {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const skeletonRef = useRef<THREE.Group | null>(null);
  const dragControlsRef = useRef<DragControls | null>(null);
  
  const [selectedSensorType, setSelectedSensorType] = useState<SensorType | null>(null);
  const [selectedView, setSelectedView] = useState<ViewType>("lateral");
  const [rotationValues, setRotationValues] = useState<RotationValues>({ x: 0, y: 0, z: 0 });
  const [axisMapping, setAxisMapping] = useState({ up: "X", left: "Y", out: "Z" });
  const [showControls, setShowControls] = useState(true);
  
  const sensorTypesRef = useRef<SensorState>({});
  const currentSelectedSensorRef = useRef<THREE.Mesh | null>(null);
  const draggableSensorsRef = useRef<THREE.Mesh[]>([]);

  const sensorButtons: { type: SensorType; label: string }[] = [
    { type: "pelvis", label: "Pelvis" },
    { type: "leftThigh", label: "Left Thigh" },
    { type: "rightThigh", label: "Right Thigh" },
    { type: "leftShank", label: "Left Shank" },
    { type: "rightShank", label: "Right Shank" },
    { type: "leftToes", label: "Left Toes" },
    { type: "rightToes", label: "Right Toes" },
  ];

  const viewButtons: { type: ViewType; label: string }[] = [
    { type: "frontal", label: "Frontal" },
    { type: "lateral", label: "Lateral" },
    { type: "medial", label: "Medial" },
    { type: "posterior", label: "Posterior" },
  ];

  useEffect(() => {
    if (!mountRef.current) return;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x222222);
    sceneRef.current = scene;

    // Camera setup
    const camera = new THREE.PerspectiveCamera(
      45,
      mountRef.current.clientWidth / mountRef.current.clientHeight,
      0.1,
      5000
    );
    camera.position.set(0, 200, 600);
    cameraRef.current = camera;

    // Renderer setup
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Controls setup
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 100, 0);
    controls.update();
    controlsRef.current = controls;

    // Lighting
    scene.add(new THREE.AmbientLight(0x888888));
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(100, 500, 500);
    scene.add(directionalLight);

    // Load skeleton
    const objLoader = new OBJLoader();
    objLoader.load(
      "/skeleton.obj",
      (object) => {
        // Clean and center the skeleton
        object.traverse((child) => {
          if (child instanceof THREE.Mesh && child.geometry) {
            cleanGeometry(child.geometry);
            child.geometry.center();
          }
        });

        const box = new THREE.Box3().setFromObject(object);
        const boxCenter = box.getCenter(new THREE.Vector3());
        object.position.sub(boxCenter);

        skeletonRef.current = object;
        scene.add(object);

        // Setup camera positioning
        const newBox = new THREE.Box3().setFromObject(object);
        const newBoxSize = newBox.getSize(new THREE.Vector3());
        const newCenter = newBox.getCenter(new THREE.Vector3());
        newCenter.x += 0.5;

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

        // Setup drag controls
        const dragControls = new DragControls(draggableSensorsRef.current, camera, renderer.domElement);
        dragControlsRef.current = dragControls;
        
        dragControls.addEventListener("dragstart", () => {
          controls.enabled = false;
        });
        
        dragControls.addEventListener("dragend", () => {
          controls.enabled = true;
        });
        
        dragControls.addEventListener("drag", (event) => {
          currentSelectedSensorRef.current = event.object as THREE.Mesh;
          updateRotationSlidersFromSensor(event.object as THREE.Mesh);
        });

        // Start animation loop
        animate();
      },
      (xhr) => {
        if (xhr.total) {
          console.log((xhr.loaded / xhr.total * 100).toFixed(2) + "% loaded");
        }
      },
      (error) => {
        console.error("Error loading skeleton:", error);
      }
    );

    // Mouse click handler for sensor placement
    const onMouseClick = (event: MouseEvent) => {
      event.preventDefault();
      if (!skeletonRef.current || !selectedSensorType) return;

      const rect = renderer.domElement.getBoundingClientRect();
      const mouse = new THREE.Vector2();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      const raycaster = new THREE.Raycaster();
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObject(skeletonRef.current, true);
      
      if (intersects.length > 0) {
        const intersect = intersects[0];
        const localPoint = intersect.point.clone();
        skeletonRef.current.worldToLocal(localPoint);

        placeSensor(selectedSensorType, localPoint);
      }
    };

    renderer.domElement.addEventListener("click", onMouseClick);

    // Cleanup
    return () => {
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [selectedSensorType]);

  const cleanGeometry = (geometry: THREE.BufferGeometry) => {
    const posAttr = geometry.attributes.position;
    if (posAttr) {
      const arr = posAttr.array as Float32Array;
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
  };

  const placeSensor = (sensorType: SensorType, position: THREE.Vector3) => {
    if (!skeletonRef.current) return;

    // Calculate sensor size relative to skeleton
    const box = new THREE.Box3().setFromObject(skeletonRef.current);
    const size = box.getSize(new THREE.Vector3());
    const sensorWidth = size.x * 0.05;
    const sensorHeight = size.y * 0.05;
    const sensorDepth = size.z * 0.05;

    let sensor = sensorTypesRef.current[sensorType];
    if (!sensor) {
      const geometry = new THREE.BoxGeometry(sensorWidth, sensorHeight, sensorDepth);
      const material = new THREE.MeshLambertMaterial({ color: 0xff0000 });
      sensor = new THREE.Mesh(geometry, material);
      sensorTypesRef.current[sensorType] = sensor;
      sensor.userData = { sensorType, placementView: selectedView };
      skeletonRef.current.add(sensor);
      draggableSensorsRef.current.push(sensor);
      if (dragControlsRef.current) {
        dragControlsRef.current.objects = draggableSensorsRef.current;
      }
    }

    sensor.position.copy(position);
    currentSelectedSensorRef.current = sensor;
    updateRotationSlidersFromSensor(sensor);
    applyCombinedRotation(sensor);
  };

  const updateRotationSlidersFromSensor = (sensor: THREE.Mesh) => {
    const euler = new THREE.Euler().setFromQuaternion(sensor.quaternion, "YXZ");
    const degX = Math.round(THREE.MathUtils.radToDeg(euler.x));
    const degY = Math.round(THREE.MathUtils.radToDeg(euler.y));
    const degZ = Math.round(THREE.MathUtils.radToDeg(euler.z));
    
    setRotationValues({ x: degX, y: degY, z: degZ });
  };

  const getDefaultAxis = (letter: AxisType): THREE.Vector3 => {
    switch (letter) {
      case "X": return new THREE.Vector3(1, 0, 0);
      case "Y": return new THREE.Vector3(0, 1, 0);
      case "Z": return new THREE.Vector3(0, 0, 1);
      default: return new THREE.Vector3(1, 0, 0);
    }
  };

  const applyCombinedRotation = (sensor: THREE.Mesh) => {
    if (!sensor) return;

    const upAxis = getDefaultAxis(axisMapping.up as AxisType);
    const leftAxis = getDefaultAxis(axisMapping.left as AxisType);
    const outAxis = getDefaultAxis(axisMapping.out as AxisType);

    // Check for unique axes
    if (new Set([axisMapping.up, axisMapping.left, axisMapping.out]).size !== 3) {
      console.warn("Axes selections must be unique.");
      return;
    }

    const baseMat = new THREE.Matrix4();
    baseMat.makeBasis(upAxis, leftAxis, outAxis);
    const baseQuat = new THREE.Quaternion().setFromRotationMatrix(baseMat);

    const sx = THREE.MathUtils.degToRad(rotationValues.x);
    const sy = THREE.MathUtils.degToRad(rotationValues.y);
    const sz = THREE.MathUtils.degToRad(rotationValues.z);
    const sliderEuler = new THREE.Euler(sx, sy, sz, "YXZ");
    const sliderQuat = new THREE.Quaternion().setFromEuler(sliderEuler);

    sensor.quaternion.copy(baseQuat.multiply(sliderQuat));
  };

  const handleSensorSelect = (sensorType: SensorType) => {
    if (selectedSensorType === sensorType) {
      setSelectedSensorType(null);
      currentSelectedSensorRef.current = null;
    } else {
      setSelectedSensorType(sensorType);
      const sensor = sensorTypesRef.current[sensorType];
      if (sensor) {
        currentSelectedSensorRef.current = sensor;
        updateRotationSlidersFromSensor(sensor);
      }
    }
  };

  const handleRotationChange = (axis: keyof RotationValues, value: number) => {
    const newRotation = { ...rotationValues, [axis]: value };
    setRotationValues(newRotation);
    
    if (currentSelectedSensorRef.current) {
      // Apply rotation immediately
      const sensor = currentSelectedSensorRef.current;
      const sx = THREE.MathUtils.degToRad(newRotation.x);
      const sy = THREE.MathUtils.degToRad(newRotation.y);
      const sz = THREE.MathUtils.degToRad(newRotation.z);
      const euler = new THREE.Euler(sx, sy, sz, "YXZ");
      sensor.quaternion.setFromEuler(euler);
    }
  };

  const animate = () => {
    requestAnimationFrame(animate);
    if (rendererRef.current && sceneRef.current && cameraRef.current) {
      rendererRef.current.render(sceneRef.current, cameraRef.current);
    }
  };

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (mountRef.current && cameraRef.current && rendererRef.current) {
        cameraRef.current.aspect = mountRef.current.clientWidth / mountRef.current.clientHeight;
        cameraRef.current.updateProjectionMatrix();
        rendererRef.current.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div className="w-full h-full relative">
      {/* 3D Visualization Container */}
      <div ref={mountRef} className="w-full h-full" />

      {/* Control Panel */}
      {showControls && (
        <Card className="absolute top-4 left-4 w-80 max-h-[calc(100vh-2rem)] overflow-y-auto bg-white/95 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">IMU Sensor Placement</CardTitle>
            <Button
              variant="ghost"
              size="sm"
              className="absolute top-2 right-2"
              onClick={() => setShowControls(false)}
            >
              ✕
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Sensor Type Selection */}
            <div>
              <Label className="text-sm font-medium mb-2 block">Select Sensor Type:</Label>
              <div className="grid grid-cols-2 gap-2">
                {sensorButtons.map(({ type, label }) => (
                  <Button
                    key={type}
                    variant={selectedSensorType === type ? "default" : "outline"}
                    size="sm"
                    className={`text-xs ${
                      selectedSensorType === type 
                        ? "bg-[#C41230] hover:bg-[#a10e25]" 
                        : "hover:bg-gray-100"
                    }`}
                    onClick={() => handleSensorSelect(type)}
                  >
                    {label}
                  </Button>
                ))}
              </div>
            </div>

            {/* Placement View */}
            <div>
              <Label className="text-sm font-medium mb-2 block">Placement View (Informational)</Label>
              <div className="grid grid-cols-2 gap-2">
                {viewButtons.map(({ type, label }) => (
                  <Button
                    key={type}
                    variant={selectedView === type ? "default" : "outline"}
                    size="sm"
                    className={`text-xs ${
                      selectedView === type 
                        ? "bg-gray-600 hover:bg-gray-700" 
                        : "hover:bg-gray-100"
                    }`}
                    onClick={() => setSelectedView(type)}
                  >
                    {label}
                  </Button>
                ))}
              </div>
            </div>

            {/* Rotation Controls */}
            {selectedSensorType && currentSelectedSensorRef.current && (
              <div>
                <Label className="text-sm font-medium mb-2 block">Rotation Fine-Tuning (°)</Label>
                <div className="space-y-3">
                  {(["x", "y", "z"] as const).map((axis) => (
                    <div key={axis} className="flex items-center space-x-2">
                      <Label className="w-4 text-xs">{axis.toUpperCase()}:</Label>
                      <input
                        type="range"
                        min="0"
                        max="360"
                        value={rotationValues[axis]}
                        onChange={(e) => handleRotationChange(axis, parseInt(e.target.value))}
                        className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                      />
                      <span className="w-8 text-xs text-right">{rotationValues[axis]}°</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Axis Definition */}
            <div>
              <Label className="text-sm font-medium mb-2 block">Define Sensor Axes</Label>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Label className="w-16 text-xs">Up Axis:</Label>
                  <Select value={axisMapping.up} onValueChange={(value) => setAxisMapping({...axisMapping, up: value})}>
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="X">X</SelectItem>
                      <SelectItem value="Y">Y</SelectItem>
                      <SelectItem value="Z">Z</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center space-x-2">
                  <Label className="w-16 text-xs">Left Axis:</Label>
                  <Select value={axisMapping.left} onValueChange={(value) => setAxisMapping({...axisMapping, left: value})}>
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="X">X</SelectItem>
                      <SelectItem value="Y">Y</SelectItem>
                      <SelectItem value="Z">Z</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center space-x-2">
                  <Label className="w-16 text-xs">Out Axis:</Label>
                  <Select value={axisMapping.out} onValueChange={(value) => setAxisMapping({...axisMapping, out: value})}>
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="X">X</SelectItem>
                      <SelectItem value="Y">Y</SelectItem>
                      <SelectItem value="Z">Z</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* Instructions */}
            <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
              <p className="font-medium mb-1">Instructions:</p>
              <p>1. Select a sensor type above</p>
              <p>2. Click on the skeleton to place the sensor</p>
              <p>3. Drag sensors to reposition them</p>
              <p>4. Use rotation controls to fine-tune orientation</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Toggle Controls Button */}
      {!showControls && (
        <Button
          className="absolute top-4 left-4 bg-[#C41230] hover:bg-[#a10e25]"
          onClick={() => setShowControls(true)}
        >
          Show Controls
        </Button>
      )}
    </div>
  );
} 