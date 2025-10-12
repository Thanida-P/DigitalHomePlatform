import reflex as rx
from typing import Any, Dict

class ThreepipeAdvancedViewer(rx.Component):
    """Advanced Threepipe viewer with transform controls, Tweakpane UI, and Material Configurator."""
    
    tag = "ThreepipeAdvancedViewerComponent"
    
    # Props
    model_url: rx.Var[str] = "https://samples.threepipe.org/demos/classic-watch.glb"
    environment_url: rx.Var[str] = "https://samples.threepipe.org/minimal/venice_sunset_1k.hdr"
    width: rx.Var[str] = "100%"
    height: rx.Var[str] = "100vh"
    background_color: rx.Var[str] = "0x151822"
    show_ui: rx.Var[bool] = True
    enable_material_config: rx.Var[bool] = True
    
    def add_imports(self) -> Dict[str, Any]:
        return {
            "react": ["useRef", "useEffect", "useState"],
            "threepipe": {
                rx.utils.imports.ImportVar(tag="ThreeViewer", install=True),
                rx.utils.imports.ImportVar(tag="LoadingScreenPlugin", install=True),
                rx.utils.imports.ImportVar(tag="PickingPlugin", install=True),
                rx.utils.imports.ImportVar(tag="TransformControlsPlugin", install=True),
                rx.utils.imports.ImportVar(tag="EditorViewWidgetPlugin", install=True),
                rx.utils.imports.ImportVar(tag="FrameFadePlugin", install=True),
                rx.utils.imports.ImportVar(tag="SSAAPlugin", install=True),
            },
            "@threepipe/plugin-tweakpane": {
                rx.utils.imports.ImportVar(tag="TweakpaneUiPlugin", install=True),
            },
            "@threepipe/plugin-configurator": {
                rx.utils.imports.ImportVar(tag="MaterialConfiguratorPlugin", install=True),
            },
        }
    
    def add_custom_code(self) -> list[str]:
        return [
            """
            function ThreepipeAdvancedViewerComponent({ 
                modelUrl = "https://samples.threepipe.org/demos/classic-watch.glb",
                environmentUrl = "https://samples.threepipe.org/minimal/venice_sunset_1k.hdr",
                width = "100%",
                height = "100vh",
                backgroundColor = "0x151822",
                showUi = true,
                enableMaterialConfig = true
            }) {
                const canvasRef = useRef(null);
                const viewerRef = useRef(null);
                const pluginsRef = useRef({});
                const [loading, setLoading] = useState(true);
                const [error, setError] = useState(null);
                const [initialized, setInitialized] = useState(false);

                // Initialize viewer with all plugins
                useEffect(() => {
                    let viewer = null;
                    let cleanup = false;
                    
                    async function initViewer() {
                        if (!canvasRef.current || cleanup) return;
                        
                        try {
                            setLoading(true);
                            setError(null);
                            
                            console.log('🚀 Starting Threepipe initialization...');
                            
                            if (cleanup) return;
                            
                            console.log('🎨 Creating viewer...');
                            
                            // Create viewer with plugins
                            viewer = new ThreeViewer({
                                canvas: canvasRef.current,
                                msaa: false,
                                renderScale: 'auto',
                                plugins: [
                                    LoadingScreenPlugin,
                                    PickingPlugin,
                                    FrameFadePlugin,
                                    SSAAPlugin
                                ],
                            });
                            
                            viewerRef.current = viewer;
                            console.log('✅ Viewer created');
                            
                            // Set background color
                            const bgColor = parseInt(backgroundColor.replace('0x', ''), 16);
                            viewer.scene.setBackgroundColor(bgColor);
                            
                            // Add core plugins
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
                            
                            // Add Material Configurator Plugin
                            if (enableMaterialConfig) {
                                console.log('🎨 Adding Material Configurator...');
                                const materialConfigurator = viewer.addPluginSync(new MaterialConfiguratorPlugin());
                                materialConfigurator.enableEditContextMenus = true;
                                materialConfigurator.animateApply = true;
                                materialConfigurator.animateApplyDuration = 1000;
                                
                                // Example: Add custom material variations programmatically
                                // This would be done after loading the model
                                // materialConfigurator.addMaterialVariation({
                                //     name: 'Gold Watch Band',
                                //     target: 'watchBandMaterial', // Material name in the model
                                //     properties: {
                                //         color: '#FFD700',
                                //         metalness: 1.0,
                                //         roughness: 0.2,
                                //         map: 'path/to/texture.jpg' // Optional texture
                                //     }
                                // });
                                
                                pluginsRef.current.materialConfigurator = materialConfigurator;
                                console.log('✅ Material Configurator added');
                            }
                            
                            // Add Tweakpane UI if enabled
                            if (showUi) {
                                try {
                                    console.log('🎛️ Adding Tweakpane UI plugin...');
                                    const ui = viewer.addPluginSync(new TweakpaneUiPlugin(true));
                                    
                                    console.log('⚙️ Setting up plugin UIs...');
                                    
                                    // Setup Material Configurator UI first if enabled
                                    if (enableMaterialConfig && pluginsRef.current.materialConfigurator) {
                                        ui.setupPluginUi(MaterialConfiguratorPlugin);
                                        console.log('✅ Material Configurator UI setup');
                                    }
                                    
                                    ui.setupPluginUi(TransformControlsPlugin, { expanded: false });
                                    ui.setupPluginUi(PickingPlugin);
                                    ui.setupPluginUi(EditorViewWidgetPlugin);
                                    ui.appendChild(viewer.uiConfig);
                                    
                                    pluginsRef.current.ui = ui;
                                    console.log('✅ Tweakpane UI fully configured');
                                } catch (uiError) {
                                    console.error('❌ Tweakpane UI error:', uiError);
                                    console.log('⚠️ Continuing without Tweakpane UI');
                                }
                            }
                            
                            // Load environment
                            if (environmentUrl) {
                                console.log('🌍 Loading environment map...');
                                await viewer.setEnvironmentMap(environmentUrl);
                                console.log('✅ Environment loaded');
                            }
                            
                            // Load model
                            if (modelUrl) {
                                console.log('📦 Loading model:', modelUrl);
                                const model = await viewer.load(modelUrl, {
                                    autoCenter: true,
                                    autoScale: true,
                                });
                                
                                console.log('✅ Model loaded');
                                
                                // Enable damping for smoother controls
                                if (viewer.scene.mainCamera.controls) {
                                    viewer.scene.mainCamera.controls.enableDamping = true;
                                }
                                
                                // IMPORTANT: List all materials in the model for reference
                                console.log('🎨 Materials in model:');
                                const materials = new Set();
                                model.traverse((object) => {
                                    if (object.material) {
                                        if (Array.isArray(object.material)) {
                                            object.material.forEach(mat => {
                                                materials.add(mat.name);
                                                console.log(`  ✓ ${mat.name}`);
                                            });
                                        } else {
                                            materials.add(object.material.name);
                                            console.log(`  ✓ ${object.material.name}`);
                                        }
                                    }
                                });
                                
                                // Add custom material variations for EVERY material in the model
                                if (pluginsRef.current.materialConfigurator && materials.size > 0) {
                                    console.log('🎨 Adding custom material variations for ALL materials...');
                                    
                                    const configurator = pluginsRef.current.materialConfigurator;
                                    
                                    // Define color presets with unique IDs
                                    const colorPresets = [
                                        { id: 'gold', name: 'Gold', color: '#FFD700', metalness: 1.0, roughness: 0.2 },
                                        { id: 'silver', name: 'Silver', color: '#C0C0C0', metalness: 1.0, roughness: 0.15 },
                                        { id: 'bronze', name: 'Bronze', color: '#CD7F32', metalness: 1.0, roughness: 0.3 },
                                        { id: 'copper', name: 'Copper', color: '#B87333', metalness: 1.0, roughness: 0.25 },
                                        { id: 'black', name: 'Matte Black', color: '#1a1a1a', metalness: 0.0, roughness: 0.9 },
                                        { id: 'white', name: 'Glossy White', color: '#ffffff', metalness: 0.0, roughness: 0.1 },
                                        { id: 'red', name: 'Glossy Red', color: '#ff0000', metalness: 0.1, roughness: 0.2 },
                                        { id: 'blue', name: 'Glossy Blue', color: '#0066ff', metalness: 0.1, roughness: 0.2 },
                                        { id: 'green', name: 'Glossy Green', color: '#00ff00', metalness: 0.1, roughness: 0.2 },
                                        { id: 'chrome', name: 'Chrome', color: '#ffffff', metalness: 1.0, roughness: 0.05 },
                                    ];
                                    
                                    // Store material info for quick access
                                    window.threepipeMaterialsList = Array.from(materials);
                                    window.threepipeColorPresets = colorPresets;
                                    
                                    // Add variations for EACH material found in the model
                                    materials.forEach(materialName => {
                                        console.log(`  📝 Adding variations for: ${materialName}`);
                                        
                                        colorPresets.forEach(preset => {
                                            try {
                                                configurator.addMaterialVariation({
                                                    id: `${materialName}_${preset.id}`,
                                                    name: preset.name,
                                                    materialName: materialName,
                                                    properties: {
                                                        color: preset.color,
                                                        metalness: preset.metalness,
                                                        roughness: preset.roughness,
                                                    }
                                                });
                                            } catch (e) {
                                                console.warn(`    ⚠️ Could not add ${preset.name} to ${materialName}:`, e.message);
                                            }
                                        });
                                    });
                                    
                                    // Create helper function to apply materials
                                    window.applyMaterial = (materialName, presetId) => {
                                        const variation = configurator.variations?.find(v => 
                                            v.id === `${materialName}_${presetId}`
                                        );
                                        if (variation) {
                                            configurator.applyVariation(variation);
                                            console.log(`✅ Applied ${presetId} to ${materialName}`);
                                            return true;
                                        }
                                        console.error(`❌ Variation not found: ${materialName}_${presetId}`);
                                        return false;
                                    };
                                    
                                    console.log('✅ Custom material variations added for all materials!');
                                    console.log('💡 Check Tweakpane UI or use applyMaterial(materialName, presetId)');
                                    console.log('📋 Total materials configured:', materials.size);
                                    console.log('🎨 Example: applyMaterial("' + Array.from(materials)[0] + '", "gold")');
                                }
                                
                                // Select the model by default
                                if (model && picking) {
                                    console.log('🎯 Selecting model...');
                                    picking.setSelectedObject(model);
                                    
                                    const transformControls = transformControlsPlugin.transformControls;
                                    console.log('🎮 Transform controls:', transformControls);
                                }
                            }
                            
                            // Store references globally for external control
                            window.threepipeViewer = viewer;
                            window.threepipePicking = picking;
                            window.threepipeTransformControlsPlugin = transformControlsPlugin;
                            window.threepipeTransformControls = transformControlsPlugin.transformControls;
                            window.threepipeEditorView = editorView;
                            if (pluginsRef.current.ui) {
                                window.threepipeUI = pluginsRef.current.ui;
                            }
                            if (pluginsRef.current.materialConfigurator) {
                                window.threepipeMaterialConfigurator = pluginsRef.current.materialConfigurator;
                            }
                            
                            setLoading(false);
                            setInitialized(true);
                            console.log('🎉 Initialization complete!');
                            console.log('Available globals:', {
                                viewer: !!window.threepipeViewer,
                                picking: !!window.threepipePicking,
                                transformControls: !!window.threepipeTransformControls,
                                editorView: !!window.threepipeEditorView,
                                ui: !!window.threepipeUI,
                                materialConfigurator: !!window.threepipeMaterialConfigurator
                            });
                            
                        } catch (err) {
                            console.error('💥 Threepipe initialization error:', err);
                            console.error('Error stack:', err.stack);
                            if (!cleanup) {
                                setError(err.message);
                                setLoading(false);
                            }
                        }
                    }
                    
                    initViewer();
                    
                    return () => {
                        cleanup = true;
                        if (viewer) {
                            try {
                                viewer.dispose();
                            } catch (e) {
                                console.error('Dispose error:', e);
                            }
                        }
                    };
                }, [backgroundColor, showUi, enableMaterialConfig]);
                
                // Update model when URL changes
                useEffect(() => {
                    if (viewerRef.current && modelUrl && initialized) {
                        console.log('🔄 Loading new model:', modelUrl);
                        setLoading(true);
                        
                        // Clear previous material variations
                        if (pluginsRef.current.materialConfigurator) {
                            console.log('🧹 Clearing previous material configurations...');
                            // Material configurator will refresh with new model
                        }
                        
                        viewerRef.current.load(modelUrl, {
                            autoCenter: true,
                            autoScale: true,
                            disposeSceneObjects: true,
                        })
                        .then((model) => {
                            console.log('✅ New model loaded');
                            
                            // Enable damping
                            if (viewerRef.current.scene.mainCamera.controls) {
                                viewerRef.current.scene.mainCamera.controls.enableDamping = true;
                            }
                            
                            // Find and configure materials for the NEW model
                            console.log('🎨 Materials in new model:');
                            const materials = new Set();
                            model.traverse((object) => {
                                if (object.material) {
                                    if (Array.isArray(object.material)) {
                                        object.material.forEach(mat => {
                                            materials.add(mat.name);
                                            console.log(`  ✓ ${mat.name}`);
                                        });
                                    } else {
                                        materials.add(object.material.name);
                                        console.log(`  ✓ ${object.material.name}`);
                                    }
                                }
                            });
                            
                            // Add material variations for the new model
                            if (pluginsRef.current.materialConfigurator && materials.size > 0) {
                                console.log('🎨 Adding material variations for new model...');
                                
                                const colorPresets = [
                                    { name: 'Gold', color: '#FFD700', metalness: 1.0, roughness: 0.2 },
                                    { name: 'Silver', color: '#C0C0C0', metalness: 1.0, roughness: 0.15 },
                                    { name: 'Bronze', color: '#CD7F32', metalness: 1.0, roughness: 0.3 },
                                    { name: 'Copper', color: '#B87333', metalness: 1.0, roughness: 0.25 },
                                    { name: 'Matte Black', color: '#1a1a1a', metalness: 0.0, roughness: 0.9 },
                                    { name: 'Glossy White', color: '#ffffff', metalness: 0.0, roughness: 0.1 },
                                    { name: 'Glossy Red', color: '#ff0000', metalness: 0.1, roughness: 0.2 },
                                    { name: 'Glossy Blue', color: '#0066ff', metalness: 0.1, roughness: 0.2 },
                                    { name: 'Chrome', color: '#ffffff', metalness: 1.0, roughness: 0.05 },
                                ];
                                
                                materials.forEach(materialName => {
                                    colorPresets.forEach(preset => {
                                        try {
                                            pluginsRef.current.materialConfigurator.addMaterialVariation({
                                                name: `${preset.name}`,
                                                materialName: materialName,
                                                properties: {
                                                    color: preset.color,
                                                    metalness: preset.metalness,
                                                    roughness: preset.roughness,
                                                }
                                            });
                                        } catch (e) {
                                            // Silently continue if variation already exists
                                        }
                                    });
                                });
                                
                                console.log('✅ Material variations added for new model!');
                            }
                            
                            if (pluginsRef.current.picking && model) {
                                pluginsRef.current.picking.setSelectedObject(model);
                                console.log('🎯 New model selected');
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
                                    Loading 3D Viewer
                                </div>
                                <div style={{ fontSize: '14px', opacity: 0.7 }}>
                                    Initializing Threepipe...
                                </div>
                            </div>
                        )}
                        
                        {error && (
                            <div style={{
                                position: 'absolute',
                                top: '20px',
                                left: '50%',
                                transform: 'translateX(-50%)',
                                background: 'rgba(220, 38, 38, 0.95)',
                                color: 'white',
                                padding: '16px 24px',
                                borderRadius: '8px',
                                zIndex: 1000,
                                maxWidth: '80%',
                                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)'
                            }}>
                                <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>❌ Error</div>
                                <div style={{ fontSize: '14px' }}>{error}</div>
                                <div style={{ fontSize: '12px', marginTop: '8px', opacity: 0.8 }}>
                                    Check console for details
                                </div>
                            </div>
                        )}
                        
                        {!loading && !error && (
                            <div style={{
                                position: 'absolute',
                                top: '20px',
                                left: '20px',
                                background: 'rgba(34, 197, 94, 0.9)',
                                color: 'white',
                                padding: '8px 16px',
                                borderRadius: '6px',
                                fontSize: '12px',
                                zIndex: 1000,
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px',
                                boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                            }}>
                                ✅ Viewer Ready {showUi && '• Tweakpane Active'} {enableMaterialConfig && '• Material Config'}
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


threepipe_advanced_viewer = ThreepipeAdvancedViewer.create

class ViewerControls(rx.Component):
    """Controls for the Threepipe viewer."""
    
    tag = "ViewerControlsComponent"
    
    def add_imports(self) -> Dict[str, Any]:
        return {
            "react": ["useState"],
        }
    
    def add_custom_code(self) -> list[str]:
        return [
            """
            function ViewerControlsComponent() {
                const [orientation, setOrientation] = useState('+z');
                const [transformMode, setTransformMode] = useState('translate');
                const [message, setMessage] = useState('');
                
                const showMessage = (msg) => {
                    setMessage(msg);
                    setTimeout(() => setMessage(''), 2000);
                };
                
                const changeView = (newOrientation) => {
                    if (window.threepipeEditorView) {
                        window.threepipeEditorView.setOrientation(newOrientation);
                        setOrientation(newOrientation);
                        showMessage(`View: ${newOrientation}`);
                        console.log(`📐 View changed to ${newOrientation}`);
                    } else {
                        showMessage('Viewer not ready');
                    }
                };
                
                const resetView = () => {
                    if (window.threepipeViewer) {
                        window.threepipeViewer.scene.mainCamera.setCameraOptions({
                            position: [5, 5, 5],
                        });
                        showMessage('Camera reset');
                        console.log('📷 Camera reset');
                    }
                };
                
                const deselectAll = () => {
                    if (window.threepipePicking) {
                        window.threepipePicking.setSelectedObject(null);
                        showMessage('Deselected');
                        console.log('❌ Object deselected');
                    }
                };
                
                const toggleTransformMode = (mode) => {
                    if (window.threepipeTransformControls) {
                        window.threepipeTransformControls.setMode(mode);
                        setTransformMode(mode);
                        showMessage(`Mode: ${mode}`);
                        console.log(`🔧 Transform mode: ${mode}`);
                    }
                };
                
                const buttonStyle = {
                    padding: '8px 16px',
                    margin: '4px',
                    border: 'none',
                    borderRadius: '6px',
                    background: '#4a5568',
                    color: 'white',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: '500',
                    transition: 'all 0.2s',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                };
                
                const activeStyle = {
                    ...buttonStyle,
                    background: '#3182ce',
                    boxShadow: '0 2px 8px rgba(49, 130, 206, 0.4)'
                };
                
                return (
                    <div style={{
                        position: 'absolute',
                        top: '80px',
                        right: '20px',
                        zIndex: 1000,
                        background: 'rgba(0, 0, 0, 0.9)',
                        padding: '20px',
                        borderRadius: '12px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '12px',
                        minWidth: '280px',
                        maxWidth: '300px',
                        boxShadow: '0 8px 16px rgba(0,0,0,0.4)',
                        backdropFilter: 'blur(10px)'
                    }}>
                        <div style={{ 
                            color: 'white', 
                            fontSize: '18px', 
                            fontWeight: 'bold',
                            borderBottom: '2px solid #4a5568',
                            paddingBottom: '8px'
                        }}>
                            🎮 View Controls
                        </div>
                        
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                            {[
                                ['+z', 'Front'],
                                ['-z', 'Back'],
                                ['+x', 'Right'],
                                ['-x', 'Left'],
                                ['+y', 'Top'],
                                ['-y', 'Bottom']
                            ].map(([dir, label]) => (
                                <button 
                                    key={dir}
                                    style={orientation === dir ? activeStyle : buttonStyle}
                                    onClick={() => changeView(dir)}
                                    onMouseEnter={(e) => {
                                        if (orientation !== dir) e.target.style.background = '#2d3748';
                                    }}
                                    onMouseLeave={(e) => {
                                        if (orientation !== dir) e.target.style.background = '#4a5568';
                                    }}
                                >
                                    {label}
                                </button>
                            ))}
                        </div>
                        
                        <div style={{ 
                            borderTop: '1px solid #4a5568', 
                            paddingTop: '12px',
                            marginTop: '4px'
                        }}>
                            <div style={{ color: '#9ca3af', fontSize: '12px', marginBottom: '8px', fontWeight: 'bold' }}>
                                🔧 Transform Mode
                            </div>
                            <div style={{ display: 'flex', gap: '4px' }}>
                                {[
                                    ['translate', '↔️', 'Move'],
                                    ['rotate', '🔄', 'Rotate'],
                                    ['scale', '📏', 'Scale']
                                ].map(([mode, icon, label]) => (
                                    <button 
                                        key={mode}
                                        style={transformMode === mode ? activeStyle : {...buttonStyle, flex: 1, fontSize: '11px'}}
                                        onClick={() => toggleTransformMode(mode)}
                                        onMouseEnter={(e) => {
                                            if (transformMode !== mode) e.target.style.background = '#2d3748';
                                        }}
                                        onMouseLeave={(e) => {
                                            if (transformMode !== mode) e.target.style.background = '#4a5568';
                                        }}
                                        title={label}
                                    >
                                        {icon}
                                    </button>
                                ))}
                            </div>
                        </div>
                        
                        <div style={{ 
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '8px'
                        }}>
                            <button 
                                style={{...buttonStyle, background: '#3182ce', width: '100%'}}
                                onClick={resetView}
                                onMouseEnter={(e) => e.target.style.background = '#2563eb'}
                                onMouseLeave={(e) => e.target.style.background = '#3182ce'}
                            >
                                🔄 Reset Camera
                            </button>
                            <button 
                                style={{...buttonStyle, background: '#dc2626', width: '100%'}}
                                onClick={deselectAll}
                                onMouseEnter={(e) => e.target.style.background = '#b91c1c'}
                                onMouseLeave={(e) => e.target.style.background = '#dc2626'}
                            >
                                ✖️ Deselect Object
                            </button>
                        </div>
                        
                        {message && (
                            <div style={{
                                background: 'rgba(34, 197, 94, 0.9)',
                                color: 'white',
                                padding: '8px 12px',
                                borderRadius: '6px',
                                fontSize: '13px',
                                textAlign: 'center',
                                animation: 'fadeIn 0.3s'
                            }}>
                                ✓ {message}
                            </div>
                        )}
                        
                        <div style={{ 
                            color: '#9ca3af', 
                            fontSize: '11px', 
                            marginTop: '4px',
                            borderTop: '1px solid #4a5568',
                            paddingTop: '12px',
                            lineHeight: '1.6'
                        }}>
                            <div>💡 <strong>Click</strong> to select object</div>
                            <div>🎯 <strong>Drag gizmo</strong> to transform</div>
                            <div>🖱️ <strong>Drag canvas</strong> to orbit</div>
                            <div>🔍 <strong>Scroll</strong> to zoom</div>
                            <div>🎨 <strong>Right-click</strong> for material edit</div>
                            <div>🎛️ <strong>Tweakpane</strong> for textures</div>
                        </div>
                    </div>
                );
            }
            """
        ]

viewer_controls = ViewerControls.create

class MaterialPalette(rx.Component):
    """Material color palette for quick material changes."""
    
    tag = "MaterialPaletteComponent"
    
    def add_imports(self) -> Dict[str, Any]:
        return {
            "react": ["useState", "useEffect"],
        }
    
    def add_custom_code(self) -> list[str]:
        return [
            """
            function MaterialPaletteComponent() {
                const [materials, setMaterials] = useState([]);
                const [selectedMaterial, setSelectedMaterial] = useState(null);
                const [message, setMessage] = useState('');
                
                useEffect(() => {
                    // Update materials list when available
                    const interval = setInterval(() => {
                        if (window.threepipeMaterialsList && window.threepipeMaterialsList.length > 0) {
                            setMaterials(window.threepipeMaterialsList);
                            if (!selectedMaterial) {
                                setSelectedMaterial(window.threepipeMaterialsList[0]);
                            }
                            clearInterval(interval);
                        }
                    }, 500);
                    
                    return () => clearInterval(interval);
                }, []);
                
                const showMessage = (msg) => {
                    setMessage(msg);
                    setTimeout(() => setMessage(''), 2000);
                };
                
                const applyColor = (presetId, presetName) => {
                    if (!selectedMaterial) {
                        showMessage('No material selected');
                        return;
                    }
                    
                    if (window.applyMaterial) {
                        const success = window.applyMaterial(selectedMaterial, presetId);
                        if (success) {
                            showMessage(`${presetName} applied!`);
                        } else {
                            showMessage('Failed to apply');
                        }
                    }
                };
                
                const colors = [
                    { id: 'gold', name: 'Gold', color: '#FFD700' },
                    { id: 'silver', name: 'Silver', color: '#C0C0C0' },
                    { id: 'bronze', name: 'Bronze', color: '#CD7F32' },
                    { id: 'copper', name: 'Copper', color: '#B87333' },
                    { id: 'black', name: 'Black', color: '#1a1a1a' },
                    { id: 'white', name: 'White', color: '#ffffff' },
                    { id: 'red', name: 'Red', color: '#ff0000' },
                    { id: 'blue', name: 'Blue', color: '#0066ff' },
                    { id: 'green', name: 'Green', color: '#00ff00' },
                    { id: 'chrome', name: 'Chrome', color: '#e8e8e8' },
                ];
                
                if (materials.length === 0) return null;
                
                return (
                    <div style={{
                        position: 'absolute',
                        bottom: '20px',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        zIndex: 1000,
                        background: 'rgba(0, 0, 0, 0.95)',
                        padding: '20px',
                        borderRadius: '16px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '16px',
                        minWidth: '600px',
                        boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
                        backdropFilter: 'blur(10px)',
                        border: '1px solid rgba(255,255,255,0.1)'
                    }}>
                        <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center'
                        }}>
                            <div style={{ 
                                color: 'white', 
                                fontSize: '16px', 
                                fontWeight: 'bold',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px'
                            }}>
                                🎨 Material Palette
                            </div>
                            
                            {materials.length > 1 && (
                                <select
                                    value={selectedMaterial}
                                    onChange={(e) => setSelectedMaterial(e.target.value)}
                                    style={{
                                        padding: '6px 12px',
                                        borderRadius: '6px',
                                        background: '#2d3748',
                                        color: 'white',
                                        border: '1px solid #4a5568',
                                        fontSize: '13px',
                                        cursor: 'pointer'
                                    }}
                                >
                                    {materials.map(mat => (
                                        <option key={mat} value={mat}>{mat}</option>
                                    ))}
                                </select>
                            )}
                        </div>
                        
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(10, 1fr)',
                            gap: '12px'
                        }}>
                            {colors.map(color => (
                                <button
                                    key={color.id}
                                    onClick={() => applyColor(color.id, color.name)}
                                    title={color.name}
                                    style={{
                                        width: '48px',
                                        height: '48px',
                                        borderRadius: '8px',
                                        border: '2px solid rgba(255,255,255,0.2)',
                                        background: color.color,
                                        cursor: 'pointer',
                                        transition: 'all 0.2s',
                                        position: 'relative',
                                        boxShadow: '0 2px 8px rgba(0,0,0,0.3)'
                                    }}
                                    onMouseEnter={(e) => {
                                        e.target.style.transform = 'scale(1.1)';
                                        e.target.style.borderColor = 'white';
                                        e.target.style.boxShadow = '0 4px 16px rgba(255,255,255,0.3)';
                                    }}
                                    onMouseLeave={(e) => {
                                        e.target.style.transform = 'scale(1)';
                                        e.target.style.borderColor = 'rgba(255,255,255,0.2)';
                                        e.target.style.boxShadow = '0 2px 8px rgba(0,0,0,0.3)';
                                    }}
                                >
                                    <span style={{
                                        position: 'absolute',
                                        bottom: '-24px',
                                        left: '50%',
                                        transform: 'translateX(-50%)',
                                        fontSize: '10px',
                                        color: '#9ca3af',
                                        whiteSpace: 'nowrap',
                                        pointerEvents: 'none'
                                    }}>
                                        {color.name}
                                    </span>
                                </button>
                            ))}
                        </div>
                        
                        {message && (
                            <div style={{
                                background: 'rgba(34, 197, 94, 0.9)',
                                color: 'white',
                                padding: '8px 16px',
                                borderRadius: '6px',
                                fontSize: '13px',
                                textAlign: 'center',
                                fontWeight: '500'
                            }}>
                                ✓ {message}
                            </div>
                        )}
                        
                        <div style={{
                            color: '#9ca3af',
                            fontSize: '11px',
                            textAlign: 'center',
                            borderTop: '1px solid rgba(255,255,255,0.1)',
                            paddingTop: '12px'
                        }}>
                            💡 Click any color to apply • Select material from dropdown if multiple
                        </div>
                    </div>
                );
            }
            """
        ]

#material_palette = MaterialPalette.create

class ViewerState(rx.State):
    """State for the 3D viewer."""
    
    current_model: str = "https://samples.threepipe.org/demos/classic-watch.glb"
    show_ui: bool = True
    enable_material_config: bool = True
    
    def load_helmet(self):
        self.current_model = "https://samples.threepipe.org/minimal/DamagedHelmet/glTF/DamagedHelmet.gltf"
    
    def load_watch(self):
        self.current_model = "https://samples.threepipe.org/demos/classic-watch.glb"
    
    def load_chair(self):
        self.current_model = "/models/gaming_chair_pink.glb"
    
    def load_custom_url(self, url: str):
        """Load any 3D model from a URL"""
        self.current_model = url
    
    def toggle_ui(self):
        self.show_ui = not self.show_ui
    
    def toggle_material_config(self):
        self.enable_material_config = not self.enable_material_config

def index():
    return rx.fragment(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading("Material Configurator Viewer", size="7", color="white"),
                    rx.spacer(),
                    rx.hstack(
                        rx.button(
                            "⌚ Watch",
                            on_click=ViewerState.load_watch,
                            size="2",
                            variant="soft",
                            color_scheme="purple"
                        ),
                        rx.button(
                            "🪖 Helmet",
                            on_click=ViewerState.load_helmet,
                            size="2",
                            variant="soft",
                            color_scheme="blue"
                        ),
                        rx.button(
                            "🪑 Chair",
                            on_click=ViewerState.load_chair,
                            size="2",
                            variant="soft",
                            color_scheme="green"
                        ),
                        rx.button(
                            rx.cond(
                                ViewerState.show_ui,
                                "🔧 Hide UI",
                                "🔧 Show UI"
                            ),
                            on_click=ViewerState.toggle_ui,
                            size="2",
                            variant="outline",
                            color_scheme="gray"
                        ),
                        spacing="2",
                    ),
                    align="center",
                    width="100%",
                    padding="0.5rem 2rem",
                ),
                
                # Add URL input for custom models
                rx.hstack(
                    rx.text("Load from URL:", color="gray.400", size="2"),
                    rx.input(
                        placeholder="https://example.com/model.glb",
                        on_blur=lambda v: ViewerState.load_custom_url(v),
                        size="2",
                        width="400px",
                    ),
                    rx.badge("💡 Tip: Works with ANY .glb/.gltf file!", color_scheme="green", size="1"),
                    spacing="3",
                    padding="0 2rem",
                    padding_bottom="0.5rem",
                ),
                
                spacing="2",
            ),
            bg="gray.900",
            border_bottom="1px solid rgba(255, 255, 255, 0.1)",
        ),
        
        rx.box(
            threepipe_advanced_viewer(
                model_url=ViewerState.current_model,
                show_ui=ViewerState.show_ui,
                enable_material_config=ViewerState.enable_material_config,
                width="100%",
                height="calc(100vh - 120px)"
            ),
            viewer_controls(),
            position="relative",
        ),
        
        width="100%",
        height="100vh",
        bg="gray.900",
        overflow="hidden",
    )