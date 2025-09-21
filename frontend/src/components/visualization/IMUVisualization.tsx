"use client";

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { OBJLoader } from "three/examples/jsm/loaders/OBJLoader.js";
import { DragControls } from "three/examples/jsm/controls/DragControls.js";
import { useIMUStore } from "@/store/imuStore";

interface IMUVisualizationProps {
  sidebarCollapsed?: boolean;
}

export function IMUVisualization({ sidebarCollapsed = false }: IMUVisualizationProps) {
  const { 
    selectedSensorType, 
    selectedView, 
    rotationValues, 
    axisMapping,
    setRotationValues,
    setSensorPlacement 
  } = useIMUStore();
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const skeletonRef = useRef<THREE.Object3D | null>(null);
  const dragControlsRef = useRef<DragControls | null>(null);
  
  const sensorTypesRef = useRef<{ [key: string]: THREE.Mesh }>({});
  const draggableSensorsRef = useRef<THREE.Mesh[]>([]);
  
  // Client-side only rendering to prevent hydration issues
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Handle sidebar resize with smooth transitions
  useEffect(() => {
    if (!isClient || !mountRef.current || !cameraRef.current || !rendererRef.current) return;

    const resizeCanvas = () => {
      if (mountRef.current && cameraRef.current && rendererRef.current) {
        const width = mountRef.current.clientWidth;
        const height = mountRef.current.clientHeight;
        
        cameraRef.current.aspect = width / height;
        cameraRef.current.updateProjectionMatrix();
        rendererRef.current.setSize(width, height);
      }
    };

    // Use ResizeObserver for smooth, continuous resizing
    const resizeObserver = new ResizeObserver(() => {
      resizeCanvas();
    });

    if (mountRef.current) {
      resizeObserver.observe(mountRef.current);
    }

    return () => {
      resizeObserver.disconnect();
    };
  }, [isClient]);

  const createSimpleSkeleton = (scene: THREE.Scene) => {
    console.log("Creating simple skeleton...");
    
    const skeletonGroup = new THREE.Group();
    
    // Create simple skeleton using boxes
    const createBone = (width: number, height: number, depth: number, color: number = 0x888888) => {
      const geometry = new THREE.BoxGeometry(width, height, depth);
      const material = new THREE.MeshLambertMaterial({ color, wireframe: false });
      return new THREE.Mesh(geometry, material);
    };
    
    // Pelvis
    const pelvis = createBone(40, 20, 30, 0xaaaaaa);
    pelvis.position.set(0, 100, 0);
    skeletonGroup.add(pelvis);
    
    // Left leg
    const leftThigh = createBone(15, 50, 15, 0x999999);
    leftThigh.position.set(-15, 75, 0);
    skeletonGroup.add(leftThigh);
    
    const leftShank = createBone(12, 45, 12, 0x999999);
    leftShank.position.set(-15, 30, 0);
    skeletonGroup.add(leftShank);
    
    const leftFoot = createBone(25, 8, 10, 0x999999);
    leftFoot.position.set(-15, 5, 5);
    skeletonGroup.add(leftFoot);
    
    // Right leg
    const rightThigh = createBone(15, 50, 15, 0x999999);
    rightThigh.position.set(15, 75, 0);
    skeletonGroup.add(rightThigh);
    
    const rightShank = createBone(12, 45, 12, 0x999999);
    rightShank.position.set(15, 30, 0);
    skeletonGroup.add(rightShank);
    
    const rightFoot = createBone(25, 8, 10, 0x999999);
    rightFoot.position.set(15, 5, 5);
    skeletonGroup.add(rightFoot);
    
    // Torso
    const torso = createBone(35, 60, 20, 0xaaaaaa);
    torso.position.set(0, 140, 0);
    skeletonGroup.add(torso);
    
    skeletonRef.current = skeletonGroup;
    scene.add(skeletonGroup);
    
    // Setup drag controls
    if (cameraRef.current && rendererRef.current) {
      const dragControls = new DragControls(draggableSensorsRef.current, cameraRef.current, rendererRef.current.domElement);
      dragControlsRef.current = dragControls;
      
      dragControls.addEventListener("dragstart", () => {
        if (controlsRef.current) controlsRef.current.enabled = false;
      });
      
      dragControls.addEventListener("dragend", () => {
        if (controlsRef.current) controlsRef.current.enabled = true;
      });
      
      dragControls.addEventListener("drag", (event) => {
        const sensor = event.object as THREE.Mesh;
        if (sensor.userData.sensorType && skeletonRef.current) {
          // Snap sensor to skeleton surface during drag
          snapSensorToSkeleton(sensor);
          
          // Update rotation values in store when sensor is moved
          const euler = new THREE.Euler().setFromQuaternion(sensor.quaternion, "YXZ");
          const degX = Math.round(THREE.MathUtils.radToDeg(euler.x));
          const degY = Math.round(THREE.MathUtils.radToDeg(euler.y));
          const degZ = Math.round(THREE.MathUtils.radToDeg(euler.z));
          setRotationValues({ x: degX, y: degY, z: degZ });
        }
      });
    }
    
    console.log("Simple skeleton created and added to scene");
  };

  const cleanGeometry = (geometry: THREE.BufferGeometry) => {
    const posAttr = geometry.attributes.position;
    if (posAttr) {
      const arr = posAttr.array as Float32Array;
      let foundNaN = false;
      for (let i = 0; i < arr.length; i++) {
        if (Number.isNaN(arr[i]) || arr[i] === undefined || !isFinite(arr[i])) {
          arr[i] = 0;
          foundNaN = true;
        }
      }
      if (foundNaN) {
        console.warn("Cleaned NaN/infinite values in geometry");
        posAttr.needsUpdate = true;
        geometry.computeBoundingBox();
        geometry.computeBoundingSphere();
      }
    }
  };

  const animate = () => {
    requestAnimationFrame(animate);
    if (rendererRef.current && sceneRef.current && cameraRef.current) {
      rendererRef.current.render(sceneRef.current, cameraRef.current);
    }
  };

  useEffect(() => {
    if (!mountRef.current || !isClient) return;

    // Scene setup (matching legacy implementation)
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x222222);
    sceneRef.current = scene;

    // Camera setup (matching legacy)
    const camera = new THREE.PerspectiveCamera(
      45,
      mountRef.current.clientWidth / mountRef.current.clientHeight,
      0.1,
      5000
    );
    camera.position.set(0, 200, 600);
    cameraRef.current = camera;

    // Renderer setup (matching legacy)
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Controls setup (matching legacy)
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 100, 0);
    controls.update();
    controlsRef.current = controls;

    // Lighting (matching legacy)
    scene.add(new THREE.AmbientLight(0x888888));
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(100, 500, 500);
    scene.add(directionalLight);

    // Try to load detailed skeleton first, fallback to simple if it fails
    const objLoader = new OBJLoader();
    console.log("Loading skeleton from /skeleton.obj...");
    
    objLoader.load(
      "/skeleton.obj",
      (object) => {
        console.log("Skeleton loaded successfully:", object);
        
        // Process the loaded skeleton
        object.traverse((child) => {
          if (child instanceof THREE.Mesh && child.geometry) {
            cleanGeometry(child.geometry);
            child.geometry.center();
            // Set material to be more visible
            child.material = new THREE.MeshLambertMaterial({ 
              color: 0xcccccc, 
              transparent: false 
            });
          }
        });

        // Center the skeleton
        const box = new THREE.Box3().setFromObject(object);
        const boxCenter = box.getCenter(new THREE.Vector3());
        object.position.sub(boxCenter);

        // Position camera (matching legacy implementation)
        const newBox = new THREE.Box3().setFromObject(object);
        const newBoxSize = newBox.getSize(new THREE.Vector3());
        const newCenter = newBox.getCenter(new THREE.Vector3());
        newCenter.x += 0.5; // This shifts the center point left by 0.5 units

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

        skeletonRef.current = object;
        scene.add(object);
        
        // Setup drag controls (matching legacy)
        const dragControls = new DragControls(draggableSensorsRef.current, camera, renderer.domElement);
        dragControlsRef.current = dragControls;
        
        dragControls.addEventListener("dragstart", () => {
          controls.enabled = false;
        });
        
        dragControls.addEventListener("dragend", () => {
          controls.enabled = true;
        });
        
        dragControls.addEventListener("drag", (event) => {
          const sensor = event.object as THREE.Mesh;
          if (sensor.userData.sensorType) {
            // Update rotation values in store when sensor is moved
            const euler = new THREE.Euler().setFromQuaternion(sensor.quaternion, "YXZ");
            const degX = Math.round(THREE.MathUtils.radToDeg(euler.x));
            const degY = Math.round(THREE.MathUtils.radToDeg(euler.y));
            const degZ = Math.round(THREE.MathUtils.radToDeg(euler.z));
            setRotationValues({ x: degX, y: degY, z: degZ });
          }
        });
        
        console.log("Skeleton and drag controls loaded successfully");
      },
      (xhr) => {
        if (xhr.total) {
          console.log("Loading skeleton:", (xhr.loaded / xhr.total * 100).toFixed(2) + "% loaded");
        }
      },
      (error) => {
        console.error("Failed to load skeleton, creating simple fallback:", error);
        // Create simple skeleton as fallback
        createSimpleSkeleton(scene);
      }
    );

    // Handle window resize
    const handleResize = () => {
      if (mountRef.current && camera && renderer) {
        camera.aspect = mountRef.current.clientWidth / mountRef.current.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
      }
    };

    window.addEventListener("resize", handleResize);

    // Mouse click handler for sensor placement with snapping
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
        
        // Get the surface normal for proper sensor orientation
        const normal = intersect.face?.normal.clone();
        if (normal) {
          // Transform normal to world space
          normal.transformDirection(intersect.object.matrixWorld);
        }
        
        // Use the intersection point directly (already in world space)
        const snapPoint = intersect.point.clone();
        
        // Offset the sensor slightly away from the surface
        if (normal) {
          snapPoint.add(normal.multiplyScalar(2)); // Move 2 units away from surface
        }
        
        // Convert to local coordinates for the skeleton
        const localPoint = snapPoint.clone();
        skeletonRef.current.worldToLocal(localPoint);

        placeSensor(selectedSensorType, localPoint, normal);
      }
    };

    renderer.domElement.addEventListener("click", onMouseClick);

    // Start animation
    animate();

    // Cleanup
    return () => {
      window.removeEventListener("resize", handleResize);
      renderer.domElement.removeEventListener("click", onMouseClick);
      if (mountRef.current && renderer.domElement && mountRef.current.contains(renderer.domElement)) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [isClient, selectedSensorType]);

  const placeSensor = (sensorType: string, position: THREE.Vector3, normal?: THREE.Vector3) => {
    if (!skeletonRef.current) return;

    // Calculate sensor size relative to skeleton
    const box = new THREE.Box3().setFromObject(skeletonRef.current);
    const size = box.getSize(new THREE.Vector3());
    const sensorWidth = size.x * 0.03;  // Slightly smaller for better fit
    const sensorHeight = size.y * 0.03;
    const sensorDepth = size.z * 0.03;

    let sensor = sensorTypesRef.current[sensorType];
    if (!sensor) {
      const geometry = new THREE.BoxGeometry(sensorWidth, sensorHeight, sensorDepth);
      const material = new THREE.MeshLambertMaterial({ 
        color: 0xff0000,
        transparent: true,
        opacity: 0.8
      });
      sensor = new THREE.Mesh(geometry, material);
      sensorTypesRef.current[sensorType] = sensor;
      sensor.userData = { sensorType, placementView: selectedView };
      skeletonRef.current.add(sensor);
      draggableSensorsRef.current.push(sensor);
      if (dragControlsRef.current) {
        dragControlsRef.current.objects = draggableSensorsRef.current;
      }
    }

    // Snap to surface position
    sensor.position.copy(position);
    
    // Orient sensor to surface normal if available
    if (normal) {
      // Create a rotation that aligns the sensor's up axis with the surface normal
      const up = new THREE.Vector3(0, 1, 0);
      const quaternion = new THREE.Quaternion().setFromUnitVectors(up, normal);
      sensor.quaternion.copy(quaternion);
    } else {
      applySensorRotation(sensor);
    }
    
    // Update store with placement info
    setSensorPlacement(sensorType, {
      type: sensorType,
      position: { x: position.x, y: position.y, z: position.z },
      rotation: rotationValues,
      placementView: selectedView
    });
    
    console.log(`Sensor ${sensorType} snapped to skeleton at position:`, position);
  };

  const snapSensorToSkeleton = (sensor: THREE.Mesh) => {
    if (!skeletonRef.current || !cameraRef.current) return;

    // Cast a ray downward from sensor position to find skeleton surface
    const sensorWorldPosition = new THREE.Vector3();
    sensor.getWorldPosition(sensorWorldPosition);
    
    const raycaster = new THREE.Raycaster();
    raycaster.set(sensorWorldPosition, new THREE.Vector3(0, -1, 0)); // Cast downward
    
    const intersects = raycaster.intersectObject(skeletonRef.current, true);
    
    if (intersects.length > 0) {
      const intersect = intersects[0];
      const snapPoint = intersect.point.clone();
      
      // Get surface normal for orientation
      const normal = intersect.face?.normal;
      if (normal) {
        // Offset sensor slightly from surface
        const worldNormal = normal.clone();
        worldNormal.transformDirection((intersect.object as THREE.Mesh).matrixWorld);
        snapPoint.add(worldNormal.multiplyScalar(3));
      }
      
      // Convert to local coordinates
      const localSnapPoint = snapPoint.clone();
      skeletonRef.current.worldToLocal(localSnapPoint);
      sensor.position.copy(localSnapPoint);
      
      console.log(`Sensor snapped to skeleton surface`);
    }
  };

  const applySensorRotation = (sensor: THREE.Mesh) => {
    if (!sensor) return;

    const getAxis = (letter: string): THREE.Vector3 => {
      switch (letter) {
        case "X": return new THREE.Vector3(1, 0, 0);
        case "Y": return new THREE.Vector3(0, 1, 0);
        case "Z": return new THREE.Vector3(0, 0, 1);
        default: return new THREE.Vector3(1, 0, 0);
      }
    };

    const upAxis = getAxis(axisMapping.up);
    const leftAxis = getAxis(axisMapping.left);
    const outAxis = getAxis(axisMapping.out);

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

  // Apply rotation when rotation values change
  useEffect(() => {
    if (selectedSensorType && sensorTypesRef.current[selectedSensorType]) {
      applySensorRotation(sensorTypesRef.current[selectedSensorType]);
    }
  }, [rotationValues, axisMapping, selectedSensorType]);

  // Show loading state until client-side rendering is ready
  if (!isClient) {
    return (
      <div className="w-full h-full relative bg-gray-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
          <p>Loading 3D Visualization...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative bg-gray-900">
      {/* 3D Visualization Container */}
      <div ref={mountRef} className="w-full h-full" />
      
      {/* Overlay Instructions */}
      <div className="absolute bottom-4 left-4 bg-black/70 text-white p-3 rounded text-sm">
        <p className="font-medium">3D Controls:</p>
        <p>• Mouse: Orbit camera</p>
        <p>• Wheel: Zoom in/out</p>
        <p>• Use sidebar to place sensors</p>
      </div>
    </div>
  );
} 