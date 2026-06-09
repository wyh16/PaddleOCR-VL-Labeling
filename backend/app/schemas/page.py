from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PageImageRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str | None = Field(
        None,
        title="图片资产编号",
        description="页面图片资产公开编号；页面暂未绑定图片时为空。",
    )
    width: int = Field(..., title="页面宽度", description="页面宽度，单位像素。")
    height: int = Field(..., title="页面高度", description="页面高度，单位像素。")
    sha256: str | None = Field(
        None,
        title="图片 SHA-256",
        description="页面图片资产 SHA-256，用于完整性追踪。",
    )


class PageReadData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_id: str = Field(..., title="页面编号", description="页面公开稳定编号。")
    document_id: str = Field(..., title="文档编号", description="文档公开稳定编号。")
    project_id: int = Field(
        ..., title="项目内部编号", description="项目数据库内部主键。"
    )
    page_index: int = Field(
        ..., title="页序号", description="文档内页序号，从 0 开始。"
    )
    status: str = Field(..., title="页面状态", description="页面导入和标注状态。")
    capture_method: str | None = Field(
        None, title="采集方式", description="页面采集方式。"
    )
    visual_difficulty: str | None = Field(
        None, title="视觉难度", description="视觉难度标签。"
    )
    image: PageImageRead = Field(..., title="页面图片", description="页面图片元数据。")


class PageReadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: PageReadData = Field(..., title="页面详情")
    request_id: str = Field(..., title="请求编号", description="本次请求的追踪编号。")
