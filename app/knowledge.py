"""Indicative agronomy data for the prototype. Values are SAMPLE estimates, not official
figures. Validate with TNAU / ICAR / the local agriculture officer before real use."""
ROLES = ("farmer", "consumer", "bulk_buyer", "service_provider")
SOILS = ("red", "black", "alluvial", "sandy", "loamy", "clay")
WATER = ("low", "medium", "high")
SEASONS = ("kharif", "rabi", "summer", "perennial")
# district -> (typical soil, typical water availability) -- indicative defaults only
DISTRICTS = {"Coimbatore": ("red", "medium"), "Thanjavur": ("alluvial", "high"), "Madurai": ("black", "medium"),
             "Salem": ("red", "medium"), "Erode": ("red", "medium"), "Tirunelveli": ("black", "medium"),
             "Thoothukudi": ("sandy", "low"), "Kanyakumari": ("loamy", "high"), "Nagapattinam": ("alluvial", "high"),
             "Dindigul": ("red", "low"), "Tiruppur": ("red", "medium"), "Villupuram": ("red", "low")}


def _c(ta, seasons, soils, water, days, cost, yq, price, sp, pc, unit="qtl", peak=(), low=()):
    return dict(ta=ta, seasons=seasons, soils=soils, water=water, days=days, cost=cost, yield_=yq, price=price,
                spacing=sp, plant_cost=pc, unit=unit, peak=peak, low=low)


# cost = Rs/acre, yield = per acre, price = Rs per unit, spacing = (x m, y m), plant_cost = Rs per plant/seed unit
CROPS = {
    "paddy": _c("நெல்", ("kharif", "rabi"), ("alluvial", "clay", "loamy"), "high", 130, 28000, (20, 26), 2200, (0.2, 0.2), 0.1, peak=(2, 3, 9), low=(11, 12)),
    "groundnut": _c("நிலக்கடலை", ("kharif", "rabi"), ("red", "sandy", "loamy"), "medium", 105, 24000, (6, 9), 6000, (0.3, 0.1), 0.3, peak=(5, 6), low=(10, 11)),
    "maize": _c("மக்காச்சோளம்", ("kharif", "rabi"), ("loamy", "red", "alluvial"), "medium", 110, 22000, (22, 28), 2100, (0.6, 0.2), 0.4, peak=(6, 7), low=(1, 2)),
    "cotton": _c("பருத்தி", ("kharif",), ("black", "red"), "medium", 170, 32000, (6, 9), 6500, (0.9, 0.6), 1.0, peak=(2, 3), low=(11, 12)),
    "sugarcane": _c("கரும்பு", ("kharif", "rabi"), ("alluvial", "loamy", "black"), "high", 330, 70000, (300, 400), 330, (1.2, 0.6), 4.0, peak=(1, 2), low=(7, 8)),
    "banana": _c("வாழை", ("perennial",), ("alluvial", "loamy"), "high", 330, 90000, (200, 280), 1500, (1.8, 1.8), 15, peak=(3, 4, 10), low=(7, 8)),
    "tomato": _c("தக்காளி", ("rabi", "summer"), ("loamy", "red", "sandy"), "medium", 120, 60000, (100, 160), 1500, (0.9, 0.5), 2.0, peak=(3, 4, 10), low=(1, 2, 11)),
    "onion": _c("வெங்காயம்", ("rabi",), ("loamy", "red"), "medium", 110, 45000, (60, 90), 1800, (0.15, 0.1), 0.5, peak=(8, 9, 10), low=(3, 4)),
    "turmeric": _c("மஞ்சள்", ("kharif",), ("loamy", "red", "alluvial"), "medium", 270, 80000, (20, 28), 9000, (0.45, 0.2), 4.0, peak=(3, 4), low=(1, 12)),
    "ginger": _c("இஞ்சி", ("kharif",), ("loamy", "red"), "medium", 240, 120000, (60, 80), 4000, (0.4, 0.25), 5.0, peak=(11, 12), low=(5, 6)),
    "coconut": _c("தென்னை", ("perennial",), ("sandy", "loamy", "alluvial", "red"), "medium", 365, 15000, (7, 9), 12000, (7.5, 7.5), 60, unit="1000 nuts", peak=(4, 5), low=(10, 11)),
    "ragi": _c("கேழ்வரகு", ("kharif",), ("red", "sandy", "loamy"), "low", 110, 15000, (8, 12), 3800, (0.25, 0.1), 0.1, peak=(1, 2), low=(8, 9)),
    "blackgram": _c("உளுந்து", ("kharif", "rabi"), ("loamy", "black", "red"), "low", 75, 12000, (3, 5), 7000, (0.3, 0.1), 0.2, peak=(3, 4), low=(10, 11)),
}
# main crop -> compatible intercrops (indicative; confirm with local agriculture officer)
INTERCROP = {"coconut": ["turmeric", "ginger", "onion", "blackgram"], "banana": ["turmeric", "onion", "blackgram"],
             "sugarcane": ["onion", "blackgram"], "cotton": ["blackgram"], "maize": ["blackgram"], "tomato": ["onion"],
             "groundnut": ["ragi"]}
SYMPTOMS = ("brown spots", "yellowing", "white powder", "orange pustules", "water-soaked lesions", "wilting",
            "dark spots", "purple blotches", "leaf streaks", "curling or drying")
_T = "Remove badly affected leaves/plants, avoid overhead irrigation, and use a fungicide/pesticide only as per label and local agriculture officer advice."
_P = "Use healthy seed, rotate crops, keep field clean and well drained, scout weekly."
DISEASES = [
    dict(id="early_blight", name="Early blight", crops=("tomato",), sym=("brown spots", "yellowing", "dark spots"), col=("brown", "yellow"), treat=_T, prevent=_P),
    dict(id="late_blight", name="Late blight", crops=("tomato",), sym=("water-soaked lesions", "dark spots", "wilting"), col=("dark", "brown"), treat=_T, prevent=_P),
    dict(id="tikka_leaf_spot", name="Tikka leaf spot", crops=("groundnut",), sym=("brown spots", "dark spots", "yellowing"), col=("brown", "dark", "yellow"), treat=_T, prevent=_P),
    dict(id="rust", name="Rust", crops=("groundnut", "maize", "ragi"), sym=("orange pustules", "brown spots"), col=("orange", "brown"), treat=_T, prevent=_P),
    dict(id="blast", name="Blast", crops=("paddy", "ragi"), sym=("brown spots", "leaf streaks", "curling or drying"), col=("brown",), treat=_T, prevent=_P),
    dict(id="bacterial_blight", name="Bacterial blight", crops=("paddy", "cotton"), sym=("water-soaked lesions", "yellowing", "leaf streaks"), col=("yellow",), treat=_T, prevent=_P),
    dict(id="powdery_mildew", name="Powdery mildew", crops=("blackgram", "tomato", "onion"), sym=("white powder",), col=("white",), treat=_T, prevent=_P),
    dict(id="yellow_mosaic", name="Yellow mosaic (viral)", crops=("blackgram",), sym=("yellowing", "curling or drying"), col=("yellow",), treat="Virus has no cure: rogue out infected plants and manage whitefly vectors as advised locally.", prevent="Use resistant varieties and healthy seed; control weeds."),
    dict(id="purple_blotch", name="Purple blotch", crops=("onion",), sym=("purple blotches", "dark spots"), col=("dark", "brown"), treat=_T, prevent=_P),
    dict(id="sigatoka", name="Sigatoka leaf spot", crops=("banana",), sym=("leaf streaks", "brown spots", "yellowing"), col=("brown", "yellow"), treat=_T, prevent=_P),
    dict(id="root_wilt", name="Root (wilt) disease", crops=("coconut",), sym=("yellowing", "wilting", "curling or drying"), col=("yellow",), treat="No quick cure: improve nutrition and drainage and consult the local agriculture officer.", prevent="Balanced nutrition, good drainage, remove severely affected palms."),
    dict(id="rhizome_rot", name="Rhizome rot", crops=("turmeric", "ginger"), sym=("yellowing", "wilting", "curling or drying"), col=("yellow",), treat=_T, prevent="Use disease-free rhizomes, well-drained beds, crop rotation."),
    dict(id="red_rot", name="Red rot", crops=("sugarcane",), sym=("leaf streaks", "wilting", "curling or drying"), col=("brown", "orange"), treat="Remove and destroy affected clumps; consult the local agriculture officer.", prevent="Use disease-free setts and resistant varieties."),
    dict(id="leaf_curl", name="Leaf curl (viral)", crops=("cotton",), sym=("curling or drying", "yellowing"), col=("yellow",), treat="Manage whitefly vectors as advised locally; remove infected plants.", prevent="Use tolerant varieties; control weeds."),
    dict(id="leaf_blight", name="Leaf blight", crops=("maize",), sym=("brown spots", "leaf streaks"), col=("brown",), treat=_T, prevent=_P),
]
