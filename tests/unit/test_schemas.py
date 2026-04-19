"""Unit tests for Pydantic schema validation."""
import uuid

import pytest
from pydantic import ValidationError

from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate
from app.schemas.qa import QueryRequest

pytestmark = pytest.mark.unit


class TestKnowledgeBaseCreate:
    def test_valid(self):
        s = KnowledgeBaseCreate(name="测试知识库")
        assert s.name == "测试知识库"
        assert s.description is None

    def test_with_description(self):
        s = KnowledgeBaseCreate(name="KB", description="说明")
        assert s.description == "说明"

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            KnowledgeBaseCreate(name="")

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            KnowledgeBaseCreate(name="A" * 256)


class TestKnowledgeBaseUpdate:
    def test_partial_update(self):
        s = KnowledgeBaseUpdate(name="新名称")
        data = s.model_dump(exclude_unset=True)
        assert data == {"name": "新名称"}

    def test_empty_update(self):
        s = KnowledgeBaseUpdate()
        data = s.model_dump(exclude_unset=True)
        assert data == {}


class TestQueryRequest:
    def test_valid(self):
        q = QueryRequest(question="什么是向量检索？")
        assert q.question == "什么是向量检索？"
        assert q.top_k == 5  # default from settings

    def test_custom_top_k(self):
        q = QueryRequest(question="test", top_k=10)
        assert q.top_k == 10

    def test_empty_question_rejected(self):
        with pytest.raises(ValidationError):
            QueryRequest(question="")

    def test_top_k_out_of_range(self):
        with pytest.raises(ValidationError):
            QueryRequest(question="test", top_k=0)
        with pytest.raises(ValidationError):
            QueryRequest(question="test", top_k=21)
