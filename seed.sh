#!/usr/bin/env sh
# seed.sh - seed the database

set -e

echo "🚀 Starting database seed process..."

python manage.py loaddata specialties
python manage.py loaddata users
python manage.py loaddata patients
python manage.py loaddata doctors
python manage.py loaddata doctor_specialties
python manage.py loaddata clinics
python manage.py loaddata assistants

echo "✅ All seeders completed successfully!"
