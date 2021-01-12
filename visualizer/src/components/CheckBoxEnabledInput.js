import React from 'react';
import PropTypes from 'prop-types';

import './CheckBoxEnabledInput.css';

import CheckBox from './CheckBox';
import NumericInput from './NumericInput';

/**
 * 
 * A component for a numeric input field that can be enabled or disabled
 * depending ina checkbox.
 * 
 */
export default class CheckBoxEnabledInput extends React.Component {
	static propTypes = {
		/**
		 * The checkbox current state (checked or not).
		 */
		checked: PropTypes.bool,
		/**
		 * The numeric input field value.
		 */
		value: PropTypes.number,
		/**
		 * The checkbox label string.
		 */
		label: PropTypes.string,
		/**
		 * The input field placeholder string.
		 */
		placeholder: PropTypes.string,
		/**
		 * The minimum value for the input element. 
		 */
		min: PropTypes.number,
		/**
		 * A callback called when the checkbox state changes.
		 * 
		 * @param {boolean} checked the new "checked" state.
		 */
		onCheckedChange: PropTypes.func,
		/**
		 * A callback called when the input field value changes.
		 * 
		 * @param {number} value the new value of the input field.
		 */
		onValueChange: PropTypes.func,
	}

	render() {
		const {
			checked,
			value,
			label,
			placeholder,
			min,
			disabled,
			onCheckedChange,
			onValueChange,
		} = this.props;
			
		return (
			<div className="checkbox-enable-input-wrapper">
				<CheckBox
					id="restrict-neighborhood"
					checked={checked}
					onChange={onCheckedChange}
					label={label}
					disabled={disabled}
				/>
				<div className="checkbox-enabled-input-input-wrapper">
					<NumericInput
						min={min}
						placeholder={placeholder}
						value={value}
						disabled={disabled || !checked}
						onChange={onValueChange}
						// style={{ width: '202px' }}
					/>
				</div>
			</div>
		);
	}
}
