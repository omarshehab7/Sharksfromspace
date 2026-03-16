# 🦈 Sharks From Space

> Predicting shark activity hotspots using satellite ocean data from NASA.

A cross-platform mobile application that makes ocean science accessible to everyone. By combining satellite-derived sea surface temperature, chlorophyll concentrations, and bathymetry data with machine learning, **Sharks From Space** identifies areas where shark activity is most likely — helping beachgoers stay informed and curious about the ocean.

---

## 🏗️ Architecture

```
Sharksfromspace/
├── mobile_app/       # React Native / Expo mobile client
├── backend/          # FastAPI + PostgreSQL/PostGIS backend
├── data_pipeline/    # Ruflo-orchestrated data processing pipeline
└── docs/             # Project documentation
```

| Layer | Technology |
|---|---|
| **Mobile App** | React Native, Expo, Mapbox GL, TanStack Query, NativeWind |
| **Backend API** | Python, FastAPI, SQLAlchemy, PostGIS |
| **Data Pipeline** | xarray, netCDF4, NumPy, Pandas, GeoPandas, Rasterio |
| **Orchestration** | Ruflo |
| **Infrastructure** | Docker, PostgreSQL + PostGIS, Redis |

---

## 🚀 Quick Start

### Prerequisites

- [Node.js](https://nodejs.org/) 18+
- [Python](https://python.org/) 3.11+
- [Docker](https://docker.com/) & Docker Compose
- [Expo CLI](https://docs.expo.dev/get-started/installation/)
- A [NASA Earthdata](https://urs.earthdata.nasa.gov/) account
- A [Mapbox](https://mapbox.com/) access token

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/Sharksfromspace.git
cd Sharksfromspace
cp .env.example .env
# Fill in your NASA Earthdata credentials and Mapbox token in .env
```

### 2. Start Infrastructure

```bash
docker-compose up -d postgres redis
```

### 3. Start the Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### 4. Start the Mobile App

```bash
cd mobile_app
npm install
npx expo start
```

### 5. Run Data Pipeline

```bash
cd data_pipeline
pip install -r requirements.txt
ruflo run
```

---

## 📚 Documentation

- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api_reference.md)
- [Data Dictionary](docs/data_dictionary.md)

---

## 📄 License

MIT
