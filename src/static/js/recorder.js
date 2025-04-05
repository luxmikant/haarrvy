
class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
        this.recordingTimer = null;
        this.recordingTime = 0;
    }

    async start() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(this.stream);
            this.audioChunks = [];

            this.mediaRecorder.addEventListener('dataavailable', event => {
                this.audioChunks.push(event.data);
            });

            this.mediaRecorder.start();
            this.startTimer();
            return true;
        } catch (error) {
            console.error('Error starting audio recording:', error);
            throw error;
        }
    }

    stop() {
        return new Promise(resolve => {
            if (!this.mediaRecorder) {
                resolve(null);
                return;
            }

            this.mediaRecorder.addEventListener('stop', () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                this.stopStream();
                this.stopTimer();
                resolve(audioBlob);
            });

            this.mediaRecorder.stop();
        });
    }

    stopStream() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }

    startTimer() {
        this.recordingTime = 0;
        this.stopTimer();
        this.recordingTimer = setInterval(() => {
            this.recordingTime++;
            const minutes = Math.floor(this.recordingTime / 60).toString().padStart(2, '0');
            const seconds = (this.recordingTime % 60).toString().padStart(2, '0');
            const timeString = `${minutes}:${seconds}`;
            
            const timeElement = document.getElementById('recordingTime');
            if (timeElement) {
                timeElement.textContent = timeString;
            }
        }, 1000);
    }

    stopTimer() {
        if (this.recordingTimer) {
            clearInterval(this.recordingTimer);
            this.recordingTimer = null;
        }
    }
}// Audio recorder functionality 
