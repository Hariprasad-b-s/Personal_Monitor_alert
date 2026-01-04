// Global State
let tasks = [];
let todayProgress = {};
let currentTimer = {
    taskId: null,
    taskName: null,
    seconds: 0,
    interval: null,
    isRunning: false
};
let chart = null;

// API Base URL
const API_BASE = '';

// Initialize App
document.addEventListener('DOMContentLoaded', async () => {
    await loadTasks();
    await loadTodayProgress();
    await loadStats();
    await initChart();
    setupEventListeners();
});

// Load Tasks from API
async function loadTasks() {
    try {
        const response = await fetch(`${API_BASE}/api/tasks`);
        tasks = await response.json();
        renderChecklist();
    } catch (error) {
        console.error('Error loading tasks:', error);
    }
}

// Load Today's Progress
async function loadTodayProgress() {
    try {
        const response = await fetch(`${API_BASE}/api/progress/today`);
        todayProgress = await response.json();
        renderChecklist();
    } catch (error) {
        console.error('Error loading progress:', error);
    }
}

// Render Checklist
function renderChecklist() {
    const checklist = document.getElementById('checklist');
    checklist.innerHTML = '';

    // Separate parent and child tasks
    const parentTasks = tasks.filter(t => !t.parent_id);
    const childTasks = tasks.filter(t => t.parent_id);

    parentTasks.forEach(task => {
        const li = createChecklistItem(task, true);
        checklist.appendChild(li);

        // Add child tasks
        const children = childTasks.filter(c => c.parent_id === task.id);
        children.forEach(child => {
            const childLi = createChecklistItem(child, false);
            checklist.appendChild(childLi);
        });
    });
}

// Create Checklist Item
function createChecklistItem(task, isParent) {
    const li = document.createElement('li');
    li.className = `checklist-item ${isParent ? 'parent' : 'child'}`;
    li.dataset.taskId = task.id;

    const progressInfo = todayProgress[task.id] || {};
    const isCompleted = progressInfo.completed || false;
    const currentCount = progressInfo.current_count || 0;

    if (isCompleted) {
        li.classList.add('completed');
    }

    const hours = Math.floor(task.time_minutes / 60);
    const minutes = task.time_minutes % 60;
    const timeText = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;

    let counterHtml = '';
    if (task.target_count > 0) {
        counterHtml = `
            <div class="counter-container">
                <span class="counter-label">${currentCount} / ${task.target_count}</span>
                <button class="increment-btn" onclick="incrementTask(${task.id}); event.stopPropagation();">+</button>
            </div>
        `;
    }

    li.innerHTML = `
        <div class="item-content">
            <div class="checkbox ${isCompleted ? 'checked' : ''}" onclick="toggleTask(${task.id})"></div>
            <span class="item-text ${isCompleted ? 'completed' : ''}">${task.name}</span>
            ${counterHtml}
        </div>
        <div class="item-controls">
            <span class="time-badge">${timeText}</span>
            <button class="timer-btn" onclick="selectTaskForTimer(${task.id}, '${task.name.replace(/'/g, "\\'")}', ${task.time_minutes})">
                Timer
            </button>
            <button class="edit-time-btn" onclick="openEditTimeModal(${task.id}, '${task.name.replace(/'/g, "\\'")}', ${task.time_minutes})">
                Edit
            </button>
        </div>
    `;

    return li;
}

// Toggle Task Completion
async function toggleTask(taskId) {
    try {
        const response = await fetch(`${API_BASE}/api/progress/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ task_id: taskId })
        });

        if (response.ok) {
            await loadTodayProgress();
            await loadStats();
        }
    } catch (error) {
        console.error('Error toggling task:', error);
    }
}

// Increment Task Count
async function incrementTask(taskId) {
    try {
        const response = await fetch(`${API_BASE}/api/progress/increment`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ task_id: taskId })
        });

        if (response.ok) {
            await loadTodayProgress();
            await loadStats();
        }
    } catch (error) {
        console.error('Error incrementing task:', error);
    }
}

// Select Task for Timer
function selectTaskForTimer(taskId, taskName, timeMinutes) {
    // Stop current timer if running
    if (currentTimer.isRunning) {
        stopTimer();
    }

    // Set new task
    currentTimer.taskId = taskId;
    currentTimer.taskName = taskName;
    currentTimer.seconds = 0;

    // Update UI
    document.getElementById('timerTaskName').textContent = taskName;
    document.getElementById('timerDisplay').textContent = '00:00:00';
    document.getElementById('startBtn').disabled = false;
    document.getElementById('resetBtn').disabled = false;

    // Highlight selected task
    document.querySelectorAll('.timer-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
}

// Start Timer
function startTimer() {
    if (!currentTimer.taskId || currentTimer.isRunning) return;

    currentTimer.isRunning = true;
    document.getElementById('startBtn').disabled = true;
    document.getElementById('stopBtn').disabled = false;

    currentTimer.interval = setInterval(() => {
        currentTimer.seconds++;
        updateTimerDisplay();
    }, 1000);
}

// Stop Timer
async function stopTimer() {
    if (!currentTimer.isRunning) return;

    currentTimer.isRunning = false;
    clearInterval(currentTimer.interval);

    document.getElementById('startBtn').disabled = false;
    document.getElementById('stopBtn').disabled = true;

    // Save timer session
    if (currentTimer.seconds > 0) {
        await saveTimerSession();
    }
}

// Reset Timer
function resetTimer() {
    if (currentTimer.isRunning) {
        stopTimer();
    }

    currentTimer.seconds = 0;
    updateTimerDisplay();
}

// Update Timer Display
function updateTimerDisplay() {
    const hours = Math.floor(currentTimer.seconds / 3600);
    const minutes = Math.floor((currentTimer.seconds % 3600) / 60);
    const seconds = currentTimer.seconds % 60;

    const display = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    document.getElementById('timerDisplay').textContent = display;
}

// Save Timer Session
async function saveTimerSession() {
    try {
        const response = await fetch(`${API_BASE}/api/timer/session`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                task_id: currentTimer.taskId,
                duration: currentTimer.seconds
            })
        });

        if (response.ok) {
            await loadStats();
            await updateChart();
        }
    } catch (error) {
        console.error('Error saving timer session:', error);
    }
}

// Open Edit Time Modal
function openEditTimeModal(taskId, taskName, timeMinutes) {
    const modal = document.getElementById('editTimeModal');
    const hours = Math.floor(timeMinutes / 60);
    const minutes = timeMinutes % 60;

    document.getElementById('taskNameDisplay').value = taskName;
    document.getElementById('hoursInput').value = hours;
    document.getElementById('minutesInput').value = minutes;

    modal.classList.add('active');

    // Store task ID for saving
    modal.dataset.taskId = taskId;
}

// Close Edit Time Modal
function closeEditTimeModal() {
    const modal = document.getElementById('editTimeModal');
    modal.classList.remove('active');
}

// Save Time Changes
async function saveTimeChanges() {
    const modal = document.getElementById('editTimeModal');
    const taskId = parseInt(modal.dataset.taskId);
    const hours = parseInt(document.getElementById('hoursInput').value) || 0;
    const minutes = parseInt(document.getElementById('minutesInput').value) || 0;
    const totalMinutes = (hours * 60) + minutes;

    try {
        const response = await fetch(`${API_BASE}/api/tasks/${taskId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                time_minutes: totalMinutes
            })
        });

        if (response.ok) {
            await loadTasks();
            closeEditTimeModal();
        }
    } catch (error) {
        console.error('Error updating task time:', error);
    }
}

// Load Stats
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/api/progress/today`);
        const progress = await response.json();

        // Calculate completed tasks
        const completedCount = Object.values(progress).filter(p => p.completed).length;
        document.getElementById('todayCompleted').textContent = completedCount;

        // Calculate total time spent
        const totalSeconds = Object.values(progress).reduce((sum, p) => sum + (p.time_spent || 0), 0);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        document.getElementById('todayTime').textContent = `${hours}h ${minutes}m`;

        // Calculate streak (simplified - just count days with completed tasks)
        const weekResponse = await fetch(`${API_BASE}/api/stats/weekly`);
        const weekStats = await weekResponse.json();
        document.getElementById('weekStreak').textContent = weekStats.length;

    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Initialize Chart
async function initChart() {
    const ctx = document.getElementById('progressChart').getContext('2d');

    try {
        const response = await fetch(`${API_BASE}/api/stats/daily`);
        const stats = await response.json();

        // Prepare data for last 30 days
        const labels = stats.map(s => {
            const date = new Date(s.date);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });

        const completedData = stats.map(s => s.completed_tasks || 0);
        const timeData = stats.map(s => Math.round((s.total_time_seconds || 0) / 3600 * 10) / 10); // Convert to hours

        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Tasks Completed',
                        data: completedData,
                        borderColor: 'rgba(67, 233, 123, 1)',
                        backgroundColor: 'rgba(67, 233, 123, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Hours Spent',
                        data: timeData,
                        borderColor: 'rgba(102, 126, 234, 1)',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#e4e4e7',
                            font: {
                                size: 12,
                                family: 'Inter'
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(26, 26, 46, 0.9)',
                        titleColor: '#e4e4e7',
                        bodyColor: '#a1a1aa',
                        borderColor: 'rgba(102, 126, 234, 0.2)',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(102, 126, 234, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#a1a1aa',
                            font: {
                                size: 10
                            },
                            maxRotation: 45,
                            minRotation: 45
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: {
                            color: 'rgba(102, 126, 234, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#a1a1aa',
                            font: {
                                size: 10
                            }
                        },
                        title: {
                            display: true,
                            text: 'Tasks',
                            color: '#a1a1aa'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false,
                            drawBorder: false
                        },
                        ticks: {
                            color: '#a1a1aa',
                            font: {
                                size: 10
                            }
                        },
                        title: {
                            display: true,
                            text: 'Hours',
                            color: '#a1a1aa'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error initializing chart:', error);
    }
}

// Update Chart
async function updateChart() {
    if (!chart) return;

    try {
        const response = await fetch(`${API_BASE}/api/stats/daily`);
        const stats = await response.json();

        const labels = stats.map(s => {
            const date = new Date(s.date);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });

        const completedData = stats.map(s => s.completed_tasks || 0);
        const timeData = stats.map(s => Math.round((s.total_time_seconds || 0) / 3600 * 10) / 10);

        chart.data.labels = labels;
        chart.data.datasets[0].data = completedData;
        chart.data.datasets[1].data = timeData;
        chart.update();
    } catch (error) {
        console.error('Error updating chart:', error);
    }
}

// Setup Event Listeners
function setupEventListeners() {
    // Timer controls
    document.getElementById('startBtn').addEventListener('click', startTimer);
    document.getElementById('stopBtn').addEventListener('click', stopTimer);
    document.getElementById('resetBtn').addEventListener('click', resetTimer);

    // Modal controls
    document.getElementById('saveTimeBtn').addEventListener('click', saveTimeChanges);
    document.getElementById('cancelTimeBtn').addEventListener('click', closeEditTimeModal);

    // Close modal on background click
    document.getElementById('editTimeModal').addEventListener('click', (e) => {
        if (e.target.id === 'editTimeModal') {
            closeEditTimeModal();
        }
    });
}

// Refresh data periodically
setInterval(async () => {
    if (!currentTimer.isRunning) {
        await loadTodayProgress();
        await loadStats();
    }
}, 60000); // Every minute
