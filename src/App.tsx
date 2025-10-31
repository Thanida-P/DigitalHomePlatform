import React from "react";
import { Canvas, ThreeEvent, useFrame } from "@react-three/fiber";
import { Environment, Gltf, PerspectiveCamera, Text } from "@react-three/drei";
import { createXRStore, XR, useXRInputSourceState } from "@react-three/xr";
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

// Available furniture items
const FURNITURE_CATALOG: Furniture[] = [
  { id: "table1", name: "Lab Table", modelPath: "/target.glb" },
  { id: "chair1", name: "Lab Chair", modelPath: "/chair1.glb" },
  { id: "cabinet1", name: "Cabinet", modelPath: "/tv.glb" },
  { id: "equipment1", name: "Equipment", modelPath: "/target.glb" },
];

// VR Locomotion Component

interface VRLocomotionProps {
  rigRef: React.RefObject<THREE.Group>;
}

export function VRLocomotion({ rigRef }: VRLocomotionProps) {
  const leftInputSource = useXRInputSourceState("controller", "left");
  const rightInputSource = useXRInputSourceState("controller", "right");

  useFrame((state, delta) => {
    if (!rigRef.current) return;

    let moveX = 0;
    let moveZ = 0;
    let rotateY = 0;

    if (leftInputSource?.gamepad?.axes) {
      const axes = leftInputSource.gamepad.axes as unknown as number[];
      if (axes.length >= 2) {
        moveX = axes[0];
        moveZ = axes[1];
      }
    }

    if (rightInputSource?.gamepad?.axes) {
      const axes = rightInputSource.gamepad.axes as unknown as number[];
      if (axes.length >= 1) {
        rotateY = axes[0];
      }
    }

    const moveSpeed = 2.0; // units/sec
    const rotateSpeed = 1.5; // radians/sec

    // Movement
    if (Math.abs(moveX) > 0.1 || Math.abs(moveZ) > 0.1) {
      const camera = state.camera;

      const forward = new THREE.Vector3();
      camera.getWorldDirection(forward);
      forward.y = 0;
      forward.normalize();

      const right = new THREE.Vector3();
      right.crossVectors(forward, new THREE.Vector3(0, 1, 0)).normalize();

      const movement = new THREE.Vector3();
      movement.addScaledVector(right, moveX * moveSpeed * delta);
      movement.addScaledVector(forward, -moveZ * moveSpeed * delta);

      rigRef.current.position.add(movement);
    }

    // Rotation
    if (Math.abs(rotateY) > 0.1) {
      rigRef.current.rotation.y -= rotateY * rotateSpeed * delta;
    }
  });

  return null;
}

function DraggableFurniture({ 
  item, 
  isSelected,
  onSelect,
  onPositionChange 
}: { 
  item: PlacedItem; 
  isSelected: boolean;
  onSelect: () => void;
  onPositionChange: (newPosition: [number, number, number]) => void;
}) {
  const groupRef = React.useRef<THREE.Group>(null);
  const [isDragging, setIsDragging] = React.useState(false);
  const [dragPlane] = React.useState(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), 0));
  const [offset] = React.useState(() => new THREE.Vector3());

  const handlePointerDown = (event: ThreeEvent<PointerEvent>) => {
    event.stopPropagation();
    onSelect();
    setIsDragging(true);

    // Calculate offset between click point and object position
    if (groupRef.current && event.point) {
      const objectPosition = new THREE.Vector3();
      groupRef.current.getWorldPosition(objectPosition);
      
      // Set the drag plane at the object's Y position
      dragPlane.constant = -objectPosition.y;
      
      offset.copy(objectPosition).sub(event.point);
    }
  };

  const handlePointerMove = (event: ThreeEvent<PointerEvent>) => {
    if (!isDragging) return;
    event.stopPropagation();

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2(event.pointer.x, event.pointer.y);
    raycaster.setFromCamera(pointer, event.camera);

    const intersectPoint = new THREE.Vector3();
    if (raycaster.ray.intersectPlane(dragPlane, intersectPoint)) {
      intersectPoint.add(offset);
      onPositionChange([intersectPoint.x, item.position[1], intersectPoint.z]);
    }
  };

  const handlePointerUp = (event: ThreeEvent<PointerEvent>) => {
    if (isDragging) {
      event.stopPropagation();
      setIsDragging(false);
    }
  };

  return (
    <group
      ref={groupRef}
      position={item.position}
      rotation={item.rotation}
      scale={item.scale || 1}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
    >
      <Gltf src={item.modelPath} />
      
      {/* Selection indicator */}
      {isSelected && (
        <>
          <mesh position={[0, 0.5, 0]} rotation={[Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.3, 0.35, 32]} />
            <meshBasicMaterial color="#00ff00" transparent opacity={0.7} side={THREE.DoubleSide} />
          </mesh>
          {/* Rotation direction indicator */}
          <mesh position={[0, 0.5, 0.35]} rotation={[Math.PI / 2, 0, 0]}>
            <coneGeometry args={[0.05, 0.1, 8]} />
            <meshBasicMaterial color="#ffff00" />
          </mesh>
        </>
      )}
      
      {/* Hover/interaction helper - invisible box around furniture */}
      <mesh visible={false}>
        <boxGeometry args={[1, 2, 1]} />
      </mesh>
    </group>
  );
}

function PlacedFurniture({ 
  items, 
  selectedIndex,
  onSelectItem,
  onUpdatePosition 
}: { 
  items: PlacedItem[];
  selectedIndex: number | null;
  onSelectItem: (index: number) => void;
  onUpdatePosition: (index: number, position: [number, number, number]) => void;
}) {
  return (
    <>
      {items.map((item, index) => (
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

function VREditButton({ onClick, showSlider }: { onClick: () => void; showSlider: boolean; }) {
  const meshRef = React.useRef<THREE.Mesh>(null);

  return (
    <group position={[-1.5, 1.6, -1]}>
      <mesh
        ref={meshRef}
        onClick={onClick}
        onPointerDown={onClick}
      >
        <boxGeometry args={[0.3, 0.15, 0.05]} />
        <meshStandardMaterial color={showSlider ? "#ff6b6b" : "#4CAF50"} />
      </mesh>
      <Text
        position={[0, 0, 0.03]}
        fontSize={0.05}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {showSlider ? "Hide" : "Edit"}
      </Text>
    </group>
  );
}

function VRSlider(
  { show, value, onChange, label, min = 0, max = 1, position = [0, 1.6, -1.5], showDegrees = false }:
  { show: boolean; value: number; onChange: (value: number) => void; label: string; min?: number; 
    max?: number; position?: [number, number, number]; showDegrees?: boolean; }
  ) {
  const handleRef = React.useRef<THREE.Mesh | null>(null);
  const [isDragging, setIsDragging] = React.useState(false);

  if (!show) return null;

  const handleSliderInteraction = (event: ThreeEvent<MouseEvent> | ThreeEvent<PointerEvent>) => {
    if (event.point) {
      const localPoint = event.point;
      const normalizedX = (localPoint.x - position[0] + 0.4) / 0.8;
      const clampedX = Math.max(0, Math.min(1, normalizedX));
      const newValue = min + clampedX * (max - min);
      onChange(newValue);
    }
  };

  const sliderPosition = ((value - min) / (max - min)) * 0.8 - 0.4;
  
  // Display value in degrees if showDegrees is true
  const displayValue = showDegrees ? (value * 180 / Math.PI).toFixed(0) + "°" : value.toFixed(2);

  return (
    <group position={position}>
      {/* Background panel */}
      <mesh position={[0, 0, -0.01]}>
        <planeGeometry args={[1, 0.3]} />
        <meshStandardMaterial color="#2c3e50" opacity={0.9} transparent />
      </mesh>

      {/* Label */}
      <Text
        position={[0, 0.1, 0]}
        fontSize={0.04}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {label}: {displayValue}
      </Text>

      {/* Slider track */}
      <mesh position={[0, -0.05, 0]}>
        <boxGeometry args={[0.8, 0.02, 0.01]} />
        <meshStandardMaterial color="#34495e" />
      </mesh>

      {/* Slider handle */}
      <mesh 
        ref={handleRef}
        position={[sliderPosition, -0.05, 0.01]}
        onClick={(e) => handleSliderInteraction(e)}
        onPointerDown={(e) => {
          setIsDragging(true);
          handleSliderInteraction(e);
        }}
        onPointerUp={() => setIsDragging(false)}
        onPointerMove={(e) => {
          if (isDragging || e.buttons > 0) {
            handleSliderInteraction(e);
          }
        }}
      >
        <sphereGeometry args={[0.04, 16, 16]} />
        <meshStandardMaterial color="#3498db" />
      </mesh>
    </group>
  );
}

function VRFurniturePanel({ show, onSelectItem }: { show: boolean; onSelectItem: (furniture: Furniture) => void; }) {
  if (!show) return null;

  return (
    <group position={[0, 1.6, -1.5]}>
      {/* Panel background */}
      <mesh position={[0, 0, 0]}>
        <planeGeometry args={[1.5, 1]} />
        <meshStandardMaterial color="#2c3e50" opacity={0.9} transparent />
      </mesh>

      {/* Title */}
      <Text
        position={[0, 0.45, 0.01]}
        fontSize={0.06}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        Select Furniture
      </Text>
      
      {/* Furniture buttons */}
      {FURNITURE_CATALOG.map((furniture, index) => {
        const x = (index % 2) * 0.6 - 0.3;
        const y = Math.floor(index / 2) * -0.3 + 0.15;
        
        return (
          <group key={furniture.id} position={[x, y, 0.01]}>
            <mesh
              onClick={() => onSelectItem(furniture)}
              onPointerDown={() => onSelectItem(furniture)}
            >
              <boxGeometry args={[0.5, 0.2, 0.05]} />
              <meshStandardMaterial color="#3498db" />
            </mesh>
            <Text
              position={[0, 0, 0.03]}
              fontSize={0.04}
              color="white"
              anchorX="center"
              anchorY="middle"
            >
              {furniture.name}
            </Text>
          </group>
        );
      })}
    </group>
  );
}

export default function App() {
  const [showSlider, setShowSlider] = React.useState<boolean>(false);
  const [showFurniture, setShowFurniture] = React.useState<boolean>(false);
  const [sliderValue, setSliderValue] = React.useState<number>(0.5);
  const [rotationValue, setRotationValue] = React.useState<number>(0);
  const [placedItems, setPlacedItems] = React.useState<PlacedItem[]>([]);
  const [selectedItemIndex, setSelectedItemIndex] = React.useState<number | null>(null);
  const xrRig = React.useRef<THREE.Group>(null);

  const handleSelectFurniture = (furniture: Furniture) => {
    // Place furniture in front of the user at a default position
    const newItem: PlacedItem = {
      ...furniture,
      position: [0, 0, -2 - placedItems.length * 0.5],
      rotation: [0, 0, 0],
      scale: sliderValue, // Use slider value for scale
    };
    
    setPlacedItems([...placedItems, newItem]);
    setSelectedItemIndex(placedItems.length); // Select the newly added item
    setRotationValue(0); // Reset rotation for new item
    console.log(`Added ${furniture.name} to the room with scale ${sliderValue}`);
  };

  const handleUpdateItemPosition = (index: number, newPosition: [number, number, number]) => {
    setPlacedItems(prevItems => {
      const updatedItems = [...prevItems];
      updatedItems[index] = {
        ...updatedItems[index],
        position: newPosition,
      };
      return updatedItems;
    });
  };

  const handleSelectItem = (index: number) => {
    setSelectedItemIndex(index);
    // Update rotation slider to match selected item's rotation
    if (placedItems[index].rotation) {
      setRotationValue(placedItems[index].rotation![1]);
    }
  };

  const handleRotationChange = (newRotation: number) => {
    setRotationValue(newRotation);
    
    // Update the selected item's rotation
    if (selectedItemIndex !== null) {
      setPlacedItems(prevItems => {
        const updatedItems = [...prevItems];
        updatedItems[selectedItemIndex] = {
          ...updatedItems[selectedItemIndex],
          rotation: [0, newRotation, 0],
        };
        return updatedItems;
      });
    }
  };

  return (
    <>
      <Canvas
        style={{
          width: "100vw",
          height: "100vh",
          position: "fixed",
        }}
      >
        <color args={["#808080"]} attach="background" />
        <PerspectiveCamera makeDefault position={[0, 1.6, 2]} fov={75} />
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 5, 5]} intensity={1} />
        <Environment preset="warehouse" />
        
        <Gltf src="/labPlan.glb" />
        
        <XR store={xrStore}>
          <group ref={xrRig}>
            <VRLocomotion rigRef={xrRig} />
            <VREditButton 
              onClick={() => {
                setShowSlider(!showSlider);
                setShowFurniture(!showFurniture);
              }} 
              showSlider={showSlider}
            />
            <VRSlider
              show={showSlider}
              value={sliderValue}
              onChange={setSliderValue}
              label="Furniture Scale"
              min={0.1}
              max={2}
              position={[-1.5, 1.2, -1]}
            />
            <VRSlider
              show={showSlider && selectedItemIndex !== null}
              value={rotationValue}
              onChange={handleRotationChange}
              label="Rotation"
              min={0}
              max={Math.PI * 2}
              position={[-1.5, 0.8, -1]}
              showDegrees={true}
            />
            <VRFurniturePanel 
              show={showFurniture} 
              onSelectItem={handleSelectFurniture}
            />
          </group>
        </XR>
        
        <PlacedFurniture 
          items={placedItems}
          selectedIndex={selectedItemIndex}
          onSelectItem={handleSelectItem}
          onUpdatePosition={handleUpdateItemPosition}
        />
      </Canvas>
      
      <div
        style={{
          position: "fixed",
          display: "flex",
          width: "100vw",
          height: "100vh",
          flexDirection: "column",
          justifyContent: "space-between",
          alignItems: "center",
          color: "white",
          pointerEvents: "none",
        }}
      >
        <button
          style={{
            position: "fixed",
            bottom: "20px",
            left: "50%",
            transform: "translateX(-50%)",
            fontSize: "20px",
            pointerEvents: "auto",
            padding: "12px 24px",
            backgroundColor: "#4CAF50",
            color: "white",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
          }}
          onClick={() => {
            xrStore.enterVR();
          }}
        >
          Enter VR
        </button>
      </div>
    </>
  );
}