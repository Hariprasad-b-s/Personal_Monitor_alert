# Daily Activity Tracker 🎯

A beautiful, modern web application for tracking daily activities with timers, progress visualization, and SQLite database storage.

## Features ✨

- **Interactive Checklist**: Track your daily tasks with a beautiful, hierarchical checklist
- **Smart Timers**: Built-in timers for each task with start/stop/reset functionality
- **Customizable Time Allocations**: Edit time allocations for each task via dropdown
- **Progress Visualization**: Beautiful charts showing your 30-day progress
- **Daily Statistics**: View completed tasks, time spent, and streaks
- **Data Persistence**: All data stored in lightweight SQLite database
- **Modern UI**: Premium dark theme with gradients, animations, and glassmorphism

## Tech Stack 🛠️

- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Charts**: Chart.js
- **Fonts**: Google Fonts (Inter)

## Installation 📦

1. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run the application**:
```bash
python app.py
```

3. **Open your browser**:
Navigate to `http://localhost:5001`

**Or use the quick start script**:
```bash
./start.sh
```

## Usage 📖

### Checklist
- Click the checkbox to mark tasks as complete
- Completed tasks are tracked per day
- Parent tasks and sub-tasks are organized hierarchically

### Timers
1. Click the "Timer" button next to any task
2. Use Start/Stop/Reset controls
3. Timer sessions are automatically saved to the database
4. Time spent is tracked and displayed in statistics

### Edit Time Allocations
1. Click the "Edit" button next to any task
2. Set hours and minutes
3. Click "Save" to update

### Progress Chart
- View your 30-day progress
- Dual-axis chart shows tasks completed and hours spent
- Automatically updates as you complete tasks

## Default Tasks 📋

1. **25 Apps (2.5 hrs)**
   - 15 with Claude and LinkedIn (1.5 hrs)
   - 10 generics (1 hr)
2. **Leetcode (1.5-2 hrs)**
3. **Projects - Data Engineer, AI, ML (2 hrs)**
4. **Learn AI - Andrew NG (30 mins)**
5. **Learn Data Engineering (1 hr)**
6. **Learn ML (1 hr)**
7. **Learn MLOps (30 mins)**

## Database Schema 💾

### Tables
- **tasks**: Stores task information (name, time allocation, hierarchy)
- **daily_progress**: Tracks daily completion status and time spent
- **timer_sessions**: Records all timer sessions

## API Endpoints 🔌

- `GET /api/tasks` - Get all tasks
- `PUT /api/tasks/<id>` - Update task time
- `GET /api/progress/today` - Get today's progress
- `POST /api/progress/toggle` - Toggle task completion
- `POST /api/timer/session` - Save timer session
- `GET /api/stats/weekly` - Get weekly statistics
- `GET /api/stats/daily` - Get 30-day statistics

## Customization 🎨

### Adding New Tasks
Edit the `default_tasks` list in `app.py` or add tasks directly to the database.

### Styling
Modify `static/css/style.css` to customize colors, fonts, and animations.

### Time Allocations
Use the "Edit" button in the UI or update the database directly.

## Browser Support 🌐

- Chrome (recommended)
- Firefox
- Safari
- Edge

## License 📄

MIT License - feel free to use and modify!

## Author 👨‍💻

Built with ❤️ for productivity enthusiasts
