const workerCode = () => {
	// eslint-disable-next-line no-restricted-globals
	self.onmessage = function(message) {
		const reader = new FileReader();
	
		reader.addEventListener('load', load => {
			try {
				const data = JSON.parse(load.target.result)
				postMessage(data)
			} catch (exception) {
				postMessage(exception)
			}
		});
	
		reader.readAsBinaryString(message.data);
	}
}

let code = workerCode.toString();
code = code.substring(code.indexOf("{")+1, code.lastIndexOf("}"));

const blob = new Blob([code], {type: "application/javascript"});
const workerScript = URL.createObjectURL(blob);

module.exports = workerScript;