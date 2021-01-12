import React from 'react';
import PropTypes from 'prop-types';
import Select from 'react-select';
import MultiSelect from "@kenshooui/react-multi-select";
import ClipLoader from "react-spinners/ClipLoader";
import { FaBars } from 'react-icons/fa';
import { observer } from 'mobx-react';

import './Sidebar.css';

import CheckBox from './CheckBox';
import CheckBoxEnabledInput from './CheckBoxEnabledInput';
import FormLabel from './FormLabel';
import JsonFileInput from './JsonFileInput';
import NumericInput from './NumericInput';
import Slider from './Slider';

import AlignmentStore from '../stores/AlignmentStore';
import UiState from '../stores/UiState';

/**
 * 
 * A Sidebar component for the alignment visualization tool. This sidebar
 * renders the components necessary to input alignment json files and change
 * visualization parameters.
 * 
 */
const Sidebar = observer(
	class Sidebar extends React.Component {
		static propTypes = {
			/**
			 * A mobx store of frame alignments.
			 */
			store: PropTypes.instanceOf(AlignmentStore),
			/**
			 * A mobx store for the application's UI state.
			 */
			uiState: PropTypes.instanceOf(UiState),
		}

		/**
		 * Handles an alignment file. All parsed data is loaded to the
		 * AlignmentStore instance.
		 * 
		 * @public
		 * @method
		 * @param {Object} data parsed data from an alignment file.
		 */
		onFileChange = data => this.props.store.isLoading = true

		/**
		 * Handles an alignment file. All parsed data is loaded to the
		 * AlignmentStore instance.
		 * 
		 * @public
		 * @method
		 * @param {Object} data parsed data from an alignment file.
		 */
		onFileParse = data => {
			if (!(data instanceof Error)) {
				this.props.store.load(data)
			}

			this.props.store.isLoading = false
		}


		/**
		 * Handles the selection of a scoring option.
		 * 
		 * @public
		 * @method
		 * @param {Object} option the selected scoring option.
		 */
		onScoringChange = option => this.props.uiState.setScoring(option.value)

		/**
		 * Handles changes in frame selection for the visualization.
		 * 
		 * @public
		 * @method
		 * @param {Array} selected list of selected frames.
		 */
		onFrameSelectionChange = selected => this.props.uiState.sankeyFrames = selected

		/**
		 * Updates a property in the params object of the current scoring of the
		 * UiState instance.
		 * 
		 * @public
		 * @method
		 * @param {string} param the parameter propery name
		 * @param {*} value the new value for the parameter.
		 */
		updateParam = (param, value) => {
			const {uiState} = this.props;
			if (uiState.scoring) {
				uiState.scoring.params[param] = value;
			}
		}

		/**
		 * Handles change in visualization score threshold.
		 * 
		 * @public
		 * @method
		 * @param {number} value the new threshold value.
		 */
		onThresholdChange = value => this.updateParam("threshold", value)

		/**
		 * Handles change in checkbox "Restrict number of connections of each frame".
		 * 
		 * @public
		 * @method
		 * @param {boolean} checked whether the checkbox is checked. 
		 */
		onLimitSankeyEdgesChange = checked => this.updateParam("limitSankeyEdges", checked)

		/**
		 * Handles change in maximum number of edges displayed in the Sankey diagram.
		 * 
		 * @public
		 * @method
		 * @param {number} value an integer edge limit for each frame.
		 */
		onSankeyEdgesMaxChange = value => this.updateParam("sankeyMaxEdges", value)

		/**
		 * Handles change on checkbox "Show ONLY selected frames".
		 * 
		 * @public
		 * @method
		 * @param {boolean} checked whether the checkbox is checked. 
		 */
		onDisplayOnlyFrameSetChange = checked => this.updateParam("displayOnlyFrameSet", checked)

		/**
		 * Handles change in vector neighborhood size parameter.
		 * 
		 * @public
		 * @method
		 * @param {number} value an integer neighborhood size.
		 */
		onNeighborhoodSizeChange = value => this.updateParam("neighborhoodSize", value)

		/**
		 * Handles change in cosine similarity threshold.
		 * 
		 * @public
		 * @method
		 * @param {number} value the new cosine similarity threshold value.
		 */
		onSimilarityThresholdChange = value => this.updateParam("similarityThreshold", value)

		/**
		 * Renders parameters that are exclusive for scoring matching LUs through
		 * vectors.
		 * 
		 * @public 
		 * @method
		 * @returns {JSX} 
		 */
		renderVectorFields() {
			const {uiState} = this.props;

			if (uiState.scoring && (uiState.scoring.type === 'lu_muse' || uiState.scoring.type === 'lu_bert')) {
				const {params} = uiState.scoring;

				return (
					<div className="sidebar-row">
						<div className="sidebar-cell">
							<NumericInput
								min={1}
								step={1}
								value={params.neighborhoodSize}
								onChange={this.onNeighborhoodSizeChange}
								label="Vector neighborhood size"
							/>
						</div>
						<div className="sidebar-cell">
							<Slider
								label="Cosine similarity threshold"
								value={params.similarityThreshold}
								onChange={this.onSimilarityThresholdChange}
							/>
						</div>
					</div>
				);
			}
		}
		
		render() {
			const {store, uiState} = this.props;
			const sidebarWidth = { width: `calc(${uiState.isSidebarOpen ? '550px' : '60px'} - 32px)` };
			const contentDisplay = { display: uiState.isSidebarOpen ? 'block' : 'none' };
			const params = uiState.scoring ? uiState.scoring.params : {};
		
			return (
				<div className="sidebar-container" style={sidebarWidth} >
					<div className="sidebar-icon-container">
						<div
							onClick={() => uiState.isSidebarOpen = !uiState.isSidebarOpen}
							className="siderbar-icon-click-wrapper"
						>
							<FaBars size="1.75em" color="#3F51B5" />
						</div>
					</div>
					<div style={contentDisplay} >
						<FormLabel style={{ marginTop: 0 }}>Alignment file</FormLabel>
						<div className="sidebar-row">
							<JsonFileInput onFileChange={this.onFileChange} onFileParse={this.onFileParse} />
							{store.isLoading &&
								<ClipLoader size={24} color={'#3F51B5'} css={'margin-left: 25px;'} />
							}
						</div>
						<div className="sidebar-row">
							<div className="sidebar-cell">
								<FormLabel>Scoring technique</FormLabel>
								<Select
									options={uiState.scoringSelectOptions}
									onChange={this.onScoringChange}
									disabled={store.isLoading}
								/>
							</div>
							<div className="sidebar-cell">
								<Slider
									value={params.threshold}
									disabled={store.isLoading || !uiState.scoring}
									onChange={this.onThresholdChange}
									label="Score threshold"
								/>
							</div>
						</div>
						{this.renderVectorFields()}
						<div className="sidebar-row">
							<div className="sidebar-cell">
								<CheckBoxEnabledInput
									checked={params.limitSankeyEdges}
									value={params.sankeyMaxEdges}
									disabled={store.isLoading || !uiState.scoring}
									onCheckedChange={this.onLimitSankeyEdgesChange}
									onValueChange={this.onSankeyEdgesMaxChange}
									min={1}
									label="Restrict number of connections of each frame:"
									placeholder="Max # of edges for frame"
								/>
							</div>
							<div className="sidebar-cell">
								<CheckBox
									id="show-selected-only"
									checked={params.displayOnlyFrameSet}
									disabled={store.isLoading || !uiState.scoring}
									onChange={this.onDisplayOnlyFrameSetChange}
									label="Show ONLY selected frames"
								/>
							</div>
						</div>
						<FormLabel>Frame selection</FormLabel>
						<MultiSelect
							items={store.frameOptions}	
							selectedItems={uiState.sankeyFrames}
							onChange={this.onFrameSelectionChange}
							responsiveHeight="350px"
							itemHeight={30}
							wrapperClassName="multi-select-wrapper"
						/>
					</div>
				</div>
			);
		}
	}
);

export default Sidebar;