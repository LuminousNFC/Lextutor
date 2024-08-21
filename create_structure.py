"""Module docstring: This module does XYZ."""
import os

# Définir la structure du projet
project_structure = {
    "app": [
        "__init__.py",
        "main.py",
        "config.py",
        "routes.py",
        "database.py",
        "fedlex_references.json",
        "fedlex_extractor.py",
        "beta_entscheidsuche_extractor.py",
    ],
    "static": [
        "index.html",
        "script.js",
        "styles.css"
    ],
    ".": [
        ".env",
        "requirements.txt",
        "README.md"
    ]
}

# Chemin racine du projet
PROJECT_ROOT = "C:/PoC MasterLaw"

def create_project_structure(root, structure):
    """Function docstring."""
    for folder, files in structure.items():
        # Créer le chemin complet du dossier
        folder_path = os.path.join(root, folder)
        os.makedirs(folder_path, exist_ok=True)

        for file in files:
            # Créer chaque fichier dans le dossier
            file_path = os.path.join(folder_path, file)
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    # Optionnel : ajouter un contenu initial pour certains fichiers
                    if file.endswith(".py"):
                        f.write("# Ce fichier peut rester vide pour l'instant
")
                    elif file == "README.md":
                        f.write("# PoC MasterLaw

Ce projet utilise FastAPI pour l'analyse juridique
")
                    elif file == "requirements.txt":
                        f.write("fastapi==0.111.0
pydantic==1.10.12
uvicorn==0.22.0
requests==2.3
")
                    elif file == ".env":
                        f.write("DATABASE_URL=sqlite:///./test.db
SECRET_KEY=your_secret_key
")

# Exécution du script pour créer l'arborescence
create_project_structure(PROJECT_ROOT, project_structure)

print("Arborescence du projet créée avec succès!")
