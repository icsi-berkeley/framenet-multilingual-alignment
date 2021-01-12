import React from 'react';
import PropTypes from 'prop-types';

import './JsonFileInput.css';

const worker = new Worker('parser.js')

/**
 * 
 * A file input component used to load local json files.
 * 
 */
class JsonFileInput extends React.Component {

	static propTypes = {
		/**
		 * A callback called when the file is changed.
		 * 
		 * @param {String} file the file name.
		 */
		onFileChange: PropTypes.func,

		/**
		 * A callback called when the file is parsed
		 * @param {Object} data the parsed json file.
		 */
		onFileParse: PropTypes.func,
	}

	/**
	 * Parses the file of the input field and sends its contents to the parent
	 * component. When parsing fails, this method will be update this component
	 * state.
	 * 
	 * @todo Move parsing to a service worker.
	 * @public
	 * @param {Event} event the file change event.
	 */
	onFileChange = event => {
		const file = event.target.files[0];

		if (file) {
			this.props.onFileChange(file)

			worker.postMessage(file)
			worker.onmessage = (message) => {
				if (message.data instanceof Error) {
					this.setState({ error: true });
				}

				this.props.onFileParse(message.data)
			}
		}
	}

	/**
	 * Renders an error message.
	 * 
	 * @public
	 * @method
	 * @returns {JSX}
	 */
	renderError() {
		const {error} = this.props;
		return error ? <p className="upload-error">Error reading input file.</p> : null;
	}

	render() {
		return (
			<>
				<input type="file" onChange={this.onFileChange} />
				{this.renderError()}
			</>
		);
	}
}

export default JsonFileInput;
