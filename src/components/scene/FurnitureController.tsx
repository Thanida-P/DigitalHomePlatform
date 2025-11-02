import * as React from "react";
import * as THREE from "three";
import { ThreeEvent, useThree, useFrame } from "@react-three/fiber";
import { useXR } from "@react-three/xr";
import { useGLTF } from "@react-three/drei";
import { PlacedItem } from "../types/Furniture";

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
  const modelRef = React.useRef<THREE.Group>(null);
  const xr = useXR();
  const camera = useThree((state) => state.camera);
  const isPresenting = !!xr.session;
  const [_modelHeight, setModelHeight] = React.useState(0);

  const { scene } = item.modelPath ? useGLTF(item.modelPath) : { scene: null };

  React.useEffect(() => {
    if (!modelRef.current || !scene) return;

    // Clone the scene
    const clonedScene = scene.clone();
    
    // Clear existing children
    modelRef.current.clear();
    
    // Calculate bounding box
    const box = new THREE.Box3().setFromObject(clonedScene);
    const minY = box.min.y;
    const height = box.max.y - box.min.y;
    
    setModelHeight(-minY);
    
    clonedScene.position.y = -minY;
    
    modelRef.current.add(clonedScene);
    
    console.log('🪑 Furniture aligned:', {
      name: item.name,
      originalMinY: minY,
      height,
      adjustment: -minY
    });
  }, [scene, item.modelPath]);

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
        const dx = gamepad.axes[2];
        const dy = gamepad.axes[3];
        if (typeof dx === 'number' && !isNaN(dx) && Math.abs(dx) > deadzone) moveVector.x = dx;
        if (typeof dy === 'number' && !isNaN(dy) && Math.abs(dy) > deadzone) moveVector.z = dy;

      } else if (inputSource.handedness === 'left') {
        const dr = gamepad.axes[2];
        if (typeof dr === 'number' && !isNaN(dr) && Math.abs(dr) > deadzone) {
          rotateDelta = -dr;
        }
      }
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
      deltaPosition.addScaledVector(forward, -moveVector.z * moveSpeed * delta);
      deltaPosition.addScaledVector(right, moveVector.x * moveSpeed * delta);

      const newPosition = new THREE.Vector3().fromArray(item.position);
      newPosition.add(deltaPosition);
      
      // Keep Y at 0 (floor level) since the model itself is already aligned
      onPositionChange([newPosition.x, 0, newPosition.z]);
    }

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
      <group ref={modelRef} />
      
      {isSelected && (
        <>
          <mesh position={[0, 0.01, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.3, 0.35, 32]} />
            <meshBasicMaterial color="#00ff00" transparent opacity={0.7} side={THREE.DoubleSide} />
          </mesh>
          <mesh position={[0, 0.01, 0.35]} rotation={[-Math.PI / 2, 0, 0]}>
            <coneGeometry args={[0.05, 0.1, 8]} />
            <meshBasicMaterial color="#ffff00" />
          </mesh>
        </>
      )}
    </group>
  );
}
 
export function PlacedFurniture({ items, selectedIndex, onSelectItem, onUpdatePosition, onUpdateRotation }: any) {
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

export function SpawnManager({ 
  spawnPositionRef 
}: { 
  spawnPositionRef: React.MutableRefObject<[number, number, number]>
}) {
  const camera = useThree((state) => state.camera);
  
  useFrame(() => {
    if (!camera) return;
    
    const cameraWorldPos = new THREE.Vector3();
    camera.getWorldPosition(cameraWorldPos);
    
    const cameraDirection = new THREE.Vector3();
    camera.getWorldDirection(cameraDirection);
    
    const spawnDistance = 2;
    const spawnPos = cameraWorldPos.clone();
    spawnPos.addScaledVector(cameraDirection, spawnDistance);
    
    spawnPos.y = 0;
    
    spawnPositionRef.current = [spawnPos.x, 0, spawnPos.z];
  });
  
  return null;
}