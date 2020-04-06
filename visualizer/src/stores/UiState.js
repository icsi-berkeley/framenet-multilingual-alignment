import { action, computed, 	decorate, observable } from "mobx"

/**
 * MobX store for global UI state.
 */
class UiState {

	/**
	 * If the application sidebar is open.
	 */
	isSidebarOpen = true

	/**
	 * If the selected alignment (this.selectedFrames) visualization must be
	 * visible.
	 */
	isAlignmentDetailVisible = false

	/**
	 * Selected alignment scoring method.
	 */
	scoring = null

	/**
	 * Existing alignment scoring options.
	 */
	scoringOptions = []

	/**
	 * Selected frames for Sankey diagram.
	 */
	sankeyFrames = []

	/**
	 * Selected frame pair for alignment detailed visualization.
	 */
	selectedFrames = [null, null]

	height = null

	width = null

	/**
	 * Gets available scoring options.
	 * 
	 * @public
	 * @method
	 * @returns {Array} list of scoring options.
	 */
	get scoringSelectOptions() {
		return this.scoringOptions.map(x => ({ value: x.id, label: x.desc }));
	}

	/**
	 * Sets the active scoring method of the visualizer.
	 * 
	 * @public
	 * @method
	 * @param {string} id scoring option id.
	 */
	setScoring(id) {
		this.scoring = this.scoringOptions.find(x => x.id === id);
	}

	/**
	 * Sets the selected frame pair.
	 * 
	 * @public
	 * @method
	 * @param {string} source source frame id/
	 * @param {string} target target frame id.
	 */
	setSelectedFramePair = action((source, target) => {
		this.selectedFrames[0] = source;
		this.selectedFrames[1] = target;
	})

}

decorate(UiState, {
	isSidebarOpen: observable,
	isAlignmentDetailVisible: observable,
	scoring: observable,
	scoringOptions: observable,
	sankeyFrames: observable,
	selectedFrames: observable,
	height: observable,
	width: observable,
	scoringSelectOptions: computed,
});

export default UiState;