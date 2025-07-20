document.addEventListener('DOMContentLoaded', function() {
    let socket = null;
    let evaluationResults = [];
    let filteredResults = [];
    let selectedModels = new Set();
    let selectedScenarios = new Set();

    // Initialize Socket.IO if available
    if (typeof io !== 'undefined') {
        socket = io();
        setupSocketListeners();
    }

    // Initialize the page
    loadPastEvaluations();
    setupEventListeners();
    setupModalFunctionality();

    function setupEventListeners() {
        // Filter and sort controls
        document.getElementById('filter-input').addEventListener('input', filterResults);
        document.getElementById('sort-select').addEventListener('change', sortResults);
        document.getElementById('refresh-evaluations-btn').addEventListener('click', loadPastEvaluations);
        document.getElementById('export-csv-btn').addEventListener('click', exportToCSV);
    }

    function setupModalFunctionality() {
        const modal = document.getElementById('new-evaluation-modal');
        const openBtn = document.getElementById('open-evaluation-modal-btn');
        const closeBtn = document.getElementById('new-evaluation-modal-close-btn');
        const evaluationForm = document.getElementById('evaluation-form');

        // Open modal
        if (openBtn) {
            openBtn.addEventListener('click', function(e) {
                e.preventDefault();
                openModal();
            });
        }

        // Close modal
        if (closeBtn) {
            closeBtn.addEventListener('click', function(e) {
                e.preventDefault();
                closeModal();
            });
        }

        // Close modal when clicking outside
        if (modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    closeModal();
                }
            });
        }

        // Handle escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modal && !modal.classList.contains('hidden')) {
                closeModal();
            }
        });

        // Handle form submission
        if (evaluationForm) {
            evaluationForm.addEventListener('submit', handleEvaluationSubmit);
        }

        // Setup select all/deselect all buttons
        document.getElementById('select-all-models').addEventListener('click', selectAllModels);
        document.getElementById('deselect-all-models').addEventListener('click', deselectAllModels);
        document.getElementById('select-all-scenarios').addEventListener('click', selectAllScenarios);
        document.getElementById('deselect-all-scenarios').addEventListener('click', deselectAllScenarios);
    }

    function openModal() {
        const modal = document.getElementById('new-evaluation-modal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            document.body.style.overflow = 'hidden';
            // Load models and scenarios when modal opens
            loadModelsAndScenarios();
        }
    }

    function closeModal() {
        const modal = document.getElementById('new-evaluation-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            document.body.style.overflow = 'auto';
        }
        // Reset form state
        resetModalState();
    }

    function resetModalState() {
        // Hide loading states
        document.getElementById('models-loading').classList.add('hidden');
        document.getElementById('scenarios-loading').classList.add('hidden');
        document.getElementById('evaluation-spinner').classList.add('hidden');
        document.getElementById('evaluation-error').classList.add('hidden');

        // Reset selections
        selectedModels.clear();
        selectedScenarios.clear();

        // Clear visual selections
        document.querySelectorAll('.model-card.selected').forEach(card => {
            card.classList.remove('selected');
        });
        document.querySelectorAll('.scenario-card.selected').forEach(card => {
            card.classList.remove('selected');
        });

        // Reset checkboxes
        document.querySelectorAll('.model-card .card-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        document.querySelectorAll('.scenario-card .card-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });

        // Reset button state
        const startBtn = document.getElementById('start-evaluation-btn');
        if (startBtn) {
            startBtn.disabled = true;
        }
    }

    async function loadModelsAndScenarios() {
        await Promise.all([
            loadModels(),
            loadScenarios()
        ]);
    }

    async function loadModels() {
        const container = document.getElementById('model-selector');
        const loadingDiv = document.getElementById('models-loading');

        if (!container || !loadingDiv) return;

        loadingDiv.classList.remove('hidden');
        container.innerHTML = '';

        try {
            const response = await fetch('/api/evaluations/models');
            if (!response.ok) throw new Error('Failed to load models');

            const models = await response.json();
            loadingDiv.classList.add('hidden');

            models.forEach(model => {
                const modelCard = createModelCard(model);
                container.appendChild(modelCard);
            });
        } catch (error) {
            console.error('Error loading models:', error);
            loadingDiv.classList.add('hidden');
            showError('Failed to load models: ' + error.message);
        }
    }

    async function loadScenarios() {
        const container = document.getElementById('scenario-selector');
        const loadingDiv = document.getElementById('scenarios-loading');

        if (!container || !loadingDiv) return;

        loadingDiv.classList.remove('hidden');
        container.innerHTML = '';

        try {
            const response = await fetch('/api/evaluations/scenarios');
            if (!response.ok) throw new Error('Failed to load scenarios');

            const scenarios = await response.json();
            loadingDiv.classList.add('hidden');

            scenarios.forEach(scenario => {
                const scenarioCard = createScenarioCard(scenario);
                container.appendChild(scenarioCard);
            });
        } catch (error) {
            console.error('Error loading scenarios:', error);
            loadingDiv.classList.add('hidden');
            showError('Failed to load scenarios: ' + error.message);
        }
    }

    function createModelCard(model) {
        const card = document.createElement('div');
        card.className = 'model-card';
        card.dataset.modelId = model.id;

        card.innerHTML = `
            <input type="checkbox" class="card-checkbox" value="${model.id}">
            <div class="card-category">AI Model</div>
            <div class="card-title">${model.name}</div>
            <div class="card-description">${model.description || 'Advanced AI model for comprehensive evaluation tasks.'}</div>
        `;

        const checkbox = card.querySelector('.card-checkbox');
        checkbox.addEventListener('change', () => toggleModelSelection(model.id, card, checkbox.checked));

        card.addEventListener('click', (e) => {
            if (e.target !== checkbox) {
                checkbox.checked = !checkbox.checked;
                toggleModelSelection(model.id, card, checkbox.checked);
            }
        });

        return card;
    }

    function createScenarioCard(scenario) {
        const card = document.createElement('div');
        card.className = 'scenario-card';
        card.dataset.scenarioId = scenario.id;

        card.innerHTML = `
            <input type="checkbox" class="card-checkbox" value="${scenario.id}">
            <div class="card-category">Test Scenario</div>
            <div class="card-title">${scenario.title}</div>
            <div class="card-description">${scenario.description || scenario.category || 'Comprehensive evaluation scenario.'}</div>
        `;

        const checkbox = card.querySelector('.card-checkbox');
        checkbox.addEventListener('change', () => toggleScenarioSelection(scenario.id, card, checkbox.checked));

        card.addEventListener('click', (e) => {
            if (e.target !== checkbox) {
                checkbox.checked = !checkbox.checked;
                toggleScenarioSelection(scenario.id, card, checkbox.checked);
            }
        });

        return card;
    }

    function toggleModelSelection(modelId, cardElement, isSelected) {
        if (isSelected) {
            selectedModels.add(modelId);
            cardElement.classList.add('selected');
        } else {
            selectedModels.delete(modelId);
            cardElement.classList.remove('selected');
        }
        updateStartButton();
    }

    function toggleScenarioSelection(scenarioId, cardElement, isSelected) {
        if (isSelected) {
            selectedScenarios.add(scenarioId);
            cardElement.classList.add('selected');
        } else {
            selectedScenarios.delete(scenarioId);
            cardElement.classList.remove('selected');
        }
        updateStartButton();
    }

    function updateStartButton() {
        const startBtn = document.getElementById('start-evaluation-btn');
        if (startBtn) {
            startBtn.disabled = selectedModels.size === 0 || selectedScenarios.size === 0;
        }
    }

    function selectAllModels() {
        document.querySelectorAll('.model-card').forEach(card => {
            const checkbox = card.querySelector('.card-checkbox');
            if (!checkbox.checked) {
                checkbox.checked = true;
                toggleModelSelection(card.dataset.modelId, card, true);
            }
        });
    }

    function deselectAllModels() {
        document.querySelectorAll('.model-card').forEach(card => {
            const checkbox = card.querySelector('.card-checkbox');
            if (checkbox.checked) {
                checkbox.checked = false;
                toggleModelSelection(card.dataset.modelId, card, false);
            }
        });
    }

    function selectAllScenarios() {
        document.querySelectorAll('.scenario-card').forEach(card => {
            const checkbox = card.querySelector('.card-checkbox');
            if (!checkbox.checked) {
                checkbox.checked = true;
                toggleScenarioSelection(card.dataset.scenarioId, card, true);
            }
        });
    }

    function deselectAllScenarios() {
        document.querySelectorAll('.scenario-card').forEach(card => {
            const checkbox = card.querySelector('.card-checkbox');
            if (checkbox.checked) {
                checkbox.checked = false;
                toggleScenarioSelection(card.dataset.scenarioId, card, false);
            }
        });
    }

    async function handleEvaluationSubmit(event) {
        event.preventDefault();

        if (selectedModels.size === 0 || selectedScenarios.size === 0) {
            showError('Please select at least one model and one scenario.');
            return;
        }

        // Show progress
        document.getElementById('evaluation-spinner').classList.remove('hidden');
        document.getElementById('evaluation-error').classList.add('hidden');
        document.getElementById('start-evaluation-btn').disabled = true;

        try {
            const response = await fetch('/api/evaluations/run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model_ids: Array.from(selectedModels),
                    scenario_ids: Array.from(selectedScenarios)
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to start evaluation');
            }

            const result = await response.json();
            document.getElementById('progress-text').textContent = result.message;

        } catch (error) {
            console.error('Failed to start evaluation:', error);
            showError('Failed to start evaluation: ' + error.message);
            document.getElementById('start-evaluation-btn').disabled = false;
            document.getElementById('evaluation-spinner').classList.add('hidden');
        }
    }

    function setupSocketListeners() {
        if (!socket) return;

        socket.on('evaluation_progress', function(data) {
            updateProgress(data);
        });

        socket.on('evaluation_complete', function(data) {
            completeEvaluation(data);
        });
    }

    function updateProgress(data) {
        if (data.progress !== undefined) {
            document.getElementById('progress-bar').style.width = data.progress + '%';
        }

        if (data.status) {
            document.getElementById('progress-text').textContent = data.status;
        }

        // Update completed count
        const completedMatch = data.status?.match(/(\d+)\/(\d+)/);
        if (completedMatch) {
            document.getElementById('completed-runs').textContent = completedMatch[1];
            document.getElementById('total-runs').textContent = completedMatch[2];
        }

        if (data.error) {
            showError(data.error);
        }
    }

    function completeEvaluation(data) {
        document.getElementById('evaluation-spinner').classList.add('hidden');
        document.getElementById('start-evaluation-btn').disabled = false;

        // Refresh the evaluations list
        loadPastEvaluations();

        // Close modal after completion
        setTimeout(() => {
            closeModal();
        }, 1000);
    }

    function showError(message) {
        document.getElementById('error-message').textContent = message;
        document.getElementById('evaluation-error').classList.remove('hidden');
        document.getElementById('evaluation-spinner').classList.add('hidden');
    }

    async function loadPastEvaluations() {
        const tableBody = document.getElementById('past-evaluations-table');
        const loading = document.getElementById('evaluations-loading');
        const empty = document.getElementById('evaluations-empty');

        if (!tableBody) return;

        loading.classList.remove('hidden');
        empty.classList.add('hidden');
        tableBody.innerHTML = '';

        try {
            const response = await fetch('/api/evaluations');
            if (!response.ok) throw new Error('Failed to load evaluations');

            evaluationResults = await response.json();
            filteredResults = [...evaluationResults];

            loading.classList.add('hidden');

            if (evaluationResults.length === 0) {
                empty.classList.remove('hidden');
                return;
            }

            renderEvaluations();
        } catch (error) {
            console.error('Error loading evaluations:', error);
            loading.classList.add('hidden');
            empty.classList.remove('hidden');
        }
    }

    function renderEvaluations() {
        const tableBody = document.getElementById('past-evaluations-table');
        const resultsCount = document.getElementById('results-count');

        if (!tableBody) return;

        tableBody.innerHTML = '';
        resultsCount.textContent = filteredResults.length;

        filteredResults.forEach(evaluation => {
            const row = document.createElement('tr');
            row.className = 'border-b border-border-color hover:bg-secondary-bg';

            const trustScore = evaluation.metrics?.trust_score || 0;
            const trustScoreClass = trustScore >= 0.8 ? 'trust-score-excellent' :
                                   trustScore >= 0.6 ? 'trust-score-good' : 'trust-score-poor';

            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm text-text-primary">${evaluation.model?.name || 'Unknown'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-text-primary">${evaluation.scenario?.title || 'Unknown'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm ${trustScoreClass}">${(trustScore * 100).toFixed(1)}%</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-text-primary">${evaluation.metrics?.hallucinations_found || 0}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-text-primary">${evaluation.metrics?.hallucinations_corrected || 0}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-text-secondary">${formatDate(evaluation.timestamp)}</td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <a href="/evaluations/${evaluation.id}" class="text-accent-blue hover:text-accent-blue-light">View</a>
                </td>
            `;

            tableBody.appendChild(row);
        });
    }

    function filterResults() {
        const filterValue = document.getElementById('filter-input').value.toLowerCase();

        if (!filterValue) {
            filteredResults = [...evaluationResults];
        } else {
            filteredResults = evaluationResults.filter(evaluation => {
                const modelName = evaluation.model?.name?.toLowerCase() || '';
                const scenarioTitle = evaluation.scenario?.title?.toLowerCase() || '';
                return modelName.includes(filterValue) || scenarioTitle.includes(filterValue);
            });
        }

        renderEvaluations();
    }

    function sortResults() {
        const sortValue = document.getElementById('sort-select').value;

        filteredResults.sort((a, b) => {
            switch (sortValue) {
                case 'timestamp-desc':
                    return new Date(b.timestamp) - new Date(a.timestamp);
                case 'timestamp-asc':
                    return new Date(a.timestamp) - new Date(b.timestamp);
                case 'trust-score-desc':
                    return (b.metrics?.trust_score || 0) - (a.metrics?.trust_score || 0);
                case 'trust-score-asc':
                    return (a.metrics?.trust_score || 0) - (b.metrics?.trust_score || 0);
                case 'model-asc':
                    return (a.model?.name || '').localeCompare(b.model?.name || '');
                case 'scenario-asc':
                    return (a.scenario?.title || '').localeCompare(b.scenario?.title || '');
                default:
                    return 0;
            }
        });

        renderEvaluations();
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }

    function exportToCSV() {
        if (filteredResults.length === 0) {
            showError('No evaluations to export');
            return;
        }

        const csvContent = [
            ['Model', 'Scenario', 'Trust Score', 'Issues Found', 'Issues Fixed', 'Timestamp'],
            ...filteredResults.map(evaluation => [
                evaluation.model?.name || 'Unknown',
                evaluation.scenario?.title || 'Unknown',
                ((evaluation.metrics?.trust_score || 0) * 100).toFixed(1) + '%',
                evaluation.metrics?.hallucinations_found || 0,
                evaluation.metrics?.hallucinations_corrected || 0,
                formatDate(evaluation.timestamp)
            ])
        ].map(row => row.join(',')).join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `evaluations_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    }
});
