import typer
from rich.console import Console
from rich.table import Table
from .database import SessionLocal
from . import models, scheduler
import json

app = typer.Typer()
console = Console()

def get_db_session():
    return SessionLocal()

@app.command()
def list_packs(status: str = None):
    db = get_db_session()
    query = db.query(models.ContentPack)
    if status:
        query = query.filter(models.ContentPack.status == status)
    packs = query.all()
    
    table = Table(title="Content Packs")
    table.add_column("ID")
    table.add_column("Lane")
    table.add_column("Status")
    table.add_column("Created At")
    
    for p in packs:
        table.add_row(str(p.id), p.lane, p.status, str(p.created_at))
    
    console.print(table)
    db.close()

@app.command()
def approve_pack(id: int):
    db = get_db_session()
    pack = db.query(models.ContentPack).filter(models.ContentPack.id == id).first()
    if pack:
        pack.status = models.PackStatus.approved
        db.commit()
        console.print(f"Pack {id} approved.")
    else:
        console.print(f"Pack {id} not found.")
    db.close()

@app.command()
def reject_pack(id: int):
    db = get_db_session()
    pack = db.query(models.ContentPack).filter(models.ContentPack.id == id).first()
    if pack:
        pack.status = models.PackStatus.rejected
        db.commit()
        console.print(f"Pack {id} rejected.")
    else:
        console.print(f"Pack {id} not found.")
    db.close()

@app.command()
def schedule_tick(dry_run: bool = False):
    db = get_db_session()
    result = scheduler.tick(db, dry_run=dry_run)
    console.print(result)
    db.close()

@app.command()
def show_policy():
    db = get_db_session()
    policy = scheduler.get_policy(db)
    console.print(f"Active: {policy.active}")
    console.print(f"Start Date: {policy.start_date}")
    console.print(f"Slots: {policy.slots_json}")
    db.close()

if __name__ == "__main__":
    app()
