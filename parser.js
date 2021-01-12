onmessage = function(message) {
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