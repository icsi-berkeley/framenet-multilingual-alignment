import React from 'react';
import PropTypes from 'prop-types';

import './NumericInput.css';
import FormLabel from './FormLabel';

/**
 * 
 * A numeric input field component.
 * 
 */
export default class NumericInput extends React.Component {
	static propTypes = {
		/**
		 * Optional label for this field.
		 */
		label: PropTypes.string,
		/**
		 * The minimum value for the input element. 
		 */
		min: PropTypes.number,
		/**
		 * The maximum value for the input element. 
		 */
		max: PropTypes.number,
		/**
		 * The step of the input field. Use 1 for integer only.
		 */
		step: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
		/**
		 * Placeholder string of the input field.
		 */
		placeholder: PropTypes.string,
		/**
		 * The numeric input field value.
		 */
		value: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
		/**
		 * Whether the input field is disabled or not.
		 */
		disabled: PropTypes.bool,
		/**
		 * A callback called when the input field value changes.
		 * 
		 * @param {number} value the new value of the input field.
		 */
		onChange: PropTypes.func,
	}

	/**
	 * Renders the input label if it was passed via props.
	 * 
	 * @public
	 * @method
	 * @returns {JSX} 
	 */
	renderLabel() {
		const {label} = this.props;

		if (label) {
			return <FormLabel>{label}</FormLabel>;
		}
	}

	render() {
		const {min, max, step, placeholder, value, disabled, onChange} = this.props;

		return (
			<div>
				{this.renderLabel()}
				<div className="numeric-input-wrapper">
					<input
						type="number"
						min={min}
						max={max}
						step={step}
						placeholder={placeholder}
						value={value || ''}
						disabled={disabled}
						onChange={e => onChange(Number(e.target.value))}
					/>
			</div>
			</div>
		);
	}
};
