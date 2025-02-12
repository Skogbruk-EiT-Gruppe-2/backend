from pydantic import BaseModel, Field

class Device(BaseModel):
    deviceId: str
    collectionId: str
    imei: str
    imsi: str
    tags: dict

class CoapMetaData(BaseModel):
    method: str
    path: str

class UdpMetaData(BaseModel):
    localPort: str
    remotePort: str

class SpanMessage(BaseModel):
    device: Device
    payload: str = Field(..., description="JSON string representing BlobMetaData")
    received: int
    type: str
    transport: str
    coapMetaData: CoapMetaData
    udpMetaData: UdpMetaData

class SpanPayload(BaseModel):
    messages: list[SpanMessage]

class Bird(BaseModel):
    name: str
    isRedlisted: bool

class Observation(BaseModel):
    timestamp: str
    latitude: float
    longitude: float
    value: Bird