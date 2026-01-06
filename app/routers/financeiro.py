from fastapi import APIRouter

router = APIRouter(
    prefix="/os",
    tags=["OS"]
)

@router.get("/nova")
def os_nova():
    return {"status": "rota /os/nova funcionando"}
