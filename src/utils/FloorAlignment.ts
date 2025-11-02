// src/utils/floorAlignment.ts
import { useEffect } from 'react';
import * as THREE from 'three';

/**
 * Hook to automatically align a 3D model to the floor
 * This calculates the bounding box and adjusts the position so the bottom sits at y=0
 */
export function useFloorAlignment(
  modelRef: React.RefObject<THREE.Group | THREE.Object3D | null>,
  enabled = true
) {
  useEffect(() => {
    if (!enabled || !modelRef.current) return;

    // Wait a frame for the model to load
    const timer = setTimeout(() => {
      if (!modelRef.current) return;

      // Calculate the bounding box of the entire model
      const box = new THREE.Box3().setFromObject(modelRef.current);
      
      // Get the minimum Y value (bottom of the model)
      const minY = box.min.y;
      
      // Adjust the position so the bottom is at y=0
      modelRef.current.position.y -= minY;
      
      console.log('✅ Floor alignment applied:', {
        originalMinY: minY,
        newPositionY: modelRef.current.position.y
      });
    }, 100);

    return () => clearTimeout(timer);
  }, [enabled, modelRef]);
}

/**
 * Utility function to get the bottom Y position of any Object3D
 */
export function getBottomY(object: THREE.Object3D): number {
  const box = new THREE.Box3().setFromObject(object);
  return box.min.y;
}

/**
 * Utility function to align an object to y=0 floor
 * Returns the adjustment that was made
 */
export function alignToFloor(object: THREE.Object3D): number {
  const minY = getBottomY(object);
  object.position.y -= minY;
  return minY;
}

/**
 * Get the height of an object (from bottom to top)
 */
export function getObjectHeight(object: THREE.Object3D): number {
  const box = new THREE.Box3().setFromObject(object);
  return box.max.y - box.min.y;
}

/**
 * Get the bounding box dimensions of an object
 */
export function getObjectDimensions(object: THREE.Object3D): {
  width: number;
  height: number;
  depth: number;
} {
  const box = new THREE.Box3().setFromObject(object);
  const size = new THREE.Vector3();
  box.getSize(size);
  
  return {
    width: size.x,
    height: size.y,
    depth: size.z
  };
}