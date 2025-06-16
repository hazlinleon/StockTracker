from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class NewsSource(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    url: str
    source_type: str  # news, official, wechat
    is_active: bool = True
    last_crawled: Optional[datetime] = None
    crawl_interval: int = 300  # 秒
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class NewsItem(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str
    content: str
    url: str
    source_name: str
    source_type: str
    publish_time: datetime
    crawl_time: datetime = Field(default_factory=datetime.now)
    is_processed: bool = False
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class AnalysisResult(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    news_id: PyObjectId
    sentiment_score: int  # 1-10
    sentiment_desc: str
    affected_sectors: List[str]
    affected_concepts: List[str]
    related_stocks: List[str]
    time_range: str  # 短期/中期/长期
    importance: int  # 1-5星
    summary: str
    analysis_time: datetime = Field(default_factory=datetime.now)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class StockInfo(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    code: str
    name: str
    sector: str
    concepts: List[str]
    market: str  # SH/SZ
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Subscriber(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    platform: str  # telegram, wechat, email
    chat_id: str
    is_active: bool = True
    subscribe_types: List[str] = ["all"]  # all, important_only, sectors
    interested_sectors: List[str] = []
    interested_stocks: List[str] = []
    created_time: datetime = Field(default_factory=datetime.now)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Alert(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    news_id: PyObjectId
    analysis_id: PyObjectId
    title: str
    content: str
    importance: int
    sent_to: List[str] = []
    created_time: datetime = Field(default_factory=datetime.now)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str} 