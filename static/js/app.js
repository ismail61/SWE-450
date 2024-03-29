//webkitURL is deprecated but nevertheless
URL = window.URL || window.webkitURL;

var gumStream; 						//stream from getUserMedia()
var rec; 							//Recorder.js object
var input; 							//MediaStreamAudioSourceNode we'll be recording

// shim for AudioContext when it's not avb. 
var AudioContext = window.AudioContext || window.webkitAudioContext;
var audioContext //audio context to help us record

var recordButton = document.getElementById("recordButton");
var stopButton = document.getElementById("stopButton");
var pauseButton = document.getElementById("pauseButton");

//add events to those 2 buttons
recordButton.addEventListener("click", startRecording);
stopButton.addEventListener("click", stopRecording);
pauseButton.addEventListener("click", pauseRecording);

function startRecording() {
	console.log("recordButton clicked");

	/*
		Simple constraints object, for more advanced audio features see
		https://addpipe.com/blog/audio-constraints-getusermedia/
	*/
    
    var constraints = { audio: true, video:false }

 	/*
    	Disable the record button until we get a success or fail from getUserMedia() 
	*/

	recordButton.disabled = true;
	stopButton.disabled = false;
	pauseButton.disabled = false

	/*
    	We're using the standard promise based getUserMedia() 
    	https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
	*/

	navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
		console.log("getUserMedia() success, stream created, initializing Recorder.js ...");

		/*
			create an audio context after getUserMedia is called
			sampleRate might change after getUserMedia is called, like it does on macOS when recording through AirPods
			the sampleRate defaults to the one set in your OS for your playback device
		*/
		audioContext = new AudioContext();

		//update the format 
		// document.getElementById("formats").innerHTML="Format: 1 channel pcm @ "+audioContext.sampleRate/1000+"kHz"

		/*  assign to gumStream for later use  */
		gumStream = stream;
		
		/* use the stream */
		input = audioContext.createMediaStreamSource(stream);

		/* 
			Create the Recorder object and configure to record mono sound (1 channel)
			Recording 2 channels  will double the file size
		*/
		rec = new Recorder(input,{numChannels:1})

		//start the recording process
		rec.record()

		console.log("Recording started");

	}).catch(function(err) {
	  	//enable the record button if getUserMedia() fails
		console.log("Recording Errro", err);
    	recordButton.disabled = false;
    	stopButton.disabled = true;
    	pauseButton.disabled = true
	});
}

function pauseRecording(){
	console.log("pauseButton clicked rec.recording=",rec.recording );
	if (rec.recording){
		//pause
		rec.stop();
		pauseButton.innerHTML="Resume";
	}else{
		//resume
		rec.record()
		pauseButton.innerHTML="Pause";

	}
}

function stopRecording() {
	console.log("stopButton clicked");

	//disable the stop button, enable the record too allow for new recordings
	stopButton.disabled = true;
	recordButton.disabled = false;
	pauseButton.disabled = true;

	//reset button just in case the recording is stopped while paused
	pauseButton.innerHTML="Pause";
	
	//tell the recorder to stop the recording
	rec.stop();

	//stop microphone access
	gumStream.getAudioTracks()[0].stop();

	//create the wav blob and pass it on to createDownloadLink
	rec.exportWAV(createDownloadLink);
}

function createDownloadLink(blob) {
	
	var url = URL.createObjectURL(blob);
	var au = document.createElement('audio');
	var li = document.createElement('li');
	var link = document.createElement('a');

	// Loader
	let buttonload = document.getElementById('buttonload'); 

	//name of .wav file to use during upload and download (without extendion)
	var filename = new Date().toISOString();

	//add controls to the <audio> element
	au.controls = true;
	au.src = url;

	//save to disk link
	link.href = url;
	link.download = filename+".wav"; //download forces the browser to donwload the file using the  filename
	link.innerHTML = "Download";
	link.className += 'btn btn-primary';
	link.style.position = 'relative';
	link.style.bottom = '20px';
	link.style.marginLeft = '10px';

	//add the new audio element to li
	li.appendChild(au);
	
	//add the filename to the li
	li.appendChild(document.createTextNode(filename+".wav "))

	//add the save to disk link to li
	li.appendChild(link);
	
	//upload link
	var upload = document.createElement('a');
	upload.href="#";
	upload.innerHTML = "Predict";
	upload.className += 'btn btn-success';
	upload.style.position = 'relative';
	upload.style.bottom = '20px';
	upload.style.marginLeft = '10px';
	upload.addEventListener("click", function(){
		buttonload.style.display = 'block';
		upload.disabled = true;
		var form = new FormData();
		form.append('file', blob, filename);
		form.append('title', filename);
		//Chrome inspector shows that the post data includes a file and a title.
		$.ajax({
			type: 'POST',
			url: '/predict',
			data: form,
			cache: false,
			processData: false,
			contentType: false,
			error: function() {
				buttonload.style.display = 'none';
				upload.disabled = false;
				alert('Something went wrong!');
			}
		}).done(function(data) {
			console.log(data);
			if(data) {
				// result plot
				let resultTxt1 = document.getElementById('resultTxt1'); 
				let resultTxt2 = document.getElementById('resultTxt2'); 
				let resultPlot1 = document.getElementById('resultPlot1'); 
				let resultPlot2 = document.getElementById('resultPlot2'); 
				let resultPlot3 = document.getElementById('resultPlot3'); 
				let mfccsPlot = document.getElementById('mfccsPlot'); 
				let spectrogramPloat = document.getElementById('spectrogramPloat');

				resultTxt1.style.display = 'block';
				resultTxt2.style.display = 'block';
				buttonload.style.display = 'none';

				// Plot
				mfccsPlot.style.display = 'block';
				mfccsPlot.src= `data:image/png;base64, ${data.mfccsPlot}`;

				spectrogramPloat.style.display = 'block';
				spectrogramPloat.src= `data:image/png;base64, ${data.spectrogramPloat}`;

				resultPlot1.style.display = 'block';
				resultPlot1.src= `data:image/png;base64, ${data.resultPlot1}`;

				resultPlot2.style.display = 'block';
				resultPlot2.src= `data:image/png;base64, ${data.resultPlot2}`;

				resultPlot3.style.display = 'block';
				resultPlot3.src= `data:image/png;base64, ${data.resultPlot3}`;
			}
		});
	})
	li.appendChild(document.createTextNode (" "))//add a space in between
	li.appendChild(upload)//add the upload link to li

	recordingsList.appendChild(li);
}

function fileSelectionSubmitButtonHandling(event) {

	event.preventDefault();

	// Loader
	let buttonload = document.getElementById('buttonload'); 
	buttonload.style.display = 'block';

	// result plot
	let resultTxt1 = document.getElementById('resultTxt1'); 
	let resultTxt2 = document.getElementById('resultTxt2'); 
	let resultPlot1 = document.getElementById('resultPlot1'); 
	// for newly
	resultPlot1.style.display = 'none';
	let resultPlot2 = document.getElementById('resultPlot2'); 
	resultPlot2.style.display = 'none';
	let resultPlot3 = document.getElementById('resultPlot3'); 
	resultPlot3.style.display = 'none';
	let mfccsPlot = document.getElementById('mfccsPlot'); 
	mfccsPlot.style.display = 'none';
	let spectrogramPloat = document.getElementById('spectrogramPloat'); 
	spectrogramPloat.style.display = 'none';

	const form = new FormData(event.target);
	var filename = new Date().toISOString();
	form.append('file', form.get('selectFile'), filename);
	form.append('title', filename);
	$.ajax({
		type: 'POST',
		url: '/predict',
		data: form,
		cache: false,
		processData: false,
		contentType: false,
		error: function() {
			buttonload.style.display = 'none';
			alert('Something went wrong!');
		}
	}).done(function(data) {
		console.log(data);
		if(data) {
			resultTxt1.style.display = 'block';
			resultTxt2.style.display = 'block';
			buttonload.style.display = 'none';

			// Plot
			mfccsPlot.style.display = 'block';
			mfccsPlot.src= `data:image/png;base64, ${data.mfccsPlot}`;

			spectrogramPloat.style.display = 'block';
			spectrogramPloat.src= `data:image/png;base64, ${data.spectrogramPloat}`;

			resultPlot1.style.display = 'block';
			resultPlot1.src= `data:image/png;base64, ${data.resultPlot1}`;

			resultPlot2.style.display = 'block';
			resultPlot2.src= `data:image/png;base64, ${data.resultPlot2}`;

			resultPlot3.style.display = 'block';
			resultPlot3.src= `data:image/png;base64, ${data.resultPlot3}`;
			// alert(`${data} is our expected value.`)
			// window.location.reload();
		}
	});
}