#"""
#setup.py - Script untuk membuat struktur project
#Simpan di: C:\Users\jk2161203\Documents\D-CONDA\d-conda\setup.py
#"""

import os

# Base path
base_path = r"C:\Users\jk2161203\Documents\D-CONDA\d-conda"

# Struktur folder
folders = [
    "pages",
    "components", 
    "utils",
    "data"
]

# File yang akan dibuat
files = {
    "": [  # Root folder
        "main.py",
        "config.py", 
        "app_controller.py"
    ],
    "pages": [
        "__init__.py",
        "base_page.py",
        "dashboard_page.py",
        "table_settings_page.py",
        "plc_settings_page.py",
        "help_page.py"
    ],
    "components": [
        "__init__.py",
        "sidebar.py",
        "dialogs.py"
    ],
    "utils": [
        "__init__.py",
        "data_manager.py",
        "plc_fins.py"
    ]
}

def create_structure():
    """Membuat struktur folder dan file"""
    print("🚀 Membuat struktur project...\n")
    
    # Buat folder utama
    os.makedirs(base_path, exist_ok=True)
    print(f"✅ Folder utama: {base_path}")
    
    # Buat subfolder
    for folder in folders:
        folder_path = os.path.join(base_path, folder)
        os.makedirs(folder_path, exist_ok=True)
        print(f"✅ Folder: {folder}")
    
    print("\n📄 Membuat file...\n")
    
    # Buat file
    for folder, file_list in files.items():
        for filename in file_list:
            # Tentukan path file
            if folder == "":
                file_path = os.path.join(base_path, filename)
            else:
                file_path = os.path.join(base_path, folder, filename)
            
            # Buat file dengan template
            with open(file_path, "w", encoding="utf-8") as f:
                if filename == "__init__.py":
                    f.write(f'"""\n{folder} package\n"""\n')
                else:
                    f.write(f'"""\n{filename}\n"""\n\n')
            
            print(f"✅ {file_path}")
    
    print("\n" + "="*60)
    print("🎉 Setup selesai!")
    print("="*60)
    print(f"\n📁 Lokasi project: {base_path}")
    print("\n📋 Struktur folder:")
    print("""
flexible_table_app/
├── main.py
├── config.py
├── app_controller.py
├── pages/
│   ├── __init__.py
│   ├── base_page.py
│   ├── dashboard_page.py
│   ├── table_settings_page.py
│   ├── plc_settings_page.py
│   └── help_page.py
├── components/
│   ├── __init__.py
│   ├── sidebar.py
│   └── dialogs.py
├── utils/
│   ├── __init__.py
│   ├── data_manager.py
│   └── plc_fins.py
└── data/
    """)
    
    print("\n🔧 Langkah selanjutnya:")
    print(f'1. cd "{base_path}"')
    print("2. code .  (untuk buka di VS Code)")
    print("3. Mulai coding!")

if __name__ == "__main__":
    create_structure()