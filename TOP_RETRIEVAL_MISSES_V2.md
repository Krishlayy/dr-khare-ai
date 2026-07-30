# Top Retrieval Misses V2

Due to the new hard metadata filtering logic, most retrieval misses stem from category misclassifications during querying.

## Top Misses

**1. Question:** "What professional certificate did Dr. Khare obtain from Catalyst Clinical?"
- **Classified Category:** `certification`
- **Expected Source:** `education_training.txt` or `employment.txt` (often listed there instead of standalone certifications).
- **Root Cause:** Hard filtering prevented searching across employment/education chunks, where the fact actually resides.

**2. Question:** "When did Dr. Khare complete his PCPV from Catalyst Clinical?"
- **Classified Category:** `employment`
- **Expected Source:** `certifications.txt` or `education_training.txt`.
- **Root Cause:** Mismatch between query keyword ("complete") routing it incorrectly and the fact's true location.

**3. Question:** "When did Dr. Khare complete his PDCR?"
- **Classified Category:** `None`
- **Expected Source:** `education_training.txt`
- **Root Cause:** A `None` classification defaults to a full database search. However, acronyms like PDCR may not match well semantically without BM25 picking them up heavily, or the confidence threshold of 0.40 rejected the found chunk.

**4. Question:** "Where did Dr. Khare complete his Internal Medicine residency?"
- **Classified Category:** `education`
- **Expected Source:** `employment.txt`
- **Root Cause:** Residency is frequently documented as employment experience in the CV, but the query routed to the `education` metadata tag.

## Recommendations
To resolve these, **Hard Metadata Filtering must be replaced with Soft Metadata Boosting**. The query classifier should attach a positive multiplier to the predicted category rather than excluding all other categories. This will allow cross-category retrieval while still prioritizing the likeliest domain.
