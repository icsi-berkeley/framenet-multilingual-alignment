import { computed, decorate, flow, observable } from 'mobx';

// Default params of some scoring types
const DEFAULT_PARAMS = {
	attr_matching: {
		threshold: 0,
		displayOnlyFrameSet: true,
		sankeyMaxEdges: null,
		limitSankeyEdges: false,
	},
	lu_wordnet: {
		threshold: 0.4,
		displayOnlyFrameSet: false,
		sankeyMaxEdges: null,
		limitSankeyEdges: false,
	},
	lu_muse: {
		threshold: 0.75,
		displayOnlyFrameSet: false,
		sankeyMaxEdges: 5,
		limitSankeyEdges: true,
		neighborhoodSize: 5,
		similarityThreshold: 0.3,
	},
	lu_mean_muse: {
		threshold: 0.85,
		displayOnlyFrameSet: false,
		sankeyMaxEdges: 5,
		limitSankeyEdges: true,
	}
}

const FE_SCORING_TYPES = new Set([
	"fe_matching",
	"muse_fe_matching",
])

const LU_SCORING_TYPES = new Set([
	"lu_wordnet",
	"synset",
	"synset_inv",
	"lu_muse",
	"lu_bert",
	"lu_mean_muse",
])

/**
 * Awaits until main thread is free again.
 */
const oneMoment = () => new Promise(resolve => setTimeout(resolve))

/**
 * Computes the diagram edges based on the alignment scores.
 * 
 * @method
 * @param {Object} data input alignment data.
 * @returns {Array} edges of the sankey diagram with source, target and size.
 */
const loadEdges = async (data) => {
	const edges = {}
	let iter = 0
	let then = performance.now()

	for (let ai = 0; ai < data.alignments.length; ai++ ){
		let scores = data.alignments[ai].data
		let edgeArray = []
	
		if (scores) {
			for (let i = 0; i < scores.length; ++i) {
				for (let j = 0; j < scores[i].length; ++j) {
					let value = scores[i][j]
	
					if (value > 0) {
						edgeArray.push([data.indices[0][i], data.indices[1][j], value])
					}

					if (++iter % 1000 === 0) {
						let now = performance.now()
						if (now - then > 100) {
							await oneMoment()
							then = performance.now()
						}
					}
				}
			}

			edges[data.alignments[ai].id] = edgeArray;
		}
	}

	return edges;
}

/**
 * Check if two sets are equal in the sense that they have a matching set of
 * values.
 *
 * @param {Set} a 
 * @param {Set} b
 * @returns {Boolean} 
 */
const areSetsEqual = (a, b) => (
	(a.size === b.size) ? 
	[...a].every( value => b.has(value) ) : false
);

/**
 * MobX store for alignment data of a specific FrameNet database against
 * Berkeley FrameNet.
 */
class AlignmentStore {

	/**
	 * Name of the FrameNet database of loaded alignemnt.
	 */
	fndb

	/**
	 * Language of this.fndb, aka, L2.
	 */
	language

	/**
	 * Dictionary to hold multiple lists of non-zero alignment score between two
	 * frames, the key for each list is a string representing a scoring technique.
	 */
	edges = {}

	/**
	 * String indices of the scoring matrix of shape (M, N) where M is the number
	 * of english frames e N the number of L2 frames.
	 */
	indices = []

	/**
	 * Frame data dictionary with global ids as keys.
	 */
	frames = {}

	/**
	 * Frame data dictionary with frame names + language as keys.
	 */
	framesByName = {}

	/**
	 * Mapping of LU names to a list of relevant synsets.
	 */
	synsetsByLU = {}

	/**
	 * Synset data dictionary with synset ids as keys.
	 */
	synsetData = {}

	/**
	 * Mapping of english LU names to word vectors ids in L2 space.
	 */
	vectorIdsByLU = []

	/**
	 * Dictionary of words with vector ids as keys.
	 */
	wordsByVectorId = []

	/**
	 * Dictionary used for caching the vectors of frames.
	 */
	frameVectorCache = {}

	/**
	 * Object used to store the values of the parameters used in the most recent
	 * visualization.
	 */
	previousParams = {}

	/**
	 * Indicates whether the user needs to wait for some heavy operation.
	 */
	isLoading = false

	constructor(uiState) {
		this.uiState = uiState;
	}

	/**
	 * Returns the edges of a sankey diagram of the stored alignment respecting
	 * UI params. 
	 * 
	 * @public
	 * @method
	 * @returns {Array} edges of the sankey diagram with source, target and size.
	 */
	get sankeyData() {
		const state = this.uiState;
		const {scoring} = state;
		
		if (scoring) {
			const {params} = scoring;
			const frameSet = new Set(state.sankeyFrames.map(x => x.id));
			const filterFn = params.displayOnlyFrameSet
				? x => frameSet.has(x[0]) && frameSet.has(x[1]) && x[2] >= params.threshold
				: x => (frameSet.has(x[0]) || frameSet.has(x[1])) && x[2] >= params.threshold;
			const edges = this.getEdges(frameSet);
			const filtered = edges.filter(filterFn);

			return this.pruneEdges(filtered)
				.map(x => [
					this.frames[x[0]].name + '.' + this.frames[x[0]].language,
					this.frames[x[1]].name + '.' + this.frames[x[1]].language,
					x[2],
				]);
		} else {
			return [];
		}
	}

	/**
	 * Returns indices of lexical frames derived from this.indices.
	 * 
	 * @public
	 * @method
	 * @returns {Array[Array[string]]} 2-dimension array of index ids.
	 */
	get lexicalIndices() {
		return this.indices.map(i => i.filter(f => this.frames[f].LUs.length > 0));
	}

	/**
	 * Returns a sorted list of frames present in this alignment indicating if
	 * they can be selected for visualization. This method sets the "disabled"
	 * attribute for all options based on the selected scoring technique. For
	 * example: If the selected scoring depends on LUs but the Frame has none, it
	 * will be disabled in the selection widget.
	 * 
	 * @public
	 * @method
	 * @returns {Array} english + L2 frames in "Select" components option format.
	 */
	get frameOptions() {
		const {scoring} = this.uiState;
		const options = this.indices
			.flat()
			.map(x => ({
				id: x,
				label: this.frames[x].name + '.' + this.frames[x].language,
				disabled: false,
			}))
			.sort((a, b) => (a.label < b.label) ? -1 : (a.label > b.label) ? 1 : 0);

		if (!scoring)
			return options.map(x => ({ ...x, disabled: true }));
		
		if (FE_SCORING_TYPES.has(scoring.type))
			return options.map(x => ({ ...x, disabled: this.frames[x.id].FEs.length === 0 }))

		if (LU_SCORING_TYPES.has(scoring.type))
			return options.map(x => ({ ...x, disabled: this.frames[x.id].LUs.length === 0 }))

		return options;
	}

	/**
	 * Returns the LU matching graph definition of the selected alignemnt. When
	 * no alignment is selected, i.e., the UI state doesn't have a pair of
	 * selected frames, this method should return an empty list for both node and
	 * link definitions. The same applies with the method has no mapping between
	 * LUs (e.g. The alignment is score is the similarity of the average LU
	 * vector of each frame).
	 * 
	 * @public
	 * @method
	 * @returns {Object} Graph definition with a node list and a link list.
	 */
	get graphData() {
		const {scoring} = this.uiState;
		
		if (!scoring)
			return { nodes: [], links: [] };

		switch(scoring.type) {
			case 'lu_wordnet':
				return this.LUWordNetGraph();
			case 'synset':
			case 'synset_inv':
				return this.synsetGraph();
			case 'lu_muse':
			case 'lu_bert':
				return this.LUMuseGraph();
			case 'fe_matching':
				return this.FEMatchingGraph();
			default:
				return { nodes: [], links: [] };
		}
	}

	/**
	 * Gets the edges of the Sankey diagram for the selected scoring method. This
	 * function will recomputed edges if necessary, else it will return data from
	 * this.edges.
	 * 
	 * @public
	 * @method
	 * @param {Set} frameSet set of frames of interest.
	 * @returns {Array[Array]} edges of the sankey diagram in the format
	 * 	[source id, target id, score value].
	 */
	getEdges(frameSet) {
		const {scoring} = this.uiState;
		const {params} = scoring;
		const prevParams = this.previousParams[scoring.id] || {};
		let edges;

		if (scoring.type === 'lu_muse' || !this.edges[scoring.id]) {
			let recompute = false;

			for (let key of ['neighborhoodSize', 'similarityThreshold']) {
				if (prevParams[key] !== params[key]) {
					recompute = true;
					break;
				}
			}

			if (!recompute) {
				recompute = !areSetsEqual(prevParams['frameSet'], frameSet);
			}

			if (recompute) {
				edges = this.computeEdges(frameSet);
				this.edges[scoring.id] = edges;
			} else {
				edges = this.edges[scoring.id];
			}
		} else {
			edges = this.edges[scoring.id];
		}

		this.previousParams[scoring.id] = {...params};
		this.previousParams[scoring.id]['frameSet'] = frameSet;

		return edges;
	}

	/**
	 * Computes Sankey diagram edges of the given frame set. Each frame in this
	 * set will have its alignment score with all frames in the other language
	 * computed.
	 * 
	 * @public
	 * @method
	 * @param {Set} frameSet set of frames that edges will be computed.
	 * @returns {Array[Array]} edges of the sankey diagram in the format
	 * 	[source id, target id, score value].
	 */
	computeEdges(frameSet) {
		const edges = [];
		/**
		 * Indices are filtered to prevent duplicate edges when "frameSet" has
		 * english and L2 frames. For example, if "A" is an english frame and "B"
		 * is a L2 frame, "A" would first be scored against all L2 frames
		 * (including "B"). Later, "B" would be scored against all english frames;
		 * the alignment of the pair ("A", "B") would end up being calculated
		 * again. Of course, we could always check if the other frame is in the
		 * frame set before calculating the pair score, but filtering the indices
		 * yields the same results with less checks.
		 */
		const indices = [
			this.indices[0].filter(x => !frameSet.has(x)),
			this.indices[1],
		];
	
	
		for (let frameId of frameSet) {
			const frame = this.frames[frameId];
	
			if (frame.LUs.length === 0) {
				continue;
			} 
	
			if (frame.language === 'en') {
				edges.push(
					...indices[1].map(i => [frame.gid, i, this.LUVectorMatchingScore(frame, this.frames[i])])
				);
			} else {
				edges.push(
					...indices[0].map(i => [i, frame.gid, this.LUVectorMatchingScore(this.frames[i], frame)])
				);
			}
		}
		this.frameVectorCache = {};
		return edges.filter(x => x[2] > 0);
	}

	/**
	 * Computes the alignment score between the given frames using multilingual
	 * space vectors to match LUs.
	 * 
	 * @public
	 * @method
	 * @param {Object} bfnFrame the english frame data object.
	 * @param {Object} l2Frame the L2 frame data object.
	 */
	LUVectorMatchingScore(bfnFrame, l2Frame) {
		const {params} = this.uiState.scoring;

		if (!this.frameVectorCache[bfnFrame.gid]) {
			this.frameVectorCache[bfnFrame.gid] = 
				bfnFrame.LUs
					.map(x => this.vectorIdsByLU[x.gid])
					.filter(x => x)
					.flatMap(x => x.slice(0, params.neighborhoodSize))
					.filter(x => x[0] >= params.similarityThreshold);
		}

		if (!this.frameVectorCache[l2Frame.gid]) {
			this.frameVectorCache[l2Frame.gid] = new Set(
				l2Frame.LUs
					.flatMap(x => this.vectorIdsByLU[x.gid])
					.filter(x => x)
					.map(x => x[1])
			);
		}
	
		const matches = this.frameVectorCache[bfnFrame.gid]
				.filter(x => x && this.frameVectorCache[l2Frame.gid].has(x[1]));
		
		return matches.length / bfnFrame.LUs.length;
	}

	/**
	 * Returns the LU matching graph definition for lu_wordnet scoring, where
	 * two LUs are matched when both are in the same synset.
	 * 
	 * @public
	 * @method
	 * @returns {Object} Graph definition with a node list and a link list.
	 */
	LUWordNetGraph() {
		const nodes = this.getNodes();
		const inter = this.getConnectionObjects(nodes, this.synsetsByLU);
		const links = inter.links.filter(l => l.target.hasLeftSource);

		nodes.push(...inter.nodes.filter(n => n.hasLeftSource));
		links.filter(l => l.source.type === 'right').forEach(l => {
			let swap = l.source;
			l.source = l.target;
			l.target = swap;
		})
		nodes.forEach(n => n.isReferenceNode = n.type === 'left');
		links
			.filter(l => (l.source.type === 'left' && l.target.isIntersection))
			.forEach(l => {
				l.source.isMatchingNode = true;
			});
		this.computeDegrees(links);

		return { nodes, links };
	}

	/**
	 * Returns the LU matching graph definition for synset/synset_inv scoring,
	 * where a set of synsets is defined for each frame (based on their LUs) and
	 * the intersection between two sets is the base of the alignment between two
	 * frames.
	 * 
	 * @public
	 * @method
	 * @returns {Object} Graph definition with a node list and a link list.
	 */
	synsetGraph() {
		const type = this.uiState.scoring.type;
		const nodes = this.getNodes();
		const inter = this.getConnectionObjects(nodes, this.synsetsByLU);
		const links = inter.links;

		nodes.push(...inter.nodes);
		const isReferenceFn = type === 'synset' ? n => n.hasLeftSource : n => n.hasRightSource;
		nodes.forEach(n => {
			n.isReferenceNode = isReferenceFn(n);
			n.isMatchingNode = n.isIntersection;
		})
		this.computeDegrees(links);

		return { nodes, links };
	}

	/**
	 * Returns the LU matching graph definition for lu_muse scoring, where a
	 * match between two LUs happen when the cosine similarity of their vectors
	 * is more than a given threshold.
	 * 
	 * @public
	 * @method
	 * @returns {Object} Graph definition with a node list and a link list.
	 */
	LUMuseGraph() {
		const nodes = this.getNodes();
		const inter = this.getConnectionObjects(nodes, this.vectorIdsByLU, x => this.wordsByVectorId[x]);
		const links = inter.links.filter(l => l.target.hasLeftSource);

		nodes.push(...inter.nodes.filter(n => n.hasLeftSource));
		links.filter(l => l.source.type === 'right').forEach(l => {
			let swap = l.source;
			l.source = l.target;
			l.target = swap;
		})
		nodes.forEach(n => n.isReferenceNode = n.type === 'left');
		links
			.filter(l => (l.source.type === 'left' && l.target.isIntersection))
			.forEach(l => l.source.isMatchingNode = true);
		this.computeDegrees(links);

		return { nodes, links };
	}

	/**
	 * Returns the FE matching graph definition where a match between two FEs
	 * happens when both have the same name.
	 * 
	 * @public
	 * @method
	 * @returns {Object} Graph definition with a node list and a link list.
	 */
	FEMatchingGraph() {
		const nodes = this.getNodes("FEs", x => x.name);
		const links = [];

		nodes.forEach(x => x.isReferenceNode = true);
		const left = nodes.filter(x => x.type === "left");
		const right = nodes.filter(x => x.type === "right");

		for (let a of left) {
			for (let b of right) {
				if (a.type !== b.type && a.name === b.name) {
					links.push({ 
						source: a,
						target: b, 
					})
					a.isMatchingNode = true;
					b.isMatchingNode = true;
				}
			}
		}

		return { nodes, links };
	}

	/**
	 * Creates an object containing default information of a graph node.
	 * 
	 * @public
	 * @method
	 * @returns {Object} graph node object.
	 */
	createNode = () => ({ inDegree: 0, outDegree: 0, });

	/**
	 * Returns the list of nodes of the selected frames distinguishing the source
	 * frame of the node between "left" and "right".
	 * 
	 * @public
	 * @method
	 * @param {string} frameAttr frame attribute that holds nodes base objects.
	 * @param {Func} nodeNameFn name getter for a graph node.
	 * @returns {Array} list of LU nodes.
	 */
	getNodes(frameAttr = "LUs", nodeNameFn = x => x['name']) {
		const {selectedFrames} = this.uiState;

		if (selectedFrames[0] && selectedFrames[1]) {
			return this.frames[selectedFrames[0]][frameAttr]
				.map(x => ({
					type: 'left',
					...this.createNode(),
					...(typeof x === "object" ? x : null),
					'name': nodeNameFn(x),
				}))
				.concat(
					this.frames[selectedFrames[1]][frameAttr]
					.map(x => ({
						type: 'right',
						...this.createNode(),
						...(typeof x === "object" ? x : null),
						'name': nodeNameFn(x),
					}))
				);
		} else {
			return [];
		}
	}

	/**
	 * Generates intermediate node objects for a graph based on the mapping of
	 * LUs to these nodes. An intermediate node can be, for example, a synset
	 * node that was used as  "translator". The method returns those nodes and
	 * their links to LU nodes.
	 * 
	 * @public
	 * @method
	 * @param {Array} LUNodes list of LU nodes.
	 * @param {Object} relationMap mapping of LUs to intermediate node ids.
	 * @param {function} nodeNameFn function to get the name of a node using id.
	 * @returns {Object} A object containing the intermediate nodes of the graph
	 * and their links to LU nodes.
	 */
	getConnectionObjects(LUNodes, relationMap, nodeNameFn=x=>x) {
		const {params} = this.uiState.scoring;

		const links = LUNodes
			.flatMap(s =>
				(relationMap[s.gid] || [])
					.slice(0, params.neighborhoodSize)
					.filter(t => !Array.isArray(t) || t[0] > params.similarityThreshold)
					.map(t => ({
						source: s,
						target: Array.isArray(t) ? t[1] : t,
						isDirected: true,
					}))
			)
		// Creating node objects for intermediate Nodes
		const intermediateMap = {}
		const nodes = [...new Set(links.map(l => l.target))]
				.map(t => {
					const node = {
						type: 'intermediate',
						...this.createNode(),
						'name': nodeNameFn(t),
					};
					intermediateMap[t] = node;
					return node;
				});
		// Including references to objects in links
		links.forEach(l => {
			l.target = intermediateMap[l.target];
			l.target[l.source.type === 'left' ? 'hasLeftSource' : 'hasRightSource'] = true;
		});
		nodes.forEach(n => n.isIntersection = n.hasLeftSource && n.hasRightSource);

		return { nodes, links };
	}

	/**
	 * Computes the degrees of each node in a graph based on its link Array.
	 * 
	 * @public
	 * @method
	 * @param {Array} links link list of a graph.
	 */
	computeDegrees(links) {
		links.forEach(l => {
			++l.source.outDegree;
			++l.target.inDegree;
		});
	}

	/**
	 * Filters the Sankey diagram edge list based on the UI visualization params.
	 * The list is returned unchanged when limitation of edges on the Sankey
	 * diagram is disabled.
	 * 
	 * @public
	 * @method
	 * @param {Array} edges Sankey diagram edges.
	 * @returns {Array} filtered array of edges.
	 */
	pruneEdges(edges) {
		const {params} = this.uiState.scoring;

		if (!params.limitSankeyEdges)
			return edges;

		edges.sort((a, b) => {
			if (a[0] > b[0]) {
				return -1;
			} else if (a[0] < b[0]) {
				return 1;
			} else {
				return a[2] > b[2] ? -1 : a[2] < b[2] ? 1 : 0;
			}
		});

		const counts = {};

		edges.forEach(x => counts[x[0]] = 0);

		return edges.filter(x => {
			++counts[x[0]];
			return counts[x[0]] <= params.sankeyMaxEdges;
		});
	}

	/**
	 * Loads a JSON alignment file into the store.
	 * 
	 * @public
	 * @method
	 * @param {Object} data parsed alignment JSON file.
	 */
	load = flow(function * (data) {
		this.fndb = data.db[1];
		this.language = data.lang[1];
		this.edges = yield loadEdges(data)

		this.framesByName = {};
		for (let key in data.frames) {
			if (Object.prototype.hasOwnProperty.call(data.frames, key)) {
				let frame = data.frames[key];
				this.framesByName[frame.name + '.' + frame.language] = frame;
			}
		}

		this.uiState.scoringOptions =
			data.alignments.map(x => ({
				id: x.id,
				desc: x.desc,
				type: x.type,
				params: DEFAULT_PARAMS[x.type] || {
					threshold: 0.1,
					displayOnlyFrameSet: false,
					sankeyMaxEdges: null,
					limitSankeyEdges: false,
				}
			}));

		this.indices = data.indices;
		this.frames = data.frames;
		this.synsetsByLU = data.resources.lu_to_syn;
		this.synsetData = data.resources.syn_data;
		this.vectorIdsByLU = data.resources.lu_vec_nn;
		this.wordsByVectorId = data.resources.id2word;

		// Resets
		this.uiState.setSelectedFramePair(null, null);
		this.uiState.scoring = null;
		this.uiState.sankeyFrames = [];
	})

}

decorate(AlignmentStore, {
	fndb: observable,
	language: observable,
	indices: observable,
	frames: observable,
	synsetsByLU: observable,
	synsetData: observable,
	vectorIdsByLU: observable,
	wordsByVectorId: observable,
	isLoading: observable,
	lexicalIndices: computed,
	sankeyData: computed,
	frameOptions: computed,
});

export default AlignmentStore;