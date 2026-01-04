from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from uuid import uuid4

from .db import Base, engine, get_db
from .models import Volcano, VolcanoStatusCurrent, VolcanoStatusHistory
from .schemas import VolcanoCreate, VolcanoOut, normalize_level, VALID_LEVELS

app = FastAPI(title="Volcano Service (Normalized)", version="0.2.0")

# Auto-create table (untuk development/testing).
# Di production Railway, sebaiknya gunakan schema.sql atau migration tool (Alembic).
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Volcano Service API is running", "docs_url": "/docs"}

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/v1/volcano", response_model=VolcanoOut)
def create_volcano_status(payload: VolcanoCreate, db: Session = Depends(get_db)):
    """
    Menerima data gunung & status. 
    1. Cek/Buat Master Gunung (volcanoes)
    2. Update Status Terkini (volcano_status_current)
    3. Catat di History (volcano_status_history)
    """
    lvl = normalize_level(payload.level)
    if lvl not in VALID_LEVELS:
        raise HTTPException(400, f"level harus salah satu: {sorted(VALID_LEVELS)}")

    # 1. Cek apakah gunung sudah ada (by name)
    stmt = select(Volcano).where(Volcano.name == payload.name)
    volcano = db.execute(stmt).scalars().first()

    if not volcano:
        # Create new volcano master
        volcano = Volcano(
            name=payload.name,
            province=payload.province,
            latitude=payload.latitude,
            longitude=payload.longitude
        )
        db.add(volcano)
        db.flush() # flush to get ID
    else:
        # Update master data if needed (optional, assuming incoming data might be newer fix)
        # For now let's just update coordinates/province if they changed? 
        # Or assume master doesn't change often. Let's update just in case.
        volcano.province = payload.province
        volcano.latitude = payload.latitude
        volcano.longitude = payload.longitude
        db.add(volcano)

    # 2. Upsert Current Status
    # Cek existing status
    current_status = db.execute(
        select(VolcanoStatusCurrent).where(VolcanoStatusCurrent.volcano_id == volcano.id)
    ).scalars().first()

    if not current_status:
        current_status = VolcanoStatusCurrent(volcano_id=volcano.id)
    
    current_status.level = lvl
    current_status.status_text = payload.status_text
    current_status.source = payload.source
    current_status.observed_at = payload.observed_at
    
    db.add(current_status)

    # 3. Insert History
    # History always new record
    history = VolcanoStatusHistory(
        volcano_id=volcano.id,
        level=lvl,
        status_text=payload.status_text,
        source=payload.source,
        observed_at=payload.observed_at
    )
    db.add(history)

    db.commit()
    db.refresh(volcano)
    db.refresh(current_status)

    return VolcanoOut(
        id=volcano.id,
        name=volcano.name,
        province=volcano.province,
        latitude=volcano.latitude,
        longitude=volcano.longitude,
        level=current_status.level,
        source=current_status.source,
        status_text=current_status.status_text,
        observed_at=current_status.observed_at,
        updated_at=current_status.updated_at
    )

@app.get("/v1/volcano", response_model=list[VolcanoOut])
def list_volcano(
    db: Session = Depends(get_db),
    level: str | None = Query(None),
    province: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    # Join Volcano + Status Current
    stmt = select(Volcano, VolcanoStatusCurrent).join(Volcano.current_status)

    if level:
        lvl = normalize_level(level)
        stmt = stmt.where(VolcanoStatusCurrent.level == lvl)

    if province:
        stmt = stmt.where(Volcano.province.ilike(f"%{province}%"))

    if q:
        stmt = stmt.where(Volcano.name.ilike(f"%{q}%"))

    # Order by updated_at desc (newest update likely most interesting)
    stmt = stmt.order_by(desc(VolcanoStatusCurrent.observed_at)).limit(limit)

    rows = db.execute(stmt).all()
    
    results = []
    for v, s in rows:
        results.append(VolcanoOut(
            id=v.id,
            name=v.name,
            province=v.province,
            latitude=v.latitude,
            longitude=v.longitude,
            level=s.level,
            source=s.source,
            status_text=s.status_text,
            observed_at=s.observed_at,
            updated_at=s.updated_at
        ))
    
    return results

@app.get("/v1/volcano/{vid}", response_model=VolcanoOut)
def get_volcano(vid: str, db: Session = Depends(get_db)):
    stmt = select(Volcano, VolcanoStatusCurrent).join(Volcano.current_status).where(Volcano.id == vid)
    row = db.execute(stmt).first()

    if not row:
        raise HTTPException(404, "not found")
    
    v, s = row
    return VolcanoOut(
        id=v.id,
        name=v.name,
        province=v.province,
        latitude=v.latitude,
        longitude=v.longitude,
        level=s.level,
        source=s.source,
        status_text=s.status_text,
        observed_at=s.observed_at,
        updated_at=s.updated_at
    )

@app.delete("/v1/volcano/{vid}")
def delete_volcano(vid: str, db: Session = Depends(get_db)):
    # Cascade delete should handle children, but let's select logic
    stmt = select(Volcano).where(Volcano.id == vid)
    v = db.execute(stmt).scalars().first()
    
    if not v:
        raise HTTPException(404, "not found")
    
    db.delete(v)
    db.commit()
    return {"deleted": True, "id": vid}
