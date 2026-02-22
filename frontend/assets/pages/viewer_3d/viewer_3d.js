
const state = {
  productId: null,
  productData: {},
  modelUrl: null, // furniture model data URL
  sceneUrls: [], // list of room/scene data URLs
  selectedSceneIndex: 0,

  // transforms
  modelScale: 1.0,
  modelX: 0,
  modelY: 0,
  modelZ: 0,
  modelRotationY: 0,

  // three objects
  mainScene: null,
  mainCamera: null,
  mainRenderer: null,
  mainControls: null,

  // loaded models (gltf.scene)
  furnitureModel: null,
  roomModel: null,

  // tokens to avoid race conditions
  furnitureLoadToken: 0,
  roomLoadToken: 0,

  // loader instances
  gltfLoader: null,
};

function getUrlParams() {
  return new URLSearchParams(window.location.search);
}

function getApiBase() {
  const params = getUrlParams();
  return params.get("api") || "http://localhost:8001";
}

function getDemoUrl() {
  const params = getUrlParams();
  return params.get("demoUrl") || "http://localhost:5174";
}

function getTokenFromUrl() {
  const params = getUrlParams();
  return params.get("token");
}

function isDataUrl(url) {
  return typeof url === "string" && url.startsWith("data:");
}

function safeName(obj) {
  return (obj && (obj.name || obj.type)) || "(unnamed)";
}

async function authenticateIframe() {
  const token = getTokenFromUrl();
  const api = getApiBase();

  if (!token) {
    console.warn("No authentication token provided in URL.");
    return;
  }

  const form = new FormData();
  form.append("token", token);

  try {
    const res = await fetch(`${api}/users/verify_login_token/`, {
      method: "POST",
      body: form,
      credentials: "include",
    });

    if (res.ok) {
    } else {
      console.error("Iframe login failed:", res.status, await res.text());
    }
  } catch (err) {
    console.error("Authentication error:", err);
  }
}

async function initMainViewer() {
  const container = document.getElementById("main-canvas");
  if (!container) throw new Error("#main-canvas not found in DOM");

  const width = container.clientWidth || 800;
  const height = container.clientHeight || 600;

  // Scene + camera + renderer
  state.mainScene = new THREE.Scene();
  state.mainScene.background = new THREE.Color(0x87ceeb);

  state.mainCamera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
  state.mainCamera.position.set(3, 3, 3);

  state.mainRenderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: false,
  });
  state.mainRenderer.setSize(width, height);
  state.mainRenderer.setPixelRatio(window.devicePixelRatio || 1);
  container.appendChild(state.mainRenderer.domElement);

  // Lights
  const ambient = new THREE.AmbientLight(0xffffff, 0.5);
  ambient.name = "ambient_light";
  state.mainScene.add(ambient);

  const directional = new THREE.DirectionalLight(0xffffff, 1);
  directional.position.set(5, 5, 5);
  directional.name = "directional_light";
  state.mainScene.add(directional);

  // Controls
  if (THREE.OrbitControls) {
    state.mainControls = new THREE.OrbitControls(
      state.mainCamera,
      state.mainRenderer.domElement
    );
    state.mainControls.enableDamping = true;
    state.mainControls.dampingFactor = 0.08;
    state.mainControls.screenSpacePanning = false;
    state.mainControls.minDistance = 0.5;
    state.mainControls.maxDistance = Infinity;
  } else {
    console.warn(
      "OrbitControls not available. Make sure examples/js/controls/OrbitControls.js is included."
    );
  }

  // GLTFLoader
  if (THREE.GLTFLoader) {
    state.gltfLoader = new THREE.GLTFLoader();
  } else {
    console.error(
      "GLTFLoader is not available. Include examples/js/loaders/GLTFLoader.js in your HTML."
    );
  }

  // Resize handling
  window.addEventListener("resize", () => {
    const w = container.clientWidth || 800;
    const h = container.clientHeight || 600;
    state.mainCamera.aspect = w / h;
    state.mainCamera.updateProjectionMatrix();
    state.mainRenderer.setSize(w, h);
  });

  // Render loop
  function animate() {
    requestAnimationFrame(animate);
    if (state.mainControls) state.mainControls.update();
    state.mainRenderer.render(state.mainScene, state.mainCamera);
  }
  animate();
}

function disposeGltfScene(gltfScene) {
  if (!gltfScene) return;
  try {
    gltfScene.traverse((obj) => {
      if (obj.isMesh) {
        if (obj.geometry) {
          obj.geometry.dispose();
        }
        if (obj.material) {
          if (Array.isArray(obj.material)) {
            obj.material.forEach((m) => {
              if (m.map) m.map.dispose();
              if (m.materials) {
              }
              try {
                m.dispose();
              } catch (e) {}
            });
          } else {
            if (obj.material.map) obj.material.map.dispose();
            try {
              obj.material.dispose();
            } catch (e) {}
          }
        }
      }
    });
  } catch (e) {
    console.warn("Error disposing gltf scene:", e);
  }
}

function getWidgetType(product) {
  if (!product) return null;
  const cat = (product.category || "").toLowerCase();
  const name = (product.name || "").toLowerCase();
  const type = (product.type || "").toLowerCase();
  if (cat !== "widget" && cat !== "widgets") return null;
  if (name.includes("clock") || type === "clock") return "clock";
  if (name.includes("whiteboard") || type === "whiteboard") return "whiteboard";
  if (name.includes("weather") || type === "weather_widget") return "weather";
  return null;
}

function createClockWidgetPreview() {
  const group = new THREE.Group();
  const width = 512;
  const height = 256;
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) return group;

  ctx.fillStyle = "#0a0a0f";
  ctx.fillRect(0, 0, width, height);
  ctx.font = 'bold 72px "Courier New", monospace';
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.strokeStyle = "#000000";
  ctx.lineWidth = 4;
  ctx.strokeText("12:00:00 PM", width / 2, height / 2);
  ctx.fillStyle = "#ffffff";
  ctx.fillText("12:00:00 PM", width / 2, height / 2);

  const timeTexture = new THREE.CanvasTexture(canvas);
  timeTexture.minFilter = THREE.LinearFilter;
  timeTexture.magFilter = THREE.LinearFilter;

  const frameWidth = 0.5;
  const frameHeight = 0.25;
  const frameDepth = 0.03;
  const frameGeo = new THREE.BoxGeometry(frameWidth + 0.04, frameHeight + 0.04, frameDepth);
  const frameMaterial = new THREE.MeshStandardMaterial({
    color: 0x1e293b,
    roughness: 0.6,
    metalness: 0.2,
  });
  const frame = new THREE.Mesh(frameGeo, frameMaterial);
  frame.position.z = -frameDepth / 2;
  group.add(frame);

  const screenGeo = new THREE.PlaneGeometry(frameWidth, frameHeight);
  const screenMaterial = new THREE.MeshBasicMaterial({
    map: timeTexture,
    color: 0xffffff,
    side: THREE.DoubleSide,
  });
  const screen = new THREE.Mesh(screenGeo, screenMaterial);
  screen.position.z = 0.01;
  group.add(screen);

  const box = new THREE.Box3().setFromObject(group);
  group.position.y = -box.min.y;
  return group;
}

function createWhiteboardWidgetPreview() {
  const group = new THREE.Group();
  const BOARD_WIDTH = 1.0;
  const BOARD_HEIGHT = 0.6;
  const CANVAS_WIDTH = 1024;
  const CANVAS_HEIGHT = 612;

  const canvas = document.createElement("canvas");
  canvas.width = CANVAS_WIDTH;
  canvas.height = CANVAS_HEIGHT;
  const ctx = canvas.getContext("2d");
  if (!ctx) return group;
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

  const drawTexture = new THREE.CanvasTexture(canvas);
  drawTexture.minFilter = THREE.LinearFilter;
  drawTexture.magFilter = THREE.LinearFilter;

  const frameDepth = 0.03;
  const frameGeo = new THREE.BoxGeometry(BOARD_WIDTH + 0.04, BOARD_HEIGHT + 0.04, frameDepth);
  const frameMaterial = new THREE.MeshStandardMaterial({
    color: 0x1e293b,
    roughness: 0.6,
    metalness: 0.2,
  });
  const frame = new THREE.Mesh(frameGeo, frameMaterial);
  frame.position.z = -frameDepth / 2;
  group.add(frame);

  const boardGeo = new THREE.PlaneGeometry(BOARD_WIDTH, BOARD_HEIGHT);
  const boardMaterial = new THREE.MeshBasicMaterial({
    map: drawTexture,
    color: 0xffffff,
    side: THREE.DoubleSide,
  });
  const board = new THREE.Mesh(boardGeo, boardMaterial);
  board.position.z = 0.01;
  group.add(board);

  const box = new THREE.Box3().setFromObject(group);
  group.position.y = -box.min.y;
  return group;
}

function createWeatherWidgetPreview() {
  const group = new THREE.Group();
  const CANVAS_WIDTH = 512;
  const CANVAS_HEIGHT = 320;
  const PANEL_WIDTH = 0.5;
  const PANEL_HEIGHT = PANEL_WIDTH * (CANVAS_HEIGHT / CANVAS_WIDTH);

  const canvas = document.createElement("canvas");
  canvas.width = CANVAS_WIDTH;
  canvas.height = CANVAS_HEIGHT;
  const ctx = canvas.getContext("2d");
  if (!ctx) return group;

  function drawFallbackGradient() {
    const g = ctx.createLinearGradient(0, 0, 0, CANVAS_HEIGHT);
    g.addColorStop(0, "#1e3a5f");
    g.addColorStop(1, "#0f172a");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
  }

  function drawBackgroundImage(img) {
    if (!img || !img.complete || img.naturalWidth <= 0) {
      drawFallbackGradient();
      return;
    }
    const imgAspect = img.width / img.height;
    const canvasAspect = CANVAS_WIDTH / CANVAS_HEIGHT;
    let sx = 0, sy = 0, sWidth = img.width, sHeight = img.height;
    if (imgAspect > canvasAspect) {
      sWidth = img.height * canvasAspect;
      sx = (img.width - sWidth) / 2;
    } else {
      sHeight = img.width / canvasAspect;
      sy = (img.height - sHeight) / 2;
    }
    ctx.drawImage(img, sx, sy, sWidth, sHeight, 0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
  }

  function drawTextScrim() {
    ctx.fillStyle = "rgba(0, 0, 0, 0.5)";
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
  }

  function drawWeatherOverlay() {
    ctx.fillStyle = "#94a3b8";
    ctx.font = "20px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText("Weather Widget", 30, 40);
    ctx.font = "72px sans-serif";
    ctx.fillText("☀", 30, 140);
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 64px sans-serif";
    ctx.textAlign = "right";
    ctx.fillText("22°C", CANVAS_WIDTH - 30, 130);
    ctx.fillStyle = "#cbd5e1";
    ctx.font = "24px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText("Clear", 30, 195);
    ctx.strokeStyle = "#334155";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(30, 220);
    ctx.lineTo(CANVAS_WIDTH - 30, 220);
    ctx.stroke();
    ctx.fillStyle = "#94a3b8";
    ctx.font = "20px sans-serif";
    ctx.fillText("Humidity: 45%", 30, 260);
    ctx.fillText("Wind: 12 km/h", 30, 290);
  }

  drawFallbackGradient();
  drawTextScrim();
  drawWeatherOverlay();

  const canvasTexture = new THREE.CanvasTexture(canvas);
  canvasTexture.minFilter = THREE.LinearFilter;
  canvasTexture.magFilter = THREE.LinearFilter;

  const imgUrl = (typeof window !== "undefined" && window.location?.origin)
    ? new URL("/images/weather/weather_clearSky.png", window.location.origin).href
    : "/images/weather/weather_clearSky.png";
  const img = new Image();
  img.onload = function () {
    drawBackgroundImage(img);
    drawTextScrim();
    drawWeatherOverlay();
    canvasTexture.needsUpdate = true;
  };
  img.onerror = function () {};
  img.src = imgUrl;

  const frameGeometry = new THREE.BoxGeometry(
    PANEL_WIDTH + 0.02,
    PANEL_HEIGHT + 0.02,
    0.015
  );
  const frameMaterial = new THREE.MeshStandardMaterial({
    color: 0x1a1a2e,
    roughness: 0.3,
    metalness: 0.6,
  });
  const frame = new THREE.Mesh(frameGeometry, frameMaterial);
  group.add(frame);

  const screenGeometry = new THREE.PlaneGeometry(PANEL_WIDTH, PANEL_HEIGHT);
  const screenMaterial = new THREE.MeshBasicMaterial({
    map: canvasTexture,
    toneMapped: false,
  });
  const screen = new THREE.Mesh(screenGeometry, screenMaterial);
  screen.position.z = 0.009;
  group.add(screen);

  const box = new THREE.Box3().setFromObject(group);
  group.position.y = -box.min.y;
  return group;
}

function createWidgetPreview(widgetType) {
  switch (widgetType) {
    case "clock":
      return createClockWidgetPreview();
    case "whiteboard":
      return createWhiteboardWidgetPreview();
    case "weather":
      return createWeatherWidgetPreview();
    default:
      return null;
  }
}

function showWidgetPreview(widgetType) {
  const group = createWidgetPreview(widgetType);
  if (!group) return;

  if (state.furnitureModel) {
    try {
      state.mainScene.remove(state.furnitureModel);
      disposeGltfScene(state.furnitureModel);
    } catch (e) {
      console.warn("Error removing previous furniture model:", e);
    }
    state.furnitureModel = null;
  }

  state.furnitureModel = group;
  state.furnitureModel.name = "furniture_model";
  state.modelUrl = null;

  try {
    state.furnitureModel.scale.set(
      state.modelScale,
      state.modelScale,
      state.modelScale
    );
    state.furnitureModel.position.set(state.modelX, state.modelY, state.modelZ);
    state.furnitureModel.rotation.y = state.modelRotationY;
  } catch (e) {}

  state.mainScene.add(state.furnitureModel);

  if (
    state.roomModel &&
    !state.mainScene.children.includes(state.roomModel)
  ) {
    state.mainScene.add(state.roomModel);
  }
}

function loadModelWithLoader(url, loadToken, isRoom = false) {
  return new Promise((resolve, reject) => {
    if (!state.gltfLoader) {
      reject(new Error("GLTFLoader not initialized"));
      return;
    }

    try {
      state.gltfLoader.load(
        url,
        (gltf) => {
          resolve({ gltf, loadToken, isRoom });
        },
        undefined,
        (err) => {
          reject(err);
        }
      );
    } catch (err) {
      reject(err);
    }
  });
}

async function updateRoomModel() {
  const sceneUrl = state.sceneUrls[state.selectedSceneIndex];
  if (!sceneUrl) {
    console.warn("No scene URL available to load room.");
    return;
  }

  const myToken = ++state.roomLoadToken;

  try {
    const { gltf, loadToken, isRoom } = await loadModelWithLoader(
      sceneUrl,
      myToken,
      true
    );

    if (loadToken !== state.roomLoadToken) {
      try {
        disposeGltfScene(gltf.scene);
      } catch (e) {}
      return;
    }

    if (state.roomModel) {
      try {
        state.mainScene.remove(state.roomModel);
        disposeGltfScene(state.roomModel);
      } catch (e) {
        console.warn("Error removing previous room model:", e);
      }
      state.roomModel = null;
    }

    state.roomModel = gltf.scene;
    state.roomModel.name = "room_model";
    state.mainScene.add(state.roomModel);

    if (
      state.furnitureModel &&
      !state.mainScene.children.includes(state.furnitureModel)
    ) {
      state.mainScene.add(state.furnitureModel);
    }
  } catch (err) {
    console.error("Error loading room scene:", err);
  }
}

async function updateFurnitureModel() {
  if (!state.modelUrl) {
    console.warn("No modelUrl available to load furniture.");
    return;
  }

  const myToken = ++state.furnitureLoadToken;

  try {
    const { gltf, loadToken, isRoom } = await loadModelWithLoader(
      state.modelUrl,
      myToken,
      false
    );

    if (loadToken !== state.furnitureLoadToken) {
      try {
        disposeGltfScene(gltf.scene);
      } catch (e) {}
      return;
    }

    if (state.furnitureModel) {
      try {
        state.mainScene.remove(state.furnitureModel);
        disposeGltfScene(state.furnitureModel);
      } catch (e) {
        console.warn("Error removing previous furniture model:", e);
      }
      state.furnitureModel = null;
    }

    state.furnitureModel = gltf.scene;
    state.furnitureModel.name = "furniture_model";

    try {
      state.furnitureModel.scale.set(
        state.modelScale,
        state.modelScale,
        state.modelScale
      );
      state.furnitureModel.position.set(
        state.modelX,
        state.modelY,
        state.modelZ
      );
      state.furnitureModel.rotation.y = state.modelRotationY;
    } catch (e) {
    }

    state.mainScene.add(state.furnitureModel);

    if (
      state.roomModel &&
      !state.mainScene.children.includes(state.roomModel)
    ) {
      state.mainScene.add(state.roomModel);
    }
  } catch (err) {
    console.error("Error loading furniture:", err);
  }
}

function updateFurnitureTransform() {
  if (!state.furnitureModel) return;
  try {
    state.furnitureModel.scale.set(
      state.modelScale,
      state.modelScale,
      state.modelScale
    );
    state.furnitureModel.position.set(state.modelX, state.modelY, state.modelZ);
    state.furnitureModel.rotation.y = state.modelRotationY;
  } catch (e) {
    console.warn("Could not update furniture transform:", e);
  }
  const scaleElem = document.getElementById("scale-value");
  if (scaleElem) scaleElem.textContent = state.modelScale.toFixed(1);
}

async function createThumbnail(url, index) {
  const container = document.createElement("div");
  container.className = "scene-thumbnail";
  if (index === state.selectedSceneIndex) container.classList.add("active");

  const canvas = document.createElement("canvas");
  canvas.width = 200;
  canvas.height = 200;
  container.appendChild(canvas);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x87ceeb);

  const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 1000);
  camera.position.set(3, 3, 3);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setSize(200, 200);

  // lights
  const ambient = new THREE.AmbientLight(0xffffff, 0.5);
  scene.add(ambient);
  const directional = new THREE.DirectionalLight(0xffffff, 1);
  directional.position.set(5, 5, 5);
  scene.add(directional);

  try {
    const thumbLoader = new THREE.GLTFLoader();
    thumbLoader.load(
      url,
      (gltf) => {
        const model = gltf.scene;
        model.scale.set(3, 3, 3);
        scene.add(model);
        renderer.render(scene, camera);
      },
      undefined,
      (err) => {
        console.error("Thumbnail load failed:", err, url);
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#ccc";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = "#666";
        ctx.fillText("Preview failed", 10, 20);
      }
    );
  } catch (err) {
    console.error("Thumbnail loader exception:", err);
  }

  container.addEventListener("click", () => {
    selectScene(index);
  });

  return container;
}

async function renderThumbnails() {
  const container = document.getElementById("thumbnails-container");
  if (!container) return;

  container.innerHTML = "";

  if (!state.sceneUrls || state.sceneUrls.length === 0) {
    container.innerHTML = '<div class="loading">Loading scenes...</div>';
    return;
  }

  for (let i = 0; i < state.sceneUrls.length; i++) {
    try {
      const thumb = await createThumbnail(state.sceneUrls[i], i);
      container.appendChild(thumb);
    } catch (err) {
      console.warn("Could not render thumbnail for index", i, err);
    }
  }
}

async function selectScene(index) {
  if (index < 0 || index >= state.sceneUrls.length) return;
  state.selectedSceneIndex = index;

  document.querySelectorAll(".scene-thumbnail").forEach((thumb, i) => {
    thumb.classList.toggle("active", i === index);
  });

  await updateRoomModel();
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result.split(",")[1]);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

async function fetchProductData(productId) {
  const api = getApiBase();
  if (!productId) {
    console.warn("fetchProductData called without productId");
    return;
  }

  try {
    const res = await fetch(
      `${api}/products/get_product_detail/${productId}/`,
      {
        credentials: "include",
      }
    );

    if (!res.ok) {
      console.error("Product fetch failed", res.status);
      return;
    }

    const data = await res.json();
    state.productData = data.product || {};

    const nameElem = document.getElementById("product-name");
    if (nameElem) nameElem.textContent = state.productData.name || "Product";
    const physElem = document.getElementById("physical-price");
    const digiElem = document.getElementById("digital-price");
    if (physElem)
      physElem.textContent = `$${state.productData.physical_price ?? 0}`;
    if (digiElem)
      digiElem.textContent = `$${state.productData.digital_price ?? 0}`;

    const modelId = state.productData.model_id;
    const widgetType = getWidgetType(state.productData);
    if (modelId === -1 || modelId == null) {
      if (widgetType) {
        showWidgetPreview(widgetType);
      }
    } else {
      await fetch3DModel(modelId);
    }
    if (state.productData.display_scenes_ids)
      await fetchDisplayScenes(state.productData.display_scenes_ids);
  } catch (err) {
    console.error("Error fetching product data:", err);
  }
}

async function fetch3DModel(modelId) {
  const api = getApiBase();
  try {
    const res = await fetch(`${api}/products/get_3d_model/${modelId}/`, {
      credentials: "include",
    });

    if (!res.ok) {
      console.error("3D model fetch failed", res.status);
      return;
    }

    const blob = await res.blob();
    const base64 = await blobToBase64(blob);
    state.modelUrl = `data:model/gltf-binary;base64,${base64}`;

    updateFurnitureModel();
  } catch (err) {
    console.error("Model fetch failed:", err);
  }
}

async function fetchDisplayScenes(ids) {
  const api = getApiBase();
  state.sceneUrls = [];

  for (const id of ids) {
    try {
      const res = await fetch(`${api}/products/get_display_scene/${id}/`, {
        credentials: "include",
      });

      if (!res.ok) {
        console.warn(`Display scene ${id} fetch failed: ${res.status}`);
        continue;
      }

      const blob = await res.blob();
      const base64 = await blobToBase64(blob);
      state.sceneUrls.push(`data:model/gltf-binary;base64,${base64}`);
    } catch (err) {
      console.warn("Error fetching display scene:", err);
    }
  }

  if (state.sceneUrls.length > 0) {
    await renderThumbnails();
    await updateRoomModel();
  }
}

function setupControls() {
  // Scale
  const up = document.getElementById("scale-up");
  const down = document.getElementById("scale-down");
  if (up)
    up.addEventListener("click", () => {
      state.modelScale = Math.min(state.modelScale + 0.1, 5.0);
      updateFurnitureTransform();
    });
  if (down)
    down.addEventListener("click", () => {
      state.modelScale = Math.max(state.modelScale - 0.1, 0.1);
      updateFurnitureTransform();
    });

  // Movement
  const moveLeft = document.getElementById("move-left");
  const moveRight = document.getElementById("move-right");
  const moveUp = document.getElementById("move-up");
  const moveDown = document.getElementById("move-down");
  const moveForward = document.getElementById("move-forward");
  const moveBack = document.getElementById("move-back");

  if (moveLeft)
    moveLeft.addEventListener("click", () => {
      state.modelX -= 0.2;
      updateFurnitureTransform();
    });
  if (moveRight)
    moveRight.addEventListener("click", () => {
      state.modelX += 0.2;
      updateFurnitureTransform();
    });
  if (moveUp)
    moveUp.addEventListener("click", () => {
      state.modelY += 0.2;
      updateFurnitureTransform();
    });
  if (moveDown)
    moveDown.addEventListener("click", () => {
      state.modelY -= 0.2;
      updateFurnitureTransform();
    });
  if (moveForward)
    moveForward.addEventListener("click", () => {
      state.modelZ -= 0.2;
      updateFurnitureTransform();
    });
  if (moveBack)
    moveBack.addEventListener("click", () => {
      state.modelZ += 0.2;
      updateFurnitureTransform();
    });

  // Rotation
  const rotL = document.getElementById("rotate-left");
  const rotR = document.getElementById("rotate-right");
  if (rotL)
    rotL.addEventListener("click", () => {
      state.modelRotationY -= Math.PI / 8;
      updateFurnitureTransform();
    });
  if (rotR)
    rotR.addEventListener("click", () => {
      state.modelRotationY += Math.PI / 8;
      updateFurnitureTransform();
    });

  // Reset
  const resetBtn = document.getElementById("reset");
  if (resetBtn)
    resetBtn.addEventListener("click", () => {
      state.modelScale = 1;
      state.modelX = 0;
      state.modelY = 0;
      state.modelZ = 0;
      state.modelRotationY = 0;
      updateFurnitureTransform();
    });

  // Scene navigation buttons
  const sceneUp = document.getElementById("scene-up");
  const sceneDown = document.getElementById("scene-down");
  if (sceneUp)
    sceneUp.addEventListener("click", () => {
      if (state.selectedSceneIndex < state.sceneUrls.length - 1)
        selectScene(state.selectedSceneIndex + 1);
    });
  if (sceneDown)
    sceneDown.addEventListener("click", () => {
      if (state.selectedSceneIndex > 0)
        selectScene(state.selectedSceneIndex - 1);
    });

  // Add to cart
  const addPhysical = document.getElementById("add-physical");
  const addDigital = document.getElementById("add-digital");
  if (addPhysical)
    addPhysical.addEventListener("click", () => {
      window.parent.postMessage(
        {
          type: "ADD_TO_CART",
          productId: state.productData.id,
          priceType: "physical",
          quantity: 1,
        },
        "*"
      );
    });
  if (addDigital)
    addDigital.addEventListener("click", () => {
      window.parent.postMessage(
        {
          type: "ADD_TO_CART",
          productId: state.productData.id,
          priceType: "digital",
          quantity: 1,
        },
        "*"
      );
    });

  const browseMore = document.getElementById("browse-more");
  if (browseMore)
    browseMore.addEventListener("click", () => {
      window.parent.postMessage({ type: "NAVIGATE", url: "/shop" }, "*");
    });

  const previewVr = document.getElementById("preview-vr");
  if (previewVr) {
    previewVr.addEventListener("click", async () => {
      try {
        const productId = state.productId;
        const displaySceneId = state.productData.display_scenes_ids?.[state.selectedSceneIndex] 
                            || state.productData.display_scenes_ids?.[0];
        
        if (!productId) {
          alert("Product information not available. Please refresh the page.");
          return;
        }
        
        const apiBase = getApiBase();
        
        try {
          const tokenResponse = await fetch(`${apiBase}/users/get_login_token/`, {
            method: 'GET',
            credentials: 'include',
          });

          if (!tokenResponse.ok) {
            console.error('Failed to get token:', tokenResponse.status);
            alert("Authentication failed. Please make sure you're logged in.");
            return;
          }

          const tokenData = await tokenResponse.json();
          const freshToken = tokenData.token;

          const PRODUCT_DEMO_URL = getDemoUrl();
          
          const demoUrl = new URL(`${PRODUCT_DEMO_URL}`);
          demoUrl.searchParams.set('token', freshToken);
          demoUrl.searchParams.set('productId', productId);
          
          if (displaySceneId) {
            demoUrl.searchParams.set('sceneId', displaySceneId);
          }
          
          demoUrl.searchParams.set('api', apiBase);
          
          if (state.productData.name) {
            demoUrl.searchParams.set('productName', state.productData.name);
          }
          
          const newWindow = window.open(demoUrl.toString(), '_blank');
          
          if (!newWindow) {
            alert("Please allow pop-ups for this site to use VR/AR preview.");
          }
          
        } catch (tokenError) {
          console.error('Error getting authentication token:', tokenError);
          alert("Failed to authenticate. Please make sure you're logged in and try again.");
        }
        
      } catch (error) {
        console.error('Error opening VR/AR preview:', error);
        alert("Failed to open VR/AR preview. Please try again.");
      }
    });
  }
}

async function init() {
  const params = new URLSearchParams(window.location.search);
  state.productId = params.get("productId");

  await authenticateIframe();

  try {
    await initMainViewer();
  } catch (err) {
    console.error("Failed to initialize main viewer:", err);
    return;
  }

  setupControls();

  if (state.productId) {
    await fetchProductData(state.productId);
  } else {
    console.warn("No productId found in URL params.");
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
