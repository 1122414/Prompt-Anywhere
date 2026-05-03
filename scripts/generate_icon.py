import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QBuffer, QIODevice

app = QApplication.instance() or QApplication(sys.argv)

from app.utils.icon_utils import create_app_icon

icon = create_app_icon()
pixmap = icon.pixmap(256, 256)
output_dir = Path(__file__).parent.parent / "assets"
output_dir.mkdir(parents=True, exist_ok=True)

png_path = output_dir / "app_icon.png"
pixmap.save(str(png_path))

png_data = png_path.read_bytes()
ico_path = output_dir / "app_icon.ico"

num_images = 1
header = struct.pack("<HHH", 0, 1, num_images)
offset = 6 + 16
entry = struct.pack("<BBBBHHII",
    0, 0,
    0,
    0,
    1, 32,
    len(png_data),
    offset,
)
ico_path.write_bytes(header + entry + png_data)

print(f"Icon saved: {png_path}")
print(f"Icon saved: {ico_path}")
