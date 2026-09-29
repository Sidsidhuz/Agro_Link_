"""Reviewed disease guidance. Never derive a treatment from a model label alone."""
KAU_SOURCE = "https://kau.in/sites/default/files/documents/pop2016.pdf"
GUIDANCE = {
    ("Banana", "sigatoka"): {
        "title": "Sigatoka leaf spot",
        "steps": [
            "Remove severely affected leaves and dispose of them safely.",
            "KAU's Package of Practices describes a 1% Bordeaux mixture with sticker after initial symptoms. Read the source and consult a local agricultural officer before applying any product.",
        ],
        "source": KAU_SOURCE,
        "section": "Banana — Sigatoka leaf spot, plant protection",
        "status": "source_matched",
    },
}


def for_result(crop, prediction):
    if "healthy" in prediction.lower():
        return {"status": "healthy", "title": "No disease detected", "steps": ["Keep monitoring the crop. An image result does not replace field inspection."], "source": None}
    return GUIDANCE.get((crop, prediction), {
        "status": "unverified", "title": "A matching KAU treatment has not been verified",
        "steps": ["Avoid applying a treatment based only on the image result. Ask your local Krishi Bhavan or agricultural officer to confirm the disease."],
        "source": KAU_SOURCE,
    })
