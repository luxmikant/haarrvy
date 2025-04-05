document.addEventListener('DOMContentLoaded', function() {
    const startButton = document.getElementById('startRecording');
    const stopButton = document.getElementById('stopRecording');
    const recordingStatus = document.getElementById('recordingStatus');
    const processingStatus = document.getElementById('processingStatus');
    const transcriptCard = document.getElementById('transcriptCard');
    const transcriptContent = document.getElementById('transcriptContent');
    const ehrDataCard = document.getElementById('ehrDataCard');
    const ehrDataContent = document.getElementById('ehrDataContent');

    const recorder = new AudioRecorder();

    startButton.addEventListener('click', async () => {
        try {
            // Hide any previous results
            transcriptCard.classList.add('d-none');
            ehrDataCard.classList.add('d-none');
            
            // Start recording
            await recorder.start();
            
            // Update UI
            startButton.disabled = true;
            stopButton.disabled = false;
            recordingStatus.classList.remove('d-none');
        } catch (error) {
            alert('Error starting recording: ' + error.message);
            console.error('Recording error:', error);
        }
    });

    stopButton.addEventListener('click', async () => {
        try {
            // Update UI
            stopButton.disabled = true;
            recordingStatus.classList.add('d-none');
            processingStatus.classList.remove('d-none');
            
            // Stop recording and get audio blob
            const audioBlob = await recorder.stop();
            
            // Send to server for processing
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            
            const response = await fetch('/api/process-audio', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            // Display results
            if (result.error) {
                alert('Error processing audio: ' + result.error);
            } else {
                // Display transcript if available
                if (result.rawText) {
                    transcriptContent.textContent = result.rawText;
                    transcriptCard.classList.remove('d-none');
                }
                
                // Display structured EHR data
                ehrDataContent.innerHTML = '<pre>' + JSON.stringify(result, null, 2) + '</pre>';
                ehrDataCard.classList.remove('d-none');
            }
        } catch (error) {
            alert('Error processing recording: ' + error.message);
            console.error('Processing error:', error);
        } finally {
            // Reset UI
            startButton.disabled = false;
            processingStatus.classList.add('d-none');
        }
    });
});// Main application logic 
