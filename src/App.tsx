import React from "react";
import { Canvas } from "@react-three/fiber";
import { GlobalProvider } from "./context/global-context";
import { Environment, Gltf, PerspectiveCamera } from "@react-three/drei";
import { createXRStore, XR } from "@react-three/xr";
// import Gun from "./components/gun";
// import Bullets from "./components/bullets";
// import Target from "./components/target";
// import Score from "./components/score";

const xrStore = createXRStore({
  // controller: {
  //   right: Gun,
  // },
});

export default function App() {
  const [isVRActive, setIsVRActive] = React.useState(false);
  const [showFurniture, setShowFurniture] = React.useState(false);

  React.useEffect(() => {
    const unsubscribe = xrStore.subscribe((state) => {
      setIsVRActive(state !== null);
    });
    
    return () => unsubscribe();
  }, []);

  const furnitureItems = [
    { id: 1, name: "Modern Stylish Mini Table", category: "Chairs", image: "/chair1.jpg" },
    { id: 2, name: "Modern Stylish Mini Table", category: "Chairs", image: "/chair2.jpg" },
    { id: 3, name: "Modern Stylish Mini Table", category: "Tables", image: "/table.jpg" },
    { id: 4, name: "Modern Stylish Mini Table", category: "Sofas", image: "/sofa.jpg" },
    { id: 5, name: "Modern Stylish Mini Table", category: "Chairs", image: "/chair3.jpg" },
  ];

  return (
    <GlobalProvider>
      <>
        <Canvas
          style={{
            width: "100vw",
            height: "100vh",
            position: "fixed",
          }}
        >
          <color args={[0x808080]} attach={"background"} />
          <PerspectiveCamera makeDefault position={[0, 1.6, 2]} fov={75} />
          <Environment preset="warehouse" />
          <Gltf src="/labPlan.glb" />
          <XR store={xrStore} />
          {/* <Bullets />
          <Target targetIdx={0} />
          <Target targetIdx={1} />
          <Target targetIdx={2} />
          <Score /> */}
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
          {!isVRActive ? (
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
          ) : (
            <button
              style={{
                position: "fixed",
                top: "20px",
                right: "20px",
                fontSize: "16px",
                pointerEvents: "auto",
                padding: "10px 20px",
                backgroundColor: "#2196F3",
                color: "white",
                border: "none",
                borderRadius: "8px",
                cursor: "pointer",
                zIndex: 1000,
              }}
              onClick={() => setShowFurniture(!showFurniture)}
            >
              {showFurniture ? "Close" : "Edit"}
            </button>
          )}

          {/* Furniture Slider */}
          <div
            style={{
              position: "fixed",
              bottom: showFurniture ? "0" : "-400px",
              left: "0",
              width: "100%",
              height: "350px",
              backgroundColor: "rgba(255, 255, 255, 0.95)",
              transition: "bottom 0.3s ease-in-out",
              pointerEvents: "auto",
              padding: "20px",
              boxShadow: "0 -4px 20px rgba(0, 0, 0, 0.2)",
              zIndex: 999,
            }}
          >
            <h2 style={{ color: "#333", marginBottom: "20px", marginTop: "0" }}>
              My Inventory
            </h2>
            <div
              style={{
                display: "flex",
                gap: "15px",
                overflowX: "auto",
                paddingBottom: "10px",
              }}
            >
              {furnitureItems.map((item) => (
                <div
                  key={item.id}
                  style={{
                    minWidth: "200px",
                    backgroundColor: "white",
                    borderRadius: "12px",
                    padding: "15px",
                    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
                    cursor: "pointer",
                    transition: "transform 0.2s",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = "scale(1.05)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = "scale(1)";
                  }}
                >
                  <div
                    style={{
                      width: "100%",
                      height: "150px",
                      backgroundColor: "#f5f5f5",
                      borderRadius: "8px",
                      marginBottom: "10px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "#999",
                    }}
                  >
                    {item.category}
                  </div>
                  <div
                    style={{
                      fontSize: "11px",
                      color: "#666",
                      backgroundColor: "#f0f0f0",
                      padding: "4px 8px",
                      borderRadius: "4px",
                      display: "inline-block",
                      marginBottom: "8px",
                    }}
                  >
                    {item.category}
                  </div>
                  <div style={{ fontSize: "14px", color: "#333", fontWeight: "500" }}>
                    {item.name}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </>
    </GlobalProvider>
  );
}