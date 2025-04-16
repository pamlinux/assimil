MENU_ITEMS = [
    {
        "category": "Accueil",
        "items": [{"name": "Accueil", "url": "/spanish/", "key": "home"}]
    },
    {
        "category": "Espagnol de base",
        "items": [
            {"name": "Première phase", "url": "/basic/first-phase/", "key": "basic-first-phase"},
            {"name": "Seconde phase", "url": "/basic/second-phase/", "key": "basic-second-phase"},
            {"name": "Historique", "url": "/basic/history/", "key": "basic-history"},
        ]
    },
    {
        "category": "Espagnol avancé",
        "items": [
            {"name": "Première phase", "url": "/using-spanish/first-phase/", "key": "using-spanish-first-phase"},
            {"name": "Seconde phase", "url": "/using-spanish/second-phase/", "key": "using-spanish-second-phase"},
            {"name": "Historique", "url": "/using-spanish/history/", "key": "using-spanish-history"},
        ]
    },
    {
        "category": "Vidéo",
        "items": [
            {"name": "Recherche de video", "url": "/video", "key": "video-search"},
            {"name": "dernière vidéo", "url": "/video", "key": "last-video"}
        ]
    },
    {
        "category": "Maintenance",
        "toggleable": True,  # Permet d'afficher/masquer les items
        "items": [
            {"name": "Correction de paragraphes", "url": "/correct-assimil-paragraphs/?prog=single", "key": "correct-paragraphs"},
            {"name": "Ajout de notes", "url": "/test-grammar/?level=0&lesson_nb=95", "key": "grammar"},
            {"name": "Éditeur d'accent tonique", "url": "/using-spanish/editor/1", "key": "using-spanish-editor"},
            {"name": "Marquer les erreurs", "url": "/marker-editor/1", "key": "marker-editor"},
        ]
    }
]
