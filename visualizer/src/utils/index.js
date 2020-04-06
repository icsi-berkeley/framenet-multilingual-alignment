/**
 * Measures the rendered width of arbitrary text given the font size and font
 * face.
 * 
 * @param {string} text The text to measure.
 * @param {number} fontSize The font size in pixels.
 * @param {string} fontFace The font face ("Arial", "Helvetica", etc.).
 * @returns {number} The width of the text.
 */
function getRenderedTextSize(text, fontSize, fontFace = null) {
	const canvas = document.createElement('canvas');
	const context = canvas.getContext('2d');

	if (fontFace) {
		context.font = `${fontSize}px ${fontFace}`;
	} else {
		context.font = context.font.replace(/\d+px/, `${fontSize}px`);
	}

	return context.measureText(text).width;
}

export {
	getRenderedTextSize,
};