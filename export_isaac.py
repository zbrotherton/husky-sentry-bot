import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from ament_index_python.packages import get_package_share_directory

export_dir = Path("/home/ros2_ws/clearpath")
urdf_path = export_dir / "husky_full.urdf"

tree = ET.parse(urdf_path)
root = tree.getroot()

copied_packages = set()

for element in root.iter():
    for attribute in ("filename", "url"):
        uri = element.get(attribute)

        if not uri or not uri.startswith("package://"):
            continue

        package_path = uri.removeprefix("package://")
        package_name, separator, relative_path = package_path.partition("/")

        if not separator:
            raise ValueError(f"Invalid package URI: {uri}")

        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe package URI: {uri}")

        source = Path(get_package_share_directory(package_name))
        destination = export_dir / "packages" / package_name

        if not (source / relative).exists():
            raise FileNotFoundError(uri)

        if package_name not in copied_packages:
            shutil.copytree(source, destination, dirs_exist_ok=True)
            copied_packages.add(package_name)
            print(f"Copied: {package_name}")

        element.set(
            attribute,
            f"./packages/{package_name}/{relative.as_posix()}"
        )

output = export_dir / "husky.urdf"

tree.write(output, encoding="utf-8", xml_declaration=True)

print(f"\nExported: {output}")
