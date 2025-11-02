import { useEffect, useState } from 'react';
import { Gltf, Text } from '@react-three/drei';
import { makeAuthenticatedRequest } from '../../utils/Auth';

export function HomeModel({ homeId }: { homeId: string }) {
  const [modelUrl, setModelUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadHomeModel = async () => {
      try {
        const response = await makeAuthenticatedRequest(`/digitalhomes/download_digital_home/${homeId}/`);
        
        if (response.ok) {
          const blob = await response.blob();
          const url = URL.createObjectURL(blob);
          setModelUrl(url);
        } else {
          console.error('Failed to load home model');
        }
      } catch (error) {
        console.error('Error loading home model:', error);
      } finally {
        setLoading(false);
      }
    };

    loadHomeModel();

    return () => {
      if (modelUrl) {
        URL.revokeObjectURL(modelUrl);
      }
    };
  }, [homeId]);

  if (loading) {
    return (
      <Text position={[0, 1, 0]} fontSize={0.2} color="white">
        Loading home model...
      </Text>
    );
  }

  if (!modelUrl) {
    return (
      <Text position={[0, 1, 0]} fontSize={0.2} color="red">
        Failed to load home model
      </Text>
    );
  }

  return <Gltf src={modelUrl} />;
}