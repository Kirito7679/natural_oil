"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables, SessionLocal
from app.config import settings
from app.routers import (
    auth,
    balance,
    products,
    partners,
    purchases,
    inventory,
    sales,
    debts,
    expenses,
    reports,
    excel_export,
    users,
    admin,
    report_tabs,
)
from app.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed initial data on startup."""
    create_tables()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Natural Oil ERP",
    description="Natural Oil ERP backend API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Production domains
        "https://naturaloilerp.uz",
        "https://www.naturaloilerp.uz",
        # Local development
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(balance.router)
app.include_router(products.router)
app.include_router(partners.router)
app.include_router(purchases.router)
app.include_router(inventory.router)
app.include_router(sales.router)
app.include_router(debts.router)
app.include_router(expenses.router)
app.include_router(reports.router)
app.include_router(excel_export.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(report_tabs.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Natural Oil ERP API"}


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": "Natural Oil ERP"}