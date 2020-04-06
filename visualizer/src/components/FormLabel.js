import React from 'react';
import PropTypes from 'prop-types';

import './FormLabel.css';

/**
 * 
 * A component for styled form labels.
 * 
 */
export default class FormLabel extends React.Component {
	static propTypes = {
		/**
		 * The label string.
		 */
		text: PropTypes.string,
	}

	render() {
		const {children, style} = this.props;

		return (
			<div className="form-label" style={style}>
				{children}
			</div>
		);
	}
};
