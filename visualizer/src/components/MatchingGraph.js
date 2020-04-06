import React from 'react';
import PropTypes from 'prop-types';
import {format} from 'd3-format';
import {select} from 'd3-selection';

import './MatchingGraph.css';

const scoreFormatter = format(".3f");

/**
 * A component for lexical unit matching graphs.
 */
class MatchingGraph extends React.Component {
	static propTypes = {
		/**
		 * An object containing the graph definition: an array of nodes under
		 * "nodes" and an array of edges under "links".s
		 */
		data: PropTypes.object,
		/**
		 * The frame pair of the FEs/LUs used for rendering the graph.
		 */
		framePair: PropTypes.array,
		/**
		 * A callback called when mouse is placed over of the nodes.
		 */
		onMouseOverNode: PropTypes.func,
		/**
		 * A callback called when mouse is leaves of the nodes.
		 */
		onMouseOutNode: PropTypes.func,
	}

	constructor() {
		super();
		this.root = null;
		this.links = null;
		this.nodes = null;
	}

	/**
	 * Manually invokes D3.js rendering function when the component is mounted.
	 * 
	 * @public
	 * @method
	 */
	componentDidMount() {
		this.renderGraph();
	}

	/**
	 * Manually invokes D3.js rendering function when the component is updated.
	 * 
	 * @public
	 * @method
	 */
	componentDidUpdate() {
		this.renderGraph();
	}

	/**
	 * Computes the path string for the path element of the given link data.
	 * 
	 * @public
	 * @method
	 * @param {Object} datum Link data object.
	 * @returns {string} A string of path commands.
	 */
	computePath(datum) {
		let direction;
		let x1 = datum.source.x;
		let y1 = datum.source.y - (datum.source.height/4);
		let x2 = datum.target.x;
		let y2 = datum.target.y - (datum.target.height/4);

		if (datum.source.type === 'left') {
			x1 += datum.source.width + 12;
			x2 -= datum.target.width/2 + 16;
			direction = 1;
		} else if (datum.source.type === 'intermediate') {
			x1 += (datum.source.width/2) + 12;
			x2 -= datum.target.width + 16;
			direction = 1;
		} else {
			x1 -= datum.source.width + 12;
			x2 += (datum.target.width/2) + 18;
			direction = -1;
		}

		const offset = 15;
		const ccoef = (Math.abs(x1 - x2)-2*offset)/2.25;

		return `
			M ${x1}                 ${y1}
			L ${x1 + 3*direction}   ${y1}
			C ${x1+ccoef*direction} ${y1}, ${x2-ccoef*direction} ${y2}, ${x2+offset*-direction} ${y2}
			L ${x2}                 ${y2}
		`;
	}

	/**
	 * Renders the graph footer that shows the frame names and the alignment
	 * score of the pair.
	 * 
	 * @public
	 * @method
	 * @param {Object} data Graph data object as returned by getRenderingData.
	 */
	includeFooter(data) {
		const { framePair, height, width, margin } = this.props;
		const svg = select(this.root).select("svg");
		const matching = data.nodes.filter(d => d.isMatchingNode).length;
		const reference = data.nodes.filter(d => d.isReferenceNode && !d.isMatchingNode).length;
		
		if (framePair[0] && framePair[1]) {
			const right = framePair[0];
			const left = framePair[1];

			svg.select("#title")
			.attr("x", margin)
			.attr("y", height-margin/2)
			.attr("class", "graph-info")
			.text(`Frames: ${right.name} (${right.gid}), ${left.name} (${left.gid})`)

			svg.select("#stats")
				.attr("x", width-margin)
				.attr("y", height-margin/2)
				.attr("class", "graph-info graph-score")
				.html(`
					Alignment score:
					<tspan class="match">${matching}</tspan>
					÷
					(
					<tspan class="match">${matching}</tspan>
					+
					<tspan class="reference">${reference}</tspan>
					)
					= ${scoreFormatter(matching/(matching + reference))}`)
		}
	}

	/**
	 * Renders the matching graph using D3.js and sets up DOM events for its
	 * elements. This rendering should be controlled by D3.js and not ReactJS.
	 * This guarantees that the diagram will not be part of React's virtual
	 * DOM, thus preventing the framework from interfering with elements
	 * created by the library (D3.js).
	 * 
	 * @public
	 * @method
	 */
	renderGraph() {
		const { data, height, width } = this.props;
		const svg = select(this.root).select("svg");

		svg
			.attr("height", height)
			.attr("width", width);

		this.nodes = svg.select("#nodes")
			.selectAll("text")
			.data(data.nodes)
			.join("text")
				.text(d => d.name)
				.each(function(d) {
					const bbox = this.getBBox();
					d.width = bbox.width;
					d.height = bbox.height + 2;
				})
				.attr("x", d => d.x)
				.attr("y", d => d.y)
				.attr("text-anchor", d => d.type === 'left' ? 'start' : d.type === 'right' ? 'end' : 'middle')
				.attr("class", d => {
					let name = "node";
					if (d.isMatchingNode) {
						name += " match";
					} else if (d.isReferenceNode) {
						name += " ref";
					}
					return name;
				})
				.attr("opacity", 0.75)
				.on("mouseover", d => this.onMouseOverNode(d))
				.on("mouseout", d => this.onMouseOutNode(d))

		this.links = svg.select("#links")
			.selectAll("path")
			.data(data.links)
			.join("path")
				.attr("d", this.computePath)
				.attr("marker-end", d => d.isDirected ? "url(#arrowhead)" : null)
				.attr("stroke", "#555")
				.attr("fill-opacity", 0)
				.attr("opacity", 0.1)

		this.includeFooter(data);
	}

	/**
	 * Handles mouse over node event highlighting the element and its links. It
	 * also invokes the handler of the parent component when it is passed via
	 * props.
	 * 
	 * @public
	 * @method
	 * @param {Object} datum Node data object.
	 */
	onMouseOverNode(datum) {
		const linked = new Set();

		this.links
			.filter(d => d.source === datum || d.target === datum)
			.each(d => {
				linked.add(d.source);
				linked.add(d.target);
			})
			.attr("opacity", 1);

		this.nodes.filter(d => linked.has(d))
			.style("font-weight", "bold")
			.attr("opacity", 1);

		if (this.props.onMouseOverNode)
			this.props.onMouseOverNode(datum, this.nodes, this.links);
	}

	/**
	 * Handles mouse out of node event, removing any highlight that was applied
	 * before and invoking the parent component's handler when it is passed via
	 * props.
	 * 
	 * @public
	 * @method
	 */
	onMouseOutNode() {
		this.links.attr("opacity", 0.1);
		this.nodes
			.style("font-weight", "normal")
			.attr("opacity", 0.75);

		select("#synset-tooltip").style("display", "none");

		if (this.props.onMouseOutNode)
			this.props.onMouseOutNode();
	}

	render() {
		const {data, width} = this.props;

		return (
			<div
				className="visualization-container"
				style={{ minWidth: width }}
				ref={node => this.root = node}
			>
				{
					data.nodes.length > 0
					?
						<svg>
							<defs>
								<marker id="arrowhead"
									markerWidth="10" markerHeight="7" 
									refX="0" refY="3.5" orient="auto">
									<polygon points="0 0, 10 3.5, 0 7" fill="#555" />
								</marker>
							</defs>
							<g id="nodes" />
							<g id="links" />
							<text id="title" />
							<text id="stats" />
						</svg>
					: <h3 className="no-data-text">No data to show.</h3>
				}
			</div>
		);
	}

}

export default MatchingGraph;