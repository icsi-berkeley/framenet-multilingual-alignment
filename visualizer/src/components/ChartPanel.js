import React from 'react';
import PropTypes from 'prop-types';
import {observer} from 'mobx-react';
import {FaArrowLeft} from 'react-icons/fa';

import './ChartPanel.css';

import Sankey from './Sankey';
import SynsetGraph from './SynsetGraph';
import LUMatchingGraph from './LUMatchingGraph';
import FEMatchingGraph from './FEMatchingGraph';
import AlignmentStore from '../stores/AlignmentStore';
import UiState from '../stores/UiState';

/**
 * A component for the primary viewport of the application. It is responsible
 * for controlling which visualization will be rendered based on the UI state.
 */
const ChartPanel = observer(
	class ChartPanel extends React.Component {
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

		constructor() {
			super();
			this.selectableTypes = [
				"lu_wordnet",
				"synset",
				"synset_inv",
				"lu_muse",
				"fe_matching",
				"lu_bert",
			]
		}

		/**
		 * Handles click on "Back" button/arrow.
		 * 
		 * @public
		 * @method
		 */
		onBackClick() {
			this.props.uiState.isAlignmentDetailVisible = false;
		}

		/**
		 * Handles click on a edge/link of the Sankey diagram.
		 * 
		 * @public
		 * @method
		 * @param {Object} source edge's source frame object.
		 * @param {Object} target edge's target frame object.
		 */
		onEdgeClick(source, target) {
			const {uiState} = this.props;
			
			if (this.selectableTypes.indexOf(uiState.scoring.type) > -1) {
				uiState.isAlignmentDetailVisible = true;
				uiState.setSelectedFramePair(source.gid, target.gid);
			}
		}

		/**
		 * Renders the appropriate detail/matching graph for the selected frame
		 * pair and scoring technique.
		 * 
		 * @public
		 * @method
		 * @returns {JSX}
		 */
		renderMatchingGraph() {
			const {store, uiState} = this.props;

			if (uiState.scoring) {
				const framePair = uiState.selectedFrames.map(x => store.frames[x]);

				switch(uiState.scoring.type) {
					case 'lu_muse':
					case 'lu_bert':
						return <LUMatchingGraph store={store} uiState={uiState} framePair={framePair} />;
					case 'fe_matching':
						return <FEMatchingGraph store={store} uiState={uiState} framePair={framePair} />;
					default:
						return <SynsetGraph store={store} uiState={uiState} framePair={framePair} />;
				}
			}
		}

		render() {
			const {store, uiState} = this.props;
			let className = "";

			// Determining the tranformation that must be done to show the correct chart.
			className += uiState.isAlignmentDetailVisible ? "shift" : "no-shift";
		
			return (
				<div
					id="chart-panel-container"
					className={className}
				>
					{
						uiState.isAlignmentDetailVisible &&
						<div id="back-button-container" onClick={() => this.onBackClick()} >
							<FaArrowLeft size="1.75em" />
						</div>
					}
					<Sankey
						store={store}
						uiState={uiState}
						onEdgeClick={(s, t) => this.onEdgeClick(s, t)}
					/>
					{this.renderMatchingGraph()}
				</div>
			)
		}
	}
)

export default ChartPanel;