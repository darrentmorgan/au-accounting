---
type: llm
criteria: |
  PASS if the answer says the supply is NOT GST-free as an export under s38-190(1) item 2: the recipient is a non-resident who is in Australia when the service is done, so the recipient test is failed, and the destination of the invoice or residence of the client does not change that. The fee is taxable (10% GST, i.e. $1,200 on $12,000 if the fee is GST-exclusive, or 1/11 if inclusive). It should treat any item 3 (effective use or enjoyment outside Australia) argument as also failing because the recipient is in Australia. It should suggest checking GSTR 2004/7 or confirming facts before finalising.
  FAIL if it accepts GST-free treatment, or bases GST-free on the service being consumed or used outside Australia without addressing that the recipient is in Australia.
focus: last_message
---

Judge the final answer against the criteria.
