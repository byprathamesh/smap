/**
 * WatchHer AI Surveillance System - Enhanced JavaScript Application
 * Advanced client-side webcam integration with professional UI controls
 * Real-time AI processing and dynamic map visualization
 */

class WatchHerApp {
    constructor() {
        // Core state
        this.isProcessing = false;
        this.mediaStream = null;
        this.processingInterval = null;
        this.eventSource = null;
        this.map = null;
        this.roadSegments = [];
        
        // Configuration
        this.config = {
            frameProcessingInterval: 200, // 200ms = ~5 FPS
            reconnectDelay: 3000,
            maxReconnectAttempts: 5,
            videoConstraints: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                frameRate: { ideal: 30 }
            }
        };
        
        // State tracking
        this.reconnectAttempts = 0;
        this.sourceType = 'webcam';
        this.lastFrameTime = 0;
        this.performanceStats = {
            framesProcessed: 0,
            totalProcessingTime: 0,
            averageProcessingTime: 0
        };
        
        // DOM elements (will be set in initialize())
        this.elements = {};
    }
    
    /**
     * Initialize the application
     */
    initialize() {
        console.log('[WatchHer] Initializing application...');
        
        this.initializeElements();
        this.setupEventListeners();
        this.initializeMap();
        this.checkSystemCapabilities();
        
        console.log('[WatchHer] Application initialized successfully');
    }
    
    /**
     * Cache DOM elements for performance
     */
    initializeElements() {
        this.elements = {
            // Source selection
            sourceRadios: document.querySelectorAll('input[name="sourceType"]'),
            videoPathContainer: document.getElementById('videoPathContainer'),
            videoPathInput: document.getElementById('videoPathInput'),
            validatePathBtn: document.getElementById('validatePathBtn'),
            pathValidation: document.getElementById('pathValidation'),
            
            // Control buttons
            startBtn: document.getElementById('startAnalysisBtn'),
            stopBtn: document.getElementById('stopAnalysisBtn'),
            resetMapBtn: document.getElementById('resetMapBtn'),
            
            // Video elements
            liveCameraFeed: document.getElementById('liveCameraFeed'),
            hiddenCanvas: document.getElementById('hiddenCanvas'),
            processedDisplay: document.getElementById('processedDisplay'),
            permissionNotice: document.getElementById('permissionNotice'),
            
            // Status displays
            systemStatus: document.getElementById('systemStatus'),
            statusIndicator: document.getElementById('statusIndicator'),
            statusText: document.getElementById('statusText'),
            processingStatus: document.getElementById('processingStatus'),
            inputSourceStatus: document.getElementById('inputSourceStatus'),
            
            // Performance displays
            fpsDisplay: document.getElementById('fpsDisplay'),
            peopleCount: document.getElementById('peopleCount'),
            sourceDisplay: document.getElementById('sourceDisplay'),
            
            // Risk assessment
            riskScore: document.getElementById('riskScore'),
            threatLevel: document.getElementById('threatLevel'),
            riskProgress: document.getElementById('riskProgress'),
            detectionCount: document.getElementById('detectionCount'),
            processingFps: document.getElementById('processingFps'),
            
            // Footer
            timestamp: document.getElementById('timestamp'),
            performanceInfo: document.getElementById('performanceInfo')
        };
        
        // Validate all required elements exist
        const missingElements = Object.entries(this.elements)
            .filter(([key, element]) => !element)
            .map(([key]) => key);
            
        if (missingElements.length > 0) {
            console.error('[WatchHer] Missing DOM elements:', missingElements);
        }
    }
    
    /**
     * Set up all event listeners
     */
    setupEventListeners() {
        // Source selection
        this.elements.sourceRadios.forEach(radio => {
            radio.addEventListener('change', (e) => this.handleSourceTypeChange(e));
        });
        
        // Video path validation
        if (this.elements.validatePathBtn) {
            this.elements.validatePathBtn.addEventListener('click', () => this.validateVideoPath());
        }
        
        if (this.elements.videoPathInput) {
            this.elements.videoPathInput.addEventListener('input', () => this.clearPathValidation());
        }
        
        // Control buttons
        if (this.elements.startBtn) {
            this.elements.startBtn.addEventListener('click', () => this.startAnalysis());
        }
        
        if (this.elements.stopBtn) {
            this.elements.stopBtn.addEventListener('click', () => this.stopAnalysis());
        }
        
        if (this.elements.resetMapBtn) {
            this.elements.resetMapBtn.addEventListener('click', () => this.resetMapView());
        }
        
        // Window events
        window.addEventListener('beforeunload', () => this.cleanup());
        window.addEventListener('focus', () => this.handleWindowFocus());
        window.addEventListener('blur', () => this.handleWindowBlur());
    }
    
    /**
     * Handle source type radio button changes
     */
    handleSourceTypeChange(event) {
        this.sourceType = event.target.value;
        
        if (this.sourceType === 'video_file') {
            this.elements.videoPathContainer.style.display = 'block';
            this.elements.permissionNotice.style.display = 'none';
        } else {
            this.elements.videoPathContainer.style.display = 'none';
            this.elements.permissionNotice.style.display = 'block';
            this.clearPathValidation();
        }
        
        this.updateSourceDisplay();
        console.log(`[WatchHer] Source type changed to: ${this.sourceType}`);
    }
    
    /**
     * Validate video file path
     */
    async validateVideoPath() {
        const path = this.elements.videoPathInput.value.trim();
        
        if (!path) {
            this.showPathValidation('Please enter a video file path', 'error');
            return;
        }
        
        try {
            this.elements.validatePathBtn.textContent = 'Validating...';
            this.elements.validatePathBtn.disabled = true;
            
            const response = await fetch('/validate_video_path', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ video_path: path })
            });
            
            const result = await response.json();
            
            if (result.valid) {
                this.showPathValidation(result.message, 'success');
            } else {
                this.showPathValidation(result.message, 'error');
            }
            
        } catch (error) {
            console.error('[WatchHer] Path validation error:', error);
            this.showPathValidation('Failed to validate path', 'error');
        } finally {
            this.elements.validatePathBtn.textContent = 'Validate';
            this.elements.validatePathBtn.disabled = false;
        }
    }
    
    /**
     * Show path validation message
     */
    showPathValidation(message, type) {
        if (this.elements.pathValidation) {
            this.elements.pathValidation.textContent = message;
            this.elements.pathValidation.className = `validation-message ${type}`;
        }
    }
    
    /**
     * Clear path validation message
     */
    clearPathValidation() {
        if (this.elements.pathValidation) {
            this.elements.pathValidation.className = 'validation-message';
            this.elements.pathValidation.textContent = '';
        }
    }
    
    /**
     * Start analysis based on selected source
     */
    async startAnalysis() {
        if (this.isProcessing) {
            console.log('[WatchHer] Analysis already running');
            return;
        }
        
        try {
            this.setButtonStates(true);
            this.updateSystemStatus('starting', 'Starting analysis...');
            
            if (this.sourceType === 'webcam') {
                await this.startWebcamAnalysis();
            } else if (this.sourceType === 'video_file') {
                await this.startVideoFileAnalysis();
            }
            
        } catch (error) {
            console.error('[WatchHer] Failed to start analysis:', error);
            this.updateSystemStatus('error', `Failed to start: ${error.message}`);
            this.setButtonStates(false);
        }
    }
    
    /**
     * Start webcam analysis with getUserMedia
     */
    async startWebcamAnalysis() {
        console.log('[WatchHer] Starting webcam analysis...');
        
        try {
            // Request webcam access
            this.updateSystemStatus('requesting', 'Requesting camera access...');
            
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                video: this.config.videoConstraints,
                audio: false
            });
            
            console.log('[WatchHer] Camera access granted');
            
            // Set up video element
            this.elements.liveCameraFeed.srcObject = this.mediaStream;
            
            // Wait for video to be ready
            await new Promise((resolve, reject) => {
                this.elements.liveCameraFeed.onloadedmetadata = resolve;
                this.elements.liveCameraFeed.onerror = reject;
                setTimeout(() => reject(new Error('Video load timeout')), 5000);
            });
            
            // Initialize backend
            const response = await fetch('/start_analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    source_type: 'webcam'
                })
            });
            
            if (!response.ok) {
                throw new Error(`Backend initialization failed: ${response.status}`);
            }
            
            // Start frame processing
            this.startFrameProcessing();
            this.startEventStream();
            
            this.isProcessing = true;
            this.updateSystemStatus('active', 'Live webcam analysis active');
            this.elements.permissionNotice.style.display = 'none';
            
            console.log('[WatchHer] Webcam analysis started successfully');
            
        } catch (error) {
            console.error('[WatchHer] Webcam analysis failed:', error);
            this.cleanup();
            throw error;
        }
    }
    
    /**
     * Start video file analysis
     */
    async startVideoFileAnalysis() {
        const videoPath = this.elements.videoPathInput.value.trim();
        
        if (!videoPath) {
            throw new Error('Please enter a video file path');
        }
        
        console.log(`[WatchHer] Starting video file analysis: ${videoPath}`);
        
        try {
            this.updateSystemStatus('starting', 'Initializing video file...');
            
            // Initialize backend for video file
            const response = await fetch('/start_analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    source_type: 'video_file',
                    video_path: videoPath
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `Server error: ${response.status}`);
            }
            
            // Set video feed source to server stream
            this.elements.processedDisplay.src = '/video_feed_stream';
            
            // Start event stream for updates
            this.startEventStream();
            
            this.isProcessing = true;
            this.updateSystemStatus('active', `Video file analysis active: ${videoPath}`);
            this.elements.permissionNotice.style.display = 'none';
            
            console.log('[WatchHer] Video file analysis started successfully');
            
        } catch (error) {
            console.error('[WatchHer] Video file analysis failed:', error);
            throw error;
        }
    }
    
    /**
     * Start frame processing loop for webcam
     */
    startFrameProcessing() {
        if (this.processingInterval) return;
        
        console.log('[WatchHer] Starting frame processing loop');
        
        this.processingInterval = setInterval(async () => {
            try {
                await this.processFrame();
            } catch (error) {
                console.error('[WatchHer] Frame processing error:', error);
            }
        }, this.config.frameProcessingInterval);
    }
    
    /**
     * Process a single frame from webcam
     */
    async processFrame() {
        if (!this.mediaStream || !this.elements.liveCameraFeed.videoWidth) {
            return;
        }
        
        const startTime = performance.now();
        
        try {
            // Capture frame to canvas
            const canvas = this.elements.hiddenCanvas;
            const ctx = canvas.getContext('2d');
            
            canvas.width = this.elements.liveCameraFeed.videoWidth;
            canvas.height = this.elements.liveCameraFeed.videoHeight;
            
            ctx.drawImage(this.elements.liveCameraFeed, 0, 0);
            
            // Convert to base64
            const frameData = canvas.toDataURL('image/jpeg', 0.8);
            
            // Send to backend for processing
            const response = await fetch('/process_live_frame', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    frame: frameData
                })
            });
            
            if (!response.ok) {
                throw new Error(`Processing failed: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.status === 'success') {
                // Update processed video display
                this.elements.processedDisplay.src = result.processed_frame;
                
                // Update performance stats
                const processingTime = performance.now() - startTime;
                this.updatePerformanceStats(processingTime);
            }
            
        } catch (error) {
            console.error('[WatchHer] Frame processing error:', error);
        }
    }
    
    /**
     * Start Server-Sent Events stream
     */
    startEventStream() {
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        console.log('[WatchHer] Starting event stream...');
        
        this.eventSource = new EventSource('/risk_score_stream');
        
        this.eventSource.onopen = () => {
            console.log('[WatchHer] Event stream connected');
            this.reconnectAttempts = 0;
        };
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.updateDisplays(data);
            } catch (error) {
                console.error('[WatchHer] Event data parsing error:', error);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('[WatchHer] Event stream error:', error);
            this.handleEventStreamError();
        };
    }
    
    /**
     * Handle event stream errors with reconnection
     */
    handleEventStreamError() {
        if (this.reconnectAttempts < this.config.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`[WatchHer] Reconnecting event stream (attempt ${this.reconnectAttempts})...`);
            
            setTimeout(() => {
                if (this.isProcessing) {
                    this.startEventStream();
                }
            }, this.config.reconnectDelay);
        } else {
            console.error('[WatchHer] Max reconnection attempts reached');
            this.updateSystemStatus('error', 'Connection lost - please restart');
        }
    }
    
    /**
     * Update all display elements with new data
     */
    updateDisplays(data) {
        // Risk score and threat level
        if (this.elements.riskScore) {
            this.elements.riskScore.textContent = data.risk_score.toFixed(1);
            this.updateRiskScoreClass(data.risk_score);
        }
        
        if (this.elements.threatLevel) {
            this.elements.threatLevel.textContent = data.threat_level;
            this.elements.threatLevel.className = `threat-value threat-${data.threat_level.toLowerCase()}`;
        }
        
        // Progress bar
        if (this.elements.riskProgress) {
            const progressWidth = Math.min(data.risk_score, 100);
            this.elements.riskProgress.style.width = `${progressWidth}%`;
            this.updateProgressClass(data.risk_score);
        }
        
        // Performance stats
        if (this.elements.fpsDisplay) {
            this.elements.fpsDisplay.textContent = data.fps.toFixed(1);
        }
        
        if (this.elements.peopleCount) {
            this.elements.peopleCount.textContent = data.detection_count;
        }
        
        if (this.elements.detectionCount) {
            this.elements.detectionCount.textContent = data.detection_count;
        }
        
        if (this.elements.processingFps) {
            this.elements.processingFps.textContent = data.fps.toFixed(1);
        }
        
        // Update map colors
        this.updateMapColors(data.risk_score);
        
        // Update timestamp
        if (this.elements.timestamp) {
            const timestamp = new Date(data.timestamp).toLocaleTimeString();
            this.elements.timestamp.textContent = `Updated: ${timestamp}`;
        }
    }
    
    /**
     * Update risk score styling based on value
     */
    updateRiskScoreClass(score) {
        if (!this.elements.riskScore) return;
        
        this.elements.riskScore.className = 'risk-score';
        
        if (score >= 80) {
            this.elements.riskScore.classList.add('risk-critical');
        } else if (score >= 60) {
            this.elements.riskScore.classList.add('risk-high');
        } else if (score >= 30) {
            this.elements.riskScore.classList.add('risk-moderate');
        } else if (score >= 10) {
            this.elements.riskScore.classList.add('risk-low');
        }
    }
    
    /**
     * Update progress bar styling
     */
    updateProgressClass(score) {
        if (!this.elements.riskProgress) return;
        
        this.elements.riskProgress.className = 'progress-fill';
        
        if (score >= 80) {
            this.elements.riskProgress.classList.add('progress-critical');
        } else if (score >= 60) {
            this.elements.riskProgress.classList.add('progress-high');
        } else if (score >= 30) {
            this.elements.riskProgress.classList.add('progress-moderate');
        } else if (score >= 10) {
            this.elements.riskProgress.classList.add('progress-low');
        } else {
            this.elements.riskProgress.classList.add('progress-safe');
        }
    }
    
    /**
     * Stop analysis and cleanup
     */
    async stopAnalysis() {
        console.log('[WatchHer] Stopping analysis...');
        
        try {
            this.updateSystemStatus('stopping', 'Stopping analysis...');
            
            // Stop backend processing
            await fetch('/stop_analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            // Cleanup resources
            this.cleanup();
            
            this.updateSystemStatus('inactive', 'Analysis stopped');
            this.setButtonStates(false);
            
            // Reset displays
            this.resetDisplays();
            
            console.log('[WatchHer] Analysis stopped successfully');
            
        } catch (error) {
            console.error('[WatchHer] Error stopping analysis:', error);
            this.updateSystemStatus('error', 'Error stopping analysis');
        }
    }
    
    /**
     * Cleanup all resources
     */
    cleanup() {
        this.isProcessing = false;
        
        // Stop frame processing
        if (this.processingInterval) {
            clearInterval(this.processingInterval);
            this.processingInterval = null;
        }
        
        // Close event stream
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        
        // Stop media stream
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }
        
        // Reset video elements
        if (this.elements.liveCameraFeed) {
            this.elements.liveCameraFeed.srcObject = null;
        }
        
        console.log('[WatchHer] Resources cleaned up');
    }
    
    /**
     * Reset display elements to initial state
     */
    resetDisplays() {
        if (this.elements.riskScore) {
            this.elements.riskScore.textContent = '0.0';
            this.elements.riskScore.className = 'risk-score';
        }
        
        if (this.elements.threatLevel) {
            this.elements.threatLevel.textContent = 'SAFE';
            this.elements.threatLevel.className = 'threat-value threat-safe';
        }
        
        if (this.elements.riskProgress) {
            this.elements.riskProgress.style.width = '0%';
            this.elements.riskProgress.className = 'progress-fill progress-safe';
        }
        
        if (this.elements.fpsDisplay) {
            this.elements.fpsDisplay.textContent = '0.0';
        }
        
        if (this.elements.peopleCount) {
            this.elements.peopleCount.textContent = '0';
        }
        
        if (this.elements.detectionCount) {
            this.elements.detectionCount.textContent = '0';
        }
        
        if (this.elements.processingFps) {
            this.elements.processingFps.textContent = '0.0';
        }
        
        if (this.elements.processedDisplay) {
            this.elements.processedDisplay.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='640' height='480'%3E%3Crect width='100%25' height='100%25' fill='%23000'/%3E%3Ctext x='50%25' y='50%25' fill='%23666' text-anchor='middle' dy='.3em' font-family='Arial' font-size='18'%3ENo Video Feed%3C/text%3E%3C/svg%3E";
        }
        
        if (this.elements.timestamp) {
            this.elements.timestamp.textContent = 'Ready to Start';
        }
        
        if (this.elements.permissionNotice && this.sourceType === 'webcam') {
            this.elements.permissionNotice.style.display = 'block';
        }
        
        // Reset map colors
        this.updateMapColors(0);
    }
    
    /**
     * Update performance statistics
     */
    updatePerformanceStats(processingTime) {
        this.performanceStats.framesProcessed++;
        this.performanceStats.totalProcessingTime += processingTime;
        this.performanceStats.averageProcessingTime = 
            this.performanceStats.totalProcessingTime / this.performanceStats.framesProcessed;
        
        if (this.elements.performanceInfo) {
            const avgTime = this.performanceStats.averageProcessingTime.toFixed(1);
            const fps = (1000 / this.config.frameProcessingInterval).toFixed(1);
            this.elements.performanceInfo.textContent = 
                `Processing: ${avgTime}ms avg | Target: ${fps} FPS | Frames: ${this.performanceStats.framesProcessed}`;
        }
    }
    
    /**
     * Set button states based on processing status
     */
    setButtonStates(processing) {
        if (this.elements.startBtn) {
            this.elements.startBtn.disabled = processing;
        }
        
        if (this.elements.stopBtn) {
            this.elements.stopBtn.disabled = !processing;
        }
        
        // Disable source selection during processing
        this.elements.sourceRadios.forEach(radio => {
            radio.disabled = processing;
        });
        
        if (this.elements.videoPathInput) {
            this.elements.videoPathInput.disabled = processing;
        }
        
        if (this.elements.validatePathBtn) {
            this.elements.validatePathBtn.disabled = processing;
        }
    }
    
    /**
     * Update system status display
     */
    updateSystemStatus(status, message) {
        if (this.elements.statusText) {
            this.elements.statusText.textContent = message;
        }
        
        if (this.elements.statusIndicator) {
            this.elements.statusIndicator.className = 'status-indicator';
            
            switch (status) {
                case 'active':
                    this.elements.statusIndicator.classList.add('active');
                    break;
                case 'error':
                    this.elements.statusIndicator.classList.add('error');
                    break;
            }
        }
        
        if (this.elements.processingStatus) {
            this.elements.processingStatus.textContent = 
                status === 'active' ? 'Active' : 
                status === 'error' ? 'Error' : 'Inactive';
            this.elements.processingStatus.className = `status-${status === 'active' ? 'active' : 'inactive'}`;
        }
        
        this.updateSourceDisplay();
    }
    
    /**
     * Update source display
     */
    updateSourceDisplay() {
        if (this.elements.inputSourceStatus) {
            this.elements.inputSourceStatus.textContent = 
                this.isProcessing ? this.sourceType : 'None';
            this.elements.inputSourceStatus.className = 
                this.isProcessing ? 'status-active' : 'status-inactive';
        }
        
        if (this.elements.sourceDisplay) {
            this.elements.sourceDisplay.textContent = 
                this.isProcessing ? this.sourceType : 'None';
        }
    }
    
    /**
     * Initialize Leaflet map with Delhi road network
     */
    initializeMap() {
        console.log('[WatchHer] Initializing map...');
        
        try {
            // Initialize map centered on Delhi
            this.map = L.map('riskMap').setView([28.6139, 77.2090], 11);
            
            // Add tile layer with dark theme
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 18
            }).addTo(this.map);
            
            // Define Delhi road segments with real coordinates
            const roadSegments = [
                {
                    name: "Connaught Place Area",
                    coordinates: [
                        [28.6328, 77.2197],
                        [28.6315, 77.2190],
                        [28.6300, 77.2180],
                        [28.6290, 77.2170]
                    ],
                    center: [28.6315, 77.2185]
                },
                {
                    name: "India Gate Area",
                    coordinates: [
                        [28.6129, 77.2295],
                        [28.6140, 77.2280],
                        [28.6150, 77.2265],
                        [28.6160, 77.2250]
                    ],
                    center: [28.6145, 77.2270]
                },
                {
                    name: "Karol Bagh Market",
                    coordinates: [
                        [28.6507, 77.1901],
                        [28.6520, 77.1920],
                        [28.6535, 77.1940],
                        [28.6550, 77.1960]
                    ],
                    center: [28.6530, 77.1930]
                },
                {
                    name: "Chandni Chowk",
                    coordinates: [
                        [28.6506, 77.2303],
                        [28.6520, 77.2290],
                        [28.6535, 77.2275],
                        [28.6550, 77.2260]
                    ],
                    center: [28.6530, 77.2280]
                },
                {
                    name: "Lajpat Nagar Market",
                    coordinates: [
                        [28.5659, 77.2436],
                        [28.5670, 77.2450],
                        [28.5680, 77.2465],
                        [28.5690, 77.2480]
                    ],
                    center: [28.5675, 77.2460]
                }
            ];
            
            // Create road segments on map
            this.roadSegments = roadSegments.map(segment => {
                const polyline = L.polyline(segment.coordinates, {
                    color: '#00D4AA',
                    weight: 6,
                    opacity: 0.8
                }).addTo(this.map);
                
                // Add popup with area information
                polyline.bindPopup(`
                    <div style="text-align: center;">
                        <h4 style="margin: 0 0 8px 0; color: #007BFF;">${segment.name}</h4>
                        <p style="margin: 0; color: #E8E8E8;">Risk Level: <span id="popup-risk-${segment.name.replace(/\s+/g, '-')}">SAFE</span></p>
                    </div>
                `);
                
                return {
                    ...segment,
                    polyline: polyline
                };
            });
            
            console.log('[WatchHer] Map initialized with', this.roadSegments.length, 'road segments');
            
        } catch (error) {
            console.error('[WatchHer] Map initialization error:', error);
        }
    }
    
    /**
     * Update map colors based on risk score
     */
    updateMapColors(riskScore) {
        if (!this.map || !this.roadSegments) return;
        
        let color = '#00D4AA'; // Safe (green)
        let riskLevel = 'SAFE';
        
        if (riskScore >= 70) {
            color = '#FF006E'; // High (red)
            riskLevel = 'HIGH RISK';
        } else if (riskScore >= 40) {
            color = '#FF8500'; // Moderate (orange)
            riskLevel = 'MODERATE';
        } else if (riskScore >= 15) {
            color = '#FFD60A'; // Low (yellow)
            riskLevel = 'LOW RISK';
        }
        
        // Update all road segments
        this.roadSegments.forEach(segment => {
            segment.polyline.setStyle({ color: color });
            
            // Update popup content if open
            const popupId = `popup-risk-${segment.name.replace(/\s+/g, '-')}`;
            const popupElement = document.getElementById(popupId);
            if (popupElement) {
                popupElement.textContent = riskLevel;
                popupElement.style.color = color;
            }
        });
    }
    
    /**
     * Reset map view to default
     */
    resetMapView() {
        if (this.map) {
            this.map.setView([28.6139, 77.2090], 11);
            console.log('[WatchHer] Map view reset to Delhi center');
        }
    }
    
    /**
     * Check system capabilities
     */
    async checkSystemCapabilities() {
        try {
            // Check camera availability
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            
            console.log(`[WatchHer] Found ${videoDevices.length} video devices`);
            
            if (videoDevices.length === 0) {
                console.warn('[WatchHer] No video devices found');
            }
            
            // Check backend capabilities
            const response = await fetch('/api/system_info');
            if (response.ok) {
                const systemInfo = await response.json();
                console.log('[WatchHer] System capabilities:', systemInfo);
            }
            
        } catch (error) {
            console.error('[WatchHer] Capability check error:', error);
        }
    }
    
    /**
     * Handle window focus events
     */
    handleWindowFocus() {
        if (this.isProcessing && !this.eventSource) {
            console.log('[WatchHer] Window focused, reconnecting event stream');
            this.startEventStream();
        }
    }
    
    /**
     * Handle window blur events
     */
    handleWindowBlur() {
        // Optionally reduce processing frequency when window is not focused
        console.log('[WatchHer] Window blurred');
    }
}

// Initialize application when DOM is loaded
if (typeof window !== 'undefined') {
    window.WatchHerApp = WatchHerApp;
} 