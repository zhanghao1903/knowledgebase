import uuid

from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.document import (
    DocumentList,
    DocumentRecrawlResponse,
    DocumentResponse,
    DocumentURLCreateRequest,
    DocumentUploadResponse,
    DocumentVersionResponse,
)
from app.services import document as doc_service

router = APIRouter(tags=["Document"])


@router.post(
    "/knowledge-bases/{kb_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=201,
)
async def upload_document(
    kb_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """上传文档到指定知识库（支持 PDF、TXT、DOCX）"""
    doc, task = await doc_service.upload_document(db, kb_id, file)
    return DocumentUploadResponse(document=doc, task_id=task.id)


@router.get(
    "/knowledge-bases/{kb_id}/documents",
    response_model=DocumentList,
)
async def list_documents(
    kb_id: uuid.UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取知识库下的文档列表"""
    items, total = await doc_service.list_documents(db, kb_id, offset, limit)
    return DocumentList(items=items, total=total)


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """获取文档详情"""
    return await doc_service.get_document(db, doc_id)


@router.get(
    "/documents/{doc_id}/versions",
    response_model=list[DocumentVersionResponse],
)
async def get_document_versions(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """获取文档的版本列表"""
    return await doc_service.get_document_versions(db, doc_id)


@router.post(
    "/knowledge-bases/{kb_id}/documents/url",
    response_model=DocumentUploadResponse,
    status_code=201,
)
async def upload_url_document(
    kb_id: uuid.UUID,
    payload: DocumentURLCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """从 URL 抓取网页并加入知识库（单页，HTML 正文提取）"""
    doc, task = await doc_service.upload_url_document(db, kb_id, payload.url)
    return DocumentUploadResponse(document=doc, task_id=task.id)


@router.post(
    "/documents/{doc_id}/recrawl",
    response_model=DocumentRecrawlResponse,
    status_code=200,
)
async def recrawl_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """重新抓取 URL 文档；内容哈希变化才会生成新版本"""
    doc, task, changed = await doc_service.recrawl_url_document(db, doc_id)
    if changed:
        return DocumentRecrawlResponse(
            document=doc,
            task_id=task.id if task else None,
            changed=True,
            message="URL content changed; new version ingest started",
        )
    return DocumentRecrawlResponse(
        document=doc,
        task_id=None,
        changed=False,
        message="URL content unchanged; no new version created",
    )


@router.put(
    "/documents/{doc_id}/reupload",
    response_model=DocumentUploadResponse,
    status_code=200,
)
async def reupload_document(
    doc_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """重新上传文档（创建新版本并重新入库）"""
    doc, task = await doc_service.reupload_document(db, doc_id, file)
    return DocumentUploadResponse(
        document=doc,
        task_id=task.id,
        message="Document re-uploaded, new version processing started",
    )


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """删除文档及其所有切块"""
    await doc_service.delete_document(db, doc_id)
