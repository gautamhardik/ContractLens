"""Adversarial Benchmark Dataset for ContractLens (Phase 22).

60 stress-testing queries across 6 failure-mode categories:
1. ROLE_COLLISION (10 queries): Testing supplier ≠ manufacturer, vendor ≠ service provider, customer ≠ reseller, buyer ≠ customer.
2. UNANCHORED_TEMPORAL (10 queries): Relative offsets where trigger event never occurred, non-existent calendar milestones.
3. UNSUPPORTED_FACT_TRAP (10 queries): Non-existent GDPR fines, fictitious arbitration venues, fictitious clauses.
4. NUMERICAL_TRAP (10 queries): Misleading numbers, wrong insurance limits ($5M vs $2M), wrong payment windows (Net 45 vs Net 60).
5. AMENDMENT_SUPERSEDING (10 queries): "Did amendment cancel entire agreement?", unamended confidentiality, preserved terms.
6. CROSS_CONTRACT_DISTRACTOR (10 queries): Parties from contract A queried against contract B (e.g., Square inside AMX).
"""

from typing import List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class AdversarialCategory(str, Enum):
    ROLE_COLLISION = "ROLE_COLLISION"
    UNANCHORED_TEMPORAL = "UNANCHORED_TEMPORAL"
    UNSUPPORTED_FACT_TRAP = "UNSUPPORTED_FACT_TRAP"
    NUMERICAL_TRAP = "NUMERICAL_TRAP"
    AMENDMENT_SUPERSEDING = "AMENDMENT_SUPERSEDING"
    CROSS_CONTRACT_DISTRACTOR = "CROSS_CONTRACT_DISTRACTOR"


class AdversarialBenchmarkQuery(BaseModel):
    id: str
    category: AdversarialCategory
    query: str
    target_documents: List[str]
    is_answerable: bool
    expected_behavior: str
    key_terms: List[str] = Field(default_factory=list)


def get_adversarial_dataset() -> List[AdversarialBenchmarkQuery]:
    return [
        # =========================================================================
        # 1. ROLE_COLLISION (10 Queries)
        # =========================================================================
        AdversarialBenchmarkQuery(
            id="adv_role_01",
            category=AdversarialCategory.ROLE_COLLISION,
            query="What are the manufacturer's obligations under the Turtle Beach-Foxconn agreement?",
            target_documents=["doc_17"],
            is_answerable=True,
            expected_behavior="Resolve Foxconn as manufacturer / service provider without confusing with Turtle Beach.",
            key_terms=["Foxconn", "manufacturer"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_role_02",
            category=AdversarialCategory.ROLE_COLLISION,
            query="What obligations does Turtle Beach have as the buyer versus Foxconn as the manufacturer?",
            target_documents=["doc_17"],
            is_answerable=True,
            expected_behavior="Distinguish buyer obligations (payment/forecast) from manufacturer obligations (manufacturing/delivery).",
            key_terms=["Turtle Beach", "Foxconn"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_role_03",
            category=AdversarialCategory.ROLE_COLLISION,
            query="Does Best Circuit Boards have customer obligations under the AMX agreement?",
            target_documents=["doc_01"],
            is_answerable=False,
            expected_behavior="Safely reject or clarify: Best Circuit Boards is the supplier/seller, not customer.",
            key_terms=["supplier", "seller", "not customer"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_role_04",
            category=AdversarialCategory.ROLE_COLLISION,
            query="What are AMX's obligations as the supplier under the Supply Agreement?",
            target_documents=["doc_01"],
            is_answerable=False,
            expected_behavior="Safely reject or clarify: AMX is the buyer/customer, not supplier.",
            key_terms=["buyer", "customer", "not supplier"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_role_05",
            category=AdversarialCategory.ROLE_COLLISION,
            query="What are the licensor obligations under the Access-E*TRADE Master Services Agreement?",
            target_documents=["doc_03"],
            is_answerable=False,
            expected_behavior="Contract is a services agreement between Access (service provider/contractor) and E*TRADE (client), not an exclusive IP license agreement.",
            key_terms=["services agreement", "contractor", "client"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_role_06",
            category=AdversarialCategory.ROLE_COLLISION,
            query="What duties does the service provider have under the Access-E*TRADE agreement?",
            target_documents=["doc_03"],
            is_answerable=True,
            expected_behavior="Resolve service provider to Access Integrated Information Management.",
            key_terms=["Access", "services"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_role_07",
            category=AdversarialCategory.ROLE_COLLISION,
            query="What responsibilities does the client have in the Access agreement?",
            target_documents=["doc_03"],
            is_answerable=True,
            expected_behavior="Resolve client to E*TRADE Financial Corporation.",
            key_terms=["E*TRADE", "payment", "cooperation"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_role_08",
            category=AdversarialCategory.ROLE_COLLISION,
            query="Is Foxconn designated as a reseller in the Foxconn-Turtle Beach contract?",
            target_documents=["doc_17"],
            is_answerable=False,
            expected_behavior="Safely confirm Foxconn is manufacturer/supplier, not reseller.",
            key_terms=["manufacturer", "not reseller"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_role_09",
            category=AdversarialCategory.ROLE_COLLISION,
            query="What obligations does the vendor have under the AMX agreement?",
            target_documents=["doc_01"],
            is_answerable=True,
            expected_behavior="Resolve vendor to Best Circuit Boards, Inc. and return supply/delivery obligations.",
            key_terms=["Best Circuit Boards", "supply", "delivery"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_role_10",
            category=AdversarialCategory.ROLE_COLLISION,
            query="What are the licensee duties under the Marqeta-Square agreement?",
            target_documents=["doc_16"],
            is_answerable=False,
            expected_behavior="Marqeta-Square agreement is an outsourced payment processing agreement, not a software license.",
            key_terms=["payment processing", "processing services"]
        ),

        # =========================================================================
        # 2. UNANCHORED_TEMPORAL (10 Queries)
        # =========================================================================
        AdversarialBenchmarkQuery(
            id="adv_temp_01",
            category=AdversarialCategory.UNANCHORED_TEMPORAL,
            query="On what exact calendar date must the cure period for default end under the AMX agreement?",
            target_documents=["doc_01"],
            is_answerable=False,
            expected_behavior="Safely explain 30-day cure period from notice of breach, but specific date is unanchored without notice.",
            key_terms=["30 days", "unanchored", "notice of default"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_temp_02",
            category=AdversarialCategory.UNANCHORED_TEMPORAL,
            query="When does the warranty expire for products delivered on October 14, 2029 under AMX?",
            target_documents=["doc_01"],
            is_answerable=False,
            expected_behavior="Fictitious future delivery date not grounded in contract; state contract specifies warranty period (e.g. 1 year) but no such delivery event is recorded.",
            key_terms=["unrecorded delivery", "warranty period"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_temp_03",
            category=AdversarialCategory.UNANCHORED_TEMPORAL,
            query="What is the exact deadline date for Foxconn to deliver the first batch of prototypes?",
            target_documents=["doc_17"],
            is_answerable=False,
            expected_behavior="Deliveries are governed by purchase orders or schedules; exact calendar deadline is unanchored in master text.",
            key_terms=["purchase orders", "unanchored", "statement of work"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_temp_04",
            category=AdversarialCategory.UNANCHORED_TEMPORAL,
            query="What calendar day does the 60-day non-renewal notice take effect for Access-E*TRADE in 2025?",
            target_documents=["doc_03"],
            is_answerable=False,
            expected_behavior="Agreement term was 2008-2010 (extended to 2011 by amendment); no 2025 term exists in contract evidence.",
            key_terms=["expired", "2011", "no 2025 term"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_temp_05",
            category=AdversarialCategory.UNANCHORED_TEMPORAL,
            query="How many days after breach must Foxconn notify Turtle Beach of force majeure?",
            target_documents=["doc_17"],
            is_answerable=True,
            expected_behavior="Extract prompt notice / reasonable time requirement from force majeure clause.",
            key_terms=["prompt", "notice", "force majeure"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_temp_06",
            category=AdversarialCategory.UNANCHORED_TEMPORAL,
            query="What is the specific calendar date of final payment under the Access MSA?",
            target_documents=["doc_03"],
            is_answerable=False,
            expected_behavior="Payment is Net 30 (Net 60 per amendment) from invoice receipt; exact calendar date requires ungrounded invoice date.",
            key_terms=["Net 30", "Net 60", "invoice date", "unanchored"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_temp_07",
            category=AdversarialCategory.UNANCHORED_TEMPORAL,
            query="When was the closing date of the merger mentioned in the Marqeta agreement?",
            target_documents=["doc_16"],
            is_answerable=False,
            expected_behavior="No merger closing date exists in the processing agreement text.",
            key_terms=["not found", "unsupported", "no merger"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_temp_08",
            category=AdversarialCategory.UNANCHORED_TEMPORAL,
            query="What is the notice period for terminating for convenience under the Access-E*TRADE MSA?",
            target_documents=["doc_03"],
            is_answerable=True,
            expected_behavior="Identify termination notice requirement (30 days prior written notice).",
            key_terms=["30 days", "written notice", "Section 3"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_temp_09",
            category=AdversarialCategory.UNANCHORED_TEMPORAL,
            query="What is the delivery lead time specified in days under the AMX Supply Agreement?",
            target_documents=["doc_01"],
            is_answerable=True,
            expected_behavior="Extract lead time or purchase order delivery requirements.",
            key_terms=["days", "lead time", "purchase order"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_temp_08_b",
            category=AdversarialCategory.UNANCHORED_TEMPORAL,
            query="On what date did E*TRADE cure its payment default in 2012?",
            target_documents=["doc_02", "doc_03"],
            is_answerable=False,
            expected_behavior="No default or cure event in 2012 exists in contract record; safely report unanswerable.",
            key_terms=["no default event", "unsupported"]
        ),

        # =========================================================================
        # 3. UNSUPPORTED_FACT_TRAP (10 Queries)
        # =========================================================================
        AdversarialBenchmarkQuery(
            id="adv_fact_01",
            category=AdversarialCategory.UNSUPPORTED_FACT_TRAP,
            query="What GDPR penalty amount is specified in the AMX-Best Circuit Boards agreement?",
            target_documents=["doc_01"],
            is_answerable=False,
            expected_behavior="Contract dated 2006 contains no GDPR clauses or GDPR penalty provisions.",
            key_terms=["no GDPR", "not found", "2006"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_fact_02",
            category=AdversarialCategory.UNSUPPORTED_FACT_TRAP,
            query="Which London arbitration institution handles disputes under the Access-E*TRADE MSA?",
            target_documents=["doc_03"],
            is_answerable=False,
            expected_behavior="Disputes are governed by Delaware state law and courts, not London arbitration.",
            key_terms=["Delaware", "no London arbitration"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_fact_03",
            category=AdversarialCategory.UNSUPPORTED_FACT_TRAP,
            query="What are the liquidated damages for delayed shipment under the Turtle Beach agreement?",
            target_documents=["doc_17"],
            is_answerable=False,
            expected_behavior="Contract contains no liquidated damages clause; safely decline to fabricate.",
            key_terms=["no liquidated damages", "unsupported"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_fact_04",
            category=AdversarialCategory.UNSUPPORTED_FACT_TRAP,
            query="What is the 2024 Amendment terms for Access-E*TRADE?",
            target_documents=["doc_02", "doc_03"],
            is_answerable=False,
            expected_behavior="Corpus only contains Amendment No. 1 dated October 1, 2010; no 2024 amendment exists.",
            key_terms=["no 2024 amendment", "October 1, 2010"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_fact_05",
            category=AdversarialCategory.UNSUPPORTED_FACT_TRAP,
            query="What is the parent guarantee provided by Foxconn's parent company Hon Hai?",
            target_documents=["doc_17"],
            is_answerable=False,
            expected_behavior="No parent guarantee from Hon Hai is specified in the agreement text.",
            key_terms=["not found", "no parent guarantee"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_fact_06",
            category=AdversarialCategory.UNSUPPORTED_FACT_TRAP,
            query="What is the annual software maintenance fee in the AMX agreement?",
            target_documents=["doc_01"],
            is_answerable=False,
            expected_behavior="AMX agreement is for circuit board hardware manufacturing, not software maintenance.",
            key_terms=["hardware", "circuit boards", "no software maintenance fee"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_fact_07",
            category=AdversarialCategory.UNSUPPORTED_FACT_TRAP,
            query="Which clause in the Access MSA requires payment in Bitcoin or cryptocurrency?",
            target_documents=["doc_03"],
            is_answerable=False,
            expected_behavior="Agreement requires payment in lawful money of the United States, no cryptocurrency provision.",
            key_terms=["US Dollars", "no cryptocurrency"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_fact_08",
            category=AdversarialCategory.UNSUPPORTED_FACT_TRAP,
            query="What is the non-compete restriction period preventing AMX from selling electronics?",
            target_documents=["doc_01"],
            is_answerable=False,
            expected_behavior="Agreement does not contain a non-compete preventing AMX from selling its products.",
            key_terms=["no non-compete", "unsupported"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_fact_09",
            category=AdversarialCategory.UNSUPPORTED_FACT_TRAP,
            query="What are the carbon emission reduction targets in the Foxconn MSA?",
            target_documents=["doc_17"],
            is_answerable=False,
            expected_behavior="Agreement contains no ESG or carbon emission reduction targets.",
            key_terms=["no carbon emission targets", "unsupported"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_fact_10",
            category=AdversarialCategory.UNSUPPORTED_FACT_TRAP,
            query="What is the penalty fee if E*TRADE hires an Access employee during the term?",
            target_documents=["doc_03"],
            is_answerable=False,
            expected_behavior="Section 18.2 addresses non-solicitation, but specifies no fixed liquidated penalty amount.",
            key_terms=["non-solicitation", "no liquidated penalty amount"]
        ),

        # =========================================================================
        # 4. NUMERICAL_TRAP (10 Queries)
        # =========================================================================
        AdversarialBenchmarkQuery(
            id="adv_num_01",
            category=AdversarialCategory.NUMERICAL_TRAP,
            query="Is the insurance requirement under Section 15.4 of Access-E*TRADE $5,000,000?",
            target_documents=["doc_02", "doc_03"],
            is_answerable=True,
            expected_behavior="Correct the trap: Original Section 15.4 requires $2,000,000 commercial general liability, and Amendment No. 1 added $1,000,000 Errors & Omissions, not $5,000,000.",
            key_terms=["$2,000,000", "$1,000,000", "not $5,000,000"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_num_02",
            category=AdversarialCategory.NUMERICAL_TRAP,
            query="What is the hourly fee under the amended Access agreement?",
            target_documents=["doc_02"],
            is_answerable=True,
            expected_behavior="Identify exact rate: $115.00 per hour (increased from $110.00).",
            key_terms=["$115", "hour"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_num_03",
            category=AdversarialCategory.NUMERICAL_TRAP,
            query="Are invoices payable within Net 45 days under the amended Access-E*TRADE agreement?",
            target_documents=["doc_02", "doc_03"],
            is_answerable=True,
            expected_behavior="Correct the trap: Section 6 was amended to Net 60 days, not Net 45 days (original was Net 30).",
            key_terms=["Net 60", "not Net 45", "Section 6"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_num_04",
            category=AdversarialCategory.NUMERICAL_TRAP,
            query="What is the termination notice period in Section 3 of the Access MSA?",
            target_documents=["doc_03"],
            is_answerable=True,
            expected_behavior="30 days written notice.",
            key_terms=["30 days", "Section 3"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_num_05",
            category=AdversarialCategory.NUMERICAL_TRAP,
            query="Does the Access amendment extend the term by 5 years?",
            target_documents=["doc_02", "doc_03"],
            is_answerable=True,
            expected_behavior="Correct the trap: Amendment extends term by 1 year (to September 30, 2011), not 5 years.",
            key_terms=["1 year", "September 30, 2011", "not 5 years"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_num_06",
            category=AdversarialCategory.NUMERICAL_TRAP,
            query="What is the interest rate charged on late payments under the Access MSA?",
            target_documents=["doc_03"],
            is_answerable=True,
            expected_behavior="Extract 1.5% per month or maximum permitted by law.",
            key_terms=["1.5%", "month", "late payment"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_num_07",
            category=AdversarialCategory.NUMERICAL_TRAP,
            query="What is the minimum aggregate liability cap under the AMX Supply Agreement?",
            target_documents=["doc_01"],
            is_answerable=True,
            expected_behavior="Identify limitation of liability clause details or state exact formula.",
            key_terms=["limitation of liability", "damages"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_num_08",
            category=AdversarialCategory.NUMERICAL_TRAP,
            query="Does Section 15.4 of the Access MSA require $10,000,000 in umbrella coverage?",
            target_documents=["doc_03"],
            is_answerable=True,
            expected_behavior="Correct the trap: Requires $5,000,000 umbrella coverage, not $10,000,000.",
            key_terms=["$5,000,000", "umbrella", "not $10,000,000"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_num_09",
            category=AdversarialCategory.NUMERICAL_TRAP,
            query="What was the original hourly rate before Amendment No. 1 in Access-E*TRADE?",
            target_documents=["doc_03"],
            is_answerable=True,
            expected_behavior="$110.00 per hour in Exhibit A.",
            key_terms=["$110", "hour"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_num_10",
            category=AdversarialCategory.NUMERICAL_TRAP,
            query="Is the cure period for material breach under AMX 90 days?",
            target_documents=["doc_01"],
            is_answerable=True,
            expected_behavior="Correct the trap: The cure period is 30 days, not 90 days.",
            key_terms=["30 days", "not 90 days"]
        ),

        # =========================================================================
        # 5. AMENDMENT_SUPERSEDING (10 Queries)
        # =========================================================================
        AdversarialBenchmarkQuery(
            id="adv_amend_01",
            category=AdversarialCategory.AMENDMENT_SUPERSEDING,
            query="Did Amendment No. 1 terminate or supersede the entire Access-E*TRADE Master Agreement?",
            target_documents=["doc_02", "doc_03"],
            is_answerable=True,
            expected_behavior="Confirm that Amendment No. 1 only modified specific sections (§1.2, §3, §6, §15.4) and all other terms remain in full force and effect.",
            key_terms=["full force and effect", "only modified specific sections", "did not terminate"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_amend_02",
            category=AdversarialCategory.AMENDMENT_SUPERSEDING,
            query="Which document governs the current hourly rate between Access and E*TRADE?",
            target_documents=["doc_02", "doc_03"],
            is_answerable=True,
            expected_behavior="Amendment No. 1 governs the hourly rate ($115/hr superseding original $110/hr).",
            key_terms=["Amendment No. 1", "$115", "supersedes"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_amend_03",
            category=AdversarialCategory.AMENDMENT_SUPERSEDING,
            query="Are the confidentiality provisions in Section 8 of the Access MSA still active after Amendment No. 1?",
            target_documents=["doc_02", "doc_03"],
            is_answerable=True,
            expected_behavior="Yes, Section 8 was not modified by Amendment No. 1 and remains in full force and effect.",
            key_terms=["still active", "full force and effect", "Section 8"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_amend_04",
            category=AdversarialCategory.AMENDMENT_SUPERSEDING,
            query="What payment terms apply to Access and E*TRADE today: Net 30 or Net 60?",
            target_documents=["doc_02", "doc_03"],
            is_answerable=True,
            expected_behavior="Net 60 applies; Amendment No. 1 superseded the original Net 30 term.",
            key_terms=["Net 60", "superseded Net 30"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_amend_05",
            category=AdversarialCategory.AMENDMENT_SUPERSEDING,
            query="Does the governing law of Access change from Delaware to New York under the Amendment?",
            target_documents=["doc_02", "doc_03"],
            is_answerable=True,
            expected_behavior="No, governing law remains State of Delaware under Section 18.4, unmodified by the amendment.",
            key_terms=["Delaware", "unmodified", "remains in force"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_amend_06",
            category=AdversarialCategory.AMENDMENT_SUPERSEDING,
            query="What sections of the Access MSA were modified by Amendment No. 1?",
            target_documents=["doc_02", "doc_03"],
            is_answerable=True,
            expected_behavior="Sections 1.2 (Price), 3 (Term), 6 (Payment Terms), and 15.4 (Insurance).",
            key_terms=["1.2", "3", "6", "15.4"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_amend_07",
            category=AdversarialCategory.AMENDMENT_SUPERSEDING,
            query="Did Amendment No. 1 remove the requirement for commercial general liability insurance?",
            target_documents=["doc_02", "doc_03"],
            is_answerable=True,
            expected_behavior="No, it added Errors & Omissions coverage ($1,000,000) while confirming existing insurance obligations.",
            key_terms=["did not remove", "added Errors & Omissions", "$1,000,000"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_amend_08",
            category=AdversarialCategory.AMENDMENT_SUPERSEDING,
            query="Is the expiration date of the Access agreement still September 30, 2010?",
            target_documents=["doc_02", "doc_03"],
            is_answerable=True,
            expected_behavior="No, Amendment No. 1 extended the term to September 30, 2011.",
            key_terms=["extended", "September 30, 2011", "not 2010"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_amend_09",
            category=AdversarialCategory.AMENDMENT_SUPERSEDING,
            query="What amendment exists in the corpus for the Turtle Beach-Foxconn agreement?",
            target_documents=["doc_17"],
            is_answerable=False,
            expected_behavior="No amendment for the Turtle Beach-Foxconn agreement is present in the repository.",
            key_terms=["no amendment", "unsupported"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_amend_10",
            category=AdversarialCategory.AMENDMENT_SUPERSEDING,
            query="Can E*TRADE rely on the $110 rate from the original MSA for invoices issued in 2011?",
            target_documents=["doc_02", "doc_03"],
            is_answerable=True,
            expected_behavior="No, Amendment No. 1 took effect October 1, 2010 and replaced the rate with $115/hr.",
            key_terms=["No", "$115", "October 1, 2010"]
        ),

        # =========================================================================
        # 6. CROSS_CONTRACT_DISTRACTOR (10 Queries)
        # =========================================================================
        AdversarialBenchmarkQuery(
            id="adv_cross_01",
            category=AdversarialCategory.CROSS_CONTRACT_DISTRACTOR,
            query="What are Foxconn's obligations under the AMX Supply Agreement?",
            target_documents=["doc_01"],
            is_answerable=False,
            expected_behavior="Foxconn is not a party to the AMX Supply Agreement (parties are AMX and Best Circuit Boards).",
            key_terms=["not a party", "AMX", "Best Circuit Boards"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_cross_02",
            category=AdversarialCategory.CROSS_CONTRACT_DISTRACTOR,
            query="Does E*TRADE have payment obligations under the Turtle Beach contract?",
            target_documents=["doc_17"],
            is_answerable=False,
            expected_behavior="E*TRADE is not a party to the Turtle Beach-Foxconn contract.",
            key_terms=["not a party", "Turtle Beach", "Foxconn"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_cross_03",
            category=AdversarialCategory.CROSS_CONTRACT_DISTRACTOR,
            query="What are Square's responsibilities in the Access-E*TRADE MSA?",
            target_documents=["doc_03"],
            is_answerable=False,
            expected_behavior="Square is not a party to the Access-E*TRADE MSA.",
            key_terms=["not a party", "Access", "E*TRADE"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_cross_04",
            category=AdversarialCategory.CROSS_CONTRACT_DISTRACTOR,
            query="Which contract governs both Best Circuit Boards and Foxconn together?",
            target_documents=["doc_01", "doc_17"],
            is_answerable=False,
            expected_behavior="No agreement links Best Circuit Boards and Foxconn together; they are suppliers in separate contracts.",
            key_terms=["no contract", "separate agreements"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_cross_05",
            category=AdversarialCategory.CROSS_CONTRACT_DISTRACTOR,
            query="What are Marqeta's obligations under the AMX agreement?",
            target_documents=["doc_01"],
            is_answerable=False,
            expected_behavior="Marqeta is not a party to the AMX agreement.",
            key_terms=["not a party", "AMX"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_cross_06",
            category=AdversarialCategory.CROSS_CONTRACT_DISTRACTOR,
            query="Which contracts in the corpus have Delaware governing law?",
            target_documents=["doc_01", "doc_02", "doc_03", "doc_16", "doc_17"],
            is_answerable=True,
            expected_behavior="Identify contracts governed by Delaware law (including Access-E*TRADE MSA and Amendment).",
            key_terms=["Delaware", "Access"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_cross_07",
            category=AdversarialCategory.CROSS_CONTRACT_DISTRACTOR,
            query="Does Best Circuit Boards provide card issuing services to Square?",
            target_documents=["doc_01", "doc_16"],
            is_answerable=False,
            expected_behavior="Best Circuit Boards manufactures circuit boards for AMX; it has no relationship or agreement with Square.",
            key_terms=["no relationship", "not a party"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_cross_08",
            category=AdversarialCategory.CROSS_CONTRACT_DISTRACTOR,
            query="What confidentiality obligations does Turtle Beach have toward E*TRADE?",
            target_documents=["doc_03", "doc_17"],
            is_answerable=False,
            expected_behavior="Turtle Beach and E*TRADE are unrelated parties with no contractual relationship in the corpus.",
            key_terms=["no contractual relationship", "unrelated"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_cross_09",
            category=AdversarialCategory.CROSS_CONTRACT_DISTRACTOR,
            query="Which contracts involve hardware manufacturing as opposed to software or data services?",
            target_documents=["doc_01", "doc_03", "doc_17"],
            is_answerable=True,
            expected_behavior="Differentiate AMX-Best Circuit Boards (circuit boards) and Turtle Beach-Foxconn (headset hardware) from Access-E*TRADE (data/records services).",
            key_terms=["AMX", "Turtle Beach", "hardware"]
        ),
        AdversarialBenchmarkQuery(
            id="adv_cross_10",
            category=AdversarialCategory.CROSS_CONTRACT_DISTRACTOR,
            query="What is the governing law of the Foxconn contract versus the Access contract?",
            target_documents=["doc_03", "doc_17"],
            is_answerable=True,
            expected_behavior="Contrast governing laws: Access is governed by Delaware law, while Turtle Beach-Foxconn is governed by California law.",
            key_terms=["Delaware", "California"]
        ),
    ]
