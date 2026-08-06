# Fixtures — SYNTHETIC, NOT CAPTURED

Every record in this directory was hand-authored to match the *documented field shapes* of the
real feeds. None of it was captured from them, because this build environment cannot reach
`api.fda.gov`, `www.fda.gov`, or `www.fsis.usda.gov` — the egress policy blocks all three.

Field names follow openFDA's food enforcement endpoint (`recall_number`, `product_description`,
`reason_for_recall`, `classification`, `code_info`, `recalling_firm`, `report_date`) and FSIS's
recall summaries, confirmed via documentation. The *values* are invented.

**Replacing these with real captures is item 1 of `VERIFY.md`.** Until that happens, the matcher's
measured precision is a statement about this synthetic set, not about the real world.
