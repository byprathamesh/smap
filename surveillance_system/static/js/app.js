/**
 * WatchHer AI Surveillance System - JavaScript Application
 * Advanced webcam integration with real-time AI processing and dynamic map visualization
 * Strict Color Scheme: BLACK, WHITE, GREY, RED, GREEN only
 */

class WatchHerApp {
    constructor() {
        // Core system state
        this.isProcessing = false;
        this.webcamStream = null;
        this.eventSource = null;
        this.processingInterval = null;
        this.map = null;
        this.roadSegments = [];
        
        // DOM elements
        this.elements = {};
        
        // Configuration
        this.config = {
            processFrameInterval: 200,  // Process every 200ms for ~5 FPS
            mapUpdateInterval: 1000,    // Update map every 1 second
            webcamConstraints: {
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    frameRate: { ideal: 30 }
                },
                audio: false
            },
            // Strict color scheme
            colors: {
                black: '#000000',
                white: '#FFFFFF',
                grey: '#808080',
                red: '#FF0000',
                green: '#00FF00'
            }
        };
        
        // Performance tracking
        this.stats = {
            framesProcessed: 0,
            lastFpsUpdate: Date.now(),
            currentFps: 0
        };
    }
    
    /**
     * Initialize the application
     */
    async initialize() {
        console.log('[WatchHer] Initializing AI Surveillance System...');
        
        try {
            this.bindDOMElements();
            this.setupEventListeners();
            this.initializeMap();
            this.updateSystemStatus('inactive', 'System Ready');
            
            console.log('[WatchHer] System initialized successfully');
            
        } catch (error) {
            console.error('[WatchHer] Initialization failed:', error);
            this.showError('System initialization failed: ' + error.message);
        }
    }
    
    /**
     * Bind all DOM elements
     */
    bindDOMElements() {
        this.elements = {
            // Buttons
            startBtn: document.getElementById('startBtn'),
            stopBtn: document.getElementById('stopBtn'),
            
            // Status indicators
            systemStatus: document.getElementById('systemStatus'),
            statusIndicator: document.getElementById('statusIndicator'),
            statusText: document.getElementById('statusText'),
            processingStatus: document.getElementById('processingStatus'),
            cameraStatus: document.getElementById('cameraStatus'),
            
            // Video elements
            permissionNotice: document.getElementById('permissionNotice'),
            webcamVideo: document.getElementById('webcamVideo'),
            processedVideo: document.getElementById('processedVideo'),
            captureCanvas: document.getElementById('captureCanvas'),
            
            // Stats display
            fpsDisplay: document.getElementById('fpsDisplay'),
            peopleCount: document.getElementById('peopleCount'),
            
            // Risk assessment
            riskScore: document.getElementById('riskScore'),
            threatLevel: document.getElementById('threatLevel'),
            riskProgress: document.getElementById('riskProgress'),
            
            // Footer
            timestamp: document.getElementById('timestamp'),
            performanceInfo: document.getElementById('performanceInfo')
        };
        
        // Verify all elements exist
        for (const [key, element] of Object.entries(this.elements)) {
            if (!element) {
                throw new Error(`Required DOM element not found: ${key}`);
            }
        }
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Control buttons
        this.elements.startBtn.addEventListener('click', () => this.startAnalysis());
        this.elements.stopBtn.addEventListener('click', () => this.stopAnalysis());
        
        // Window events
        window.addEventListener('beforeunload', () => this.cleanup());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                if (!this.isProcessing) {
                    this.startAnalysis();
                } else {
                    this.stopAnalysis();
                }
            }
        });
    }
    
    /**
     * Initialize Leaflet map with Delhi road network simulation
     */
    initializeMap() {
        try {
            // Delhi coordinates
            const delhiCenter = [28.6139, 77.2090];
            
            // Initialize map with custom styling
            this.map = L.map('riskMap', {
                zoomControl: true,
                attributionControl: false
            }).setView(delhiCenter, 12);
            
            // Use dark tiles for strict color scheme
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 18,
                className: 'map-tiles'
            }).addTo(this.map);
            
            // Create simulated road network
            this.createRoadNetwork();
            
            console.log('[WatchHer] Map initialized successfully');
            
        } catch (error) {
            console.error('[WatchHer] Map initialization failed:', error);
            throw error;
        }
    }
    
    /**
     * Create simulated road network for Delhi
     */
    createRoadNetwork() {
        // Simulated road segments with Delhi-like coordinates
        const roadSegments = [
            {
                id: 'connaught-place',
                name: 'Connaught Place',
                coords: [[28.6315, 77.2167], [28.6289, 77.2156]],
                riskLevel: 0
            },
            {
                id: 'india-gate',
                name: 'India Gate Area',
                coords: [[28.6129, 77.2295], [28.6139, 77.2273]],
                riskLevel: 0
            },
            {
                id: 'karol-bagh',
                name: 'Karol Bagh Market',
                coords: [[28.6519, 77.1909], [28.6489, 77.1889]],
                riskLevel: 0
            },
            {
                id: 'chandni-chowk',
                name: 'Chandni Chowk',
                coords: [[28.6506, 77.2334], [28.6489, 77.2298]],
                riskLevel: 0
            },
            {
                id: 'lajpat-nagar',
                name: 'Lajpat Nagar',
                coords: [[28.5656, 77.2431], [28.5639, 77.2456]],
                riskLevel: 0
            }
        ];
        
        // Create polylines for each road segment
        this.roadSegments = roadSegments.map(segment => {
            const polyline = L.polyline(segment.coords, {
                color: this.config.colors.green,
                weight: 6,
                opacity: 0.8
            }).addTo(this.map);
            
            // Add popup with area name
            polyline.bindPopup(`
                <div style="color: black; font-weight: bold;">
                    ${segment.name}<br>
                    <span style="color: green;">Risk Level: SAFE</span>
                </div>
            `);
            
            return {
                ...segment,
                polyline: polyline
            };
        });
    }
    
    /**
     * Start surveillance analysis
     */
    async startAnalysis() {
        console.log('[WatchHer] Starting surveillance analysis...');
        
        try {
            // Update UI state
            this.elements.startBtn.disabled = true;
            this.elements.startBtn.classList.add('loading');
            this.updateSystemStatus('connecting', 'Requesting camera access...');
            
            // Request webcam access
            await this.initializeWebcam();
            
            // Start backend analysis
            const response = await fetch('/start_analysis', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) {
                throw new Error(`Backend start failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('[WatchHer] Backend analysis started:', result);
            
            // Start processing loop
            this.startProcessingLoop();
            
            // Start real-time updates
            this.startRealTimeUpdates();
            
            // Update UI
            this.isProcessing = true;
            this.elements.startBtn.disabled = true;
            this.elements.stopBtn.disabled = false;
            this.elements.startBtn.classList.remove('loading');
            this.updateSystemStatus('active', 'Analysis Active');
            this.updateCameraStatus('connected');
            this.updateProcessingStatus('active');
            
            console.log('[WatchHer] Surveillance analysis started successfully');
            
        } catch (error) {
            console.error('[WatchHer] Failed to start analysis:', error);
            this.showError('Failed to start analysis: ' + error.message);
            this.resetUI();
        }
    }
    
    /**
     * Stop surveillance analysis
     */
    async stopAnalysis() {
        console.log('[WatchHer] Stopping surveillance analysis...');
        
        try {
            // Stop processing
            this.isProcessing = false;
            if (this.processingInterval) {
                clearInterval(this.processingInterval);
                this.processingInterval = null;
            }
            
            // Stop real-time updates
            if (this.eventSource) {
                this.eventSource.close();
                this.eventSource = null;
            }
            
            // Stop webcam
            if (this.webcamStream) {
                this.webcamStream.getTracks().forEach(track => track.stop());
                this.webcamStream = null;
            }
            
            // Stop backend analysis
            const response = await fetch('/stop_analysis', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (response.ok) {
                console.log('[WatchHer] Backend analysis stopped');
            }
            
            // Reset UI
            this.resetUI();
            this.updateSystemStatus('inactive', 'System Ready');
            
            console.log('[WatchHer] Surveillance analysis stopped successfully');
            
        } catch (error) {
            console.error('[WatchHer] Error stopping analysis:', error);
            this.resetUI();
        }
    }
    
    /**
     * Initialize webcam access
     */
    async initializeWebcam() {
        try {
            console.log('[WatchHer] Requesting webcam access...');
            
            // Check if getUserMedia is available
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Webcam access not supported by this browser');
            }
            
            // Request webcam access
            this.webcamStream = await navigator.mediaDevices.getUserMedia(this.config.webcamConstraints);
            
            // Attach stream to video element
            this.elements.webcamVideo.srcObject = this.webcamStream;
            
            // Wait for video to be ready
            await new Promise((resolve, reject) => {
                this.elements.webcamVideo.onloadedmetadata = resolve;
                this.elements.webcamVideo.onerror = reject;
                setTimeout(reject, 5000); // 5 second timeout
            });
            
            // Hide permission notice and show video
            this.elements.permissionNotice.style.display = 'none';
            this.elements.processedVideo.style.display = 'block';
            
            console.log('[WatchHer] Webcam initialized successfully');
            
        } catch (error) {
            console.error('[WatchHer] Webcam initialization failed:', error);
            
            if (error.name === 'NotAllowedError') {
                throw new Error('Camera access denied. Please allow camera access and try again.');
            } else if (error.name === 'NotFoundError') {
                throw new Error('No camera found. Please connect a camera and try again.');
            } else {
                throw new Error('Camera initialization failed: ' + error.message);
            }
        }
    }
    
    /**
     * Start processing loop for frame analysis
     */
    startProcessingLoop() {
        if (this.processingInterval) {
            clearInterval(this.processingInterval);
        }
        
        this.processingInterval = setInterval(async () => {
            if (this.isProcessing && this.webcamStream) {
                await this.processFrame();
            }
        }, this.config.processFrameInterval);
        
        console.log('[WatchHer] Processing loop started');
    }
    
    /**
     * Process a single frame
     */
    async processFrame() {
        try {
            // Capture frame from webcam
            const frameData = this.captureFrame();
            
            if (!frameData) return;
            
            // Send frame to backend for processing
            const response = await fetch('/process_frame', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ frame: frameData })
            });
            
            if (!response.ok) {
                console.warn('[WatchHer] Frame processing failed:', response.statusText);
                return;
            }
            
            const result = await response.json();
            
            // Update processed video display
            if (result.processed_frame) {
                this.elements.processedVideo.src = result.processed_frame;
            }
            
            // Update stats
            this.updateStats(result);
            
        } catch (error) {
            console.error('[WatchHer] Frame processing error:', error);
        }
    }
    
    /**
     * Capture frame from webcam video
     */
    captureFrame() {
        try {
            const video = this.elements.webcamVideo;
            const canvas = this.elements.captureCanvas;
            
            if (video.readyState !== 4) return null;
            
            // Set canvas dimensions to match video
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            
            // Draw video frame to canvas
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // Convert to base64 JPEG
            return canvas.toDataURL('image/jpeg', 0.8);
            
        } catch (error) {
            console.error('[WatchHer] Frame capture failed:', error);
            return null;
        }
    }
    
    /**
     * Start real-time updates via Server-Sent Events
     */
    startRealTimeUpdates() {
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        this.eventSource = new EventSource('/risk_score_stream');
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.updateRealTimeData(data);
            } catch (error) {
                console.error('[WatchHer] SSE data parsing error:', error);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('[WatchHer] SSE connection error:', error);
        };
        
        console.log('[WatchHer] Real-time updates started');
    }
    
    /**
     * Update UI with real-time data
     */
    updateRealTimeData(data) {
        // Update risk score
        this.updateRiskDisplay(data.risk_score);
        
        // Update FPS
        this.elements.fpsDisplay.textContent = data.fps.toFixed(1);
        
        // Update people count
        this.elements.peopleCount.textContent = data.detection_count;
        
        // Update timestamp
        this.elements.timestamp.textContent = `Timestamp: ${new Date(data.timestamp).toLocaleTimeString()}`;
        
        // Update map colors
        if (data.map_color) {
            this.updateMapColors(data.risk_score);
        }
        
        // Update performance info
        this.elements.performanceInfo.textContent = `Threat Level: ${data.threat_level} | Processing: ${data.status}`;
    }
    
    /**
     * Update risk score display
     */
    updateRiskDisplay(riskScore) {
        // Update score value
        this.elements.riskScore.textContent = riskScore.toFixed(1);
        
        // Update threat level and colors
        let threatLevel = 'SAFE';
        let riskClass = 'risk-safe';
        let threatClass = 'threat-safe';
        let progressClass = 'progress-safe';
        
        if (riskScore >= 80) {
            threatLevel = 'CRITICAL';
            riskClass = 'risk-high';
            threatClass = 'threat-critical';
            progressClass = 'progress-critical';
        } else if (riskScore >= 60) {
            threatLevel = 'HIGH';
            riskClass = 'risk-high';
            threatClass = 'threat-high';
            progressClass = 'progress-high';
        } else if (riskScore >= 30) {
            threatLevel = 'MODERATE';
            riskClass = 'risk-moderate';
            threatClass = 'threat-moderate';
            progressClass = 'progress-moderate';
        } else if (riskScore >= 15) {
            threatLevel = 'LOW';
            riskClass = 'risk-low';
            threatClass = 'threat-low';
            progressClass = 'progress-low';
        }
        
        // Apply classes
        this.elements.riskScore.className = `risk-score ${riskClass}`;
        this.elements.threatLevel.className = `threat-value ${threatClass}`;
        this.elements.threatLevel.textContent = threatLevel;
        
        // Update progress bar
        this.elements.riskProgress.className = `progress-fill ${progressClass}`;
        this.elements.riskProgress.style.width = `${Math.min(riskScore, 100)}%`;
    }
    
    /**
     * Update map colors based on risk score
     */
    updateMapColors(riskScore) {
        const color = this.getRiskColor(riskScore);
        
        this.roadSegments.forEach(segment => {
            segment.polyline.setStyle({ color: color });
            
            // Update popup content
            const threatLevel = this.getThreatLevel(riskScore);
            segment.polyline.setPopupContent(`
                <div style="color: black; font-weight: bold;">
                    ${segment.name}<br>
                    <span style="color: ${color};">Risk Level: ${threatLevel}</span>
                </div>
            `);
        });
    }
    
    /**
     * Get risk color based on score
     */
    getRiskColor(riskScore) {
        if (riskScore >= 70) return this.config.colors.red;
        if (riskScore >= 40) return this.config.colors.grey;
        if (riskScore >= 15) return this.config.colors.white;
        return this.config.colors.green;
    }
    
    /**
     * Get threat level text
     */
    getThreatLevel(riskScore) {
        if (riskScore >= 80) return 'CRITICAL';
        if (riskScore >= 60) return 'HIGH';
        if (riskScore >= 30) return 'MODERATE';
        if (riskScore >= 15) return 'LOW';
        return 'SAFE';
    }
    
    /**
     * Update stats display
     */
    updateStats(result) {
        this.stats.framesProcessed++;
        
        // Calculate FPS
        const now = Date.now();
        if (now - this.stats.lastFpsUpdate >= 1000) {
            this.stats.currentFps = this.stats.framesProcessed / ((now - this.stats.lastFpsUpdate) / 1000);
            this.stats.lastFpsUpdate = now;
            this.stats.framesProcessed = 0;
        }
    }
    
    /**
     * Update system status
     */
    updateSystemStatus(status, message) {
        this.elements.statusText.textContent = message;
        
        // Update status indicator
        this.elements.statusIndicator.className = 'status-indicator';
        
        switch (status) {
            case 'active':
                this.elements.statusIndicator.classList.add('active');
                break;
            case 'error':
                this.elements.statusIndicator.classList.add('error');
                break;
            default:
                // inactive - keep default grey
                break;
        }
    }
    
    /**
     * Update camera status
     */
    updateCameraStatus(status) {
        const element = this.elements.cameraStatus;
        
        switch (status) {
            case 'connected':
                element.textContent = 'Connected';
                element.className = 'status-active';
                break;
            case 'error':
                element.textContent = 'Error';
                element.className = 'status-error';
                break;
            default:
                element.textContent = 'Disconnected';
                element.className = 'status-inactive';
                break;
        }
    }
    
    /**
     * Update processing status
     */
    updateProcessingStatus(status) {
        const element = this.elements.processingStatus;
        
        switch (status) {
            case 'active':
                element.textContent = 'Active';
                element.className = 'status-active';
                break;
            case 'error':
                element.textContent = 'Error';
                element.className = 'status-error';
                break;
            default:
                element.textContent = 'Inactive';
                element.className = 'status-inactive';
                break;
        }
    }
    
    /**
     * Reset UI to initial state
     */
    resetUI() {
        this.elements.startBtn.disabled = false;
        this.elements.stopBtn.disabled = true;
        this.elements.startBtn.classList.remove('loading');
        
        this.updateCameraStatus('disconnected');
        this.updateProcessingStatus('inactive');
        
        // Reset video display
        this.elements.permissionNotice.style.display = 'block';
        this.elements.processedVideo.style.display = 'none';
        this.elements.processedVideo.src = '';
        
        // Reset stats
        this.elements.fpsDisplay.textContent = '0.0';
        this.elements.peopleCount.textContent = '0';
        
        // Reset risk display
        this.updateRiskDisplay(0);
        
        // Reset map colors
        this.updateMapColors(0);
    }
    
    /**
     * Show error message
     */
    showError(message) {
        console.error('[WatchHer] Error:', message);
        alert('WatchHer Error: ' + message);
    }
    
    /**
     * Cleanup resources
     */
    cleanup() {
        console.log('[WatchHer] Cleaning up resources...');
        
        if (this.isProcessing) {
            this.stopAnalysis();
        }
    }
}

// Export for use
window.WatchHerApp = WatchHerApp; 