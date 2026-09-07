# QueryLens Setup Guide

## Quick Start (5 minutes)

### Prerequisites
- Node.js 18+ and pnpm (or npm)
- Python 3.10+
- Gemini API key (get one at https://aistudio.google.com/apikey)

### Step 1: Clone and Install Dependencies

```bash
# Install Node dependencies
pnpm install

# Install Python dependencies
pip install -r requirements.txt
# OR if using uv:
uv add -r pyproject.toml
```

### Step 2: Set Up Environment Variables

```bash
# Copy example env file
cp .env.example .env.local

# Edit .env.local and add your Gemini API key
# GEMINI_API_KEY=your_key_here
# GEMINI_MODEL=gemini-2.0-flash
# ALLOW_CLIENT_LLM_CONFIG=false
```

### Step 3: Run the Application

Option A - Using the startup script:
```bash
chmod +x start.sh
./start.sh
```

Option B - Run in separate terminals:

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
pnpm dev
```

### Step 4: Access the App

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## File Structure

```
QueryLens/
├── app/                          # Next.js application
│   ├── page.tsx                 # Main dashboard page
│   ├── globals.css              # Global styles & theme
│   └── layout.tsx               # Root layout
├── components/                   # React components
│   ├── file-upload-panel.tsx    # File upload interface
│   ├── schema-viewer.tsx        # Table schema display
│   ├── chat-interface.tsx       # Query chat UI
│   ├── query-results.tsx        # Results table
│   └── error-boundary.tsx       # Error handling
├── hooks/
│   └── use-query-lens.ts        # Main data hook
├── backend/                      # FastAPI backend
│   ├── main.py                  # FastAPI application
│   ├── config.py                # Configuration
│   ├── models.py                # SQLAlchemy models
│   ├── database.py              # Database utilities
│   ├── llm.py                   # LLM integration
│   └── __init__.py
├── data/                         # Data storage (auto-created)
│   ├── querylens.db             # SQLite database
│   └── uploads/                 # Uploaded CSV files
├── public/                       # Static assets
├── README.md                     # Project documentation
├── SETUP.md                      # This file
├── package.json                  # Node dependencies
├── pyproject.toml               # Python project config
├── requirements.txt             # Python dependencies
├── tailwind.config.ts           # Tailwind CSS config
├── tsconfig.json                # TypeScript config
└── start.sh                      # Startup script
```

## Usage

1. **Upload Data**: Drag a CSV file into the upload area
2. **Select Table**: Choose the uploaded dataset
3. **Ask Questions**: Type natural language questions like:
   - "Show me all records from 2024"
   - "What's the average price?"
   - "Count records by category"
4. **View Results**: Results appear in a formatted table
5. **Check History**: View all previous queries in the History tab

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# If in use, kill the process or use a different port
python -m uvicorn backend.main:app --port 8001
```

### Frontend won't start
```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
pnpm install --force

# Try again
pnpm dev
```

### Database errors
```bash
# Reset the database
rm data/querylens.db

# Restart the backend to recreate tables
```

### Gemini API errors
- Check your API key is correct in `.env.local`
- Verify account has available credits
- Check rate limits aren't exceeded

### CORS errors
Ensure:
- Frontend is running on `http://localhost:3000`
- Backend is running on `http://localhost:8000`
- Environment variables are set correctly

## Development

### Backend API Documentation
Visit http://localhost:8000/docs for interactive API documentation

### Available Endpoints
- `GET /` - Health check
- `POST /upload` - Upload CSV file
- `GET /tables` - List available tables
- `GET /schema/{table_name}` - Get table schema
- `POST /query` - Generate and execute query
- `GET /history` - Query history

### Python Backend Testing
```bash
cd backend
python -c "from main import app; print('Backend imports OK')"
```

## Deployment

### To Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy frontend
vercel deploy

# Backend needs separate hosting (Railway, Heroku, etc.)
```

### To Docker

Create a Dockerfile for production deployment:
```dockerfile
FROM node:18 as frontend-build
WORKDIR /app
COPY . .
RUN pnpm install && pnpm build

FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY --from=frontend-build /app/.next ./.next
COPY --from=frontend-build /app/public ./public
EXPOSE 3000 8000
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & pnpm start"]
```

## Performance Tips

- Use SQLite for small datasets (< 100MB)
- For larger datasets, migrate to PostgreSQL
- Add query result pagination for large result sets
- Cache frequently used queries
- Optimize CSV import by chunking large files

## Security Notes

- All SQL queries are validated for SELECT-only operations
- User inputs are sanitized
- CORS is configured to trusted origins
- Consider adding authentication for production use
- Store sensitive keys in secure environment variables

## Next Steps

- Customize the theme in `globals.css`
- Add authentication with Auth.js
- Connect to production database (PostgreSQL)
- Deploy to cloud platform
- Add more LLM providers (Claude, Llama, etc.)

## Support

For issues:
1. Check the API docs at http://localhost:8000/docs
2. Review backend logs for errors
3. Check browser console for frontend errors
4. Verify environment variables are set
