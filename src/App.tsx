import React from "react";
import * as THREE from "three";
import { Canvas, ThreeEvent, useThree, useFrame } from "@react-three/fiber";
import { Environment, Gltf, PerspectiveCamera, Text } from "@react-three/drei";
import { createXRStore, XR, useXR } from "@react-three/xr";
import { ControllerUIToggle } from "./components/ControllerUIToggle";
import { VRInstructionPanel } from "./components/VRInstructionPanel";
import { VRSlider } from "./components/RotationControl";
import { HeadLockedUI } from "./components/HeadLockedUI";

const xrStore = createXRStore();

type Furniture = {
  id: string;
  name?: string;
  modelPath: string;
};

type PlacedItem = Furniture & {
  position: [number, number, number];
  rotation?: [number, number, number];
  scale?: number;
};

const FURNITURE_CATALOG: Furniture[] = [
  { id: "table1", name: "Lab Table", modelPath: "/target.glb" },
  { id: "chair1", name: "Lab Chair", modelPath: "/chair1.glb" },
  { id: "cabinet1", name: "Cabinet", modelPath: "/tv.glb" },
  { id: "equipment1", name: "Equipment", modelPath: "/target.glb" },
];

function SpawnManager({ 
  spawnPositionRef 
}: { 
  spawnPositionRef: React.MutableRefObject<[number, number, number]>
}) {
  const camera = useThree((state) => state.camera);
  
  useFrame(() => {
    if (!camera) return;
    
    // Continuously update the spawn position based on camera
    const cameraWorldPos = new THREE.Vector3();
    camera.getWorldPosition(cameraWorldPos);
    
    const cameraDirection = new THREE.Vector3();
    camera.getWorldDirection(cameraDirection);
    
    const spawnDistance = 2;
    const spawnPos = cameraWorldPos.clone();
    spawnPos.addScaledVector(cameraDirection, spawnDistance);
    spawnPos.y = 0; // Floor level
    
    spawnPositionRef.current = [spawnPos.x, spawnPos.y, spawnPos.z];
  });
  
  return null;
}

function DraggableFurniture({
  item,
  isSelected,
  onSelect,
  onPositionChange,
  onRotationChange,
}: {
  item: PlacedItem;
  isSelected: boolean;
  onSelect: () => void;
  onPositionChange: (newPosition: [number, number, number]) => void;
  onRotationChange: (newRotation: [number, number, number]) => void;
}) {
  const groupRef = React.useRef<THREE.Group>(null);
  const xr = useXR();
  const camera = useThree((state) => state.camera);
  const isPresenting = !!xr.session;

  useFrame((_state, delta) => {
    if (!isSelected || !groupRef.current || !isPresenting) return; 

    const session = xr.session;
    const referenceSpace = xr.originReferenceSpace;
    if (!session || !referenceSpace) return;

    const inputSources = session.inputSources;
    if (!inputSources || inputSources.length === 0) return;

    const moveSpeed = 1.5;
    const rotateSpeed = 1.5; 
    const deadzone = 0.1;
    const moveVector = new THREE.Vector3(0, 0, 0);
    let rotateDelta = 0;

    for (const inputSource of inputSources) {
      const gamepad = inputSource.gamepad;
      if (!gamepad || gamepad.axes.length < 4) continue;

      if (inputSource.handedness === 'right') {
        // RIGHT STICK for Movement
        const dx = gamepad.axes[2];
        const dy = gamepad.axes[3];
        if (typeof dx === 'number' && !isNaN(dx) && Math.abs(dx) > deadzone) moveVector.x = dx;
        if (typeof dy === 'number' && !isNaN(dy) && Math.abs(dy) > deadzone) moveVector.z = dy;

      } else if (inputSource.handedness === 'left') {
        // LEFT STICK for Rotation (X-axis)
        const dr = gamepad.axes[2];
        if (typeof dr === 'number' && !isNaN(dr) && Math.abs(dr) > deadzone) {
          rotateDelta = -dr;
        }
      }
    }

    // Handle position change
    if (moveVector.length() > deadzone) {
      const forward = new THREE.Vector3();
      camera.getWorldDirection(forward);
      forward.y = 0;
      forward.normalize();

      const right = new THREE.Vector3();
      right.setFromMatrixColumn(camera.matrixWorld, 0);
      right.y = 0;
      right.normalize();

      const deltaPosition = new THREE.Vector3();
      deltaPosition.addScaledVector(forward, -moveVector.z * moveSpeed * delta);
      deltaPosition.addScaledVector(right, moveVector.x * moveSpeed * delta);

      const newPosition = new THREE.Vector3().fromArray(item.position);
      newPosition.add(deltaPosition);
      onPositionChange([newPosition.x, item.position[1], newPosition.z]);
    }

    // Handle rotation change 
    if (Math.abs(rotateDelta) > deadzone) {
      const deltaRotation = rotateDelta * rotateSpeed * delta;

      const currentRotationY = (item.rotation && typeof item.rotation[1] === 'number' && !isNaN(item.rotation[1])) ? item.rotation[1] : 0;
      
      const newRotationY = currentRotationY + deltaRotation;
      onRotationChange([0, newRotationY, 0]);
    }
  });


  const handleSelect = (e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation();
    onSelect();
  };

  return (
    <group
      ref={groupRef}
      position={item.position}
      rotation={item.rotation}
      scale={item.scale || 1}
      onPointerDown={handleSelect}
    >
      <Gltf src={item.modelPath} />
      {isSelected && (
        <>
          <mesh position={[0, 0.01, 0]} rotation={[Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.3, 0.35, 32]} />
            <meshBasicMaterial color="#00ff00" transparent opacity={0.7} side={THREE.DoubleSide} />
          </mesh>
          <mesh position={[0, 0.01, 0.35]} rotation={[Math.PI / 2, 0, 0]}>
            <coneGeometry args={[0.05, 0.1, 8]} />
            <meshBasicMaterial color="#ffff00" />
          </mesh>
        </>
      )}
    </group>
  );
}

function PlacedFurniture({ items, selectedIndex, onSelectItem, onUpdatePosition, onUpdateRotation }: any) {
  return (
    <>
      {items.map((item: PlacedItem, index: number) => (
        <DraggableFurniture
          key={`${item.id}-${index}`}
          item={item}
          isSelected={selectedIndex === index}
          onSelect={() => onSelectItem(index)}
          onPositionChange={(newPosition) => onUpdatePosition(index, newPosition)}
          onRotationChange={(newRotation) => onUpdateRotation(index, newRotation)}
        />
      ))}
    </>
  );
}

function VRFurniturePanel({ show, onSelectItem }: { show: boolean; onSelectItem: (f: Furniture) => void }) {
  if (!show) return null;
  return (
    <group>
      <mesh>
        <planeGeometry args={[1.5, 1]} />
        <meshStandardMaterial color="#2c3e50" opacity={0.9} transparent />
      </mesh>
      <Text position={[0, 0.45, 0.01]} fontSize={0.06} color="white" anchorX="center" anchorY="middle">
        Select Furniture
      </Text>
      {FURNITURE_CATALOG.map((f, i) => {
        const x = (i % 2) * 0.6 - 0.3;
        const y = Math.floor(i / 2) * -0.3 + 0.15;
        return (
          <group key={f.id} position={[x, y, 0.01]}>
            <mesh onPointerDown={(e) => { e.stopPropagation(); onSelectItem(f); }}>
              <boxGeometry args={[0.5, 0.2, 0.05]} />
              <meshStandardMaterial color="#3498db" />
            </mesh>
            <Text position={[0, 0, 0.03]} fontSize={0.04} color="white" anchorX="center" anchorY="middle">
              {f.name}
            </Text>
          </group>
        );
      })}
    </group>
  );
}

export default function App() {
  const [showSlider, setShowSlider] = React.useState(false);
  const [showFurniture, setShowFurniture] = React.useState(false);
  const [showInstructions, setShowInstructions] = React.useState(true);
  const [sliderValue, setSliderValue] = React.useState(0.5);
  const [rotationValue, setRotationValue] = React.useState(0);
  const [placedItems, setPlacedItems] = React.useState<PlacedItem[]>([]);
  const [selectedItemIndex, setSelectedItemIndex] = React.useState<number | null>(null);
  const currentSpawnPositionRef = React.useRef<[number, number, number]>([0, 0, -2]);

  const handleToggleUI = () => {
    if (showInstructions) {
      setShowInstructions(false);
      setShowFurniture(true);
      setShowSlider(true);
    } else if (showFurniture) {
      setShowFurniture(false);
      setShowSlider(false);
    } else {
      setShowFurniture(true);
      setShowSlider(true);
    }
  };

  const handleSelectFurniture = (f: Furniture) => {
    console.log("Spawning furniture at:", currentSpawnPositionRef.current);
    const newItem: PlacedItem = {
      ...f,
      position: [currentSpawnPositionRef.current[0], currentSpawnPositionRef.current[1], currentSpawnPositionRef.current[2]],
      rotation: [0, 0, 0],
      scale: sliderValue,
    };
    setPlacedItems([...placedItems, newItem]);
    setSelectedItemIndex(placedItems.length);
    setRotationValue(0);
  };

  const handleUpdateItemPosition = (index: number, newPosition: [number, number, number]) => {
    setPlacedItems((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], position: newPosition };
      return updated;
    });
  };

  const handleUpdateItemRotation = (index: number, newRotation: [number, number, number]) => {
    setPlacedItems((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], rotation: newRotation };
      return updated;
    });

    // Keep slider in sync if the selected item is being rotated
    if (selectedItemIndex === index) {
      // We normalize the rotation to keep the slider value within 0 to 2*PI
      const twoPi = Math.PI * 2;
      let normalizedRotation = newRotation[1] % twoPi;
      if (normalizedRotation < 0) {
        normalizedRotation += twoPi;
      }
      setRotationValue(normalizedRotation);
    }
  };


  const handleSelectItem = (index: number) => {
    setSelectedItemIndex(index);
    if (placedItems[index]?.rotation) {
      const twoPi = Math.PI * 2;
      let normalizedRotation = placedItems[index].rotation![1] % twoPi;
      if (normalizedRotation < 0) {
        normalizedRotation += twoPi;
      }
      setRotationValue(normalizedRotation);
    } else {
      setRotationValue(0);
    }
  };

  return (
    <>
      <Canvas style={{ width: "100vw", height: "100vh", position: "fixed" }}>
        <XR store={xrStore}>
          <SpawnManager spawnPositionRef={currentSpawnPositionRef} />
          <color args={["#808080"]} attach="background" />
          <PerspectiveCamera makeDefault position={[0, 1.6, 2]} fov={75} />
          <ambientLight intensity={0.5} />
          <directionalLight position={[5, 5, 5]} intensity={1} />
          <Environment preset="warehouse" />

          <group position={[0, 0, 0]}>
            <Gltf src="/labPlan.glb" />
            <PlacedFurniture
              items={placedItems}
              selectedIndex={selectedItemIndex}
              onSelectItem={handleSelectItem}
              onUpdatePosition={handleUpdateItemPosition}
              onUpdateRotation={handleUpdateItemRotation}
            />
          </group>

          <ControllerUIToggle onToggle={handleToggleUI} />
          
          <HeadLockedUI 
            distance={1.5} 
            verticalOffset={0} 
            enabled={showInstructions}
          >
            <VRInstructionPanel show={showInstructions} />
          </HeadLockedUI>

          <HeadLockedUI 
            distance={1.5} 
            verticalOffset={0} 
            enabled={showFurniture}
          >
            <VRFurniturePanel show={showFurniture} onSelectItem={handleSelectFurniture} />
          </HeadLockedUI>

          <HeadLockedUI 
            distance={1.0} 
            verticalOffset={0}
            enabled={showSlider}
          >
            <VRSlider 
              show={showSlider} 
              value={sliderValue} 
              onChange={setSliderValue} 
              label="Scale" 
              min={0.1} 
              max={2} 
              position={[0, -0.5, 0]} 
            />
          </HeadLockedUI>
        </XR>
      </Canvas>

      <div style={{ position: "fixed", width: "100vw", height: "100vh", display: "flex", justifyContent: "center", alignItems: "flex-end", pointerEvents: "none" }}>
        <button
          style={{ marginBottom: 20, padding: "12px 24px", backgroundColor: "#4CAF50", color: "white", border: "none", borderRadius: 8, cursor: "pointer", pointerEvents: "auto" }}
          onClick={() => {
            xrStore.enterVR().catch((err) => console.warn("Failed to enter VR:", err));
          }}
        >
          Enter VR
        </button>
      </div>
    </>
  );
}