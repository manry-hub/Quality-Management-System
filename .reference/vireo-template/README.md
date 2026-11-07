# Vireo — Django Edition

Django server-rendered admin template with Tailwind CSS v4 and Alpine.js, with front-end assets built via Vite.

## Requirements

- Python 3.11+
- pip
- Node.js 18+ (for the Tailwind/Vite asset build)

## Getting started

1. Install dependencies:

   ```bash
   python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
   ```

2. Set up the database:

   ```bash
   python manage.py migrate
   ```

3. Build the front-end assets and collect static files:

   ```bash
   npm install && npm run build && python manage.py collectstatic --noinput
   ```

4. Start the development server:

   ```bash
   python manage.py runserver
   ```

   The app is now available at http://127.0.0.1:8000/.

## Production build

Rebuild the compiled Tailwind/Vite assets:

```bash
npm run build
```

## Run / serve

```bash
python manage.py runserver
```

## Documentation

Full documentation is available at [../../Documentation/index.html](../../Documentation/index.html).
