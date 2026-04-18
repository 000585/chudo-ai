import os, sys

fp = 'app/main.py'
if not os.path.exists(fp):
    print('ERROR: app/main.py not found')
    sys.exit(1)

with open(fp, 'r', encoding='utf-8') as f:
    content = f.read()

# --- import ---
if 'from app.api import chat_context' not in content:
    lines = content.splitlines()
    out = []
    added = False
    for line in lines:
        out.append(line)
        if not added and line.startswith('from app.api import'):
            out.append('from app.api import chat_context')
            added = True
    if not added:
        out.insert(0, 'from app.api import chat_context')
    content = '\n'.join(out)
    print('PATCH: added import chat_context')

# --- router ---
if 'chat_context.router' not in content:
    lines = content.splitlines()
    out = []
    added = False
    for line in lines:
        out.append(line)
        if not added and 'app.include_router(chat.router' in line:
            # берем тот же prefix что и у chat.router
            out.append('app.include_router(chat_context.router, prefix="/api/v1")')
            added = True
    if not added:
        out.append('app.include_router(chat_context.router, prefix="/api/v1")')
    content = '\n'.join(out)
    print('PATCH: added router chat_context')

# --- startup create_all ---
if 'Base.metadata.create_all' not in content:
    startup = '''
@app.on_event("startup")
async def startup_event():
    import app.models.message
    from app.db.base import Base
    from app.core.config import settings
    from sqlalchemy.ext.asyncio import create_async_engine
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(db_url, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
'''
    if "if __name__ ==" in content:
        content = content.replace("if __name__ ==", startup + "\nif __name__ ==")
    else:
        content += startup
    print('PATCH: added startup_event')

with open(fp, 'w', encoding='utf-8') as f:
    f.write(content)
print('DONE: app/main.py patched')
