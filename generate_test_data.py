import struct

imsi = b"123456789012345"  # 15 bytes IMSI
file_number = struct.pack(">H", 1024)  # 2-byte unsigned int (big endian)
sequence_number = struct.pack(">H", 0)  # 2-byte unsigned int (big endian)
audio_blob = b"\x01\x02\x03\x04"  # Replace with actual audio bytes
eof_marker = b"\xFF\xD9"

raw_binary_data = imsi + file_number + sequence_number + audio_blob + eof_marker

with open("test_payload.bin", "wb") as f:
    f.write(raw_binary_data)

print("Binary file created: test_payload.bin")
