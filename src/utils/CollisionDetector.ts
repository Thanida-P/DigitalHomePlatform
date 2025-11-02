import * as THREE from 'three';

/**
 * Collision Detection System for 3D Scene
 * Prevents furniture from overlapping with each other and the home model
 */

export interface CollisionBox {
  min: THREE.Vector3;
  max: THREE.Vector3;
  center: THREE.Vector3;
  size: THREE.Vector3;
}

export class CollisionDetector {
  private furnitureBoxes: Map<string, THREE.Box3> = new Map();
  private homeBox: THREE.Box3 | null = null;
  private collisionMargin: number = 0.1; // 10cm margin between objects

  /**
   * Set the bounding box for the home model
   */
  setHomeBoundingBox(homeObject: THREE.Object3D) {
    const box = new THREE.Box3().setFromObject(homeObject);
    this.homeBox = box;
    console.log('Home bounding box set:', box);
  }

  /**
   * Update furniture bounding box
   */
  updateFurnitureBoundingBox(
    itemId: string,
    position: THREE.Vector3,
    rotation: THREE.Euler,
    scale: number,
    modelSize?: THREE.Vector3
  ) {
    // Create a temporary object to calculate the bounding box
    const tempObject = new THREE.Object3D();
    tempObject.position.copy(position);
    tempObject.rotation.copy(rotation);
    tempObject.scale.setScalar(scale);

    // Use provided model size or default
    const size = modelSize || new THREE.Vector3(0.5, 0.5, 0.5);
    
    // Create a box geometry to represent the furniture
    const geometry = new THREE.BoxGeometry(size.x, size.y, size.z);
    const mesh = new THREE.Mesh(geometry);
    tempObject.add(mesh);
    tempObject.updateMatrixWorld(true);

    // Calculate bounding box
    const box = new THREE.Box3().setFromObject(tempObject);
    
    // Expand box by collision margin
    box.expandByScalar(this.collisionMargin);
    
    this.furnitureBoxes.set(itemId, box);
    
    // Cleanup
    geometry.dispose();
  }

  /**
   * Remove furniture bounding box
   */
  removeFurnitureBoundingBox(itemId: string) {
    this.furnitureBoxes.delete(itemId);
  }

  /**
   * Check if a position would cause collision
   */
  checkCollision(
    itemId: string,
    newPosition: THREE.Vector3,
    rotation: THREE.Euler,
    scale: number,
    modelSize?: THREE.Vector3
  ): { 
    hasCollision: boolean; 
    correctedPosition?: THREE.Vector3;
    collidingWith?: string;
  } {
    // Create temporary bounding box for the new position
    const tempObject = new THREE.Object3D();
    tempObject.position.copy(newPosition);
    tempObject.rotation.copy(rotation);
    tempObject.scale.setScalar(scale);

    const size = modelSize || new THREE.Vector3(0.5, 0.5, 0.5);
    const geometry = new THREE.BoxGeometry(size.x, size.y, size.z);
    const mesh = new THREE.Mesh(geometry);
    tempObject.add(mesh);
    tempObject.updateMatrixWorld(true);

    const testBox = new THREE.Box3().setFromObject(tempObject);
    testBox.expandByScalar(this.collisionMargin);

    geometry.dispose();

    // Check collision with home model
    if (this.homeBox && testBox.intersectsBox(this.homeBox)) {
      const corrected = this.resolveCollisionWithHome(testBox, newPosition);
      return { 
        hasCollision: true, 
        correctedPosition: corrected,
        collidingWith: 'home'
      };
    }

    // Check collision with other furniture
    for (const [otherId, otherBox] of this.furnitureBoxes.entries()) {
      if (otherId !== itemId && testBox.intersectsBox(otherBox)) {
        const corrected = this.resolveCollisionWithFurniture(
          testBox, 
          otherBox, 
          newPosition
        );
        return { 
          hasCollision: true, 
          correctedPosition: corrected,
          collidingWith: otherId
        };
      }
    }

    return { hasCollision: false };
  }

  /**
   * Resolve collision with home by pushing furniture outside
   */
  private resolveCollisionWithHome(
    furnitureBox: THREE.Box3,
    currentPosition: THREE.Vector3
  ): THREE.Vector3 {
    if (!this.homeBox) return currentPosition;

    const homeCenter = new THREE.Vector3();
    this.homeBox.getCenter(homeCenter);

    const furnitureCenter = new THREE.Vector3();
    furnitureBox.getCenter(furnitureCenter);

    // Calculate direction from home center to furniture
    const direction = new THREE.Vector3()
      .subVectors(furnitureCenter, homeCenter)
      .normalize();

    // Calculate how much to push
    const homeSize = new THREE.Vector3();
    this.homeBox.getSize(homeSize);

    const furnitureSize = new THREE.Vector3();
    furnitureBox.getSize(furnitureSize);

    // Push furniture outside home bounds
    const pushDistance = Math.max(
      homeSize.x / 2 + furnitureSize.x / 2,
      homeSize.z / 2 + furnitureSize.z / 2
    ) + this.collisionMargin * 2;

    const correctedPosition = homeCenter.clone()
      .add(direction.multiplyScalar(pushDistance));

    // Keep Y position unchanged (don't push up/down)
    correctedPosition.y = currentPosition.y;

    return correctedPosition;
  }

  /**
   * Resolve collision with another furniture piece
   */
  private resolveCollisionWithFurniture(
    movingBox: THREE.Box3,
    staticBox: THREE.Box3,
    currentPosition: THREE.Vector3
  ): THREE.Vector3 {
    const movingCenter = new THREE.Vector3();
    movingBox.getCenter(movingCenter);

    const staticCenter = new THREE.Vector3();
    staticBox.getCenter(staticCenter);

    // Calculate direction to push
    const direction = new THREE.Vector3()
      .subVectors(movingCenter, staticCenter);

    // Determine primary axis of separation (X or Z)
    const absX = Math.abs(direction.x);
    const absZ = Math.abs(direction.z);

    const movingSize = new THREE.Vector3();
    movingBox.getSize(movingSize);

    const staticSize = new THREE.Vector3();
    staticBox.getSize(staticSize);

    let correctedPosition = currentPosition.clone();

    if (absX > absZ) {
      // Push along X axis
      const pushDistance = (movingSize.x + staticSize.x) / 2 + this.collisionMargin;
      correctedPosition.x = staticCenter.x + Math.sign(direction.x) * pushDistance;
    } else {
      // Push along Z axis
      const pushDistance = (movingSize.z + staticSize.z) / 2 + this.collisionMargin;
      correctedPosition.z = staticCenter.z + Math.sign(direction.z) * pushDistance;
    }

    return correctedPosition;
  }

  /**
   * Get all current furniture positions for visualization
   */
  getFurnitureBoundingBoxes(): Map<string, CollisionBox> {
    const result = new Map<string, CollisionBox>();
    
    for (const [id, box] of this.furnitureBoxes.entries()) {
      const center = new THREE.Vector3();
      box.getCenter(center);
      
      const size = new THREE.Vector3();
      box.getSize(size);
      
      result.set(id, {
        min: box.min.clone(),
        max: box.max.clone(),
        center,
        size
      });
    }
    
    return result;
  }

  /**
   * Calculate model size from GLTF object
   */
  static calculateModelSize(object: THREE.Object3D): THREE.Vector3 {
    const box = new THREE.Box3().setFromObject(object);
    const size = new THREE.Vector3();
    box.getSize(size);
    return size;
  }

  /**
   * Visualize bounding boxes for debugging
   */
  createDebugHelpers(): THREE.Group {
    const group = new THREE.Group();
    group.name = 'collision-debug-helpers';

    // Visualize home box
    if (this.homeBox) {
      const homeSize = new THREE.Vector3();
      this.homeBox.getSize(homeSize);
      
      const homeCenter = new THREE.Vector3();
      this.homeBox.getCenter(homeCenter);
      
      const homeHelper = new THREE.BoxHelper(
        new THREE.Mesh(
          new THREE.BoxGeometry(homeSize.x, homeSize.y, homeSize.z)
        ),
        0xff0000 // Red for home
      );
      homeHelper.position.copy(homeCenter);
      group.add(homeHelper);
    }

    // Visualize furniture boxes
    for (const [id, box] of this.furnitureBoxes.entries()) {
      const size = new THREE.Vector3();
      box.getSize(size);
      
      const center = new THREE.Vector3();
      box.getCenter(center);
      
      const helper = new THREE.BoxHelper(
        new THREE.Mesh(
          new THREE.BoxGeometry(size.x, size.y, size.z)
        ),
        0x00ff00 // Green for furniture
      );
      helper.position.copy(center);
      group.add(helper);
    }

    return group;
  }

  /**
   * Clear all collision data
   */
  clear() {
    this.furnitureBoxes.clear();
    this.homeBox = null;
  }

  /**
   * Set collision margin (default 0.1)
   */
  setCollisionMargin(margin: number) {
    this.collisionMargin = margin;
  }
}

// Singleton instance
export const collisionDetector = new CollisionDetector();

/**
 * React Hook for using collision detection in components
 */
export function useCollisionDetection() {
  return collisionDetector;
}