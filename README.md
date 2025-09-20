# CivicSightAI - Mumbai Pothole Detection & Reporting System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](CONTRIBUTING.md)

A comprehensive civic tech platform for reporting and visualizing pothole complaints in Mumbai. Features an interactive heatmap, real-time complaint tracking, and notification system.

## 🛠️ Technology StackicSightAI - Mumbai Pothole Detection & Reporting System

A comprehensive civic tech platform for reporting and visualizing pothole complaints in Mumbai. Features an interactive heatmap, real-time complaint tracking, and notification system.

## �️ Technology Stack

### Backend
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)

### Frontend
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

### AI/ML
![YOLOv11](https://img.shields.io/badge/YOLOv11-00FFFF?style=for-the-badge&logo=yolo&logoColor=black)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)

### DevOps & Tools
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)


## �🚀 Features

### 🗺️ Interactive Heatmap
- **Mumbai-focused visualization** with real complaint data
- **Multiple view modes**: Heatmap density, individual markers, or both
- **Advanced filtering** by category, status, time period, and road type
- **Real-time updates** with live complaint data

### 📱 Complaint Reporting
- **Image-based detection** using YOLOv11 AI model
- **GPS location capture** for accurate mapping
- **Category classification** (pothole, drainage, streetlight, etc.)
- **Status tracking** (pending, in-progress, resolved)

### 🔔 Notification System
- **WhatsApp integration** for instant updates
- **Email notifications** for complaint status changes
- **Administrative dashboard** for complaint management

## 📁 Project Structure

```
CivicSightAI/
├── 📄 app.py                 # Main Flask application
├── ⚙️ config.py              # Configuration settings
├── 🗄️ init_database.py       # Database initialization
├── 📋 requirements.txt       # Python dependencies
├── 
├── 📁 src/                   # Core application modules
│   ├── 🗄️ database.py        # Database operations
│   ├── 🤖 pothole_detector.py # AI model integration
│   ├── 🔔 notification_service.py # Notification handling
│   ├── 📍 notification_routes.py # Notification endpoints
│   └── 🏢 ward_office_parser.py # Ward office utilities
├── 
├── 📁 templates/             # HTML templates
│   ├── 🏠 base.html          # Base template
│   ├── 🏛️ index.html         # Homepage
│   ├── 📊 dashboard.html     # Admin dashboard
│   ├── 🗺️ heatmap.html       # Interactive map
│   └── 🔔 notifications.html # Notifications page
├── 
├── 📁 static/               # Static assets
│   ├── 🎨 css/              # Stylesheets
│   ├── ⚡ js/               # JavaScript files
│   └── 📤 uploads/          # User uploaded files
├── 
├── 📁 setup/                # Database setup scripts
├── 📁 tests/                # Unit tests
├── 📁 data/                 # Application data
└── 🤖 yolov11_best.pt      # AI model weights
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL with PostGIS extension
- Node.js (for frontend dependencies)

### 1. Clone Repository
```bash
git clone https://github.com/PrachitiSParulekar/Pothole-detection.git
cd Pothole-detection
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your database and API credentials
```

### 5. Database Setup
```bash
python init_database.py
```

### 6. Run Application
```bash
python app.py
```

Visit `http://localhost:5000` to access the application.

## 🗺️ Mumbai Heatmap Features

### Interactive Visualization
- **Heat density mapping** showing complaint concentration areas
- **Location pin markers** with detailed complaint information
- **Dynamic filtering** for targeted analysis
- **Real-time data loading** from PostgreSQL with PostGIS

### View Toggle Controls
- 🔥 **Heatmap View**: Shows density and intensity of complaints
- 📍 **Markers View**: Individual location pins with details
- 📊 **Both Views**: Combined visualization for comprehensive analysis

### Mumbai Areas Covered
- Mumbai Central, Nariman Point, Churchgate
- Bandra West, Dadar, Andheri
- Colaba, Marine Drive, Gateway of India
- Borivali, Malad, Jogeshwari
- Chembur, Govandi, Powai

## 🔧 Technology Stack

### Backend
- **Flask** - Python web framework
- **PostgreSQL** - Database with PostGIS for geographic data
- **YOLOv11** - AI model for pothole detection
- **Psycopg2** - PostgreSQL adapter

### Frontend
- **HTML5/CSS3** - Modern responsive design
- **Leaflet.js** - Interactive mapping
- **Bootstrap** - UI components
- **JavaScript** - Dynamic interactions

### Integrations
- **WhatsApp API** - GreenAPI for messaging
- **Email SMTP** - Notification delivery
- **GPS/Geolocation** - Precise location capture


## 📈 Database Schema

### Complaints Table
- `id` - UUID primary key
- `category` - Complaint type
- `description` - Issue details
- `location` - PostGIS geography point
- `status` - Current state
- `severity` - Impact level (1-5)
- `created_at` - Timestamp
- `image_path` - Photo reference

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## Contributing

Please read `CONTRIBUTING.md` for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.