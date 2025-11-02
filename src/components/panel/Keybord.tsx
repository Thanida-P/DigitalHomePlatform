import * as React from "react";
import { Text } from "@react-three/drei";

interface VRKeyboardProps {
  show: boolean;
  onType: (text: string) => void;
  currentText: string;
  position?: [number, number, number];
}

export function VRKeyboard({ 
  show, 
  onType, 
  currentText,
  position = [0, -0.5, 0] 
}: VRKeyboardProps) {
  const [shift, setShift] = React.useState(false);
  const [hoveredKey, setHoveredKey] = React.useState<string | null>(null);

  if (!show) return null;

  const rows = [
    ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
    ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
    ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
    ['z', 'x', 'c', 'v', 'b', 'n', 'm']
  ];

  const handleKeyPress = (key: string) => {
    if (key === 'BACK') {
      onType(currentText.slice(0, -1));
    } else if (key === 'SPACE') {
      onType(currentText + ' ');
    } else if (key === 'SHIFT') {
      setShift(!shift);
    } else if (key === 'CLEAR') {
      onType('');
    } else {
      const char = shift ? key.toUpperCase() : key;
      onType(currentText + char);
      setShift(false);
    }
  };

  const KeyButton = ({ 
    char, 
    x, 
    y, 
    width = 0.08, 
    special = false 
  }: { 
    char: string; 
    x: number; 
    y: number; 
    width?: number; 
    special?: boolean;
  }) => {
    const isHovered = hoveredKey === `${char}-${x}-${y}`;
    const displayChar = special ? char : (shift ? char.toUpperCase() : char);

    return (
      <group position={[x, y, 0]}>
        <mesh
          onPointerDown={(e) => {
            e.stopPropagation();
            handleKeyPress(char);
          }}
          onPointerEnter={() => setHoveredKey(`${char}-${x}-${y}`)}
          onPointerLeave={() => setHoveredKey(null)}
        >
          <planeGeometry args={[width, 0.08]} />
          <meshStandardMaterial 
            color={isHovered ? "#3b82f6" : (special ? "#475569" : "#334155")}
            emissive={isHovered ? "#1e40af" : "#000000"}
            emissiveIntensity={isHovered ? 0.5 : 0}
          />
        </mesh>
        <Text 
          position={[0, 0, 0.01]} 
          fontSize={special ? 0.03 : 0.04} 
          color="white" 
          anchorX="center" 
          anchorY="middle"
        >
          {displayChar}
        </Text>
      </group>
    );
  };

  return (
    <group position={position}>
      {/* Background panel */}
      <mesh position={[0, 0, -0.01]}>
        <planeGeometry args={[1.0, 0.55]} />
        <meshStandardMaterial color="#0f172a" opacity={0.95} transparent />
      </mesh>

      {/* Display current text */}
      <group position={[0, 0.22, 0.01]}>
        <mesh>
          <planeGeometry args={[0.9, 0.08]} />
          <meshStandardMaterial color="#1e293b" />
        </mesh>
        <Text 
          position={[-0.42, 0, 0.01]} 
          fontSize={0.04} 
          color="#e2e8f0" 
          anchorX="left" 
          anchorY="middle"
          maxWidth={0.85}
        >
          {currentText || "Type to search..."}
        </Text>
      </group>

      {/* Keyboard rows */}
      {rows.map((row, rowIdx) => {
        const rowWidth = row.length * 0.09;
        const startX = -rowWidth / 2 + 0.045;
        const y = 0.10 - rowIdx * 0.10;

        return (
          <group key={rowIdx}>
            {row.map((key, keyIdx) => (
              <KeyButton
                key={key}
                char={key}
                x={startX + keyIdx * 0.09}
                y={y}
              />
            ))}
          </group>
        );
      })}

      {/* Bottom row with special keys */}
      <group position={[0, -0.20, 0]}>
        <KeyButton char="SHIFT" x={-0.35} y={0} width={0.12} special />
        <KeyButton char="SPACE" x={0} y={0} width={0.35} special />
        <KeyButton char="BACK" x={0.27} y={0} width={0.12} special />
        <KeyButton char="CLEAR" x={0.42} y={0} width={0.12} special />
      </group>
    </group>
  );
}