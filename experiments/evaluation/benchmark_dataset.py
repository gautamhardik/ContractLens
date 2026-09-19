"""Golden Benchmark Questions Dataset for ContractLens (Phase 10).

Constructs 40 rigorously curated questions across 8 legal and operational categories:
1. Metadata (5 questions)
2. Parties (5 questions)
3. Dates / Lifecycle (5 questions)
4. Payment & Pricing (5 questions)
5. Termination & Non-Renewal (5 questions)
6. Obligations & Covenants (5 questions)
7. Cross-Document / Portfolio (5 questions)
8. Version & Amendment Precedence (5 questions)

All key phrases are strictly anchored to verbatim contract text in the 18-PDF corpus.
"""

from typing import List
from experiments.evaluation.benchmark_schema import (
    BenchmarkQuestion,
    QuestionCategory,
    ReasoningType,
    DifficultyLevel,
    ExpectedEvidence,
)


def get_evaluation_dataset() -> List[BenchmarkQuestion]:
    return [
        # =========================================================================
        # 1. METADATA (5 Questions)
        # =========================================================================
        BenchmarkQuestion(
            question_id="Q01_meta_law_access",
            category=QuestionCategory.METADATA,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.EASY,
            target_documents=["doc_03"],
            question="What is the governing law of the Access-E*TRADE Master Services Agreement?",
            expected_answer="State of Delaware",
            acceptable_variants=["Delaware", "laws of the State of Delaware"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[12],
                    target_section="Section 18.4",
                    key_phrases=["laws of the State of Delaware", "agreements executed and to be performed"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q02_meta_law_sabre",
            category=QuestionCategory.METADATA,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.EASY,
            target_documents=["doc_10"],
            question="Which state's laws govern the Sabre-DXC Amended & Restated Agreement?",
            expected_answer="State of Texas",
            acceptable_variants=["Texas", "laws of Texas"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_10",
                    target_pages=[88],
                    target_section="Section 27.1",
                    key_phrases=["laws of the State of Texas", "choice-of-law"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q03_meta_term_amx",
            category=QuestionCategory.METADATA,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.EASY,
            target_documents=["doc_01"],
            question="How is the initial term and renewal structured in the AMX-Best Circuit Boards Supply Agreement?",
            expected_answer="Continues through the Original Termination Date on Exhibit A, with automatic renewals for successive two (2) year terms unless terminated at least thirty (30) days prior.",
            acceptable_variants=["Original Termination Date on Exhibit A with 2-year renewals", "Successive Two (2) year term renewals"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_01",
                    target_pages=[1],
                    target_section="Section 1.1 / 1.2",
                    key_phrases=["Original Termination Date as set forth on Exhibit A", "successive Two (2) year term"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q04_meta_order_precedence_access",
            category=QuestionCategory.METADATA,
            reasoning_type=ReasoningType.PARAPHRASED_LOOKUP,
            difficulty=DifficultyLevel.MEDIUM,
            target_documents=["doc_03"],
            question="If there is a conflict between the terms of a Scope of Work (SOW) and the Access-E*TRADE MSA, which document takes precedence?",
            expected_answer="The Agreement (MSA) takes precedence unless the Scope of Work explicitly states otherwise.",
            acceptable_variants=["The Agreement takes precedence", "The MSA", "Agreement terms govern over SOW"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[1],
                    target_section="Section 1.2",
                    key_phrases=["take precedence over any contrary or inconsistent", "Scope of Work explicitly states otherwise"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q05_meta_unanswerable_arbitration_seat",
            category=QuestionCategory.METADATA,
            reasoning_type=ReasoningType.UNANSWERABLE,
            difficulty=DifficultyLevel.HARD,
            target_documents=["doc_03"],
            question="What is the designated city for arbitration in the Access-E*TRADE MSA?",
            expected_answer="Insufficient evidence. The agreement does not specify an arbitration seat (disputes are submitted to courts of competent jurisdiction).",
            acceptable_variants=["No arbitration seat specified", "Agreement specifies court jurisdiction, not arbitration"],
            is_answerable=False,
            unanswerable_reason="The contract specifies judicial resolution in a court of competent jurisdiction located in the defendant's location, with no arbitration clause.",
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[12],
                    target_section="Section 18.4",
                    key_phrases=["court of competent jurisdiction", "personal jurisdiction and venue"]
                )
            ]
        ),

        # =========================================================================
        # 2. PARTIES (5 Questions)
        # =========================================================================
        BenchmarkQuestion(
            question_id="Q06_parties_access_identity",
            category=QuestionCategory.PARTIES,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.EASY,
            target_documents=["doc_03"],
            question="Who are the primary contracting parties in the Access-E*TRADE MSA?",
            expected_answer="Access Worldwide Communications, Inc. and E*TRADE Financial Corporation.",
            acceptable_variants=["Access Worldwide Communications and E*TRADE Financial", "Access and E*TRADE"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[1],
                    key_phrases=["Access Worldwide Communications, Inc.", "E*TRADE Financial Corporation"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q07_parties_marqeta_role",
            category=QuestionCategory.PARTIES,
            reasoning_type=ReasoningType.PARAPHRASED_LOOKUP,
            difficulty=DifficultyLevel.MEDIUM,
            target_documents=["doc_16"],
            question="Who are the contracting parties and what is Marqeta's role under the Agreement with Square?",
            expected_answer="Square, Inc. (Client) and Marqeta, Inc. (Processor providing program management and card processing services).",
            acceptable_variants=["Square and Marqeta", "Processor / Program Manager"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_16",
                    target_pages=[1],
                    key_phrases=["Square, Inc.", "Marqeta, Inc.", "Schedule A - Program Terms"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q08_parties_viac_nda",
            category=QuestionCategory.PARTIES,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.EASY,
            target_documents=["doc_18"],
            question="Who is the named investment entity entering into the 2025 VIAC Mutual Non-Disclosure Agreement?",
            expected_answer="Venerable Investment Advisers, LLC",
            acceptable_variants=["Venerable Investment Advisers", "VIAC"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_18",
                    target_pages=[1],
                    key_phrases=["Venerable Investment Advisers, LLC", "Venerable Variable Insurance Trust"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q09_parties_foxconn_turtle_beach",
            category=QuestionCategory.PARTIES,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.EASY,
            target_documents=["doc_17"],
            question="What corporate entities are named as Parties in the Turtle Beach MSA?",
            expected_answer="Turtle Beach Corporation ('TB') and Hon Hai Precision Industry Co. Ltd. ('Foxconn').",
            acceptable_variants=["Turtle Beach Corporation and Hon Hai Precision Industry Co. Ltd.", "Turtle Beach and Foxconn"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_17",
                    target_pages=[1],
                    key_phrases=["Turtle Beach Corporation", "Hon Hai Precision", "Foxconn"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q10_parties_unanswerable_guarantor",
            category=QuestionCategory.PARTIES,
            reasoning_type=ReasoningType.UNANSWERABLE,
            difficulty=DifficultyLevel.HARD,
            target_documents=["doc_01"],
            question="Who is the named parent guarantor for Best Circuit Boards in the AMX Supply Agreement?",
            expected_answer="Insufficient evidence. The agreement does not designate any parent guarantor.",
            acceptable_variants=["No parent guarantor is named or provided in the agreement"],
            is_answerable=False,
            unanswerable_reason="AMX, LLC and Best Circuit Boards, Inc. contract directly; no parent guarantee exists.",
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_01",
                    target_pages=[1],
                    key_phrases=["AMX, LLC", "Best Circuit Boards, Inc."]
                )
            ]
        ),

        # =========================================================================
        # 3. DATES / LIFECYCLE (5 Questions)
        # =========================================================================
        BenchmarkQuestion(
            question_id="Q11_date_effective_access_msa",
            category=QuestionCategory.DATES_LIFECYCLE,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.EASY,
            target_documents=["doc_03"],
            question="What is the effective date of the original Access-E*TRADE Master Services Agreement?",
            expected_answer="June 1, 2005",
            acceptable_variants=["June 1, 2005", "2005-06-01"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[1],
                    key_phrases=["effective June 1, 2005", "Effective Date"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q12_date_initial_expiration_access_msa",
            category=QuestionCategory.DATES_LIFECYCLE,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.MEDIUM,
            target_documents=["doc_03"],
            question="When was the Initial Term of the Access-E*TRADE MSA originally scheduled to terminate?",
            expected_answer="June 9, 2006 (twelve months later)",
            acceptable_variants=["June 9, 2006", "12 months later on June 9, 2006"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[2],
                    target_section="Section 3.1",
                    key_phrases=["June 9, 2006", "Initial Term"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q13_date_renewal_window_access",
            category=QuestionCategory.DATES_LIFECYCLE,
            reasoning_type=ReasoningType.TEMPORAL_REASONING,
            difficulty=DifficultyLevel.MEDIUM,
            target_documents=["doc_03"],
            question="How many days prior to expiration must a party give notice to prevent automatic renewal under the Access-E*TRADE MSA?",
            expected_answer="At least thirty (30) days prior to the expiration of the initial or any renewal term.",
            acceptable_variants=["30 days", "at least thirty days prior to expiration"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[2],
                    target_section="Section 3.1",
                    key_phrases=["intent not to", "at least thirty (30) days prior to the expiration"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q14_date_scyx_gsk_effective",
            category=QuestionCategory.DATES_LIFECYCLE,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.EASY,
            target_documents=["doc_09"],
            question="What is the effective date stated in the SCYNEXIS-GSK License Agreement?",
            expected_answer="March 30, 2023",
            acceptable_variants=["30 March 2023", "2023-03-30"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_09",
                    target_pages=[1],
                    key_phrases=["March 30, 2023", "dated as of"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q15_date_unanswerable_amendment_exact_expiration",
            category=QuestionCategory.DATES_LIFECYCLE,
            reasoning_type=ReasoningType.UNANSWERABLE,
            difficulty=DifficultyLevel.HARD,
            target_documents=["doc_02"],
            question="What specific calendar date did the Access-E*TRADE Agreement expire on under the Amendment?",
            expected_answer="Insufficient evidence. The Amendment removed the calendar expiration date and instead tied the term to the date the Service Savings Amount reaches the Initial Services Savings Amount.",
            acceptable_variants=["No specific calendar date stated", "Tied to Service Savings Amount threshold, not a fixed calendar date"],
            is_answerable=False,
            unanswerable_reason="Section 3 was deleted and replaced by a contingent threshold metric rather than a fixed calendar date.",
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_02",
                    target_pages=[1],
                    target_section="Section 3",
                    key_phrases=["Service Savings Amount", "Initial Services Savings Amount"]
                )
            ]
        ),

        # =========================================================================
        # 4. PAYMENT & PRICING (5 Questions)
        # =========================================================================
        BenchmarkQuestion(
            question_id="Q16_pay_net_terms_access_msa",
            category=QuestionCategory.PAYMENT,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.EASY,
            target_documents=["doc_03"],
            question="What are the standard payment terms for invoices under Section 6 of the original Access-E*TRADE MSA?",
            expected_answer="Undisputed invoices are due within thirty (30) days of the date of receipt of the invoice.",
            acceptable_variants=["Within 30 days of receipt", "Net 30 days", "30 days"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[4],
                    target_section="Section 6",
                    key_phrases=["undisputed invoices are due within thirty", "days of the date of receipt of the invoice"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q17_pay_invoicing_cycle_access",
            category=QuestionCategory.PAYMENT,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.MEDIUM,
            target_documents=["doc_03"],
            question="On what frequency will Access invoice the Company under Section 6 of the MSA?",
            expected_answer="ACCESS will invoice the COMPANY on a monthly basis for sales and services provided during the previous month.",
            acceptable_variants=["Monthly basis", "Monthly", "On a monthly basis for sales and services"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[4],
                    target_section="Section 6",
                    key_phrases=["invoice the COMPANY on a monthly basis", "previous month as"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q18_pay_marqeta_interchange_statement",
            category=QuestionCategory.PAYMENT,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.MEDIUM,
            target_documents=["doc_16"],
            question="How are periodic payments and statements handled for the Interchange Fee under the Square-Marqeta Agreement?",
            expected_answer="Marqeta shall pay Client the Interchange Fee as set forth in Schedule D and provide Client with periodic statements.",
            acceptable_variants=["Paid as set forth in Schedule D with periodic statements", "Schedule D statements and payments"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_16",
                    target_pages=[10],
                    target_section="Section 7",
                    key_phrases=["Interchange", "Schedule D", "statement"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q19_pay_square_marqeta_fees_schedule",
            category=QuestionCategory.PAYMENT,
            reasoning_type=ReasoningType.TABLE_LOOKUP,
            difficulty=DifficultyLevel.HARD,
            target_documents=["doc_16"],
            question="Where are the specific processing fee schedules and terms defined in the Square-Marqeta contract?",
            expected_answer="Schedule D - Fees.",
            acceptable_variants=["Schedule D", "Schedule D - Fees"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_16",
                    target_pages=[1],
                    key_phrases=["Schedule D - Fees", "Order of Preference"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q20_pay_unanswerable_cryptocurrency",
            category=QuestionCategory.PAYMENT,
            reasoning_type=ReasoningType.UNANSWERABLE,
            difficulty=DifficultyLevel.HARD,
            target_documents=["doc_03"],
            question="What is the exchange rate formula for paying Access in Bitcoin or digital assets?",
            expected_answer="Insufficient evidence. Invoices are payable exclusively in US Dollars.",
            acceptable_variants=["No cryptocurrency payment provision exists", "Payable in US Dollars"],
            is_answerable=False,
            unanswerable_reason="Section 6 states that invoices are payable in US Dollars; no digital currency is supported.",
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[4],
                    target_section="Section 6",
                    key_phrases=["Invoices are payable in US Dollars", "undisputed invoices"]
                )
            ]
        ),

        # =========================================================================
        # 5. TERMINATION (5 Questions)
        # =========================================================================
        BenchmarkQuestion(
            question_id="Q21_term_convenience_access_msa",
            category=QuestionCategory.TERMINATION,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.MEDIUM,
            target_documents=["doc_03"],
            question="Can the Company terminate the Access-E*TRADE MSA for convenience, and if so, with how much notice?",
            expected_answer="Yes, the Company may terminate with or without cause upon thirty (30) days prior written notice to ACCESS.",
            acceptable_variants=["30 days prior written notice", "Thirty (30) days prior written notice"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[6],
                    target_section="Section 11.1",
                    key_phrases=["with or without cause, upon thirty (30) days prior", "written notice to ACCESS"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q22_term_breach_cure_period_access",
            category=QuestionCategory.TERMINATION,
            reasoning_type=ReasoningType.TEMPORAL_REASONING,
            difficulty=DifficultyLevel.MEDIUM,
            target_documents=["doc_03"],
            question="What is the cure period for a material breach before a party can terminate the Access-E*TRADE MSA?",
            expected_answer="Ten (10) business days after written notice thereof.",
            acceptable_variants=["10 business days", "Ten (10) business days"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[6],
                    target_section="Section 11.2",
                    key_phrases=["breach is not cured within Ten (10) business days", "written notice thereof"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q23_term_amx_notice_period",
            category=QuestionCategory.TERMINATION,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.EASY,
            target_documents=["doc_01"],
            question="How many days written notice is required to terminate the AMX-Best Circuit Boards Supply Agreement in the event of a breach?",
            expected_answer="Sixty (60) days' written notice.",
            acceptable_variants=["60 days", "sixty (60) days"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_01",
                    target_pages=[4],
                    target_section="Section 9.1",
                    key_phrases=["sixty (60) days' written notice to the other party", "breach of any material provision"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q24_term_foxconn_redacted_notice",
            category=QuestionCategory.TERMINATION,
            reasoning_type=ReasoningType.UNANSWERABLE,
            difficulty=DifficultyLevel.HARD,
            target_documents=["doc_17"],
            question="What is the exact numerical notice period in days for termination for convenience in the Turtle Beach-Foxconn MSA?",
            expected_answer="Insufficient evidence. The notice period is redacted with [*****] in the SEC filing.",
            acceptable_variants=["Redacted in filing", "Notice days are redacted [*****]"],
            is_answerable=False,
            unanswerable_reason="The SEC filing redacts the convenience termination notice duration as confidential information [*****].",
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_17",
                    target_pages=[13],
                    target_section="Section 9.1",
                    key_phrases=["without cause upon no less than [*****] prior written notice"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q25_term_effects_return_materials_access",
            category=QuestionCategory.TERMINATION,
            reasoning_type=ReasoningType.PARAPHRASED_LOOKUP,
            difficulty=DifficultyLevel.MEDIUM,
            target_documents=["doc_03"],
            question="What must Access do with Customer Information upon termination of the MSA?",
            expected_answer="ACCESS will promptly return or destroy all Customer Information in its possession, and if destroyed, certify in writing.",
            acceptable_variants=["Promptly return or destroy Customer Information", "Return or destroy with certification"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[10],
                    target_section="Section 13.5",
                    key_phrases=["promptly return or destroy all Customer Information", "certify to COMPANY in writing"]
                )
            ]
        ),

        # =========================================================================
        # 6. OBLIGATIONS (5 Questions)
        # =========================================================================
        BenchmarkQuestion(
            question_id="Q26_ob_insurance_minimum_access_msa",
            category=QuestionCategory.OBLIGATIONS,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.MEDIUM,
            target_documents=["doc_03"],
            question="What General Liability insurance limit was Access required to maintain under Section 15.4 of the MSA?",
            expected_answer="$2,000,000 each occurrence.",
            acceptable_variants=["$2,000,000", "$2,000,000 each occurrence", "$2M each occurrence"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[11],
                    target_section="Section 15.4",
                    key_phrases=["General Liability", "$2,000,000 each occu"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q27_ob_insurance_eo_amendment",
            category=QuestionCategory.OBLIGATIONS,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.MEDIUM,
            target_documents=["doc_02"],
            question="What new insurance coverage type and limit did the Access-E*TRADE Amendment add to Section 15.4?",
            expected_answer="Errors and Omissions coverage in the amount of $2,000,000 each occurrence.",
            acceptable_variants=["$2,000,000 Errors & Omissions", "$2,000,000 E&O coverage", "Section 15.4 addition"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_02",
                    target_pages=[3],
                    target_section="Section 4",
                    key_phrases=["Errors and Omissions coverage in the amount of $2,000,000 each occurrence", "March 1, 2008"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q28_ob_confidentiality_duration_access",
            category=QuestionCategory.OBLIGATIONS,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.MEDIUM,
            target_documents=["doc_03"],
            question="How long do the confidentiality obligations in Section 13 survive after termination of the Access-E*TRADE MSA?",
            expected_answer="The obligations of Section 13 survive the termination or expiration of this Agreement.",
            acceptable_variants=["Survives termination or expiration", "Survives indefinitely"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[10],
                    target_section="Section 13.6",
                    key_phrases=["obligations of this Section 13 shall survive the termination or expiration"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q29_ob_audit_rights_access",
            category=QuestionCategory.OBLIGATIONS,
            reasoning_type=ReasoningType.PARAPHRASED_LOOKUP,
            difficulty=DifficultyLevel.MEDIUM,
            target_documents=["doc_03"],
            question="What audit rights does the Company possess regarding Access's books and records under Section 20?",
            expected_answer="COMPANY has the right to review books, records, policies and procedures of ACCESS, and conduct on-site audits and inspections during reasonable business hours.",
            acceptable_variants=["Review books and records and conduct on-site audits during reasonable business hours"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[13],
                    target_section="Section 20",
                    key_phrases=["review the books, records, policies and procedures", "conduct on-site audits and inspections"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q30_ob_preexisting_rights_access",
            category=QuestionCategory.OBLIGATIONS,
            reasoning_type=ReasoningType.DIRECT_LOOKUP,
            difficulty=DifficultyLevel.MEDIUM,
            target_documents=["doc_03"],
            question="Who owns pre-existing intellectual property rights under Section 14.2 of the Access-E*TRADE MSA?",
            expected_answer="All pre-existing intellectual property rights belonging to ACCESS as of the date of the Agreement remain the sole and exclusive property of ACCESS.",
            acceptable_variants=["ACCESS remains sole and exclusive owner", "Pre-Existing Rights remain property of ACCESS"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[10],
                    target_section="Section 14.2",
                    key_phrases=["Pre-Existing Rights", "remain the sole and exclusive property of ACCESS"]
                )
            ]
        ),

        # =========================================================================
        # 7. CROSS-DOCUMENT / CROSS-CONTRACT (5 Questions)
        # =========================================================================
        BenchmarkQuestion(
            question_id="Q31_cross_governing_law_comparison",
            category=QuestionCategory.CROSS_DOCUMENT,
            reasoning_type=ReasoningType.CROSS_CONTRACT,
            difficulty=DifficultyLevel.HARD,
            target_documents=["doc_03", "doc_10"],
            question="Compare the governing law between the Access-E*TRADE MSA and the Sabre-DXC Agreement. Which states govern each?",
            expected_answer="The Access-E*TRADE MSA is governed by Delaware law, whereas the Sabre-DXC Agreement is governed by Texas law.",
            acceptable_variants=["Access-E*TRADE is Delaware, Sabre-DXC is Texas", "Delaware for Access, Texas for Sabre"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(document_id="doc_03", target_pages=[12], key_phrases=["laws of the State of Delaware"]),
                ExpectedEvidence(document_id="doc_10", target_pages=[88], key_phrases=["laws of the State of Texas"])
            ]
        ),
        BenchmarkQuestion(
            question_id="Q32_cross_payment_terms_access_vs_amx",
            category=QuestionCategory.CROSS_DOCUMENT,
            reasoning_type=ReasoningType.CROSS_CONTRACT,
            difficulty=DifficultyLevel.MEDIUM,
            target_documents=["doc_03", "doc_01"],
            question="How do standard invoice payment deadlines compare between the Access-E*TRADE MSA and the AMX Supply Agreement?",
            expected_answer="Both contracts establish thirty-day payment windows: Access invoices are due within thirty (30) days of receipt, and AMX invoices are payable thirty (30) days from receipt.",
            acceptable_variants=["Both provide 30-day payment terms", "Net 30 in both"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(document_id="doc_03", target_pages=[4], key_phrases=["undisputed invoices are due within thirty"]),
                ExpectedEvidence(document_id="doc_01", target_pages=[2], key_phrases=["thirty (30) days", "receipt of such invoice"])
            ]
        ),
        BenchmarkQuestion(
            question_id="Q33_cross_spare_backup_hp_sow_linkage",
            category=QuestionCategory.CROSS_DOCUMENT,
            reasoning_type=ReasoningType.MULTI_HOP,
            difficulty=DifficultyLevel.HARD,
            target_documents=["doc_13"],
            question="In the Spare Backup-Hewlett-Packard agreement, how are Services defined in relation to Statements of Work?",
            expected_answer="Services are defined as the services to be provided by Supplier pursuant to the Agreement, as further described in a Statement of Work.",
            acceptable_variants=["Described in a Statement of Work", "Pursuant to the Agreement as described in a SOW"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_13",
                    target_pages=[3],
                    target_section="Section 2.11",
                    key_phrases=["services to be provided by Supplier", "described in a Statement of Work"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q34_cross_notice_windows_access_vs_amx",
            category=QuestionCategory.CROSS_DOCUMENT,
            reasoning_type=ReasoningType.CROSS_CONTRACT,
            difficulty=DifficultyLevel.MEDIUM,
            target_documents=["doc_03", "doc_01"],
            question="Which agreement requires longer notice for termination: Access-E*TRADE for convenience or AMX for breach?",
            expected_answer="AMX requires longer notice (60 days for breach) compared to Access-E*TRADE (30 days for convenience).",
            acceptable_variants=["AMX (60 days) vs Access (30 days)", "AMX requires 60 days"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(document_id="doc_03", target_pages=[6], key_phrases=["with or without cause, upon thirty (30) days prior"]),
                ExpectedEvidence(document_id="doc_01", target_pages=[4], key_phrases=["sixty (60) days' written notice to the other party"])
            ]
        ),
        BenchmarkQuestion(
            question_id="Q35_cross_unanswerable_shared_indemnity_fund",
            category=QuestionCategory.CROSS_DOCUMENT,
            reasoning_type=ReasoningType.UNANSWERABLE,
            difficulty=DifficultyLevel.HARD,
            target_documents=["doc_03", "doc_01"],
            question="Which joint cross-company escrow bank holds indemnity escrow funds for both Access-E*TRADE and AMX?",
            expected_answer="Insufficient evidence. The agreements are completely separate bilateral contracts and have no shared escrow or common fund.",
            acceptable_variants=["No shared escrow or bank exists between the contracts"],
            is_answerable=False,
            unanswerable_reason="The agreements are independent contracts with no common parties, funds, or escrow arrangements.",
            evidence_requirements=[
                ExpectedEvidence(document_id="doc_03", target_pages=[1], key_phrases=["Access Worldwide Communications"]),
                ExpectedEvidence(document_id="doc_01", target_pages=[1], key_phrases=["AMX, LLC"])
            ]
        ),

        # =========================================================================
        # 8. VERSION & AMENDMENT PRECEDENCE (5 Questions)
        # =========================================================================
        BenchmarkQuestion(
            question_id="Q36_amend_term_replacement_access",
            category=QuestionCategory.AMENDMENTS_VERSIONS,
            reasoning_type=ReasoningType.AMENDMENT_PRECEDENCE,
            difficulty=DifficultyLevel.HARD,
            target_documents=["doc_02", "doc_03"],
            question="How does Section 2 of the Access-E*TRADE Amendment modify the term provisions in Section 3 of the original MSA?",
            expected_answer="It deletes Section 3 of the original Agreement in its entirety and replaces it with a term continuing until the Service Savings Amount reaches the Initial Services Savings Amount.",
            acceptable_variants=["Deletes and replaces Section 3 in its entirety", "Replaces fixed term with Service Savings threshold"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_02",
                    target_pages=[1],
                    target_section="Section 2 / Section 3",
                    key_phrases=["Section 3 of the Agreement shall be deleted in its entirety", "Service Savings Amount"]
                ),
                ExpectedEvidence(
                    document_id="doc_03",
                    target_pages=[2],
                    target_section="Section 3.1",
                    key_phrases=["Initial Term", "June 9, 2006"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q37_amend_price_replacement_access",
            category=QuestionCategory.AMENDMENTS_VERSIONS,
            reasoning_type=ReasoningType.AMENDMENT_PRECEDENCE,
            difficulty=DifficultyLevel.HARD,
            target_documents=["doc_02", "doc_03"],
            question="What happened to Section 1.2 of the Access-E*TRADE MSA under the Amendment?",
            expected_answer="Section 1.2 was deleted in its entirety and replaced with new pricing language.",
            acceptable_variants=["Deleted in its entirety and replaced"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_02",
                    target_pages=[1],
                    target_section="Section 1",
                    key_phrases=["Section 1.2 of the Agreement shall be deleted in its entirety", "inserted in lieu thereof"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q38_amend_payment_amendment_access",
            category=QuestionCategory.AMENDMENTS_VERSIONS,
            reasoning_type=ReasoningType.AMENDMENT_PRECEDENCE,
            difficulty=DifficultyLevel.HARD,
            target_documents=["doc_02", "doc_03"],
            question="How did the Access-E*TRADE Amendment modify the payment provisions in Section 6?",
            expected_answer="Section 6 of the Agreement was deleted in its entirety and replaced with an updated payment section.",
            acceptable_variants=["Deleted and replaced Section 6"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_02",
                    target_pages=[2],
                    target_section="Section 3",
                    key_phrases=["Section 6 of the Agreement shall be deleted in its entirety", "inserted in lieu thereof"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q39_amend_full_force_confirmation_access",
            category=QuestionCategory.AMENDMENTS_VERSIONS,
            reasoning_type=ReasoningType.AMENDMENT_PRECEDENCE,
            difficulty=DifficultyLevel.MEDIUM,
            target_documents=["doc_02"],
            question="What effect does Section 5 of the Access-E*TRADE Amendment have on provisions of the original Agreement not amended?",
            expected_answer="Except as otherwise set forth herein, the Agreement and any Scope of Work shall remain in full force and effect.",
            acceptable_variants=["Remain in full force and effect", "Unchanged terms continue in full force and effect"],
            is_answerable=True,
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_02",
                    target_pages=[3],
                    target_section="Section 5",
                    key_phrases=["remain in full force", "and effect"]
                )
            ]
        ),
        BenchmarkQuestion(
            question_id="Q40_amend_unanswerable_governing_law_override",
            category=QuestionCategory.AMENDMENTS_VERSIONS,
            reasoning_type=ReasoningType.UNANSWERABLE,
            difficulty=DifficultyLevel.HARD,
            target_documents=["doc_02"],
            question="Which section of the Access-E*TRADE Amendment changed the governing law from Delaware to New York?",
            expected_answer="Insufficient evidence. The Amendment did not change governing law; Delaware law remains in full force and effect under Section 5.",
            acceptable_variants=["The Amendment did not change governing law; Delaware remains in effect", "No change to governing law"],
            is_answerable=False,
            unanswerable_reason="The Amendment only modifies Sections 1.2, 3, 6, and 15; governing law remains unchanged under Section 5.",
            evidence_requirements=[
                ExpectedEvidence(
                    document_id="doc_02",
                    target_pages=[3],
                    target_section="Section 5",
                    key_phrases=["remain in full force", "and effect"]
                )
            ]
        )
    ]
