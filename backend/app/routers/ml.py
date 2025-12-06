from fastapi import APIRouter, Depends, UploadFile, File
from pathlib import Path
import shutil
from ..core.deps import get_current_admin
from ..core.db import get_db
from ..services.ml_service import retrain_from_file

router = APIRouter(prefix="/ml", tags=["ml"])

@router.post("/retrain")
async def retrain(
    file: UploadFile = File(...),
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    tmp_path = Path(f"/tmp/{file.filename}")
    with tmp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # naive versioning: count existing versions
    count = db["model_versions"].count_documents({"username": current_admin["username"]})
    version = count + 1
    metrics = retrain_from_file(db, current_admin["username"], tmp_path, version)
    return {"version": version, "metrics": metrics}
