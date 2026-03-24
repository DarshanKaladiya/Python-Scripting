# Comprehensive Crop Intelligence Mapping for Indian Agriculture
CROP_METADATA = {
    "Rice": {
        "scientific_name": "Oryza sativa L.",
        "duration": 150,
        "season": "Kharif",
        "temp": "21-37°C",
        "soil": "Clayey to clay loam"
    },
    "Paddy": {
        "scientific_name": "Oryza sativa L.",
        "duration": 150,
        "season": "Kharif",
        "temp": "21-37°C",
        "soil": "Clayey to clay loam"
    },
    "Wheat": {
        "scientific_name": "Triticum aestivum",
        "duration": 120,
        "season": "Rabi",
        "temp": "10-26°C",
        "soil": "Well-drained fertile loamy"
    },
    "Mango": {
        "scientific_name": "Mangifera indica",
        "duration": 365,
        "season": "Perennial",
        "temp": "24-30°C",
        "soil": "Well-drained deep loamy"
    },
    "Banana": {
        "scientific_name": "Musa spp.",
        "duration": 365,
        "season": "Perennial",
        "temp": "20-35°C",
        "soil": "Moist fertile loamy"
    },
    "Potato": {
        "scientific_name": "Solanum tuberosum",
        "duration": 100,
        "season": "Rabi",
        "temp": "15-20°C",
        "soil": "Loose fertile loamy"
    },
    "Tomato": {
        "scientific_name": "Solanum lycopersicum",
        "duration": 110,
        "season": "Kharif",
        "temp": "20-30°C",
        "soil": "Rich well-drained loamy"
    },
    "Onion": {
        "scientific_name": "Allium cepa",
        "duration": 120,
        "season": "Rabi",
        "temp": "15-25°C",
        "soil": "Sandy loam with organic matter"
    },
    "Arhar": {
        "scientific_name": "Cajanus cajan",
        "duration": 180,
        "season": "Kharif",
        "temp": "25-35°C",
        "soil": "Deep alluvial or black"
    },
    "Mustard": {
        "scientific_name": "Brassica juncea",
        "duration": 110,
        "season": "Rabi",
        "temp": "10-20°C",
        "soil": "Sandy loam to heavy loam"
    },
    "Soybean": {
        "scientific_name": "Glycine max",
        "duration": 100,
        "season": "Kharif",
        "temp": "20-35°C",
        "soil": "Well-drained fertile clay"
    },
    "Tur": {
        "scientific_name": "Cajanus cajan",
        "duration": 180,
        "season": "Kharif",
        "temp": "25-35°C",
        "soil": "Deep alluvial or black"
    },
    "Gram": {
        "scientific_name": "Cicer arietinum L.",
        "duration": 130,
        "season": "Rabi",
        "temp": "20-25°C",
        "soil": "Well-drained medium-heavy"
    },
    "Moong": {
        "scientific_name": "Vigna radiata",
        "duration": 75,
        "season": "Kharif",
        "temp": "25-35°C",
        "soil": "Well-drained loamy"
    },
    "Urad": {
        "scientific_name": "Vigna mungo",
        "duration": 80,
        "season": "Kharif",
        "temp": "25-35°C",
        "soil": "Heavier soils"
    },
    "Cabbage": {
        "scientific_name": "Brassica oleracea",
        "duration": 100,
        "season": "Rabi",
        "temp": "15-20°C",
        "soil": "Heavy moisture-retentive"
    },
    "Brinjal": {
        "scientific_name": "Solanum melongena",
        "duration": 120,
        "season": "Kharif",
        "temp": "20-30°C",
        "soil": "Rich fertile loamy"
    },
    "Chilli": {
        "scientific_name": "Capsicum annuum",
        "duration": 150,
        "season": "Kharif",
        "temp": "20-30°C",
        "soil": "Well-drained loamy"
    },
    "Ginger": {
        "scientific_name": "Zingiber officinale",
        "duration": 240,
        "season": "Perennial",
        "temp": "20-30°C",
        "soil": "Well-drained sandy/clayey loam"
    },
    "Garlic": {
        "scientific_name": "Allium sativum",
        "duration": 150,
        "season": "Rabi",
        "temp": "12-24°C",
        "soil": "Rich loamy with organic matter"
    },
    "Turmeric": {
        "scientific_name": "Curcuma longa L.",
        "duration": 210,
        "season": "Perennial",
        "temp": "20-30°C",
        "soil": "Loamy or alluvial"
    },
    "Cotton": {
        "scientific_name": "Gossypium spp.",
        "duration": 180,
        "season": "Kharif",
        "temp": "21-30°C",
        "soil": "Deep black soils"
    },
    "Sugarcane": {
        "scientific_name": "Saccharum officinarum",
        "duration": 360,
        "season": "Perennial",
        "temp": "21-27°C",
        "soil": "Deep rich loamy"
    },
    "Litchi": {
        "scientific_name": "Litchi chinensis",
        "duration": 365,
        "season": "Perennial",
        "temp": "15-30°C",
        "soil": "Deep, well-drained loamy"
    },
    "Sapota": {
        "scientific_name": "Manilkara zapota",
        "duration": 365,
        "season": "Perennial",
        "temp": "11-34°C",
        "soil": "Alluvial, sandy loam or red"
    },
    "Soursop": {
        "scientific_name": "Annona muricata",
        "duration": 365,
        "season": "Perennial",
        "temp": "25-30°C",
        "soil": "Well-drained, sandy to loamy"
    }
}

def get_crop_enrichment(name):
    """Fuzzy match crop name to get enriched metadata"""
    name_clean = name.lower()
    for key, data in CROP_METADATA.items():
        if key.lower() in name_clean:
            return data
    
    # Defaults for unknown crops based on general category if we had it here
    return {
        "scientific_name": None,
        "duration": None,
        "season": "Varies",
        "temp": "15-35°C",
        "soil": "Mixed soil types"
    }
