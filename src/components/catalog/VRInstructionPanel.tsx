import { Text } from "@react-three/drei";

export function VRInstructionPanel({ show }: { show: boolean }) {
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