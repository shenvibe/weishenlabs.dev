"""Regenerates assets/tip-qr.png (TNG DuitNow QR) in the site colours. Needs: pip install "qrcode[pil]"."""
import qrcode
from pathlib import Path

PAYLOAD = "00020201021126440014A0000006150001010689005302121102595745695204000053034585802MY5910TANWEISHEN6002MY6213060991415621863048905"


def crc16(data):  # CRC-16/CCITT-FALSE, the checksum DuitNow/EMVCo QR uses in its last field
    crc = 0xFFFF
    for b in data.encode():
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else crc << 1
            crc &= 0xFFFF
    return f"{crc:04X}"


assert crc16(PAYLOAD[:-4]) == PAYLOAD[-4:], "payload checksum mismatch"
qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=12, border=3)
qr.add_data(PAYLOAD)
qr.make(fit=True)
out = Path(__file__).resolve().parent.parent / "assets" / "tip-qr.png"
qr.make_image(fill_color="#3b2f27", back_color="#fffaf0").save(out)
print("wrote", out.name, "version", qr.version)
