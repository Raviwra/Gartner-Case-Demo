# D6. [SYNTHETIC SUMMARY] SR 26-2 Model Risk Management Guidance: summary prepared for the case exercise

This is a summary written for the exercise. Verify against the letter at federalreserve.gov before relying on it.

Plain-language summary of the revised interagency guidance on model risk management, prepared September 2026 for the Meridian case. It paraphrases the Federal Reserve cover letter and its attachment and two published commentaries listed under Sources. It does not reproduce the letter text.

## §1 What it is and whom it applies to

¶1 SR 26-2, "Revised Guidance on Model Risk Management", was issued on April 17, 2026 by the Federal Reserve, the OCC and the FDIC. It supersedes SR 11-7 (April 4, 2011), the guidance most bank model risk policies were written to, and SR 21-8 (April 9, 2021), the interagency statement on model risk for BSA/AML systems.

¶2 The cover letter says the guidance is expected to be most relevant to banking organizations with over $30 billion in total assets. Smaller organizations are generally expected to manage models under their own risk practices, though the guidance may still be relevant to some of them. Meridian, at about $42 billion in total assets, falls within the group the letter names as most relevant.

¶3 The attachment describes the guidance as principles, not enforceable standards or prescriptive requirements. It also says supervisory action may still follow from unsafe or unsound practices arising from insufficient management of model risk.

## §2 What counts as a model, and what falls outside

¶1 The guidance defines a model as a complex quantitative method, system or approach that applies statistical, economic or financial theories to turn input data into quantitative estimates.

¶2 The definition leaves out simple arithmetic, such as the calculations found in spreadsheets, and deterministic rule-based processes and software that have no statistical, economic or financial theory behind their design or use. Commentators read this as narrower than SR 11-7. Baker Tilly notes that spreadsheets with complex forecasting may still be in scope.

¶3 The attachment's scope footnotes also address certain categories of AI. Published commentaries describe that treatment differently (see Sources). This summary does not characterize it. Risk should read the footnotes in the attachment directly.

## §3 Core elements kept from SR 11-7

¶1 The guidance keeps the three elements that SR 11-7 was built on, in updated form.

- **Development and use.** A clear statement of purpose, testing in proportion to complexity and materiality, user input on design and assumptions, and understanding of a model's limitations. Using a model beyond its intended purpose calls for added analysis and a review of controls.
- **Validation and monitoring.** Conceptual soundness, outcomes analysis (comparing outputs with real-world results) and ongoing monitoring. Validation generally comes before first use. When urgent need requires earlier use, the guidance looks for closer attention to limitations, informed stakeholders and controls such as limits on use.
- **Governance and controls.** Policies and procedures, clear roles and accountability, a model inventory, documentation, and internal audit's role in assessing whether model risk practices work.

¶2 "Effective challenge" by objective, qualified people with the standing to effect change runs through all three. Vendor and third-party models stay within the principles: the bank remains responsible for understanding, validating and monitoring them.

## §4 Risk-based and materiality-based approach

¶1 Model risk depends on a model's inherent risk (assumptions, complexity, input quality), its exposure (how much business rests on its output), its purpose and its use. Purpose and exposure together determine materiality.

¶2 A bank may treat some models as immaterial; for those, the guidance expects identification and monitoring for signs that they are becoming material. Models of higher materiality get more comprehensive and rigorous oversight. Risk is assessed for each model and in aggregate, where models share assumptions, data or methods.

¶3 The depth of model risk management can be tailored to the bank's size and complexity and to the risk of each model. Baker Tilly and Sia Partners both describe proportionality, and validation scaled to materiality instead of fixed cycles, as the main practical change from SR 11-7.

## §5 What it means for a drafting tool that assembles and cites but does not rate

¶1 The prototype retrieves passages from the borrower file, assembles cited text into the memo template, reports conflicts and gaps, and leaves the risk rating and recommendation to the underwriter (D4 §4.2.5). It does not produce its own estimates; ratios come from the spread.

¶2 Whether a generative AI drafting tool is a "model" under SR 26-2 is a judgment for Meridian's Risk function. This summary takes no position on that question.

¶3 Either way, the practices the guidance describes map onto controls the tool can carry: a stated purpose and limits of use, testing before first use (the evaluation set), monitoring after release, documentation and version control of the rulebook, an inventory entry with a named owner, effective challenge from people outside the build team, and oversight of the vendor whose model sits underneath. Models that feed the memo, such as the spreading tool and any risk-rating scorecard, are separate inventory questions for Risk.

## §6 Prototype assumption

¶1 [Prototype assumption: Meridian's model risk policy, described in the case as aligned with SR 11-7, would be updated to SR 26-2 and joined by an AI addendum. The addendum would record the drafting tool in an inventory with a named owner, a stated purpose (assemble and cite; no rating or recommendation), an evaluation set re-run on every prompt or model change, and Risk's written determination of whether the tool is governed as a model under the model risk policy or under the AI addendum.]

## Sources

- Board of Governors of the Federal Reserve System, SR 26-2, "Revised Guidance on Model Risk Management" (cover letter), April 17, 2026: https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm
- Attachment to SR 26-2, "Supervisory Guidance on Model Risk Management": https://www.federalreserve.gov/supervisionreg/srletters/SR2602a1.pdf
- Baker Tilly, "Updated interagency guidance on model risk management": https://www.bakertilly.com/insights/updated-interagency-guidance-on-model-risk-management
- Sia Partners, "SR 11-7 vs. SR 26-2: model risk management modernization": https://www.sia-partners.com/en/insights/publications/sr-11-7-vs-sr-26-2-model-risk-management-modernization

The Meridian facts and the prototype assumption are part of the case exercise; SR 26-2 itself is a real supervisory letter.

FICTIONAL - prepared for case exercise.
