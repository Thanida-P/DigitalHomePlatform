import React from "react";
import { Canvas, ThreeEvent, useThree, useFrame } from "@react-three/fiber";
import { Environment, Gltf, PerspectiveCamera, Text } from "@react-three/drei";
import { createXRStore, XR, useXR } from "@react-three/xr";

import * as THREE from "three";

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

// furniture items
const FURNITURE_CATALOG: Furniture[] = [
  { id: "table1", name: "Lab Table", modelPath: "/target.glb" },
  { id: "chair1", name: "Lab Chair", modelPath: "/chair1.glb" },
  { id: "cabinet1", name: "Cabinet", modelPath: "/tv.glb" },
  { id: "equipment1", name: "Equipment", modelPath: "/target.glb" },
];

function ControllerUIToggle({ onToggle }: { onToggle: () => void }) {
  const xr = useXR();
  const prevButtonStateRef = React.useRef<Map<string, boolean>>(new Map());

  useFrame(() => {
    const session = xr.session;
    if (!session || !session.inputSources) return;

    session.inputSources.forEach((inputSource, controllerIndex: number) => {
      const gamepad = inputSource.gamepad;
      if (!gamepad || !gamepad.buttons) return;

      const buttonIndexes = [4, 5]; // Y and B
      buttonIndexes.forEach((buttonIndex) => {
        const button = gamepad.buttons[buttonIndex];
        if (!button) return;

        const isPressed = button.pressed;
        const key = `${controllerIndex}-${buttonIndex}`;
        const wasPressed = prevButtonStateRef.current.get(key) || false;

        if (isPressed && !wasPressed) {
          onToggle();
        }

        prevButtonStateRef.current.set(key, isPressed);
      });
    });
  });

  return null;
}

/* ──────────────────────────────────────────────
   DraggableFurniture — adds null safety & useXRFrame
────────────────────────────────────────────── */
function DraggableFurniture({
  item,
  isSelected,
  onSelect,
  onPositionChange,
}: {
  item: PlacedItem;
  isSelected: boolean;
  onSelect: () => void;
  onPositionChange: (newPosition: [number, number, number]) => void;
}) {
  const groupRef = React.useRef<THREE.Group>(null);
  const xr = useXR();
  const camera = useThree((state) => state.camera);

  useFrame((frame) => {
    if (!isSelected || !groupRef.current || !frame) return;

    const session = xr.session;
    const referenceSpace = xr.originReferenceSpace;
    if (!session || !referenceSpace) return;

    const inputSources = session.inputSources;
    if (!inputSources || inputSources.length === 0) return;

    const moveSpeed = 1.5;
    const deadzone = 0.1;
    const moveVector = new THREE.Vector3(0, 0, 0);

    for (const inputSource of inputSources) {
      const gamepad = inputSource.gamepad;
      if (!gamepad || gamepad.axes.length < 4) continue;

      const dx = gamepad.axes[2];
      const dy = gamepad.axes[3];

      if (Math.abs(dx) > deadzone) moveVector.x = dx;
      if (Math.abs(dy) > deadzone) moveVector.z = dy;
      if (moveVector.length() > deadzone) break;
    }

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
      deltaPosition.addScaledVector(forward, -moveVector.z * moveSpeed * (1 / 60));
      deltaPosition.addScaledVector(right, moveVector.x * moveSpeed * (1 / 60));

      const newPosition = new THREE.Vector3().fromArray(item.position);
      newPosition.add(deltaPosition);
      onPositionChange([newPosition.x, item.position[1], newPosition.z]);
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

function PlacedFurniture({ items, selectedIndex, onSelectItem, onUpdatePosition }: any) {
  return (
    <>
      {items.map((item: PlacedItem, index: number) => (
        <DraggableFurniture
          key={`${item.id}-${index}`}
          item={item}
          isSelected={selectedIndex === index}
          onSelect={() => onSelectItem(index)}
          onPositionChange={(newPosition) => onUpdatePosition(index, newPosition)}
        />
      ))}
    </>
  );
}

function VRSlider({ show, value, onChange, label, min = 0, max = 1, position = [0, 1.6, -1.5], showDegrees = false }: any) {
  const [isDragging, setIsDragging] = React.useState(false);
  const trackRef = React.useRef<THREE.Mesh>(null);
  if (!show) return null;

  const handleSliderInteraction = (e: ThreeEvent<PointerEvent>) => {
    if (!trackRef.current || !e.point) return;
    const trackMatrix = trackRef.current.matrixWorld;
    const inverseTrackMatrix = new THREE.Matrix4().copy(trackMatrix).invert();
    const localPoint = e.point.clone().applyMatrix4(inverseTrackMatrix);
    const normalizedX = (localPoint.x + 0.4) / 0.8;
    const clampedX = Math.max(0, Math.min(1, normalizedX));
    const newValue = min + clampedX * (max - min);
    onChange(newValue);
  };

  const sliderPosition = ((value - min) / (max - min)) * 0.8 - 0.4;
  const displayValue = showDegrees ? ((value * 180) / Math.PI).toFixed(0) + "°" : value.toFixed(2);

  return (
    <group position={position}>
      <mesh position={[0, 0, -0.01]}>
        <planeGeometry args={[1, 0.3]} />
        <meshStandardMaterial color="#2c3e50" opacity={0.9} transparent />
      </mesh>

      <Text position={[0, 0.1, 0]} fontSize={0.04} color="white" anchorX="center" anchorY="middle">
        {label}: {displayValue}
      </Text>

      <mesh
        ref={trackRef}
        position={[0, -0.05, 0]}
        onPointerDown={(e) => {
          e.stopPropagation();
          setIsDragging(true);
          handleSliderInteraction(e);
        }}
        onPointerUp={() => setIsDragging(false)}
        onPointerMove={(e) => {
          if (isDragging) {
            e.stopPropagation();
            handleSliderInteraction(e);
          }
        }}
        onPointerLeave={() => setIsDragging(false)}
      >
        <boxGeometry args={[0.8, 0.02, 0.01]} />
        <meshStandardMaterial color="#34495e" />
      </mesh>

      <mesh position={[sliderPosition, -0.05, 0.01]}>
        <sphereGeometry args={[0.04, 16, 16]} />
        <meshStandardMaterial color="#3498db" />
      </mesh>
    </group>
  );
}

function VRFurniturePanel({ show, onSelectItem }: { show: boolean; onSelectItem: (f: Furniture) => void }) {
  if (!show) return null;
  return (
    <group position={[0, 1.6, -1.5]}>
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

function VRInstructionPanel({ show }: { show: boolean }) {
  if (!show) return null;
  return (
    <group position={[0, 1.6, -1.5]}>
      <mesh>
        <planeGeometry args={[1.8, 1.2]} />
        <meshStandardMaterial color="#2c3e50" opacity={0.9} transparent />
      </mesh>
      <Text position={[0, 0.5, 0.01]} fontSize={0.06} color="#4CAF50" anchorX="center" anchorY="middle">
        VR Controls
      </Text>
      <Text position={[0, 0.35, 0.01]} fontSize={0.04} color="white" anchorX="center" anchorY="middle">
        Press Y or B to toggle menu
      </Text>
      <Text position={[0, 0.2, 0.01]} fontSize={0.035} color="#ccc" anchorX="center" anchorY="middle">
        Trigger: Select furniture
      </Text>
      <Text position={[0, 0.1, 0.01]} fontSize={0.035} color="#ccc" anchorX="center" anchorY="middle">
        Thumbstick: Move selected item
      </Text>
      <Text position={[0, -0.05, 0.01]} fontSize={0.035} color="#ccc" anchorX="center" anchorY="middle">
        Use sliders to adjust scale/rotation
      </Text>
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
    const newItem: PlacedItem = {
      ...f,
      position: [0, 0, -2 - placedItems.length * 0.5],
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

  const handleSelectItem = (index: number) => {
    setSelectedItemIndex(index);
    if (placedItems[index]?.rotation) setRotationValue(placedItems[index].rotation![1]);
  };

  const handleRotationChange = (r: number) => {
    setRotationValue(r);
    if (selectedItemIndex !== null) {
      setPlacedItems((prev) => {
        const updated = [...prev];
        updated[selectedItemIndex] = { ...updated[selectedItemIndex], rotation: [0, r, 0] };
        return updated;
      });
    }
  };

  return (
    <>
      <Canvas style={{ width: "100vw", height: "100vh", position: "fixed" }}>
        <XR store={xrStore}>
          <color args={["#808080"]} attach="background" />
          <PerspectiveCamera makeDefault position={[0, 1.6, 2]} fov={75} />
          <ambientLight intensity={0.5} />
          <directionalLight position={[5, 5, 5]} intensity={1} />
          <Environment preset="warehouse" />

          <group position={[0, 0, -5]}>
            <Gltf src="/labPlan.glb" />
            <PlacedFurniture
              items={placedItems}
              selectedIndex={selectedItemIndex}
              onSelectItem={handleSelectItem}
              onUpdatePosition={handleUpdateItemPosition}
            />
          </group>

          <ControllerUIToggle onToggle={handleToggleUI} />
          <VRInstructionPanel show={showInstructions} />
          <VRSlider show={showSlider} value={sliderValue} onChange={setSliderValue} label="Scale" min={0.1} max={2} position={[-1.5, 1.2, -1]} />
          <VRSlider show={showSlider && selectedItemIndex !== null} value={rotationValue} onChange={handleRotationChange} label="Rotation" min={0} max={Math.PI * 2} position={[-1.5, 0.8, -1]} showDegrees />
          <VRFurniturePanel show={showFurniture} onSelectItem={handleSelectFurniture} />
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
