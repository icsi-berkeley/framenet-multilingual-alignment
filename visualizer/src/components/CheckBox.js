import React from 'react';
import PropTypes from 'prop-types';

import './CheckBox.css';

import FormLabel from './FormLabel';

/**
 * 
 * A checkbox component with label and state change event support.
 * 
 */
export default class CheckBox extends React.Component {
	static propTypes = {
		/**
		 * The checkbox current state (checked or not).
		 */
		checked: PropTypes.bool,
		/**
		 * The checkbox label string.
		 */
		label: PropTypes.string,
		/**
		 * A callback called when the checkbox state changes.
		 * 
		 * @param {boolean} checked the new "checked" state.
		 */
		onChange: PropTypes.func,
	}

	render() {
		const { checked, label, onChange } = this.props;

		return (
			<div className="checkbox-wrapper">
				<input type="checkbox" checked={checked || false} onChange={e => onChange(e.target.checked)} />
				<FormLabel style={{ marginLeft: 6 }}>{label}</FormLabel>
			</div>
		);
	}
};
