import React from 'react';
import PropTypes from 'prop-types';
import { observer } from 'mobx-react';

import './Slider.css';

import FormLabel from './FormLabel';

/**
 * 
 * A slider component that also allows textual input in [0,1] interval.
 * 
 */
const Slider = observer(
	class Slider extends React.Component {
		static propTypes = {
			/**
			 * The current value of the slider.
			 */
			value: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
			/**
			 * A callback called when the slider value changes.
			 * 
			 * @param {string} value the new value.
			 */
			onChange: PropTypes.func,
		}

		render(){
			const {value, disabled, onChange, label} = this.props;

			return (
				<div className="slider-container">
					<FormLabel>{label}</FormLabel>
					<div className="slider-input-container">
						<input
							type="range"
							min={0}
							max={1}
							step={0.001}
							value={value || ""}
							disabled={disabled}
							onChange={e => onChange(e.target.value)}
							className="slider" />
						<input
							type="number"
							min={0}
							max={1}
							step="any"
							value={value || ""}
							disabled={disabled}
							onChange={e => onChange(e.target.value)}
							className="slider-text" />
					</div>
				</div>
			);
		}
	}
);

export default Slider;
