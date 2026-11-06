# Region-neutral design for later European deployment

Do not embed MENA country names, legal labels, or Arabic/English assumptions into shared core. Region config owns jurisdiction hierarchy, languages and domain taxonomy. Source/provision IDs include jurisdiction namespace and don't assume a flat country-only hierarchy.

Europe may require EU instruments, EEA, national transpositions, devolved jurisdictions, local regulations, official multilingual versions and changing applicability timelines. Treat EU directive vs regulation differences and national implementing instruments explicitly; avoid single 'Europe law' scope.

Test second region with minimal fake examples (not legal assertions) before moving core out. Migration should maintain old URLs and IDs or redirect explicitly.
