#!/bin/bash
#check if gunicorn is installed, if not install it
if ! pip show gunicorn > /dev/null 2>&1; then
    echo "gunicorn not found, installing..."
    pip install gunicorn
fi

#Activate virtual environment
source .venv/bin/activate

#Apply migrations
echo "Applying migrations..."
python migrate.py apply

#Check if intent model is trained
if [ ! -f "ai_bot/intent_classifier.joblib" ] || [ ! -f "ai_bot/intent_vectorizer.joblib" ]; then
    echo "Intent model not found, training..."
    python ai_bot/ml_intent_detection.py
fi

#Setting port and ip
IP="127.0.0.1"
PORT="80"

#start the server with gunicorn
echo "Starting server with gunicorn on $IP:$PORT..."
gunicorn index:app --bind $IP:$PORT --workers 4
echo "Server started on http://$IP:$PORT"