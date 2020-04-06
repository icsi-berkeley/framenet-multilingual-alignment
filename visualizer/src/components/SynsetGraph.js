import React from 'react';
import PropTypes from 'prop-types';
import {observer} from 'mobx-react';
import {select} from 'd3-selection';

import './SynsetGraph.css';

import LUMatchingGraph from './LUMatchingGraph';
import AlignmentStore from '../stores/AlignmentStore';

/**
 * A component based on LUMatchingGraph with specific functionalities for
 * Synset matching visualization.
 */
const SynsetGraph = observer(
	class SynsetGraph extends React.Component {
		static propTypes = {
			/**
			 * A mobx store of frame alignments.
			 */
			store: PropTypes.instanceOf(AlignmentStore),
		}

		posRegex = /\.\w{1,4}$/gi

		/**
		 * Returns the HTML string to be used when rendering a lemma.
		 * 
		 * @public
		 * @method
		 * @param {string} lemma the lemma strin
		 * @param {boolean} isHighlighted whether the lemma should be highlighted.
		 * @returns {string} HTML string for the lemma.
		 */
		lemmaHtml(lemma, isHighlighted) {
			if(isHighlighted)
				return `<span class="synset-lemma highlighted">${lemma}</span>`;
			else
				return `<span class="synset-lemma">${lemma}</span>`;
		}

		/**
		 * Handles mouse over node event. If the hovered node represents a synset
		 * the synset tooltip will be rendered next to it by this method.
		 * 
		 * @public
		 * @method
		 */
		onMouseOverNode = (datum, nodes, links) => {
			if (datum.type !== 'intermediate')
				return;

			const {store} = this.props;
			const synset = store.synsetData[datum.name];
			const language = store.language;
			const highlighted = new Set();

			links.each(d => {
				highlighted.add(d.source.name.replace(this.posRegex, ''))
				highlighted.add(d.target.name.replace(this.posRegex, ''))
			});

			// Updating tooltip box
			select("#synset-name").html(datum.name);
			select("#synset-desc").html(synset.definition);
			select("#synset-eng-lemmas")
				.html(synset["en"].map(l => this.lemmaHtml(l, highlighted.has(l))).join(", "))
			select("#synset-l2-title").html(`${language}:`)
			select("#synset-l2-lemmas")
				.html(synset[language].map(l => this.lemmaHtml(l, highlighted.has(l))).join(", "))

			// Rendering tooltip with the right coordinates
			const tooltip = select("#synset-tooltip");
			tooltip.style("display", "block");
			const bbox = tooltip.node().getBoundingClientRect();
			let top = datum.y + datum.height/2;

			if (datum.y + bbox.height > window.innerHeight) {
				top = datum.y - datum.height - bbox.height;
			} else {
				top = datum.y + datum.height/2;
			}

			tooltip
				.style("top", `${top}px`)
				.style("left", `${datum.x+12}px`)
		}

		/**
		 * Handles mouse out of node event. The synset tooltip is hidden.
		 * 
		 * @public
		 * @method
		 */
		onMouseOutNode() {
			select("#synset-tooltip").style("display", "none");
		}

		render() {
			const {store, uiState, framePair} = this.props;

			return (
				<div
					className="visualization-container"
					style={{ minWidth: uiState.width }}
					ref={node => this.root = node}
				>
					<div id="synset-graph-content">
						<div id="synset-tooltip">
							<div className="synset-lang-title large" id="synset-name"></div>
							<div id="synset-desc"></div>
							<div className="synset-lang-title">eng:</div>
							<div id="synset-eng-lemmas"></div>
							<div className="synset-lang-title" id="synset-l2-title" />
							<div id="synset-l2-lemmas"></div>
						</div>
						<LUMatchingGraph
							store={store}
							uiState={uiState}
							framePair={framePair}
							onMouseOverNode={this.onMouseOverNode}
							onMouseOutNode={this.onMouseOutNode}
						/>
					</div>
				</div>
			);
		}
	}
)

export default SynsetGraph;