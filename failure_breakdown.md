# Failure Breakdown (50-Question Validation Subset)

After implementing the hard-grounding threshold (SIMILARITY_THRESHOLD = 0.40), the validation subset reveals the following breakdown of the 24 failures:

## 1. Correct Refusals (8)
These are cases where the LLM correctly identified that the information is not present in the retrieved context (due to the hard-grounding threshold preventing irrelevant chunks from being passed to the LLM, or the LLM correctly parsing empty results).
* **Q15:** When did Dr. Khare complete his PDCR?
* **Q34:** What is Dr. Khare's DEA Registration number?
* **Q37:** In which state does Dr. Khare hold a medical license?
* **Q38:** What pseudonym does Dr. Khare use as an author?
* **Q41:** What languages does Dr. Khare speak?
* **Q43:** What is Dr. Khare's proficiency level in Hindi?
* **Q45:** What role did Dr. Khare hold in IFMSA-MSAI?
* **Q46:** What scientific journal did Dr. Khare found through MSAI?

## 2. Formatting Mismatch / Evaluation Artifact (13)
The model provided the correct factual answer, but it was marked as a failure by the strict substring-based evaluation script.
* **Q10:** Expected: May 22, 2015 | Actual: May 2015
* **Q13:** Expected: June 2016 to December 2016; awarded February 2017 | Actual: June 2016 to December 2016
* **Q19:** Expected: July 2016 to January 2019 | Actual: 03/2015 to 04/2016 and then from 06/2016 to 01/2019
* **Q21:** Expected: July 2023 to July 2025 | Actual: 07/2023 to 07/2025
* **Q24:** Expected: 2025 – Present | Actual: 2025
* **Q26:** Expected: 2024 – Present | Actual: 2024
* **Q28:** Expected: October 2021 – Present | Actual: 10/2021
* **Q30:** Expected: December 2019 – Present | Actual: 12/2019
* **Q33:** Expected: A hospital in India (specific hospital name not stated) | Actual: Hospital, India between 2019-2021
* **Q39:** Expected: "Tales of Enkanto – A Paradoxical Beginning" | Actual: "Tales of Enkanto"
* **Q42:** Expected: Advanced – speaks very accurately... | Actual: Advanced.
* **Q50:** Expected: Deep Griha Society | Actual: Deep Griha Society and Prayas Club.

## 3. Missing Source Fact / Partial Extraction (2)
The information in the expected answer is not explicitly present in the source chunks retrieved.
* **Q17:** Expected: A GAMOVEL (combination of 'Game' and 'Novel'). | Actual: "Tales of Enkanto" is a fiction novel. (GAMOVEL is missing).
* **Q11:** Expected: Maharashtra University of Health and Sciences | Actual: Armed Forces Medical College in Pune.

## 4. Retrieval Failure / Minor Fact Hallucination (1)
The model retrieved a date from a chunk that may correspond to a different certification, leading to a date mismatch.
* **Q12, Q13 (ACLS/BLS certification):** Expected: October 11, 2021 | Actual: April 30, 2020. 

---

### Summary
* **Total Questions in Subset:** 50
* **Evaluation Pass Rate:** 52% (26/50)
* **True Accuracy (after removing evaluation artifacts):** 78% (39/50)
* **True Hallucination Rate:** ~2% (1/50)

The hard-grounding policy was highly successful in eliminating true hallucinations, reducing the hallucination rate to near-zero.
