import reflex as rx
from ..template import template 
from typing import Any, Dict

class ThreepipeViewer(rx.Component):
    """Threepipe viewer with drag and drop support for multiple models"""
    
    tag = "ThreepipeViewerComponent"
    
    # Props
    model_url: rx.Var[str] = ""
    environment_url: rx.Var[str] = "https://samples.threepipe.org/minimal/venice_sunset_1k.hdr"
    width: rx.Var[str] = "100%"
    height: rx.Var[str] = "100vh"
    show_ui: rx.Var[bool] = True
    enable_dropzone: rx.Var[bool] = True
    
    # 🆕 Separate props for initial model only
    initial_model_position: rx.Var[list] = [0, 25, 0]
    initial_model_scale: rx.Var[float] = 1.0
    
    def add_imports(self) -> Dict[str, Any]:
        return {
            "react": ["useRef", "useEffect", "useState"],
            "threepipe": {
                rx.utils.imports.ImportVar(tag="ThreeViewer", install=True),
                rx.utils.imports.ImportVar(tag="LoadingScreenPlugin", install=True),
                rx.utils.imports.ImportVar(tag="PickingPlugin", install=True),
                rx.utils.imports.ImportVar(tag="TransformControlsPlugin", install=True),
                rx.utils.imports.ImportVar(tag="EditorViewWidgetPlugin", install=True),
                rx.utils.imports.ImportVar(tag="DropzonePlugin", install=True),
            },
            "@threepipe/plugin-tweakpane": {
                rx.utils.imports.ImportVar(tag="TweakpaneUiPlugin", install=True),
            },
        }
    
    def add_custom_code(self) -> list[str]:
        return [
            """
            function ThreepipeViewerComponent({ 
                modelUrl = "",
                environmentUrl = "https://samples.threepipe.org/minimal/venice_sunset_1k.hdr",
                width = "100%",
                height = "100vh",
                showUi = true,
                enableDropzone = true,
                initialModelPosition = [0, 0, 0],
                initialModelScale = 0.5
            }) {
                const canvasRef = useRef(null);
                const viewerRef = useRef(null);
                const pluginsRef = useRef({});
                const initialModelUrlRef = useRef(modelUrl);
                const [loading, setLoading] = useState(true);
                const [error, setError] = useState(null);
                const [initialized, setInitialized] = useState(false);
                const [showDropPrompt, setShowDropPrompt] = useState(!modelUrl);
                const [loadedModels, setLoadedModels] = useState([]);

                useEffect(() => {
                    let viewer = null;
                    let cleanup = false;
                    let animationFrameId = null;
                    
                    async function initViewer() {
                        if (!canvasRef.current || cleanup) return;
                        
                        try {
                            setLoading(true);
                            setError(null);
                            
                            console.log('🚀 Starting Threepipe initialization...');
                            
                            if (cleanup) return;
                            
                            console.log('🎨 Creating viewer...');
                            
                            viewer = new ThreeViewer({
                                canvas: canvasRef.current,
                                msaa: true,
                                renderScale: 'auto',
                                plugins: [LoadingScreenPlugin],
                                camera: {
                                    near: 0.0001,
                                    far: 100000,
                                },
                                dropzone: enableDropzone ? {
                                    allowedExtensions: ['gltf', 'glb', 'hdr', 'bin', 'png', 'jpeg', 'webp', 'jpg', 'exr', 'fbx', 'obj', 'stl', 'ply', 'usdz', 'zip'],
                                    addOptions: {
                                        disposeSceneObjects: false,
                                        autoSetEnvironment: true,
                                        autoScale: false,
                                        autoCenter: false,
                                        autoScaleRadius: 5,
                                        importConfig: true,
                                    },
                                } : false,
                            });
                            
                            viewerRef.current = viewer;
                            console.log('✅ Viewer created');
                            
                            const camera = viewer.scene.mainCamera;
                            
                            if (camera.controls) {
                                camera.controls.minDistance = 0.01;
                                camera.controls.maxDistance = 1000;
                                camera.controls.enableDamping = true;
                                camera.controls.dampingFactor = 0.05;
                                
                                console.log('✅ Camera controls configured');
                            }
                            
                            // Dynamic clipping plane updater
                            function updateCameraClipping() {
                                if (!viewer || cleanup) return;
                                
                                const cam = viewer.scene.mainCamera;
                                if (cam.isPerspectiveCamera && cam.controls) {
                                    const distance = cam.controls.target.distanceTo(cam.position);
                                    cam.near = Math.max(distance * 0.0001, 0.00001);
                                    cam.far = Math.max(distance * 1000, 10000);
                                    cam.updateProjectionMatrix();
                                }
                                
                                if (!cleanup) {
                                    animationFrameId = requestAnimationFrame(updateCameraClipping);
                                }
                            }
                            
                            updateCameraClipping();
                            console.log('✅ Dynamic camera clipping started');
                            
                            
                            console.log('🔌 Adding plugins...');
                            const picking = viewer.addPluginSync(PickingPlugin);
                            const transformControlsPlugin = viewer.addPluginSync(TransformControlsPlugin);
                            const editorView = viewer.addPluginSync(
                                new EditorViewWidgetPlugin('bottom-left', 256)
                            );
                            
                            pluginsRef.current = {
                                picking,
                                transformControlsPlugin,
                                editorView
                            };
                            
                            console.log('✅ Core plugins added');
                            
                            // 🆕 Dropzone: all dropped models stay at [0, 0, 0]
                            if (enableDropzone) {
                                const dropzone = viewer.getPlugin(DropzonePlugin);
                                if (dropzone) {
                                    let droppedFileNames = [];
                                    
                                    canvasRef.current.addEventListener('drop', (e) => {
                                        droppedFileNames = [];
                                        if (e.dataTransfer && e.dataTransfer.files) {
                                            for (let file of e.dataTransfer.files) {
                                                droppedFileNames.push(file.name);
                                            }
                                        }
                                    });
                                    
                                    dropzone.addEventListener('drop', (e) => {
                                        console.log('📦 Files dropped:', e);
                                        if (e.assets && e.assets.length > 0) {
                                            setShowDropPrompt(false);
                                            
                                            // 🆕 All dropped models stay at [0, 0, 0] with scale 1.0
                                            const newModels = e.assets.map((asset, index) => {
                                                const fileName = droppedFileNames[index] || 
                                                               asset.name || 
                                                               asset.assetInfo?.originalName ||
                                                               asset.modelObject?.name || 
                                                               `Model ${index + 1}`;
                                                
                                                // 🎯 Set position to [0, 0, 0] and scale to 1.0
                                                if (asset.modelObject) {
                                                    asset.modelObject.position.set(0, 0, 0);
                                                    asset.modelObject.scale.set(1, 1, 1);
                                                    
                                                    console.log(`✅ Dropped model "${fileName}" placed at [0, 0, 0] with scale 1.0`);
                                                }
                                                
                                                return {
                                                    name: fileName,
                                                    object: asset,
                                                    id: Math.random().toString(36).substr(2, 9)
                                                };
                                            });
                                            
                                            setLoadedModels(prev => [...prev, ...newModels]);
                                            
                                            if (e.assets[0] && picking) {
                                                setTimeout(() => {
                                                    picking.setSelectedObject(e.assets[0]);
                                                }, 100);
                                            }
                                            
                                            console.log(`✅ Loaded ${e.assets.length} model(s) at origin`);
                                        }
                                    });
                                    console.log('✅ Dropzone configured');
                                }
                            }
                            
                            if (showUi) {
                                try {
                                    console.log('🎛️ Adding Tweakpane UI plugin...');
                                    const ui = viewer.addPluginSync(new TweakpaneUiPlugin(true));
                                    
                                    ui.setupPluginUi(TransformControlsPlugin, { expanded: true });
                                    ui.setupPluginUi(PickingPlugin);
                                    ui.setupPluginUi(EditorViewWidgetPlugin);
                                    
                                    if (enableDropzone) {
                                        ui.setupPluginUi(DropzonePlugin);
                                    }
                                    
                                    pluginsRef.current.ui = ui;
                                    console.log('✅ Tweakpane UI configured');
                                } catch (uiError) {
                                    console.error('❌ Tweakpane UI error:', uiError);
                                }
                            }
                            
                            if (environmentUrl) {
                                console.log('🌍 Loading environment map...');
                                await viewer.setEnvironmentMap(environmentUrl);
                                console.log('✅ Environment loaded');
                            }
                            
                            // 🆕 Load initial model with CUSTOM position and scale
                            if (modelUrl) {
                                console.log('📦 Loading initial model:', modelUrl);
                                const model = await viewer.load(modelUrl, {
                                    autoCenter: false,
                                    autoScale: false,
                                });
                                
                                console.log('✅ Initial model loaded');
                                
                                if (model) {
                                    // 🎯 Apply CUSTOM position and scale to initial model ONLY
                                    if (model.modelObject) {
                                        model.modelObject.position.set(
                                            initialModelPosition[0],
                                            initialModelPosition[1],
                                            initialModelPosition[2]
                                        );
                                        model.modelObject.scale.set(
                                            initialModelScale,
                                            initialModelScale,
                                            initialModelScale
                                        );
                                        console.log(`✅ Initial model positioned at [${initialModelPosition}] with scale ${initialModelScale}`);
                                    }
                                    
                                    setShowDropPrompt(false);
                                    
                                    const modelName = modelUrl.split('/').pop() || 'Initial Model';
                                    const newModel = {
                                        name: modelName,
                                        object: model,
                                        id: 'initial-model'
                                    };
                                    setLoadedModels([newModel]);
                                    
                                    if (picking) {
                                        picking.setSelectedObject(model);
                                    }
                                }
                            }
                            
                            window.threepipeViewer = viewer;
                            window.threepipePicking = picking;
                            window.threepipeTransformControlsPlugin = transformControlsPlugin;
                            window.threepipeTransformControls = transformControlsPlugin.transformControls;
                            window.threepipeEditorView = editorView;
                            if (pluginsRef.current.ui) {
                                window.threepipeUI = pluginsRef.current.ui;
                            }
                            
                            window.setModelTransform = (modelId, position = null, scale = null) => {
                                const model = loadedModels.find(m => m.id === modelId);
                                if (model && model.object.modelObject) {
                                    if (position) {
                                        model.object.modelObject.position.set(position[0], position[1], position[2]);
                                    }
                                    if (scale) {
                                        model.object.modelObject.scale.set(scale, scale, scale);
                                    }
                                    console.log('✅ Transform updated for:', model.name);
                                }
                            };
                            
                            window.getCameraInfo = () => {
                                const cam = viewer.scene.mainCamera;
                                const distance = cam.controls ? cam.controls.target.distanceTo(cam.position) : 0;
                                return {
                                    distance: distance.toFixed(4),
                                    near: cam.near.toFixed(6),
                                    far: cam.far.toFixed(2),
                                    minDistance: cam.controls?.minDistance,
                                    maxDistance: cam.controls?.maxDistance
                                };
                            };
                            
                            window.clearAllModels = () => {
                                const scene = viewer.scene;
                                const objectsToRemove = scene.modelRoot.children.filter(obj => 
                                    obj.userData && obj.userData.importedObject
                                );
                                objectsToRemove.forEach(obj => {
                                    scene.remove(obj);
                                    obj.dispose?.();
                                });
                                setLoadedModels([]);
                                setShowDropPrompt(true);
                                console.log('🗑️ All models cleared');
                            };
                            
                            setLoading(false);
                            setInitialized(true);
                            console.log('🎉 Initialization complete!');
                            
                        } catch (err) {
                            console.error('💥 Error:', err);
                            if (!cleanup) {
                                setError(err.message);
                                setLoading(false);
                            }
                        }
                    }
                    
                    initViewer();
                    
                    return () => {
                        cleanup = true;
                        if (animationFrameId) {
                            cancelAnimationFrame(animationFrameId);
                        }
                        if (viewer) {
                            try {
                                viewer.dispose();
                            } catch (e) {
                                console.error('Dispose error:', e);
                            }
                        }
                    };
                }, [showUi, enableDropzone, initialModelPosition, initialModelScale]);
                
                // Update model when URL changes
                useEffect(() => {
                    if (modelUrl === initialModelUrlRef.current) {
                        console.log('⏭️ Skipping initial model URL in update effect');
                        return;
                    }
                    
                    if (viewerRef.current && modelUrl && initialized) {
                        console.log('🔄 Loading new model:', modelUrl);
                        setLoading(true);
                        viewerRef.current.load(modelUrl, {
                            autoCenter: false,
                            autoScale: false,
                            disposeSceneObjects: false,
                        })
                        .then((model) => {
                            console.log('✅ New model loaded');
                            if (model) {
                                // 🎯 New models from state also get custom position
                                if (model.modelObject) {
                                    model.modelObject.position.set(
                                        initialModelPosition[0],
                                        initialModelPosition[1],
                                        initialModelPosition[2]
                                    );
                                    model.modelObject.scale.set(
                                        initialModelScale,
                                        initialModelScale,
                                        initialModelScale
                                    );
                                }
                                
                                setShowDropPrompt(false);
                                
                                const modelName = modelUrl.split('/').pop() || 'Model';
                                const newModel = {
                                    name: modelName,
                                    object: model,
                                    id: Math.random().toString(36).substr(2, 9)
                                };
                                setLoadedModels(prev => [...prev, newModel]);
                                
                                if (pluginsRef.current.picking) {
                                    pluginsRef.current.picking.setSelectedObject(model);
                                }
                            }
                            setLoading(false);
                        })
                        .catch(err => {
                            console.error('❌ Model load error:', err);
                            setError(err.message);
                            setLoading(false);
                        });
                    }
                }, [modelUrl, initialized]);
                
                const selectModel = (model) => {
                    if (pluginsRef.current.picking && model.object) {
                        pluginsRef.current.picking.setSelectedObject(model.object);
                        console.log('Selected model:', model.name);
                    }
                };
                
                const removeModel = (modelId) => {
                    const modelToRemove = loadedModels.find(m => m.id === modelId);
                    if (modelToRemove && viewerRef.current) {
                        viewerRef.current.scene.remove(modelToRemove.object);
                        modelToRemove.object.dispose?.();
                        setLoadedModels(prev => prev.filter(m => m.id !== modelId));
                        console.log('Removed model:', modelToRemove.name);
                        
                        if (loadedModels.length === 1) {
                            setShowDropPrompt(true);
                        }
                    }
                };
                
                return (
                    <div style={{
                        width: width,
                        height: height,
                        position: 'relative',
                        overflow: 'hidden',
                        backgroundColor: '#1a1a2e'
                    }}>
                        <canvas 
                            ref={canvasRef}
                            id="mcanvas"
                            style={{
                                width: '100%',
                                height: '100%',
                                display: 'block'
                            }}
                        />
                        {enableDropzone && showDropPrompt && !loading && (
                            <div style={{
                                position: 'absolute',
                                top: '50%',
                                left: '50%',
                                transform: 'translate(-50%, -50%)',
                                color: 'rgba(255, 255, 255, 0.7)',
                                fontSize: '24px',
                                fontFamily: 'sans-serif',
                                textAlign: 'center',
                                pointerEvents: 'none',
                                zIndex: 50,
                                background: 'rgba(0, 0, 0, 0.6)',
                                padding: '40px 60px',
                                borderRadius: '16px',
                                border: '2px dashed rgba(255, 255, 255, 0.3)',
                                backdropFilter: 'blur(10px)'
                            }}>
                                <div style={{ fontSize: '48px', marginBottom: '20px' }}>📦</div>
                                <div style={{ marginBottom: '12px', fontWeight: '600' }}>
                                    Drop 3D Models Here
                                </div>
                                <div style={{ 
                                    fontSize: '16px', 
                                    opacity: 0.9,
                                    marginTop: '8px',
                                    color: '#22c55e'
                                }}>
                                    Will be placed at origin [0, 0, 0]
                                </div>
                                <div style={{ 
                                    fontSize: '14px', 
                                    opacity: 0.8,
                                    fontFamily: 'monospace',
                                    marginTop: '16px'
                                }}>
                                    GLB • GLTF • FBX • OBJ • STL • PLY • USDZ
                                </div>
                            </div>
                        )}
                        
                        {loadedModels.length > 0 && (
                            <div style={{
                                position: 'absolute',
                                top: '60px',
                                left: '20px',
                                background: 'rgba(0, 0, 0, 0.9)',
                                padding: '16px',
                                borderRadius: '12px',
                                zIndex: 1000,
                                maxWidth: '300px',
                                maxHeight: '400px',
                                overflow: 'auto',
                                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)',
                                backdropFilter: 'blur(10px)'
                            }}>
                                <div style={{
                                    color: 'white',
                                    fontSize: '14px',
                                    fontWeight: 'bold',
                                    marginBottom: '12px',
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    borderBottom: '1px solid #4a5568',
                                    paddingBottom: '8px'
                                }}>
                                    <span>📦 Loaded Models ({loadedModels.length})</span>
                                </div>
                                {loadedModels.map((model) => (
                                    <div 
                                        key={model.id}
                                        style={{
                                            background: 'rgba(255, 255, 255, 0.1)',
                                            padding: '10px',
                                            borderRadius: '6px',
                                            marginBottom: '8px',
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            alignItems: 'center',
                                            cursor: 'pointer',
                                            transition: 'all 0.2s'
                                        }}
                                        onMouseEnter={(e) => {
                                            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.15)';
                                        }}
                                        onMouseLeave={(e) => {
                                            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
                                        }}
                                        onClick={() => selectModel(model)}
                                    >
                                        <span style={{
                                            color: 'white',
                                            fontSize: '13px',
                                            flex: 1,
                                            overflow: 'hidden',
                                            textOverflow: 'ellipsis',
                                            whiteSpace: 'nowrap'
                                        }}>
                                            {model.name}
                                        </span>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                removeModel(model.id);
                                            }}
                                            style={{
                                                background: '#dc2626',
                                                border: 'none',
                                                borderRadius: '4px',
                                                color: 'white',
                                                padding: '4px 8px',
                                                fontSize: '11px',
                                                cursor: 'pointer',
                                                marginLeft: '8px',
                                                transition: 'background 0.2s'
                                            }}
                                            onMouseEnter={(e) => e.target.style.background = '#b91c1c'}
                                            onMouseLeave={(e) => e.target.style.background = '#dc2626'}
                                        >
                                            ✕
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                        
                        {loading && (
                            <div style={{
                                position: 'absolute',
                                top: '50%',
                                left: '50%',
                                transform: 'translate(-50%, -50%)',
                                color: 'white',
                                fontSize: '18px',
                                textAlign: 'center',
                                backgroundColor: 'rgba(0, 0, 0, 0.9)',
                                padding: '24px 32px',
                                borderRadius: '12px',
                                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)',
                                zIndex: 999
                            }}>
                                <div style={{ marginBottom: '12px', fontSize: '32px', animation: 'spin 2s linear infinite' }}>
                                    🔄
                                </div>
                                <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>
                                    Loading 3D Model
                                </div>
                                <div style={{ fontSize: '14px', opacity: 0.7 }}>
                                    Please wait...
                                </div>
                            </div>
                        )}
                        
                        {error && (
                            <div style={{
                                position: 'absolute',
                                top: '20px',
                                right: '20px',
                                background: 'rgba(220, 38, 38, 0.95)',
                                color: 'white',
                                padding: '16px 24px',
                                borderRadius: '8px',
                                zIndex: 1000,
                                maxWidth: '400px',
                                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)'
                            }}>
                                <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>❌ Error</div>
                                <div style={{ fontSize: '14px' }}>{error}</div>
                            </div>
                        )}
                        
                        {showUi && !loading && !error && (
                            <div style={{
                                position: 'absolute',
                                bottom: '20px',
                                left: '20px',
                                background: 'rgba(59, 130, 246, 0.9)',
                                color: 'white',
                                padding: '6px 12px',
                                borderRadius: '6px',
                                fontSize: '11px',
                                zIndex: 1000,
                                boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                            }}>
                                🎛️ Tweakpane UI Active
                            </div>
                        )}
                        
                        <style>{`
                            @keyframes spin {
                                from { transform: rotate(0deg); }
                                to { transform: rotate(360deg); }
                            }
                        `}</style>
                    </div>
                );
            }
            """
        ]

threepipe_advanced_viewer = ThreepipeViewer.create

class ViewerState(rx.State):
    """State for the 3D viewer."""
    
    # Initial model from code (this one gets custom position/scale)
    initial_model: str = "/models/forest_cabin.glb"
    current_model: str = initial_model
    show_ui: bool = True
    enable_dropzone: bool = True
    
    # 🆕 Position and scale for INITIAL MODEL ONLY
    initial_model_position: list = [-20, -8, 10]  # Custom position for initial model
    initial_model_scale: float = 1.5  # Custom scale for initial model
    
    background_color: str = "0xF5F5F5" 
    
    def load_helmet(self):
        self.current_model = "https://samples.threepipe.org/minimal/DamagedHelmet/glTF/DamagedHelmet.gltf"
    
    def load_chair(self):
        self.current_model = "/models/Rocking_Chair.glb"
    
    def toggle_ui(self):
        self.show_ui = not self.show_ui

def room_content() -> rx.Component:
    return rx.fragment(
        rx.box(
            threepipe_advanced_viewer(
                model_url=ViewerState.current_model,
                show_ui=ViewerState.show_ui,
                enable_dropzone=ViewerState.enable_dropzone,
                initial_model_position=ViewerState.initial_model_position,
                initial_model_scale=ViewerState.initial_model_scale,
                width="100%",
                height="100vh",
            ),
            position="relative",
        ),
        
        # Back button
        rx.link(
            rx.button(
                rx.icon("arrow-left", size=20),
                rx.text("Back", margin_left="8px"),
                display="flex",
                align_items="center",
                padding="12px 20px",
                background="rgba(0, 0, 0, 0.8)",
                color="white",
                border="1px solid rgba(255, 255, 255, 0.2)",
                border_radius="8px",
                cursor="pointer",
                font_size="14px",
                font_weight="500",
                transition="all 0.2s",
                _hover={
                    "background": "rgba(59, 130, 246, 0.9)",
                    "border_color": "rgba(59, 130, 246, 1)",
                    "transform": "translateY(-2px)",
                    "box_shadow": "0 4px 12px rgba(59, 130, 246, 0.4)",
                },
            ),
            href="/",
            position="absolute",
            top="20px",
            left="20px",
            z_index="2000",
        ),
        
        width="100%",
        height="100vh",
        bg="gray.900",
        overflow="hidden",
    )

def my_digital_home_page() -> rx.Component:
    return room_content()
    # return template(room_content)