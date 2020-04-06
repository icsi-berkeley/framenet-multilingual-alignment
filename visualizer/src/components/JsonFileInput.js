import React from 'react';
import PropTypes from 'prop-types';

import './JsonFileInput.css';

/**
 * 
 * A file input component used to load local json files.
 * 
 */
class JsonFileInput extends React.Component {

	static propTypes = {
		/**
		 * A callback called when a valid json file is read and parsed.
		 * 
		 * @param {Object} data the parsed json file.
		 */
		onFileChange: PropTypes.func,
	}

	constructor(props) {
		super(props);
		this.state = {
			error: false,
		}
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
			const reader = new FileReader();

			reader.addEventListener('load', e => {
				let error = false;
				try {
					const data = JSON.parse(e.target.result);
					this.props.onFileChange(data);
				} catch (exception) {
					error = true;
				}
				this.setState({ error });
			});

			reader.readAsBinaryString(file);
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
		const {error} = this.state;
		return error ? <p className="upload-error">Error reading input file.</p> : null;
	}

	render() {
		return (
			<div>
				<input type="file" onChange={this.onFileChange} />
				{this.renderError()}
			</div>
		);
	}
}

export default JsonFileInput;
