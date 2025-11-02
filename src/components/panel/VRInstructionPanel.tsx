import { Text } from "@react-three/drei";

export function VRInstructionPanel({ show }: { show: boolean }) {
  if (!show) return null;
  return (
    <group>
      <mesh>
        <planeGeometry args={[1.8, 1.4]} />
        <meshStandardMaterial color="#2c3e50" opacity={0.9} transparent />
      </mesh>
      <Text position={[0, 0.6, 0.01]} fontSize={0.06} color="#4CAF50" anchorX="center" anchorY="middle">
        VR Controls
      </Text>
      <Text position={[0, 0.45, 0.01]} fontSize={0.04} color="white" anchorX="center" anchorY="middle">
        Press Y or B to toggle furniture menu
      </Text>
      <Text position={[0, 0.32, 0.01]} fontSize={0.04} color="white" anchorX="center" anchorY="middle">
        Press X or A to toggle control panel
      </Text>
      <Text position={[0, 0.16, 0.01]} fontSize={0.035} color="#ccc" anchorX="center" anchorY="middle">
        Trigger: Select furniture
      </Text>
      <Text position={[0, 0.06, 0.01]} fontSize={0.035} color="#ccc" anchorX="center" anchorY="middle">
        Right Thumbstick: Move selected item
      </Text>
      <Text position={[0, -0.04, 0.01]} fontSize={0.035} color="#ccc" anchorX="center" anchorY="middle">
        Left Thumbstick: Rotate selected item
      </Text>
      <Text position={[0, -0.14, 0.01]} fontSize={0.035} color="#ccc" anchorX="center" anchorY="middle">
        Use sliders to adjust scale & rotation
      </Text>
      <Text position={[0, -0.28, 0.01]} fontSize={0.032} color="#fbbf24" anchorX="center" anchorY="middle">
        Control Panel: Save, Back to Home, Logout
      </Text>
    </group>
  );
}