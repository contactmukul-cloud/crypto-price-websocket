# Crypto Price WebSocket Tracker

## Overview
This project streams live cryptocurrency prices and displays them on a web interface.

## Tech Stack
- Backend: FastAPI + WebSocket
- Frontend: HTML, JavaScript
- Deployment: Render (Backend), Vercel (Frontend)
- Containerization: Docker

## Features
- Real-time crypto price updates
- REST API endpoint for latest price
- Frontend polling every 2 seconds

## Live Links
- Frontend: https://crypto-price-websocket-mfrd4azup-contactmukul-clouds-projects.vercel.app/
- Backend API: https://crypto-price-websocket-ekol.onrender.com/price

## Run Locally

### Backend
```bash
pip install -r requirements.txt
uvicorn app:app --reload
