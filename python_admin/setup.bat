@echo off
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
cd ..
npx prisma generate
cd python_admin
