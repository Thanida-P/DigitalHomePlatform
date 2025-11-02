export type Furniture = {
  id: string;
  name: string;
  description?: string;
  model_id: number;
  modelPath?: string;
  image?: string;
  category?: string;
  type?: string;
  is_container: boolean;
};

export type PlacedItem = Furniture & {
  position: [number, number, number];
  rotation?: [number, number, number];
  scale?: number;
};