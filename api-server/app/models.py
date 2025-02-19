from pydantic import BaseModel, Field
from typing import Literal, Dict, Optional

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

class WebhookMessage(BaseModel):
    device: Device
    payload: str = Field(..., description="JSON string representing BlobMetaData")
    received: int
    type: str
    transport: str
    coapMetaData: CoapMetaData
    udpMetaData: UdpMetaData

class WebhookPayload(BaseModel):
    messages: list[WebhookMessage]

class Bird(BaseModel):
    name: str
    isRedlisted: bool

class Observation(BaseModel):
    timestamp: str
    latitude: float
    longitude: float
    value: Bird

# Nested models for SpanMessage
class SpanFirmware(BaseModel):
    currentFirmwareId: str
    targetFirmwareId: str
    firmwareVersion: str
    serialNumber: str
    modelNumber: str
    manufacturer: str
    state: str
    stateMessage: str

class SpanCiotConfig(BaseModel):
    imsi: str
    imei: str

class SpanConfig(BaseModel):
    ciot: SpanCiotConfig
    inet: Dict
    gateway: Dict

class SpanCiotMetadata(BaseModel):
    gatewayId: str
    allocatedIp: str
    allocatedAt: str
    cellId: str
    mcc: int
    mnc: int
    country: str
    network: str
    countryCode: str
    lastUpdate: str
    lastImsi: str
    lastImei: str

class SpanInetMetadata(BaseModel):
    gatewayId: str
    lastUpdate: str
    remoteAddress: str
    certificateSerial: str

class SpanGatewayMetadata(BaseModel):
    gatewayId: str
    lastUpdate: str
    params: Dict

class SpanMetadata(BaseModel):
    ciot: SpanCiotMetadata
    inet: SpanInetMetadata
    gateway: SpanGatewayMetadata

class SpanDevice(BaseModel):
    deviceId: str
    collectionId: str
    tags: Dict
    firmware: SpanFirmware
    config: SpanConfig
    metadata: SpanMetadata
    lastGatewayId: str
    lastTransport: str  = "unspecified"
    lastReceived: str
    lastPayload: str

# Metadata models for SpanMessage
class SpanUdpMetaData(BaseModel):
    localPort: int
    remotePort: int

class SpanCoapMetaData(BaseModel):
    code: Literal["POST", "GET"]
    path: str

class SpanMqttMetaData(BaseModel):
    topic: str

# Main SpanMessage model
class SpanMessage(BaseModel):
    messageId: str
    type: Literal["keepalive", "data"]
    device: SpanDevice
    payload: str
    received: str
    transport: Literal["udp", "coap", "mqtt"]
    udpMetaData: Optional[SpanUdpMetaData] = None
    coapMetaData: Optional[SpanCoapMetaData] = None
    mqttMetaData: Optional[SpanMqttMetaData] = None
    gatewayMetaData: Dict[str, str]
    gatewayId: str


