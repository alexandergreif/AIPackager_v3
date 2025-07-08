document.addEventListener('DOMContentLoaded', () => {
    const modelSelector = document.getElementById('model-selector');
    const scenarioSelector = document.getElementById('scenario-selector');
    const evaluationForm = document.getElementById('evaluation-form');
    const startEvaluationBtn = document.getElementById('start-evaluation-btn');
    const evaluationSpinner = document.getElementById('evaluation-spinner');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const evaluationError = document.getElementById('evaluation-error');
    const resultsContainer = document.getElementById('evaluation-results-container');
    const pastEvaluationsTable = document.getElementById('past-evaluations-table');

    const newEvaluationModal = document.getElementById('new-evaluation-modal');
    const openEvaluationModalBtn = document.getElementById('open-evaluation-modal-btn');
    const newEvaluationModalCloseBtn = document.getElementById('new-evaluation-modal-close-btn');

    const selectAllModelsBtn = document.getElementById('select-all-models');
    const deselectAllModelsBtn = document.getElementById('deselect-all-models');
    const selectAllScenariosBtn = document.getElementById('select-all-scenarios');
    const deselectAllScenariosBtn = document.getElementById('deselect-all-scenarios');

    // Details modal elements removed - now using full-page view

    // New elements for enhanced functionality
    const filterInput = document.getElementById('filter-input');
    const sortSelect = document.getElementById('sort-select');
    const resultsCount = document.getElementById('results-count');
    const exportCsvBtn = document.getElementById('export-csv-btn');
    const refreshBtn = document.getElementById('refresh-evaluations-btn');
    const modelsLoading = document.getElementById('models-loading');
    const scenariosLoading = document.getElementById('scenarios-loading');
    const evaluationsLoading = document.getElementById('evaluations-loading');
    const evaluationsEmpty = document.getElementById('evaluations-empty');
    const retryBtn = document.getElementById('retry-evaluation');
    const errorMessage = document.getElementById('error-message');
    const completedRuns = document.getElementById('completed-runs');
    const totalRuns = document.getElementById('total-runs');

    // State management
    let allEvaluations = [];
    let filteredEvaluations = [];
    let currentFilter = '';
    let currentSort = 'timestamp-desc';

    const api = {
        getModels: () => fetch('/api/evaluations/models').then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            return res.json();
        }),
        getScenarios: () => fetch('/api/evaluations/scenarios').then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            return res.json();
        }),
        getEvaluations: () => fetch('/api/evaluations').then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            return res.json();
        }),
        getEvaluationLog: (logPath) => fetch(`/api/evaluations/logs?path=${encodeURIComponent(logPath)}`).then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            return res.text();
        }),
        runEvaluation: (model_ids, scenario_ids) => fetch('/api/evaluations/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model_ids, scenario_ids }),
        }).then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            return res.json();
        }),
    };
    const socket = io();

    function createCard(item, type) {
        const card = document.createElement('div');
        card.className = `glass-card p-4 ${type}-card cursor-pointer flex items-start`;
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'mr-4 mt-1 h-4 w-4 text-accent-purple bg-secondary-bg border-border-color rounded focus:ring-accent-purple';
        checkbox.dataset.id = item.id;
        checkbox.dataset.type = type;

        const content = document.createElement('div');
        content.innerHTML = `
            <h4 class="font-bold text-text-primary">${item.name || item.title}</h4>
            <p class="text-sm text-text-secondary">${item.description || `Category: ${item.category}`}</p>
        `;

        card.appendChild(checkbox);
        card.appendChild(content);

        card.addEventListener('click', (e) => {
            if (e.target !== checkbox) {
                checkbox.checked = !checkbox.checked;
            }
            card.classList.toggle('selected', checkbox.checked);
            updateButtonState();
        });

        return card;
    }

    function getSelectedIds(type) {
        const selector = type === 'model' ? modelSelector : scenarioSelector;
        return Array.from(selector.querySelectorAll(`input[type="checkbox"]:checked`)).map(cb => cb.dataset.id);
    }

    function updateButtonState() {
        const selectedModels = getSelectedIds('model');
        const selectedScenarios = getSelectedIds('scenario');
        startEvaluationBtn.disabled = !(selectedModels.length > 0 && selectedScenarios.length > 0);
        
        // Save selections to localStorage
        localStorage.setItem('selectedModels', JSON.stringify(selectedModels));
        localStorage.setItem('selectedScenarios', JSON.stringify(selectedScenarios));
    }

    function loadSavedSelections() {
        try {
            const savedModels = JSON.parse(localStorage.getItem('selectedModels') || '[]');
            const savedScenarios = JSON.parse(localStorage.getItem('selectedScenarios') || '[]');
            
            // Apply saved model selections
            savedModels.forEach(id => {
                const checkbox = modelSelector.querySelector(`input[data-id="${id}"]`);
                if (checkbox) {
                    checkbox.checked = true;
                    checkbox.closest('.model-card')?.classList.add('selected');
                }
            });
            
            // Apply saved scenario selections
            savedScenarios.forEach(id => {
                const checkbox = scenarioSelector.querySelector(`input[data-id="${id}"]`);
                if (checkbox) {
                    checkbox.checked = true;
                    checkbox.closest('.scenario-card')?.classList.add('selected');
                }
            });
            
            updateButtonState();
        } catch (e) {
            console.warn('Failed to load saved selections:', e);
        }
    }

    function getTrustScoreClass(score) {
        if (score >= 0.8) return 'trust-score-excellent';
        if (score >= 0.6) return 'trust-score-good';
        return 'trust-score-poor';
    }

    function showLoadingState(type) {
        if (type === 'models') {
            modelSelector.classList.add('hidden');
            modelsLoading.classList.remove('hidden');
        } else if (type === 'scenarios') {
            scenarioSelector.classList.add('hidden');
            scenariosLoading.classList.remove('hidden');
        } else if (type === 'evaluations') {
            pastEvaluationsTable.parentElement.classList.add('hidden');
            evaluationsEmpty.classList.add('hidden');
            evaluationsLoading.classList.remove('hidden');
        }
    }

    function hideLoadingState(type) {
        if (type === 'models') {
            modelSelector.classList.remove('hidden');
            modelsLoading.classList.add('hidden');
        } else if (type === 'scenarios') {
            scenarioSelector.classList.remove('hidden');
            scenariosLoading.classList.add('hidden');
        } else if (type === 'evaluations') {
            pastEvaluationsTable.parentElement.classList.remove('hidden');
            evaluationsLoading.classList.add('hidden');
        }
    }

    async function loadInitialData() {
        try {
            // Show loading states
            showLoadingState('models');
            showLoadingState('scenarios');
            showLoadingState('evaluations');

            const [models, scenarios, evaluations] = await Promise.all([
                api.getModels(),
                api.getScenarios(),
                api.getEvaluations(),
            ]);

            // Load models
            modelSelector.innerHTML = '';
            models.forEach(model => modelSelector.appendChild(createCard(model, 'model')));
            hideLoadingState('models');

            // Load scenarios
            scenarioSelector.innerHTML = '';
            scenarios.forEach(scenario => scenarioSelector.appendChild(createCard(scenario, 'scenario')));
            hideLoadingState('scenarios');

            // Load evaluations
            allEvaluations = evaluations;
            applyFiltersAndSort();
            hideLoadingState('evaluations');

            // Load saved selections
            loadSavedSelections();
            updateButtonState();
        } catch (error) {
            console.error('Failed to load initial data:', error);
            hideLoadingState('models');
            hideLoadingState('scenarios');
            hideLoadingState('evaluations');
            showError('Failed to load data: ' + error.message);
        }
    }

    function showError(message) {
        errorMessage.textContent = message;
        evaluationError.classList.remove('hidden');
    }

    function hideError() {
        evaluationError.classList.add('hidden');
    }

    function filterEvaluations(evaluations, filterText) {
        if (!filterText) return evaluations;
        
        const filter = filterText.toLowerCase();
        return evaluations.filter(e => 
            e.model.name.toLowerCase().includes(filter) ||
            e.scenario.title.toLowerCase().includes(filter) ||
            e.scenario.category?.toLowerCase().includes(filter)
        );
    }

    function sortEvaluations(evaluations, sortBy) {
        const sorted = [...evaluations];
        
        switch (sortBy) {
            case 'timestamp-desc':
                return sorted.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            case 'timestamp-asc':
                return sorted.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
            case 'trust-score-desc':
                return sorted.sort((a, b) => b.metrics.trust_score - a.metrics.trust_score);
            case 'trust-score-asc':
                return sorted.sort((a, b) => a.metrics.trust_score - b.metrics.trust_score);
            case 'model-asc':
                return sorted.sort((a, b) => a.model.name.localeCompare(b.model.name));
            case 'scenario-asc':
                return sorted.sort((a, b) => a.scenario.title.localeCompare(b.scenario.title));
            default:
                return sorted;
        }
    }

    function applyFiltersAndSort() {
        // Filter evaluations
        filteredEvaluations = filterEvaluations(allEvaluations, currentFilter);
        
        // Sort evaluations
        filteredEvaluations = sortEvaluations(filteredEvaluations, currentSort);
        
        // Render results
        renderPastEvaluations(filteredEvaluations);
        
        // Update results count
        if (resultsCount) {
            resultsCount.textContent = filteredEvaluations.length;
        }
    }

    function renderPastEvaluations(evaluations) {
        pastEvaluationsTable.innerHTML = '';
        
        if (evaluations.length === 0) {
            if (allEvaluations.length === 0) {
                // No evaluations at all - show empty state
                pastEvaluationsTable.parentElement.classList.add('hidden');
                evaluationsEmpty.classList.remove('hidden');
            } else {
                // Evaluations exist but filtered out
                pastEvaluationsTable.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-text-secondary">No evaluations match your filter criteria.</td></tr>';
                pastEvaluationsTable.parentElement.classList.remove('hidden');
                evaluationsEmpty.classList.add('hidden');
            }
            return;
        }

        // Hide empty state and show table
        pastEvaluationsTable.parentElement.classList.remove('hidden');
        evaluationsEmpty.classList.add('hidden');
        
        evaluations.forEach(e => {
            const row = document.createElement('tr');
            row.className = 'border-b border-border-color hover:bg-secondary-bg transition-colors';
            
            const trustScoreClass = getTrustScoreClass(e.metrics.trust_score);
            const trustScoreDisplay = (e.metrics.trust_score * 100).toFixed(1) + '%';
            
            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-text-primary font-medium">${e.model.name}</td>
                <td class="px-6 py-4 whitespace-nowrap text-text-primary">${e.scenario.title}</td>
                <td class="px-6 py-4 whitespace-nowrap font-bold ${trustScoreClass}">${trustScoreDisplay}</td>
                <td class="px-6 py-4 whitespace-nowrap text-text-primary">${e.metrics.hallucinations_found || 0}</td>
                <td class="px-6 py-4 whitespace-nowrap text-text-primary">${e.metrics.hallucinations_corrected || 0}</td>
                <td class="px-6 py-4 whitespace-nowrap text-text-secondary">${new Date(e.timestamp).toLocaleString()}</td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <a href="/evaluations/${e.id}" class="text-accent-blue hover:underline focus:outline-none focus:underline">View Details</a>
                </td>
            `;
            pastEvaluationsTable.appendChild(row);
        });
    }

    function renderEvaluationResult(result, logContent = null) {
        const formatReport = (title, report, isCorrection = false) => {
            if (!report || report.length === 0) {
                return `<div><h4 class="font-semibold text-accent-green mb-2">${title}</h4><p class="text-sm text-text-secondary">None</p></div>`;
            }
            return `
                <div>
                    <h4 class="font-semibold text-accent-green mb-2">${title}</h4>
                    <ul class="space-y-3">
                        ${report.map(item => `
                            <li class="text-sm text-text-secondary border-l-2 border-border-color pl-3">
                                <strong class="text-text-primary">${isCorrection ? 'Correction' : item.type}:</strong> ${isCorrection ? item.original : (item.text || 'N/A')}
                                <pre class="bg-secondary-bg p-2 rounded mt-1 text-xs font-mono whitespace-pre-wrap">${isCorrection ? `Reason: ${item.reason}` : (item.description || 'No description')}</pre>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        };

        const logHtml = logContent ? `<pre class="bg-secondary-bg p-3 rounded text-sm whitespace-pre-wrap font-mono text-text-secondary h-64 overflow-y-auto">${logContent}</pre>` : `<p class="text-sm text-text-secondary">Log not available.</p>`;

        return `
            <div class="glass-card p-6 mb-4">
                <h3 class="text-xl font-semibold text-accent-green mb-4">Result for ${result.model.name} on "${result.scenario.title}"</h3>
                
                <!-- Metrics -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div class="glass-card p-4 text-center">
                        <p class="text-sm text-text-secondary">Hallucinations Found</p>
                        <p class="text-2xl font-bold text-text-primary">${result.metrics.hallucinations_found}</p>
                    </div>
                    <div class="glass-card p-4 text-center">
                        <p class="text-sm text-text-secondary">Hallucinations Corrected</p>
                        <p class="text-2xl font-bold text-text-primary">${result.metrics.hallucinations_corrected}</p>
                    </div>
                    <div class="glass-card p-4 text-center">
                        <p class="text-sm text-text-secondary">Trust Score</p>
                        <p class="text-2xl font-bold text-text-primary">${result.metrics.trust_score.toFixed(2)}</p>
                    </div>
                </div>

                <!-- Two-column layout for details -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Left Column: Outputs -->
                    <div class="space-y-4">
                        <div>
                            <h4 class="font-semibold text-accent-green mb-2">Raw Model Output</h4>
                            <pre class="bg-secondary-bg p-3 rounded text-sm whitespace-pre-wrap text-text-secondary font-mono h-48 overflow-y-auto">${result.raw_model_output}</pre>
                        </div>
                        <div>
                            <h4 class="font-semibold text-accent-green mb-2">Advisor Corrected Output</h4>
                            <pre class="bg-green-900 bg-opacity-20 p-3 rounded text-sm whitespace-pre-wrap text-green-300 font-mono h-48 overflow-y-auto">${result.advisor_corrected_output}</pre>
                        </div>
                    </div>

                    <!-- Right Column: Reports -->
                    <div class="space-y-4">
                        ${formatReport('Detected Hallucinations', result.detailed_hallucination_report)}
                        ${formatReport('Applied Corrections', result.detailed_corrections_log, true)}
                    </div>
                </div>

                <!-- Full Log Section -->
                <div class="mt-6 full-log-container">
                    <h4 class="font-semibold text-accent-green mb-2">Full Evaluation Log</h4>
                    ${logHtml}
                </div>
            </div>
        `;
    }

    evaluationForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        evaluationSpinner.classList.remove('hidden');
        evaluationError.classList.add('hidden');
        startEvaluationBtn.disabled = true;
        progressBar.style.width = '0%';
        progressText.textContent = '';

        const selectedModelIds = getSelectedIds('model');
        const selectedScenarioIds = getSelectedIds('scenario');
        const totalRunsCount = selectedModelIds.length * selectedScenarioIds.length;
        let completedRunsCount = 0;

        // Update total runs display
        if (totalRuns) totalRuns.textContent = totalRunsCount;
        if (completedRuns) completedRuns.textContent = completedRunsCount;

        resultsContainer.innerHTML = '';
        let allResults = [];

        socket.on('evaluation_progress', (data) => {
            progressBar.style.width = `${data.progress}%`;
            progressText.textContent = data.status;

            if (data.result) {
                allResults.push(data.result);
                resultsContainer.innerHTML += renderEvaluationResult(data.result);
                completedRunsCount++;
                if (completedRuns) completedRuns.textContent = completedRunsCount;
            }
            if (data.error) {
                showError(data.error);
            }
        });

        socket.on('evaluation_complete', async (data) => {
            progressText.textContent = data.message;
            evaluationSpinner.classList.add('hidden');
            startEvaluationBtn.disabled = false;
            hideNewEvaluationModal();
            
            // Fetch full logs for all results now that the process is complete
            for (let i = 0; i < allResults.length; i++) {
                try {
                    const logContent = await api.getEvaluationLog(allResults[i].evaluation_log);
                    const resultElement = resultsContainer.children[i];
                    const logContainer = resultElement.querySelector('.full-log-container');
                    if (logContainer) {
                        logContainer.innerHTML = `
                            <h4 class="font-semibold text-accent-green mb-2">Full Evaluation Log</h4>
                            <pre class="bg-secondary-bg p-3 rounded text-sm whitespace-pre-wrap font-mono text-text-secondary h-64 overflow-y-auto">${logContent}</pre>
                        `;
                    }
                } catch (error) {
                    console.warn('Failed to load log for result', i, error);
                }
            }

            // Refresh evaluations data
            try {
                allEvaluations = await api.getEvaluations();
                applyFiltersAndSort();
            } catch (error) {
                console.error('Failed to refresh evaluations:', error);
            }

            // Clean up listeners
            socket.off('evaluation_progress');
            socket.off('evaluation_complete');
        });

        try {
            const response = await api.runEvaluation(selectedModelIds, selectedScenarioIds);
            if (response.error) {
                throw new Error(response.error);
            }
        } catch (err) {
            showError(`Failed to start evaluation: ${err.message}`);
            evaluationSpinner.classList.add('hidden');
            startEvaluationBtn.disabled = false;
            socket.off('evaluation_progress');
            socket.off('evaluation_complete');
        }
    });

    // Modal functions removed - now using full-page view

    function showNewEvaluationModal() {
        newEvaluationModal.classList.remove('hidden');
        newEvaluationModal.classList.add('flex');
    }

    function hideNewEvaluationModal() {
        newEvaluationModal.classList.add('hidden');
        newEvaluationModal.classList.remove('flex');
    }

    function exportToCSV() {
        if (filteredEvaluations.length === 0) {
            alert('No evaluations to export');
            return;
        }

        const headers = ['Model', 'Scenario', 'Trust Score (%)', 'Issues Found', 'Issues Fixed', 'Timestamp'];
        const csvContent = [
            headers.join(','),
            ...filteredEvaluations.map(e => [
                `"${e.model.name}"`,
                `"${e.scenario.title}"`,
                (e.metrics.trust_score * 100).toFixed(1),
                e.metrics.hallucinations_found || 0,
                e.metrics.hallucinations_corrected || 0,
                `"${new Date(e.timestamp).toLocaleString()}"`
            ].join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `evaluations_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    async function refreshEvaluations() {
        try {
            showLoadingState('evaluations');
            allEvaluations = await api.getEvaluations();
            applyFiltersAndSort();
            hideLoadingState('evaluations');
        } catch (error) {
            hideLoadingState('evaluations');
            showError('Failed to refresh evaluations: ' + error.message);
        }
    }

    // View details click handler removed - now using direct links to detail pages

    // Filter and sort event handlers
    if (filterInput) {
        filterInput.addEventListener('input', (e) => {
            currentFilter = e.target.value;
            applyFiltersAndSort();
        });
    }

    if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            currentSort = e.target.value;
            applyFiltersAndSort();
        });
    }

    // Export and refresh handlers
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', exportToCSV);
    }

    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshEvaluations);
    }

    // Retry evaluation handler
    if (retryBtn) {
        retryBtn.addEventListener('click', () => {
            hideError();
            evaluationForm.dispatchEvent(new Event('submit'));
        });
    }

    if (openEvaluationModalBtn) {
        openEvaluationModalBtn.addEventListener('click', showNewEvaluationModal);
    } else {
        console.error('open-evaluation-modal-btn element not found!');
    }
    
    if (newEvaluationModalCloseBtn) {
        newEvaluationModalCloseBtn.addEventListener('click', hideNewEvaluationModal);
    }
    
    // Modal close handler removed - now using full-page view

    selectAllModelsBtn.addEventListener('click', () => {
        modelSelector.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.checked = true;
            cb.closest('.model-card')?.classList.add('selected');
        });
        updateButtonState();
    });
    
    deselectAllModelsBtn.addEventListener('click', () => {
        modelSelector.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.checked = false;
            cb.closest('.model-card')?.classList.remove('selected');
        });
        updateButtonState();
    });
    
    selectAllScenariosBtn.addEventListener('click', () => {
        scenarioSelector.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.checked = true;
            cb.closest('.scenario-card')?.classList.add('selected');
        });
        updateButtonState();
    });
    
    deselectAllScenariosBtn.addEventListener('click', () => {
        scenarioSelector.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.checked = false;
            cb.closest('.scenario-card')?.classList.remove('selected');
        });
        updateButtonState();
    });
    
    newEvaluationModal.addEventListener('click', (event) => {
        if (event.target === newEvaluationModal) {
            hideNewEvaluationModal();
        }
    });
    // Modal click handler removed - now using full-page view

    loadInitialData();
});
