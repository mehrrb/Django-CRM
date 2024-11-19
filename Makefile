run_app:
	python manage.py migrate
	python manage.py makemigrations accounts common contacts reports invoices emails tasks teams users
	python manage.py migrate accounts
	python manage.py migrate common
	python manage.py migrate contacts
	python manage.py migrate reports
	python manage.py migrate invoices
	python manage.py migrate emails
	python manage.py migrate tasks
	python manage.py migrate teams
	python manage.py migrate users
	python manage.py runserver 0.0.0.0:8000

run: run_app