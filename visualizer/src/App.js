import React from 'react';
import ReactResizeDetector from 'react-resize-detector';

import "@kenshooui/react-multi-select/dist/style.css";
import './App.css';

import ChartPanel from './components/ChartPanel';
import Sidebar from './components/Sidebar';
import AlignmentStore from './stores/AlignmentStore';
import UiState from './stores/UiState';

const uiState = new UiState();
const store = new AlignmentStore(uiState);

function onResize (width, height) {
	uiState.width = width;
	uiState.height = height;
}

function App() {
	return (
		<div className="App">
			<Sidebar store={store} uiState={uiState} />
			<div className="app-body">
				<ChartPanel store={store} uiState={uiState} />
				<ReactResizeDetector handleWidth handleHeight onResize={onResize} />
			</div>
		</div>
	);
}

export default App;
