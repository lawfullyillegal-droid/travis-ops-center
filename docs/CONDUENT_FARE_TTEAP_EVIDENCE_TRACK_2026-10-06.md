# Conduent / FARE / TTEAP Evidence Track

Updated: 2026-10-06

## Executive assessment

The defensible proposition is that **Conduent is documented in Arizona's statewide FARE technical/program architecture**. Arizona Judicial Branch materials describe FARE as a public/private program, current technical specifications explicitly reference Conduent, and the CCR specification documents transactions for notices, TTEAP status, special-collections status, addresses, and MVD TTEAP hold-request rejections.

That does **not**, by itself, establish that Conduent caused, mishandled, or unlawfully processed a particular CaseOps matter. The case-specific vendor transaction and audit records must be obtained before making that claim.

## Documented statewide chain

Court/CMS → AOC/CCR/FARE → FARE collection vendor / Conduent → TTEAP/MVD → status/rejection/address/notice feedback to court.

## Official Arizona Judicial Branch sources

- FARE: https://www.azcourts.gov/courtservices/Consolidated-Collections-Unit/FARE
- TTEAP: https://www.azcourts.gov/courtservices/Consolidated-Collections-Unit/Traffic-Ticket-Enforcement-Assistance-Program-TTEAP
- CCR Master Data Integration Design Specification: https://www.azcourts.gov/Portals/0/CCRMasterIntegrationDesignSpecificationVer4_1_4.pdf
- Court Implementations and Projects: https://www.azcourts.gov/courtservices/Consolidated-Collections-Unit/Court-Implementations-and-Projects
- Procurement / RFP 25-01 FARE Program: https://www.azcourts.gov/adminservices/Procurement.aspx

## Transaction-level targets

The current CCR specification supports requesting:

- `fr_evnts` — notice number/date/type/balance, TTEAP MVD status, special-collections status
- `fr_party.sp_coll_flg` — including Enhanced FARE processing status
- `fr_party.tteap_flg` — TTEAP state
- `frcore_paddr` — collection-vendor address updates and address flags
- `fr_rjcts` — MVD TTEAP hold-request rejection records
- complete FARE/CCR audit timestamps and actor/system identifiers
- records establishing the collection attempts relied upon before TTEAP
- recall, release, waiver, contract and subsequent status history

## CaseOps chronology to reconcile

| Date | Recorded event | Evidence needed |
|---|---|---|
| 2025-08-01 | Enhanced FARE referral | FARE status + special-collections flag history |
| 2025-09-24 | TTEAP activity | eligibility, request timestamp, MVD response, match basis |
| 2025-09-25 | TTEAP notice | notice number/type/date/balance, address used, prior attempt(s) |
| 2025-09-26 | mail returned undelivered | bad-address flag, address update/skip trace, re-noticing, downstream action |

## Presentation rule

Use this formulation:

> The Arizona Judicial Branch's own records document Conduent within the statewide FARE technical/program infrastructure. The open evidentiary question is whether the required notice, eligibility, address, and MVD transaction steps were correctly performed in this specific matter.

Do not state as established fact that Conduent caused or unlawfully imposed a case-specific hold unless the underlying transaction/audit records prove it.
