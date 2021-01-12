import React from 'react';
import PropTypes from 'prop-types';
import ScaleLoader from "react-spinners/ScaleLoader";
import { format } from 'd3-format';
import { select } from 'd3-selection';
import { observer } from 'mobx-react';
// TODO: Should redo this d3 layout
import viz from '../layouts/viz.js';

import './Sankey.css';

import AlignmentStore from '../stores/AlignmentStore';
import { getRenderedTextSize } from '../utils';

// A 3-decimal precision formatter.
const scoreFormatter = format(".3f");

/**
 * Infinitely yields hex colors strings. Since the amount of hex color strings
 * is finite, the same list is yielded through a circular iteration.
 * 
 * @generator
 * @function colors
 * @yields {string} a hex color string
 */
const colors = function*() {
	const colors = [
		"#3366CC",
		"#DC3912",
		"#FF9900",
		"#109618",
		"#990099",
		"#0099C6"
	];
	let index = 0;

	while(true) {
		yield colors[index];
		index = ++index % colors.length;
	}
};

/**
 * 
 * A Sankey diagram component that uses D3.js to render the visualization as a
 * svg image. This diagram supports click events on Sankey labels and flow
 * connections.
 *
 */
const Sankey = observer(
	class Sankey extends React.Component {

		static propTypes = {
			/**
			 * A mobx store of frame alignments.
			 */
			store: PropTypes.instanceOf(AlignmentStore),
			/**
			 * A callback called a edge of the diagram is clicked.
			 * 
			 * @param {Array} edge A 2-position array containing the source and target of the edge.
			 */
			onEdgeClick: PropTypes.func,
		}

		constructor(props) {
			super(props);

			// Reference to svg element
			this.svg = null;
			// Expanded diagram node
			this.selection = null;
			// Reference to D3.js layout of the diagram
			this.bP = null;
			// Reference to diagram root "g" svg element
			this.bPg = null;
			// Container dimensions for next render
			this.height = null;
			this.width = null;
		}

		/**
		 * Manually invokes D3.js rendering function when the component is mounted.
		 * 
		 * @public
		 * @method
		 */
		componentDidMount() {
			this.renderSankey();
		}

		/**
		 * Manually invokes D3.js rendering function when the component is updated.
		 * 
		 * @public
		 * @method
		 */
		componentDidUpdate() {
			this.renderSankey();
		}

		/**
		 * Handles click on a bar/node/label of the Sankey diagram. The clicked
		 * item will be expanded or shrink depending of the current state of the
		 * digram.
		 * 
		 * @public
		 * @model
		 * @param {Object} bar data object of the clicked bar/label.
		 */
		onNodeClick(bar) {
			if (this.selection && this.selection.key === bar.key) {
				this.shrink(this.selection);
				this.selection = null;
			} else {
				if (this.selection) {
					this.shrink(this.selection);
				}
				this.selection = bar;
				this.expand(bar);
			}
		}

		/**
		 * Handles click on a edge/connection of the diagram calling parent
		 * component's handler.
		 * 
		 * @public
		 * @method
		 * @param {Object} edge data object of the clicked edge.
		 */
		onEdgeClick(edge) {
			const {store, onEdgeClick} = this.props;
			
			onEdgeClick(
				store.framesByName[edge.primary],
				store.framesByName[edge.secondary],
			);
		}

		/**
		 * Expands one of the diagram nodes. This will hide all diagram connections
		 * except the ones where the parameter node is source or target. The score
		 * of these connections is also displayed.
		 * 
		 * @public
		 * @method
		 * @param {Object} node data object of the node being expanded.
		 */
		expand(node) {
			const filterFn =
				node.part === "primary"
					? (d => node.key === d.primary)
					: (d => node.key === d.secondary);

			this.bP.mouseover(node);
			this.bPg.selectAll(".score")
				.filter(filterFn)
				.text(d => scoreFormatter(d.value))
		}

		/**
		 * Shrinks all diagram node expansions, showing all edges and hiding score
		 * numbers.
		 * 
		 * @public
		 * @method
		 * @param {Object} node data object of the node being shrinked.
		 */
		shrink(node) {
			this.bP.mouseout(node);
			this.bPg.selectAll(".score").text("");
		}

		/**
		 * Gets the width of the text boxes for the diagram frame labels. The size
		 * is always defined based on the length of longest frame name.
		 * 
		 * @public
		 * @method
		 * @returns {number} width to be used for text boxes
		 */
		getLabelSize() {
			const {store} = this.props;
			let max = store.sankeyData[0];

			for (let edge of store.sankeyData) {
				if (edge[0].length > max.length) {
					max = edge[0];
				}
				if (edge[1].length > max.length) {
					max = edge[1];
				}
			}

			return getRenderedTextSize(max, 14);
		}

		/**
		 * Returns a mapping of each left side frame name to a color.
		 * 
		 * @public
		 * @method
		 * @returns {Object}
		 */
		getColorMap() {
			const {store} = this.props;
			const colorGen = colors();

			return [...new Set(store.sankeyData.map(x => x[0]))]
				.reduce((res, current) => {
					res[current] = colorGen.next().value;
					return res;
				}, {});
		}

		/**
		 * Renders the svg Sankey diagram using D3.js and sets up DOM events for its
		 * elements. This rendering should be controlled by D3.js and not ReactJS.
		 * This guarantees that the diagram will not be part of React's virtual
		 * DOM, thus preventing the framework from interfering with elements
		 * created by the library (D3.js).
		 * 
		 * @public
		 * @method
		 */
		renderSankey() {
			const {store} = this.props;
			const labelSize = this.getLabelSize();
			const colorMap = this.getColorMap();
			const svg = select(this.svg);

			svg.select("*").remove();
			svg.attr("width", this.width).attr("height", this.height);

			// Sankey dimensions
			const height = Math.max(this.height - 160, 400);
			const vMargin = Math.max((this.height - height) / 2, 0);
			const width = Math.min(600, Math.max(this.width - (2 * labelSize) - 160, 200));
			const hMargin = Math.max((this.width - width) / 2, 0);

			const g = svg.append("g").attr("transform", `translate(${hMargin}, ${vMargin})`);
			
			// Create layout for sankey (AKA bipartite graph)
			this.bP =
				viz.bP()
					.data(store.sankeyData)
					.min(12)
					.pad(1)
					.height(height)
					.width(width)
					.fill(d => colorMap[d.primary])
			
			this.bPg = g.call(this.bP);

			// Setting up events
			this.bPg.selectAll(".mainBars")
				.on("click", d => this.onNodeClick(d));
			
			this.bPg.selectAll(".edges")
				.on("click", d => this.onEdgeClick(d));

			// Appending score text elements
			this.bPg.selectAll(".subBars")
				.filter(d => d.part === "secondary")
				.append("text")
					.attr("class", "score")
					.attr("x", -58)
					.attr("y", 6)
			
			// Appending node name text elements
			this.bPg.selectAll(".mainBars")
				.append("text")
					.attr("class","label")
					.attr("x", d => (d.part === "primary" ? -30 : 30))
					.attr("y", () => 6)
					.text(d => d.key)
					.attr("text-anchor", d => (d.part === "primary" ? "end": "start"));
		}

		render() {
			const {store, uiState} = this.props;
			const data = store.sankeyData;
			this.height = uiState.height;
			this.width = uiState.width;

			return (
				<div className="visualization-container" style={{ minWidth: uiState.width }}>
					{
						data.length > 0
						? <svg ref={node => this.svg = node}></svg>
						: <h3 className="no-data-text">No data to show.</h3>
					}
					{store.isComputingSankey &&
						<div className="loading-overlay">
							<div className="loading-box">
								<span>Computing</span>
								<ScaleLoader height="24" color={'#3F51B5'} />
							</div>
						</div>
					}
				</div>
			)
		}
	}
);

export default Sankey;