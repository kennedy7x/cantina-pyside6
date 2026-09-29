"""Catálogo real da cantina (doces, salgados, bebidas)."""

CATEGORIES = ["Doces", "Salgados", "Bebidas", "Cup Noodles", "Biscoitos", "Chicletes"]

PRODUCTS = [
    # ---------- DOCES ----------
    ("Doce",                 "Doces", 3.00),
    ("Paçoca",               "Doces", 1.00),
    ("Bom bom",              "Doces", 2.50),
    ("Trento",               "Doces", 4.50),
    ("Biscoito",             "Doces", 3.50),
    ("Emilia",               "Doces", 2.50),
    ("Halls",                "Doces", 2.50),
    ("Bolo",                 "Doces", 6.00),
    ("Suspiro",              "Doces", 3.00),
    ("Pão de mel",           "Doces", 5.00),
    ("Copinho de banana",    "Doces", 3.00),
    ("Cocada",               "Doces", 3.00),
    ("Doce em massa de batata doce", "Doces", 3.00),
    ("Cajuzinho",            "Doces", 3.00),
    ("Geladão",              "Doces", 7.00),
    ("Cremosinho",           "Doces", 2.50),
    ("Maria bolacha",        "Doces", 3.00),
    ("Café",                 "Doces", 2.00),
    ("Chokito",              "Doces", 3.00),

    # ---------- SALGADOS ----------
    ("Croissant de apresentado e queijo", "Salgados", 7.00),
    ("Risole de 4 queijos",               "Salgados", 5.50),
    ("Risole de carne",                   "Salgados", 5.50),
    ("Croissant 3 queijos",               "Salgados", 6.50),
    ("Hambúrguer com cheddar",            "Salgados", 7.00),
    ("Enroladinho de bauru",              "Salgados", 7.00),
    ("Pão de batata com calabresa",       "Salgados", 6.50),
    ("Pão de batata de frango",           "Salgados", 6.50),
    ("Esfiha de carne",                   "Salgados", 7.00),
    ("Coxinha",                           "Salgados", 5.50),
    ("Pão de queijo",                     "Salgados", 3.50),
    ("Caldo (mandioca, abóbora, verde, feijão)", "Salgados", 20.00),
    ("Espeto de carne/medalhão/coração",  "Salgados", 9.00),

    # ---------- BEBIDAS ----------
    ("Guaraná 350ml",            "Bebidas", 5.50),
    ("Fanta uva 350ml",          "Bebidas", 5.50),
    ("Fanta laranja 350ml",      "Bebidas", 5.50),
    ("Coca-Cola zero 350ml",     "Bebidas", 5.50),
    ("Coca-Cola 350ml",          "Bebidas", 5.50),
    ("Suco tropical 480ml",      "Bebidas", 8.00),
    ("Suco Kmais 300ml",         "Bebidas", 7.50),
    ("Refrigerante caçula 200ml","Bebidas", 3.00),

    # ---------- CUP NOODLES ----------
    ("Cup Noodles cheddar",       "Cup Noodles", 7.00),
    ("Cup Noodles galinha caipira","Cup Noodles", 7.00),
    ("Cup Noodles queijo",        "Cup Noodles", 7.00),
    ("Cup Noodles bolonhesa",     "Cup Noodles", 7.00),

    # ---------- BISCOITOS ----------
    ("Biscoito de chocolate", "Biscoitos", 3.50),
    ("Biscoito de morango",   "Biscoitos", 3.50),

    # ---------- CHICLETES ----------
    ("Trident morango",     "Chicletes", 2.50),
    ("Trident tutti-fruit", "Chicletes", 2.50),
    ("Trident menta",       "Chicletes", 2.50),
    ("Trident canela",      "Chicletes", 2.50),
    ("Halls extra forte",   "Chicletes", 2.50),
    ("Halls morango",       "Chicletes", 2.50),
    ("Halls menta",         "Chicletes", 2.50),
    ("Halls melancia",      "Chicletes", 2.50),
]

FLAVORS = {
    "Geladão":     ["leite condensado", "morango", "maracujá", "leite em pó", "paçoca"],
    "Cremosinho":  ["morango", "maracujá", "leite condensado", "coco", "uva",
                    "kiwi", "açaí com banana", "frutas tropicais",
                    "frutas cristalizadas", "manga"],
    "Trento":      ["mousse de maracujá", "torta de limão", "dark", "chocolate"],
    "Bom bom":     ["sonho de valsa", "ouro branco"],
    "Suco tropical": ["uva", "manga", "abacaxi", "açaí", "goiaba"],
    "Suco Kmais":  ["goiaba", "laranja", "uva", "maracujá"],
    "Caldo":       ["mandioca", "abóbora", "verde", "feijão"],
}

ICON_RULES = [
    ("coca", "🥤"), ("fanta", "🥤"), ("guaraná", "🥤"), ("guarana", "🥤"),
    ("pepsi", "🥤"), ("refrigerante", "🥤"), ("caçula", "🥤"), ("cacula", "🥤"),
    ("suco", "🧃"), ("água", "💧"), ("agua", "💧"), ("café", "☕"), ("cafe", "☕"),
    ("coxinha", "🍗"), ("risole", "🥟"), ("esfiha", "🥟"), ("esfirra", "🥟"),
    ("croissant", "🥐"), ("hambúrguer", "🍔"), ("hamburguer", "🍔"),
    ("pão de queijo", "🧀"), ("pao de queijo", "🧀"),
    ("enroladinho", "🌭"), ("caldo", "🍲"), ("espeto", "🍢"),
    ("pão de batata", "🥖"), ("pao de batata", "🥖"),
    ("paçoca", "🥜"), ("pacoca", "🥜"), ("bolo", "🍰"),
    ("cookie", "🍪"), ("biscoito", "🍪"), ("bolacha", "🍪"),
    ("chokito", "🍫"), ("trento", "🍫"), ("bom bom", "🍬"),
    ("emilia", "🍪"), ("suspiro", "🍥"),
    ("pão de mel", "🍯"), ("pao de mel", "🍯"),
    ("cocada", "🥥"), ("cajuzinho", "🥜"),
    ("geladão", "🍨"), ("geladao", "🍨"), ("cremosinho", "🍦"),
    ("copinho", "🍌"), ("doce em massa", "🍠"),
    ("doce", "🍬"),
    ("trident", "🍬"), ("halls", "🍬"), ("menta", "🌿"),
    ("cup noodles", "🍜"), ("noodles", "🍜"),
]

CATEGORY_ICONS = {
    "Bebidas": "🥤", "Salgados": "🥟", "Doces": "🍬",
    "Cup Noodles": "🍜", "Biscoitos": "🍪", "Chicletes": "🍬",
}


def icon_for(name: str, category: str = "") -> str:
    low = name.lower()
    for key, icon in ICON_RULES:
        if key in low:
            return icon
    return CATEGORY_ICONS.get(category, "🍴")