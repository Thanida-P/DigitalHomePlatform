import * as React from "react";
import { useEffect } from "react";
import { Environment, PerspectiveCamera } from "@react-three/drei";
import { CatalogToggle } from "../panel/FurnitureCatalogToggle";
import { VRInstructionPanel } from "../panel/VRInstructionPanel";
import { VRFurniturePanel } from "../panel/FurniturePanel";
import { VRSlider } from "../panel/VRSlider";
import { HeadLockedUI } from "../panel/HeadLockedUI";
import { HomeModel } from "./HomeModel";
import { PlacedFurniture, SpawnManager } from "./FurnitureController";
import { Furniture, PlacedItem } from "../types/Furniture";
import { makeAuthenticatedRequest } from "../../utils/Auth";

export function SceneContent({ homeId }: { homeId: string }) {
  const [showSlider, setShowSlider] = React.useState(false);
  const [showFurniture, setShowFurniture] = React.useState(false);
  const [showInstructions, setShowInstructions] = React.useState(true);
  const [sliderValue, setSliderValue] = React.useState(0.5);
  const [rotationValue, setRotationValue] = React.useState(0);
  const [placedItems, setPlacedItems] = React.useState<PlacedItem[]>([]);
  const [selectedItemIndex, setSelectedItemIndex] = React.useState<number | null>(null);
  const currentSpawnPositionRef = React.useRef<[number, number, number]>([0, 0, -2]);
  
  const [furnitureCatalog, setFurnitureCatalog] = React.useState<Furniture[]>([]);
  const [catalogLoading, setCatalogLoading] = React.useState(false);
  const [modelUrlCache, setModelUrlCache] = React.useState<Map<number, string>>(new Map());

  useEffect(() => {
    const loadFurnitureCatalog = async () => {
      setCatalogLoading(true);
      try {
        const response = await makeAuthenticatedRequest('/digitalhomes/list_available_items/');
        
        if (response.ok) {
          const data = await response.json();
          console.log('📦 Loaded furniture catalog:', data.available_items);
          
          const items: Furniture[] = data.available_items.map((item: any) => ({
            id: item.id.toString(),
            name: item.name,
            description: item.description,
            model_id: item.model_id,
            image: item.image,
            category: item.category,
            type: item.type,
            is_container: item.is_container,
          }));
          
          setFurnitureCatalog(items);
          
          // Preload all furniture models
          items.forEach(item => {
            loadFurnitureModel(item.model_id);
          });
        } else {
          console.error('Failed to load furniture catalog');
        }
      } catch (error) {
        console.error('Error loading furniture catalog:', error);
      } finally {
        setCatalogLoading(false);
      }
    };

    loadFurnitureCatalog();

    // Cleanup all model URLs on unmount
    return () => {
      modelUrlCache.forEach(url => URL.revokeObjectURL(url));
    };
  }, []);

  const loadFurnitureModel = async (modelId: number) => {
    if (modelUrlCache.has(modelId)) return;

    try {
      const response = await makeAuthenticatedRequest(`/products/get_3d_model/${modelId}/`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        setModelUrlCache(prev => new Map(prev).set(modelId, url));
      } else {
        console.error(`Failed to load model ${modelId}`);
      }
    } catch (error) {
      console.error(`Error loading model ${modelId}:`, error);
    }
  };

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
    console.log("Spawning furniture:", f.name, "at:", currentSpawnPositionRef.current);
    
    const modelPath = modelUrlCache.get(f.model_id);
    if (!modelPath) {
      console.warn('Model not loaded yet for:', f.name);
      return;
    }

    const newItem: PlacedItem = {
      ...f,
      modelPath,
      position: [
        currentSpawnPositionRef.current[0], 
        currentSpawnPositionRef.current[1], 
        currentSpawnPositionRef.current[2]
      ],
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

    if (selectedItemIndex === index) {
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

  const handleScaleChange = (newScale: number) => {
    setSliderValue(newScale);
    if (selectedItemIndex !== null) {
      setPlacedItems((prev) => {
        const updated = [...prev];
        updated[selectedItemIndex] = { ...updated[selectedItemIndex], scale: newScale };
        return updated;
      });
    }
  };

  const handleRotationSliderChange = (newRotation: number) => {
    setRotationValue(newRotation);
    if (selectedItemIndex !== null) {
      setPlacedItems((prev) => {
        const updated = [...prev];
        updated[selectedItemIndex] = { 
          ...updated[selectedItemIndex], 
          rotation: [0, newRotation, 0] 
        };
        return updated;
      });
    }
  };

  return (
    <>
      <SpawnManager spawnPositionRef={currentSpawnPositionRef} />
      <color args={["#808080"]} attach="background" />
      <PerspectiveCamera makeDefault position={[0, 1.6, 2]} fov={75} />
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 5, 5]} intensity={1} />
      <Environment preset="warehouse" />

      <group position={[0, 0, 0]}>
        <HomeModel homeId={homeId} />
        <PlacedFurniture
          items={placedItems}
          selectedIndex={selectedItemIndex}
          onSelectItem={handleSelectItem}
          onUpdatePosition={handleUpdateItemPosition}
          onUpdateRotation={handleUpdateItemRotation}
        />
      </group>

      <CatalogToggle onToggle={handleToggleUI} />
      
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
        <VRFurniturePanel 
          show={showFurniture} 
          catalog={furnitureCatalog}
          loading={catalogLoading}
          onSelectItem={handleSelectFurniture} 
        />
      </HeadLockedUI>

      <HeadLockedUI 
        distance={1.0} 
        enabled={showSlider && selectedItemIndex !== null}
      >
        <group>
          <VRSlider
            show={showSlider && selectedItemIndex !== null} 
            value={sliderValue} 
            onChange={handleScaleChange} 
            label="Scale" 
            min={0.1} 
            max={2} 
            position={[0, -0.4, 0]} 
          />
          <VRSlider
            show={ null} 
            value={rotationValue} 
            onChange={handleRotationSliderChange} 
            label="Rotation" 
            min={0} 
            max={Math.PI * 2} 
            position={[0, -0.4, 0]} 
            showDegrees={true}
          />
        </group>
      </HeadLockedUI>
    </>
  );
}