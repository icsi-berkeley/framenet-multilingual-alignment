import React from 'react';
import PropTypes from 'prop-types';
import {observer} from 'mobx-react';
import {scalePoint} from 'd3-scale';

import MatchingGraph from './MatchingGraph';
import AlignmentStore from '../stores/AlignmentStore';

/**
 * A component for frame element matching graphs.
 */
const FEMatchingGraph = observer(
	class FEMatchingGraph extends React.Component {
		static propTypes = {
			/**
			 * The frame pair of the FEs used for rendering the graph.
			 */
			framePair: PropTypes.array,
			/**
			 * A mobx store of frame alignments.
			 */
			store: PropTypes.instanceOf(AlignmentStore),
			/**
			 * A callback called when mouse is placed over of the nodes.
			 */
			onMouseOverNode: PropTypes.func,
			/**
			 * A callback called when mouse is leaves of the nodes.
			 */
			onMouseOutNode: PropTypes.func,
		}

		/**
		 * Gets all required data for rendering. Basic node and link data comes
		 * from the store received from props, this method computes the coordinates
		 * where each element should be rendered.
		 * 
		 * @public
		 * @method
		 * @returns {Object} Graph definition with a node list and a link list.
		 */
		getRenderingData() {
			const {store, uiState} = this.props;
			const data = store.graphData;

			const height = uiState.height-10;
			const width = Math.max(uiState.width, 400);
			const margin = 60;
			
			const x =
				scalePoint()
					.domain(['left', 'right'])
					.range([0, width])
					.padding(.3)

			const yLeft = scalePoint()
				.domain(data.nodes
					.filter(d => d.type === 'left')
					.sort((a, b) => b.outDegree - a.outDegree)
					.map(d => d.name))
				.range([margin*4, height-(margin*4)]);

			const yRight = scalePoint()
				.domain(data.nodes
						.filter(d => d.type === 'right')
						.sort((a,b) => b.outDegree - a.outDegree)
						.map(d => d.name))
				.range([margin*4, height-(margin*4)]);

			const xLeft = x('left');
			const xRight = x('right');

			data.nodes.forEach(d => {
				if (d.type === 'left') {
					d.x = xLeft;
					d.y = yLeft(d.name);
				} else {
					d.x = xRight;
					d.y = yRight(d.name);
				}
			})

			return {
				nodes: data.nodes,
				links: data.links
			}
		}

		render() {
			const {uiState} = this.props;

			return (
				<MatchingGraph
					data={this.getRenderingData()}
					framePair={this.props.framePair}
					height={uiState.height}
					width={uiState.width}
					margin={60}
					onMouseOverNode={this.props.onMouseOutNode}
					onMouseOutNode={this.props.onMouseOutNode}
				/>
			);
		}

	}
);

export default FEMatchingGraph;