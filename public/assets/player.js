// "use strict";

document.ready = function (callback) {
	// 兼容FF, Google
	if (document.addEventListener) {
		document.addEventListener('DOMContentLoaded', function () {
			document.removeEventListener('DOMContentLoaded', arguments.callee, false);
			callback();
		}, false)
	}
	// 兼容IE
	else if (document.attachEvent) {
		document.attachEvent('onreadystatechange', function () {
			  if (document.readyState == "complete") {
						document.detachEvent("onreadystatechange", arguments.callee);
						callback();
			   }
		})
	}
	else if (document.lastChild == document.body) {
		callback();
	}
}

document.ready(function () {
	loadPlayer();
});

function loadPlayer() {
	// console.log('loadPlayer');
	var playpauseBtns = document.getElementById('playpause');
	// console.log(playpauseBtns);
	playpauseBtns.addEventListener("click", (event) => {
		var audio = event.currentTarget.nextElementSibling;
		console.log(audio);
		if (audio.paused || audio.ended) {
			console.log("click: allow to play!");
			audio.play();
		} else {
			console.log("click: not allow to play!");
			audio.pause();
		}
	});

	var audios = document.getElementsByTagName('audio');
	for (var i = 0; i < audios.length; i++) {
		let audio = audios[i];
		// console.log(audio);
		audio.addEventListener("play", (event) => {
			var btn = event.currentTarget.previousSibling.previousSibling;
			// console.log(btn);
			updateButtons(btn, true);
		});
		audio.addEventListener("playing", (event) => {
			var btn = event.currentTarget.previousSibling.previousSibling;
			// console.log(btn);
			updateButtons(btn, true);
		});
		audio.addEventListener("ended", (event) => {
			var btn = event.currentTarget.previousSibling.previousSibling;
			// console.log(btn);
			updateButtons(btn, false);
		});
	}
}

function updateButtons(btn, playing) {
    if (playing) {
        btn.classList.add('jp-state-playing');
    } else {
        btn.classList.remove('jp-state-playing');
    }
    /*if(!this.status.noFullWindow && this.options.fullWindow) {
		this.addStateClass('fullScreen');
	} else {
		this.removeStateClass('fullScreen');
	}
	if(this.options.loop) {
		this.addStateClass('looped');
	} else {
		this.removeStateClass('looped');
	}
	// Toggle the GUI element pairs. (For the useStateClassSkin:false option)
	if(this.css.jq.play.length && this.css.jq.pause.length) {
		if(playing) {
			this.css.jq.play.hide();
			this.css.jq.pause.show();
		} else {
			this.css.jq.play.show();
			this.css.jq.pause.hide();
		}
	}
	if(this.css.jq.restoreScreen.length && this.css.jq.fullScreen.length) {
		if(this.status.noFullWindow) {
			this.css.jq.fullScreen.hide();
			this.css.jq.restoreScreen.hide();
		} else if(this.options.fullWindow) {
			this.css.jq.fullScreen.hide();
			this.css.jq.restoreScreen.show();
		} else {
			this.css.jq.fullScreen.show();
			this.css.jq.restoreScreen.hide();
		}
	}
	if(this.css.jq.repeat.length && this.css.jq.repeatOff.length) {
		if(this.options.loop) {
			this.css.jq.repeat.hide();
			this.css.jq.repeatOff.show();
		} else {
			this.css.jq.repeat.show();
			this.css.jq.repeatOff.hide();
		}
	}*/
}
